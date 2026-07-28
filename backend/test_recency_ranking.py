from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator

generator = StructuredReportGenerator(
    report_obj=None,
    user_prompt="test prompt for Maria Chli",
    theme_id=None,
    report_id=None,
    report_type="impact_case_study",
)

results = [
    {"title": "Old 2018 case study on traffic AI", "snippet": "deployed in 2018 across cities", "link": "https://example.com/old", "source": "example.com"},
    {"title": "Brand new 2026 traffic AI deployment", "snippet": "deployed in 2026, huge success", "link": "https://example.com/new", "source": "example.com"},
    {"title": "Mid-range 2022 traffic AI pilot", "snippet": "piloted in 2022", "link": "https://example.com/mid", "source": "example.com"},
]

ranked = generator._rank_search_results("traffic AI deployment", results)
for r in ranked:
    print(r["title"])
