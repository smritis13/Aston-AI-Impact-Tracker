import asyncio
import io
import re
import requests
import aiohttp
import pdfplumber
from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain.schema import Document
from langchain_community.document_transformers import MarkdownifyTransformer
import logging
from urllib.parse import urlparse

PDF_MAX_PAGES = 30

class SimpleHtmlScraper:
    """
    A lightweight HTML scraper that uses AsyncHtmlLoader (aiohttp) for fetching and BeautifulSoup for parsing.
    Features:
    - Asynchronous fetching using aiohttp
    - BeautifulSoup for HTML parsing and cleaning
    - Metadata extraction from meta tags
    - Automatic removal of non-essential elements (scripts, styles, headers, footers, etc.)
    - Text cleaning and formatting
    - Fallback to requests with retry mechanism if needed
    """
    def __init__(self, timeout=10, max_retries=2):
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        self.metadata = {}  # Store metadata here
        
    async def scrape_only(self, url: str) -> dict:
        """
        Scrapes a URL without using Playwright or Chromium.
        Returns extracted plain text (body or article).
        
        Args:
            url (str): The URL to scrape
        
        Returns:
            dict: Dictionary containing url and extracted text
        """
        if not url or not isinstance(url, str):
            return {"url": url, "text": ""}
            
        try:
            # Reset metadata for new scrape
            self.metadata = {}
            
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {"url": url, "text": "Invalid URL"}

            if parsed.path.lower().endswith(".pdf"):
                return await self._scrape_pdf(url)

            # Use AsyncHtmlLoader which uses aiohttp under the hood (no browser)
            loader = AsyncHtmlLoader([url])
            docs = await loader.aload()
            
            if not docs:
                return {"url": url, "text": ""}
                
            html = docs[0].page_content
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find the main content
            content = None
            
            # Clean the entire content and get text with metadata
            text = self._clean_content(soup)
            
            if not text:
                return {"url": url, "text": ""}
            
            # Clean up text
            text = self._clean_text(text)
            
            return {
                "url": url,
                "text": text
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return {"url": url, "text": f"Error: {str(e)}"}

    async def _scrape_pdf(self, url: str) -> dict:
        """
        Downloads a PDF and extracts its text with pdfplumber instead of
        treating it as HTML (which fails to decode the binary content).
        """
        try:
            timeout = aiohttp.ClientTimeout(total=max(self.timeout, 20))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    pdf_bytes = await response.read()

            text = await asyncio.to_thread(self._extract_pdf_text, pdf_bytes)
            return {"url": url, "text": self._clean_text(text)}
        except Exception as e:
            self.logger.error(f"Error scraping PDF {url}: {str(e)}")
            return {"url": url, "text": f"Error: {str(e)}"}

    @staticmethod
    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        text_content = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:PDF_MAX_PAGES]:
                text_content.append(page.extract_text() or "")
        return "\n".join(text_content).strip()

    def _clean_text(self, text: str) -> str:
        """
        Clean up extracted text.
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned text
        """

        if(text is None):
            return ""
        
        # Replace multiple newlines with a single one
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text
    
    async def fetch_with_retry(self, url: str) -> str:
        """
        Fetch URL content with retry mechanism.
        
        Args:
            url (str): The URL to fetch
            
        Returns:
            str: HTML content
        """
        attempts = 0
        while attempts < self.max_retries:
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                attempts += 1
                if attempts >= self.max_retries:
                    raise e
                await asyncio.sleep(1)  # Wait before retrying
                
        return ""

    def _clean_content(self, content: BeautifulSoup) -> str:
        """
        Clean the HTML content by removing non-essential elements.
        Extracts metadata from meta tags and returns the cleaned text with metadata.
        
        Args:
            content (BeautifulSoup): The BeautifulSoup object containing the content
            
        Returns:
            str: Cleaned text with metadata
        """
        # Extract metadata from meta tags. Publish-date tags in particular are
        # usually declared via property= (Open Graph: article:published_time,
        # og:updated_time) or the "name="-only lookup below silently misses
        # them, leaving the extraction LLM with no reliable publish-date
        # signal for pages that don't show a visible byline.
        for meta in content.find_all('meta'):
            name = meta.get('name', '') or meta.get('property', '')
            content_value = meta.get('content', '')
            if name and content_value:
                self.metadata[name] = content_value

        # JSON-LD (schema.org) is the other common place a page declares its
        # own publish date and isn't a <meta> tag at all - many gov.uk/news
        # sites rely on it exclusively. Pull datePublished/dateModified
        # before the <script> tags get stripped below.
        for script in content.find_all('script', attrs={'type': 'application/ld+json'}):
            script_text = script.string or script.get_text() or ''
            for key in ('datePublished', 'dateModified'):
                match = re.search(rf'"{key}"\s*:\s*"([^"]+)"', script_text)
                if match and key not in self.metadata:
                    self.metadata[key] = match.group(1)

        # Elements to remove
        elements_to_remove = [
            "header", "footer", "nav", "aside",
            "form", "button", "input", "select",
            "iframe", "noscript", "svg", "img",
            "style", "script", "link", "meta"
        ]
        
        # Remove elements by tag name
        for element in elements_to_remove:
            for tag in content.find_all(element):
                tag.decompose()
        
        # Remove elements by common class names
        common_classes = [
            "header", "footer", "navigation", "nav",
            "sidebar", "menu", "banner", "advertisement",
            "ad", "social", "share", "comment",
            "related", "recommended", "popular"
        ]
        
        for class_name in common_classes:
            for tag in content.find_all(class_=re.compile(class_name, re.I)):
                tag.decompose()
        
        # Remove elements by common IDs
        common_ids = [
            "header", "footer", "nav", "sidebar",
            "menu", "banner", "ad", "social",
            "share", "comment", "related"
        ]
        
        for id_name in common_ids:
            for tag in content.find_all(id=re.compile(id_name, re.I)):
                tag.decompose()
        
        # Extract text from the cleaned content
        text = content.get_text(separator="\n", strip=True)

        # Append metadata if any exists
        if self.metadata:
            text += "\n\nMetadata:\n"
            for name, value in self.metadata.items():
                text += f"{name}: {value}\n"
        
        return text