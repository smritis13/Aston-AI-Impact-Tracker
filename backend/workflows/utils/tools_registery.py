# workflows/utils/tools_registery.py
from langchain.tools import BaseTool, tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.serpapi import SerpAPIWrapper
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun
from langchain_community.tools.requests.tool import RequestsGetTool
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.tools.youtube.search import YouTubeSearchTool
from langchain_experimental.utilities.python import PythonREPL
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json
import requests
import datetime
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
from typing import Optional, Any


class ToolRegistry:
    _tools = {}
    
    @classmethod
    def register_tool(cls, tool_id, tool_class, description, parameters_schema=None, requires_api_key=False):
        cls._tools[tool_id] = {
            "class": tool_class,
            "description": description,
            "parameters_schema": parameters_schema,
            "requires_api_key": requires_api_key
        }
    
    @classmethod
    def get_tool(cls, tool_id, api_keys=None):
        """Get a tool instance by ID with API keys from the database."""
        if tool_id not in cls._tools:
            raise ValueError(f"Tool {tool_id} not found in registry")
        
        tool_info = cls._tools[tool_id]
        
        if tool_info["requires_api_key"]:
            if not api_keys or tool_id not in api_keys:
                raise ValueError(f"Tool {tool_id} requires an API key, but none was provided in api_keys")
            return tool_info["class"](api_keys[tool_id])
        return tool_info["class"]()

    @classmethod
    def list_tools(cls):
        return {
            tool_id: {
                "description": info["description"],
                "requires_api_key": info["requires_api_key"],
                "parameters_schema": info["parameters_schema"]
            }
            for tool_id, info in cls._tools.items()
        }

def register_search_tools():
    class TavilySearchTool(BaseTool):
        name: str = "tavily_search"
        description: str = "Advanced web search using Tavily AI. Returns detailed search results."
        search: Optional[TavilySearchResults] = None
        
        def __init__(self, api_key):
            super().__init__()
            # we set a default max_results; callers may override when instantiating
            self.search = TavilySearchResults(tavily_api_key=api_key, max_results=10)
        
        def _run(self, query: str, max_results: Optional[int] = None) -> list:
            """Search the web and return a capped list of results.

            ``max_results`` may be provided by callers (e.g. the API view) when they
            want fewer than the default set during initialization.  We still slice a
            second time to protect against library bugs.
            """
            try:
                results = self.search.run(query)
                if not isinstance(results, list):
                    return results
                limit = max_results or getattr(self.search, "max_results", None)
                if limit is not None and len(results) > limit:
                    return results[:limit]
                return results
            except Exception as e:
                return [{"error": str(e)}]
    
    ToolRegistry.register_tool(
        "tavily_search",
        TavilySearchTool,
        "Advanced web search using Tavily AI. Returns detailed search results with better understanding.",
        {
            "query": "The search query string",
            "max_results": "Optional integer limit for number of results (default inherits from tool initialization)"
        },
        requires_api_key=True
    )
    
    class SerpAPISearchTool(BaseTool):
        name: str = "serpapi_search"
        description: str = "Search the web using SerpAPI. Returns snippets and links."
        search: Optional[SerpAPIWrapper] = None
        
        def __init__(self, api_key):
            super().__init__()
            self.search = SerpAPIWrapper(serpapi_api_key=api_key)
        
        def _run(self, query: str) -> list:  # Change return type to list
            try:
                # Get raw JSON results from SerpAPI
                results = self.search.results(query)
                # Extract organic_results and format as a list
                organic_results = results.get("organic_results", [])
                return [
                    {
                        "title": result.get("title", ""),
                        "url": result.get("link", ""),
                        "snippet": result.get("snippet", "")+ " " +result.get("source", "")
                    }
                    for result in organic_results
                ]
            except Exception as e:
                return [{"error": str(e)}]
    
    ToolRegistry.register_tool(
        "serpapi_search",
        SerpAPISearchTool,
        "Search the web using SerpAPI. Returns snippets and links from search results.",
        {"query": "The search query string"},
        requires_api_key=True
    )
    
    class DuckDuckGoSearchTool(BaseTool):
        name: str = "duckduckgo_search"
        description: str = "Search the web using DuckDuckGo. Returns snippets."
        search: Optional[DuckDuckGoSearchRun] = None
        
        def __init__(self):
            super().__init__()
            self.search = DuckDuckGoSearchRun()
        
        def _run(self, query: str) -> str:
            return self.search.run(query)
    
    ToolRegistry.register_tool(
        "duckduckgo_search",
        DuckDuckGoSearchTool,
        "Search the web using DuckDuckGo. Returns snippets from search results.",
        {"query": "The search query string"},
        requires_api_key=False
    )

