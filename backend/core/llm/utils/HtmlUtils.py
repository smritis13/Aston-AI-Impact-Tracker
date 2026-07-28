from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

class HtmlUtils:
    @staticmethod
    def clean_html(html: str) -> str:
        """
        Cleans the HTML by removing unnecessary elements such as header, footer, sidebar, and other non-essential tags.
        """
        soup = BeautifulSoup(html, 'html.parser')

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Remove header, footer, and sidebar elements
        for tag in ['header', 'footer', 'aside', 'nav']:
            for element in soup.find_all(tag):
                element.decompose()

        # Optionally remove other elements by class or id
        for class_name in ['sidebar', 'advertisement', 'ad', 'promo']:
            for element in soup.find_all(class_=class_name):
                element.decompose()

        for id_name in ['sidebar', 'advertisement', 'ad', 'promo']:
            for element in soup.find_all(id=id_name):
                element.decompose()

        return str(soup)

    @staticmethod
    def should_scrape_url(website_url: str, candidate_url: str) -> bool:
        """
        Determines if a candidate URL should be scraped based on the originating website.
        """
        parsed_base = urlparse(website_url)
        base_domain = parsed_base.netloc.lower()

        if "techcrunch.com" in base_domain:
            return bool(re.search(r"/\d{4}/\d{2}/\d{2}/", candidate_url))
        if "wired.com" in base_domain:
            return "/story/" in candidate_url
        if "https://www.alpha-sense.com" in base_domain:
            return "/blog/" in candidate_url

        parsed_candidate = urlparse(candidate_url)
        return parsed_candidate.netloc == base_domain 