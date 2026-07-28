from __future__ import annotations

import json
from datetime import datetime
import re
from typing import List
import asyncio

from langchain_community.chat_models import ChatOpenAI
from core.llm.utils.SimpleHtmlScraper import SimpleHtmlScraper
from core.llm.langchain.langgraph.prompts import EXTRACTION_PROMPT
from core.llm.langchain.langgraph.report_generator_utils import (
    ExtractedUseCase,
    clean_text_for_db,
    get_default_schema,
    INDUSTRY_SECTORS,
    PERFORMANCE_IMPROVEMENT_CATEGORIES,
    GEOGRAPHY_REGIONS
)

class SingleUrlExtractor:
    """A simplified version of StructuredReportGenerator that works with a single URL."""

    def __init__(
        self,
        *,
        user_prompt: str,
        theme_id: int | None = None,
        debug_mode: bool = False,
    ) -> None:
        self.user_prompt = user_prompt
        self.theme_id = theme_id
        self.theme_title = None
        if theme_id:
            from content.models import UseCaseTheme
            theme = UseCaseTheme.objects.get(id=theme_id)
            self.theme_title = theme.title

        self.debug = debug_mode
        self.schema = get_default_schema()
        self.base_extract_prompt = EXTRACTION_PROMPT
        self.llm_core = ChatOpenAI(model="gpt-5.4", temperature=1)
        self.scraper = SimpleHtmlScraper()

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
                return sorted(set(options))
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
        return []
    
    @staticmethod
    def _clean_llm(text: str) -> str:
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

    def extract_from_url(self, url: str) -> List[ExtractedUseCase]:
        """Extract use cases from a single URL."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Scrape the URL using the event loop
            scraped_data = loop.run_until_complete(self.scraper.scrape_only(url))
            if not scraped_data or "text" not in scraped_data:
                return []
            
            # print(scraped_data)

            # Clean the text for the database
            cleaned_text = clean_text_for_db(scraped_data["text"])

            
            # Get use_case_type options for the theme
            use_case_type_options = self.get_use_case_type_options()

            # Prepare and send the extraction prompt
            prompt = self.base_extract_prompt.format(
                article=cleaned_text,
                user_prompt=self.user_prompt,
                today=datetime.now().strftime("%Y-%m-%d"),
                schema=json.dumps(self.schema),
                theme_title=self.theme_title or "General",
                use_case_type_options=json.dumps(use_case_type_options)
            )
            
            # Call LLM directly
            raw = self.llm_core.invoke(prompt).content
            clean = self._clean_llm(raw.strip())


            # Parse the response
            data = json.loads(clean)
            if isinstance(data, dict):
                data = [data]

            # Convert to ExtractedUseCase objects
            use_cases = []
            for d in data:
                d["source"] = url
                cleaned_data = {k: clean_text_for_db(d.get(k, "")) for k in self.schema}
                uc = ExtractedUseCase(**cleaned_data)
                use_cases.append(uc)

            return use_cases
            
        finally:
            # Clean up the event loop
            loop.close() 