import json
import re
import statistics

from django.core.management.base import BaseCommand

from content.models import Report, ScrapedURL, UseCase, UseCaseTheme

FEATURED_THEMES = ["CIRCARB-IMPACTS", "BIOENERGY-IMPACTS", "FIBRE-IMPACTS", "KHAMSIN-IMPACTS"]

REQUIRED_SECTIONS = [
    r"^#\s+.+",
    r"^##\s*1\.\s*Summary of the Impact",
    r"^##\s*2\.\s*Underpinning Research",
    r"^##\s*3\.\s*References to the Research",
    r"^##\s*4\.\s*Details of the Impact",
    r"^###\s*Pathway from Research to Impact",
    r"^###\s*Reach",
    r"^###\s*Significance",
    r"^###\s*Attribution to the Research",
    r"^##\s*5\.\s*Sources to Corroborate the Impact",
    r"^##\s*6\.\s*REF Readiness Assessment",
]

READINESS_ROWS = [
    "Reach",
    "Significance",
    "Research attribution",
    "Independent corroboration",
    "Timeframe and eligibility",
    "Overall REF readiness",
]

HEDGING_PHRASES = [
    "it is suggested",
    "may have contributed",
    "it is believed",
    "could potentially",
    "appears to",
    "it is thought",
    "may have played a role",
    "it is likely that",
]


def word_target(n_use_cases):
    return (1800, 2200) if n_use_cases < 12 else (2500, 3500)


def get_section(text, start_pat, end_pats):
    start = re.search(start_pat, text, re.MULTILINE)
    if not start:
        return ""
    tail = text[start.end():]
    end_pos = len(tail)
    for ep in end_pats:
        m = re.search(ep, tail, re.MULTILINE)
        if m and m.start() < end_pos:
            end_pos = m.start()
    return tail[:end_pos]


def section_slice(text, pattern):
    """Slice out the body of a header until the next header of the SAME OR
    SHALLOWER level (so a ## section's H3 subsections stay inside its slice)."""
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        return ""
    start_level = len(re.match(r"^(#+)", m.group(0)).group(1))
    start = m.end()
    end = len(text)
    for hm in re.finditer(r"^(#{1,6})\s", text, re.MULTILINE):
        if hm.start() <= m.start():
            continue
        level = len(hm.group(1))
        if level <= start_level:
            end = hm.start()
            break
    return text[start:end]


def analyze_report_structure(theme_title, report):
    text = report.generated_report or ""
    words = len(text.split())
    n_use_cases = UseCase.objects.filter(theme__title=theme_title).count()
    lo, hi = word_target(n_use_cases)

    section_hits = {pat: bool(re.search(pat, text, re.MULTILINE)) for pat in REQUIRED_SECTIONS}
    sections_present = sum(section_hits.values())

    references_section = section_slice(text, r"^##\s*3\.\s*References to the Research")
    sources_section = section_slice(text, r"^##\s*5\.\s*Sources to Corroborate the Impact")
    details_section = section_slice(text, r"^##\s*4\.\s*Details of the Impact")
    readiness_section = section_slice(text, r"^##\s*6\.\s*REF Readiness Assessment")

    references_numbered = len(re.findall(r"^\s*\d+\.\s", references_section, re.MULTILINE))
    sources_numbered = len(re.findall(r"^\s*\d+\.\s", sources_section, re.MULTILINE))
    citation_markers = len(re.findall(r"\[\d+\]", details_section))

    readiness_rows_found = sum(1 for row in READINESS_ROWS if row.lower() in readiness_section.lower())
    readiness_is_table = "|" in readiness_section

    hedging_count = sum(len(re.findall(re.escape(p), text, re.IGNORECASE)) for p in HEDGING_PHRASES)

    return {
        "report_id": report.id,
        "theme": theme_title,
        "word_count": words,
        "target_range": [lo, hi],
        "within_target": lo <= words <= hi,
        "sections_present": sections_present,
        "sections_required": len(REQUIRED_SECTIONS),
        "missing_sections": [pat for pat, hit in section_hits.items() if not hit],
        "references_numbered_items": references_numbered,
        "sources_numbered_items": sources_numbered,
        "citation_markers_in_details": citation_markers,
        "readiness_table_present": readiness_is_table,
        "readiness_rows_found": readiness_rows_found,
        "readiness_rows_required": len(READINESS_ROWS),
        "hedging_phrase_count": hedging_count,
        "structural_compliance_pct": round(
            100 * (sections_present / len(REQUIRED_SECTIONS)) * (0.7)
            + 100 * (readiness_rows_found / len(READINESS_ROWS)) * 0.15
            + (100 if readiness_is_table else 0) * 0.15,
            1,
        ),
    }


def pearson(xs, ys):
    if len(xs) < 2:
        return None
    mean_x, mean_y = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return None
    return round(num / (den_x * den_y), 3)


