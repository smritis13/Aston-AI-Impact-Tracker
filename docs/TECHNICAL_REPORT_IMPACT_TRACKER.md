# Aston AI Research Tool: Technical Report and Impact Tracker Explanation

## 1. Executive Summary

This tool is a full-stack AI research platform built to discover, scrape, analyze, and store structured research findings from the web. In its current form, its most important business function is not just "report generation" but **impact tracking**.

The system acts as an impact tracker because it:

- takes a research question or theme,
- searches the web for relevant evidence,
- scrapes source pages,
- extracts structured impact/use-case records,
- scores those records for credibility and relevance,
- stores them in a queryable database,
- groups them under reusable themes and reports,
- supports filtering, exporting, and re-use.

In other words, the tool converts unstructured web content into structured evidence entries that can be tracked over time.

## 2. High-Level Architecture

The project is split into:

- `backend/`: Django REST Framework application
- `frontend/`: React-based frontend package and static assets
- ChromaDB: vector database used for semantic indexing/search
- OpenAI/LangChain/LangGraph: LLM orchestration and extraction logic
- Tavily: web search provider
- Pusher: real-time progress streaming
- MySQL: primary relational database

At a system level, the workflow is:

1. User provides a query or chooses a theme.
2. Backend creates or updates a `Report`.
3. The report generator plans search tasks with an LLM.
4. Tavily search returns candidate URLs.
5. URLs are scraped into page text.
6. The LLM extracts structured `UseCase` records.
7. Optional credibility and relevance checks score each use case.
8. Results are stored in the database and can be filtered/exported.

## 3. Core Backend Modules

### 3.1 Content module

The `content` app is the main impact-tracking domain.

Important models:

- `Report`: container for one research run
- `UseCase`: the main impact-tracking record
- `UseCaseTheme`: reusable grouping/category for a report family
- `ScrapedURL`: stores scraped page content tied to a report
- `Prompt`: stores prompt templates or saved user prompts
- `WebsiteEvaluation`: stores domain-level trust/quality scoring
- `Content`, `ContentSource`, `ContentSourceURL`, `UrlToScrape`: support scraping/indexing workflows

### 3.2 Workflow module

The `workflows` app is a general-purpose graph workflow engine using LangGraph-style execution concepts:

- `WorkflowDefinition`: stores graph JSON
- `WorkflowExecution`: stores input, output, status, execution trace
- `Agent`: stores agent configs
- `ToolConfig`: stores tool definitions and requirements

This is more generic orchestration infrastructure. It is useful for extensibility, but the current impact tracker mainly relies on the `StructuredReportGenerator` in the LLM layer.

### 3.3 Agent module

The `agent` app defines a simpler visual workflow model:

- `Workflow`
- `Node`
- `Edge`

This appears to support node-based workflow execution and experimentation. It is adjacent to the impact-tracking flow rather than the main persistence model for tracked impact data.

## 4. The Real Impact Tracker Data Model

The main impact tracker entity is `UseCase` in `backend/content/models.py`.

It stores:

- `report`: which report produced the record
- `theme`: which theme/group it belongs to
- `use_case_name`: short summary of the impact example
- `use_case_type`: category/type of impact
- `company`
- `industry`
- `tools`
- `use_case_description`
- `performance_improvement_category`
- `performance_impact`
- `geography`
- `country`
- `use_case_date`
- `source`
- `credibility_score`
- `is_credible`
- `credibility_reasoning`
- `relevance_score`
- `is_relevant`
- `relevance_reasoning`

This is why the tool qualifies as an impact tracker:

- every extracted case is stored as a normalized record,
- each record has source attribution,
- each record can be assessed for trust and relevance,
- each record can be grouped by theme/report,
- records can be searched, filtered, sorted, and exported.

## 5. Why `Report` and `Theme` Matter

`Report` is the execution container. It stores:

- `topic`
- `query`
- `generated_report`
- `thoughts`
- `metadata`
- optional `prompt`
- optional `theme`

`metadata` is especially important because it tracks runtime state such as:

- processing status,
- progress counters,
- start/completion times,
- stop flags,
- error details,
- report type.

