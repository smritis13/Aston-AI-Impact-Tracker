from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator

generator = StructuredReportGenerator(
    report_obj=None,
    user_prompt="Maria Chli Aston University traffic AI deployment adopted patients users national policy",
    theme_id=None,
    report_id=None,
    report_type="impact_case_study",
)

results = [
    {"title": "2018 Maria Chli Aston traffic AI deployment adopted national policy evidence trial", "snippet": "deployed adopted implemented improved reduction 2018 million patients users national policy report evidence trial", "link": "https://example.com/old", "source": "example.com"},
    {"title": "2026 Maria Chli Aston traffic AI deployment adopted national policy evidence trial", "snippet": "deployed adopted implemented improved reduction 2026 million patients users national policy report evidence trial", "link": "https://example.com/new", "source": "example.com"},
    {"title": "2022 Maria Chli Aston traffic AI deployment adopted national policy evidence trial", "snippet": "deployed adopted implemented improved reduction 2022 million patients users national policy report evidence trial", "link": "https://example.com/mid", "source": "example.com"},
]

ranked = generator._rank_search_results("Maria Chli Aston traffic AI deployment", results)
for r in ranked:
    print(r["title"])
