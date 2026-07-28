import openai
from bs4 import BeautifulSoup
from django.conf import settings

class ContentImageGenerator:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def extract_image_from_html(self, html: str) -> str:
        """
        Attempts to extract an image URL from the HTML using common tags.
        
        Returns:
            str: The image URL if found; otherwise, None.
        """
        soup = BeautifulSoup(html, 'html.parser')
        # Try to find an Open Graph image
        meta_img = soup.find("meta", property="og:image")
        if meta_img and meta_img.get("content"):
            return meta_img["content"]
        # Fallback: find the first <img> tag
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]
        return None

    def generate_image_via_ai(self, summary: str) -> str:
        """
        Generates an image using OpenAI's image API based on the content summary.
        
        Returns:
            str: The URL of the generated image.
        """
        prompt = f"Create an artistic illustration that represents the following summary: {summary}"
        try:
            image_response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = image_response['data'][0]['url']
            return image_url
        except Exception as e:
            raise Exception(f"Failed to generate image via AI: {str(e)}")

    def get_content_image(self, url: str, html: str, summary: str) -> str:
        """
        Returns an image URL for the content. Attempts to extract an image from the HTML first;
        if none is found, generates an image using the content summary.
        
        Args:
            url (str): The source URL (not used directly but could be useful for logging).
            html (str): The HTML content of the page.
            summary (str): The content summary used for AI generation if needed.
        
        Returns:
            str: The image URL.
        """
        image_url = self.extract_image_from_html(html)
        if image_url:
            return image_url
        return self.generate_image_via_ai(summary)