def register_knowledge_tools():
    class WikipediaTool(BaseTool):
        name: str = "wikipedia"
        description: str = "Search Wikipedia and get article summaries."
        search: Optional[WikipediaQueryRun] = None
        
        def __init__(self):
            super().__init__()
            self.search = WikipediaQueryRun()
        
        def _run(self, query: str) -> str:
            return self.search.run(query)
    
    ToolRegistry.register_tool(
        "wikipedia",
        WikipediaTool,
        "Search Wikipedia and get article summaries.",
        {"query": "The search query string"},
        requires_api_key=False
    )
    
    class ArxivTool(BaseTool):
        name: str = "arxiv"
        description: str = "Search academic papers on Arxiv."
        search: Optional[ArxivQueryRun] = None
        
        def __init__(self):
            super().__init__()
            self.search = ArxivQueryRun()
        
        def _run(self, query: str) -> str:
            return self.search.run(query)
    
    ToolRegistry.register_tool(
        "arxiv",
        ArxivTool,
        "Search academic papers on Arxiv.",
        {"query": "The search query string"},
        requires_api_key=False
    )
    
    class YouTubeSearchToolWrapper(BaseTool):
        name: str = "youtube_search"
        description: str = "Search for YouTube videos."
        search: Optional[YouTubeSearchTool] = None
        
        def __init__(self, api_key):
            super().__init__()
            self.search = YouTubeSearchTool(api_key=api_key)
        
        def _run(self, query: str) -> str:
            return self.search.run(query)
    
    ToolRegistry.register_tool(
        "youtube_search",
        YouTubeSearchToolWrapper,
        "Search for YouTube videos.",
        {"query": "The search query string"},
        requires_api_key=True
    )

def register_data_tools():
    class PythonREPLTool(BaseTool):
        name: str = "python_repl"
        description: str = "Execute Python code and return the result."
        repl: Optional[PythonREPL] = None
        
        def __init__(self):
            super().__init__()
            self.repl = PythonREPL()
        
        def _run(self, code: str) -> str:
            return self.repl.run(code)
    
    ToolRegistry.register_tool(
        "python_repl",
        PythonREPLTool,
        "Execute Python code and return the result. Useful for calculations, data processing, and more.",
        {"code": "The Python code to execute"},
        requires_api_key=False
    )
    
    @tool
    def json_parser(json_string, path):
        """Parse JSON and extract values using dot notation path."""
        try:
            data = json.loads(json_string)
            parts = path.split('.')
            result = data
            for part in parts:
                if part.isdigit() and isinstance(result, list):
                    result = result[int(part)]
                elif isinstance(result, dict):
                    result = result.get(part)
                else:
                    return f"Error: Cannot access '{part}' in {type(result)}"
            return json.dumps(result)
        except Exception as e:
            return f"Error parsing JSON: {str(e)}"
    
    ToolRegistry.register_tool(
        "json_parser",
        lambda _: json_parser,
        "Extract values from JSON using dot notation path (e.g., 'results.0.title').",
        {
            "json_string": "The JSON string to parse",
            "path": "Dot notation path to extract (e.g., 'results.0.title')"
        },
        requires_api_key=False
    )
    
    @tool
    def csv_analyzer(csv_data, query):
        """Analyze CSV data using pandas."""
        try:
            df = pd.read_csv(StringIO(csv_data))
            result = eval(query, {"__builtins__": {}}, {"df": df, "pd": pd})
            if isinstance(result, pd.DataFrame):
                return result.to_string()
            return str(result)
        except Exception as e:
            return f"Error analyzing CSV: {str(e)}"
    
    ToolRegistry.register_tool(
        "csv_analyzer",
        lambda _: csv_analyzer,
        "Analyze CSV data using pandas. Write pandas code that uses the DataFrame 'df'.",
        {
            "csv_data": "The CSV data as a string",
            "query": "Pandas code that uses 'df' as the DataFrame (e.g., 'df.describe()')"
        },
        requires_api_key=False
    )