`UseCaseTheme` is the higher-level grouping mechanism. A theme lets the user organize many impact records under a reusable topic such as:

- AI in healthcare
- GenAI in banking
- SDLC automation
- sector-specific transformation themes

This means the tool tracks impact both:

- at the **run level** via `Report`
- at the **evidence level** via `UseCase`
- at the **portfolio/topic level** via `UseCaseTheme`

## 6. End-to-End Impact Tracking Flow

The most important endpoint is:

- `POST /api/content/report-generation/`

### 6.1 Theme selection or creation

When a request arrives:

- the backend reads `query`, `prompt_id`, `theme_id`, and flags
- if a theme is supplied, it reuses it
- otherwise it generates a theme name with an LLM
- if needed, it creates a new `UseCaseTheme`

### 6.2 Report creation

The system then:

- finds the most recent report for that theme, or
- creates a new `Report`

It sets metadata like:

- `status = processing`
- `theme_id`
- `report_type`
- `error`

### 6.3 Background generation

A background thread starts `StructuredReportGenerator`, which performs the real pipeline.

## 7. Structured Report Generator

`backend/core/llm/langchain/langgraph/structured_report_generator.py` is the operational core of the impact tracker.

It implements a graph-based pipeline:

1. `planning`
2. `search`
3. `scrape`
4. `extract`

### 7.1 Planning stage

The generator first:

- generates likely use-case categories,
- asks the LLM to create research/search tasks,
- stores those tasks in graph state.

This makes the system adaptive: it does not only run one fixed query. It asks the model to decompose the research problem into tasks and search queries.

### 7.2 Search stage

For each task:

- it runs Tavily search queries,
- transforms results into `{title, link, snippet, source}`,
- optionally skips URLs already processed for the theme.

This is one of the clearest impact-tracker features: the system avoids re-processing already tracked evidence when `skip_processed_urls=True`.

### 7.3 Scrape stage

The scraper:

- collects URLs from search results,
- batches them,
- scrapes each page asynchronously,
- stores page text in memory for extraction.

### 7.4 Extract stage

For each scraped page:

- the LLM receives the article text plus a target schema,
- it returns structured JSON,
- each extracted record is turned into an `ExtractedUseCase`,
- then persisted as a real `UseCase` row.

This is the exact moment where raw research becomes tracked impact data.

## 8. Scoring and Evidence Quality

The system has two important quality checks:

- credibility scoring
- relevance scoring

These are optional flags in the generator but are enabled by default in the report generation view.

### 8.1 Credibility scoring

For each extracted use case, the LLM evaluates:

- source credibility
- evidence quality
- specificity of claims
- trustworthiness of the use case description

Outputs written back to the database:

- `credibility_score`
- `is_credible`
- `credibility_reasoning`

### 8.2 Relevance scoring

The LLM also checks whether the extracted use case actually matches:

- the original user prompt
- the selected theme

Outputs written back:

- `relevance_score`
- `is_relevant`
- `relevance_reasoning`

### 8.3 Domain-level trust scoring

The `URLValidator` and `WebsiteEvaluation` model add another layer.

The system can score domains on:

- authority
- HTTPS/security
- recency
- transparency
- peer review / content quality

This produces a `total_score` from 0 to 10 for domains. In the serializer, this appears as `url_validation_score` for a `UseCase`.

So the tool supports:

- record-level scoring,
- source-domain scoring,
- prompt/theme relevance scoring.

That is strong impact-tracker behavior because it helps distinguish good evidence from weak evidence.

## 9. Search, Filter, Export, and Retrieval

The `UseCaseListView` makes the stored impact data operational.

Supported filters include:

- `report_id`
- `theme_id`
- `company`
- `industry`
- `use_case_type`
- `tools`
- `performance_impact`
- `performance_improvement_category`
- `geography`
- `country`
- date range
- minimum relevance score
- generic search text

Supported sorting includes:

- `relevance_score`
- `credibility_score`
- `created_at`
- `use_case_date`
- company/industry/type fields

Supported exports:

- CSV
- Excel
- JSON

This matters for an impact tracker because it turns the database into a reporting dataset, not just a one-time AI answer.

## 10. Semantic Search and Vector Indexing

The system also includes semantic indexing:

