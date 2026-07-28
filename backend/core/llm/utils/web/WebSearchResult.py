from typing import Dict, List, Optional
from core.llm.utils.web.WebSearchABC import WebSearch, WebSearchResult
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.google_search import GoogleSearchRun
from langchain_community.utilities.google_search import GoogleSearchAPIWrapper
from langchain_community.tools.google_serper import GoogleSerperRun
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_community.tools.searchapi import SearchAPIRun
# from langchain_community.tools.searx_search import SearxSearchRun
from langchain_community.utilities.searx_search import SearxSearchWrapper
from langchain_community.tools.tavily_search import TavilySearchResults
import requests
from dotenv import load_dotenv
import os



class PerplexitySearch(WebSearch):
    """Perplexity Search (Free tier with limits) - URL, Title, Snippet, Answer"""
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        if not self.api_key:
            raise ValueError("Perplexity Search requires an API key")
        
        # Perplexity uses a chat-like API; we craft a prompt for search
        payload = {
            "model": "pplx-70b-online",  # Adjust model as needed
            "messages": [
                {"role": "system", "content": "You are a search engine. Provide concise answers with sources."},
                {"role": "user", "content": query}
            ],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post(self.url, json=payload, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract answer and sources from response
        answer = data["choices"][0]["message"]["content"]
        # Perplexity doesn't always return structured sources in the free tier; we simulate parsing
        # In practice, you might need to parse the answer text or use a paid tier for structured data
        results = []
        lines = answer.split("\n")
        for line in lines[:max_results]:
            if "http" in line:
                url = line.split("http")[1].split(" ")[0]
                url = "http" + url
                title = line.split(" - ")[0] if " - " in line else "Perplexity Result"
                snippet = line.split(" - ")[1] if " - " in line else line
                results.append(WebSearchResult(url=url, title=title, snippet=snippet, answer=answer))
        
        # If no structured sources, return a single result with the full answer
        if not results:
            results.append(WebSearchResult(url="https://perplexity.ai", title="Perplexity Answer", snippet=answer, answer=answer))
        
        return results

class BingSearch(WebSearch):
    """Bing Search (Paid) - URL, Snippet, Title"""
    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        if not self.api_key:
            raise ValueError("Bing Search requires an API key")
        # LangChain doesn't have a direct Bing tool; use custom implementation
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": max_results}
        response = requests.get(url, headers=headers, params=params)
        data = response.json().get("webPages", {}).get("value", [])
        return [WebSearchResult(url=r["url"], title=r["name"], snippet=r["snippet"]) for r in data]

class BraveSearch(WebSearch):
    """Brave Search (Free) - URL, Snippet, Title"""
    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        # No direct LangChain support; use custom implementation
        url = "https://api.search.brave.com/res/v1/web/search"
        params = {"q": query, "count": max_results}
        response = requests.get(url, params=params)
        data = response.json().get("web", {}).get("results", [])
        return [WebSearchResult(url=r["url"], title=r["title"], snippet=r["description"]) for r in data]

class DuckDuckGoSearch(WebSearch):
    """DuckDuckGo Search (Free) - URL, Snippet, Title"""
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.tool = DuckDuckGoSearchRun()

    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        results = self.tool.run(query, max_results=max_results)
        return self._parse_results(results, max_results)

class ExaSearch(WebSearch):
    """Exa Search (1000 free searches/month) - URL, Author, Title, Published Date"""
    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        if not self.api_key:
            raise ValueError("Exa Search requires an API key")
        # No direct LangChain support; use custom implementation
        url = "https://api.exa.ai/search"
        headers = {"x-api-key": self.api_key}
        params = {"query": query, "numResults": max_results}
        response = requests.get(url, headers=headers, params=params)
        data = response.json().get("results", [])
        return [WebSearchResult(url=r["url"], title=r["title"], author=r.get("author"), published_date=r.get("publishedDate")) for r in data]

class GoogleSearch(WebSearch):
    """Google Search (Paid) - URL, Snippet, Title"""
    def __init__(self, api_key: str, cse_id: str):
        super().__init__(api_key)
        self.wrapper = GoogleSearchAPIWrapper(google_api_key=api_key, google_cse_id=cse_id)
        self.tool = GoogleSearchRun(api_wrapper=self.wrapper)

    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        results = self.tool.run(query, max_results=max_results)
        return self._parse_results(results, max_results)

class GoogleSerperSearch(WebSearch):
    """Google Serper (Free) - URL, Snippet, Title, Search Rank, Site Links"""
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.wrapper = GoogleSerperAPIWrapper(serper_api_key=api_key)
        self.tool = GoogleSerperRun(api_wrapper=self.wrapper)

    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        results = self.tool.run(query, max_results=max_results)
        return self._parse_results(results, max_results)

class JinaSearch(WebSearch):
    """Jina Search (1M Response Tokens Free) - URL, Snippet, Title, Page Content"""
    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        if not self.api_key:
            raise ValueError("Jina Search requires an API key")
        # No direct LangChain support; use custom implementation
        url = "https://api.jina.ai/v1/search"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"q": query, "limit": max_results}
        response = requests.get(url, headers=headers, params=params)
        data = response.json().get("results", [])
        return [WebSearchResult(url=r["url"], title=r["title"], snippet=r["snippet"], page_content=r.get("content")) for r in data]

class MojeekSearch(WebSearch):
    """Mojeek Search (Paid) - URL, Snippet, Title"""
    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        if not self.api_key:
            raise ValueError("Mojeek Search requires an API key")
        # No direct LangChain support; use custom implementation
        url = "https://api.mojeek.com/search"
        headers = {"X-API-Key": self.api_key}
        params = {"q": query, "count": max_results}
        response = requests.get(url, headers=headers, params=params)
        data = response.json().get("results", [])
        return [WebSearchResult(url=r["url"], title=r["title"], snippet=r["desc"]) for r in data]

# class SearchApiSearch(WebSearch):
#     """SearchApi (100 Free Searches on Sign Up) - URL, Snippet, Title, Search Rank, Site Links, Authors"""
#     def __init__(self, api_key: str):
#         super().__init__(api_key)
#         self.wrapper = SearchAPIWrapper(api_key=api_key)
#         self.tool = SearchAPIRun(api_wrapper=self.wrapper)

#     def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
#         results = self.tool.run(query, max_results=max_results)
#         return self._parse_results(results, max_results)

# class SearxNGSearch(WebSearch):
#     """SearxNG Search (Free) - URL, Snippet, Title, Category"""
#     def __init__(self, api_key: Optional[str] = None, host: str = "https://searxng.example.com"):
#         super().__init__(api_key)
#         self.wrapper = SearxSearchWrapper(searx_host=host)
#         self.tool = SearxSearchRun(api_wrapper=self.wrapper)

#     def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
#         results = self.tool.run(query, max_results=max_results)
#         return self._parse_results(results, max_results)

class SerpAPISearch(WebSearch):
    """SerpAPI (100 Free Searches/Month) - Answer"""
    def __init__(self, api_key: str):
        super().__init__(api_key)
        from langchain_community.utilities import SerpAPIWrapper
        self.wrapper = SerpAPIWrapper(serpapi_api_key=api_key)
        self.tool = Tool(
            name="SerpAPI",
            func=self.wrapper.run,
            description="Search using SerpAPI"
        )

    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        results = self.tool.run(query)
        return self._parse_results(results, max_results)

class TavilySearch(WebSearch):
    """Tavily Search (1000 free searches/month) - URL, Content, Title, Images, Answer"""
    def __init__(self, api_key: Optional[str] = None):
        # Load API key from environment if not provided
        load_dotenv()
        api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("Tavily Search requires an API key. Set TAVILY_API_KEY in your environment or pass it explicitly.")
        
        super().__init__(api_key)
        # Instantiate the TavilySearchResults tool with options from the document
        self.tool = TavilySearchResults(
            max_results=10,  # Default max_results, can be overridden in search()
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True,
            include_images=True
        )

    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        """
        Perform a search using Tavily's Search API and return results as WebSearchResult objects.
        
        Args:
            query (str): The search query in natural language.
            max_results (int): Maximum number of results to return (default: 10).
        
        Returns:
            List[WebSearchResult]: List of search results.
        """
        # Update max_results for this specific search call
        self.tool.max_results = max_results
        
        # Invoke the tool with the query
        results = self.tool.invoke({"query": query})
        
        # Convert the results to WebSearchResult objects
        web_results = []
        for result in results:
            web_result = WebSearchResult(
                url=result.get("url", ""),
                title=result.get("title", ""),
                snippet=result.get("content", ""),  # Using 'content' as snippet per document
                answer=result.get("answer", "") if "answer" in result else None,
                # Optionally include additional fields if supported by WebSearchResult
                # images=result.get("images", []),
                # raw_content=result.get("raw_content", "")
            )
            web_results.append(web_result)
        
        return web_results

class YouComSearch(WebSearch):
    """You.com Search (Free for 60 days) - URL, Title, Page Content"""
    def search(self, query: str, max_results: int = 10) -> List[WebSearchResult]:
        if not self.api_key:
            raise ValueError("You.com requires an API key after free trial")
        # No direct LangChain support; use custom implementation
        url = "https://api.you.com/search"
        headers = {"X-API-Key": self.api_key}
        params = {"query": query, "count": max_results}
        response = requests.get(url, headers=headers, params=params)
        data = response.json().get("hits", [])
        return [WebSearchResult(url=r["url"], title=r["title"], page_content=r.get("description")) for r in data]

class UnifiedWebSearch:
    """Manages multiple LangChain-based search tools."""
    def __init__(self, tool_name: str, api_key: Optional[str] = None, **kwargs):
        self.tools = {
            "bing": BingSearch,
            "brave": BraveSearch,
            "duckduckgo": DuckDuckGoSearch,
            "exa": ExaSearch,
            "google": lambda api_key: GoogleSearch(api_key, kwargs.get("cse_id")),
            "google_serper": GoogleSerperSearch,
            "jina": JinaSearch,
            "mojeek": MojeekSearch,
            # "searchapi": SearchApiSearch,
            # "searxng": lambda api_key: SearxNGSearch(api_key, kwargs.get("host", "https://searxng.example.com")),
            "serpapi": SerpAPISearch,
            "tavily": TavilySearch,
            "youcom": YouComSearch
        }
        if tool_name not in self.tools:
            raise ValueError(f"Unsupported tool: {tool_name}")
        self.search_tool = self.tools[tool_name](api_key) if api_key else self.tools[tool_name]()

    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        results = self.search_tool.search(query, max_results)
        return [r.to_dict() for r in results]

# Example usage
if __name__ == "__main__":
    # DuckDuckGo (free, no API key)
    searcher = UnifiedWebSearch("duckduckgo")
    results = searcher.search("latest AI trends 2025")
    for result in results:
        print(result)

    # Tavily (requires API key)
    # searcher = UnifiedWebSearch("tavily")
    # results = searcher.search("SDLC tools")
    # for result in results:
    #     print(result)

    # Google Search (requires API key and CSE ID)
    # searcher = UnifiedWebSearch("google", api_key="YOUR_GOOGLE_API_KEY", cse_id="YOUR_CSE_ID")
    # results = searcher.search("AI trends")
    # for result in results:
    #     print(result)