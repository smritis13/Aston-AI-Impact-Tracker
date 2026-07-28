# Aston AI Research Tool

A full-stack application with Django REST Framework backend and React TypeScript frontend, featuring semantic search capabilities using ChromaDB.

## Tech Stack

### Backend
- Django 4.2
- Django REST Framework
- ChromaDB (Vector Database)
- Python 3.9
- MySQL
- LangChain & LangGraph for AI workflows
- OpenAI GPT models

### Frontend
- React 18
- TypeScript
- React Bootstrap
- React Query (useQuery)
- React Hook Form


## Prerequisites

- Python 3.9+
- Node.js 18+
- MySQL
- Docker and Docker Compose (optional, for containerized setup)
- API Keys:
  - OpenAI API Key
  - Tavily API Key
  - Pusher credentials (App ID, Key, Secret, Cluster)

## Local Development Setup

### Backend Setup

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the backend directory with the following variables:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
DEBUG=True
SECRET_KEY=your_secret_key

# Pusher Configuration
PUSHER_APP_ID=your_app_id
PUSHER_KEY=your_key
PUSHER_SECRET=your_secret
PUSHER_CLUSTER=your_cluster

# Tavily Search Configuration
TAVILY_API_KEY=your_tavily_api_key
```

4. Run database migrations:
```bash
python manage.py migrate
```

5. Create a directory for ChromaDB:
```bash
mkdir -p backend/chromadb
```

6. Start the backend server:
```bash
python manage.py runserver
```

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

## Docker Setup

### Using Docker Compose

1. Build and start the containers:
```bash
docker-compose up --build
```

### Manual Docker Setup

#### Backend Container
```bash
cd backend
docker build -t backend .
docker run -p 8000:8000 backend
```

#### Frontend Container
```bash
cd frontend
docker build -t frontend .
docker run -p 3001:3001 frontend
```

## API Endpoints

The backend provides several REST API endpoints:

- `POST /api/content/index/` - Reindex content
- `POST /api/content/scrape/` - Scrape new content

## Frontend Routes

The frontend routes are defined in the main routes file and include:
- Home page
- Content pages
- Search functionality

## Development Notes

### Vector Database (ChromaDB)
- The ChromaDB files are not tracked in Git due to size limitations
- The database will be automatically initialized when you:
  - Run the reindex endpoint (`POST /api/content/index/`)
  - Or scrape new content (`POST /api/content/scrape/`)
- If you need to share the vector database, you'll need to transfer it separately
- You can always rebuild the index using the reindex endpoint

### Frontend Development
- Uses React Query for data fetching
- Implements React Hook Form for form handling
- Bootstrap for styling and responsive design


## Backend Architecture

### Database Schema

The application uses a comprehensive database schema designed to support content management, use case extraction, and AI-powered research workflows. The main models are defined in `backend/content/models.py`.

#### Content Management Models

**ContentSource**
- Manages automated content scraping sources with configurable intervals
- Fields: `title`, `category`, `scrape_interval_value`, `scrape_interval_unit`, `is_active`, `last_scraped`, `next_scheduled`
- Supports scheduling with units: days, hours, minutes
- Tracks scraping history and scheduling

**ContentSourceURL**
- Links URLs to content sources for batch processing
- Many-to-one relationship with ContentSource
- Enables organized URL management per source

**ContentSourceScrapeLog**
- Audit trail for scraping operations
- Tracks: `scraped_at`, `status`, `items_scraped`, `error_message`
- Provides monitoring and debugging capabilities

**Content**
- Core content storage model
- Fields: `url`, `category`, `title`, `original_content`, `content`, `summary`, `tags`, `scraped_at`, `image`
- Stores both original and processed content
- Supports JSON tags for flexible categorization

**UrlToScrape**
- Queue management for URL processing
- Status tracking: pending, processing, completed, failed
- Links to Content model when processing completes
- Error message storage for failed scrapes

#### Use Case and Research Models

**UseCaseTheme**
- Organizes use cases by thematic categories
- Fields: `title`, `description`, `featured`, `created_at`
- Supports featured themes for priority display

**Report**
- Central model for AI-generated research reports
- Fields: `topic`, `query`, `generated_report`, `type`, `thoughts`, `metadata`
- Stores LLM reasoning process in `thoughts` JSON field
- Links to prompts and themes for context

**UseCase** (Primary Use Case Model)
- Comprehensive use case storage with quality assessment
- Core fields: `use_case_name`, `use_case_type`, `company`, `industry`, `tools`, `use_case_description`
- Performance tracking: `performance_improvement_category`, `performance_impact`
- Geographic data: `geography`, `country`
- Quality assessment: `credibility_score`, `relevance_score`, `is_credible`, `is_relevant`
- Reasoning fields: `credibility_reasoning`, `relevance_reasoning`
- Metadata: `use_case_date`, `source`, `created_at`



Initially, these models were developed to facilitate the creation of diverse research entities tailored to specific use cases. Ultimately, they were consolidated into the comprehensive UseCase model.

<!-- Removed deprecated specialized use case models; the system now uses the unified `UseCase` model for all research impact entries. -->

#### Research and Processing Models

**ScrapedURL**
- Temporary storage for scraped content during processing
- Fields: `url`, `title`, `content`, `scraped_at`
- Links to Report for research context
- Supports content processing pipeline

**Prompt**
- Template management for AI prompts
- Fields: `title`, `content`, `json_structure`
- Enables reusable prompt templates with structured output

**WebsiteEvaluation**
- Domain credibility and quality assessment
- Comprehensive scoring system (0-10 total score)
- Component scores: `domain_authority_score`, `security_score`, `recency_score`, `content_quality_score`
- Quality metrics: `transparency`, `bias_risk`, `peer_review`, `updated`
- Automatic score calculation via `update_scores()` method
- Supports URL validation and ranking

#### Database Relationships

**Key Relationships:**
- `ContentSource` → `ContentSourceURL` (one-to-many)
- `ContentSource` → `ContentSourceScrapeLog` (one-to-many)
- `Report` → `UseCase` (one-to-many)
- `Report` → `ExtractedUseCase` (one-to-many)
- `Report` → `ExtractedSDLCUseCase` (one-to-many)
- `Report` → `ExtractedAISDLCUseCase` (one-to-many)
- `Report` → `ScrapedURL` (one-to-many)
- `UseCaseTheme` → `UseCase` (one-to-many)
- `UseCaseTheme` → `Report` (one-to-many)
- `Prompt` → `Report` (one-to-many)
- `Category` → `Content` (one-to-many)
- `Category` → `ContentSource` (one-to-many)

#### Database Features

**Quality Assessment System:**
- Automated credibility scoring (0-10 scale)
- Relevance assessment for user requirements
- Detailed reasoning storage for transparency
- Domain authority evaluation for source reliability

**Content Processing Pipeline:**
- Multi-stage content processing (scrape → extract → analyze)
- Status tracking throughout the pipeline
- Error handling and retry mechanisms
- Audit trails for compliance and debugging

**Flexible Categorization:**
- JSON-based tagging system
- Hierarchical category structure
- Thematic organization via UseCaseTheme
- Industry and geographic classification

**Performance Optimization:**
- Indexed ordering on key fields
- Efficient foreign key relationships
- JSON field usage for flexible data storage
- Timestamp tracking for temporal analysis

### Agentic Workflow System (StructuredReportGenerator)

The backend features a sophisticated agentic workflow built with LangGraph that autonomously orchestrates intelligent use case extraction from web content. The system implements a single autonomous workflow that can interpret user goals, plan its own execution strategy, and coordinate multiple specialized tools and processes without human intervention.

#### Agentic Workflow Architecture

The system operates as a single autonomous agent that owns the control flow and makes decisions about:

**Goal Decomposition & Planning**
- Analyzes user prompts and autonomously generates strategic research plans
- Creates use case type categories using LLM reasoning (e.g., for SDLC: Requirements Engineering, Design, Development, Testing, Deployment, Maintenance & Operations)
- Decides on company-specific search strategies and query variations
- Determines the optimal number and scope of parallel tasks

**Task Orchestration & Execution**
- Coordinates multiple specialized tools and processes
- Manages the three-stage pipeline (Search → Scrape → Extract) across parallel tasks
- Makes real-time decisions about content relevance and processing priorities
- Handles error recovery and retry logic without human intervention

**Intelligent Content Processing**
- Evaluates content quality and relevance using LLM reasoning
- Decides which content to extract, filter, or discard
- Performs autonomous quality assessment and validation
- Coordinates credibility and relevance scoring processes

#### Detailed Agentic Workflow Process

**Phase 1: Goal Decomposition**
```
User Input → Workflow Agent → Goal Analysis → Strategic Planning → Task Generation
```

The workflow agent autonomously:
- **Analyzes the user's intent** and determines the scope of research needed
- **Generates use case categories** using LLM reasoning to create MECE (Mutually Exclusive, Collectively Exhaustive) frameworks
- **Plans search strategies** by identifying relevant companies and creating targeted query variations
- **Decides on execution parameters** such as number of tasks, search depth, and processing priorities

**Phase 2: Task Execution**
```
Workflow Agent → Parallel Task Coordination → Tool Selection → Progress Monitoring
```

The workflow agent autonomously:
- **Orchestrates parallel processing** of multiple research tasks
- **Selects appropriate tools** for each stage (Tavily Search API, web scrapers, LLM processors)
- **Monitors progress** and makes real-time decisions about resource allocation
- **Handles failures** and implements retry strategies without human intervention

**Phase 3: Content Intelligence**

1. **LLM-Driven Content Evaluation**:
   - The workflow agent uses LLM reasoning to evaluate content relevance
   - Makes autonomous decisions about which content to process or discard
   - Identifies multiple use cases within single articles through intelligent analysis

2. **Structured Information Extraction**:
   - Uses `get_default_schema()` for consistent data extraction
   - Applies industry-specific validation rules autonomously
   - Extracts comprehensive use case information (name, type, company, industry, tools, description, performance impact, date, geography)

3. **Autonomous Quality Assessment**:
   - Performs LLM-driven validation using `_clean_llm()` to detect hallucinations
   - Conducts autonomous credibility scoring to assess source reliability
   - Executes relevance scoring to ensure alignment with user requirements
   - Makes decisions about data quality and completeness

**Phase 4: Data Management**
- Saves validated use cases to Django `UseCase` model
- Updates progress in real-time via Pusher
- Maintains comprehensive audit trail of the autonomous workflow execution

#### Decision-Making Capabilities

**Real-time Progress Management**
- Autonomous progress tracking and reporting
- Dynamic resource allocation based on task complexity
- Intelligent prioritization of high-value content sources

**Content Intelligence**
- Flexible filtering of irrelevant or low-quality content
- Intelligent duplicate detection and prevention
- Dynamic adjustment of search strategies based on results quality

**Error Recovery & Resilience**
- Error detection and recovery
- Intelligent retry strategies with exponential backoff
- Graceful degradation when external services are unavailable

**Quality Assurance**
- Validation of extracted data
- Dynamic adjustment of extraction parameters based on content quality
- Intelligent scoring and ranking of use cases

#### Advanced Autonomous Features

**Self-Optimizing Performance**
- Batch size optimization for web scraping
- Dynamic thread management for optimal resource utilization
- Intelligent caching and reuse of processed content

**Adaptive Processing**
- Autonomous adjustment of processing strategies based on content type
- Dynamic schema adaptation for different industries and themes
- Intelligent handling of edge cases and unusual content formats

**User Experience Optimization**
- Progress reporting with meaningful updates
- Intelligent status messaging that explains current activities
- Graceful interruption handling with state preservation

**Schema Validation & Compliance**
- Industry-specific validation rule application
- Dynamic performance improvement categorization
- Intelligent geographic and temporal validation

#### Performance Categories
- Cost Savings
- Revenue Growth
- Increased Resiliency
- Reduced Risk
- Increased Stability
- Faster Speed to Market
- Increased Agility

#### Industry Sectors
- Technology, IT & Software
- Financial Services
- Healthcare & Pharmaceuticals
- Energy (Oil, Gas & Renewables)
- Automotive
- Retail & E-commerce
- Telecommunications
- Construction & Real Estate
- Agriculture & Food Production
- Media & Entertainment

#### Geography Regions
- Global
- EMEA
- AMER
- APAC

### Vector Database and Document Processing

The system uses ChromaDB as a vector database for semantic search capabilities, powered by LlamaIndex and OpenAI models for document processing and vectorization.

#### Document Processing Pipeline:
1. **Document Upload**
   - Supports multiple file formats:
     - PDF documents
     - Word documents (.docx)
     - Text files (.txt)
     - Other text-based formats
   - Documents are processed and chunked for optimal indexing

2. **Vectorization**
   - Uses OpenAI's embedding models to convert text into vector representations
   - Maintains semantic relationships between documents
   - Enables similarity-based search across the document corpus

3. **Indexing**
   - LlamaIndex integration for efficient document indexing
   - Current implementation uses a universal index (`combined_index`)
   - Architecture supports multiple specialized indexes for different purposes
   - Indexes are stored in ChromaDB for persistence

#### Search Capabilities:
- Semantic search across all indexed documents
- Similarity-based document retrieval
- Context-aware search results
- Support for complex queries and filters

#### Advanced Features:
- **Workflow Creator**: Framework for creating custom document processing workflows
- **Agent Creation**: Infrastructure for building specialized document processing agents
  - Currently in early stages of development
  - Potential for future expansion and customization

#### Storage and Management:
- ChromaDB files are stored in `backend/chromadb`
- Indexes are automatically initialized during:
  - Document upload and processing
  - Manual reindexing via API endpoints
- Database can be rebuilt using the reindex endpoint

### Chatbot (LLM Agent)

The system includes an intelligent chatbot powered by LLM (Large Language Model) that can assist users with queries about use cases and related information.

#### Features:
- **Interactive Query Resolution**: Natural language interface for asking questions about use cases
- **Tool Integration**:
  - Web Search: Real-time information retrieval from the internet
  - Use Case Search: Access to the vector database for semantic search across use cases
  - Context Awareness: Maintains conversation context for coherent interactions

#### Capabilities:
- Answer questions about specific use cases
- Provide industry insights and trends
- Compare different use cases and their implementations
- Offer recommendations based on user queries
- Access and summarize information from the vector database

#### Technical Implementation:
- Built on Django REST Framework
- Integrates with the vector database for use case retrieval
- Uses OpenAI models for natural language understanding
- Implements a tool-based architecture for extensible functionality

### External Services and Scraping Capabilities

#### Real-time Updates (Pusher)
- **Implementation**: Uses Pusher for real-time communication between backend and frontend
- **Configuration**:
  - Required environment variables in `.env`:
    ```
    PUSHER_APP_ID=your_app_id
    PUSHER_KEY=your_key
    PUSHER_SECRET=your_secret
    PUSHER_CLUSTER=your_cluster
    ```
  - Frontend configuration in environment variables:
    ```
    REACT_APP_PUSHER_KEY=your_key
    REACT_APP_PUSHER_CLUSTER=your_cluster
    ```
- **Features**:
  - Real-time progress updates for long-running tasks
  - Streaming of thoughts and intermediate results
  - Use case extraction status updates
  - Chat message delivery

#### Web Search (Tavily)
- **Implementation**: Uses Tavily Search API for web content retrieval
- **Configuration**:
  - Required environment variable in `.env`:
    ```
    TAVILY_API_KEY=your_api_key
    ```
- **Features**:
  - Advanced search capabilities
  - Real-time web content retrieval
  - Integration with LLM agents for intelligent search

#### Web Scraping
The system implements multiple scraping strategies for different use cases:

1. **SimpleHtmlScraper**
   - Lightweight HTML scraping using `requests` and `BeautifulSoup`
   - Features:
     - Async operation support
     - Automatic content extraction
     - HTML cleaning and text normalization
     - Error handling and retries

2. **CrawlAIScraper**
   - Advanced scraping using headless Chromium
   - Features:
     - JavaScript rendering support
     - Anti-bot detection bypass
     - Advanced content extraction
     - Markdown conversion

3. **ContentScraperChromeDriver**
   - Selenium-based scraping with undetected-chromedriver
   - Features:
     - Full browser automation
     - Custom user agent support
     - Dynamic content handling
     - Robust error recovery

#### Scraping Features
- **Content Processing**:
  - Automatic title extraction
  - Main content identification
  - HTML cleaning and normalization
  - Markdown conversion
  - Text encoding handling

- **URL Management**:
  - Domain-specific URL filtering
  - Duplicate detection
  - URL validation and normalization
  - Custom rules for different websites

- **Error Handling**:
  - Automatic retries
  - Timeout management
  - Error logging
  - Graceful failure recovery

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add your license information here] 