def register_web_tools():
    class HTTPGetTool(BaseTool):
        name: str = "http_get"
        description: str = "Make an HTTP GET request and return the response."
        request: Optional[RequestsGetTool] = None
        
        def __init__(self):
            super().__init__()
            self.request = RequestsGetTool()
        
        def _run(self, url: str) -> str:
            return self.request.run(url)
    
    ToolRegistry.register_tool(
        "http_get",
        HTTPGetTool,
        "Make an HTTP GET request to the specified URL and return the response.",
        {"url": "The URL to send the GET request to"},
        requires_api_key=False
    )
    
    @tool
    def html_parser(html_content, css_selector):
        """Extract content from HTML using CSS selectors."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            elements = soup.select(css_selector)
            return "\n".join([el.get_text().strip() for el in elements])
        except Exception as e:
            return f"Error parsing HTML: {str(e)}"
    
    ToolRegistry.register_tool(
        "html_parser",
        lambda _: html_parser,
        "Extract content from HTML using CSS selectors.",
        {
            "html_content": "The HTML content to parse",
            "css_selector": "CSS selector to extract elements (e.g., 'div.content p')"
        },
        requires_api_key=False
    )

def register_utility_tools():
    @tool
    def calculator(expression):
        """Calculate the result of a mathematical expression."""
        try:
            allowed_names = {"abs": abs, "pow": pow, "round": round, "int": int, "float": float, "max": max, "min": min}
            return str(eval(expression, {"__builtins__": {}}, allowed_names))
        except Exception as e:
            return f"Error calculating: {str(e)}"
    
    ToolRegistry.register_tool(
        "calculator",
        lambda _: calculator,
        "Evaluate mathematical expressions safely.",
        {"expression": "The mathematical expression to evaluate"},
        requires_api_key=False
    )
    
    @tool
    def datetime_tool(format_string="%Y-%m-%d %H:%M:%S", days_delta=0):
        """Get current date and time, optionally with a delta in days."""
        try:
            date = datetime.datetime.now() + datetime.timedelta(days=float(days_delta))
            return date.strftime(format_string)
        except Exception as e:
            return f"Error processing date: {str(e)}"
    
    ToolRegistry.register_tool(
        "datetime",
        lambda _: datetime_tool,
        "Get current date/time or calculate relative dates.",
        {
            "format_string": "Format string (default '%Y-%m-%d %H:%M:%S')",
            "days_delta": "Days to add/subtract (can be decimal, default 0)"
        },
        requires_api_key=False
    )

def register_text_tools():
    class TranslatorTool(BaseTool):
        name: str = "translator"
        description: str = "Translate text between languages."
        api_key: Optional[str] = None
        
        def __init__(self, api_key):
            super().__init__()
            self.api_key = api_key
        
        def _run(self, text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
            if not self.api_key:
                return "Translation requires API key"
            try:
                url = "https://translation.googleapis.com/language/translate/v2"
                params = {"q": text, "target": target_lang, "key": self.api_key}
                if source_lang != "auto":
                    params["source"] = source_lang
                response = requests.post(url, params=params)
                if response.status_code == 200:
                    return response.json()["data"]["translations"][0]["translatedText"]
                return f"Translation error: {response.text}"
            except Exception as e:
                return f"Error during translation: {str(e)}"
    
    ToolRegistry.register_tool(
        "translator",
        TranslatorTool,
        "Translate text between languages.",
        {
            "text": "Text to translate",
            "source_lang": "Source language code (or 'auto' for automatic detection)",
            "target_lang": "Target language code (e.g., 'en', 'es', 'fr')"
        },
        requires_api_key=True
    )
    
    class TextSummarizerTool(BaseTool):
        name: str = "text_summarizer"
        description: str = "Summarize long texts using AI."
        llm: Optional[ChatOpenAI] = None
        prompt: Optional[ChatPromptTemplate] = None
        chain: Optional[Any] = None
        
        def __init__(self):
            super().__init__()
            self.llm = ChatOpenAI(temperature=0)
            self.prompt = ChatPromptTemplate.from_template(
                "Summarize the following text in {max_length} words or less:\n\n{text}"
            )
            self.chain = self.prompt | self.llm | StrOutputParser()
        
        def _run(self, text: str, max_length: int = 200) -> str:
            try:
                return self.chain.invoke({"text": text, "max_length": max_length})
            except Exception as e:
                return f"Error summarizing text: {str(e)}"
    
    ToolRegistry.register_tool(
        "text_summarizer",
        TextSummarizerTool,
        "Summarize long texts using AI.",
        {
            "text": "The text to summarize",
            "max_length": "Maximum length of summary in words (default 200)"
        },
        requires_api_key=False
    )

def register_all_tools():
    register_search_tools()
    register_knowledge_tools()
    register_data_tools()
    register_web_tools()
    register_utility_tools()
    register_text_tools()

def initialize_tools():
    register_all_tools()