from content.models import Report
import json

for rid in [50, 49, 48]:
    r = Report.objects.get(id=rid)
    print(f"=== report {rid} metadata ===")
    print(json.dumps(r.metadata, indent=2, default=str)[:2000])
    print()
