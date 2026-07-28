import json
import os
from typing import List, Set, Tuple

from crawl4ai import (
    BrowserConfig,
    LLMExtractionStrategy,
)
from content.models import Content, Category
from django.conf import settings



def get_browser_config() -> BrowserConfig:
    """
    Returns the browser configuration for the crawler.

    Returns:
        BrowserConfig: The configuration settings for the browser.
    """
    # https://docs.crawl4ai.com/core/browser-crawler-config/
    return BrowserConfig(
        browser_type="chromium",  # Type of browser to simulate
        headless=True,  # Whether to run in headless mode (no GUI)
        verbose=False,  # Enable verbose logging
    )


def get_llm_strategy() -> LLMExtractionStrategy:
    """
    Returns the configuration for the language model extraction strategy for article content.

    Returns:
        LLMExtractionStrategy: The settings for how to extract article content using LLM.
    """
    return LLMExtractionStrategy(
        provider="gpt4o",  # Name of the LLM provider
        api_token=settings.OPENAI_API_KEY,
        schema=Content.model_json_schema(),  # JSON schema of the Content data model
        extraction_type="schema",  # Type of extraction to perform
        instruction=(
            "Extract article content information with the following fields: 'title', "
            "'original_content', 'summary', 'tags', and 'image_url' if available, "
            "from the provided markdown content. Ensure the summary is concise (2-3 sentences) "
            "and the tags are 5-10 relevant keywords."
        ),
        input_format="markdown",  # Format of the input content
        verbose=True,  # Enable verbose logging
    )
