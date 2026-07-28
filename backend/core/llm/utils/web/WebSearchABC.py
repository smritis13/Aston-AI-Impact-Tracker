from abc import ABC, abstractmethod
from typing import Dict, List, Optional

# Standardized result structure
class WebSearchResult:
    def __init__(self, url: str, title: str, snippet: Optional[str] = None, **kwargs):
        self.url = url
        self.title = title
        self.snippet = snippet
        self.extra = kwargs

    def to_dict(self) -> Dict:
        return {"url": self.url, "title": self.title, "snippet": self.snippet, **self.extra}

class WebSearch(ABC):
    """Base class for web search tools."""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        pass

    def _parse_results(self, results: str, max_results: int) -> List[WebSearchResult]:
        """Parse LangChain's string results into WebSearchResult objects."""
        # Simplified parsing; adjust based on actual output format
        lines = results.split("\n")[:max_results]
        parsed = []
        for line in lines:
            if "http" in line and " - " in line:
                url, rest = line.split(" - ", 1)
                title = rest.split(": ")[0] if ": " in rest else rest
                snippet = rest.split(": ")[1] if ": " in rest else None
                parsed.append(WebSearchResult(url=url.strip(), title=title.strip(), snippet=snippet))
        return parsed
