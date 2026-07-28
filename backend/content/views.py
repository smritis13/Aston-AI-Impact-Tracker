import io
import json
import os
import re
import tempfile
import textwrap
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import now

from core.llm.utils.web.WebSearchResult import UnifiedWebSearch
from core.llm.utils.WebSearcher import WebSearcher

from .models import *
from rest_framework import generics
from rest_framework.views import APIView

from .serializers import *
from core.llm.utils.ContentScraper import ContentScraper
from core.llm.utils.ContentIndexer import ContentIndexer
from core.llm.utils.SimpleHtmlScraper import SimpleHtmlScraper

from rest_framework import generics, status
from rest_framework.response import Response
from base.pagination import CustomPagination
from asgiref.sync import async_to_sync, sync_to_async


from core.llm.utils.web.URLValidator import URLValidator

from urllib.parse import urlparse
from core.llm.langchain.langgraph.base_report_generator import BaseGraphReportGenerator
from core.llm.langchain.langgraph.structured_report_generator import StructuredReportGenerator
from core.llm.utils.web.serper_api import SerperAPI
# removed medical-specific generators to focus on research impact
from core.llm.utils.Streamer import Streamer

from django.db.models import Max, Q, Subquery

from core.utils.ExportUtils import ExportUtils
from langchain_community.chat_models import ChatOpenAI
from core.llm.langchain.langgraph.prompts import THEME_NAME_GENERATION_PROMPT

from rest_framework.decorators import api_view
from django.db.models import Count
from core.llm.langchain.langgraph.single_url_extractor import SingleUrlExtractor
from base.throttling import ReportGenerationRateThrottle
from .entity_extractor import EntityExtractor

# ContentSource Views
class ContentSourceListCreateView(generics.ListCreateAPIView):
    queryset = ContentSource.objects.all()
    serializer_class = ContentSourceSerializer

class ContentSourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ContentSource.objects.all()
    serializer_class = ContentSourceSerializer

# ContentSourceURL Views
class ContentSourceURLListCreateView(generics.ListCreateAPIView):
    serializer_class = ContentSourceURLSerializer

    def get_queryset(self):
        return ContentSourceURL.objects.filter(content_source_id=self.kwargs['content_source_id'])

    def perform_create(self, serializer):
        content_source = ContentSource.objects.get(id=self.kwargs['content_source_id'])
        serializer.save(content_source=content_source)

class ContentSourceURLDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ContentSourceURL.objects.all()
    serializer_class = ContentSourceURLSerializer

# ContentSourceScrapeLog Views
class ContentSourceScrapeLogListView(generics.ListAPIView):
    serializer_class = ContentSourceScrapeLogSerializer

    def get_queryset(self):
        return ContentSourceScrapeLog.objects.filter(content_source_id=self.kwargs['content_source_id'])



# Import or define your ContentScraper and ContentIndexer classes
# from your_app.scraping import ContentScraper, ContentIndexer

