import requests
from duckduckgo_search import DDGS
import random
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.87 Mobile Safari/537.36"
]

class WebSearcher:
    """
    WebSearcher performs web searches using different search APIs.
    It supports:
      - Google Custom Search API (default)
      - Bing Search API
      - Perplexity AI (if an API is available)
    """
    def __init__(self, google_api_key: str= None, google_cx: str= None, bing_api_key: str = None, perplexity_api_key: str = None):
        """
        Initialize WebSearcher with API credentials.

        Args:
            google_api_key (str): API key for Google Custom Search.
            google_cx (str): Custom Search Engine ID for Google.
            bing_api_key (str, optional): API key for Bing Search API.
            perplexity_api_key (str, optional): API key for Perplexity AI search.
        """
        self.google_api_key = google_api_key
        self.google_cx = google_cx
        self.bing_api_key = bing_api_key
        self.perplexity_api_key = perplexity_api_key

    def google_search(self, query: str, num_results: int = 10) -> list[dict]:
        """
        Perform a web search using the Google Custom Search API.

        Args:
            query (str): The search query.
            num_results (int, optional): Number of results to return. Defaults to 10.

        Returns:
            list[dict]: A list of dictionaries with 'title', 'snippet', and 'link'.
        """
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": num_results
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            items = response.json().get("items", [])
            results = []
            for item in items:
                results.append({
                    "title": item.get("title"),
                    "snippet": item.get("snippet"),
                    "link": item.get("link")
                })
            return results
        else:
            return []

    def bing_search(self, query: str, num_results: int = 10) -> list[dict]:
        """
        Perform a web search using the Bing Search API.

        Args:
            query (str): The search query.
            num_results (int, optional): Number of results to return. Defaults to 10.

        Returns:
            list[dict]: A list of dictionaries with 'title', 'snippet', and 'link'.
        """
        if not self.bing_api_key:
            raise ValueError("Bing API key is not provided.")
        
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.bing_api_key}
        params = {
            "q": query,
            "count": num_results
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("webPages", {}).get("value", []):
                results.append({
                    "title": item.get("name"),
                    "snippet": item.get("snippet"),
                    "link": item.get("url")
                })
            return results
        else:
            return []

    def perplexity_search(self, query: str, num_results: int = 10) -> list[dict]:
        """
        Perform a web search using Perplexity AI's API.
        Note: This is a hypothetical implementation. Replace the URL and parameters
        with the correct ones if/when an official API is available.

        Args:
            query (str): The search query.
            num_results (int, optional): Number of results to return. Defaults to 10.

        Returns:
            list[dict]: A list of dictionaries with 'title', 'snippet', and 'link'.
        """
        if not self.perplexity_api_key:
            raise ValueError("Perplexity API key is not provided.")
        
        # Hypothetical endpoint and headers; update with official details as needed.
        url = "https://api.perplexity.ai/search"
        headers = {"Authorization": f"Bearer {self.perplexity_api_key}"}
        params = {
            "q": query,
            "limit": num_results
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            results = []
            # Assume that the API returns a "results" list with title, snippet, and link.
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title"),
                    "snippet": item.get("snippet") or item.get("description", ""),
                    "link": item.get("link") or item.get("url")
                })
            return results
        else:
            return []
    
    def duckduckgo_search(self, query, num_results=10):

        headers = {"User-Agent": random.choice(USER_AGENTS)}

        try:
            with DDGS(headers=headers) as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
            return [{
                "title": res.get("title", ""),
                "snippet": res.get("body", ""),
                "link": res.get("href", "")
            } for res in results]
        except Exception as e:
            print(f"Search failed: {str(e)}")
            return []
    


    # def duckduckgo_html_search(self, query, num_results=10):
    #     """
    #     Perform a search using DuckDuckGo's HTML API.
    #     """
    #     url = f"https://html.duckduckgo.com/html/?q={query}"
    #     headers = {"User-Agent": "Mozilla/5.0"}

    #     response = requests.get(url, headers=headers)
    #     if response.status_code == 200:
    #         return response.text  # Parse HTML to extract links
    #     else:
    #         return None


    def search(self, query: str, num_results: int = 20, engine: str = "duckduckgo") -> list[dict]:
        """
        Default search function that selects which API to use.

        Args:
            query (str): The search query.
            num_results (int, optional): Number of results to return. Defaults to 20.
            engine (str, optional): Which engine to use ('google', 'bing', or 'perplexity'). Defaults to "duckduckgo".

        Returns:
            list[dict]: A list of search results.
        """
        engine = engine.lower()
        if engine == "bing":
            return self.bing_search(query, num_results=num_results)
        elif engine == "perplexity":
            return self.perplexity_search(query, num_results=num_results)
        if engine == "google" and self.google_api_key and self.google_cx:
            return self.google_search(query, num_results)
        else:
            return self.duckduckgo_search(query, num_results)