def bucket_scores(scores):
    buckets = {"0-2": 0, "3-4": 0, "5-6": 0, "7-8": 0, "9-10": 0}
    for s in scores:
        if s <= 2:
            buckets["0-2"] += 1
        elif s <= 4:
            buckets["3-4"] += 1
        elif s <= 6:
            buckets["5-6"] += 1
        elif s <= 8:
            buckets["7-8"] += 1
        else:
            buckets["9-10"] += 1
    return buckets


def analyze_scoring(theme_title):
    qs = UseCase.objects.filter(theme__title=theme_title)
    total = qs.count()
    cred_scores = [uc.credibility_score for uc in qs if uc.credibility_score is not None]
    rel_scores = [uc.relevance_score for uc in qs if uc.relevance_score is not None]

    cred_violations = qs.filter(is_credible=True, credibility_score__lt=6).count() + qs.filter(
        is_credible=False, credibility_score__gte=6
    ).count()
    rel_violations = qs.filter(is_relevant=True, relevance_score__lt=6).count() + qs.filter(
        is_relevant=False, relevance_score__gte=6
    ).count()

    paired = [
        (uc.credibility_score, uc.relevance_score)
        for uc in qs
        if uc.credibility_score is not None and uc.relevance_score is not None
    ]
    corr = pearson([p[0] for p in paired], [p[1] for p in paired]) if paired else None

    return {
        "theme": theme_title,
        "total_use_cases": total,
        "credibility_scored": len(cred_scores),
        "relevance_scored": len(rel_scores),
        "credibility_mean": round(statistics.mean(cred_scores), 2) if cred_scores else None,
        "credibility_stdev": round(statistics.pstdev(cred_scores), 2) if len(cred_scores) > 1 else None,
        "credibility_buckets": bucket_scores(cred_scores),
        "relevance_mean": round(statistics.mean(rel_scores), 2) if rel_scores else None,
        "relevance_stdev": round(statistics.pstdev(rel_scores), 2) if len(rel_scores) > 1 else None,
        "relevance_buckets": bucket_scores(rel_scores),
        "credibility_self_consistency_violations": cred_violations,
        "relevance_self_consistency_violations": rel_violations,
        "credibility_relevance_correlation": corr,
        "high_score_leniency_pct": round(
            100 * sum(1 for s in cred_scores if s >= 7) / len(cred_scores), 1
        )
        if cred_scores
        else None,
    }


def analyze_system(theme_title):
    theme_reports = Report.objects.filter(theme__title=theme_title)
    report_ids = list(theme_reports.values_list("id", flat=True))
    scraped_count = ScrapedURL.objects.filter(report_id__in=report_ids).count()

    use_cases = UseCase.objects.filter(theme__title=theme_title)
    extracted = use_cases.count()
    credible = use_cases.filter(is_credible=True).count()
    relevant = use_cases.filter(is_relevant=True).count()
    both = use_cases.filter(is_credible=True, is_relevant=True).count()

    missing_source = use_cases.filter(source__isnull=True).count() + use_cases.filter(source="").count()
    missing_source_ref = (
        use_cases.filter(source_reference__isnull=True).count()
        + use_cases.filter(source_reference="").count()
    )

    source_type_counts = {}
    for st in use_cases.values_list("source_type", flat=True):
        key = st or "(unset)"
        source_type_counts[key] = source_type_counts.get(key, 0) + 1

    return {
        "theme": theme_title,
        "scraped_urls": scraped_count,
        "extracted_use_cases": extracted,
        "extraction_yield_pct": round(100 * extracted / scraped_count, 1) if scraped_count else None,
        "credible_count": credible,
        "credible_pct": round(100 * credible / extracted, 1) if extracted else None,
        "relevant_count": relevant,
        "relevant_pct": round(100 * relevant / extracted, 1) if extracted else None,
        "both_credible_and_relevant": both,
        "final_yield_pct": round(100 * both / extracted, 1) if extracted else None,
        "missing_source_count": missing_source,
        "missing_source_reference_count": missing_source_ref,
        "unverifiable_pct": round(100 * missing_source / extracted, 1) if extracted else None,
        "source_type_breakdown": source_type_counts,
    }


class Command(BaseCommand):
    help = "Computes scoring-validity, synthesis-quality, and system-reliability metrics from already-generated reports/use cases."

    def handle(self, *args, **options):
        results = {"scoring_validity": [], "synthesis_quality": [], "system_reliability": []}

        for theme_title in FEATURED_THEMES:
            if not UseCaseTheme.objects.filter(title=theme_title, is_deleted=False).exists():
                continue
            results["scoring_validity"].append(analyze_scoring(theme_title))
            results["system_reliability"].append(analyze_system(theme_title))

            markdown_reports = [
                r
                for r in Report.objects.filter(theme__title=theme_title)
                if (r.generated_report or "").lstrip().startswith("#")
            ]
            for r in markdown_reports:
                results["synthesis_quality"].append(analyze_report_structure(theme_title, r))

        print("===JSON_START===")
        print(json.dumps(results, indent=2))
        print("===JSON_END===")