class ScrapeAndIndexContentAPIView(generics.GenericAPIView):
    """
    Generic API view to scrape content from a given URL and index it,
    without using a dedicated serializer.
    """


    def post(self, request, *args, **kwargs):
        url = request.data.get("url")
        # category_id = request.data.get("category_id")
        
        # # Basic input validation
        # if not url or not category_id:
        #     return Response(
        #         {"error": "Both 'url' and 'category_id' are required."},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        
        try:
            # Scrape and save the content
            # scraper = ContentScraper()
            # content = scraper.scrape_and_save(url) 

            
            scraper = SimpleHtmlScraper()
            content = async_to_sync(scraper.scrape_only)(url)
            
            # Index the content
            indexer = ContentIndexer()
            # indexer.delete_all_indexes()
            indexer.index_content(content)
            
            return Response(
                {"message": "Content scraped and indexed successfully."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # Optionally log the exception details here
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class IndexContentAPIView(generics.GenericAPIView):

    def post(self, request, *args, **kwargs):
        category_name = request.data.get("category_name")
        indexer = ContentIndexer()
        # indexer.delete_all_indexes()
        # indexer.index_content(content)

        contents = Content.objects.all()
        for content in contents:
            try:
                indexer.index_content(content)
            except Exception as e:
                print(f"Failed to index content {content.id}: {str(e)}")
                continue
        message = f"Successfully reindexed {contents.count()} content items."
        
        return Response(
            {"message": message},
            status=status.HTTP_200_OK
        )

class ContentListCreateView(generics.ListCreateAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ContentListSerializer  # Serializer for GET requests
        return ContentSerializer  # Serializer for POST/PUT, etc.


class ContentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer





class SearchContentAPIView(generics.GenericAPIView):
    """
    API view to search for content using semantic search.
    
    Expects a POST request with a JSON body like:
    {
        "query": "your search query here",
        "category_name": "optional category name",
        "n_results": 5  # optional, defaults to 5
    }
    """
    
    def post(self, request, *args, **kwargs):
        query = request.data.get("query")
        category_name = request.data.get("category_name")
        n_results = request.data.get("n_results", 5)
        
        if not query:
            return Response(
                {"error": "query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            indexer = ContentIndexer()
            search_results = indexer.search(
                category_name=category_name,
                query_text=query,
                n_results=n_results
            )
            
            # Process the results to include more details
            processed_results = []
            if search_results.get('ids'):
                for i, doc_id in enumerate(search_results['ids'][0]):
                    result = {
                        'id': doc_id,
                        'distance': search_results['distances'][0][i] if search_results.get('distances') else None,
                        'metadata': search_results['metadatas'][0][i] if search_results.get('metadatas') else None,
                    }
                    processed_results.append(result)
            
            return Response({
                "results": processed_results,
                "total_results": len(processed_results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebSearchView(APIView):
    """
    API view to perform web search and store URLs for later scraping.
    """

    def post(self, request, *args, **kwargs):
        query = request.data.get("query")
        num_results = request.data.get("num_results", 10)
        engine = request.data.get("engine", "duckduckgo")

        try:
            # searcher = WebSearcher()
            # results = searcher.search(query, num_results, engine)
            searcher = UnifiedWebSearch("tavily")
            results = searcher.search(query, num_results)

            stored_urls = []
            for result in results:
                # url = result["link"]
                url = result["url"]
                url_obj, created = UrlToScrape.objects.get_or_create(
                    url=url,
                    defaults={
                        "title": result.get("title"),
                        "status": "pending"
                    }
                )
                stored_urls.append({
                    "id": url_obj.id,
                    "url": url_obj.url,
                    "title": url_obj.title,
                    "status": url_obj.status
                })

            return Response({
                "message": f"Stored {len(stored_urls)} URLs for scraping",
                "stored_urls": stored_urls
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ContentScraperView(APIView):
    """
    API view to scrape stored URLs using SimpleHtmlScraper.
    Can scrape all pending URLs or specific URLs by ID.
    """

    def post(self, request, *args, **kwargs):
        
        try:
            # Get URLs to scrape
            urls_to_scrape = UrlToScrape.objects.filter(
                    status__in=['pending', 'failed']
                )
                

            scraper = SimpleHtmlScraper()
            indexer = ContentIndexer()
            
            results = []
            for url_obj in urls_to_scrape:
                try:
                    # Update status to processing
                    url_obj.status = 'processing'
                    url_obj.save()

                    # Scrape content
                    scraped_content = async_to_sync(scraper.scrape_only)(url_obj.url)

                    if scraped_content:
                        # Create or update Content object
                        # content_obj = Content.objects.create(
                        #     title=url_obj.title,
                        #     original_content=scraped_content,
                        #     url=url_obj.url
                        # )

                        # Index the content
                        indexer.index_content(scraped_content)

                        # Update URL status to completed and link to content
                        url_obj.status = 'completed'
                        url_obj.error_message = None
                        url_obj.content = scraped_content
                        url_obj.save()

                        results.append({
                            "url_id": url_obj.id,
                            "status": "success",
                            "content_id": scraped_content.id
                        })
                    else:
                        raise Exception("No content scraped")

                except Exception as e:
                    url_obj.status = 'failed'
                    url_obj.error_message = str(e)
                    url_obj.save()
                    results.append({
                        "url_id": url_obj.id,
                        "status": "failed",
                        "error": str(e)
                    })

            return Response({
                "message": f"Processed {len(results)} URLs",
                "results": results
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportListView(generics.ListAPIView):
    serializer_class = ReportSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = Report.objects.all()
        report_type = self.request.query_params.get('report_type')
        if report_type:
            qs = qs.filter(metadata__report_type=report_type)
        return qs

class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

class ReportPdfExportView(APIView):
    _PDF_CSS = """
        @page {
            size: A4;
            margin: 2.5cm 2cm 2.5cm 2cm;
        }
        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 11pt;
            line-height: 1.55;
            color: #111827;
        }
        .pdf-title {
            font-size: 17pt;
            font-weight: bold;
            color: #1e3a5f;
            margin: 0 0 4pt 0;
            border-bottom: 2pt solid #1e3a5f;
            padding-bottom: 6pt;
        }
        .pdf-meta {
            font-size: 9pt;
            color: #6b7280;
            margin: 0 0 20pt 0;
        }
        h1 {
            font-size: 14.5pt;
            color: #1e3a5f;
            margin: 20pt 0 8pt 0;
            border-bottom: 1.5pt solid #1e3a5f;
            padding-bottom: 4pt;
        }
        h2 {
            font-size: 12pt;
            color: #1e3a5f;
            margin: 16pt 0 6pt 0;
            border-bottom: 0.5pt solid #9ca3af;
            padding-bottom: 3pt;
        }
        h3 {
            font-size: 10.5pt;
            color: #374151;
            margin: 12pt 0 5pt 0;
        }
        h4 {
            font-size: 10pt;
            color: #374151;
            font-style: italic;
            margin: 10pt 0 4pt 0;
        }
        p { margin: 0 0 7pt 0; }
        a {
            color: #1d4ed8;
            text-decoration: underline;
        }
        ul, ol {
            margin: 4pt 0 8pt 0;
            padding-left: 18pt;
        }
        li { margin-bottom: 3pt; }
        table {
            table-layout: fixed;
            width: 100%;
            border-collapse: collapse;
            margin: 10pt 0 12pt 0;
            font-size: 9.5pt;
        }
        th {
            background-color: #1e3a5f;
            color: #ffffff;
            padding: 5pt 7pt;
            text-align: left;
            font-weight: bold;
            border: 0.5pt solid #1e3a5f;
            word-wrap: break-word;
        }
        td {
            padding: 5pt 7pt;
            border: 0.5pt solid #d1d5db;
            vertical-align: top;
            word-wrap: break-word;
        }
        td a {
            word-wrap: break-word;
            -pdf-word-wrap: CJK;
        }
        tr.even td { background-color: #f8f9fa; }
        strong, b { font-weight: bold; }
        em, i { font-style: italic; }
        blockquote {
            margin: 6pt 0 6pt 14pt;
            padding: 4pt 10pt;
            border-left: 2.5pt solid #9ca3af;
            color: #4b5563;
            font-style: italic;
        }
        hr {
            border: none;
            border-top: 0.5pt solid #d1d5db;
            margin: 14pt 0;
        }
        code {
            font-family: Courier, monospace;
            font-size: 9.5pt;
            background-color: #f3f4f6;
            padding: 1pt 3pt;
        }
        .page-break { page-break-before: always; }
    """

    def _strip_columns_by_header(self, html, header_names):
        """Remove any table column whose header cell text matches one of
        header_names (case-insensitive), across the header row and every
        data row. Column position/count is detected per-table, not assumed."""
        header_names_lower = {h.lower() for h in header_names}
        cell_re = re.compile(r'<(th|td)\b[^>]*>(.*?)</\1>', re.DOTALL)
        row_re = re.compile(r'<tr\b[^>]*>.*?</tr>', re.DOTALL)

        def _process_table(table_m):
            drop_indices = set()
            found_header = False

            def _process_row(row_m):
                nonlocal drop_indices, found_header
                row_html = row_m.group(0)
                cells = list(cell_re.finditer(row_html))
                if not cells:
                    return row_html
                if not found_header:
                    found_header = True
                    for i, c in enumerate(cells):
                        text = re.sub(r'<[^>]+>', '', c.group(2)).strip().lower()
                        if text in header_names_lower:
                            drop_indices.add(i)
                if not drop_indices:
                    return row_html
                new_row = row_html
                for idx in sorted(drop_indices, reverse=True):
                    if idx < len(cells):
                        span = cells[idx].span()
                        new_row = new_row[:span[0]] + new_row[span[1]:]
                return new_row

            return row_re.sub(_process_row, table_m.group(0))

        return re.sub(r'<table\b[^>]*>.*?</table>', _process_table, html, flags=re.DOTALL)

    def _sanitise_html(self, html):
        """Strip dark-theme inline styles and background colours that would bleed into PDF."""
        html = re.sub(r'style="[^"]*"', '', html)
        html = re.sub(r'class="[^"]*"', '', html)
        # Stripe even table rows for readability
        html = re.sub(r'<tr>', lambda m, c=iter(range(9999)):
            f'<tr class="{"even" if next(c) % 2 == 0 else "odd"}">', html)
        # Older reports have a redundant "Where to check" column baked into
        # their stored content (duplicate of the Link column). Strip it from
        # any table, regardless of column count/position, before layout.
        html = self._strip_columns_by_header(html, ["where to check"])
        # xhtml2pdf's table renderer does not reliably wrap or clip long unbroken
        # tokens (raw URLs, whether linked or plain text) inside table cells - they
        # overflow into neighbouring cells instead. Shorten any such token so it
        # never reaches xhtml2pdf in the first place. Threshold is kept short (not
        # just "very long") because these tables commonly have 5-6 narrow columns,
        # leaving room for only ~15-20 characters per line before wrapping fails.
        def _shorten_run(m):
            run = m.group(0)
            return run[:16] + '…' if len(run) > 20 else run
        def _process_text_node(m):
            return '>' + re.sub(r'\S{21,}', _shorten_run, m.group(1)) + '<'
        html = re.sub(r'>([^<]+)<', _process_text_node, html)
        # xhtml2pdf's row-height calculation is unreliable when it has to infer
        # column widths implicitly (even under table-layout:fixed) - rows can
        # collapse onto a single overlapping line regardless of content length.
        # Giving every table explicit per-column widths via <colgroup> is the
        # standard mitigation. Tables that already declare a <colgroup> are
        # left untouched (the regex below requires <thead> to immediately
        # follow the opening <table> tag, which excludes them).
        def _insert_colgroup(m):
            table_open, thead_block = m.group(1), m.group(2)
            n_cols = len(re.findall(r'<th\b', thead_block))
            if n_cols == 0:
                return m.group(0)
            # References tables: #, Link, Title, Claim corroborated[, Where to
            # check], Evidence Quality. 5-col is the current shape (6-col is
            # kept for older stored reports that still have "Where to check").
            if n_cols == 5:
                widths = [5, 18, 18, 34, 25]
            elif n_cols == 6:
                widths = [5, 16, 16, 28, 16, 19]
            else:
                widths = [round(100 / n_cols)] * n_cols
            colgroup = '<colgroup>' + ''.join(f'<col style="width:{w}%"/>' for w in widths) + '</colgroup>'
            return table_open + colgroup + thead_block
        html = re.sub(r'(<table[^>]*>)(<thead>.*?</thead>)', _insert_colgroup, html, flags=re.DOTALL)
        return html

    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)

        from xhtml2pdf import pisa
        from markdown_it import MarkdownIt

        title = report.topic or report.query or f"Impact Case Study {report.id}"
        created = (
            report.created_at.strftime("Generated: %d %B %Y at %H:%M")
            if report.created_at else ""
        )
        md = MarkdownIt("commonmark", {"html": True}).enable("table")
        body_html = self._sanitise_html(md.render(report.generated_report or ""))

        full_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>{self._PDF_CSS}</style>
</head>
<body>
  <div class="pdf-title">{re.sub(r"<[^>]+>", "", title)}</div>
  {f'<div class="pdf-meta">{created}</div>' if created else ''}
  {body_html}
</body>
</html>"""

        pdf_buffer = io.BytesIO()
        status_obj = pisa.CreatePDF(
            io.BytesIO(full_html.encode("utf-8")),
            dest=pdf_buffer,
            encoding="utf-8",
        )

        if status_obj.err:
            return Response({"error": "PDF generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        filename = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()[:80] \
                   or f"impact-case-study-{report.id}"
        response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response

class PromptListView(generics.ListCreateAPIView):
    """
    List all prompts or create a new prompt.
    """
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    pagination_class = CustomPagination


class PromptDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a prompt.
    """
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer


class URLValidationView(generics.ListCreateAPIView):
    """
    A view to rank URLs using URLValidator and store/retrieve WebsiteEvaluation data.
    
    - POST: Send a list of URLs or URL-content pairs to rank and store evaluations.
    - GET: Retrieve all stored WebsiteEvaluations.
    - GET /url-validation/: Validate a single URL and return its evaluation.
    """
    queryset = WebsiteEvaluation.objects.all()
    serializer_class = WebsiteEvaluationSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = URLValidator()

    def get(self, request, *args, **kwargs):
        """
        Handle GET request to rank a single URL.
        """
        url = request.query_params.get('url')

        
        if url:
            try:
                validation_result = async_to_sync(self.validator.evaluate_url)(url)
                return Response(validation_result, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # If no URL provided, return all evaluations
        evaluations = WebsiteEvaluation.objects.all()
        serializer = self.get_serializer(evaluations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SerperSearchView(APIView):
    """
    API view to perform web search using Serper API.
    """
    def get(self, request):
        query = request.query_params.get("q")
        api = SerperAPI()
        result = api.get_sources(query)

        if result.failed:
            return Response({"error": result.error}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result.data, status=status.HTTP_200_OK)

class ReportGenerationView(APIView):
    """
    API endpoint that generates a report based on a topic.
    Supports customization via 'report_length' and 'industry'.
    If a report exists and 'force_regenerate' is not set, returns cached report.
    """
    # throttle_classes = ['base.throttling.ReportGenerationRateThrottle']

    @staticmethod
    def _impact_theme_title(query, fallback="Impact Case Study"):
        """Create a short, human-readable theme title from a REF search brief.

        The complete brief remains the description/search context.  Starter
        prompts begin with a useful subject line followed by named academics
        and evidence instructions; saving that entire brief as the title made
        themes unreadable and broke the previous title/description split.
        """
        text = (query or "").strip()
        if not text:
            return fallback
        first_block = re.split(r"\r?\n\s*\r?\n", text, maxsplit=1)[0].strip()
        first_block = re.sub(
            r"^(?:Build REF-ready impact evidence for:|Generate a REF-style impact case study report for:|Research impact case study for:)\s*",
            "",
            first_block,
            flags=re.IGNORECASE,
        ).strip(" -:\u2013\u2014")
        return (first_block or fallback)[:200]

    def generate_theme_name(self, query):
            # Get all existing (active) themes. Deleted themes are excluded so the
            # LLM isn't steered toward reusing a name that's currently in the trash.
            existing_themes = UseCaseTheme.objects.filter(is_deleted=False).values_list('title', flat=True)
            existing_themes_str = ", ".join(existing_themes) if existing_themes else "None"

            llm_core = ChatOpenAI(model="gpt-5.4-mini", temperature=1)
            prompt = THEME_NAME_GENERATION_PROMPT.format(
                query=query,
                existing_themes=existing_themes_str
            )
            response = llm_core.invoke(prompt)
            theme_name = re.sub(r"^```[a-zA-Z]*|```$", "", response.content.strip(), flags=re.MULTILINE)
            return theme_name

    def extract_uploaded_file_text(self, uploaded_files):
        extracted_documents = []

        for uploaded_file in uploaded_files:
            lower_name = uploaded_file.name.lower()
            if lower_name.endswith(".docx"):
                suffix = ".docx"
            elif lower_name.endswith(".pdf"):
                suffix = ".pdf"
            else:
                continue

            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_path = temp_file.name
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)

                if suffix == ".docx":
                    import docx2txt
                    text = docx2txt.process(temp_path) or ""
                else:
                    import pdfplumber
                    pages = []
                    with pdfplumber.open(temp_path) as pdf:
                        for page_number, page in enumerate(pdf.pages, 1):
                            page_text = page.extract_text() or ""
                            if page_text.strip():
                                pages.append(f"\n\n--- Page {page_number} ---\n{page_text.strip()}")
                    text = "\n".join(pages)

                if text.strip():
                    extracted_documents.append(
                        f"\n\n--- Uploaded {suffix.upper().lstrip('.')}: {uploaded_file.name} ---\n{text.strip()}"
                    )
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

        return "\n".join(extracted_documents).strip()

    def post(self, request):
        query = request.data.get("query","")
        pdf_text = request.data.get("pdf_text")
        pdf_filename = request.data.get("pdf_filename")
        # This tool only ever produces REF impact case studies - there is no
        # other kind of report it's used for - so this defaults to
        # "impact_case_study" rather than "", matching CompileReportFromUseCasesView's
        # default below. A caller that omits report_type used to silently get
        # the generic non-REF report format (no Aston-source filtering caveats,
        # no attribution/draft-commentary structure); that was a real bug, not
        # a legitimate alternate mode.
        report_type = request.data.get("report_type", "impact_case_study")
        prompt_id = request.data.get("prompt_id")
        debug_mode = request.data.get("debug_mode", False)
        theme_id = request.data.get("theme_id")
        skip_processed_urls = request.data.get("skip_processed_urls", False)
        if isinstance(skip_processed_urls, str):
            skip_processed_urls = skip_processed_urls.lower() in ["true", "1", "t", "yes"]
        if report_type == "impact_case_study":
            skip_processed_urls = False
        theme_is_featured = request.data.get("theme_is_featured", False)
        number_of_outcomes = request.data.get("number_of_outcomes", "10")
        search_complexity = request.data.get("search_complexity", "medium")
        max_links_to_scrape = request.data.get("max_links_to_scrape")
        if max_links_to_scrape not in (None, ""):
            max_links_to_scrape = int(max_links_to_scrape)
        else:
            max_links_to_scrape = None
        relevance_threshold = request.data.get("relevance_threshold")
        if relevance_threshold not in (None, ""):
            relevance_threshold = float(relevance_threshold)
        else:
            relevance_threshold = None
        impact_sections = request.data.get("impact_sections", [])
        if isinstance(impact_sections, str):
            try:
                impact_sections = json.loads(impact_sections)
            except json.JSONDecodeError:
                impact_sections = []
        include_summary = request.data.get("include_summary", True)
        if isinstance(include_summary, str):
            include_summary = include_summary.lower() in ["true", "1", "t", "yes"]

        # Optional list of {name, aston_start, aston_end} dicts, one per named
        # researcher, e.g. for a researcher who moved institutions during the
        # REF period - lets the synthesis prompt distinguish Aston's
        # institutional role from each individual academic's. Stored on
        # Report.metadata rather than a new model field.
        researcher_affiliations = request.data.get("researcher_affiliations", [])
        if isinstance(researcher_affiliations, str):
            try:
                researcher_affiliations = json.loads(researcher_affiliations)
            except json.JSONDecodeError:
                researcher_affiliations = []
        if not isinstance(researcher_affiliations, list):
            researcher_affiliations = []

        # Fresh impact-case-study searches should only discover/persist
        # evidence. The professional report is generated later from the saved
        # use cases via CompileReportFromUseCasesView, so finding evidence and
        # writing the report are separate user actions.
        skip_report_generation = request.data.get("skip_report_generation", False)
        if isinstance(skip_report_generation, str):
            skip_report_generation = skip_report_generation.lower() in ["true", "1", "t", "yes"]
        if report_type == "impact_case_study":
            skip_report_generation = True

        uploaded_file_text = self.extract_uploaded_file_text(request.FILES.getlist("uploaded_files"))
        if uploaded_file_text:
            pdf_filename = pdf_filename or "uploaded-file-context"
            pdf_text = "\n\n".join(part for part in [pdf_text, uploaded_file_text] if part)

        # Determine source priority: PDF-first if PDF is provided
        source_priority = "PDF_FIRST" if pdf_text else "WEB_FIRST"
        
        # if not query and prompt_id:
        #     return Response({"error": "Missing 'query' field."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the prompt if prompt_id is provided
        prompt = None
        if prompt_id:
            try:
                prompt = Prompt.objects.get(id=prompt_id)
                metadata = {"json_structure": prompt.json_structure} if prompt.json_structure else {}
            except Prompt.DoesNotExist:
                return Response({"error": "Prompt not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            prompt = None
            metadata = {}
        
        if(prompt):
                query = prompt.content

        if not query and report_type == "impact_case_study" and pdf_text:
            query = "Impact case study from uploaded documents"
        
        theme = None
        if theme_id:
            try:
                theme = UseCaseTheme.objects.get(id=theme_id, is_deleted=False)

                # Reusing an existing theme still respects the "Save as Featured
                # Theme" toggle. Only ever turns featured on here; unchecking the
                # box on a later search should not silently un-feature a theme,
                # since un-featuring is a deliberate separate action elsewhere.
                if theme_is_featured and not theme.featured:
                    theme.featured = True
                    theme.save(update_fields=["featured"])

                # Theme refreshes use the theme description. Impact case studies can
                # still use a professor's prompt/DOCX context with the selected theme.
                if report_type != "impact_case_study" or not query:
                    query = theme.description or query
            except UseCaseTheme.DoesNotExist:
                return Response({"error": "Theme not found"}, status=status.HTTP_404_NOT_FOUND)

        user_prompt = query
        # Use PDF/DOCX text as the extraction basis if provided, otherwise use the query field.
        search_query = pdf_text if pdf_text else query
        
        # --- Save prompt if no theme is selected by the user ---
        if not theme_id:
            # Only save if not already present (deduplicate by content)
            if query:
                prompt_obj, created = Prompt.objects.get_or_create(
                    content=query,
                    defaults={"title": query[:100]}
                )
                prompt = prompt_obj
        
        if not theme:
            if report_type == "impact_case_study":
                # Avoid a blocking LLM call before a report object exists. The
                # generator can still use the full prompt after the report is queued.
                base_theme_name = self._impact_theme_title(query, pdf_filename or "Impact Case Study")
                theme_name = base_theme_name
                if UseCaseTheme.objects.filter(title=theme_name, is_deleted=False).exists():
                    theme_name = f"{base_theme_name[:160]} ({now().strftime('%Y%m%d-%H%M%S')})"
                theme = UseCaseTheme.objects.create(
                    title=theme_name,
                    featured=theme_is_featured,
                    description=query or "Impact case study generated from uploaded context",
                )
            else:
                try:
                    # Generate a theme name using the LLM
                    theme_name = self.generate_theme_name(query)
                    print(f"Generated theme name: {theme_name}")
                    # Search for an existing *active* theme with the generated name.
                    # Deleted themes are skipped on purpose: re-searching the same
                    # topic after deleting its theme creates a fresh new theme
                    # rather than silently reviving the deleted one.
                    theme = UseCaseTheme.objects.filter(title=theme_name, is_deleted=False).first()
                except Exception as e:
                    return Response({"error": f"Failed to generate theme name: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # If no existing theme is found, create a new one
                if theme_name and not theme:
                    theme = UseCaseTheme.objects.create(title=theme_name, featured=theme_is_featured, description=query)
        
        theme_id = theme.id if theme else None

        # Return theme information immediately
        serializer = UseCaseThemeSerializer(theme)
        response_data = serializer.data

        # Create a report object with initial status
        try:
            # Impact case studies should be a fresh run each time. Standard
            # reports can still refresh the latest report for a selected theme.
            report_obj = None if report_type == "impact_case_study" else Report.objects.filter(theme=theme).order_by('-created_at').first()
            created = False
            
            if not report_obj:
                # Create new report if none exists
                report_obj = Report.objects.create(
                    theme=theme,
                    query=query,
                    prompt=prompt,
                    generated_report="",
                    thoughts=[],
                    updated_at=now(),
                    metadata={
                        "status": "processing",
                        "report_type": report_type,
                        "theme_id": theme_id,
                        "error": "None",
                        "source_priority": source_priority,
                        "pdf_filename": pdf_filename,
                        "pdf_uploaded": bool(pdf_text),
                        "impact_sections": impact_sections,
                        "include_summary": include_summary,
                        "skip_processed_urls": skip_processed_urls,
                        "researcher_affiliations": researcher_affiliations,
                        "skip_report_generation": skip_report_generation,
                    }
                )
                created = True
            else:
                # Update existing report
                report_obj.query = query
                report_obj.prompt = prompt
                report_obj.metadata.update({
                    "status": "processing",
                    "report_type": report_type,
                    "theme_id": theme_id,
                    "error": None,
                    "source_priority": source_priority,
                    "pdf_filename": pdf_filename,
                    "pdf_uploaded": bool(pdf_text),
                    "impact_sections": impact_sections,
                    "include_summary": include_summary,
                    "skip_processed_urls": skip_processed_urls,
                    "researcher_affiliations": researcher_affiliations,
                    "skip_report_generation": skip_report_generation,
                })
                report_obj.save()

            # Add report ID to response data
            response_data['report_id'] = report_obj.id

            # Start report generation in a separate thread
            import threading
            def run_report_generation():
                try:
                    print("Structured Report Generator view called")

                    print(f"Query searching for the theme: {query}")

                    generator = StructuredReportGenerator(
                        debug_mode=debug_mode,
                        report_obj=report_obj,
                        user_prompt=user_prompt,
                        search_query=search_query,
                        pdf_text=pdf_text,
                        pdf_filename=pdf_filename,
                        source_priority=source_priority,
                        theme_id=theme_id,
                        report_id=report_obj.id,
                        enable_credibility_check=True,
                        enable_relevance_check=True,
                        skip_processed_urls=skip_processed_urls,
                        number_of_outcomes=int(number_of_outcomes),
                        search_complexity=search_complexity,
                        max_links_to_scrape=max_links_to_scrape,
                        relevance_threshold=relevance_threshold,
                        report_type=report_type,
                        impact_sections=impact_sections,
                        include_summary=include_summary,
                        researcher_affiliations=researcher_affiliations,
                        skip_report_generation=skip_report_generation,
                    )
                    report_id, use_cases = generator.run()

                    # Don't clobber a FAILED/STOPPED status the generator already
                    # recorded (e.g. every web search request failed) with "completed"
                    if (not report_type and report_obj
                            and report_obj.metadata.get("status") not in ("FAILED", "STOPPED")):
                        report_obj.metadata["status"] = "completed"
                        report_obj.save()
                except Exception as e:
                    print(f"Error in report generation thread: {str(e)}")
                    if report_obj:
                        report_obj.metadata["status"] = "FAILED"
                        report_obj.metadata["error"] = str(e)
                        report_obj.save()

            # Start the report generation in a background thread
            thread = threading.Thread(target=run_report_generation)
            thread.start()

            # Return the theme information immediately
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Handle errors
            print(f"Error generating report: {str(e)}")
            
            if(not report_type and report_obj):
                # Update the report object with error
                report_obj.metadata["status"] = "error"
                report_obj.metadata["error"] = str(e)
                report_obj.save()
            
            # Return the report object with error status
            serializer = ReportSerializer(report_obj)
            return Response(serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# SDLC use case endpoint removed; this service now focuses only on general research impact


# Retail/pharmaceutical specific endpoints removed; only general research use cases remain


# AI SDLC specific endpoint removed to streamline research impact functionality

class CompileReportFromUseCasesView(APIView):
    """
    Builds a report directly from `UseCase` rows that already exist for a theme,
    skipping the search/scrape/extract pipeline entirely. Lets a user turn
    previously-gathered evidence into a report instantly instead of paying for
    a fresh web search.
    """

    def post(self, request):
        theme_id = request.data.get("theme_id")
        if not theme_id:
            return Response({"error": "theme_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            theme_id = int(theme_id)
        except (TypeError, ValueError):
            return Response({"error": "theme_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            theme = UseCaseTheme.objects.get(id=theme_id, is_deleted=False)
        except UseCaseTheme.DoesNotExist:
            return Response({"error": "Theme not found"}, status=status.HTTP_404_NOT_FOUND)

        use_case_ids = request.data.get("use_case_ids")
        if use_case_ids:
            try:
                use_case_ids = [int(i) for i in use_case_ids]
            except (TypeError, ValueError):
                return Response({"error": "use_case_ids must be a list of integers"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = UseCase.objects.filter(theme_id=theme_id)
        if use_case_ids:
            queryset = queryset.filter(id__in=use_case_ids)

        use_cases = list(queryset)
        if not use_cases:
            return Response(
                {"error": "No existing use cases found for this theme. Generate some first, or pick a different theme."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report_type = request.data.get("report_type", "impact_case_study")
        impact_sections = request.data.get("impact_sections", [])
        if isinstance(impact_sections, str):
            try:
                impact_sections = json.loads(impact_sections)
            except json.JSONDecodeError:
                impact_sections = []
        include_summary = request.data.get("include_summary", True)
        if isinstance(include_summary, str):
            include_summary = include_summary.lower() in ["true", "1", "t", "yes"]
        researcher_affiliations = request.data.get("researcher_affiliations", [])
        if isinstance(researcher_affiliations, str):
            try:
                researcher_affiliations = json.loads(researcher_affiliations)
            except json.JSONDecodeError:
                researcher_affiliations = []
        if not isinstance(researcher_affiliations, list):
            researcher_affiliations = []

        user_prompt = (
            request.data.get("prompt")
            or theme.description
            or f"Compile a REF impact case study report from {len(use_cases)} existing evidence item(s) for theme: {theme.title}"
        )

        try:
            report_obj = Report.objects.create(
                theme=theme,
                query=user_prompt,
                generated_report="",
                thoughts=[],
                updated_at=now(),
                metadata={
                    "status": "processing",
                    "report_type": report_type,
                    "theme_id": theme_id,
                    "error": None,
                    "impact_sections": impact_sections,
                    "include_summary": include_summary,
                    "compiled_from_existing_use_cases": True,
                    "source_use_case_count": len(use_cases),
                    "researcher_affiliations": researcher_affiliations,
                },
            )

            serializer = UseCaseThemeSerializer(theme)
            response_data = serializer.data
            response_data['report_id'] = report_obj.id

            import threading

            def run_compile():
                try:
                    generator = StructuredReportGenerator(
                        report_obj=report_obj,
                        user_prompt=user_prompt,
                        theme_id=theme_id,
                        report_id=report_obj.id,
                        report_type=report_type,
                        impact_sections=impact_sections,
                        include_summary=include_summary,
                        researcher_affiliations=researcher_affiliations,
                    )
                    generator.compile_from_existing_use_cases(use_cases)
                except Exception as e:
                    print(f"Error compiling report from existing use cases: {str(e)}")
                    report_obj.metadata["status"] = "FAILED"
                    report_obj.metadata["error"] = str(e)
                    report_obj.save()

            thread = threading.Thread(target=run_compile)
            thread.start()

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error setting up report compilation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UseCaseDestroyView(generics.DestroyAPIView):
    queryset = UseCase.objects.all()
    serializer_class = UseCaseSerializer


class UseCaseListView(generics.ListAPIView):
    """
    List all Use Cases.
    """
    queryset = UseCase.objects.all()
    serializer_class = UseCaseSerializer
    pagination_class = CustomPagination

    def _build_use_case_search_query(self, search_query, extracted_entity=None):
        searchable_fields = [
            'company',
            'use_case_type',
            'use_case_description',
            'tools',
            'performance_impact',
            'industry',
            'performance_improvement_category',
            'geography',
            'country',
            'use_case_name',
            'source',
        ]
        stop_words = {
            'and', 'for', 'from', 'impact', 'impacts', 'research', 'study',
            'case', 'cases', 'with', 'the', 'use', 'uses', 'using', 'show',
            'find', 'about', 'into', 'what', 'where', 'which'
        }
        entity_tokens = set()
        if extracted_entity:
            entity_tokens = {
                token.lower()
                for token in re.findall(r"[A-Za-z0-9]+", extracted_entity[0])
                if len(token) > 2
            }
        terms = [
            token.lower()
            for token in re.findall(r"[A-Za-z0-9]+", search_query or "")
            if len(token) > 2 and token.lower() not in stop_words and token.lower() not in entity_tokens
        ]

        if not terms:
            terms = [search_query]

        combined_query = Q()
        for term in terms:
            term_query = Q()
            for field in searchable_fields:
                term_query |= Q(**{f"{field}__icontains": term})
            combined_query &= term_query
        return combined_query
    
    def get_queryset(self):
        # "Researcher Affiliation Record" rows are metadata used to auto-populate
        # the report's Aston-attribution language (see _format_researcher_affiliations
        # in structured_report_generator.py) - they're not impact evidence and were
        # never meant to be browsable alongside real use cases. They still have
        # relevance_score=None (never scored, since the impact rubric doesn't apply
        # to them), so excluding that type here also matches what a reviewer expects
        # to see when browsing this theme's REF evidence.
        queryset = UseCase.objects.exclude(use_case_type='Researcher Affiliation Record')
        report_id = self.request.query_params.get('report_id', None)
        search_query = self.request.query_params.get('search', None)
        company = self.request.query_params.get('company', None)
        industry = self.request.query_params.get('industry', None)
        use_case_type = self.request.query_params.get('use_case_type', None)
        tools = self.request.query_params.get('tools', None)
        performance_impact = self.request.query_params.get('performance_impact', None)
        performance_improvement_category = self.request.query_params.get('performance_improvement_category', None)
        geography = self.request.query_params.get('geography', None)
        country = self.request.query_params.get('country', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        theme_id = self.request.query_params.get('theme_id', None)
        min_relevance_score = self.request.query_params.get('min_relevance_score', None)
        
        # Entity extraction parameters
        extract_entity = self.request.query_params.get('extract_entity', 'true').lower() == 'true'
        enforce_entity_match = self.request.query_params.get('enforce_entity_match', 'false').lower() == 'true'
        entity_name_param = self.request.query_params.get('entity_name', None)
        entity_type_param = self.request.query_params.get('entity_type', None)
        
        # Get sorting parameters
        sort_by = self.request.query_params.get('sort_by', '-created_at')
        sort_direction = self.request.query_params.get('sort_direction', 'desc')
        
        # Define allowed sort fields
        allowed_sort_fields = {
            'relevance_score': 'relevance_score',
            'credibility_score': 'credibility_score',
            'created_at': 'created_at',
            'updated_at': 'updated_at',
            'use_case_date': 'use_case_date',
            'published_date': 'published_date',
            'company': 'company',
            'industry': 'industry',
            'use_case_type': 'use_case_type',
            'performance_impact': 'performance_impact',
            'performance_improvement_category': 'performance_improvement_category',
            'geography': 'geography',
            'country': 'country'
        }
        
        # Apply sorting
        if sort_by in allowed_sort_fields:
            field = allowed_sort_fields[sort_by]
            if sort_direction.lower() == 'asc':
                queryset = queryset.order_by(field)
            else:
                queryset = queryset.order_by(f'-{field}')
        
        if report_id is not None:
            queryset = queryset.filter(report_id=report_id)
        
        # Entity extraction and filtering
        entity_extractor = EntityExtractor()
        extracted_entity = None
        
        # Check if entity was explicitly provided as parameters
        if entity_name_param:
            extracted_entity = (entity_name_param, entity_type_param or 'company')
        # Otherwise, try to extract from search query
        elif search_query and extract_entity:
            extracted_entity = entity_extractor.extract_entity(search_query)
        
        # Apply entity filtering if entity was found/provided
        if extracted_entity:
            entity_name, entity_type = extracted_entity
            queryset = entity_extractor.filter_by_entity(
                queryset, 
                entity_name, 
                entity_type, 
                strict=enforce_entity_match
            )
            # Store entity info in request for later use in response
            self._extracted_entity = extracted_entity
        
        # If enforce_entity_match is enabled but no entity found, still do full text search
        if search_query and not enforce_entity_match:
            queryset = queryset.filter(self._build_use_case_search_query(search_query, extracted_entity))
            
        if company:
            queryset = queryset.filter(company__icontains=company)
            
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
            
        if use_case_type:
            queryset = queryset.filter(use_case_type__icontains=use_case_type)
            
        if tools:
            queryset = queryset.filter(tools__icontains=tools)
            
        if performance_impact:
            queryset = queryset.filter(performance_impact__icontains=performance_impact)

        if performance_improvement_category:
            queryset = queryset.filter(performance_improvement_category__icontains=performance_improvement_category)

        if geography:
            queryset = queryset.filter(geography__icontains=geography)

        if country:
            queryset = queryset.filter(country__icontains=country)
            
        if start_date and end_date:
            queryset = queryset.filter(use_case_date__range=[start_date, end_date])
        
        if theme_id:
            queryset = queryset.filter(theme__id=theme_id)
        
        if min_relevance_score:
            queryset = queryset.filter(relevance_score__gte=float(min_relevance_score))

        # Filter for non-null field if requested
        not_null_field = self.request.query_params.get('not_null_field', None)
        if not_null_field:
            allowed_fields = [
                'relevance_score', 'credibility_score', 'created_at', 'use_case_date',
                'company', 'industry', 'use_case_type', 'performance_impact',
                'performance_improvement_category', 'geography', 'country', 'tools'
            ]
            if not_null_field in allowed_fields:
                queryset = queryset.exclude(**{f"{not_null_field}__isnull": True}).exclude(**{not_null_field: ""})

        # Older runs could save several reworded findings from the same URL.
        # Show one representative evidence item per source without deleting
        # the historical rows; newly generated runs are consolidated earlier
        # in the pipeline as well.
        canonical_source_ids = (
            queryset.exclude(source__isnull=True)
            .exclude(source="")
            .order_by()
            .values("source")
            .annotate(keep_id=Max("id"))
            .values("keep_id")
        )
        queryset = queryset.filter(
            Q(source__isnull=True) | Q(source="") | Q(id__in=Subquery(canonical_source_ids))
        )
        return queryset
    
    def get(self, request, *args, **kwargs):
        """
        Override the get method to handle export requests.
        """
        # Check if this is an export request
        export_format = request.query_params.get('export', None)
        
        # Get the queryset
        queryset = self.get_queryset()

        
        # If it's an export request, return the appropriate format
        if export_format:
            # Serialize the data
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            
            # Export based on the requested format
            if export_format == 'csv':
                return ExportUtils.export_to_csv(data, filename_prefix="use_cases")
            elif export_format == 'excel':
                return ExportUtils.export_to_excel(data, filename_prefix="use_cases")
            elif export_format == 'json':
                return ExportUtils.export_to_json(data, filename_prefix="use_cases")
        
        # Otherwise, proceed with the normal list view
        return super().get(request, *args, **kwargs)

class UseCaseThemeListView(generics.ListCreateAPIView):
    """
    View for listing all use case themes and creating new ones.
    By default only active (non-deleted) themes are returned; pass
    ?deleted=true to list the trash instead.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        featured = self.request.query_params.get('featured', None)

        if featured is not None:
            # Convert the featured parameter to a boolean
            featured_bool = featured.lower() in ['true', '1', 't', 'yes']
            queryset = queryset.filter(featured=featured_bool)

        deleted = self.request.query_params.get('deleted', 'false')
        deleted_bool = deleted.lower() in ['true', '1', 't', 'yes']
        queryset = queryset.filter(is_deleted=deleted_bool)

        return queryset

    queryset = UseCaseTheme.objects.all()
    serializer_class = UseCaseThemeSerializer
    ordering = ['title']

class UseCaseThemeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a specific use case theme.
    Deleting is a soft delete: the theme (and its reports/use cases) stays in
    the database so it can be restored later via UseCaseThemeRestoreView.
    """
    queryset = UseCaseTheme.objects.all()
    serializer_class = UseCaseThemeSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])


class UseCaseThemeRestoreView(APIView):
    """
    Restores a soft-deleted theme, bringing its original reports and use
    cases back with it since they were never actually removed.
    """

    def post(self, request, pk):
        try:
            theme = UseCaseTheme.objects.get(pk=pk)
        except UseCaseTheme.DoesNotExist:
            return Response({"error": "Theme not found"}, status=status.HTTP_404_NOT_FOUND)

        conflict = UseCaseTheme.objects.filter(title=theme.title, is_deleted=False).exclude(pk=theme.pk)
        if conflict.exists():
            return Response(
                {"error": f"A theme named '{theme.title}' already exists. Rename or delete it before restoring this one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        theme.is_deleted = False
        theme.save(update_fields=['is_deleted'])
        serializer = UseCaseThemeSerializer(theme)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StopReportGenerationView(APIView):
    """
    API endpoint to stop a running report generation process.
    """
    def post(self, request, theme_id):
        try:
            # Find the report with the given theme_id
            report = Report.objects.filter(theme_id=theme_id).order_by('-id').first()
            
            if not report:
                return Response({
                    "error": f"No report found for theme_id: {theme_id}"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Set should_stop flag
            report.metadata['should_stop'] = True
            report.metadata['status'] = 'stopping'
            report.save()
            
            return Response({
                "message": "Stop signal sent to report generation process",
                "report_id": report.id,
                "status": "stopping"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FindReportByThemeView(APIView):
    """
    API endpoint to find a report by theme_id.
    Returns the most recent report for the given theme.
    """
    def get(self, request, theme_id):
        try:
            report = Report.objects.filter(theme_id=theme_id).order_by('-created_at').first()
            
            if not report:
                return Response({
                    "error": f"No report found for theme_id: {theme_id}"
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = ReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FieldOptionsView(generics.GenericAPIView):
    """
    Get all possible values for use case search filters
    """
    def get(self, request, *args, **kwargs):
        theme_id = request.query_params.get('theme_id')
        queryset = UseCase.objects.all()
        
        if theme_id:
            queryset = queryset.filter(theme_id=theme_id)

        # Get unique values for each field using distinct() and case-insensitive handling
        use_case_types = queryset.values_list('use_case_type', flat=True).distinct()
        companies = queryset.values_list('company', flat=True).distinct()
        industries = queryset.values_list('industry', flat=True).distinct()
        performance_impacts = queryset.values_list('performance_impact', flat=True).distinct()
        tools_raw = queryset.values_list('tools', flat=True).distinct()
        countries = queryset.values_list('country', flat=True).distinct()

        # Filter out None/empty values, normalize case, and ensure uniqueness
        def clean_and_sort(values):
            unique_values = set()
            for value in values:
                if value and value.strip():
                    normalized = value.strip()
                    unique_values.add(normalized)
            return sorted(unique_values)

        # Special handling for tools: split by comma, trim, flatten, deduplicate
        tools_set = set()
        for entry in tools_raw:
            if entry:
                for tool in entry.split(','):
                    tool = tool.strip()
                    if tool:
                        tools_set.add(tool)
        tools = sorted(tools_set)

        return Response({
            'useCaseTypes': clean_and_sort(use_case_types),
            'companies': clean_and_sort(companies),
            'industries': clean_and_sort(industries),
            'impacts': clean_and_sort(performance_impacts),
            'tools': tools,
            'countries': clean_and_sort(countries),
        })

class TestUrlExtractionView(generics.GenericAPIView):
    """
    Test endpoint for extracting use cases from a single URL.
    
    Expected request body:
    {
        "url": "https://example.com/article",
        "user_prompt": "Optional prompt to guide extraction",
        "theme_id": 123  # Optional theme ID
    }
    """
    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        user_prompt = request.data.get('user_prompt', '')
        theme_id = request.data.get('theme_id')
        
        if not url:
            return Response(
                {"error": "URL is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            extractor = SingleUrlExtractor(
                user_prompt=user_prompt,
                theme_id=theme_id
            )
            
            # Call extract_from_url directly since it's now synchronous
            use_cases = extractor.extract_from_url(url)
            
            # Convert use cases to dictionaries
            result = [uc.to_dict() for uc in use_cases]
            
            return Response({
                "url": url,
                "use_cases": result
            })
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SavedEntitySearchListView(generics.ListCreateAPIView):
    """
    List all saved entity searches or create a new one.
    
    GET: Returns list of all saved entity searches, sorted by favorites and recent usage
    POST: Creates a new saved entity search
    """
    queryset = SavedEntitySearch.objects.all()
    serializer_class = SavedEntitySearchSerializer
    pagination_class = CustomPagination
    
    def get_queryset(self):
        queryset = SavedEntitySearch.objects.all()
        
        # Filter by entity type if provided
        entity_type = self.request.query_params.get('entity_type', None)
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        # Filter by favorites if requested
        favorites_only = self.request.query_params.get('favorites_only', 'false').lower() == 'true'
        if favorites_only:
            queryset = queryset.filter(is_favorite=True)
        
        # Search by entity name or display name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(display_name__icontains=search) |
                Q(entity_name__icontains=search)
            )
        
        return queryset


class SavedEntitySearchDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a saved entity search.
    """
    queryset = SavedEntitySearch.objects.all()
    serializer_class = SavedEntitySearchSerializer
    
    def put(self, request, *args, **kwargs):
        """Update a saved search and track usage"""
        response = super().put(request, *args, **kwargs)
        
        # Update usage tracking
        instance = self.get_object()
        instance.usage_count += 1
        instance.last_used = now()
        instance.save()
        
        return response


class SavedEntitySearchUsageView(APIView):
    """
    Track usage of a saved entity search (increment counter, update last_used).
    """
    def post(self, request, pk):
        try:
            search = SavedEntitySearch.objects.get(pk=pk)
            search.usage_count += 1
            search.last_used = now()
            search.save()
            
            serializer = SavedEntitySearchSerializer(search)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SavedEntitySearch.DoesNotExist:
            return Response(
                {"error": "Saved search not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EntitySuggestionsView(generics.GenericAPIView):
    """
    Get suggestions for entity autocomplete in search.
    
    Supports:
    - get_all: true -> Get all company/institution suggestions
    - entity_type: company|university|research_institution|person
    - search: partial entity name for filtering suggestions
    """
    def get(self, request):
        extractor = EntityExtractor()
        entity_type = request.query_params.get('entity_type', 'company')
        search_term = request.query_params.get('search', '')
        get_all = request.query_params.get('get_all', 'false').lower() == 'true'
        
        try:
            if get_all:
                if entity_type == 'company':
                    suggestions = extractor.get_all_company_suggestions(limit=50)
                elif entity_type in ['university', 'research_institution']:
                    suggestions = extractor.get_all_institution_suggestions(limit=50)
                else:
                    suggestions = []
            elif search_term:
                suggestions = extractor.get_entity_suggestions(search_term)
            else:
                suggestions = []
            
            return Response({
                'suggestions': suggestions,
                'count': len(suggestions)
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
