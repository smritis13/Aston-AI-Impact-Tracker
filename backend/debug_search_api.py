from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator

generator = StructuredReportGenerator(
    report_obj=None,
    user_prompt="test",
    theme_id=None,
    report_id=None,
    report_type="impact_case_study",
)

try:
    results = generator.search_api.run('"Andrew Ellis" Aston University research profile expertise')
    print("TYPE:", type(results))
    print("RESULT:", results)
except Exception as e:
    import traceback
    traceback.print_exc()
