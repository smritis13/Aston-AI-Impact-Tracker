from django.urls import path
from .views import *

urlpatterns = [
    
    path('', ContentListCreateView.as_view(), name='content-list'),
    path('<int:pk>/', ContentDetailView.as_view(), name='content-detail'),

    # ContentSource URLs
    path('source/', ContentSourceListCreateView.as_view(), name='source-list'),
    path('source/<int:pk>/', ContentSourceDetailView.as_view(), name='source-detail'),
    
    # ContentSourceURL URLs
    path('source/<int:content_source_id>/urls/', 
         ContentSourceURLListCreateView.as_view(), 
         name='source-url-list'),
    path('source/urls/<int:pk>/', ContentSourceURLDetailView.as_view(),  name='source-url-detail'),
    
    # ContentSourcecrapeLog URLs
    path('source/<int:content_source_id>/scrape-logs/', 
         ContentSourceScrapeLogListView.as_view(), 
         name='source-scrape-log-list'),
        
    
    path('index/', IndexContentAPIView.as_view(), name='re_index'),
    path('scrape/', ScrapeAndIndexContentAPIView.as_view(), name='scrape-and-index'),
    path('search/', SearchContentAPIView.as_view(), name='content-search'),


    path("web-search/", WebSearchView.as_view(), name="web-search"),
    path('scrape-saved-urls/', ContentScraperView.as_view(), name='scrape-saved-urls'),

    path("reports/", ReportListView.as_view(), name="report-list"),
    path("reports/<int:pk>/", ReportDetailView.as_view(), name="report-detail"),
    path("reports/<int:pk>/export-pdf/", ReportPdfExportView.as_view(), name="report-export-pdf"),
    path("reports/<int:theme_id>/stop/", StopReportGenerationView.as_view(), name="stop-report-generation"),
    path("reports/theme/<int:theme_id>/", FindReportByThemeView.as_view(), name="find-report-by-theme"),

    path("prompts/", PromptListView.as_view(), name="prompt-list"),
    path("prompts/<int:pk>/", PromptDetailView.as_view(), name="prompt-detail"),

    path("url-validation/", URLValidationView.as_view(), name="url-validation"),

    path("serper-search/", SerperSearchView.as_view(), name="serper-search"),
    path("report-generation/", ReportGenerationView.as_view(), name="report-generation"),
    path("reports/compile-from-use-cases/", CompileReportFromUseCasesView.as_view(), name="compile-report-from-use-cases"),

    # Use Case URLs
    path("use-cases/", UseCaseListView.as_view(), name="use-case-list"),
    path("use-cases/<int:pk>/", UseCaseDestroyView.as_view(), name="use-case-detail"),

    path('sources/', ContentSourceListCreateView.as_view(), name='content-source-list'),
    path('sources/<int:pk>/', ContentSourceDetailView.as_view(), name='content-source-detail'),
    path('sources/<int:content_source_id>/urls/', ContentSourceURLListCreateView.as_view(), name='content-source-url-list'),
    path('urls/<int:pk>/', ContentSourceURLDetailView.as_view(), name='content-source-url-detail'),

    # UseCaseTheme URLs
    path('themes/', UseCaseThemeListView.as_view(), name='use-case-theme-list'),
    path('themes/<int:pk>/', UseCaseThemeDetailView.as_view(), name='use-case-theme-detail'),
    path('themes/<int:pk>/restore/', UseCaseThemeRestoreView.as_view(), name='use-case-theme-restore'),

    path('field-options/', FieldOptionsView.as_view(), name='field-options'),

    path('test-url-extraction/', TestUrlExtractionView.as_view(), name='test_url_extraction'),
    
    # Saved Entity Searches URLs
    path('saved-searches/', SavedEntitySearchListView.as_view(), name='saved-entity-search-list'),
    path('saved-searches/<int:pk>/', SavedEntitySearchDetailView.as_view(), name='saved-entity-search-detail'),
    path('saved-searches/<int:pk>/track-usage/', SavedEntitySearchUsageView.as_view(), name='saved-entity-search-track-usage'),
    
    # Entity Suggestions and Alias Resolution URLs
    path('entity-suggestions/', EntitySuggestionsView.as_view(), name='entity-suggestions'),
]
