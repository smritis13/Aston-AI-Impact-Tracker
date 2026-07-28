import asyncio
import json
import re
import openai
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from django.conf import settings
from django.utils import timezone
from .image_generator import ContentImageGenerator
from core.llm.utils.ContentIndexer import ContentIndexer
from content.models import Content, Category
from asgiref.sync import sync_to_async
from asgiref.sync import sync_to_async
import json


# crawl4ai and related imports
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from langchain_community.document_transformers import MarkdownifyTransformer
from langchain.schema import Document

# Import scraper utils for browser configuration
from core.llm.utils.scraper_utils import get_browser_config  # and get_llm_strategy if needed
from core.llm.utils.HtmlUtils import HtmlUtils

class CrawlAiScraper:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    async def fetch_page(self, url: str) -> tuple[str, str]:
        """
        Uses crawl4ai's AsyncWebCrawler to fetch the full HTML content of the given URL.
        Returns both the raw and cleaned HTML.
        """
        browser_config = get_browser_config()
        session_id = "crawl_ai_scrape_session"
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                session_id=session_id,
            )
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                raise Exception(f"Failed to fetch URL {url}: {result.error_message}")
            # Return both raw and cleaned HTML
            return result.html, result.cleaned_html

    async def save_content_to_db(self, url: str, title: str, content: str, markdown_content: str, summary: str, tags: list[str], image_url: str, category_name: str, update_if_exists: bool = True) -> Content:
        """
        Saves the content to the database, updating existing entries if applicable.
        """
        # Get the category object (wrap the ORM call)
        category = await sync_to_async(Category.objects.get)(name=category_name)

        today = timezone.now().date()

        # Check for existing content scraped today (wrapped ORM query)
        existing_content = await sync_to_async(lambda: Content.objects.filter(url=url).order_by("-scraped_at").first())()
        if update_if_exists and existing_content and existing_content.scraped_at.date() == today:
            existing_content.title = title
            existing_content.original_content = markdown_content  # Save Markdown as original content
            existing_content.summary = summary
            existing_content.tags = tags
            existing_content.image = image_url
            existing_content.content = content
            existing_content.category = category
            existing_content.scraped_at = timezone.now()
            await sync_to_async(existing_content.save)()
            return existing_content

        # Otherwise, create a new Content object (wrapped)
        content = await sync_to_async(Content.objects.create)(
            url=url,
            category=category,
            title=title,
            original_content=markdown_content,
            content=content,
            summary=summary,
            tags=tags,
            image=image_url
        )
        return content
    

    async def scrape_only(self, url: str) -> dict:
        """
        Asynchronously scrapes a URL using crawl4ai and returns extracted content
        without saving anything to the database.
        
        Returns:
            dict with title, text_content, markdown_content, summary, tags, category, image_url
        """
        try:
            raw_html, cleaned_html = await self.fetch_page(url)
        except Exception as e:
            print(f"Failed to fetch URL {url} using crawl4ai: {str(e)}")
            return {
                "url": url,
                "error": str(e)
            }

        soup = BeautifulSoup(raw_html, 'html.parser')
        title = soup.find('title').get_text(strip=True) if soup.find('title') else None

        cleaned_html = HtmlUtils.clean_html(cleaned_html)

        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        if not main_content:
            return {
                "url": url,
                "error": f"Could not extract main content"
            }
            

        text_content = main_content.get_text(separator='\n', strip=True)
        text_content = text_content.encode('utf-8', errors='ignore').decode('utf-8')  # Clean non-ASCII


        try:
            # content, summary, tags, category_name = await self.generate_markdown_summary_tags(text_content, url)


            return {
                "url": url,
                "title": title,
                "text": text_content,
            }
        except Exception as e:
            return {
                "url": url,
                "error": f"Failed to generate content for {url}: {str(e)}"
            }

    async def scrape_and_save(self, url: str, update_if_exists: bool = True) -> Content:
        """
        Asynchronously scrapes a URL using crawl4ai, converts the HTML to Markdown,
        generates a summary and tags using an LLM, extracts (or generates) a content image,
        and saves the result to the Content model.
        
        The Markdown version of the content is saved as original_content.
        """
        # Fetch the webpage asynchronously via crawl4ai
        try:
            raw_html, cleaned_html = await self.fetch_page(url)
        except Exception as e:
            print(f"Failed to fetch URL {url} using crawl4ai: {str(e)}")
            return None
            # raise Exception(f"Failed to fetch URL {url} using crawl4ai: {str(e)}")
        
        # Parse the original HTML to extract the title
        soup = BeautifulSoup(raw_html, 'html.parser')
        title = soup.find('title').get_text(strip=True) if soup.find('title') else None

        # Clean the HTML
        cleaned_html = HtmlUtils.clean_html(cleaned_html)

        # Use cleaned HTML for further processing
        # Convert HTML to Markdown using MarkdownifyTransformer
        md_transformer = MarkdownifyTransformer()
        doc = Document(page_content=cleaned_html, metadata={"source": url})
        converted_docs = md_transformer.transform_documents([doc])
        markdown_content = converted_docs[0].page_content

        # Extract the main content for generating summary and tags
        main_content = soup.find('article') or soup.find('main') or soup.find('body')
        if not main_content:
            raise Exception(f"Could not extract content from {url}")
        

        text_content = main_content.get_text(separator='\n', strip=True)
        text_content = text_content.encode('utf-8', errors='ignore').decode('utf-8')

        # Generate summary, tags, and category via OpenAI (wrapped appropriately for async)
        content, summary, tags, category_name = await self.generate_markdown_summary_tags(text_content, url)

        # Get content image (synchronously or wrap if needed)
        image_generator = ContentImageGenerator()
        image_url = image_generator.get_content_image(url, raw_html, summary)


        saved_content = await self.save_content_to_db(
            url, title, content, markdown_content, summary, tags, image_url, category_name, update_if_exists
        )

        # asyncio.create_task(self.validate_and_cleanup_content(saved_content, text_content))


        # Save content to the database
        return saved_content
    
    async def is_content_relevant(self, text: str) -> bool:
        """
        Determines if the content is relevant by using an LLM.
        Instructs the LLM to answer with 'Yes' if the content is relevant or 'No' otherwise.
        """
        prompt = (
            "You are a content analyst. "
            "Determine whether the following content is relevant for a performance and values tracker that "
            "answers daily consultant questions about topics such as industry tools, software development efficiency, "
            "and productivity improvements. "
            "Answer with a single word: 'Yes' if the content is relevant, or 'No' if it is not.\n\n"
            f"Content:\n{text}\n\n"
            "Answer:"
        )

        try:
            response = openai.chat.completions.create(
                    model="gpt-5.4-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0,
            )
            answer = response.choices[0].message.content.strip().lower()
            return answer.startswith("yes")
        except Exception as e:
            raise Exception(f"Failed to determine content relevance: {str(e)}")
    
    async def validate_and_cleanup_content(self, content: Content, text: str):
        """
        Validates the content relevance in the background using an LLM.
        If the content is deemed irrelevant, it deletes the content from the database and the index.
        """
        try:
            relevant = await self.is_content_relevant(text)
            if not relevant:
                indexer = ContentIndexer()
                indexer.delete_content(content)
                await sync_to_async(content.delete)()
                print(f"Deleted irrelevant content: {content.url}")
        except Exception as e:
            print(f"Error during background relevance validation for {content.url}: {e}")


    async def generate_markdown_summary_tags(self, text: str, url: str) -> tuple[str, str, list[str], str]:
        """
        Uses an LLM to generate clean markdown content, a summary, tags, and a category from the provided text.
        """
        # Get available categories
        categories = await sync_to_async(list)(Category.objects.all())
        category_list = [cat.name for cat in categories]
        categories_str = ", ".join(category_list) if category_list else "None"
        
        prompt = (
            "You are a content formatter, summarizer, tagger, and categorizer. "
            "Your task is to analyze the provided text and return a JSON object with specific fields.\n\n"
            "INSTRUCTIONS:\n"
            "1. Clean and format the main article content, removing headers, comments, navigation links, etc.\n"
            "2. Create a 5-6 sentence summary\n"
            "3. Generate 5-10 relevant tags\n"
            "4. Select the most appropriate category from the provided list\n\n"
            f"Available Categories: {categories_str}\n\n"
            "INPUT TEXT:\n"
            f"{text}\n\n"
            "RESPONSE FORMAT:\n"
            "You must respond with valid JSON only, using this exact structure:\n"
            "{\n"
            '    "markdown_content": "The cleaned article content in markdown format",\n'
            '    "summary": "Your 5-6 sentence summary here",\n'
            '    "tags": ["tag1", "tag2", "tag3", ...],\n'
            '    "category": "Exact category name from the provided list"\n'
            "}\n\n"
            "IMPORTANT:\n"
            "1. Use proper JSON syntax with double quotes for keys and string values\n"
            "2. Ensure the category exactly matches one from the provided list\n"
            "3. Return ONLY the JSON object, no other text\n"
            "4. DO NOT include any explanations or additional text before or after the JSON"
        )
        
        try:
            response = openai.chat.completions.create(
                    model="gpt-5.4-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise content processor that always responds with valid JSON. "
                            "Never include any text before or after the JSON. "
                            "Always use double quotes for keys and string values. "
                            "Always validate your response is proper JSON before sending."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            response_text = response.choices[0].message.content.strip()
            
            # Validate and parse the response
            try:
                parsed_data = self._validate_and_parse_llm_response(response_text)
                return parsed_data["markdown_content"], parsed_data["summary"], parsed_data["tags"], parsed_data["category"]
            except ValueError as e:
                # If first attempt fails, try one more time with a more explicit prompt
                retry_prompt = (
                    "The previous response was not properly formatted. "
                    "I need ONLY a valid JSON object with exactly these fields:\n"
                    "{\n"
                    '    "markdown_content": "string",\n'
                    '    "summary": "string",\n'
                    '    "tags": ["string", "string", ...],\n'
                    '    "category": "string"\n'
                    "}\n\n"
                    "Do not include any other text. Respond only with the JSON object.\n\n"
                    "Original text:\n" + text
                )
                
                retry_response = openai.chat.completions.create(
                        model="gpt-5.4-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a JSON formatter. Respond only with valid JSON. No other text."
                        },
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": "The previous response was invalid."},
                        {"role": "user", "content": retry_prompt}
                    ],
                    temperature=0.2
                )
                
                parsed_data = self._validate_and_parse_llm_response(retry_response.choices[0].message.content.strip())
                return parsed_data["markdown_content"], parsed_data["summary"], parsed_data["tags"], parsed_data["category"]
                
        except Exception as e:
            raise Exception(f"Error processing content: {str(e)}")

    def _validate_and_parse_llm_response(self, response_text: str) -> dict:
        """
        Validate and parse the LLM response to ensure it's proper JSON with required fields.
        
        Args:
            response_text (str): The raw response from the LLM
            
        Returns:
            dict: Parsed JSON with validated fields
            
        Raises:
            ValueError: If response is not valid JSON or missing required fields
        """
        try:
            # Try to parse the JSON
            data = json.loads(response_text)
            
            # Required fields and their types
            required_fields = {
                "markdown_content": str,
                "summary": str,
                "tags": list,
                "category": str
            }
            
            # Validate all required fields exist and are of correct type
            for field, field_type in required_fields.items():
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
                if not isinstance(data[field], field_type):
                    raise ValueError(f"Field {field} must be of type {field_type.__name__}")
            
            # Additional validation for tags
            if not all(isinstance(tag, str) for tag in data["tags"]):
                raise ValueError("All tags must be strings")
            # if not (5 <= len(data["tags"]) <= 10):
            #     raise ValueError("Must have between 5 and 10 tags")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    async def extract_content_urls(self, website_url: str) -> list[str]:
        """
        Uses crawl4ai to asynchronously fetch a webpage, parses it, and extracts links
        that are likely article URLs (based on domain matching and custom rules).
        """
        website_url = website_url.strip()

        try:
            browser_config = get_browser_config()
            session_id = "crawl_ai_extract_session"
            async with AsyncWebCrawler(config=browser_config) as crawler:
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    session_id=session_id,
                )
                result = await crawler.arun(url=website_url, config=config)
                if not result.success:
                    raise Exception(f"Failed to fetch website {website_url}: {result.error_message}")
                html = result.cleaned_html
        except Exception as e:
            raise Exception(f"Failed to fetch website {website_url} using crawl4ai: {str(e)}")

        soup = BeautifulSoup(html, "html.parser")
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

    async def scrape_all_from_website(self, website_url: str) -> list:
        """
        Extracts article URLs from the given website using crawl4ai and then scrapes each URL asynchronously.
        """
        urls = await self.extract_content_urls(website_url)
        scraped_urls = []
        indexer = ContentIndexer()

        for url in urls:
            try:
                content = await self.scrape_and_save(url)
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
