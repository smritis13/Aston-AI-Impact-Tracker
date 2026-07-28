
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, TypeVar, Generic

import requests
from django.conf import settings

T = TypeVar('T')


class SerperAPIException(Exception):
    """Custom exception for Serper API related errors"""
    pass


@dataclass
class SerperConfig:
    """Configuration for Serper API"""
    api_key: str
    api_url: str = "https://google.serper.dev/search"
    default_location: str = 'us'
    timeout: int = 10

    @classmethod
    def from_settings(cls) -> 'SerperConfig':
        api_key = getattr(settings, 'SERPER_API_KEY', None)
        if not api_key:
            raise SerperAPIException("SERPER_API_KEY is not set in Django settings.")
        return cls(api_key=api_key)


class SearchResult(Generic[T]):
    def __init__(self, data: Optional[T] = None, error: Optional[str] = None):
        self.data = data
        self.error = error
        self.success = error is None

    @property
    def failed(self) -> bool:
        return not self.success


class SerperAPI:
    def __init__(self, config: Optional[SerperConfig] = None):
        self.config = config or SerperConfig.from_settings()
        self.headers = {
            'X-API-KEY': self.config.api_key,
            'Content-Type': 'application/json'
        }

    @staticmethod
    def extract_fields(items: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
        return [{key: item.get(key, "") for key in fields if key in item} for item in items]

    def get_sources(self, query: str, num_results: int = 8, stored_location: Optional[str] = None) -> SearchResult[Dict[str, Any]]:
        if not query.strip():
            return SearchResult(error="Query cannot be empty")

        try:
            location = (stored_location or self.config.default_location).lower()
            payload = {
                "q": query,
                "num": min(max(1, num_results), 10),
                "gl": location
            }

            response = requests.post(
                self.config.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()

            results = {
                'organic': self.extract_fields(data.get('organic', []), ['title', 'link', 'snippet', 'date']),
                'topStories': self.extract_fields(data.get('topStories', []), ['title', 'imageUrl']),
                'images': self.extract_fields(data.get('images', [])[:6], ['title', 'imageUrl']),
                'graph': data.get('knowledgeGraph'),
                'answerBox': data.get('answerBox'),
                'peopleAlsoAsk': data.get('peopleAlsoAsk'),
                'relatedSearches': data.get('relatedSearches')
            }

            return SearchResult(data=results)

        except requests.RequestException as e:
            return SearchResult(error=f"API request failed: {str(e)}")
        except Exception as e:
            return SearchResult(error=f"Unexpected error: {str(e)}")
