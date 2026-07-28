from content.models import UseCase, UseCaseTheme, Report
from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator

theme = UseCaseTheme.objects.get(id=40)
use_cases = list(UseCase.objects.filter(theme_id=theme.id))

# Simulate an auto-discovered affiliation record, as if the planning/extraction
# pipeline had found one during a fresh search (LinkedIn-style bio note).
fake_affiliation_record = UseCase.objects.create(
    theme=theme,
    use_case_name="Institutional affiliation record: Patricia Thornley",
    use_case_type="Researcher Affiliation Record",
    use_case_description="Auto-discovered affiliation note (test)",
    source="https://www.linkedin.com/in/patricia-thornley-test",
    source_type="Web",
    affiliation_note="Patricia Thornley joined Aston University in 2015 as Professor of Bioenergy, having previously been at the University of Manchester.",
)
print("created fake affiliation record id:", fake_affiliation_record.id)

use_cases_with_affiliation = use_cases + [fake_affiliation_record]
print(f"Compiling report from {len(use_cases_with_affiliation)} use cases (including 1 affiliation record)")

report_obj = Report.objects.create(
    theme=theme,
    query=theme.description or "Compile REF impact case study",
    generated_report="",
    thoughts=[],
    metadata={
        "status": "processing",
        "report_type": "impact_case_study",
        "theme_id": theme.id,
        "researcher_affiliations": [],
    },
)

generator = StructuredReportGenerator(
    report_obj=report_obj,
    user_prompt=theme.description or "Compile REF impact case study",
    theme_id=theme.id,
    report_id=report_obj.id,
    report_type="impact_case_study",
    researcher_affiliations=[],
)
generator.compile_from_existing_use_cases(use_cases_with_affiliation)

report_obj.refresh_from_db()
text = report_obj.generated_report or ""
print("=== STATUS ===", report_obj.metadata.get("status"))
print("=== LENGTH ===", len(text))
print("=== affiliation_note text appears in report ===", "joined Aston University in 2015" in text or "2015" in text)
print("=== fake record's OWN use_case_name leaked into report as if it were evidence ===",
      "Institutional affiliation record" in text)
print("=== fake record's source URL appears as a numbered reference (bad if true) ===",
      "linkedin.com/in/patricia-thornley-test" in text)

with open("/app/test_affiliation_report.md", "w") as f:
    f.write(text)

# cleanup
fake_affiliation_record.delete()
report_obj.delete()
print("cleaned up test records")
