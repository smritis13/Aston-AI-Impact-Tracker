from content.models import Report

for rid in [50, 49, 48]:
    r = Report.objects.get(id=rid)
    text = r.generated_report or ""
    print(f"=== report {rid} ===")
    print("length:", len(text))
    print("is template fallback (contains 'This draft REF impact case study draws on'):",
          "This draft REF impact case study draws on" in text)
    print("has '## 1. Summary of the Impact' (real LLM synthesis heading):",
          "## 1. Summary of the Impact" in text)
    print("has '## 6. REF Readiness Assessment':", "## 6. REF Readiness Assessment" in text)
    print("first 300 chars:")
    print(text[:300])
    print()
