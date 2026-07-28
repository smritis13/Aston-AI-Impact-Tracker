# Copilot / AI Agent Instructions for Aston AI Research Tool

Purpose: quick, actionable guidance so an AI coding assistant can be immediately productive in this repo.

- **Big picture:** Full-stack app with a Django REST backend and React TypeScript frontend. Vector search uses ChromaDB; autonomous workflows use LangChain / LangGraph. See [README.md](README.md) for an overview and tech stack.

- **Start (dev)**:
  - Backend: create venv, install, migrate, run:
    ```bash
    cd backend
    python -m venv venv
    venv\Scripts\activate     # Windows
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver
    ```
  - Frontend:
    ```bash
    cd frontend
    npm install
    npm start
    ```
  - Docker compose (dev containerized): `docker-compose up --build` (see [docker-compose.yml](docker-compose.yml)).

- **Environment & secrets:** configuration is loaded from a `.env` in `backend` via `python-dotenv`. Key env vars: `OPENAI_API_KEY`, DB_* vars, `PUSHER_*`. See [backend/config/settings.py](backend/config/settings.py#L1-L60).

- **Where to look first (important files):**
  - Backend settings & env: [backend/config/settings.py](backend/config/settings.py#L1-L80)
  - Django entrypoints: [backend/manage.py](backend/manage.py)
  - LangChain agent/tool examples: [backend/core/llm/langchain/AIAgent.py](backend/core/llm/langchain/AIAgent.py#L1-L120)
  - Docker compose: [docker-compose.yml](docker-compose.yml#L1-L60)
  - Frontend package/development: [frontend/package.json](frontend/package.json#L1-L60)

- **Project conventions & patterns (concrete):**
  - Django apps are domain-oriented (content, workflows, agent, chat, document). Add new API endpoints inside the app folder and wire them in `config/urls.py`.
  - LangChain tools are implemented under `backend/core/llm/langchain/tools`. Tools expose a `langchain_tool()` helper and are invoked with `.func(query)` in `AIAgent.py` (see pattern in `AIAgent.handle_query`).
  - Autonomous workflows live under `workflows` and use LangGraph. Look for orchestration code in `workflows/utils`.
  - Vector DB files are stored outside git. Dev uses `my_index` or `backend/chromadb` (see README and `docker-compose.yml` volumes).
  - Realtime progress uses Channels + Pusher; channel layers use InMemoryChannelLayer in dev (see `ASGI_APPLICATION` and `CHANNEL_LAYERS` in settings).

- **Integration points & external dependencies to be careful with:**
  - OpenAI / LLMs: uses `OPENAI_API_KEY` and ChatOpenAI via langchain-community.
  - Tavily Search API and other external scrapers — check credentials and rate limits before running reindex/scrape endpoints.
  - ChromaDB vector store files are large and not in repo; reindex endpoints will initialize them.

- **Common dev tasks & examples:**
  - Rebuild vector index: POST `/api/content/index/` (see README).
  - Scrape new content: POST `/api/content/scrape/`.
  - Run tests: from `backend` run `python manage.py test`.

- **When changing or adding LLM tools:**
  1. Implement the tool in `backend/core/llm/langchain/tools` following existing tool classes.
  2. Provide a `langchain_tool()` that returns the LangChain Tool object.
  3. Register the tool in `AIAgent.__init__` (or wire it into workflow orchestrators).
  4. Add unit tests in the corresponding app `tests.py` that mock external APIs.

- **Safety & debugging tips:**
  - To debug LLM behavior, enable `DEBUG=True` in `.env` and run the agent locally; `AIAgent` sets `verbose=True` on initialization.
  - Mock networked LLM calls in tests (don’t use live API keys in CI).

- **Useful links / entry points:**
  - Architecture & models: [README.md](README.md#backend-architecture)
  - Example agent: [backend/core/llm/langchain/AIAgent.py](backend/core/llm/langchain/AIAgent.py#L1-L120)
  - Docker compose: [docker-compose.yml](docker-compose.yml)

If any of these areas need more detail (example workflows, tool template, or testing snippets), tell me which part to expand. Thanks — I can iterate on this file.
