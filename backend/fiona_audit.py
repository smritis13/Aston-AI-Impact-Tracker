from content.models import UseCase, UseCaseTheme, Report
from collections import Counter
from urllib.parse import urlparse

print("=== 1. Aston press releases / any aston.ac.uk sources still present? ===")
aston_sources = UseCase.objects.filter(source__icontains="aston.ac.uk")
print("count:", aston_sources.count())
for uc in aston_sources[:10]:
    print(" -", uc.id, uc.theme_id, uc.source)

print()
print("=== 2. Publication dates present + ref_period_status computable ===")
total = UseCase.objects.count()
with_date = UseCase.objects.exclude(use_case_date__isnull=True).exclude(use_case_date="").count()
print(f"with use_case_date: {with_date}/{total}")

print()
print("=== 3. Reference numbering stable in most recent completed reports ===")
recent_reports = Report.objects.exclude(generated_report__isnull=True).exclude(generated_report="").order_by('-created_at')[:5]
for r in recent_reports:
    meta = r.metadata or {}
    print("report", r.id, "theme", r.theme_id, "status", meta.get("status"))

print()
print("=== 4. content_type + researcher_affiliations mechanism usage ===")
ct_counter = Counter(UseCase.objects.values_list('content_type', flat=True))
print("content_type breakdown (all use cases):", ct_counter)
reports_with_affil = Report.objects.exclude(metadata__researcher_affiliations=[]).exclude(metadata__researcher_affiliations__isnull=True)
print("reports with non-empty researcher_affiliations:", reports_with_affil.count(), "/", Report.objects.count())

print()
print("=== 4e. direct_quote / source_reference coverage ===")
with_quote = UseCase.objects.exclude(direct_quote__isnull=True).exclude(direct_quote="").count()
with_source_ref = UseCase.objects.exclude(source_reference__isnull=True).exclude(source_reference="").count()
print(f"with direct_quote: {with_quote}/{total}")
print(f"with source_reference: {with_source_ref}/{total}")

print()
print("=== 5. draft/commentary split present in recent reports ===")
for r in recent_reports:
    meta = r.metadata or {}
    print("report", r.id, "has draft_section:", bool(meta.get("draft_section")), "has commentary_section:", bool(meta.get("commentary_section")))

print()
print("=== 6. quantitative data + direct quotes in performance_impact ===")
with_impact = UseCase.objects.exclude(performance_impact__isnull=True).exclude(performance_impact="").count()
print(f"with performance_impact: {with_impact}/{total}")

print()
print("=== theme list (most recent 10) ===")
for t in UseCaseTheme.objects.order_by('-id')[:10]:
    print(t.id, t.title, "- use cases:", UseCase.objects.filter(theme_id=t.id).count())
