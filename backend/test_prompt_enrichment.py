from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator

minimal_prompt = "REF Research impact case study evidence for Professor Andrew Ellis, Aston University."

generator = StructuredReportGenerator(
    report_obj=None,
    user_prompt=minimal_prompt,
    theme_id=None,
    report_id=None,
    report_type="impact_case_study",
)

print("=== BEFORE ===")
print(generator.user_prompt)
print()

generator._maybe_enrich_minimal_prompt()

print("=== AFTER ===")
print(generator.user_prompt)
print()
print("=== search calls used ===", generator._search_calls_total, "failed:", generator._search_calls_failed)
