"""
One-off cleanup for UseCase rows created before the dedup/re-scoring bugs were
fixed in structured_report_generator.py (_get_or_create_use_case /
_extract_node's Quality gate 2). Those bugs let the same source URL produce
several separate rows instead of merging, and let a duplicate's re-check
silently drag an existing row's score below the documented 6-point relevance
gate without deleting it. This command cleans up both symptoms in
already-saved data; it does not change how new runs behave (see the code fix
for that).

Same-source matches are now treated as an unconditional duplicate (mirroring
the live-extraction fix), not gated behind a similarity threshold - real data
showed several differently-worded restatements of the same source landing
under the old threshold and surviving as separate rows. Cross-source fuzzy
matching (different URL, same underlying claim) still uses
StructuredReportGenerator._CROSS_SOURCE_DEDUP_THRESHOLD, the same bar live
extraction uses.

Dry-run by default - pass --apply to actually merge/delete.
"""
import json

from django.core.management.base import BaseCommand

from content.models import UseCase, UseCaseTheme
from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator

CROSS_SOURCE_THRESHOLD = StructuredReportGenerator._CROSS_SOURCE_DEDUP_THRESHOLD


def claim_similarity(a, b):
    return StructuredReportGenerator._claim_similarity(a, b)


class Command(BaseCommand):
    help = (
        "Finds (and optionally merges) already-persisted duplicate use cases - "
        "same-source rows unconditionally, cross-source rows by claim similarity - "
        "and rows below the 6-point relevance gate. Dry-run by default; pass --apply to write."
    )

    def add_arguments(self, parser):
        parser.add_argument("--theme", help="Restrict to one theme title (default: all themes)")
        parser.add_argument("--apply", action="store_true", help="Actually merge/delete. Without this flag, only reports what would happen.")

    def handle(self, *args, **options):
        themes = UseCaseTheme.objects.filter(is_deleted=False)
        if options.get("theme"):
            themes = themes.filter(title=options["theme"])

        merge_report = []
        sub_gate_report = []
        for theme in themes:
            use_cases = list(UseCase.objects.filter(theme=theme).order_by("created_at", "id"))
            merged_ids = set()

            for i, a in enumerate(use_cases):
                if a.id in merged_ids:
                    continue
                for b in use_cases[i + 1:]:
                    if b.id in merged_ids:
                        continue
                    same_source = bool(a.source) and a.source == b.source
                    if same_source:
                        is_dup = True
                        sim = None
                    elif a.use_case_name and b.use_case_name:
                        sim = claim_similarity(a.use_case_name, b.use_case_name)
                        is_dup = sim > CROSS_SOURCE_THRESHOLD
                    else:
                        continue
                    if not is_dup:
                        continue

                    merge_report.append({
                        "theme": theme.title,
                        "keep_id": a.id,
                        "merge_id": b.id,
                        "same_source": same_source,
                        "similarity": round(sim, 3) if sim is not None else None,
                        "keep_name": (a.use_case_name or "")[:80],
                        "merge_name": (b.use_case_name or "")[:80],
                    })
                    if options["apply"]:
                        update_fields = {}
                        for field in (
                            "use_case_name", "company", "industry", "tools",
                            "use_case_description", "performance_impact", "use_case_date",
                            "published_date", "source_reference", "source_type", "domain",
                            "publisher", "content_type", "direct_quote", "affiliation_note",
                            "country", "geography", "performance_improvement_category",
                            "credibility_score", "is_credible", "credibility_reasoning",
                            "relevance_score", "is_relevant", "relevance_reasoning",
                        ):
                            a_val = getattr(a, field, None)
                            b_val = getattr(b, field, None)
                            if (a_val in (None, "", [])) and b_val not in (None, "", []):
                                update_fields[field] = b_val
                        if update_fields:
                            UseCase.objects.filter(id=a.id).update(**update_fields)
                        UseCase.objects.filter(id=b.id).delete()
                    merged_ids.add(b.id)

        # The is_underpinning_research exception in _passes_relevance_gate still
        # requires a minimum of 6, same as every other content_type - so any row
        # scored below 6 is a genuine gate violation regardless of use_case_type,
        # with no legitimate exemption to account for here.
        sub_gate_qs = UseCase.objects.filter(relevance_score__lt=6, relevance_score__isnull=False)
        if options.get("theme"):
            sub_gate_qs = sub_gate_qs.filter(theme__title=options["theme"])
        for row in sub_gate_qs.select_related("theme"):
            sub_gate_report.append({
                "theme": row.theme.title if row.theme_id else None,
                "id": row.id,
                "relevance_score": row.relevance_score,
                "use_case_name": (row.use_case_name or "")[:80],
            })
        if options["apply"] and sub_gate_report:
            sub_gate_qs.delete()

        print("===DEDUPE_JSON_START===")
        print(json.dumps({
            "applied": options["apply"],
            "merges": merge_report,
            "sub_gate_deletions": sub_gate_report,
        }, indent=2))
        print("===DEDUPE_JSON_END===")
