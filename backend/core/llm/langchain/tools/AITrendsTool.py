from langchain.tools import Tool
from django.utils.timezone import now
from content.models import Content, Report
from langchain.schema import SystemMessage, HumanMessage
from django.utils import timezone

class AITrendsTool:
    """
    A custom LangChain tool that retrieves and analyzes current AI development trends,
    tools, and technologies. It tracks emerging AI tools, frameworks, and development
    practices while storing reports to avoid redundant processing.
    """

    def __init__(self, llm, max_entries=12):
        self.llm = llm
        self.max_entries = max_entries  # Limit the number of retrieved entries

    def fetch_relevant_content(self, focus_area=None):
        """
        Fetches relevant AI development trends and tools content from the database.
        
        Args:
            focus_area (str): Optional specific area to focus on (e.g., 'coding', 'agents', 'mlops')
        """
        query = Content.objects.all()
        
        # Add focus area filtering if specified
        if focus_area:
            query = query.filter(title__icontains=focus_area)
            
        relevant_content = query.order_by('-created_at')[:self.max_entries]
        
        return [
            {
                "title": content.title,
                "text": content.original_content,
                "created_at": content.created_at
            }
            for content in relevant_content
        ]

    def generate_report(self, query, focus_area=None, force_regenerate=False):
        """
        Generates a comprehensive report on AI development trends and tools.
        If `force_regenerate` is False, it first checks if a recent report exists.
        
        Args:
            query (str): The specific query about AI development trends/tools
            focus_area (str): Optional specific area to focus on
            force_regenerate (bool): If True, regenerate report even if it exists
        """
        topic = f"AI Development Trends and Tools{f' - {focus_area}' if focus_area else ''}"

        # Check if a recent report exists
        if not force_regenerate:
            existing_report = Report.objects.filter(
                topic=topic,
                updated_at__gte=now() - timezone.timedelta(days=1)  # Reports older than 1 day are regenerated
            ).first()
            if existing_report:
                return existing_report.generated_report

        relevant_content = self.fetch_relevant_content(focus_area=focus_area)

        if not relevant_content:
            return "No relevant AI development trends content found."

        # Convert retrieved content into a readable format
        content_text = "\n\n".join([
            f"Title: {c['title']}\nDate: {c['created_at']}\nText: {c['text']}" 
            for c in relevant_content
        ])

        system_prompt = (
            "You are an AI that generates comprehensive reports about the latest AI development "
            "trends, tools, and technologies. Focus on:"
            "\n1. AI-powered development tools"
            "\n2. AI agents and autonomous systems"
            "\n3. Large Language Model applications and frameworks"
            "\n4. MLOps and AI infrastructure tools"
            "\n5. AI-assisted code generation and analysis"
            "\n6. Emerging AI development practices"
            "\n7. AI model fine-tuning and deployment tools"
            "\n8. AI safety and responsible development tools"
            "\n\nEnsure to highlight:"
            "\n- Recent developments and emerging trends"
            "\n- Practical applications and use cases"
            "\n- Integration possibilities with existing workflows"
            "\n- Potential impact on development productivity"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate a detailed report on current AI development trends and tools based on the following information:\n\n{content_text}\n\nQuery: {query}")
        ]

        response = self.llm(messages)
        report_text = response.content

        # Store in the database
        Report.objects.update_or_create(
            topic=topic,
            defaults={
                "query": query,
                "generated_report": report_text,
                "updated_at": now()
            }
        )

        return report_text

    def langchain_tool(self):
        """
        Returns the tool object for LangChain with correct function parameters.
        """
        return Tool(
            name="AI Development Trends Report",
            description="Retrieves and analyzes current AI development trends, tools, and technologies. Can focus on specific areas like coding assistants, AI agents, or MLOps tools.",
            func=lambda query, focus_area=None: self.generate_report(query, focus_area)
        )
