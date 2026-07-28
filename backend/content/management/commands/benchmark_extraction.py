import json
import time

from django.core.management.base import BaseCommand

from content.models import Report, ScrapedURL, UseCase, UseCaseTheme
from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator

BENCHMARK_PROMPT = (
    "Impact case studies of UK university research on renewable energy adoption "
    "by industry, including named industry partners and quantified outcomes."
)


class Command(BaseCommand):
    help = "Runs a small, isolated, real search->scrape->extract pass to measure end-to-end latency. Uses a throwaway theme so it never touches production data."

    def add_arguments(self, parser):
        parser.add_argument("--label", required=True, help="baseline or fixed")

    def handle(self, *args, **options):
        label = options["label"]
        theme_title = f"ZBENCHMARK-{label.upper()}-DELETE-ME"

        theme, _ = UseCaseTheme.objects.get_or_create(title=theme_title, defaults={"description": "Throwaway benchmark theme, safe to delete."})
        report = Report.objects.create(topic=theme_title, query=BENCHMARK_PROMPT, generated_report="", theme=theme)

        generator = StructuredReportGenerator(
            user_prompt=BENCHMARK_PROMPT,
            report_obj=report,
            theme_id=theme.id,
            max_links_to_scrape=40,
            number_of_outcomes=20,
            search_complexity="simple",
            enable_credibility_check=True,
            enable_relevance_check=True,
        )

        start = time.perf_counter()
        generator.run()
        elapsed = time.perf_counter() - start

        scraped_count = ScrapedURL.objects.filter(report=report).count()
        use_cases = UseCase.objects.filter(report=report)
        use_case_count = use_cases.count()
        credible_count = use_cases.filter(is_credible=True).count()

        result = {
            "label": label,
            "elapsed_seconds": round(elapsed, 1),
            "scraped_urls": scraped_count,
            "use_cases_extracted": use_case_count,
            "credible_count": credible_count,
            "seconds_per_scraped_page": round(elapsed / scraped_count, 2) if scraped_count else None,
            "theme_id": theme.id,
            "report_id": report.id,
        }
        print("===BENCHMARK_JSON_START===")
        print(json.dumps(result, indent=2))
        print("===BENCHMARK_JSON_END===")
