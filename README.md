# Aston AI Impact Tracker

A web application that searches for, evaluates and drafts evidence of research
impact, structured to the criteria used in the Research Excellence Framework
(REF). It is built on the Aston AI Research Tool, a use case discovery system
developed at Aston University, and extends that system to produce REF style
impact case study reports rather than lists of use cases.

## Status of this repository

This repository contains a research prototype. It was developed as the
practical component of an MSc dissertation and has not been through the
security review, rate limiting or crawl policy work that deployment would
require. Section headings in the documentation under `docs/` describe what the
code does; where a feature is partial, the documentation says so.

The codebase was inherited rather than written from scratch. The documentation
as it stood at handover is preserved unchanged at
[`docs/HANDOVER_README.md`](docs/HANDOVER_README.md), so that the starting
point and the work done since can be told apart.

## What the system does

A user selects or creates a theme, enters a prompt describing the research
whose impact is to be evidenced, and the system runs an agentic pipeline that
searches the web, scrapes candidate sources, extracts structured evidence,
scores it, and synthesises a report in the six section shape of a REF impact
case study: summary of the impact, underpinning research, references to the
research, details of the impact, sources to corroborate the impact, and a
readiness assessment against reach, significance, attribution and
corroboration.

Evidence that cannot be traced back to a scraped source is filtered out before
it reaches a report. Direct quotations are checked against the visible text of
the page they are attributed to, and numeric claims are checked in the same
way.

## Architecture

**Backend.** Django 4.2 with Django REST Framework, MySQL for persistence and
ChromaDB for the semantic index used by the chat feature. The report pipeline
is a LangGraph `StateGraph` in
`backend/core/llm/langchain/langgraph/structured_report_generator.py`. The
outer graph is a plan, execute and replan loop over the nodes `planning`,
`task_exec` and `replan`. Each task runs a nested subgraph of `search`,
`scrape` and `extract`. Progress is streamed to the browser over Pusher.

**Prompts.** The REF aligned prompts are held separately in
`backend/core/llm/langchain/langgraph/ref_prompts.py`, covering planning,
extraction, relevance and credibility checking, impact summarisation and case
study synthesis.

**Evaluation.** `backend/content/management/commands/evaluate_pipeline.py` is a
Django management command that checks generated reports for the required
section structure and readiness rows and reports summary statistics across
themes.

**Frontend.** React 18 with TypeScript, React Query and React Bootstrap,
covering theme selection, report generation with live progress, and the report
history and library views.

**External services.** OpenAI for the language models, Tavily for web search
and Pusher for progress streaming. All three require API keys.

## Getting started

See [`docs/QUICK_START.md`](docs/QUICK_START.md) for the shortest path, or
[`docs/DOCKER_SETUP.md`](docs/DOCKER_SETUP.md) for the full Docker
instructions. The application expects a `.env` file in `backend/` holding
`OPENAI_API_KEY`, `TAVILY_API_KEY`, `SECRET_KEY` and the four Pusher variables.

## Documentation

| Document | Covers |
|---|---|
| [QUICK_START.md](docs/QUICK_START.md) | Running the application for the first time |
| [DOCKER_SETUP.md](docs/DOCKER_SETUP.md) | Local Docker setup in full |
| [DOCKER_REBUILD_GUIDE.md](docs/DOCKER_REBUILD_GUIDE.md) | Rebuilding containers without losing data |
| [DATABASE_PERSISTENCE.md](docs/DATABASE_PERSISTENCE.md) | Which operations preserve and which destroy data |
| [DATABASE_BACKUP_GUIDE.md](docs/DATABASE_BACKUP_GUIDE.md) | Backup and restore scripts |
| [AZURE_DEPLOYMENT.md](docs/AZURE_DEPLOYMENT.md) | Deployment notes |
| [WORKFLOW_ANALYSIS.md](docs/WORKFLOW_ANALYSIS.md) | The report pipeline stage by stage |
| [TECHNICAL_REPORT_IMPACT_TRACKER.md](docs/TECHNICAL_REPORT_IMPACT_TRACKER.md) | Design and data model |
| [REF_PROMPTS_IMPLEMENTATION_GUIDE.md](docs/REF_PROMPTS_IMPLEMENTATION_GUIDE.md) | How the REF prompts are wired into the graph |
| [WRITING_REF_PROMPTS.md](docs/WRITING_REF_PROMPTS.md) | Writing prompts that produce usable impact evidence |
| [ENTITY_EXTRACTION_FEATURE.md](docs/ENTITY_EXTRACTION_FEATURE.md) | Entity extraction and strict filtering |
| [TESTING_GUIDE_ENTITY_EXTRACTION.md](docs/TESTING_GUIDE_ENTITY_EXTRACTION.md) | Testing that feature |
| [HANDOVER_README.md](docs/HANDOVER_README.md) | The documentation as received at handover, unchanged |

## Audit records

`audit-reports/` holds dated records of defects found by manual inspection of
generated output, with the screenshots that evidence them. These are referenced
in the dissertation and should not be removed.

## Licence

Not yet determined.