- `ContentIndexer` indexes scraped content into ChromaDB
- `UseCaseIndexer` indexes use cases by theme

Embeddings are generated with OpenAI-backed embedding components. This enables:

- semantic retrieval over source material,
- semantic retrieval over stored use cases,
- future analysis and retrieval-augmented workflows.

This improves the tool’s ability to rediscover and reuse prior evidence.

## 11. Real-Time Progress Tracking

Progress is streamed using `PusherService`.

The report generator sends progress updates for:

- planning,
- query execution,
- URL scraping,
- use-case extraction,
- credibility checking,
- relevance checking,
- completion/stopping/failure.

Status is also persisted into `Report.metadata`.

This makes the tool an impact tracker in an operational sense too: users can monitor a report run while evidence is being gathered.

## 12. APIs That Matter Most

Key endpoints in `backend/content/urls.py`:

- `POST /api/content/report-generation/`: generate/update a themed report
- `GET /api/content/reports/`: list reports
- `GET /api/content/reports/<id>/`: fetch a report
- `POST /api/content/reports/<theme_id>/stop/`: stop generation
- `GET /api/content/reports/theme/<theme_id>/`: get latest report for a theme
- `GET /api/content/use-cases/`: list/filter/export impact entries
- `GET /api/content/themes/`: list themes
- `GET /api/content/field-options/`: get filter values
- `POST /api/content/web-search/`: store URLs from web search
- `POST /api/content/scrape-saved-urls/`: scrape queued URLs
- `POST /api/content/search/`: semantic search over indexed content

## 13. Technical Strengths

The strongest parts of the design are:

- clear normalized persistence for impact records via `UseCase`
- support for theme-based research portfolios
- report metadata used as execution state
- traceable source URLs
- credibility and relevance scoring
- exportable and filterable results
- semantic indexing for future reuse
- stop/resume-aware long-running generation flow

## 14. Technical Weaknesses and Risks

While the system is strong conceptually, I found some implementation risks:

- Report generation runs in a Python thread inside the web process, which is fragile for long jobs. A queue system like Celery/RQ would be safer.
- The frontend source code is not present in the repo in a normal `frontend/src` structure, so the UI flow cannot be fully reviewed from this checkout.
- Some status strings are inconsistent (`processing`, `RUNNING`, `completed`, `COMPLETED`, `error`, `FAILED`), which can make clients harder to implement reliably.
- Some comments and old migration history show the app evolved from specialized domains into a generic impact tracker, so parts of the codebase still carry legacy structure.
- `use_case_date` is stored as text instead of a real date field, which weakens filtering and validation.
- Domain credibility scoring uses an LLM estimation from domain name only, so it is helpful but not authoritative.
- Background-thread execution may not survive restarts or scale cleanly across multiple backend instances.

## 15. Is This Really an Impact Tracker?

Yes. Technically, this tool is best described as:

**an AI-assisted evidence discovery, extraction, and structured impact tracking platform**

It is not only a chat/report tool because the main value is stored in persistent, scored, queryable `UseCase` records.

The impact tracker dimension comes from:

- structured capture of impact evidence,
- repeatable grouping by theme,
- quality scoring,
- filtering and comparison,
- export to analysis-ready formats,
- semantic reuse of prior knowledge,
- source traceability.

## 16. Recommended Description for Your Report or Presentation

You can describe the tool like this:

"The Aston AI Research Tool is a Django and React based AI research platform that functions as an impact tracker. It automates web search, content scraping, LLM-based evidence extraction, credibility and relevance scoring, and stores the results as structured use-case records linked to themes and reports. This allows users to build reusable, searchable, and exportable databases of real-world impact evidence rather than relying on one-off AI answers."

## 17. Final Conclusion

From a technical perspective, the core tracked object is the `UseCase` record, not the final text report. The report is the container and the use cases are the evidence.

That is the key idea to understand:

- `Report` = a research run
- `Theme` = a reusable topic bucket
- `UseCase` = the actual tracked impact entry

So if you are explaining this system as an impact tracker, the strongest statement is:

**the tool transforms unstructured web evidence into structured, scored, source-linked impact records that can be tracked, searched, filtered, and exported over time.**
