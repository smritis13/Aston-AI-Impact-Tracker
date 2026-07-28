from content.models import Report
for rid in [37, 38]:
    r = Report.objects.get(id=rid)
    meta = r.metadata or {}
    print(f"Report {rid}: theme_id={meta.get('theme_id')} report_type={meta.get('report_type')} theme_FK={r.theme_id}")
