from content.models import UseCase
from collections import Counter

aston_sources = UseCase.objects.filter(source__icontains="aston.ac.uk")
by_theme = Counter(uc.theme_id for uc in aston_sources)
print("aston.ac.uk source count by theme_id:", dict(sorted(by_theme.items(), key=lambda kv: (kv[0] is None, kv[0]))))

# created_at range for these records
dates = sorted([uc.created_at for uc in aston_sources if uc.created_at])
if dates:
    print("earliest:", dates[0], "latest:", dates[-1])

# theme 39 and 40 specifically (most recent, generated under current code)
for tid in [39, 40]:
    qs = UseCase.objects.filter(theme_id=tid, source__icontains="aston.ac.uk")
    print(f"theme {tid} aston.ac.uk sources:", qs.count())

print()
print("=== direct_quote vs source_reference breakdown by theme (last 6 themes) ===")
for tid in [35, 36, 37, 38, 39, 40]:
    qs = UseCase.objects.filter(theme_id=tid)
    total = qs.count()
    wq = qs.exclude(direct_quote__isnull=True).exclude(direct_quote="").count()
    wsr = qs.exclude(source_reference__isnull=True).exclude(source_reference="").count()
    print(f"theme {tid}: total={total} with_quote={wq} with_source_ref={wsr}")
