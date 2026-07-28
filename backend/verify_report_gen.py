from content.models import UseCase, UseCaseTheme, Report
from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator

theme = UseCaseTheme.objects.get(id=40)
use_cases = list(UseCase.objects.filter(theme_id=theme.id))
print(f"Compiling report from {len(use_cases)} use cases in theme {theme.id} ({theme.title})")

report_obj = Report.objects.create(
    theme=theme,
    query=theme.description or "Compile REF impact case study",
    generated_report="",
    thoughts=[],
    metadata={
        "status": "processing",
        "report_type": "impact_case_study",
        "theme_id": theme.id,
        "researcher_affiliations": [{"name": "Patricia Thornley", "aston_start": "2015", "aston_end": ""}],
    },
)

generator = StructuredReportGenerator(
    report_obj=report_obj,
    user_prompt=theme.description or "Compile REF impact case study",
    theme_id=theme.id,
    report_id=report_obj.id,
    report_type="impact_case_study",
    researcher_affiliations=[{"name": "Patricia Thornley", "aston_start": "2015", "aston_end": ""}],
)
generator.compile_from_existing_use_cases(use_cases)

report_obj.refresh_from_db()
print("=== STATUS ===")
print(report_obj.metadata.get("status"))
print("=== REPORT ID ===")
print(report_obj.id)
print("=== LENGTH ===")
print(len(report_obj.generated_report or ""))

with open("/app/test_report_output.md", "w") as f:
    f.write(report_obj.generated_report or "")
print("Saved to /app/test_report_output.md")
