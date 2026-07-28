"""Utility classes and constants for report generation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, TypedDict
import re

# ────────────────────────── REF period helpers ──────────────────────
# REF 2029 eligible windows (see https://2029.ref.ac.uk/guidance/section-6-engagement-and-impact-guidance/).
# Impact occurrence and underpinning research have different eligible
# periods - a source reporting on the impact itself must fall in the
# (shorter) impact window, while a source describing the underpinning
# research/output can be much older and only needs to fall in the (longer)
# research window. Shared here (rather than living only inside
# StructuredReportGenerator) so both the report-build step and the
# UseCase API/serializer can compute the same status for the same source.
IMPACT_PERIOD = ("2020-08-01", "2028-07-31")
RESEARCH_PERIOD = ("2008-01-01", "2028-12-31")


def date_sort_key(value: Optional[str]) -> tuple:
    """Comparable sort key for a use_case_date of any supported precision
    (YYYY, YYYY-MM, YYYY-MM-DD). Padding is for comparison only - it never
    changes the stored/displayed value. Undated values sort last."""
    if not value:
        return (9999, 12, 31)
    parts = value.split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
    except (ValueError, IndexError):
        return (9999, 12, 31)
    return (year, month, day)


def is_within_period(value: Optional[str], period: tuple) -> Optional[bool]:
    """True/False if `value` falls within `period` (inclusive), or None if
    `value` is undated and therefore can't be judged either way."""
    if not value:
        return None
    return date_sort_key(period[0]) <= date_sort_key(value) <= date_sort_key(period[1])


def ref_period_for_content_type(content_type: Optional[str]) -> tuple:
    """Peer-reviewed/research-output sources are judged against the longer
    underpinning-research window; everything else (impact evidence, press
    coverage, policy citations) against the impact occurrence window."""
    if content_type == "peer_reviewed":
        return RESEARCH_PERIOD
    return IMPACT_PERIOD


# ────────────────────────── Constants ──────────────────────────────
PERFORMANCE_IMPROVEMENT_CATEGORIES = [
    "Economic Impact",
    "Societal Impact",
    "Cultural Impact",
    "Public Policy or Services Impact",
    "Health Impact",
    "Environmental Impact",
    "Quality of Life Impact",
    "Professional Practice Impact",
    "Education or Learning Impact"
]

INDUSTRY_SECTORS = [
    "Technology & IT",
    "Financial Services",
    "Healthcare",
    "Energy & Utilities",
    "Automotive",
    "Retail & Commerce",
    "Telecommunications",
    "Construction & Real Estate",
    "Agriculture & Food",
    "Media & Entertainment",
    "Manufacturing",
    "Education",
    "Government & Public Services",
    "Culture & Heritage",
    "Environment & Sustainability",
    "Third Sector & Communities",
    "Other"
]

GEOGRAPHY_REGIONS = [
    "Global",
    "EMEA",
    "AMER",
    "APAC"
]

# ────────────────────────── Data Classes ───────────────────────────
@dataclass
class ExtractedUseCase:
    """Dataclass mirroring the DB model, handy for in‑memory work."""
    theme: Optional[int] = None  # Theme ID
    use_case_name: Optional[str] = None  # One sentence summary of the use case
    use_case_type: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    tools: Optional[str] = None
    use_case_description: Optional[str] = None
    performance_impact: Optional[str] = None
    use_case_date: Optional[str] = None
    published_date: Optional[str] = None  # when the SOURCE DOCUMENT itself was published, distinct from use_case_date (the impact/deployment date)
    source: Optional[str] = None
    source_type: Optional[str] = None  # "PDF" | "External Verification" | "Web"
    source_reference: Optional[str] = None  # page number, paragraph, URL, etc.
    domain: Optional[str] = None  # host parsed from `source`, e.g. aston.ac.uk
    publisher: Optional[str] = None  # organisation/site that published the source
    content_type: Optional[str] = None  # press_release | peer_reviewed | news | policy | testimonial | other (e.g. professional-body, funder, project, patent, repository, conference, report)
    direct_quote: Optional[str] = None  # verbatim quote supporting a citation/impact claim
    affiliation_note: Optional[str] = None  # verbatim statement of when a named researcher joined/left an institution, if this source states one
    credibility_score: Optional[float] = None
    is_credible: Optional[bool] = None
    credibility_reasoning: Optional[str] = None
    relevance_score: Optional[float] = None
    is_relevant: Optional[bool] = None
    relevance_reasoning: Optional[str] = None
    performance_improvement_category: Optional[str] = None
    geography: Optional[str] = None
    country: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class GraphState(TypedDict):
    """Type definition for the graph state."""
    tasks: List[Dict]
    current_task_index: int
    search_results: Dict[str, List[Dict]]
    scraped_pages: List[Dict]
    thoughts: List[str]
    report_id: Optional[int]
    use_cases: List[ExtractedUseCase]
    page_contents: Dict[str, str]  # Maps source URLs to their content
    use_case_types: List[str]  # Generated use case types for the theme
    pdf_uploaded: Optional[bool]  # Whether a PDF was uploaded
    pdf_text: Optional[str]  # Extracted PDF text if present
    pdf_filename: Optional[str]  # PDF filename for reference
    replanning_round: Optional[int]  # How many extra search rounds have run
    replan_start_count: Optional[int]  # use_case count snapshot taken before the current round
    tasks_exhausted: Optional[bool]  # Set when a replanning round yields no new tasks

