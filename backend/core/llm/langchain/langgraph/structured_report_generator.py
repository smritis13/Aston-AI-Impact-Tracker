# structured_report_generator.py
"""A generic researcher that extracts structured use-cases from the Web.

This is an opinionated rewrite of the original `MedicalSDLCResearcher` that has been generalized for research impact:
  * Accepts a **user prompt** that guides the search and extraction process
  * Implements a search → scrape → extract workflow with optional credibility and relevance checks
  * Persists extracted use-cases into a Django model called `UseCase`
  * Supports real-time progress updates via Pusher
  * Can be gracefully stopped and resumed

The code is organized into several components:
  * `report_generator_utils.py`: Shared constants, data classes, and utility functions
  * `prompts.py`: LLM prompts for planning, extraction, and validation
  * `single_url_extractor.py`: A simplified version for single URL processing

Dependencies:
  * langchain >= 0.1.x
  * langgraph (for StateGraph)
  * TavilySearchResults for web search
  * SimpleHtmlScraper for async web scraping
  * Django models: `Report` (optional) & `UseCase`
  * PusherService for real-time updates

Usage example
-------------
```python
from structured_report_generator import StructuredReportGenerator
from content.models import Report

user_question = "Focus on how European banks use GenAI for loan origination."  
report = Report.objects.create(title="GenAI in banking - May 2025")

r = StructuredReportGenerator(
    user_prompt=user_question,
    report_obj=report,
    theme_id=123,  # Optional: link to a specific theme
    max_tasks=3,
    enable_credibility_check=True,
    enable_relevance_check=True
)

# Start the extraction process
report_id, use_cases = r.run()

# To stop the process gracefully
r.stop()
```
"""

from __future__ import annotations

import os, re, json, asyncio, threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from queue import Queue
from datetime import datetime
from typing import List, Dict, Optional
from html import escape
from urllib.parse import urlparse

from langchain_openai import ChatOpenAI  # noqa - not langchain_community's ChatOpenAI: that
# older, separate implementation never populates response.usage_metadata (no
# stream_usage support at all), which is what silently made every tracked
# call in _track_llm_call() record 0 tokens despite a correct call count.
from langgraph.graph import StateGraph, END
from langchain_community.tools.tavily_search.tool import TavilySearchResults

# ────────────────────────── app-specific imports ──────────────────────────
from core.llm.utils.SimpleHtmlScraper import SimpleHtmlScraper  # noqa
from core.llm.utils.pusher_service import PusherService         # noqa (can be a no‑op if not needed)
from core.llm.utils.ThoughtLoggerCallback import ThoughtLoggerCallback  # noqa

from content.models import Report, UseCase, ScrapedURL   # NEW model – see below

from core.llm.langchain.langgraph.prompts import (
    PLANNING_PROMPT,
    EXTRACTION_PROMPT,
    PDF_QUANTITATIVE_EXTRACTION_PROMPT,
)
from core.llm.langchain.langgraph.ref_prompts import (
    REF_PLANNING_PROMPT,
    REF_EXTRACTION_PROMPT,
    REF_CREDIBILITY_RELEVANCE_CHECK_PROMPT,
    REF_CASE_STUDY_SYNTHESIS_PROMPT,
)
from core.llm.langchain.langgraph.report_generator_utils import (
    ExtractedUseCase,
    GraphState,
    _ScrapeTask,
    clean_text_for_db,
    get_default_schema,
    INDUSTRY_SECTORS,
    PERFORMANCE_IMPROVEMENT_CATEGORIES,
    GEOGRAPHY_REGIONS,
    shorten_url,
    calculate_progress,
    format_url_progress_message,
    format_task_progress_message,
    format_query_progress_message,
    generate_use_case_types_with_llm,
    IMPACT_PERIOD as _rgu_IMPACT_PERIOD,
    RESEARCH_PERIOD as _rgu_RESEARCH_PERIOD,
    date_sort_key as _rgu_date_sort_key,
    is_within_period as _rgu_is_within_period,
    ref_period_for_content_type as _rgu_ref_period_for_content_type,
)

# Custom exception for graceful stop
class ReportGenerationStopped(Exception):
    """Exception raised when report generation is stopped by user request."""
    pass

