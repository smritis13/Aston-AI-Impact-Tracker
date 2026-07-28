import re
import openai
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from django.conf import settings
from django.utils import timezone
from content.models import Content, Category
from .image_generator import ContentImageGenerator
from core.llm.utils.ContentIndexer import ContentIndexer

# New imports for AsyncHtmlLoader and markdown conversion:
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import MarkdownifyTransformer
from langchain.schema import Document
from core.llm.utils.HtmlUtils import HtmlUtils


import markdownify

class ContentScraper:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def save_content_to_db(self, url: str, title: str, markdown_content: str, summary: str, 
                       tags: list[str], image_url: str, category_name: str, 
                       update_if_exists: bool = True) -> Content:
        """
        Saves or updates content in the database.
        
        Args:
            url (str): The URL of the content
            title (str): The title of the content
            markdown_content (str): The content in markdown format
            summary (str): A summary of the content
            tags (list[str]): List of tags
            image_url (str): URL of the content image
            category_name (str): Name of the category
            update_if_exists (bool): If True, update existing content scraped today
            
        Returns:
            Content: The saved or updated Content instance
        """
        # Get category object
        try:
            category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            raise Exception(f"Category with Name {category_name} does not exist")

        today = timezone.now().date()

        if update_if_exists:
            # Look for an existing content entry for this URL scraped today
            existing_content = Content.objects.filter(url=url).order_by("-scraped_at").first()
            if existing_content and existing_content.scraped_at.date() == today:
                # Update fields
                existing_content.title = title
                existing_content.original_content = markdown_content
                existing_content.summary = summary
                existing_content.tags = tags
                existing_content.image = image_url
                existing_content.category = category
                existing_content.scraped_at = timezone.now()
                existing_content.save()
                return existing_content

        # Otherwise, create a new Content object
        content = Content.objects.create(
            url=url,
            category=category,
            title=title,
            original_content=markdown_content,
            summary=summary,
            tags=tags,
            image=image_url
        )
        return content

    def scrape_and_save(self, url: str, update_if_exists: bool = True) -> Content:
        """
        Scrapes a URL using AsyncHtmlLoader, converts the HTML to Markdown,
        summarizes and tags the content using an LLM, extracts (or generates) a content image,
        and saves it to the Content model.
        
        The Markdown results are saved as original_content.
        
        If update_if_exists is True and the URL has already been scraped today,
        the existing Content object is updated.
        
        Args:
            url (str): The URL to scrape.
            update_if_exists (bool): If True, update existing content scraped today.
        
        Returns:
            Content: The saved or updated Content instance.
        """
        # Fetch the webpage using AsyncHtmlLoader (synchronously)
        try:
            loader = AsyncHtmlLoader([url])
            docs = loader.load()  # load() returns a list of Document objects
            if not docs:
                raise Exception(f"No documents returned for {url}")
            html = docs[0].page_content
        except Exception as e:
            raise Exception(f"Failed to fetch URL {url} using AsyncHtmlLoader: {str(e)}")
        
        # Parse the HTML with BeautifulSoup to extract title before cleaning
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title').get_text(strip=True) if soup.find('title') else None

        # Clean the HTML using HtmlUtils
        cleaned_html = HtmlUtils.clean_html(html)

        # Convert cleaned HTML to Markdown
        md = MarkdownifyTransformer()
        doc = Document(page_content=cleaned_html, metadata={"source": url})
        converted_docs = md.transform_documents([doc])
        markdown_content = converted_docs[0].page_content

        # Extract the main content for generating summary and tags
        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        if not main_content:
            raise Exception(f"Could not extract content from {url}")
        text_content = main_content.get_text(separator='\n', strip=True)

        # Generate summary, tags, and category using OpenAI
        summary, tags, category_name = self.generate_summary_and_tags(text_content)

        # Get content image: try to extract from HTML; if not found, generate using AI.
        image_generator = ContentImageGenerator()
        image_url = image_generator.get_content_image(url, html, summary)

        # Save content to database
        return self.save_content_to_db(
            url=url,
            title=title,
            markdown_content=markdown_content,
            summary=summary,
            tags=tags,
            image_url=image_url,
            category_name=category_name,
            update_if_exists=update_if_exists
        )

    def generate_summary_and_tags(self, text: str) -> tuple[str, list[str], str]:
        # ... (existing implementation remains unchanged)
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

    def extract_content_urls(self, website_url: str) -> list[str]:
        # ... (existing implementation remains unchanged)
        try:
            response = requests.get(website_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch website {website_url}: {str(e)}")

        soup = BeautifulSoup(response.text, "html.parser")
        parsed_base = urlparse(website_url)
        base_domain = parsed_base.netloc

        article_urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute_url = urljoin(website_url, href)
            parsed_url = urlparse(absolute_url)
            if parsed_url.netloc == base_domain:
                if HtmlUtils.should_scrape_url(website_url, absolute_url):
                    article_urls.add(absolute_url)

        return list(article_urls)

    def scrape_all_from_website(self, website_url: str) -> list:
        # ... (existing implementation remains unchanged)
        urls = self.extract_content_urls(website_url)
        scraped_urls = []
        indexer = ContentIndexer()

        for url in urls:
            try:
                content = self.scrape_and_save(url)
                scraped_urls.append(url)
                print("================================== >")
                print(f"Scraped {url}")
                indexer.index_content(content)
                print(f"Indexed {url}")
                print("================================== >")
            except Exception as e:
                print(f"Error scraping {url}: {str(e)}")
                continue
        return scraped_urls