# ────────────────────────── Helper Classes ─────────────────────────
class _ScrapeTask:
    """Small wrapper so we can queue scraping work across threads."""

    def __init__(self, url: str, scraper):
        self.url, self.scraper = url, scraper

    async def run(self):
        try:
            res = await self.scraper.scrape_only(self.url)
            if res and "text" in res:
                return self.url, res.get("title", "")[:255], res["text"]
        except Exception:
            pass
        return self.url, "", ""

# ────────────────────────── Utility Functions ──────────────────────
def clean_text_for_db(text: str) -> str:
    """Clean and normalize text to be database-safe by handling special characters."""
    
    if text is None:
        return ""
    
    try:
        replacements = {
            '\u2019': "'",  # Right single quote
            '\u2018': "'",  # Left single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...' # Ellipsis
        }
        
        for special_char, replacement in replacements.items():
                text = text.replace(special_char, replacement)
            
        return ''.join(char for char in text if ord(char) < 128)
    except Exception as e:
        print(f"Error cleaning text for db: {e}")
        print(f"Text: {text}")
        return text

def get_default_schema() -> Dict[str, str]:
    """Get the default schema for use case extraction."""
    return {
        "use_case_name": "A concise REF-style impact claim. State the real-world change, beneficiary, and strongest metric where possible. Avoid generic names like 'Research Impact'.",
        "use_case_type": "The concrete impact mechanism, such as Policy Influence, Clinical Adoption, Public Engagement, Industry Adoption, Professional Practice Change, Environmental Benefit, Economic Benefit, or Community Benefit.",
        "company": "The external beneficiary, implementing organisation, public body, community, partner, or audience that experienced the impact. This can be NHS, government, charity, company, school, museum, patients, professionals, or citizens.",
        "industry": f"The affected sector or beneficiary context. Must be one of: {', '.join(INDUSTRY_SECTORS)}",
        "tools": "The underpinning research output, intervention, method, dataset, policy evidence, tool, programme, or practice that enabled the impact. Leave blank if the source does not specify it.",
        "use_case_description": "A REF-focused narrative explaining what changed beyond academia, who benefited, how the research contributed, and what evidence supports the claim. Include reach and significance if available.",
        "performance_impact": "The strongest measurable evidence of reach or significance: beneficiary counts, adoption numbers, policy citations, cost savings, health outcomes, environmental metrics, audience reach, practice changes, or qualitative corroboration. Do not invent numbers.",
        "performance_improvement_category": f"The REF impact domain. Must be one of: {', '.join(PERFORMANCE_IMPROVEMENT_CATEGORIES)}. If unclear, use Other.",
        "geography": f"The primary geographical region where the use case is implemented. Must be one of: {', '.join(GEOGRAPHY_REGIONS)}",
        "country": "The specific country where the impact occurred, if stated. Leave empty if global or not specified.",
        "use_case_date": "The date or start date when the IMPACT occurred, was implemented, or was deployed - not the date the source article was published (that goes in the separate published_date field below). Use only the precision actually stated in the source: \"YYYY-MM-DD\" if an exact day is given, \"YYYY-MM\" if only month and year are given, or \"YYYY\" if only the year is given. Never invent or pad a day or month that is not stated (e.g. do not default to the 1st of a month or year). Never use the date the article was scraped, or the current date, as a stand-in. If the source gives no date information at all, return null.",
        "published_date": "The date the SOURCE DOCUMENT itself was published or last updated - the article's byline/dateline date, journal issue date, or press-release date - not the date of the impact/event it describes (that goes in use_case_date above; the two are frequently different, e.g. a 2024 article covering a 2021 deployment). Always look for this separately from use_case_date, even when use_case_date is also present. Unlike direct_quote/source_reference, it is normal and expected to take this from the page's metadata (a 'Metadata:' block, meta tags such as article:published_time or datePublished, or JSON-LD) if it is not shown in the visible body text - a publish date is standard page metadata, not a hidden claim. Same precision rules as use_case_date (\"YYYY-MM-DD\"/\"YYYY-MM\"/\"YYYY\", never invented or padded). Return null only if genuinely no publish/update date is stated anywhere, visible or in metadata.",
        "source": "The exact source URL or source reference used as corroborating evidence. Prefer independent or beneficiary-authored sources.",
        "source_reference": "WHERE in the source the evidence appears - a locator only, not the quote itself: page number, section heading, paragraph position (e.g. 'third paragraph'), table/figure name, or URL anchor. Do NOT put quoted text here - any verbatim wording belongs in the separate direct_quote field below, even though this field and direct_quote are usually filled in together. Never cite a page's meta tags (meta description, og:description, twitter:description, or any 'Metadata:' block appended after the article text) as the location - those are invisible to a reader of the rendered page and cannot be 'jumped to'; if the only place a claim appears is in page metadata rather than the visible article, treat it as unverifiable and do not extract it as a use case at all. Be specific enough that a reviewer can jump straight to the right spot. Mandatory (do not leave blank) whenever the source text says the research was cited in, referenced by, or informed a policy/document/decision.",
        "publisher": "The organisation, outlet, or site that published the source (e.g. 'UK Parliament', 'Nature', 'BBC News'), if identifiable from the page.",
        "content_type": "Classify the source's publication type. Must be exactly one of: press_release, peer_reviewed, news, policy, testimonial, other. Use peer_reviewed for academic papers, preprints, journal articles and conference proceedings; policy for government, regulator, standards-body or formal policy documents; news for independent journalism; testimonial for letters or quoted statements from a named individual/beneficiary; press_release for an organisation's own announcement; and other for a professional-body, funder, charity, project consortium, publisher report, patent, dataset, repository, trade publication or similar external record. Do not use content type to reject a non-Aston source: classify it accurately. A non-Aston partner's or beneficiary's own announcement is admissible evidence when it makes a checkable impact claim; Aston-hosted material is not.",
        "direct_quote": "THE verbatim quotation itself (no more than about 40 words), copied character-for-character as written in the VISIBLE article body - not a paraphrase, not truncated with '...' or edited with '[...]' brackets, and never sourced from page meta tags (meta description, og:description, twitter:description, or a 'Metadata:' block) since those are invisible to someone reading the rendered page and therefore not a checkable quote. Populate this field, separately from source_reference, whenever ANY notable finding, statistic, or attributed statement in the visible source text has exact wording worth preserving - not only when a policy/document citation is claimed, though it is mandatory in that case. If nothing in the visible article has quotable exact wording worth preserving, leave blank rather than inventing one or falling back to metadata.",
        "affiliation_note": "If this source states WHEN a named researcher (from the user prompt) joined, left, or was affiliated with Aston University or any other institution - e.g. 'joined Aston University in 2015', 'previously Professor at the University of Manchester', 'has led the Supergen Bioenergy Hub from Aston since 2018' - copy that statement close to verbatim, including the institution name and date/year. This is independent of whether the source is otherwise usable as impact/research evidence - even a brief author-bio line or LinkedIn-style career summary counts. Leave blank if the source says nothing about when the researcher joined/left any institution."
    }

