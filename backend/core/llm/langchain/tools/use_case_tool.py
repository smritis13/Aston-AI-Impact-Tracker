from langchain_core.tools import Tool
from django.db.models import Q
from content.models import UseCase, UseCaseTheme
from typing import List, Dict
import json
from pydantic import BaseModel, Field

class UseCaseSearchInput(BaseModel):
    query: str = Field(..., description="Keywords or theme to search for")
    company: str = Field(None, description="Company name to filter by")

class UseCaseTool:
    def __init__(self, theme_id: int = None, company: str = None):
        self.theme_id = theme_id
        self.company = company
    
    def search_use_cases(self, query: str, limit: int = 30, company: str = None) -> Dict[str, any]:
        """
        Search the use cases database for relevant entries based on the query and optional company.
        The query can be:
        1. A comma-separated list of keywords
        2. A theme name to get all use cases for that theme
        Optionally filter by company name.
        Returns a dictionary with JSON formatted use cases and a list of references.
        """
        company_filter = company or self.company
        print(f"searching use cases for {query} {'in '+company_filter if company_filter else ''}")

        if isinstance(query, dict):
            query = query.get('query', '')

        if query == 'all':
            query = ''

        try:
            if self.theme_id:
                theme_query = UseCaseTheme.objects.filter(id=self.theme_id).first()
            else:
                # Check if query is a theme name
                theme_query = UseCaseTheme.objects.filter(title__icontains=query).first()


            if theme_query:
                # If it's a theme, get all use cases for that theme but limit to 30
                use_cases = UseCase.objects.filter(theme=theme_query)
                if company_filter:
                    use_cases = use_cases.filter(company__icontains=company_filter)
                use_cases = use_cases.select_related('theme', 'report')[:limit]
            else:
                # Split query into keywords and search for each
                keywords = [k.strip() for k in query.split(',')]
                q_objects = Q()
                for keyword in keywords:
                    if keyword == 'all':
                        continue
                    q_objects |= (
                        Q(theme__title__icontains=keyword) |
                        Q(use_case_name__icontains=keyword) |
                        Q(use_case_type__icontains=keyword) |
                        Q(use_case_description__icontains=keyword) |
                        Q(company__icontains=keyword) |
                        Q(industry__icontains=keyword) |
                        Q(tools__icontains=keyword)
                    )
                if self.theme_id:
                    q_objects |= Q(theme__id=self.theme_id)
                    
                if 'all' in query:
                    use_cases = UseCase.objects.all()
                else:
                    use_cases = UseCase.objects.filter(q_objects)

                if company_filter:
                    use_cases = use_cases.filter(company__icontains=company_filter)
                use_cases = use_cases.select_related('theme', 'report')[:limit]
            
            if not use_cases:
                return {
                    "content": "No relevant use cases found in the database.",
                    "references": []
                }
            
            # Create JSON structure for use cases
            use_cases_data = []
            references = []
            
            for use_case in use_cases:
                source_link = f'<a href="{use_case.source}" target="_blank">Source</a>' if use_case.source else ''
                theme_link = f'<a href="/usecases/{use_case.theme.id}">{use_case.theme.title}</a>' if use_case.theme else ''
                
                use_case_dict = {
                    "title_product_name": use_case.use_case_name or "N/A",
                    "organisation_beneficiary": use_case.company or "N/A",
                    "impact_type": use_case.performance_improvement_category or use_case.use_case_type or "N/A",
                    "sector": use_case.industry or "N/A",
                    "quantitative_outcome": use_case.performance_impact or "N/A",
                    "dates_timeframe": use_case.use_case_date or "N/A",
                    "source_url": source_link,
                    "verified": "Yes" if use_case.is_credible else ("No" if use_case.is_credible is False else "Unknown"),
                    "notes_corrections": use_case.credibility_reasoning or use_case.relevance_reasoning or "",
                    "theme": theme_link,
                    "theme_id": use_case.theme.id if use_case.theme else None,
                    "use_case_type": use_case.use_case_type or "N/A",
                    "description": use_case.use_case_description or "N/A",
                    "tools": use_case.tools or "N/A",
                }
                use_cases_data.append(use_case_dict)
                
                if use_case.source:
                    references.append({
                        "title": use_case.use_case_name or "Unnamed Use Case",
                        "url": use_case.source,
                        "type": "use_case"
                    })
            
            # Convert to JSON string without indentation
            result = json.dumps(use_cases_data)
            
            return {
                "content": result,
                "references": references
            }
        
        except Exception as e:
            print(f"Error in UseCaseSearch: {str(e)}")
            return {
                "content": f"Error searching use cases: {str(e)}",
                "references": []
            }

    def get_langchain_tool(self) -> Tool:
        """
        Returns a LangChain Tool instance for the use case search.
        """
        def tool_func(input):
            # If input is a string, treat it as the query (fallback for legacy calls)
            if isinstance(input, str):
                return self.search_use_cases(query=input)
            # If input is a dict (as sometimes happens), unpack it
            if isinstance(input, dict):
                return self.search_use_cases(query=input.get('query', ''), company=input.get('company'))
            # Otherwise, assume it's a UseCaseSearchInput model
            return self.search_use_cases(query=input.query, company=input.company)
        return Tool(
            name="UseCaseSearch",
            func=tool_func,
            description="Search the use cases database for relevant entries. Accepts a 'query' (keywords or theme) and an optional 'company' parameter. If the user asks for use cases for a specific company, always pass the company name as the 'company' parameter. Useful for questions about specific use cases, companies, or industries. Returns a dictionary with content and references.",
            args_schema=UseCaseSearchInput
        )