class StructuredReportGenerator:
    """Search → Scrape → Extract pipeline that writes `UseCase` rows."""

    def __init__(
        self,
        *,
        user_prompt: str,
        search_query: str | None = None,
        pdf_text: str | None = None,
        pdf_filename: str | None = None,
        source_priority: str = "WEB_FIRST",
        report_obj: Report | None = None,
        theme_id: int | None = None,
        report_id: int | None = None,
        max_tasks: int = 25,
        max_results_per_query: int = 10,
        max_links_to_scrape: int | None = None,
        relevance_threshold: float | None = None,
        max_use_cases: int = 10,
        debug_mode: bool = False,
        enable_credibility_check: bool = False,
        enable_relevance_check: bool = False,
        skip_processed_urls: bool = True,
        number_of_outcomes: int = 10,
        search_complexity: str = "medium",
        replanning_rounds: int = 2,
        report_type: str = "",
        impact_sections: List[Dict] | None = None,
        include_summary: bool = True,
        researcher_affiliations: List[Dict] | None = None,
        skip_report_generation: bool = False,
    ) -> None:

        self.user_prompt = user_prompt
        self.search_query = search_query or user_prompt  # Use search_query if provided
        self.pdf_text = pdf_text
        self.pdf_filename = pdf_filename
        self.source_priority = source_priority
        self.pdf_uploaded = bool(pdf_text)
        self.report_type = report_type or ""
        self.impact_sections = impact_sections or []
        self.include_summary = include_summary
        # Optional list of {name, aston_start, aston_end} dicts - one per
        # named researcher on this case study - so the synthesis prompt can
        # distinguish Aston's institutional role from each individual's,
        # most relevant when a researcher moved institutions during the REF
        # period. Most REF case studies name more than one academic, so this
        # is a list rather than a single dict. Stored on Report.metadata by
        # the caller.
        self.researcher_affiliations = researcher_affiliations or []
        # When True, a "search" run only discovers/persists UseCase rows and
        # skips the final narrative synthesis call - useful when the caller
        # wants to find evidence now and generate the report later (e.g. via
        # compile_from_existing_use_cases) rather than paying for a synthesis
        # call on every search run, including throwaway/exploratory ones.
        self.skip_report_generation = skip_report_generation
        self.theme_id = theme_id
        self.report_id = report_id  # Store report_id for Pusher streaming
        self.theme_title = None
        if theme_id:
            from content.models import UseCaseTheme
            theme = UseCaseTheme.objects.get(id=theme_id)
            self.theme_title = theme.title

        # Apply complexity mapping to override defaults
        complexity_params = self._map_complexity_to_params(search_complexity, number_of_outcomes)
        
        # runtime knobs - apply complexity mapping
        self.max_tasks   = complexity_params["max_tasks"]
        self.max_results = complexity_params["max_results_per_query"]
        # Explicit max_links_to_scrape overrides the complexity-tier default,
        # so callers can dial breadth/cost per run instead of only picking a tier.
        self.max_links   = max_links_to_scrape if max_links_to_scrape is not None else complexity_params["max_links_to_scrape"]
        self.max_use_cases = number_of_outcomes  # Use the user-provided number_of_outcomes
        self.search_depth = complexity_params["search_depth"]
        # Explicit relevance_threshold overrides the complexity-tier default,
        # so a run that's rejecting almost everything can be loosened without
        # changing what the tier means for every other run.
        self.relevance_threshold = relevance_threshold if relevance_threshold is not None else complexity_params["relevance_threshold"]
        # A 6/10 score is the extraction prompt's defined threshold for an
        # evidence lead that is genuinely related to the researcher and the
        # claimed impact.  Keeping the runtime floor at 7/10 meant otherwise
        # valid publications and beneficiary sources never reached the REF
        # gate, even though the gate itself supports a 6/10 minimum.
        self.relevance_threshold = max(0.6, self.relevance_threshold)
        self._consecutive_relevance_rejections = 0
        self._relevance_threshold_floor = 0.6
        self.debug       = debug_mode
        self.enable_credibility_check = enable_credibility_check
        self.enable_relevance_check = enable_relevance_check
        self.skip_processed_urls = skip_processed_urls
        self.recursion_limit = 1000
        self.total_use_cases_created = 0  # Track total use cases created
        self.max_replanning_rounds = max(0, replanning_rounds)
        # Hard ceiling on Tavily calls for the whole run, independent of the
        # replanning-round cap. Diagnosed cause of runaway API usage: each
        # replanning round can spawn up to max_tasks new tasks at 8-12
        # queries each, and the "stop after 2 stale rounds" safety valve only
        # trips on literally zero new results - a round that finds even one
        # marginal use case resets it, so a hard-to-search topic can burn
        # hundreds of calls chasing the last few requested results. This is
        # a simple, predictable cost ceiling on top of that, checked in
        # _route_after_tasks before another round is allowed to start.
        self.max_search_calls = complexity_params["max_search_calls"]
        self._all_used_queries: set[str] = set()  # Avoid repeating searches across replanning rounds
        self._all_used_focus_areas: set[str] = set()  # Avoid replanning into the same focus areas
        self.seen_result_signatures: list[set[str]] = []  # Title token-sets of results already kept, for near-duplicate detection
        self._search_calls_total = 0
        self._search_calls_failed = 0
        self._last_search_error: str | None = None
        self._streamed_search_errors: set[str] = set()  # Avoid spamming the UI with the same error repeatedly
        self._consecutive_search_failures = 0
        # If the search API itself is down/rate-limited (rather than a topic
        # genuinely having few results), every query fails in a row. Without
        # this, the self-adjusting replanner (see _replanning_node) reads
        # "zero results" as "topic needs more queries" and keeps adding tasks
        # indefinitely, burning OpenAI planning calls against a dead search API.
        self._search_api_unavailable = False
        self._SEARCH_FAILURE_THRESHOLD = 6

        # Extraction is batched N pages per LLM call instead of one call per
        # page, so a run with e.g. 30 scraped pages makes ~6 extraction calls
        # instead of 30 - fewer round trips means the extraction stage
        # finishes faster for the same evidence. Each finding must carry an
        # "article_index" (see REF_EXTRACTION_PROMPT) so it can still be
        # mapped back to its exact source page for every downstream check.
        # The batch size is a balance between fewer calls and prompt context
        # limits; 5 articles per call is cheaper with acceptable quality.
        self._EXTRACTION_BATCH_SIZE = 5

        # Token/cost tracking - no instrumentation existed before, so a run's
        # cost was invisible until the OpenAI bill arrived. Accumulated across
        # every LLM call in this run and persisted into Report.metadata at the
        # end (see _track_llm_call, run()). Guarded by a lock since extraction
        # and search dispatch calls happen concurrently across threads.
        self._token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "calls": 0}
        self._token_usage_lock = threading.Lock()

        # misc
        self.report_obj = report_obj
        self.pusher_service = PusherService()
        self.callback = ThoughtLoggerCallback()
        self.processed_urls: set[str] = set()
        self._last_progress = 0  # Track last progress value
        # Populated by _build_impact_case_study_markdown; read back by
        # _save_generated_report so the professional REF report can be
        # followed by a separated readiness commentary section in the same
        # report document.
        self._last_draft_section = ""
        self._last_commentary_section = ""

        # Initialize process status in report metadata
        if self.report_obj:
            self.report_obj.metadata.update({
                'status': 'RUNNING',
                'progress': {'current': 0, 'total': 0},
                'started_at': datetime.now().isoformat(),
                'completed_at': None,
                'should_stop': False
            })
            self.report_obj.save()

        self.schema = get_default_schema()
        self.base_extract_prompt = REF_EXTRACTION_PROMPT
        self.planning_prompt = REF_PLANNING_PROMPT  

        # external services - use complexity-mapped search_depth
        self.llm_core = ChatOpenAI(model="gpt-5.4", temperature=0.2)
        # Separate smaller model for credibility/relevance scoring.
        # gpt-5.4 is too strict on the 1-10 REF scale — it demands attribution
        # and significance evidence that a 4 000-char excerpt rarely proves,
        # yielding scores of 2-4 for genuinely relevant content. gpt-5.4-mini
        # is calibrated closer to how gpt-4o judged this task.
        self.llm_check = ChatOpenAI(model="gpt-5.4-mini", temperature=0)
        self.search_api = TavilySearchResults(
            api_key=os.getenv("TAVILY_API_KEY"),
            max_results=self.max_results,
            search_depth=self.search_depth,
            include_answer=True
        )
        self.scraper = SimpleHtmlScraper()

        # compile the graph once
        self.graph = self._build_graph().compile()

    # ────────────────────────── complexity mapping ──────────────────────────────
    
    def _map_complexity_to_params(self, complexity: str, number_of_outcomes: int) -> Dict:
        """
        Map search complexity level to research parameters.
        
        Complexity Levels:
        - simple: Fast, minimal research. Good for quick overviews.
        - medium: Balanced approach. Recommended for most use cases.
        - complex: Thorough research. More API calls and time.
        - advanced: Most comprehensive. Maximum depth and breadth.
        
        Returns a dict with mapped parameters including search_depth,
        max_tasks, max_results_per_query, and relevance_threshold.
        """
        complexity_map = {
            "low": {
                "search_depth": "advanced",
                "max_tasks": max(2, number_of_outcomes // 4),  # Keep at least two targeted tasks for REF coverage
                "max_results_per_query": 2,  # Minimum results per query
                "max_links_to_scrape": max(12, number_of_outcomes * 2),
                "relevance_threshold": 0.60,
                "max_search_calls": 16,
                "description": "Lowest-cost search - targeted REF evidence with minimal query budget"
            },
            "simple": {
                "search_depth": "basic",
                "max_tasks": max(1, number_of_outcomes // 3),  # Fewer tasks
                "max_results_per_query": 3,  # Minimal results per query
                "max_links_to_scrape": max(12, number_of_outcomes * 3),
                "relevance_threshold": 0.60,  # Matches the prompt's own is_relevant bar (score >= 6/10)
                "max_search_calls": 24,
                "description": "Fast search - minimal API calls"
            },
            "medium": {
                "search_depth": "advanced",
                "max_tasks": max(3, number_of_outcomes // 2),  # Moderate tasks
                "max_results_per_query": 8,  # Standard results
                "max_links_to_scrape": max(24, number_of_outcomes * 4),
                "relevance_threshold": 0.60,  # Matches the prompt's own is_relevant bar (score >= 6/10)
                "max_search_calls": 48,
                "description": "Balanced search - good quality results"
            },
            "complex": {
                "search_depth": "advanced",
                "max_tasks": max(5, number_of_outcomes),  # More tasks
                "max_results_per_query": 12,  # More results
                "max_links_to_scrape": max(40, number_of_outcomes * 5),
                "relevance_threshold": 0.60,  # Matches the prompt's own is_relevant bar (score >= 6/10)
                "max_search_calls": 80,
                "description": "Thorough search - comprehensive research"
            },
            "advanced": {
                "search_depth": "advanced",
                "max_tasks": max(10, number_of_outcomes * 2),  # Maximum tasks
                "max_results_per_query": 15,  # Maximum results
                "max_links_to_scrape": max(60, number_of_outcomes * 6),
                "relevance_threshold": 0.60,  # Matches the prompt's own is_relevant bar (score >= 6/10)
                "max_search_calls": 120,
                "description": "Maximum depth - exhaustive research"
            }
        }
        
        # Default to medium if complexity not recognized
        params = complexity_map.get(complexity.lower(), complexity_map["medium"])
        
        # Log the complexity mapping
        print(f"[Complexity Mapping] Level: {complexity} | Outcomes: {number_of_outcomes}")
        print(f"  {params['description']}")
        print(f"  Tasks: {params['max_tasks']}, Results/Query: {params['max_results_per_query']}, "
              f"Max Links: {params['max_links_to_scrape']}, Threshold: {params['relevance_threshold']}")
        
        return params

    def _tokenize_for_matching(self, text: str) -> set[str]:
        """Return meaningful tokens for lightweight source/result relevance checks."""
        stop_words = {
            "about", "after", "again", "against", "also", "and", "are", "case",
            "from", "have", "impact", "into", "more", "outcome", "research",
            "study", "that", "the", "their", "this", "use", "with", "within",
            "year", "years"
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(token) > 2 and token not in stop_words
        }

    # No aston.ac.uk source (any subdomain: www, news, research, publications,
    # etc.) is usable as REF evidence - Fiona's review feedback said to
    # "prioritise non-Aston sources" as a general rule, not just exclude
    # press releases. An earlier, narrower version of this check only
    # excluded /news/ and /press/ paths and explicitly allowed
    # research.aston.ac.uk - that let through both a paper hosted on
    # publications.aston.ac.uk (Aston's own repository copy, not the
    # independent journal/publisher version) and staff-profile pages on
    # research.aston.ac.uk being used as the evidence source itself, not
    # just for identity context. Every aston.ac.uk subdomain is now excluded,
    # with no carve-outs - if a paper is also indexed independently (DOI,
    # journal site, PubMed, arXiv), the pipeline should find that copy
    # instead.
    _ASTON_HOST_SUFFIX = "aston.ac.uk"

    @classmethod
    def _is_aston_source(cls, url: str) -> bool:
        """True if `url` is hosted on any aston.ac.uk subdomain."""
        host = (urlparse(url or "").netloc or "").lower()
        return host == cls._ASTON_HOST_SUFFIX or host.endswith("." + cls._ASTON_HOST_SUFFIX)

    def _source_quality_score(self, url: str) -> int:
        """Prefer independently verifiable, REF-friendly source domains."""
        host = (urlparse(url or "").netloc or "").lower()
        if not host:
            return 0

        trusted_suffixes = (
            ".gov", ".gov.uk", ".nhs.uk", ".ac.uk", ".edu", ".europa.eu",
            ".org", ".org.uk", ".who.int", ".un.org", ".oecd.org",
        )
        research_domains = (
            "nature.com", "sciencedirect.com", "springer.com", "wiley.com",
            "tandfonline.com", "bmj.com", "thelancet.com", "pubmed.ncbi.nlm.nih.gov",
            "ncbi.nlm.nih.gov", "arxiv.org", "ssrn.com", "jstor.org",
        )
        if self._is_aston_source(url):
            return -1
        if host.endswith(trusted_suffixes) or any(domain in host for domain in research_domains):
            return 3
        if any(part in host for part in ("university", "research", "institute", "policy", "charity")):
            return 2
        if any(part in host for part in ("blog", "medium.com", "substack.com", "press", "newswire", "expertfile.com")):
            return -1
        return 1

    def _rank_search_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Rank search results before scraping so API budget goes to sources likely to
        contain REF-relevant evidence: beneficiaries, metrics, implementation, and
        credible corroboration.  Results with no named-researcher/partner mention
        are penalised so generic industry articles don't crowd out attributable ones.
        """
        user_terms = self._tokenize_for_matching(self.user_prompt)
        query_terms = self._tokenize_for_matching(query)
        target_terms = user_terms | query_terms

        # Extract multi-word named entities (2+ tokens) from the user prompt so we
        # can reward results that explicitly mention them.  Single-letter tokens and
        # stop-words are already filtered by _tokenize_for_matching.
        named_entity_phrases = []
        for phrase in re.findall(r'[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+', self.user_prompt):
            named_entity_phrases.append(phrase.lower())
        # Also include prominent single capitalised words (researcher surnames, brands).
        # The exclusion set is compared in lowercase since the extracted words are
        # lowercased above - it used to be written in Title Case, which meant the
        # subtraction never matched anything and every generic word below leaked
        # through as a "named entity".
        generic_capitalised_terms = {
            "the", "and", "for", "with", "impact", "named", "aston", "university",
            "research", "evidence", "high", "prioritise", "build", "ref",
        }
        named_single = {
            w.lower() for w in re.findall(r'\b[A-Z][a-z]{2,}\b', self.user_prompt)
        } - generic_capitalised_terms
        # CamelCase/acronym coined terms (e.g. "PowerTAC", "NHS") have a second
        # capital letter inside the word, so the pattern above - one leading
        # capital followed by lowercase - never matches them, and standalone
        # mentions (not part of a two-word capitalised phrase like "BBC News")
        # were silently invisible to the named-entity boost/penalty below.
        named_single |= {
            w.lower()
            for w in re.findall(r'\b[A-Z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b', self.user_prompt)
            if len(w) >= 3
        } - generic_capitalised_terms

        evidence_terms = {
            "adopted", "adoption", "benefited", "beneficiaries", "case", "clinical",
            "cost", "deployed", "deployment", "evidence", "implemented",
            "implementation", "improved", "million", "national", "patients",
            "policy", "practice", "reduced", "reduction", "report", "saved",
            "savings", "study", "trial", "users"
        }
        metric_pattern = re.compile(
            r"(\d[\d,]*(?:\.\d+)?\s*(?:%|percent|million|bn|billion|k|people|patients|users|organisations|organizations|sites|countries|years|months|GBP|USD|EUR))",
            re.I,
        )

        def score_result(result: Dict) -> int:
            text = " ".join([
                result.get("title", ""),
                result.get("snippet", ""),
                result.get("source", ""),
                result.get("link", ""),
            ])
            text_lower = text.lower()
            tokens = self._tokenize_for_matching(text)
            score = 0
            score += min(len(tokens & target_terms), 8)
            score += min(len(tokens & evidence_terms), 6)
            if metric_pattern.search(text):
                score += 4
            # Recency bonus: decays with age instead of a flat cliff, and is
            # computed from today's year rather than a hardcoded list, so it
            # doesn't go stale. Search results are truncated to
            # max_results_per_query after ranking, so this genuinely
            # prioritises newer sources for scraping - not just a tie-breaker.
            current_year = datetime.now().year
            year_match = re.search(r"\b(19|20)\d{2}\b", text)
            if year_match:
                mentioned_year = int(year_match.group(0))
                age = current_year - mentioned_year
                if 0 <= age <= 6:
                    score += max(0, 6 - age)  # this year +6, down to 6 years ago +0
            score += self._source_quality_score(result.get("link", ""))
            if any(term in text_lower for term in ("announcement", "launches", "launch", "sponsored", "advertorial")):
                score -= 3

            # Boost results that explicitly mention a named entity from the user prompt.
            # Penalise results with zero named-entity matches when named entities exist —
            # these are generic industry articles that cannot be attributed to the research group.
            if named_entity_phrases or named_single:
                has_named_match = (
                    any(p in text_lower for p in named_entity_phrases)
                    or bool(tokens & named_single)
                )
                if has_named_match:
                    score += 6
                elif self._source_quality_score(result.get("link", "")) >= 3:
                    # Government/policy/research-institution domains (.gov.uk, .ac.uk, journal
                    # publishers, etc.) rarely surface a researcher's name in a search snippet
                    # even when the full document cites them deep inside - e.g. a citation buried
                    # in a policy PDF's reference list. Only scraping reveals that. A full -4 here
                    # would bury exactly the citation evidence Fiona's review asked us to surface,
                    # so apply a much lighter penalty for trusted domains than for the open web.
                    score -= 1
                else:
                    score -= 4

            return score

        deduped = {}
        for result in results:
            link = result.get("link")
            if link and link not in deduped:
                deduped[link] = result

        ranked = sorted(deduped.values(), key=score_result, reverse=True)
        # Raise minimum threshold: previously 3, now 5 to filter low-signal results.
        # Fall back to unfiltered ranked list only when everything scores below the bar
        # (can happen for very niche queries where no result is ideal).
        filtered = [result for result in ranked if score_result(result) >= 5]
        return filtered or ranked

    def _is_near_duplicate_result(self, result: Dict) -> bool:
        """
        Catch results that re-report a story we've already kept under a different
        URL - e.g. the same press release or study syndicated across several news
        outlets/aggregators. Exact-URL dedup (processed_urls) doesn't catch this
        because each outlet publishes it at its own URL.

        Compares title tokens (falling back to title+snippet when the title is too
        short to be distinctive) against every signature accepted so far in this
        run, across all queries and tasks. Registers the result's own signature
        when it's novel, so later queries are compared against it too.
        """
        title_tokens = self._tokenize_for_matching(result.get("title", ""))
        tokens = title_tokens if len(title_tokens) >= 3 else self._tokenize_for_matching(
            " ".join([result.get("title", ""), result.get("snippet", "")])
        )
        if not tokens:
            return False

        for seen in self.seen_result_signatures:
            union = tokens | seen
            if union and len(tokens & seen) / len(union) >= 0.6:
                return True

        self.seen_result_signatures.append(tokens)
        return False

    def _passes_relevance_gate(self, use_case: ExtractedUseCase) -> bool:
        """Apply the configured REF relevance threshold after LLM relevance checks."""
        if not self.enable_relevance_check:
            return True
        score = use_case.relevance_score
        if score is None:
            return True
        # Previously hard-floored at 6 regardless of self.relevance_threshold,
        # which silently made an explicit caller-supplied lower threshold
        # (e.g. "show everything, don't filter by relevance") a no-op - fixed
        # so a threshold of 0 genuinely means "keep everything".
        is_underpinning_research = (
            (use_case.content_type or "").lower() == "peer_reviewed"
            and (use_case.use_case_type or "").strip().lower() == "underpinning research"
        )
        minimum_score = 6 if is_underpinning_research else max(0, int(round(self.relevance_threshold * 10)))
        passed = float(score) >= minimum_score
        label = use_case.use_case_name or "(unnamed)"
        if passed:
            print(f"[relevance gate] PASS  score={score}/{minimum_score}  {label[:60]}")
        else:
            print(f"[relevance gate] FAIL  score={score}/{minimum_score}  {label[:60]}")
        return passed

    def _record_relevance_outcome(self, passed: bool) -> None:
        """
        Keep admission telemetry.  A shortfall is useful evidence that more
        corroboration is needed; it must not lower quality requirements.
        """
        if passed:
            self._consecutive_relevance_rejections = 0
            return

        self._consecutive_relevance_rejections += 1

    _BLOCKED_SOURCE_DOMAINS = (
        "linkedin.com", "facebook.com", "instagram.com", "x.com", "twitter.com",
        "youtube.com", "tiktok.com", "medium.com", "reddit.com", "quora.com",
        "medicalxpress.com", "eurekalert.org", "prnewswire.com", "businesswire.com",
    )
    _TRUSTED_POLICY_DOMAINS = (
        "gov.uk", "parliament.uk", "legislation.gov.uk", "nhs.uk", "who.int",
        "nice.org.uk", "cqc.org.uk", "hse.gov.uk", "ons.gov.uk", "europa.eu",
        "ukri.org", "royalsociety.org", "cordis.europa.eu",
    )
    _TRUSTED_RESEARCH_DOMAINS = (
        "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "doi.org", "nature.com",
        "sciencedirect.com", "springer.com", "link.springer.com", "onlinelibrary.wiley.com",
        "bmj.com", "thelancet.com", "nejm.org", "jamanetwork.com", "plos.org",
        "frontiersin.org", "tandfonline.com", "academic.oup.com", "sagepub.com",
        "cambridge.org", "mdpi.com", "ieeexplore.ieee.org", "acm.org",
        "arxiv.org", "zenodo.org", "openalex.org", "crossref.org", "orcid.org",
    )
    _TRUSTED_NEWS_DOMAINS = (
        "bbc.co.uk", "bbc.com", "reuters.com", "ft.com", "theguardian.com",
        "thetimes.com", "telegraph.co.uk", "economist.com",
    )

    @staticmethod
    def _domain_matches(domain: str, trusted_domains: tuple[str, ...]) -> bool:
        return any(domain == item or domain.endswith("." + item) for item in trusted_domains)

    def _source_is_ref_trusted(self, use_case: ExtractedUseCase) -> bool:
        """Classify source *type*, without limiting evidence to a fixed allow-list.

        REF evidence can legitimately come from a specialist journal, a foreign
        regulator, a professional body, a project consortium, or a named
        beneficiary.  A finite domain list cannot cover these.  Instead, block
        only unsuitable source classes and require the extraction/validation
        stages to establish a credible, checkable publication category.
        """
        domain = (use_case.domain or urlparse(use_case.source or "").netloc).lower().removeprefix("www.")
        content_type = (use_case.content_type or "").lower()
        if not domain or self._domain_matches(domain, self._BLOCKED_SOURCE_DOMAINS):
            return False
        if self._is_aston_source(use_case.source or ""):
            return False
        if content_type in {"peer_reviewed", "policy", "news"}:
            # The credibility/relevance/outcome requirements are enforced
            # separately; these categories permit legitimate specialist
            # publishers without needing a finite domain allow-list.
            return True
        if content_type in {"press_release", "testimonial", "other"}:
            # An external partner's project announcement, a funder or
            # professional-body report, a conference proceeding, repository,
            # patent record, or a named beneficiary statement can all be
            # valuable REF corroboration.  They must still be attributable to
            # a real publisher or contain a checkable statement; the later
            # gate also requires credibility, relevance, and an outcome.
            return bool(use_case.publisher or use_case.direct_quote or use_case.source_reference)
        return False

    def _search_result_has_eligible_domain(self, url: str) -> bool:
        """Drop only sources that can never clear the gate before scraping.

        Unknown domains are retained for classification; a specialist good
        source should not be lost merely because it was absent from a list.
        """
        domain = (urlparse(url).netloc or "").lower().removeprefix("www.")
        if not domain or self._domain_matches(domain, self._BLOCKED_SOURCE_DOMAINS):
            return False
        if self._is_aston_source(url):
            return False
        return True

    def _passes_ref_evidence_gate(self, use_case: ExtractedUseCase) -> bool:
        """Apply non-negotiable quality gates without discarding usable evidence.

        Source category, relevance, credibility and a stated real-world outcome
        are hard requirements.  A verbatim quote and machine-detected
        reach/significance flags are evidence-completeness signals: pages often
        contain a valid source and metric but do not expose a short quote in
        the scraped text.  Treating those signals as deletion gates caused
        legitimate REF candidates to disappear entirely.
        """
        is_underpinning_research = (
            (use_case.content_type or "").lower() == "peer_reviewed"
            and (use_case.use_case_type or "").strip().lower() == "underpinning research"
        )
        requirements = {
            "trusted independent source": self._source_is_ref_trusted(use_case),
            "credibility score >= 7": (use_case.credibility_score or 0) >= 7,
            # Six is the documented relevance threshold.  A seventh point is
            # useful for ranking, but should not prevent a credible,
            # attributable publication or beneficiary source from appearing.
            "relevance score >= 6": (use_case.relevance_score or 0) >= 6,
        }
        if not is_underpinning_research:
            requirements["stated reach/significance outcome"] = bool(use_case.performance_impact)
        failures = [label for label, passed in requirements.items() if not passed]
        if failures:
            print(
                "[REF evidence gate] REJECT "
                f"{(use_case.use_case_name or '(unnamed)')[:80]} :: {', '.join(failures)}"
            )
            self._stream(
                "Excluded non-REF-ready finding: " + ", ".join(failures) + "."
            )
            return False

        completeness_gaps = []
        if not use_case.direct_quote:
            completeness_gaps.append("no verified verbatim quote")
        if not use_case.source_reference or use_case.source_reference == use_case.source:
            completeness_gaps.append("no specific source location")
        if getattr(use_case, "reach_verified", None) is False:
            completeness_gaps.append("reach needs reviewer verification")
        if getattr(use_case, "significance_verified", None) is False:
            completeness_gaps.append("significance needs reviewer verification")
        if completeness_gaps:
            note = "Evidence completeness: " + "; ".join(completeness_gaps) + "."
            use_case.credibility_reasoning = (
                f"{use_case.credibility_reasoning or ''} {note}".strip()
            )
            if hasattr(use_case, "id"):
                UseCase.objects.filter(id=use_case.id).update(
                    credibility_reasoning=use_case.credibility_reasoning
                )
            print(
                "[REF evidence gate] ACCEPT WITH REVIEW "
                f"{(use_case.use_case_name or '(unnamed)')[:80]} :: {note}"
            )
        return True

    # ────────────────────────── utils ──────────────────────────────

    def _track_llm_call(self, response) -> None:
        """
        Accumulate token usage from an LLM response so the run's real cost is
        visible in Report.metadata afterward instead of only on the OpenAI
        bill. `usage_metadata` is standard on ChatOpenAI responses; tolerate
        it being absent (e.g. a mocked/older client) rather than raising.
        """
        usage = getattr(response, "usage_metadata", None) or {}
        with self._token_usage_lock:
            self._token_usage["prompt_tokens"] += usage.get("input_tokens", 0) or 0
            self._token_usage["completion_tokens"] += usage.get("output_tokens", 0) or 0
            self._token_usage["total_tokens"] += usage.get("total_tokens", 0) or 0
            self._token_usage["calls"] += 1

    def _stream(self, msg: str, progress: float = None):
        """Stream a message with optional progress."""
        if self.report_obj:
            # Use report_id for the Pusher channel (must match frontend's expected channel)
            channel_key = f"use_cases_{self.report_id}" if self.report_id else f"use_cases_{self.theme_id}"
            self.pusher_service.stream_by_key(channel_key, msg, progress)

    def _stream_url_progress(self, url: str, current: int, total: int, stage: str = 'processing'):
        """Stream URL progress with shortened URL and clickable link."""
        if not self.report_obj:
            return
        message, progress = format_url_progress_message(url, current, total, stage)
        self._stream(message, progress)

    def _stream_task_progress(self, task_name: str, current: int, total: int, stage: str = 'processing'):
        """Stream task progress."""
        if not self.report_obj:
            return
        message, progress = format_task_progress_message(task_name, current, total, stage)
        self._stream(message, progress)

    def _stream_query_progress(self, query: str, current: int, total: int):
        """Stream query progress."""
        if not self.report_obj:
            return
        message, progress = format_query_progress_message(query, current, total)
        self._stream(message, progress)

    @staticmethod
    def _clean_llm(text: str) -> str:
        try:
            # strip Markdown fences (```)
            text = re.sub(r"^```[a-zA-Z]*|```$", "", text.strip(), flags=re.MULTILINE)

            replacements = {
                '\u2019': "'",  # right single quote
                '\u2018': "'",  # left single quote
                '\u201c': '"',  # left double quote
                '\u201d': '"',  # right double quote
                '\u2013': '-',  # en dash
                '\u2014': '--', # em dash
                '\u2026': '...',# ellipsis
            }
            for orig, repl in replacements.items():
                text = text.replace(orig, repl)
                
            return text.strip()
        except Exception as e:
            print(f"Error cleaning LLM text: {e}")
            return text

    @staticmethod
    def _extract_numeric_outcome(value: str) -> str:
        if not value:
            return ""
        matches = re.findall(r'[-+]?\d[\d,]*(?:\.\d+)?%?', value)
        return ", ".join(matches)

    _USE_CASE_DATE_PATTERN = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

    # REF-period windows/helpers live in report_generator_utils (shared with
    # UseCaseSerializer so the API/use-case browse view can show the same
    # in/out-of-period status per source as the final report, instead of it
    # only being computable at report-build time). Thin wrappers kept here
    # so existing call sites in this class don't need to change.
    IMPACT_PERIOD = _rgu_IMPACT_PERIOD
    RESEARCH_PERIOD = _rgu_RESEARCH_PERIOD

    _date_sort_key = staticmethod(_rgu_date_sort_key)
    _is_within_period = staticmethod(_rgu_is_within_period)

    @classmethod
    def _ref_period_for_use_case(cls, use_case: ExtractedUseCase) -> tuple:
        return _rgu_ref_period_for_content_type(getattr(use_case, "content_type", None))

    # URL fragments that indicate a personal/researcher profile page rather than
    # a primary evidence source.  Numeric claims on profile pages are almost
    # always synthesised by the LLM rather than quoted from the page itself.
    _PROFILE_URL_INDICATORS = [
        '/en/persons/', '/en/person/', '/people/', '/staff/', '/faculty/',
        'linkedin.com/in/', 'researchgate.net/profile', 'scholar.google',
        'orcid.org/', '/researchers/', '/author/',
        # Third-party "expert bureau" / media-pitching platforms - universities
        # and press offices pay to build these to pitch academics to journalists.
        # They read as independent because they're not aston.ac.uk, but they're
        # promotional content commissioned by the institution, not independent
        # reporting - same trust level as a staff profile page, not a news
        # article. Found via real data: 6 of 19 findings in one theme leaned on
        # expertfile.com alone, scoring full credibility (7-9) with no penalty.
        'expertfile.com', '/experts/',
    ]

    @classmethod
    def _is_profile_source(cls, url: str) -> bool:
        url_lower = url.lower()
        return any(ind in url_lower for ind in cls._PROFILE_URL_INDICATORS)

    @classmethod
    def _numeric_claims_verified(cls, performance_impact: str, page_text: str) -> bool:
        """Return True if every percentage figure in performance_impact appears
        in the scraped page text, or if there are no numeric claims at all."""
        if not performance_impact or not page_text:
            return True
        numbers = re.findall(r'\d+(?:\.\d+)?(?=%)', performance_impact)
        if not numbers:
            return True
        return any(n in page_text for n in numbers)

    # Matches text between a matching pair of straight quotes, single or
    # double. Minimum length avoids trivial matches like a lone number or
    # short label picked up incidentally (e.g. a section heading in quotes).
    _QUOTED_SPAN_PATTERN = re.compile(r"'([^']{15,})'|\"([^\"]{15,})\"")

    @classmethod
    def _extract_quoted_span(cls, text: str) -> Optional[str]:
        """Return the longest quoted substring in `text`, or None if there
        isn't one. Used to recover a verbatim quote the LLM embedded inside
        source_reference instead of the dedicated direct_quote field."""
        if not text:
            return None
        spans = [g1 or g2 for g1, g2 in cls._QUOTED_SPAN_PATTERN.findall(text)]
        if not spans:
            return None
        return max(spans, key=len).strip()

    # Matches the "Metadata:" marker regardless of surrounding whitespace.
    # Observed in practice in two shapes: SimpleHtmlScraper._clean_content's
    # own "\n\nMetadata:\nkey: value\n..." (one pair per line) when real body
    # text preceded it, AND a "Metadata: key: value key: value ..." single-line
    # form with no preceding blank lines at all when the page had no
    # extractable body text (JS-rendered/empty page) - a literal-string split
    # on the first form silently misses the second, letting a metadata-only
    # page's meta tags be treated as "visible" text. The regex catches both.
    _METADATA_BLOCK_PATTERN = re.compile(r"\n{0,2}Metadata:\s*\n?", re.IGNORECASE)

    @classmethod
    def _visible_page_text(cls, page_text: str) -> str:
        """
        Strip the "Metadata:" block SimpleHtmlScraper appends after the
        visible page text (meta description, og:*, twitter:* tag values -
        see SimpleHtmlScraper.py). A quote that only exists in that block is
        invisible to a human reading the rendered page - it's in the HTML
        <head>, used for social-media link previews, not the article body -
        so it isn't something a reviewer can "just go find and check" even
        though it's technically present in what was scraped. Quote
        verification must be checked against this visible-only text, not the
        full scraped text, or a metadata-only match would silently pass. If
        the page had no extractable body text at all, the metadata marker
        sits at position 0 and this correctly returns an empty string.
        """
        if not page_text:
            return page_text
        match = cls._METADATA_BLOCK_PATTERN.search(page_text)
        if not match:
            return page_text
        return page_text[:match.start()]

    @staticmethod
    def _normalize_for_quote_match(text: str) -> str:
        """Collapse whitespace and normalize quote glyphs so a verbatim quote
        can be substring-matched against scraped page text even when the LLM
        or the page uses different Unicode quote characters."""
        text = text.replace('’', "'").replace('‘', "'")
        text = text.replace('“', '"').replace('”', '"')
        text = text.replace('–', '-').replace('—', '--')
        return re.sub(r'\s+', ' ', text).strip().lower()

    @classmethod
    def _quote_verified(cls, direct_quote: Optional[str], page_text: str) -> bool:
        """
        Anti-hallucination guard for direct_quote, mirroring
        _numeric_claims_verified: a quote is only trustworthy if it actually
        appears (near-verbatim, after normalising whitespace/quote glyphs) in
        the scraped source text. Empty quotes are trivially fine - not every
        use case has one.
        """
        if not direct_quote:
            return True
        if not page_text:
            return False
        return cls._normalize_for_quote_match(direct_quote) in cls._normalize_for_quote_match(page_text)

    @staticmethod
    def _name_similarity(a: str, b: str) -> float:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

    _STOPWORDS = {
        "a", "an", "and", "the", "in", "of", "to", "for", "with", "by", "on",
        "at", "is", "was", "that", "this", "more", "than",
    }

    @classmethod
    def _token_similarity(cls, a: str, b: str) -> float:
        """Word-overlap (Jaccard) similarity. difflib's character-sequence
        ratio penalises whole-phrase reordering unfairly - e.g. 'Mechatherm
        International and Aston University introduced...' vs 'Aston
        University and Mechatherm International Limited developed...'
        describe the same fact but score under 0.7 on SequenceMatcher because
        entire phrases moved position. Comparing word sets instead is robust
        to the LLM rewording the same source differently on repeat extraction."""
        def tokens(s: str) -> set:
            words = re.findall(r"[a-z0-9]+", s.lower())
            return {w for w in words if w not in cls._STOPWORDS and len(w) > 1}
        ta, tb = tokens(a), tokens(b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    @classmethod
    def _claim_similarity(cls, a: str, b: str) -> float:
        """Best-of character- and token-level similarity between two use-case
        names, used to decide whether they describe the same underlying claim."""
        return max(cls._name_similarity(a, b), cls._token_similarity(a, b))

    @classmethod
    def _sanitize_use_case_date(cls, value: Optional[str], today_str: str) -> Optional[str]:
        """
        Reject use_case_date values the LLM should never have produced:
        - anything that isn't a plain YYYY[-MM[-DD]] string
        - anything dated today or later
        - YYYY-only or YYYY-MM in the current year (LLM defaulting to "this year/month")
        - YYYY-MM-DD where day is 01 and month is also 01 (year-padded default)
        - YYYY-MM-DD where day is 01 (month-padded default — strip to YYYY-MM)
        """
        if not value or not isinstance(value, str):
            return None
        value = value.strip()
        if not value or not cls._USE_CASE_DATE_PATTERN.match(value):
            return None
        if value >= today_str:
            return None
        current_year = today_str[:4]
        # YYYY-01-01 → YYYY (day and month were padded)
        if len(value) == 10 and value[4:] == '-01-01':
            value = value[:4]
        # YYYY-MM-01 → YYYY-MM (day was padded)
        elif len(value) == 10 and value[7:] == '-01':
            value = value[:7]
        # Reject vague current-year dates — LLM guessing "this year" or "this month"
        if value[:4] == current_year and len(value) <= 7:
            return None
        return value

    def _format_use_cases_for_ref_synthesis(self, use_cases: List[ExtractedUseCase]) -> str:
        evidence_items = []
        for index, use_case in enumerate(use_cases, 1):
            ref_num = getattr(use_case, "reference_number", None)
            evidence_items.append({
                "finding": index,
                "reference_number": ref_num,
                "impact_claim": use_case.use_case_name,
                "beneficiary_or_organisation": use_case.company,
                "impact_domain": use_case.performance_improvement_category,
                "impact_mechanism": use_case.use_case_type,
                "sector": use_case.industry,
                "underpinning_research_or_tool": use_case.tools,
                "impact_narrative": use_case.use_case_description,
                "reach_or_significance_metric": use_case.performance_impact,
                "date_or_timeframe": use_case.use_case_date,
                "source_published_date": use_case.published_date,
                "geography": use_case.geography,
                "country": use_case.country,
                "source": use_case.source,
                "source_type": use_case.source_type,
                "source_reference": use_case.source_reference,
                "source_citation": f"[{ref_num}]" if ref_num else "",
                "publisher": use_case.publisher,
                "content_type": use_case.content_type,
                "direct_quote": use_case.direct_quote,
                "credibility_score": use_case.credibility_score,
                "credibility_reasoning": use_case.credibility_reasoning,
                "relevance_score": use_case.relevance_score,
                "relevance_reasoning": use_case.relevance_reasoning,
            })
        return json.dumps(evidence_items, indent=2, ensure_ascii=True)

    def _format_researcher_affiliations(self, affiliation_records: List[ExtractedUseCase] | None = None) -> str:
        """Render researcher affiliation info for the synthesis prompt, from
        two sources:
        - CONFIRMED: the manually-supplied researcher_affiliations list (a
          human checked these dates).
        - found during search but not independently confirmed: affiliation_note
          text the extraction step pulled out of search results (LinkedIn,
          appointment announcements, prior-employer pages, etc. - never
          aston.ac.uk, same independence rule as everything else) when no
          manual entry was given for that researcher. This is what lets the
          report state an Aston attribution window automatically instead of
          requiring it to be typed in every time - but it's a lead the LLM
          should still flag as needing verification, not treat as confirmed.
        If neither source has anything, say so explicitly so the LLM doesn't
        invent an attribution window for anyone.
        """
        confirmed_names = set()
        lines = []
        for affiliation in self.researcher_affiliations:
            if not isinstance(affiliation, dict):
                continue
            if not (affiliation.get("aston_start") or affiliation.get("aston_end")):
                continue
            name = affiliation.get("name") or "an unnamed researcher"
            start = affiliation.get("aston_start") or "unknown start"
            end = affiliation.get("aston_end") or "present"
            confirmed_names.add(name.strip().lower())
            lines.append(f"- CONFIRMED: {name} was affiliated with Aston University from {start} to {end}.")

        for record in (affiliation_records or []):
            note = (record.affiliation_note or "").strip()
            if not note:
                continue
            # Skip if a human already confirmed this researcher's window -
            # the confirmed entry takes priority over an auto-discovered lead.
            name_guess = (record.use_case_name or "").replace("Institutional affiliation record:", "").strip()
            if name_guess.strip().lower() in confirmed_names:
                continue
            source = record.source or "an unlocated source"
            lines.append(
                f"- FOUND DURING SEARCH (not independently confirmed - state as a lead, not a fact): "
                f"\"{note}\" (source: {source})."
            )

        if not lines:
            return "(none supplied or found - do not assume an affiliation window for any named researcher; treat institutional attribution as unverified where relevant.)"
        return "\n".join(lines)

    def _build_ref_case_study_with_llm(
        self,
        use_cases: List[ExtractedUseCase],
        affiliation_records: List[ExtractedUseCase] | None = None,
    ) -> str:
        if not use_cases:
            return ""

        use_cases = sorted(
            use_cases,
            key=lambda uc: (float(uc.relevance_score or 0), float(uc.credibility_score or 0)),
            reverse=True,
        )
        self._assign_reference_numbers_to_use_cases(use_cases)
        section_config = json.dumps(self.impact_sections or [], indent=2, ensure_ascii=True)
        evidence = self._format_use_cases_for_ref_synthesis(use_cases)
        prompt = REF_CASE_STUDY_SYNTHESIS_PROMPT.format(
            user_prompt=self.user_prompt,
            theme_title=self.theme_title or "Impact Case Study Report",
            researcher_affiliations=self._format_researcher_affiliations(affiliation_records or []),
            impact_sections=section_config,
            impact_evidence=evidence,
        )
        try:
            response = self.llm_core.invoke(prompt)
            self._track_llm_call(response)
            synthesized = self._clean_llm(response.content)
            if synthesized and "## 4. Details of the Impact" in synthesized:
                synthesized = self._ensure_numbered_references_section(synthesized, use_cases)
                synthesized = self._reorder_numbered_section(synthesized, "## 3. References to the Research")
                synthesized = self._reorder_numbered_section(synthesized, "## 5. Sources to Corroborate the Impact")
                return synthesized
        except Exception as exc:
            print(f"REF synthesis failed, falling back to template: {exc}")

        return ""

    @staticmethod
    def _text_has_numbered_references(markdown: str) -> bool:
        return bool(re.search(r"(?m)^\s*\d+\.\s+\[.+?\]\(.+?\)", markdown or ""))

    def _build_numbered_reference_list_markdown(self, use_cases: List[ExtractedUseCase]) -> str:
        """Build a concise numbered source register for REF evidence checking."""
        if not use_cases:
            return "No references available.\n"

        self._assign_reference_numbers_to_use_cases(use_cases)
        seen_sources = {}
        for use_case in use_cases:
            if use_case.source and use_case.source not in seen_sources:
                ref_num = getattr(use_case, "reference_number", None) or len(seen_sources) + 1
                seen_sources[use_case.source] = (use_case, ref_num)

        if not seen_sources:
            return "No references available.\n"

        lines = []
        sorted_sources = sorted(seen_sources.items(), key=lambda item: item[1][1])
        for source_url, (use_case, ref_num) in sorted_sources:
            title = use_case.use_case_name or use_case.company or "Impact evidence source"
            source_type = use_case.source_type or "Source"
            source_ref = use_case.source_reference or source_url
            claim = use_case.performance_impact or use_case.use_case_description or "Impact claim"
            claim = re.sub(r"\s+", " ", claim).strip()
            if len(claim) > 240:
                claim = claim[:237].rstrip() + "..."

            if source_url.startswith(("http://", "https://")):
                source_link = f"[{escape(shorten_url(source_url))}]({escape(source_url)})"
            else:
                source_link = escape(source_url)

            date_text = escape(use_case.use_case_date) if use_case.use_case_date else "undated"
            if self._is_within_period(use_case.use_case_date, self._ref_period_for_use_case(use_case)) is False:
                date_text += " (outside REF period)"
            published_text = escape(use_case.published_date) if use_case.published_date else "undated"

            lines.append(
                f"{ref_num}. {source_link} - {escape(title)}. "
                f"Published: {published_text}. "
                f"Impact date: {date_text}. "
                f"Corroborates: {escape(claim)}. "
                f"Source type/location: {escape(source_type)}; {escape(source_ref)}."
            )

        return "\n".join(lines) + "\n"

    # Matches a numbered-list line whose bracketed link points at a URL, e.g.
    # "1. [Title](https://example.com) - why it supports research quality."
    # Captures (indent, old_number, rest-of-line-from-the-dot, url).
    _NUMBERED_REFERENCE_LINE_PATTERN = re.compile(
        r"(?m)^(\s*)(\d+)(\.\s+\[.*?\]\((https?://[^\s)]+)\).*)$"
    )

    def _ensure_numbered_references_section(self, markdown: str, use_cases: List[ExtractedUseCase]) -> str:
        """
        Reconcile the LLM's in-prose citation numbers (in "References to the
        Research" / "Sources to Corroborate the Impact") against the
        canonical reference_number assigned by
        _assign_reference_numbers_to_use_cases, so a reviewer never sees
        numbering in the narrative that disagrees with the appended
        References table. Pure string post-processing - no extra LLM call.
        """
        if not markdown or not use_cases:
            return markdown

        url_to_ref_num = {}
        for use_case in use_cases:
            ref_num = getattr(use_case, "reference_number", None)
            if use_case.source and ref_num:
                url_to_ref_num[use_case.source] = ref_num

        if not url_to_ref_num:
            return markdown

        def fix_line(match: "re.Match") -> str:
            indent, _old_num, rest, url = match.groups()
            correct_num = url_to_ref_num.get(url)
            if correct_num is None:
                return match.group(0)
            return f"{indent}{correct_num}{rest}"

        return self._NUMBERED_REFERENCE_LINE_PATTERN.sub(fix_line, markdown)

    _NUMBERED_ITEM_START_PATTERN = re.compile(r"^(\d+)\.\s+")
    # A line that is ONLY a bold group-subheading (e.g. "**Policy documents:**")
    # with no other content - the pattern the LLM uses when it groups sources
    # by evidence type, which breaks ascending numeric order the moment a
    # later-numbered item belongs to an earlier group.
    _BOLD_ONLY_HEADER_LINE_PATTERN = re.compile(r"^\s*\*\*[^*\n]+:?\*\*\s*$")

    @classmethod
    def _reorder_numbered_section(cls, markdown: str, heading: str) -> str:
        """
        Guarantee strictly ascending numeric order within one numbered-list
        section (e.g. "## 5. Sources to Corroborate the Impact"), regardless
        of how the LLM formatted it. The prompt instructs the LLM to never
        split sources into separate headed groups by evidence type because
        that breaks ascending order - but this has been observed to fail in
        practice even when explicitly instructed otherwise, so this is a
        hard guarantee rather than relying on prompt compliance alone.
        Only touches the section if it's actually out of order - a
        well-formed section (including any inline formatting) is returned
        untouched.
        """
        if not markdown or heading not in markdown:
            return markdown

        before, _, rest = markdown.partition(heading)
        next_heading_match = re.search(r"(?m)^##\s+\d", rest)
        if next_heading_match:
            section_body = rest[:next_heading_match.start()]
            after = rest[next_heading_match.start():]
        else:
            section_body = rest
            after = ""

        lines = section_body.split("\n")
        items: list[tuple[int, list[str]]] = []
        current: tuple[int, list[str]] | None = None
        first_item_index = None
        for i, line in enumerate(lines):
            m = cls._NUMBERED_ITEM_START_PATTERN.match(line)
            if m:
                if first_item_index is None:
                    first_item_index = i
                if current is not None:
                    items.append(current)
                current = (int(m.group(1)), [line])
            elif current is not None:
                if cls._BOLD_ONLY_HEADER_LINE_PATTERN.match(line):
                    continue  # drop a bare group-subheading between numbered items
                current[1].append(line)
        if current is not None:
            items.append(current)

        if len(items) < 2:
            return markdown

        numbers = [n for n, _ in items]
        if numbers == sorted(numbers):
            return markdown  # already in order - leave formatting/headers untouched

        intro = "\n".join(lines[:first_item_index]).rstrip() if first_item_index else ""
        items.sort(key=lambda item: item[0])
        reordered_body = "\n".join("\n".join(item_lines).rstrip("\n") for _, item_lines in items) + "\n"
        if intro:
            reordered_body = intro + "\n\n" + reordered_body

        return before + heading + "\n" + reordered_body + after

    # Stable, always-present anchor per REF_CASE_STUDY_SYNTHESIS_PROMPT's
    # required structure - used to split the draft narrative from the
    # reviewer commentary/caveats.
    _REF_READINESS_HEADING = "## 6. REF Readiness Assessment"
    _REF_COMMENTARY_SEPARATOR = "---\n\n# REF Readiness Commentary"

    @classmethod
    def _split_draft_and_commentary(cls, markdown: str) -> tuple[str, str]:
        """
        Split synthesized REF case study markdown into (draft, commentary) at
        the "REF Readiness Assessment" heading, so the flowing narrative and
        the gaps/caveats table can be displayed and exported separately
        instead of merged into one scrolling document (Fiona's review
        feedback). Returns ("", "") input as-is if the heading isn't present
        (e.g. the non-LLM template fallback has no such section).
        """
        if not markdown or cls._REF_READINESS_HEADING not in markdown:
            return markdown, ""
        draft, _, rest = markdown.partition(cls._REF_READINESS_HEADING)
        return draft.rstrip(), (cls._REF_READINESS_HEADING + rest).strip()

    def _build_impact_case_study_markdown(self, use_cases: List[ExtractedUseCase]) -> str:
        """Build narrative markdown format for impact case study reports."""
        # "Researcher Affiliation Record" entries are metadata used to
        # auto-populate the Aston-attribution language (see
        # _format_researcher_affiliations below) - they are not impact
        # evidence and must never appear as a reference, a numbered source,
        # or an "Impact Finding" in the report itself.
        affiliation_records = [uc for uc in use_cases if uc.use_case_type == "Researcher Affiliation Record"]
        use_cases = [uc for uc in use_cases if uc.use_case_type != "Researcher Affiliation Record"]

        synthesized_report = self._build_ref_case_study_with_llm(use_cases, affiliation_records)
        if synthesized_report:
            # The LLM's own "Sources to Corroborate the Impact" section (see
            # ref_prompts.py) is a numbered prose list, not a table - it is
            # not a duplicate of this compact references table, so it is
            # always appended.
            references_html = self._build_references_table_html(use_cases)
            draft, commentary = self._split_draft_and_commentary(synthesized_report)
            self._last_draft_section = draft + ("\n\n" + references_html if references_html else "")
            self._last_commentary_section = commentary
            if references_html:
                return synthesized_report + "\n\n" + references_html
            return synthesized_report

        # Assign hard-coded reference numbers to use cases
        self._assign_reference_numbers_to_use_cases(use_cases)

        markdown_content = []
        theme_title = self.theme_title or "Impact Case Study Report"
        
        # Executive Summary section
        markdown_content.append(f"# {theme_title}\n")
        markdown_content.append("## Executive Summary\n")
        
        credible_count = sum(1 for use_case in use_cases if use_case.is_credible)
        if use_cases:
            summary_text = (
                f"This draft REF impact case study draws on {len(use_cases)} extracted evidence item(s), "
                f"with {credible_count} marked as credible after validation. It summarises the claimed "
                f"beyond-academia benefits, identifies the strongest reach and significance evidence, "
                f"and flags where further corroboration is needed before REF submission."
            )
            markdown_content.append(f"{summary_text}\n")
        else:
            markdown_content.append("No impact findings were extracted for this report.\n")
        
        # Underpinning Research section
        markdown_content.append("## Underpinning Research\n")
        markdown_content.append(
            "The research underlying this impact has yielded critical insights that have "
            "significantly influenced practice and policy. This section synthesizes the key research findings:\n"
        )
        
        if use_cases:
            for i, use_case in enumerate(use_cases[:3], 1):  # Show first 3 for summary
                if use_case.use_case_name:
                    ref_num = getattr(use_case, "reference_number", None)
                    citation = f" [{ref_num}]" if ref_num else ""
                    markdown_content.append(f"\n**Research {i}: {escape(use_case.use_case_name)}**\n")
                    if use_case.company:
                        markdown_content.append(f"- Organization: {escape(use_case.company)}\n")
                    if use_case.use_case_date:
                        markdown_content.append(f"- Date: {escape(use_case.use_case_date)}\n")
                    if use_case.tools:
                        markdown_content.append(f"- Underpinning research/tool: {escape(use_case.tools)}{citation}\n")
                    if use_case.relevance_reasoning:
                        markdown_content.append(f"- REF relevance: {escape(use_case.relevance_reasoning)}{citation}\n")
        
        # References to the Research section
        markdown_content.append("\n## References to the Research\n")
        markdown_content.append(
            "These are the numbered research or research-quality sources currently available. "
            "Each item states why it helps establish research quality or attribution; weak evidence "
            "should be treated as a gap until confirmed by the academic lead:\n"
        )
        
        if use_cases:
            markdown_content.append("\n")
            markdown_content.append(self._build_numbered_reference_list_markdown(use_cases))
        
        # Details of the Impact section
        markdown_content.append("\n## Details of the Impact\n")
        markdown_content.append(
            "This section elucidates the pathways through which research has underpinned these impacts "
            "and examines the nature and extent of the influence:\n"
        )
        
        if use_cases:
            for i, use_case in enumerate(use_cases, 1):
                markdown_content.append(f"\n### Impact Finding {i}\n")
                markdown_content.append(f"**Title:** {escape(use_case.use_case_name or 'Untitled')}\n\n")
                ref_num = getattr(use_case, "reference_number", None)
                citation = f" [{ref_num}]" if ref_num else ""
                
                if use_case.company:
                    markdown_content.append(f"**Organization/Beneficiary:** {escape(use_case.company)}{citation}\n\n")
                
                if use_case.use_case_type:
                    markdown_content.append(f"**Impact Type:** {escape(use_case.use_case_type)}\n\n")
                
                if use_case.industry:
                    markdown_content.append(f"**Sector:** {escape(use_case.industry)}\n\n")
                
                if use_case.performance_impact:
                    outcome = self._extract_numeric_outcome(use_case.performance_impact)
                    markdown_content.append(f"**Reach/Significance Evidence:** {escape(outcome or use_case.performance_impact)}{citation}\n\n")
                
                if use_case.use_case_date:
                    markdown_content.append(f"**Timeframe:** {escape(use_case.use_case_date)}{citation}\n\n")
                
                if use_case.use_case_description:
                    markdown_content.append(f"**Impact Narrative:** {escape(use_case.use_case_description)}{citation}\n\n")
                
                if use_case.credibility_reasoning:
                    markdown_content.append(f"**Evidence Assessment:** {escape(use_case.credibility_reasoning)}{citation}\n\n")
        
        # Sources to Corroborate the Impact section
        markdown_content.append("\n## Sources to Corroborate the Impact\n")
        markdown_content.append(
            "The following external sources provide corroboration and supporting evidence for the impacts described:\n"
        )
        
        if use_cases:
            markdown_content.append("\n")
            markdown_content.append(self._build_numbered_reference_list_markdown(use_cases))
        
        # Summary of the Impact section
        markdown_content.append("\n## Summary of the Impact\n")
        if use_cases:
            sectors = list(dict.fromkeys(filter(None, [u.industry for u in use_cases if u.industry])))
            summary = (
                f"Across {len(use_cases)} documented finding(s), the evidence indicates potential impact in "
                f"{', '.join(sectors[:3]) if sectors else 'the selected beneficiary context'}. "
                f"{credible_count} finding(s) are currently marked credible. For REF use, the academic team "
                f"should verify attribution to Aston research, confirm beneficiary corroboration, and retain "
                f"the numbered evidence links below for audit."
            )
            markdown_content.append(f"{summary}\n")
        else:
            markdown_content.append("No impact findings available to summarize.\n")
        
        # References section - HTML table format with all links
        markdown_content.append("\n## References\n\n")
        if use_cases:
            references_html = self._build_references_table_html(use_cases)
            markdown_content.append(references_html)
        else:
            markdown_content.append("No references available.\n")
        
        return "".join(markdown_content)

    def _build_generated_report_html(self, use_cases: List[ExtractedUseCase]) -> str:
        """Build a REF-style HTML table from extracted use cases."""
        # For impact case studies, use markdown narrative format
        if self.report_type == "impact_case_study":
            return self._build_impact_case_study_markdown(use_cases)
        
        # Assign hard-coded reference numbers for non-impact-case-study reports as well
        self._assign_reference_numbers_to_use_cases(use_cases)
        
        rows = []
        for use_case in use_cases:
            source_url = use_case.source or ""
            verified = "Yes" if use_case.is_credible else ("No" if use_case.is_credible is False else "Unknown")
            notes = use_case.credibility_reasoning or use_case.relevance_reasoning or ""
            source_html = (
                f'<a href="{escape(source_url)}" target="_blank" rel="noopener noreferrer">{escape(source_url)}</a>'
                if source_url else ""
            )
            rows.append(
                "<tr>"
                f"<td>{escape(use_case.use_case_name or '')}</td>"
                f"<td>{escape(use_case.company or '')}</td>"
                f"<td>{escape(use_case.performance_improvement_category or use_case.use_case_type or '')}</td>"
                f"<td>{escape(use_case.industry or '')}</td>"
                f"<td>{escape(self._extract_numeric_outcome(use_case.performance_impact or ''))}</td>"
                f"<td>{escape(use_case.use_case_date or '')}</td>"
                f"<td>{source_html}</td>"
                f"<td>{escape(verified)}</td>"
                f"<td>{escape(notes)}</td>"
                "</tr>"
            )

        if not rows:
            rows.append(
                "<tr>"
                "<td colspan=\"9\">No verified impacts were extracted for this report.</td>"
                "</tr>"
            )

        theme_title = escape(self.theme_title or "Impact Report")
        credible_count = sum(1 for use_case in use_cases if use_case.is_credible)
        summary_html = ""
        if self.include_summary:
            summary_html = (
                "<div class=\"alert alert-info\">"
                f"<strong>REF evidence summary:</strong> {len(use_cases)} impact finding(s) extracted; "
                f"{credible_count} marked credible. Review all claims with the relevant academic lead and external corroborating source before REF submission."
                "</div>"
            )

        section_html = ""
        if self.impact_sections:
            section_rows = []
            for section in self.impact_sections:
                title = escape(str(section.get("title", "")))
                description = escape(str(section.get("description", "")))
                max_words = escape(str(section.get("maxWords", "")))
                section_rows.append(
                    "<tr>"
                    f"<td>{title}</td>"
                    f"<td>{description}</td>"
                    f"<td>{max_words}</td>"
                    "</tr>"
                )
            section_html = (
                "<h4>Configured REF case study sections</h4>"
                "<div class=\"table-responsive\">"
                "<table class=\"table table-sm table-bordered\">"
                "<thead><tr><th>Section</th><th>Purpose</th><th>Max words</th></tr></thead>"
                f"<tbody>{''.join(section_rows)}</tbody>"
                "</table>"
                "</div>"
            )

        # Generate References table HTML
        references_html = self._build_references_table_html(use_cases)
        
        return (
            f"<h3>{theme_title}</h3>"
            f"{summary_html}"
            f"{section_html}"
            "<h4>Extracted impact evidence</h4>"
            "<div class=\"table-responsive\">"
            "<table class=\"table table-striped table-bordered\">"
            "<thead><tr>"
            "<th>Title / Product name</th>"
            "<th>Organisation / Beneficiary</th>"
            "<th>Impact type</th>"
            "<th>Sector</th>"
            "<th>Quantitative outcome (numbers only)</th>"
            "<th>Dates / timeframe</th>"
            "<th>Source URL</th>"
            "<th>Verified?</th>"
            "<th>Notes / corrections</th>"
            "</tr></thead>"
            f"<tbody>{''.join(rows)}</tbody>"
            "</table>"
            "</div>"
            f"{references_html}"
        )

    def _assign_reference_numbers_to_use_cases(self, use_cases: List[ExtractedUseCase]) -> None:
        """
        Assign hard-coded reference numbers for this generated report.
        This keeps numbering stable in the output without changing existing database rows.
        """
        if not use_cases:
            return

        # Collect unique sources with their first occurrence use_case
        seen_sources = {}
        source_to_ref_number = {}

        for use_case in use_cases:
            if use_case.source and use_case.source not in seen_sources:
                seen_sources[use_case.source] = use_case

        # Number by a stable, human-predictable order (date, then domain, then
        # title) rather than the order use_cases happens to be in when this is
        # called - that order is usually a relevance/credibility-score sort,
        # which reshuffles reference numbers between runs even when the
        # underlying evidence hasn't changed. This is what produced the
        # out-of-order numbering flagged in review.
        ordered_sources = sorted(
            seen_sources.items(),
            key=lambda item: (
                self._date_sort_key(item[1].use_case_date),
                (item[1].domain or "").lower(),
                (item[1].use_case_name or "").lower(),
            ),
        )
        for ref_num, (source_url, _use_case) in enumerate(ordered_sources, 1):
            source_to_ref_number[source_url] = ref_num

        # Assign reference numbers to all use cases with this source
        for use_case in use_cases:
            if use_case.source and use_case.source in source_to_ref_number:
                ref_num = source_to_ref_number[use_case.source]
                setattr(use_case, "reference_number", ref_num)
                if hasattr(use_case, "id"):
                    try:
                        UseCase.objects.filter(id=use_case.id).update(reference_number=ref_num)
                    except Exception as exc:
                        print(f"Could not persist reference number for use case {use_case.id}: {exc}")

    def _build_references_table_html(self, use_cases: List[ExtractedUseCase]) -> str:
        """Build an HTML table for all references with hard-coded numbering."""
        if not use_cases:
            return ""
        
        # Collect unique sources with their assigned reference numbers
        seen_sources = {}  # Map of source -> (use_case, reference_number)
        for use_case in use_cases:
            if use_case.source and use_case.source not in seen_sources:
                ref_num = getattr(use_case, 'reference_number', None) or 0
                seen_sources[use_case.source] = (use_case, ref_num)
        
        if not seen_sources:
            return ""
        
        # If no reference numbers are assigned, assign them now
        has_unassigned = any(ref_num == 0 for _, ref_num in seen_sources.values())
        if has_unassigned:
            self._assign_reference_numbers_to_use_cases(use_cases)
            # Re-collect with updated numbers
            seen_sources = {}
            for use_case in use_cases:
                if use_case.source and use_case.source not in seen_sources:
                    ref_num = getattr(use_case, 'reference_number', None) or 0
                    seen_sources[use_case.source] = (use_case, ref_num)
        
        # Sort by reference number to ensure consistent ordering
        sorted_sources = sorted(seen_sources.items(), key=lambda x: x[1][1] if x[1][1] > 0 else float('inf'))
        
        reference_rows = []
        for source_url, (use_case, ref_num) in sorted_sources:
            # Use stored reference number if available, otherwise use position
            if ref_num > 0:
                display_num = ref_num
            else:
                display_num = len(reference_rows) + 1
            
            short_url = shorten_url(source_url)
            title = escape(use_case.use_case_name or "Research Evidence")
            quality = "Credible" if use_case.is_credible else "Needs Review"
            source_html = f'<a href="{escape(source_url)}" target="_blank" rel="noopener noreferrer">{escape(short_url)}</a>'
            corroborated_claim = use_case.performance_impact or use_case.use_case_description or ""
            corroborated_claim = re.sub(r"\s+", " ", corroborated_claim).strip()
            if len(corroborated_claim) > 240:
                corroborated_claim = corroborated_claim[:237].rstrip() + "..."

            date_cell = escape(use_case.use_case_date) if use_case.use_case_date else "Undated"
            if self._is_within_period(use_case.use_case_date, self._ref_period_for_use_case(use_case)) is False:
                date_cell += " &#9888; outside REF period"
            published_cell = escape(use_case.published_date) if use_case.published_date else "Undated"

            # Where in the source the claim/quote actually appears (page,
            # section, paragraph - see the source_reference field spec in
            # get_default_schema). Kept here in the reference table rather
            # than inline in the narrative prose, which reads more like a
            # normal REF case study without a location parenthetical breaking
            # up every other sentence - the table is where a reviewer expects
            # to look up exactly where to verify a claim anyway.
            has_specific_location = bool(
                use_case.source_reference and use_case.source_reference != use_case.source
            )
            location_cell = escape(use_case.source_reference) if has_specific_location else "Not recorded"
            if use_case.direct_quote:
                quote_cell = escape(f'"{use_case.direct_quote}"')
                location_cell = f"{location_cell}<br/><em>{quote_cell}</em>" if has_specific_location else quote_cell

            reference_rows.append(
                "<tr>"
                f"<td>{display_num}</td>"
                f"<td>{source_html}</td>"
                f"<td>{title}</td>"
                f"<td>{published_cell}</td>"
                f"<td>{date_cell}</td>"
                f"<td>{escape(corroborated_claim)}</td>"
                f"<td>{location_cell}</td>"
                f"<td>{quality}</td>"
                "</tr>"
            )

        return (
            "<h4>References</h4>"
            "<div class=\"table-responsive\">"
            "<table class=\"table table-striped table-bordered\">"
            "<thead><tr>"
            "<th>#</th>"
            "<th>Link</th>"
            "<th>Title</th>"
            "<th>Published</th>"
            "<th>Impact Date</th>"
            "<th>Claim corroborated</th>"
            "<th>Location in source</th>"
            "<th>Evidence Quality</th>"
            "</tr></thead>"
            f"<tbody>{''.join(reference_rows)}</tbody>"
            "</table>"
            "</div>"
        )

    def _compute_content_provenance(self, use_cases: List[ExtractedUseCase]) -> Dict:
        """
        Give an honest, countable answer to "how much of this is AI-written
        vs. pulled directly from sources" - not a fabricated percentage of
        the narrative text (which is entirely AI-synthesized prose grounded
        in this evidence), but a count of how much of the underlying
        evidence pool consists of verbatim, source-verified material: direct
        quotes (already checked against the scraped page text, see
        _quote_verified), quantitative figures, and specific page/section
        citation locations, versus items with no such verbatim anchor.
        """
        total = len(use_cases)
        with_quote = sum(1 for uc in use_cases if uc.direct_quote)
        with_metric = sum(1 for uc in use_cases if self._extract_numeric_outcome(uc.performance_impact or ""))
        with_specific_citation = sum(
            1 for uc in use_cases
            if uc.source_reference and uc.source_reference != uc.source
        )
        return {
            "total_evidence_items": total,
            "items_with_verbatim_quote": with_quote,
            "items_with_quantitative_metric": with_metric,
            "items_with_specific_citation_location": with_specific_citation,
            "note": (
                "The narrative prose (summary, pathway, significance analysis) is entirely "
                "AI-synthesized from the evidence below - it is not copied from any single source. "
                "The counts above show how much of the underlying evidence is anchored to "
                "verbatim, source-verified material (a direct quote, a specific figure, or an exact "
                "page/section location) rather than the AI's own paraphrase of a source."
            ),
        }

    def _save_generated_report(self, use_cases: List[ExtractedUseCase]) -> None:
        if not self.report_obj:
            return
        self._last_draft_section = ""
        self._last_commentary_section = ""
        generated_report = self._build_generated_report_html(use_cases)
        self.report_obj.generated_report = generated_report
        update_fields = ["generated_report", "updated_at"]
        if self.report_type == "impact_case_study" and (self._last_draft_section or self._last_commentary_section):
            # Keep the professional REF report first, then append reviewer
            # readiness commentary as a visibly separated section in the same
            # report document. Do not hide commentary in metadata.
            professional_report = self._last_draft_section or generated_report
            if self._last_commentary_section:
                self.report_obj.generated_report = (
                    professional_report
                    + "\n\n"
                    + self._REF_COMMENTARY_SEPARATOR
                    + "\n\n"
                    + self._last_commentary_section
                )
            else:
                self.report_obj.generated_report = professional_report
        self.report_obj.metadata["content_provenance"] = self._compute_content_provenance(use_cases)
        if "metadata" not in update_fields:
            update_fields.append("metadata")
        self.report_obj.save(update_fields=update_fields)

    def compile_from_existing_use_cases(self, use_cases: List["UseCase"]):
        """
        Build a report straight from `UseCase` rows that already exist in the
        database, skipping planning/search/scrape/extract entirely. `UseCase`
        model instances share the exact field names `_build_generated_report_html`
        reads from `ExtractedUseCase` (it mirrors the model), so no conversion
        is needed.
        """
        submitted_use_cases = list(use_cases)
        # Existing records may pre-date the strict admission gate.  Do not
        # allow them into a newly generated report merely because they were
        # saved in an earlier exploratory run.
        use_cases = [uc for uc in submitted_use_cases if self._passes_ref_evidence_gate(uc)]
        excluded = len(submitted_use_cases) - len(use_cases)
        self._stream(
            f"Compiling report from {len(use_cases)} REF-ready evidence item(s)"
            + (f"; excluded {excluded} legacy/insufficient item(s)." if excluded else "."),
            10,
        )
        if not use_cases:
            raise ValueError(
                "No REF-ready evidence was supplied. Add independently corroborated sources "
                "with a quoted, locatable reach and significance claim before compiling."
            )
        self._save_generated_report(use_cases)
        self._update_status('COMPLETED')
        # This path skips run()'s completion branches entirely, which is
        # where token/search usage otherwise gets persisted - without this,
        # a report compiled from existing use cases silently had no cost
        # data at all (not even zeros), unlike a full search run.
        self._persist_token_usage()
        self._stream("Report compiled successfully!", 100)
        return (self.report_obj.id if self.report_obj else None, use_cases)

    # ────────────────────────── graph builder ──────────────────────
    def _build_graph(self):
        g = StateGraph(GraphState)

        g.add_node("planning", self._planning_node())
        g.add_node("task_exec", self._task_exec())
        g.add_node("replan", self._replanning_node())
        g.add_edge("planning", "task_exec")
        g.add_conditional_edges(
            "task_exec",
            lambda s: "task_exec" if s["current_task_index"] < len(s["tasks"]) - 1 else self._route_after_tasks(s),
        )
        g.add_conditional_edges(
            "replan",
            lambda s: "task_exec" if s["current_task_index"] < len(s["tasks"]) else END,
        )
        g.set_entry_point("planning")
        return g

    def _route_after_tasks(self, state: "GraphState"):
        """
        Decide what happens once the current batch of planned tasks is exhausted.
        Keeps requesting additional, non-duplicate search rounds until either the
        requested number_of_outcomes is reached, or two consecutive rounds in a
        row fail to turn up any new qualifying references, or the replanning
        round cap is hit.
        """
        if self.pdf_uploaded or self._check_should_stop():
            return END
        if self.total_use_cases_created >= self.max_use_cases:
            return END
        if state.get("tasks_exhausted"):
            return END

        prior_round_start_count = state.get("replan_start_count")
        if prior_round_start_count is not None:
            if self.total_use_cases_created <= prior_round_start_count:
                state["stale_rounds"] = state.get("stale_rounds", 0) + 1
            else:
                state["stale_rounds"] = 0

            # Give it a second consecutive attempt before giving up - a single
            # unproductive round (e.g. a scrape failure) doesn't mean there are
            # no more new angles left to search.
            if state["stale_rounds"] >= 2:
                self._stream(
                    "No new qualifying references found in the last two search rounds; stopping with what was found.",
                )
                self._record_completeness("no_new_qualifying_evidence_after_two_rounds")
                return END

        if state.get("replanning_round", 0) >= self.max_replanning_rounds:
            self._record_completeness("replanning_round_cap_reached")
            return END

        if self._search_calls_total >= self.max_search_calls:
            self._stream(
                f"Reached this run's search budget ({self.max_search_calls} calls) with "
                f"{self.total_use_cases_created}/{self.max_use_cases} found; stopping to avoid "
                "excess API usage rather than continuing to chase the remaining count.",
            )
            self._record_completeness("search_call_budget_reached")
            return END

        state["replan_start_count"] = self.total_use_cases_created
        return "replan"

    # The UI's standard REF starter is often 50-120 words long but still only
    # contains a professor name, institution and generic instructions.  That
    # is not enough context to discover impact pathways, so treat it as a
    # starter rather than assuming that word count means it contains projects
    # or collaborators.
    _MINIMAL_PROMPT_WORD_THRESHOLD = 160

    def _maybe_enrich_minimal_prompt(self) -> None:
        """
        If self.user_prompt is too short to contain any named entities to
        anchor searches on, run one lightweight search+extract pass to
        discover the actual field, named grants/funders/projects/collaborators
        and notable media coverage, then fold that into self.user_prompt
        before planning runs. This is exactly the manual research-then-
        prompt-write step a human would otherwise have to do per academic (as
        was done by hand for the Maria Chli REF starter) - without it, a
        minimal prompt has nothing for the planner's named-entity anchoring
        rule to anchor on, and produces much weaker, less attributable
        results.

        Originally this only ran when a named *researcher* could be
        extracted, so a bare project/technology codename (e.g. "Khamsin")
        with no person's name in it silently skipped enrichment entirely -
        the ambiguous term went straight into search with nothing to
        disambiguate it from an unrelated same-named thing elsewhere on the
        web. Subjects now cover any anchorable named entity - person or
        project/technology/system name - not just people.

        Also guards against silently enriching with the *wrong* thing: if
        every search result for the subject fails to mention the institution
        at all, that is a strong signal the subject is ambiguous (the search
        API found a same-named but unrelated topic) rather than under-
        documented. In that case this stops short of writing a confident-
        sounding but possibly wrong background paragraph into the prompt,
        and instead surfaces an explicit warning so the run isn't silently
        poisoned - this matters most for a user who didn't write the prompt
        themselves and has no way to sanity-check it before searching.

        Mutates self.user_prompt in place. No-op if the prompt already looks
        detailed enough, nothing anchorable can be identified, the search API
        is unavailable, or nothing useful is found - never blocks the run.
        """
        if self.pdf_uploaded or self._search_api_unavailable:
            return
        word_count = len(re.findall(r"\S+", self.user_prompt or ""))
        if word_count == 0 or word_count > self._MINIMAL_PROMPT_WORD_THRESHOLD:
            return

        try:
            name_response = self.llm_check.invoke(
                "Extract the named subject(s) this text is about, and the institution, if any. "
                "A subject can be a named researcher/academic OR a named project, technology, "
                "system, product, or programme name - anything specific enough to search on. "
                "Respond with ONLY a JSON object: "
                '{"subjects": ["Name 1", ...], "institution": "..."}. '
                'If nothing specific is named, respond with {"subjects": [], "institution": ""}.\n\n'
                f"Text: {self.user_prompt}"
            )
            self._track_llm_call(name_response)
            parsed = json.loads(self._clean_llm(name_response.content))
            subjects = [s for s in parsed.get("subjects", []) if s][:3]  # cap cost
            institution = parsed.get("institution") or "Aston University"
        except Exception as exc:
            print(f"[prompt enrichment] Could not extract subject: {exc}")
            return

        if not subjects:
            return  # nothing to anchor an enrichment search on

        self._stream(
            f"Prompt looks minimal - researching {', '.join(subjects)} before planning searches..."
        )

        # Snippets are kept separate per subject so the Aston-mention check
        # below can tell "no results at all" apart from "results exist but
        # none of them are actually about the Aston version of this subject."
        subject_snippets: dict[str, list[str]] = {s: [] for s in subjects}
        for subject in subjects:
            for query in (
                f'"{subject}" {institution}',
                f'"{subject}" {institution} research project details',
            ):
                try:
                    results = self.search_api.run(query)
                    self._search_calls_total += 1
                except Exception:
                    self._search_calls_failed += 1
                    continue
                if not isinstance(results, list):
                    self._search_calls_failed += 1
                    continue
                for r in results[:3]:
                    snippet = (r.get("content") or r.get("snippet") or "").strip()
                    if snippet:
                        subject_snippets[subject].append(f"[{r.get('url', '')}] {snippet[:500]}")

        all_snippets = [s for snippets in subject_snippets.values() for s in snippets]
        if not all_snippets:
            return  # found nothing to enrich with - leave the prompt as-is

        # Disambiguation guard: a subject whose search results never once
        # mention the institution is very likely a name collision with an
        # unrelated topic (a different "Khamsin", etc.), not just a subject
        # with sparse web coverage. Drop those subjects' snippets from the
        # brief entirely rather than let the enrichment LLM confidently
        # summarise facts about the wrong thing, and warn so a user who
        # didn't write the prompt knows to add disambiguating context
        # (department, researcher name, field) before trusting the results.
        # Strip generic institution-type words before matching - "university"
        # alone appears in snippets about any unrelated university, which
        # would defeat the whole point of this check by passing almost
        # anything academic-flavoured rather than specifically Aston.
        _generic_institution_words = {"university", "college", "institute", "school", "of"}
        institution_tokens = (
            self._tokenize_for_matching(institution) - _generic_institution_words
        ) or {"aston"}
        confirmed_snippets: list[str] = []
        unconfirmed_subjects: list[str] = []
        for subject, snippets in subject_snippets.items():
            subject_confirmed = [
                s for s in snippets
                if self._tokenize_for_matching(s) & institution_tokens
            ]
            if subject_confirmed:
                confirmed_snippets.extend(subject_confirmed)
            elif snippets:
                unconfirmed_subjects.append(subject)

        if unconfirmed_subjects:
            self._stream(
                f"[WARNING] Could not confirm '{', '.join(unconfirmed_subjects)}' refers to "
                f"{institution} in any search result - this term may be ambiguous (a same-named "
                "but unrelated topic elsewhere on the web). Results for this run may be off-target; "
                "add the researcher's name, department, or field to the prompt for a reliable search."
            )

        if not confirmed_snippets:
            # Every subject failed the institution check - do not write an
            # enrichment paragraph built entirely from unconfirmed material.
            return

        try:
            enrichment_prompt = (
                "You are preparing a research background brief to seed REF impact case "
                "study searches. From the search snippets below, write:\n"
                "1. A 100-150 word paragraph summarising the actual field of expertise, named "
                "grants/funders, named projects/competitions, named collaborators/partners, and "
                "any notable named media coverage - only using facts actually present in the "
                "snippets, never invented or guessed.\n"
                "2. A bullet list of 5-10 specific named entities (grants, funders, "
                "projects, competitions, partner organisations, media outlets) to anchor "
                "future search queries on - at least one of these should appear in every "
                "search query.\n"
                "If the snippets don't support a claim, omit it rather than guessing - an "
                "incomplete but accurate brief is better than a fabricated one. Every snippet "
                "below has already been confirmed to mention the institution, so you do not "
                "need to re-check that - just do not introduce any fact that isn't in them.\n\n"
                f"Subject(s): {', '.join(subjects)}\n"
                f"Institution: {institution}\n\n"
                "Search snippets:\n" + "\n\n".join(confirmed_snippets[:12])
            )
            enrichment_response = self.llm_check.invoke(enrichment_prompt)
            self._track_llm_call(enrichment_response)
            enrichment_text = self._clean_llm(enrichment_response.content).strip()
        except Exception as exc:
            print(f"[prompt enrichment] Could not build enrichment brief: {exc}")
            return

        if enrichment_text:
            self.user_prompt = f"{self.user_prompt}\n\n{enrichment_text}"
            self._stream("Enriched the prompt with background before planning.")

    # ────────────────────────── planning ───────────────────────────
    def _planning_node(self):
        def plan(state: GraphState):
            if self._check_should_stop():
                return state

            # Generate use case types first
            self._stream_task_progress('Planning', 1, 1, 'generating use case types')
            use_case_types = self.get_use_case_type_options()
            print(f"[_planning_node] Generated use case types: {use_case_types}")

            if self.pdf_uploaded:
                state.update(
                    tasks=[{
                        "task_id": str(uuid4()),
                        "task_name": "Extract quantitative PDF impacts",
                        "search_queries": [],
                    }],
                    current_task_index=0,
                    thoughts=["planned"],
                    use_cases=[],
                    use_case_types=use_case_types,
                )
                self._update_status('RUNNING', {'current': 0, 'total': 1})
                self._stream_task_progress('Planning', 1, 1, 'completed')
                return state

            self._maybe_enrich_minimal_prompt()

            # self.max_tasks is already derived from the chosen search complexity
            # (see _map_complexity_to_params); re-deriving a second, lower cap here
            # from max_use_cases // 2 used to silently override "complex"/"advanced"
            # complexity back down to the same task count as "simple"/"medium".
            max_tasks_to_plan = max(1, self.max_tasks)

            prompt = self.planning_prompt.format(
                user_prompt=self.user_prompt,
                max_tasks=1 if self.debug else max_tasks_to_plan,
                today=datetime.now().strftime("%Y-%m-%d"),
                theme_title=self.theme_title or "General"
            )
            self._stream_task_progress('Planning', 1, 1, 'planning tasks')
            planning_response = self.llm_core.invoke(prompt)
            self._track_llm_call(planning_response)
            raw = planning_response.content

            if self._check_should_stop():
                return state

            try:
                planning_result: Dict = json.loads(self._clean_llm(raw))
            except json.JSONDecodeError:
                print(f"Error parsing planning response: {raw}")
                return state
            
            tasks_raw: List[Dict] = planning_result.get("tasks", [])

            if self.debug:
                tasks_raw = tasks_raw[:1]

            self._all_used_focus_areas.update(
                t.get("focus_area", "").strip() for t in tasks_raw if t.get("focus_area")
            )

            state.update(
                tasks=[{"task_id": str(uuid4()), **t} for t in tasks_raw],
                current_task_index=0,
                thoughts=["planned"],
                use_cases=[],
                use_case_types=use_case_types,
            )

            task_count = len(state['tasks'])

            self._update_status('RUNNING', {'current': 0, 'total': task_count})
            print(f"Created {task_count} task(s)")
            print(f"Tasks: {state['tasks']}")

            self._stream_task_progress('Planning', 1, task_count, 'completed')
            return state
        return plan

    # ────────────────────────── replanning (extra search rounds) ────
    def _replanning_node(self):
        def replan(state: GraphState):
            if self._check_should_stop():
                return state

            if self._search_api_unavailable:
                # Don't spend an OpenAI planning call proposing new search
                # tasks against a search API that has already failed
                # repeatedly this run - that's how a single outage turns into
                # dozens of pointless replanning rounds.
                state["tasks_exhausted"] = True
                self._record_completeness("search_api_unavailable")
                return state

            remaining = self.max_use_cases - self.total_use_cases_created
            round_num = state.get("replanning_round", 0) + 1
            state["replanning_round"] = round_num

            self._stream(
                f"Only {self.total_use_cases_created}/{self.max_use_cases} qualifying references found so far. "
                f"Searching for {remaining} more (extra round {round_num}/{self.max_replanning_rounds})..."
            )

            new_task_count = max(1, min(self.max_tasks, remaining))
            avoid_queries = sorted(self._all_used_queries)[-60:]  # keep the prompt a sane size
            avoid_focus_areas = sorted(self._all_used_focus_areas)

            prompt = self.planning_prompt.format(
                user_prompt=self.user_prompt,
                max_tasks=new_task_count,
                today=datetime.now().strftime("%Y-%m-%d"),
                theme_title=self.theme_title or "General",
            )
            # A follow-up round is chasing a narrow remaining gap, not broad
            # initial coverage, so it doesn't need the base prompt's full
            # 8-12-queries-per-task fan-out - that was the single biggest
            # driver of runaway Tavily usage on hard-to-search topics (a
            # 5-task, 8-12-query round costs 40-60 calls each, and multiple
            # rounds compound fast). Shrink further in later rounds, since by
            # then the easy evidence has typically already been found.
            queries_per_task = 6 if round_num <= 2 else 4
            # Temporal funnel: stay recent-first while it's still working, then
            # explicitly widen once recent angles are exhausted, rather than
            # repeating "last 1-2 years" queries round after round with
            # diminishing returns once the recent evidence pool is used up.
            recency_instruction = (
                "Keep prioritising the last 1-2 years first, same as the base instructions - "
                "recent evidence is still the priority this round."
                if round_num <= 2 else
                "Recent-only queries have had two rounds to work - this round, deliberately widen "
                "beyond the last 1-2 years to 3-5+ years back (still within REF-eligible windows) "
                "since the recent evidence pool for this topic is likely exhausted."
            )
            prompt += (
                "\n\nIMPORTANT - THIS IS A FOLLOW-UP SEARCH ROUND:\n"
                f"We still need {remaining} more qualifying, REF-relevant findings to reach the requested "
                f"total of {self.max_use_cases}. Use {queries_per_task} search queries per task this round, "
                f"not the 8-12 the base instructions above mention - this follow-up round is narrower and "
                f"more targeted than the initial pass, so it doesn't need that much breadth per task. "
                f"{recency_instruction} "
                "Do NOT repeat any of these already-attempted search queries, "
                "and do not submit paraphrases of them either - a reworded version of an already-attempted "
                "query will surface the same articles:\n"
                f"{json.dumps(avoid_queries)}\n"
                "These focus areas have already been explored in earlier rounds - pick NEW ones, not "
                "variations on them:\n"
                f"{json.dumps(avoid_focus_areas)}\n"
                "Propose genuinely new angles not covered above: different beneficiary types, sectors, "
                "geographies, organisations, time periods, or phrasing."
            )

            replanning_response = self.llm_core.invoke(prompt)
            self._track_llm_call(replanning_response)
            raw = replanning_response.content
            if self._check_should_stop():
                return state

            try:
                planning_result: Dict = json.loads(self._clean_llm(raw))
            except json.JSONDecodeError:
                print(f"Error parsing replanning response: {raw}")
                state["tasks_exhausted"] = True
                self._record_completeness("replanning_response_unparseable")
                return state

            new_tasks_raw: List[Dict] = planning_result.get("tasks", [])
            if not new_tasks_raw:
                state["tasks_exhausted"] = True
                self._record_completeness("replanning_produced_no_new_tasks")
                return state

            self._all_used_focus_areas.update(
                t.get("focus_area", "").strip() for t in new_tasks_raw if t.get("focus_area")
            )

            new_tasks = [{"task_id": str(uuid4()), **t} for t in new_tasks_raw]
            state["tasks"] = state["tasks"] + new_tasks

            self._update_status('RUNNING', {
                'current': state["current_task_index"],
                'total': len(state["tasks"]),
            })
            print(f"[replan round {round_num}] Added {len(new_tasks)} more task(s); total tasks now {len(state['tasks'])}")
            return state
        return replan

    # ────────────────────────── sub‑graph per task ─────────────────
    def _task_exec(self):
        sub = StateGraph(GraphState)
        sub.add_node("search",  self._search_node())
        sub.add_node("scrape",  self._scrape_node())
        sub.add_node("extract", self._extract_node())

        sub.set_entry_point("search")
        sub.add_edge("search", "scrape")
        sub.add_edge("scrape", "extract")
        sub.add_edge("extract", END)
        task_graph = sub.compile()

        def exec_task(state: GraphState):
            if self._check_should_stop():
                self._stream_task_progress(state['tasks'][state['current_task_index']]['task_name'], state['current_task_index'] + 1, len(state['tasks']), 'completed')
                self._update_status('STOPPED')
                return state
            
            # Skip remaining tasks if max impacts reached (save API calls)
            if self.total_use_cases_created >= self.max_use_cases:
                self._stream(f"Maximum of {self.max_use_cases} impacts reached. Skipping remaining tasks.", 95)
                state["current_task_index"] = len(state["tasks"])
                self._update_status('RUNNING', {
                    'current': len(state["tasks"]),
                    'total': len(state["tasks"])
                })
                return state

            task_state = {
                **state,
                "search_results": {},
                "scraped_pages": [],
                "page_contents": {},
                "use_case_types": state.get("use_case_types", []),
            }
            out = task_graph.invoke(task_state,{"recursion_limit": self.recursion_limit})
            state["current_task_index"] += 1
            state["use_cases"] = out["use_cases"]
            state["use_case_types"] = out.get("use_case_types", state.get("use_case_types", []))

            # Update progress only when a new task is done
            self._update_status('RUNNING', {
                'current': state["current_task_index"],
                'total': len(state["tasks"])
            })

            return state
        return exec_task

    # ────────────────────────── search ─────────────────────────────
    def _search_node(self):
        def search(state: GraphState):
            if self._check_should_stop():
                return state
            
            # Skip search entirely if PDF is uploaded - only extract from PDF
            if self.pdf_uploaded:
                self._stream("PDF-only mode: Skipping web search. All findings will be extracted from the uploaded PDF.", 15)
                state["search_results"] = {}
                return state
            
            # Skip search if max impacts already reached (save API calls)
            if self.total_use_cases_created >= self.max_use_cases:
                self._stream(f"Maximum of {self.max_use_cases} impacts reached. Skipping search.", 90)
                return state

            task = state["tasks"][state["current_task_index"]]
            task_num = state["current_task_index"] + 1
            total_tasks = len(state["tasks"])
            queries = task["search_queries"]
            self._all_used_queries.update(queries)

            # Stream task start with progress
            self._stream_task_progress(
                task.get('task_name', 'Search'),
                task_num,
                total_tasks,
                'starting'
            )

            # Get already processed URLs for this theme
            processed_urls = set()
            if self.skip_processed_urls and self.theme_id:
                from content.models import UseCase
                processed_urls = set(UseCase.objects.filter(theme_id=self.theme_id).values_list('source', flat=True))

            results: Dict[str, List[Dict]] = {}

            # Skip the whole batch up front if we already know it's pointless -
            # cheaper than dispatching a pool of calls that will all fail/be skipped.
            if self.total_use_cases_created >= self.max_use_cases:
                self._stream(f"Maximum of {self.max_use_cases} impacts reached. Skipping remaining queries.", 92)
                state["search_results"] = {q: [] for q in queries}
                return state
            if self._search_api_unavailable:
                state["search_results"] = {q: [] for q in queries}
                return state

            # Never launch more concurrent calls than the run has left in its
            # global budget.  Previously a task could dispatch 8-12 calls at
            # once after the budget had nearly been exhausted, overshooting the
            # stated limit before _route_after_tasks had a chance to stop it.
            remaining_search_budget = max(0, self.max_search_calls - self._search_calls_total)
            active_queries = (queries[:1] if self.debug else queries)[:remaining_search_budget]
            if not active_queries:
                state["search_results"] = {q: [] for q in queries}
                return state

            def _run_query(q: str):
                try:
                    data = self.search_api.run(q)
                    if not isinstance(data, list):
                        # Some search wrappers (e.g. langchain_community's
                        # TavilySearchResults) catch their own HTTP errors and
                        # return the exception's string representation as the
                        # "result" instead of raising - iterating that string
                        # yields single characters, which fail confusingly on
                        # r.get(...). Raise explicitly with the real cause instead.
                        raise TypeError(
                            f"Search API returned a non-list response, indicating an "
                            f"upstream failure rather than zero results: {str(data)[:200]}"
                        )
                    return q, data, None
                except Exception as e:
                    return q, None, e

            # Queries within a task are independent of each other, so run them
            # concurrently instead of one Tavily call at a time - with 8-12
            # queries per task, this was the single biggest sequential cost in
            # the whole pipeline. Bounded at 8 concurrent calls, matching the
            # extraction pool below, to stay under typical per-account rate
            # limits. Ranking/dedup/failure-bookkeeping still happen afterward,
            # in query order, so behaviour there is unchanged.
            # Four concurrent searches retain most of the latency benefit
            # without needlessly provoking provider rate limits.
            with ThreadPoolExecutor(max_workers=min(4, len(active_queries))) as pool:
                query_results = list(pool.map(_run_query, active_queries))

            for i, (q, data, error) in enumerate(query_results, 1):
                if self._check_should_stop():
                    return state

                self._search_calls_total += 1
                self._stream_query_progress(q, i, len(active_queries))

                if error is not None:
                    self._search_calls_failed += 1
                    self._consecutive_search_failures += 1
                    error_msg = str(error)
                    self._record_tavily_search_denial(error)
                    self._last_search_error = error_msg
                    print(f"Search error for [{q}]: {error}")
                    # Surface the failure to the UI (deduped so the same error doesn't spam every query)
                    if error_msg not in self._streamed_search_errors:
                        self._streamed_search_errors.add(error_msg)
                        self._stream(f"Web search request failed: {error_msg[:300]}")
                    if self._consecutive_search_failures >= self._SEARCH_FAILURE_THRESHOLD:
                        self._search_api_unavailable = True
                        self._stream(
                            f"Search API has failed {self._consecutive_search_failures} times in a row "
                            "(likely rate-limited or down) - stopping further search attempts and "
                            "replanning rounds for this run rather than continuing to retry it.",
                            90,
                        )
                    results[q] = []
                    continue

                self._consecutive_search_failures = 0
                transformed = [{
                    "title": r.get("title", ""),
                    "link":  r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "source": r.get("source", ""),
                } for r in data if not self.skip_processed_urls or r.get("url") not in processed_urls][:1 if self.debug else self.max_results]
                ranked = self._rank_search_results(q, transformed)
                # Drop results that re-report a story we've already picked up under a
                # different URL, so near-duplicate queries don't pad the run with the
                # same evidence under different links.
                ranked = [r for r in ranked if not self._is_near_duplicate_result(r)]
                # Do not spend scraping/LLM time on a source that cannot be
                # REF-ready under the admission policy.
                ranked = [r for r in ranked if self._search_result_has_eligible_domain(r.get("link", ""))]
                results[q] = ranked[:1 if self.debug else self.max_results]

            for q in queries:
                if q not in results:
                    results[q] = []

            state["search_results"] = results
            return state
        return search

    # ────────────────────────── scrape ─────────────────────────────
    def _scrape_node(self):
        def scrape(state: GraphState):
            if self._check_should_stop():
                return state
            
            # Skip scraping if max use cases already reached
            if self.total_use_cases_created >= self.max_use_cases:
                self._stream(f"Maximum of {self.max_use_cases} impacts already reached. Skipping further scraping.", 90)
                state["scraped_pages"] = []
                return state

            urls: list[str] = []
            # max_links is a per-task budget, not a per-query budget.  The old
            # loop could scrape max_links for *every* query, multiplying a
            # nominal 40-link run into hundreds of pages.
            task_link_limit = min(self.max_links, max(12, self.max_use_cases * 4))
            for docs in state["search_results"].values():
                if self._check_should_stop():
                    return state
                for d in docs:
                    if len(urls) >= task_link_limit:
                        break
                    if d["link"] and d["link"] not in self.processed_urls:
                        urls.append(d["link"])
                        self.processed_urls.add(d["link"])
                if len(urls) >= task_link_limit:
                    break

            task_num = state["current_task_index"] + 1
            total_tasks = len(state["tasks"])

            if not urls:
                state["scraped_pages"] = []
                self._stream_task_progress(
                    'Scraping',
                    task_num,
                    total_tasks,
                    'completed'
                )
                return state

            # Create a queue for results
            results = {}
            
            # Process URLs in batches. Fetching is pure network I/O with no
            # shared state between pages, so a higher batch size is safe here
            # (raised from 5 - the old value serialised scraping into far more
            # round-trips than the network work actually required).
            batch_size = 15
            for i in range(0, len(urls), batch_size):
                if self._check_should_stop():
                    return state
                    
                batch_urls = urls[i:i + batch_size]
                batch_tasks = []
                
                for url in batch_urls:
                    task = _ScrapeTask(url, self.scraper)
                    batch_tasks.append(task.run())
                
                # Create a new event loop for this batch
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Stream URL processing progress
                    for j, url in enumerate(batch_urls, 1):
                        self._stream_url_progress(
                            url,
                            i + j,
                            len(urls),
                            'scraping'
                        )
                    
                    # Run the batch of tasks
                    batch_results = loop.run_until_complete(asyncio.gather(*batch_tasks))
                    
                    # Process results
                    for url, title, text in batch_results:
                        if text:
                            results[url] = {"url": url, "title": title, "text": text}
                            state["page_contents"][url] = text
                            if self.report_obj:
                                try:
                                    ScrapedURL.objects.update_or_create(
                                        report=self.report_obj,
                                        url=url,
                                        defaults={"title": title, "content": text},
                                    )
                                except Exception as exc:
                                    print(f"Could not save scraped URL {url}: {exc}")
                            
                except Exception as e:
                    print(f"Error during batch scraping: {str(e)}")
                finally:
                    try:
                        # Clean up the event loop
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        loop.close()
                    except Exception as e:
                        print(f"Error closing event loop: {str(e)}")

            state["scraped_pages"] = list(results.values())
            return state
        return scrape

    # ────────────────────────── extract ────────────────────────────
    def _check_credibility_and_relevance(self, use_case: ExtractedUseCase, page_content: str) -> None:
        """
        Check credibility and relevance for a single use case with a single
        combined LLM call (REF_CREDIBILITY_RELEVANCE_CHECK_PROMPT). This used
        to be two separate calls on the same context - merging them halves
        the number of API calls/tokens spent here, since this runs once per
        every extracted candidate, not just accepted ones.
        """
        if not self.enable_credibility_check and not self.enable_relevance_check:
            return

        if self._check_should_stop():
            self._update_status('STOPPED')
            return

        # This check only needs enough surrounding context to judge the use
        # case, not the entire page - this was a significant source of token
        # usage since it duplicated the full extraction prompt again per use case.
        page_content = page_content[:4000] if page_content else page_content

        prompt = REF_CREDIBILITY_RELEVANCE_CHECK_PROMPT.format(
            theme_title=self.theme_title or "General",
            user_prompt=self.user_prompt,
            article=page_content,
            use_case=json.dumps(use_case.to_dict(), ensure_ascii=False),
        )
        try:
            response = self.llm_check.invoke(prompt)
            self._track_llm_call(response)
            raw = response.content
        except Exception as e:
            err = str(e)
            self._stream(f"[ERROR] AI credibility/relevance check failed: {err[:200]}")
            print(f"[check_credibility_and_relevance] Exception: {e}")
            return

        print(f"[_check_credibility_and_relevance] LLM returned: {raw[:200]}")
        clean = self._clean_llm(raw)

        try:
            result = json.loads(clean)
        except json.JSONDecodeError:
            print(f"Error parsing credibility/relevance response: {clean}")
            return

        update_fields = {}
        if self.enable_credibility_check:
            use_case.credibility_score = result.get("credibility_score")
            use_case.is_credible = result.get("is_credible")
            use_case.credibility_reasoning = result.get("credibility_reasoning")
            update_fields.update(
                credibility_score=use_case.credibility_score,
                is_credible=use_case.is_credible,
                credibility_reasoning=use_case.credibility_reasoning,
            )
        if self.enable_relevance_check:
            use_case.relevance_score = result.get("relevance_score")
            use_case.is_relevant = result.get("is_relevant")
            use_case.relevance_reasoning = result.get("relevance_reasoning")
            update_fields.update(
                relevance_score=use_case.relevance_score,
                is_relevant=use_case.is_relevant,
                relevance_reasoning=use_case.relevance_reasoning,
            )

        # These are transient admission flags rather than database fields. They
        # decide whether a candidate becomes a final evidence record; the
        # persisted quote, scores and reasoning explain the decision to users.
        use_case.reach_verified = result.get("reach_verified") is True
        use_case.significance_verified = result.get("significance_verified") is True

        if update_fields and hasattr(use_case, 'id'):
            UseCase.objects.filter(id=use_case.id).update(**update_fields)


    def get_use_case_type_options(self):
        """Return a list of distinct use_case_type values for the current theme, or sensible defaults."""
        if self.theme_id:
            from content.models import UseCase
            options = list(
                UseCase.objects.filter(theme_id=self.theme_id)
                .exclude(use_case_type__isnull=True)
                .exclude(use_case_type="")
                .values_list('use_case_type', flat=True)
                .distinct()
            )
            if options:
                # Use LLM to enhance the existing types
                enhanced_options = generate_use_case_types_with_llm(
                    user_prompt=self.user_prompt,
                    theme_title=self.theme_title or "General",
                    existing_types=sorted(set(options))
                )
                return enhanced_options
        
        # Fallback for SDLC themes
        if self.theme_title and 'SDLC' in self.theme_title.upper():
            return [
                "Requirements Engineering",
                "Design",
                "Development",
                "Testing",
                "Deployment",
                "Maintenance & Operations"
            ]

        return [
            "Policy Influence",
            "Clinical Adoption",
            "Professional Practice Change",
            "Industry Adoption",
            "Public Engagement",
            "Community Benefit",
            "Environmental Benefit",
            "Economic Benefit",
            "Cultural Benefit",
            "Education or Learning Benefit"
        ]

    # Same-source pairs are now an unconditional duplicate (see Quality gate 2
    # in _extract_node) rather than a threshold - two extractions from the
    # identical URL are always a re-extraction of the same fact.
    # Different outlets substantially reword the same underlying impact.
    # 0.82 was too strict and allowed those repetitions into the table.
    _CROSS_SOURCE_DEDUP_THRESHOLD = 0.65

    def _get_or_create_use_case(self, theme_id, uc):
        """
        Three-level deduplication within a theme:

        1. Same source → consolidate into one evidence row.
        2. Cross-source fuzzy claim match (>65%) → same claim found via a
           different URL on a subsequent run; update the better-scoring row
           rather than creating a duplicate.

        A page can mention several benefits, but it is still one evidence
        item. Consolidating it prevents one source appearing as multiple
        apparently independent statements.

        Returns (use_case_row, is_new).
        """
        new_data = uc.to_dict()
        # ExtractedUseCase.theme is dead weight - nothing in the extraction
        # flow ever sets it, so it's always None, but to_dict() includes it
        # anyway. Left in place, it flows into UseCase.objects.create()/
        # .update() alongside the correct theme_id kwarg below; drop it so
        # the real theme_id is never at risk of being shadowed.
        new_data.pop("theme", None)
        source = new_data.get("source")
        name = new_data.get("use_case_name", "")

        existing = None
        if source:
            # One source is one evidence item. Later extractions of the same
            # URL merge into the earliest row rather than creating variants.
            qs = UseCase.objects.filter(source=source, theme_id=theme_id)
            existing = qs.order_by('created_at', 'id').first()

        # Level 3: cross-source fuzzy claim match — same claim, different URL
        if not existing and name:
            cross_qs = UseCase.objects.filter(theme_id=theme_id)
            if source:
                cross_qs = cross_qs.exclude(source=source)
            for candidate in cross_qs:
                if (candidate.use_case_name
                        and self._claim_similarity(name, candidate.use_case_name)
                        > self._CROSS_SOURCE_DEDUP_THRESHOLD):
                    sim = self._claim_similarity(name, candidate.use_case_name)
                    print(f"[dedup] CROSS-URL {sim:.0%}  ID {candidate.id}  "
                          f"'{(candidate.use_case_name or '')[:55]}'")
                    existing = candidate
                    break

        if existing:
            update_fields = {"report": self.report_obj, "theme_id": theme_id}
            for key, value in new_data.items():
                if value in (None, "", []):
                    continue
                if getattr(existing, key, None) in (None, "", []):
                    update_fields[key] = value
            UseCase.objects.filter(id=existing.id).update(**update_fields)
            existing.refresh_from_db()
            print(f"[save] DEDUP  id={existing.id}  {(name or '')[:60]}")
            return existing, False

        db_use_case = UseCase.objects.create(
            report=self.report_obj,
            theme_id=theme_id,
            **new_data
        )
        print(f"[save] NEW    id={db_use_case.id}  {(name or '')[:60]}")
        return db_use_case, True

    def _extract_node(self):
        def extract(state: GraphState):
            if self._check_should_stop():
                return state

            uses = state["use_cases"]
            current_task = state["tasks"][state["current_task_index"]]
            task_num = state["current_task_index"] + 1
            total_tasks = len(state["tasks"])
            scraped_pages = state["scraped_pages"]

            # Stream task start with progress
            self._stream_task_progress(
                current_task.get('task_name', 'Extraction'),
                task_num,
                total_tasks,
                'starting'
            )

            # Get use_case_type options for the theme
            use_case_type_options = state.get("use_case_types", [])

            # If PDF is uploaded, extract ONLY from PDF - skip web sources entirely
            if self.pdf_uploaded and self.pdf_text:
                self._stream(f"[PDF-Only Mode] Extracting findings from uploaded PDF: {self.pdf_filename}", 20)
                
                cleaned_text = clean_text_for_db(self.pdf_text)
                prompt = PDF_QUANTITATIVE_EXTRACTION_PROMPT.format(
                    article=cleaned_text,
                    user_prompt=self.user_prompt,
                    schema=json.dumps(self.schema),
                    theme_title=self.theme_title or "General",
                    max_use_cases=self.max_use_cases,
                )
                
                pdf_response = self.llm_core.invoke(prompt[:200000])
                self._track_llm_call(pdf_response)
                raw = pdf_response.content
                clean = self._clean_llm(raw)

                if self._check_should_stop():
                    return state
                
                try:
                    data = json.loads(clean)
                except json.JSONDecodeError:
                    print(f"Error parsing LLM response for PDF extraction: {clean}")
                    data = []

                if isinstance(data, dict):
                    data = [data]

                today_str = datetime.now().strftime("%Y-%m-%d")
                for d in data:
                    if self._check_should_stop():
                        return state

                    if self.total_use_cases_created >= self.max_use_cases:
                        self._stream(f"Reached maximum of {self.max_use_cases} impacts. Stopping extraction.", 95)
                        return state

                    # Mark as PDF source ONLY
                    d["source"] = self.pdf_filename or "Uploaded PDF"
                    d["source_type"] = "PDF"
                    # Keep the LLM's own page/section locator (needed for the
                    # citation-validation gate below) - only fall back to a
                    # generic note if it didn't extract one.
                    if not d.get("source_reference"):
                        d["source_reference"] = "Extracted from uploaded document"
                    d["use_case_date"] = self._sanitize_use_case_date(d.get("use_case_date"), today_str)
                    d["published_date"] = self._sanitize_use_case_date(d.get("published_date"), today_str)

                    cleaned_data = {k: clean_text_for_db(d.get(k, "")) for k in self.schema if k in d}
                    uc = ExtractedUseCase(**cleaned_data)
                    is_new_use_case = True
                    if self.report_obj:
                        db_use_case, is_new_use_case = self._get_or_create_use_case(self.theme_id, uc)
                        uc.id = db_use_case.id
                        if is_new_use_case and uc.use_case_type != "Researcher Affiliation Record":
                            self.total_use_cases_created += 1

                    # A merge match (is_new_use_case=False) means this finding is a
                    # duplicate of a row that was already scored and validated
                    # earlier. Re-running the credibility/relevance check here served
                    # no purpose except risking overwriting that row's score with a
                    # worse one - the pass/fail gate below is only ever reached for
                    # *new* rows, so a re-check that failed could never delete the
                    # (pre-existing, not "new") row it had just downgraded, leaving a
                    # zombie sub-threshold row permanently in the DB. Skip re-scoring
                    # entirely for merges instead: keep the winning row's original
                    # score, and save the wasted LLM call.
                    if not is_new_use_case:
                        continue

                    if uc.use_case_type == "Researcher Affiliation Record":
                        uc.is_relevant = True
                        uc.is_credible = True
                    else:
                        self._check_credibility_and_relevance(uc, self.pdf_text)
                        if not self._passes_relevance_gate(uc):
                            self._record_relevance_outcome(passed=False)
                            if is_new_use_case and hasattr(uc, 'id'):
                                UseCase.objects.filter(id=uc.id).delete()
                                self.total_use_cases_created = max(0, self.total_use_cases_created - 1)
                            self._stream("Skipped a low-REF-relevance PDF finding after validation.", 85)
                            continue
                        self._record_relevance_outcome(passed=True)
                    self._stream(f'<usecase>{json.dumps(uc.to_dict())}</usecase>')
                    uses.append(uc)

                # Stream PDF extraction completion
                self._stream(f"✓ PDF extraction complete. Found {len(uses)} finding(s) from document.", 95)
                state["use_cases"] = uses
                return state  # RETURN HERE - skip web sources entirely when PDF is present

            # Extract from web sources ONLY if NO PDF was uploaded
            today_str = datetime.now().strftime("%Y-%m-%d")

            def _build_batch_extraction_prompt(batch):
                # Cap each article at 12 000 chars (same per-article budget as
                # before) so a multi-article batch stays fast while still
                # carrying enough text for quantitative evidence.
                articles_block = "\n\n".join(
                    f"=== ARTICLE {idx} (source: {p['url']}) ===\n"
                    f"{clean_text_for_db(p['text'])[:12000]}"
                    for idx, p in enumerate(batch, 1)
                )
                return self.base_extract_prompt.format(
                    articles=articles_block,
                    user_prompt=self.user_prompt,
                    today=today_str,
                    schema=json.dumps(self.schema),
                    theme_title=self.theme_title or "General",
                    use_case_type_options=json.dumps(use_case_type_options)
                )

            def _run_batch_extraction(batch):
                try:
                    extraction_response = self.llm_core.invoke(_build_batch_extraction_prompt(batch)[:200000])
                    self._track_llm_call(extraction_response)
                    return extraction_response.content, None
                except Exception as e:
                    return None, e

            # Pages are grouped into small batches and each batch gets ONE
            # extraction call instead of one call per page - e.g. 30 scraped
            # pages becomes ~10 calls instead of 30, cutting round trips (and
            # therefore end-to-end extraction time) roughly proportionally to
            # batch size. Every finding carries an "article_index" (see
            # REF_EXTRACTION_PROMPT) so it maps back to its exact source page
            # below, preserving every per-page quality gate unchanged. Batches
            # are still dispatched concurrently, bounded at 8 workers, to stay
            # well under typical per-account rate limits.
            batches = [
                scraped_pages[i:i + self._EXTRACTION_BATCH_SIZE]
                for i in range(0, len(scraped_pages), self._EXTRACTION_BATCH_SIZE)
            ]
            with ThreadPoolExecutor(max_workers=8) as pool:
                batch_results = list(pool.map(_run_batch_extraction, batches))

            pages_processed = 0
            total_pages = len(scraped_pages)
            for batch, (raw, extraction_error) in zip(batches, batch_results):
                if self._check_should_stop():
                    return state

                # Stream extraction progress for every URL in this batch.
                for page in batch:
                    pages_processed += 1
                    self._stream_url_progress(page["url"], pages_processed, total_pages, 'extracting')

                if extraction_error is not None:
                    err = str(extraction_error)
                    batch_urls = ", ".join(p["url"][:60] for p in batch)
                    self._stream(f"[ERROR] AI extraction failed for batch [{batch_urls}]: {err[:200]}")
                    print(f"[extract] LLM error on batch {[p['url'] for p in batch]}: {extraction_error}")
                    continue
                clean = self._clean_llm(raw)

                if self._check_should_stop():
                    return state

                try:
                    data = json.loads(clean)
                except json.JSONDecodeError:
                    print(f"Error parsing LLM response when extracting use cases: {clean}")
                    data = []

                if isinstance(data, dict):
                    data = [data]

                for d in data:
                    if self._check_should_stop():
                        return state

                    # Stop extraction if max_use_cases limit reached
                    if self.total_use_cases_created >= self.max_use_cases:
                        self._stream(f"Reached maximum of {self.max_use_cases} impacts. Stopping extraction.", 95)
                        return state

                    # Resolve which page in this batch the finding actually
                    # came from via the required article_index - dropping
                    # findings with a missing/invalid index rather than risk
                    # misattributing them to the wrong source page.
                    article_index = d.pop("article_index", None)
                    try:
                        article_index = int(article_index)
                    except (TypeError, ValueError):
                        article_index = None
                    if not article_index or not (1 <= article_index <= len(batch)):
                        print(f"[extract] Dropping finding with invalid article_index={article_index!r} (batch size {len(batch)})")
                        continue
                    page = batch[article_index - 1]

                    d["source"] = page["url"]
                    # Set source type as Web (only reached when no PDF is present)
                    d["source_type"] = "Web"
                    # Keep the LLM's own page/section/paragraph locator (needed
                    # for the citation-validation gate below) - only fall back
                    # to the bare URL if it didn't extract a more specific one.
                    if not d.get("source_reference"):
                        d["source_reference"] = page["url"]
                    d["use_case_date"] = self._sanitize_use_case_date(d.get("use_case_date"), today_str)
                    d["published_date"] = self._sanitize_use_case_date(d.get("published_date"), today_str)

                    cleaned_data = {k: clean_text_for_db(d.get(k, "")) for k in self.schema if k in d}
                    uc = ExtractedUseCase(**cleaned_data)
                    uc.domain = (urlparse(page["url"]).netloc or "").lower()

                    # ── Quality gate 0: reject any Aston University source ──
                    # Fiona's review feedback: prioritise non-Aston sources -
                    # no aston.ac.uk source (news, repository, staff profile,
                    # or otherwise) counts as independent evidence. Reject
                    # before spending any credibility/relevance LLM calls on it.
                    if self._is_aston_source(page["url"]):
                        self._stream(
                            f"Skipping Aston University source (not independent evidence): {page['url'][:80]}"
                        )
                        continue

                    # ── Quality gate 0b: verify direct_quote is actually in the
                    # VISIBLE source text - same anti-hallucination posture as
                    # the numeric-claims check below, applied to quotes.
                    # Checked against visible text only (not page metadata,
                    # e.g. og:description) so a "quote" can't pass just
                    # because it happens to match an invisible meta tag a
                    # reviewer would never see on the rendered page.
                    visible_text = self._visible_page_text(page["text"])
                    if uc.direct_quote and not self._quote_verified(uc.direct_quote, visible_text):
                        self._stream(
                            f"[WARN] Quoted text from {page['url'][:70]} not found verbatim in "
                            "visible page text (only in metadata, or not present at all) — "
                            "dropping unverifiable quote"
                        )
                        uc.direct_quote = None

                    # Fallback: the LLM frequently embeds an actual quoted
                    # phrase inside source_reference (e.g. "quote from Sharon
                    # Fox on reprocessing 'around 140,000 scopes per year'")
                    # without also populating the separate direct_quote field,
                    # even when explicitly instructed to. Rather than rely on
                    # prompt-following alone, pull the longest quoted span out
                    # of source_reference and promote it to direct_quote -
                    # still gated by the same verbatim verification, so a
                    # fabricated-looking quote is never accepted.
                    if not uc.direct_quote and uc.source_reference:
                        fallback_quote = self._extract_quoted_span(uc.source_reference)
                        if fallback_quote and self._quote_verified(fallback_quote, visible_text):
                            uc.direct_quote = fallback_quote

                    # A citation claim (research "cited in"/"referenced by"/
                    # "informed" a policy/document) without any locatable
                    # quote or page reference cannot be validated by a
                    # reviewer - flag it rather than silently persisting an
                    # unverifiable claim (Fiona's review feedback).
                    citation_claim_text = f"{uc.use_case_description or ''} {uc.performance_impact or ''}".lower()
                    citation_claim_phrases = ("cited in", "referenced by", "referenced in", "informed the", "informed by")
                    if (any(phrase in citation_claim_text for phrase in citation_claim_phrases)
                            and not uc.direct_quote and not uc.source_reference):
                        note = "Citation claimed without a locatable quote or page reference — needs manual verification."
                        uc.credibility_reasoning = (
                            f"{uc.credibility_reasoning} {note}".strip() if uc.credibility_reasoning else note
                        )

                    # ── Quality gate 1: profile-page source penalty ──────────
                    # Researcher/person profile pages are poor primary sources.
                    # Cap credibility and flag any unverified numeric claims.
                    if self._is_profile_source(page["url"]):
                        uc.credibility_score = min(uc.credibility_score or 2, 2)
                        if uc.performance_impact and not self._numeric_claims_verified(
                            uc.performance_impact, page["text"]
                        ):
                            self._stream(
                                f"[WARN] Numeric claims in profile source {page['url'][:70]} "
                                "not found in page text — marked unverified"
                            )
                            uc.performance_impact = (
                                uc.performance_impact + " [figures unverified — not stated in source]"
                            )

                    # ── Quality gate 2: near-duplicate detection ─────────────
                    # Two extractions from the *same* source URL describing the
                    # same fact are always the same evidence item, no matter how
                    # differently worded (different sentence order, "Ltd" vs
                    # "Limited", "introduced" vs "developed") - a same-source
                    # match is now treated as an automatic duplicate rather than
                    # needing to clear a similarity threshold. Real data proved
                    # the threshold-based version unreliable: one article
                    # produced 5 separate rows in production because several of
                    # its restatements happened to land under the old bar.
                    # Different-source pairs still need the stricter fuzzy bar,
                    # to avoid conflating two different organisations that
                    # happen to use similar language.
                    same_source_existing = next(
                        (existing for existing in uses if existing.source and existing.source == uc.source),
                        None,
                    )
                    if same_source_existing is not None:
                        self._stream(
                            f"Skipping same-source duplicate: '{(uc.use_case_name or '')[:70]}'"
                        )
                        continue
                    if uc.use_case_name:
                        is_dup = any(
                            self._claim_similarity(uc.use_case_name, existing.use_case_name)
                            > self._CROSS_SOURCE_DEDUP_THRESHOLD
                            for existing in uses
                            if existing.use_case_name
                        )
                        if is_dup:
                            self._stream(
                                f"Skipping near-duplicate: '{uc.use_case_name[:70]}'"
                            )
                            continue

                    is_new_use_case = True
                    if self.report_obj:
                        db_use_case, is_new_use_case = self._get_or_create_use_case(self.theme_id, uc)
                        uc.id = db_use_case.id
                        # Affiliation records are metadata, not impact evidence -
                        # don't let them eat into the user's requested
                        # number_of_outcomes count.
                        if is_new_use_case and uc.use_case_type != "Researcher Affiliation Record":
                            self.total_use_cases_created += 1  # Increment counter

                    # A merge match (is_new_use_case=False) means _get_or_create_use_case
                    # found an existing row - via exact-source or cross-source fuzzy
                    # match - from an EARLIER run (the in-memory check above only
                    # catches duplicates within this run). That existing row was
                    # already scored and validated when first created. Re-running the
                    # credibility/relevance check here served no purpose except
                    # risking overwriting its score with a worse one: the pass/fail
                    # gate below only deletes rows when is_new_use_case is True, so a
                    # re-check that failed here could never delete the (pre-existing)
                    # row it had just downgraded - leaving a zombie sub-threshold row
                    # permanently in the DB. Skip re-scoring entirely for merges
                    # instead: keep the winning row's original score, and save the
                    # wasted LLM call.
                    if not is_new_use_case:
                        continue

                    # Stream credibility and relevance checks with progress
                    if self.enable_credibility_check:
                        self._stream_url_progress(
                            page["url"],
                            pages_processed,
                            total_pages,
                            'checking credibility'
                        )

                    if self.enable_relevance_check:
                        self._stream_url_progress(
                            page["url"],
                            pages_processed,
                            total_pages,
                            'checking relevance'
                        )

                    # Affiliation-timeline records aren't impact evidence, so the
                    # standard REF relevance/credibility rubric (external
                    # beneficiary, quantifiable outcome, etc.) doesn't apply and
                    # would always score them too low to survive the gate -
                    # skip straight to keeping them, since simply having the
                    # affiliation_note text extracted is the whole point.
                    if uc.use_case_type == "Researcher Affiliation Record":
                        uc.is_relevant = True
                        uc.is_credible = True
                    else:
                        self._check_credibility_and_relevance(uc, page["text"])
                        if not self._passes_relevance_gate(uc) or not self._passes_ref_evidence_gate(uc):
                            self._record_relevance_outcome(passed=False)
                            if is_new_use_case and hasattr(uc, 'id'):
                                UseCase.objects.filter(id=uc.id).delete()
                                self.total_use_cases_created = max(0, self.total_use_cases_created - 1)
                            self._stream_url_progress(
                                page["url"],
                                pages_processed,
                                total_pages,
                                'skipped low relevance'
                            )
                            continue
                        self._record_relevance_outcome(passed=True)
                    self._stream(f'<usecase>{json.dumps(uc.to_dict())}</usecase>')
                    uses.append(uc)

                    # Stream completion of use case extraction
                    self._stream_url_progress(
                        page["url"],
                        pages_processed,
                        total_pages,
                        'completed'
                    )

            state["use_cases"] = uses
            return state
        return extract

    def _update_status(self, status: str, progress: dict = None):
        """Update the process status in report metadata."""
        if not self.report_obj:
            return
        # Only update progress if it's not decreasing
        if progress:
            current = progress.get('current', 0)
            total = progress.get('total', 1)
            # Ensure total is at least 1 to avoid division by zero
            total = max(total, 1)
            # Progress starts at 5% and ends at 100%
            min_progress = 5
            max_progress = 100
            # Calculate progress percentage based on completed tasks
            percent = min_progress + (max_progress - min_progress) * (current / total)
            percent = min(percent, 100)
            # Never decrease progress
            percent = max(percent, self._last_progress)
            self._last_progress = percent
            self.report_obj.metadata['progress'] = {'current': current, 'total': total, 'percent': percent}
        self.report_obj.metadata['status'] = status
        if status in ['COMPLETED', 'FAILED', 'STOPPED']:
            self.report_obj.metadata['completed_at'] = datetime.now().isoformat()
        self.report_obj.save()

    def _check_should_stop(self) -> bool:
        """Check if the process should stop by reading the latest report status from the database."""
        if not self.report_obj:
            return False
            
        # Refresh the report object from the database to get the latest status
        from content.models import Report
        try:
            self.report_obj.refresh_from_db()
            should_stop = self.report_obj.metadata.get('should_stop', False)
            if should_stop:
                self._stream_task_progress('Stopping', -1, -1, 'stopping')
                self._update_status('STOPPED')
                self._stream_task_progress('Stopped', -1, -1, 'completed')
                # Raise custom exception to stop gracefully
                raise ReportGenerationStopped("Report generation stopped by user request")
            return should_stop
        except Report.DoesNotExist:
            return True

    def stop(self):
        """Stop the process gracefully."""
        if self.report_obj:
            self.report_obj.metadata['should_stop'] = True
            self.report_obj.save()

    # ────────────────────────── public API ─────────────────────────
    def _record_completeness(self, stopped_reason: str) -> None:
        """
        Record why a run stopped short of its requested number_of_outcomes.
        Previously these early-stop paths only streamed a transient Pusher
        message a reviewer would never see after the fact - persisting this
        into Report.metadata makes an incomplete run visible/explainable
        instead of a silent partial result ("won't pull all the cases").
        """
        if not self.report_obj:
            return
        self.report_obj.metadata["completeness"] = {
            "requested": self.max_use_cases,
            "found": self.total_use_cases_created,
            "stopped_reason": stopped_reason,
        }
        self.report_obj.save(update_fields=["metadata"])

    def _persist_token_usage(self) -> None:
        """
        Write accumulated LLM token usage (see _track_llm_call) and Tavily
        search-call counts into Report.metadata so a run's real cost is
        visible regardless of how it ends (completed, stopped, failed) -
        previously nothing recorded this anywhere, so cost was only ever
        discoverable on the OpenAI/Tavily bills. token_usage covers OpenAI
        LLM calls only (planning, extraction, credibility/relevance checks,
        synthesis) - Tavily is a separate, per-search-billed API with no
        token concept, tracked here only as a call count, not a cost figure.
        """
        if not self.report_obj:
            return
        with self._token_usage_lock:
            usage = dict(self._token_usage)
        self.report_obj.metadata["token_usage"] = usage
        self.report_obj.metadata["search_api_usage"] = {
            "provider": "tavily",
            "calls_total": self._search_calls_total,
            "calls_failed": self._search_calls_failed,
        }
        self.report_obj.save(update_fields=["metadata"])

    def _refresh_tavily_usage(self) -> None:
        """Persist Tavily's account/key usage without ever exposing the API key.

        This makes an exhausted plan visible before a long research run is
        launched, rather than leaving the UI to infer it from empty results.
        """
        if not self.report_obj or not os.getenv("TAVILY_API_KEY"):
            return
        try:
            request = Request(
                "https://api.tavily.com/usage",
                headers={"Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}"},
            )
            with urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            key_usage = payload.get("key") or {}
            account_usage = payload.get("account") or {}
            self.report_obj.metadata["tavily_usage"] = {
                "status": "available",
                "key_usage": key_usage.get("usage"),
                "key_limit": key_usage.get("limit"),
                "plan_usage": account_usage.get("plan_usage"),
                "plan_limit": account_usage.get("plan_limit"),
                "current_plan": account_usage.get("current_plan"),
            }
        except HTTPError as exc:
            self.report_obj.metadata["tavily_usage"] = {
                "status": "unavailable",
                "message": "Tavily rejected the usage check; verify API credits, plan limits, or rate limits.",
                "http_status": exc.code,
            }
        except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
            self.report_obj.metadata["tavily_usage"] = {
                "status": "unknown",
                "message": "Tavily usage could not be checked before this run.",
            }
        self.report_obj.save(update_fields=["metadata"])

    def _record_tavily_search_denial(self, error: Exception) -> None:
        """Surface quota/rate-limit denial in persistent report metadata."""
        if not self.report_obj or "432" not in str(error):
            return
        self.report_obj.metadata["tavily_usage"] = {
            "status": "denied",
            "message": "Tavily denied search requests (HTTP 432). Check remaining credits and rate limits before retrying.",
            "http_status": 432,
        }
        self.report_obj.save(update_fields=["metadata"])

    def run(self):
        try:
            report_id = self.report_obj.id if self.report_obj else None
            self._refresh_tavily_usage()

            base_state: GraphState = {
                "tasks": [],
                "current_task_index": 0,
                "search_results": {},
                "scraped_pages": [],
                "thoughts": [],
                "report_id": report_id,
                "use_cases": [],
                "page_contents": {},
                "use_case_types": [],
                "pdf_uploaded": self.pdf_uploaded,
                "pdf_text": self.pdf_text,
                "pdf_filename": self.pdf_filename,
            }
            
            # Invoke the graph
            out = self.graph.invoke(base_state,{"recursion_limit": self.recursion_limit})

            if not self._check_should_stop():
                # Filter and sort use cases based on relevance threshold and complexity
                filtered_use_cases = self._apply_relevance_filtering(out["use_cases"])

                # If every web search request failed outright (e.g. the search
                # provider rejected the API key/quota) and nothing was found,
                # this isn't a clean "no results" outcome - surface it as a
                # failure instead of silently completing with zero use cases.
                all_searches_failed = (
                    self._search_calls_total > 0
                    and self._search_calls_failed == self._search_calls_total
                )
                if all_searches_failed and not filtered_use_cases:
                    if self.report_obj:
                        self._update_status('FAILED')
                        self.report_obj.metadata["error"] = (
                            f"All {self._search_calls_total} web search request(s) failed: "
                            f"{self._last_search_error}"
                        )
                        self.report_obj.save()
                        self._persist_token_usage()
                    self._stream(
                        f"Search failed due to an error: every web search request failed "
                        f"({self._last_search_error}). No new use cases could be found.",
                        100,
                    )
                    return report_id, []

                if self.skip_report_generation:
                    if self.report_obj:
                        self.report_obj.metadata["report_generation_skipped"] = True
                        self.report_obj.save(update_fields=["metadata"])
                    # Must start with the exact same "Search completed
                    # successfully!" prefix as the normal path below - the
                    # frontend's PusherListener detects completion by string
                    # prefix match (startsWith), not by parsing structured
                    # data, so a differently-worded message here is silently
                    # never recognised as completion at all. Extra detail
                    # after the prefix is fine; changing the prefix itself
                    # is not.
                    self._stream(
                        f"Search completed successfully! Found {len(filtered_use_cases)} use case(s). "
                        "Report generation skipped - compile a report from these evidence items whenever "
                        "you're ready.",
                        100,
                    )
                else:
                    if not filtered_use_cases:
                        # This is an evidence-quality outcome, not a UI/data
                        # loading failure. Preserve it so the frontend can tell
                        # the researcher what to improve in the next search.
                        self._record_completeness("no_ref_ready_evidence")
                    self._save_generated_report(filtered_use_cases)
                    self._stream("Search completed successfully!", 100)
                self._update_status('COMPLETED')
                self._persist_token_usage()

            return report_id, [uc for uc in out["use_cases"]]
        except ReportGenerationStopped as e:
            # Handle graceful stop
            if self.report_obj:
                self._update_status('STOPPED')
                self._persist_token_usage()

            self._stream("Search stopped by user request.", 100)
            return self.report_obj.id if self.report_obj else None, []
        except Exception as e:
            print("Error in report generation")
            print(f"Error: {e}")
            if self.report_obj:
                self._update_status('FAILED')
                self.report_obj.metadata["error"] = str(e)
                self.report_obj.save()
                self._persist_token_usage()
                # Send error message
                self._stream(f"Search failed due to an error: {e}", 100)
            raise e

    def _apply_relevance_filtering(self, use_cases: List[Dict]) -> List[Dict]:
        """
        Filter and sort use cases based on relevance threshold.
        Higher complexity levels are more inclusive (lower thresholds).
        
        The use cases are filtered from the database based on their relevance scores.
        """
        if not self.report_obj or not use_cases:
            return use_cases
        
        try:
            from content.models import UseCase
            
            # Fetch all use cases from database with relevance scores
            db_use_cases = UseCase.objects.filter(report=self.report_obj).order_by('-relevance_score')
            
            filtered_use_case_ids = []
            for uc in db_use_cases:
                # A report must only use the same REF-ready standard as the
                # extraction path (_passes_relevance_gate /
                # _passes_ref_evidence_gate) - previously hardcoded to 7 here,
                # which silently dropped every use case that had already been
                # admitted (and counted toward number_of_outcomes, driving
                # further replanning rounds) at the documented 6-point bar.
                # Missing scores are not an "edge case" to include: they are
                # unassessed evidence and must be reviewed.
                relevance_floor = max(6, int(round(self.relevance_threshold * 10)))
                if (uc.relevance_score is not None
                        and uc.relevance_score >= relevance_floor
                        and uc.credibility_score is not None
                        and uc.credibility_score >= 7
                        and self._passes_ref_evidence_gate(uc)):
                    filtered_use_case_ids.append(uc.id)
            
            print(f"[Relevance Filtering] Threshold: {self.relevance_threshold * 10:.1f}/10")
            print(f"  Total use cases: {db_use_cases.count()}")
            print(f"  Filtered use cases: {len(filtered_use_case_ids)}")

            self._stream(f"Relevance filtering: {len(filtered_use_case_ids)} use cases selected", 98)
            
            return [uc for uc in db_use_cases if uc.id in filtered_use_case_ids]
        except Exception as e:
            print(f"Error during relevance filtering: {e}")
            return use_cases