def shorten_url(url: str, max_length: int = 50) -> str:
    """Shorten a URL for display purposes.
    
    Args:
        url: The URL to shorten
        max_length: Maximum length of the shortened URL
        
    Returns:
        A shortened version of the URL
    """
    if len(url) <= max_length:
        return url
    # Remove protocol and www
    url = re.sub(r'^https?://(www\.)?', '', url)
    if len(url) <= max_length:
        return url
    # Truncate and add ellipsis
    return url[:max_length-3] + '...'

def calculate_progress(current: int, total: int, stage_weight: float = 1.0) -> float:
    """Calculate progress percentage based on current item and total items.
    
    Args:
        current: Current item number (1-based)
        total: Total number of items
        stage_weight: Weight of this stage in overall progress (0-1)
        
    Returns:
        Progress percentage between 0 and 100
    """
    if total <= 0:
        return 0
    # Ensure progress is between 0 and 100
    progress = min(100, max(0, (current / total) * 100 * stage_weight))
    return round(progress, 2)

def format_url_progress_message(url: str, current: int, total: int, stage: str = 'processing') -> tuple[str, float]:
    """Format a URL progress message with shortened URL and progress.
    
    Args:
        url: The URL being processed
        current: Current item number
        total: Total number of items
        stage: Current processing stage
        
    Returns:
        Tuple of (formatted message, progress percentage)
    """
    shortened_url = shorten_url(url)
    progress = calculate_progress(current, total)
    message = f"🔗 {stage.capitalize()} URL : ({url})"
    return message, progress

