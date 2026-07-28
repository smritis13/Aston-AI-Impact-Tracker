import json

from urllib.parse import urlparse
from django.conf import settings
from asgiref.sync import sync_to_async
from datetime import datetime
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import re

class URLValidator:
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model="gpt-5.4-mini",
            temperature=0.3
        )

    async def rank_url(self, url):
        from content.models import WebsiteEvaluation

        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc.lower()
        
        # Remove 'www.' prefix if present
        if base_domain.startswith('www.'):
            base_domain = base_domain[4:]
        

        # Check existing evaluation
        evaluation = await sync_to_async(WebsiteEvaluation.objects.filter(base_domain=base_domain).first)()
        if evaluation:
            return evaluation.total_score, self._build_details(evaluation)

        # LLM prompt for domain evaluation (no content)
        system_prompt = (
    "You are a domain evaluation assistant. Given only a domain name (e.g., nytimes.com), "
    "you must estimate and classify the following fields in JSON format based on general knowledge, reputation, and available data:\n\n"
    "- source: The type of organization (e.g., News agency, Academic institution, Government body, Private company).\n"
    "- authority: The perceived credibility level of the domain. Choose one of: University, Government, Research firm, Corporate, Unknown.\n"
    "- bias_risk: The likelihood of the domain presenting biased or opinionated information. Choose one of: Very High, High, Medium, Low.\n"
    "- transparency: The clarity and openness of the domain about its information sources, authorship, and funding. Choose one of: Very High, High, Medium, Low.\n"
    "- peer_review: The extent to which the domain's content is reviewed by experts or credible sources. Choose one of: Very High, High, Medium, Low.\n"
    "- updated: True or False. Mark True if the website is known to publish or update content regularly (e.g., in the last 3 months).\n\n"
    "Return ONLY a JSON object with those six keys and no other explanation or text."
)

        human_message = f"Evaluate this domain: {base_domain}"
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_message)]

        response = self.llm.invoke(messages)

        
        cleaned_response = re.sub(r"^```json|```$", "", response.content.strip(), flags=re.MULTILINE)


        try:
            evaluation_data = json.loads(cleaned_response)
        except json.JSONDecodeError:
            evaluation_data = {
                "source": "Unknown", "authority": "Unknown", "bias_risk": "Medium",
                "transparency": "Medium", "peer_review": "Medium", "updated": False
            }

        # Score computation
        domain_authority_score = {
            "University": 3,
            "Government": 3,
            "Research firm": 2,
            "Corporate": 1
        }.get(evaluation_data.get("authority"), 0)


        security_score = 1 if url.startswith("https://") else 0
        recency_score = 3 if evaluation_data.get("updated") else 0

        # Map peer_review and other fields to numeric scores
        def score_level(value):
            return {"Very High": 3, "High": 2, "Medium": 1, "Low": 0}.get(value, 0)

        # Bias is a risk, not a quality signal.  The old calculation awarded
        # more points to "Very High" bias, which could make a promotional or
        # partisan site look more credible than a low-bias source.
        bias_safety_score = {
            "Very High": 0, "High": 1, "Medium": 2, "Low": 3
        }.get(evaluation_data.get("bias_risk"), 0)
        content_quality_score = (
            score_level(evaluation_data.get("peer_review")) +
            bias_safety_score +
            score_level(evaluation_data.get("transparency"))
        ) // 3  # Average score

        total_score = min(domain_authority_score + security_score + recency_score + content_quality_score, 10)

        # Save evaluation
        await sync_to_async(WebsiteEvaluation.objects.update_or_create)(
            base_domain=base_domain,
            defaults={
                "source": evaluation_data.get("source", "Unknown"),
                "authority": evaluation_data.get("authority", "Unknown"),
                "bias_risk": evaluation_data.get("bias_risk", "Medium"),
                "transparency": evaluation_data.get("transparency", "Medium"),
                "peer_review": evaluation_data.get("peer_review", "Medium"),
                "updated": evaluation_data.get("updated", False),
                "domain_authority_score": domain_authority_score,
                "security_score": security_score,
                "recency_score": recency_score,
                "content_quality_score": content_quality_score,
                "total_score": total_score,
            }
        )

        return total_score, {
            "domain_authority_score": domain_authority_score,
            "security_score": security_score,
            "recency_score": recency_score,
            "content_quality_score": content_quality_score,
            "total_score": total_score
        }

    async def evaluate_url(self, url):
        from content.models import WebsiteEvaluation

        base_domain = urlparse(url).netloc.lower()
        evaluation = await sync_to_async(WebsiteEvaluation.objects.filter(base_domain=base_domain).first)()


        if evaluation:
            return {
                "score": evaluation.total_score,
                "base_domain": base_domain,
                "details": self._build_details(evaluation)
            }

        score, details = await self.rank_url(url)
        return {
            "score": score,
            "base_domain": base_domain,
            "details": details
        }

    def _build_details(self, evaluation):
        return {
            "domain_authority_score": evaluation.domain_authority_score,
            "security_score": evaluation.security_score,
            "recency_score": evaluation.recency_score,
            "content_quality_score": evaluation.content_quality_score,
            "total_score": evaluation.total_score
        }
