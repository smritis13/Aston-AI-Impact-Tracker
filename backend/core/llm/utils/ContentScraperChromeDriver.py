import os
import time
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import openai
from django.conf import settings
from content.models import Content, Category
from .image_generator import ContentImageGenerator
from core.llm.utils.ContentIndexer import ContentIndexer
from dotenv import load_dotenv
import undetected_chromedriver as uc

class ContentScraper:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        load_dotenv()

    def _get_page_source(self, url: str, wait: int = 3) -> str:
        """
        Uses undetected-chromedriver with common options to fetch a page and return its HTML source.
        """
        try:
            options = uc.ChromeOptions()
            options.binary_location = "/usr/bin/google-chrome"  # Ensure Chrome is installed in your container
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
            # Initialize the driver using undetected-chromedriver
            driver = uc.Chrome(options=options)
            driver.get(url)
            time.sleep(wait)  # Consider replacing with WebDriverWait for production use
            page_source = driver.page_source
            driver.quit()
            return page_source
        except Exception as e:
            raise Exception(f"Failed to fetch website {url} using Selenium: {str(e)}")

    def extract_content_urls(self, website_url: str) -> list[str]:
        """
        Uses Selenium (via undetected-chromedriver) to fetch a page, extracts links likely to be articles,
        and returns a list of URLs.
        """
        page_source = self._get_page_source(website_url, wait=3)
        soup = BeautifulSoup(page_source, "html.parser")
        parsed_base = urlparse(website_url)
        base_domain = parsed_base.netloc

        article_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute_url = urljoin(website_url, href)
            parsed_url = urlparse(absolute_url)
            if parsed_url.netloc == base_domain:
                if self.should_scrape_url(website_url, absolute_url):
                    article_urls.add(absolute_url)
        return list(article_urls)

    def scrape_and_save(self, url: str, update_if_exists: bool = True) -> Content:
        """
        Scrapes a URL using Selenium to fetch the HTML, extracts and processes the content,
        generates summary/tags via OpenAI, extracts or generates an image, and then saves
        the result to the Content model. If update_if_exists is True and the URL was scraped today,
        the existing content is updated.
        """
        # Fetch the webpage using our common Selenium scraper
        page_source = self._get_page_source(url, wait=3)
        soup = BeautifulSoup(page_source, 'html.parser')

        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        if not main_content:
            raise Exception(f"Could not extract content from {url}")
        text_content = main_content.get_text(separator='\n', strip=True)

        title = soup.find('title').get_text(strip=True) if soup.find('title') else None

        # Generate summary, tags, and best matching category using OpenAI
        summary, tags, category_name = self.generate_summary_and_tags(text_content)
        print('====================================')
        print(category_name)
        print('====================================')

        # Get content image (extract from HTML or generate using AI)
        image_generator = ContentImageGenerator()
        image_url = image_generator.get_content_image(url, page_source, summary)
        print(image_url)

        try:
            category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            raise Exception(f"Category with Name {category_name} does not exist")

        from django.utils import timezone
        today = timezone.now().date()

        if update_if_exists:
            existing_content = Content.objects.filter(url=url).order_by("-scraped_at").first()
            if existing_content and existing_content.scraped_at.date() == today:
                existing_content.title = title
                existing_content.original_content = text_content
                existing_content.summary = summary
                existing_content.tags = tags
                existing_content.image = image_url
                existing_content.category = category
                existing_content.scraped_at = timezone.now()
                existing_content.save()
                return existing_content

        content = Content.objects.create(
            url=url,
            category=category,
            title=title,
            original_content=text_content,
            summary=summary,
            tags=tags,
            image=image_url
        )
        return content

    def scrape_all_from_website(self, website_url: str) -> list:
        """
        Extracts article URLs from the provided website URL and then scrapes each URL one by one.
        """
        urls = self.extract_content_urls(website_url)
        scraped_urls = []
        indexer = ContentIndexer()

        for url in urls:
            try:
                content = self.scrape_and_save(url)
                scraped_urls.append(url)
                indexer.index_content(content)
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                continue
        return scraped_urls

    def generate_summary_and_tags(self, text: str) -> tuple[str, list[str], str]:
        """
        Uses OpenAI to generate a summary, tags, and the best matching category for the given text.
        """
        if len(text) > 10000:
            text = text[:10000] + "\n[Content truncated]"

        categories = Category.objects.all()
        category_list = [cat.name for cat in categories]
        categories_str = ", ".join(category_list) if category_list else "None"

        prompt = (
            "You are a content summarizer, tagger, and categorizer. "
            "Given the content below and the list of available categories, provide a concise summary (2-3 sentences), "
            "a list of relevant tags (5-10 keywords), and suggest the best matching category from the list. "
            "Format your response exactly as follows:\n\n"
            "Summary: [Your summary here]\n"
            "Tags: tag1, tag2, tag3, ...\n"
            "Category: [Best matching category]\n\n"
            f"Available Categories: {categories_str}\n\n"
            f"Content:\n{text}"
        )

        try:
            response = openai.chat.completions.create(
                model="gpt-5.4-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            response_text = response.choices[0].message.content.strip()
            summary, tags, category_name = None, None, None

            for line in response_text.split('\n'):
                if line.startswith("Summary:"):
                    summary = line.replace("Summary:", "").strip()
                elif line.startswith("Tags:"):
                    tags = [tag.strip() for tag in line.replace("Tags:", "").split(',') if tag.strip()]
                elif line.startswith("Category:"):
                    category_name = line.replace("Category:", "").strip()

            if not summary or not tags or category_name is None:
                raise ValueError("LLM response did not include summary, tags, or category")

            return summary, tags, category_name

        except Exception as e:
            raise Exception(f"Failed to generate summary and tags: {str(e)}")

    def should_scrape_url(self, website_url: str, candidate_url: str) -> bool:
        """
        Determines if a candidate URL should be scraped based on the originating website.
        """
        parsed_base = urlparse(website_url)
        base_domain = parsed_base.netloc.lower()

        if "techcrunch.com" in base_domain:
            return bool(re.search(r"/\d{4}/\d{2}/\d{2}/", candidate_url))
        if "wired.com" in base_domain:
            return "/story/" in candidate_url
        if "infoq.com" in base_domain:
            return bool(re.search(r"/(articles|podcasts|news|interviews)/", candidate_url))

        parsed_candidate = urlparse(candidate_url)
        return parsed_candidate.netloc == base_domain