def format_task_progress_message(task_name: str, current: int, total: int, stage: str = 'processing') -> tuple[str, float]:
    """Format a task progress message with progress.
    
    Args:
        task_name: Name of the current task
        current: Current task number
        total: Total number of tasks
        stage: Current processing stage
        
    Returns:
        Tuple of (formatted message, progress percentage)
    """
    progress = calculate_progress(current, total)
    message = f"📋 {stage.capitalize()} task {current}/{total}: {task_name}"
    return message, progress

def format_query_progress_message(query: str, current: int, total: int) -> tuple[str, float]:
    """Format a query progress message with progress.
    
    Args:
        query: The current query
        current: Current query number
        total: Total number of queries
        
    Returns:
        Tuple of (formatted message, progress percentage)
    """
    progress = calculate_progress(current, total)
    message = f"🔍 Executing query {current}/{total}: {query}"
    return message, progress

def generate_use_case_types_with_llm(user_prompt: str, theme_title: str, existing_types: List[str] = None) -> List[str]:
    """Generate use case types using LLM based on user prompt and existing types.
    
    Args:
        user_prompt: The user's original prompt/query
        theme_title: The title of the theme
        existing_types: List of existing use case types from database (optional)
        
    Returns:
        List of use case types (existing + newly generated)
    """
    try:
        from langchain_openai import ChatOpenAI
        from core.llm.langchain.langgraph.prompts import USE_CASE_TYPE_GENERATION_PROMPT
        import json
        import os
        
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-5.4-mini")
        
        # Prepare existing types for the prompt
        existing_types_str = "None" if not existing_types else json.dumps(existing_types)
        
        # Create the prompt
        prompt = USE_CASE_TYPE_GENERATION_PROMPT.format(
            user_prompt=user_prompt,
            theme_title=theme_title,
            existing_types=existing_types_str
        )
        
        # Get response from LLM
        response = llm.invoke(prompt).content
        
        # Clean and parse the response
        cleaned_response = response.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        
        # Parse JSON response
        generated_types = json.loads(cleaned_response.strip())
        
        # Limit to 8 types maximum
        if isinstance(generated_types, list):
            generated_types = generated_types[:8]
        
        # Combine existing and generated types, removing duplicates
        all_types = existing_types or []
        for new_type in generated_types:
            if new_type not in all_types:
                all_types.append(new_type)
        
        # Ensure final result is also limited to 8
        return all_types[:8]
        
    except Exception as e:
        print(f"Error generating use case types with LLM: {e}")
        # Fallback to existing types or default types
        if existing_types:
            return existing_types
        # Default fallback for SDLC themes
        if theme_title and 'SDLC' in theme_title.upper():
            return [
                "Requirements Engineering",
                "Design", 
                "Development",
                "Testing",
                "Deployment",
                "Maintenance & Operations"
            ]
        return [] 
