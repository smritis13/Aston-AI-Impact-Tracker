# Complete Workflow Analysis: User Input → Report Generation
## Aston AI Research Tool

---

## Table of Contents
1. [High-Level Architecture](#high-level-architecture)
2. [Step-by-Step User Journey](#step-by-step-user-journey)
3. [Frontend Component Flow](#frontend-component-flow)
4. [API Communication](#api-communication)
5. [Backend Processing Pipeline](#backend-processing-pipeline)
6. [LangGraph State Machine](#langgraph-state-machine)
7. [Database Operations](#database-operations)
8. [Real-Time Updates with Pusher](#real-time-updates-with-pusher)
9. [Report Generation & Storage](#report-generation--storage)
10. [Result Display](#result-display)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React/TypeScript)                           │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  /reports/generate Route                                                  │ │
│  │  ├─ ReportGenerationPage.tsx (Main Container)                             │ │
│  │  │   ├─ PromptManagerWidget (Load saved prompts)                          │ │
│  │  │   ├─ PDF Upload Input (Optional)                                       │ │
│  │  │   ├─ Query Input/Select                                               │ │
│  │  │   ├─ Settings Modal (complexity, outcomes, sections)                   │ │
│  │  │   └─ PusherListener (Real-time updates)                               │ │
│  │  └─ UI Components:                                                        │ │
│  │      ├─ UseCasesWidget (Display extracted use cases in real-time)        │ │
│  │      └─ Progress Bar (Streaming updates)                                 │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP POST
                                    │ /content/report-generation/
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (Django REST Framework)                          │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  ReportGenerationView (content/views.py:522)                              │ │
│  │  ├─ Parse request (query, pdf_text, settings)                            │ │
│  │  ├─ Extract PDF content (if uploaded)                                     │ │
│  │  ├─ Generate/lookup theme                                                 │ │
│  │  ├─ Create Report model instance                                          │ │
│  │  └─ Start background thread → StructuredReportGenerator                  │ │
│  │      └─ Immediately return theme to frontend (no blocking)               │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                             │
│                                    ▼ (Background Thread)                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  StructuredReportGenerator (core/llm/langchain/langgraph/)               │ │
│  │  ├─ Initialize LangGraph state machine                                    │ │
│  │  ├─ Build graph with nodes: Planning → Task Execution Loop              │ │
│  │  │   ├─ Planning Node: Generate search tasks                             │ │
│  │  │   ├─ Task Execution Loop (serial):                                    │ │
│  │  │   │   ├─ Search Node: TavilySearchResults API                        │ │
│  │  │   │   ├─ Scrape Node: SimpleHtmlScraper (async batches)             │ │
│  │  │   │   └─ Extract Node: LLM extraction + credibility checks           │ │
│  │  │   │       └─ Create UseCase DB records                               │ │
│  │  └─ Stream results via Pusher in real-time                              │ │
│  │  └─ Save final report to Report.generated_report                        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  Database Models                                                           │ │
│  │  ├─ Report: Main report record + generated HTML/Markdown                 │ │
│  │  ├─ UseCase: Individual extracted findings (created during extraction)   │ │
│  │  ├─ UseCaseTheme: Report category/theme                                  │ │
│  │  └─ Prompt: Saved search templates                                       │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │  External Services                                                         │ │
│  │  ├─ LLM: OpenAI GPT-4o (planning, extraction, synthesis, validation)    │ │
│  │  ├─ Search: TavilySearchResults (web search)                            │ │
│  │  ├─ Scraping: SimpleHtmlScraper (async HTML fetching)                   │ │
│  │  └─ Streaming: Pusher (real-time updates to frontend)                   │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Pusher Events (stream-{report_id})
                                    │ Real-time: thoughts + progress
                                    ▼
                        (Back to Frontend - See below)
```

---

## Step-by-Step User Journey

### Phase 1: USER INPUTS REPORT PARAMETERS

**Location**: `/reports/generate` → ReportGenerationPage.tsx

**User Actions**:
1. Enter or select a **search query**
   - Can type manually
   - Or select from saved prompts (PromptManagerWidget)
2. (Optional) Upload a **PDF file**
   - Client-side extraction using PDF.js
   - Full page text extracted, stored in state
3. Configure **settings**:
   - Report type: "impact_case_study" or general
   - Search complexity: simple/medium/complex/advanced
   - Number of outcomes: 5-50
   - REF case study sections (optional)
4. Click **"Generate Report"**

**State at submission**:
```typescript
{
  query: "GenAI in European banking",
  report_type: "impact_case_study",
  pdf_filename: "research_context.pdf",     // if uploaded
  pdf_text: "...[extracted page content]...", // if uploaded
  number_of_outcomes: "10",
  search_complexity: "medium"
}
```

---

### Phase 2: FRONTEND MAKES API CALL

**File**: [frontend/src/features/feature_data/services/index.tsx](frontend/src/features/feature_data/services/index.tsx#L160)

**Method**: `ContentHttpService.generateReport()`

**HTTP Request**:
```
POST /content/report-generation/ HTTP/1.1
Content-Type: application/json

{
  "query": "GenAI in European banking",
  "report_type": "impact_case_study",
  "pdf_filename": "research_context.pdf",
  "pdf_text": "...[full extracted text]...",
  "number_of_outcomes": "10",
  "search_complexity": "medium",
  "theme_id": null,
  "impact_sections": []
}
```

**Expected Response** (immediate, no waiting):
```json
{
  "id": 42,
  "title": "GenAI in European banking",
  "report_id": 128,
  "description": "...",
  "featured": false
}
```

---

### Phase 3: BACKEND PROCESSES REQUEST (SYNCHRONOUS)

**File**: [backend/content/views.py](backend/content/views.py#L522) → `ReportGenerationView.post()`

**Processing Steps**:

#### 3.1 Parse and Validate Input
```python
query = request.data.get("query", "")
pdf_text = request.data.get("pdf_text")
report_type = request.data.get("report_type", "")
```

#### 3.2 Extract PDF Content (if uploaded)
```python
# Extract from PDF using pdfplumber
# Extract from DOCX using docx2txt
# Combine with any existing pdf_text parameter
source_priority = "PDF_FIRST" if pdf_text else "WEB_FIRST"
```

#### 3.3 Handle Prompt Template (if prompt_id provided)
```python
if prompt_id:
    prompt_obj = Prompt.objects.get(id=prompt_id)
    query = prompt_obj.content  # Use prompt content
```

#### 3.4 Generate or Lookup Theme
```python
if not theme_id:
    if report_type == "impact_case_study":
        theme_name = query[:100]  # Use query as theme name
    else:
        theme_name = self.generate_theme_name(query)  # LLM call
    
    theme, created = UseCaseTheme.objects.get_or_create(
        title=theme_name,
        defaults={"description": query}
    )
```

#### 3.5 Create Report Database Record
```python
report_obj = Report.objects.create(
    theme=theme,
    query=query,
    prompt=prompt_obj,
    generated_report="",  # Will be populated later
    metadata={
        "status": "processing",
        "report_type": report_type,
        "pdf_filename": pdf_filename,
        "pdf_uploaded": bool(pdf_text),
        "source_priority": source_priority
    }
)
```

#### 3.6 Start Background Thread (NON-BLOCKING)
```python
import threading

def run_report_generation():
    generator = StructuredReportGenerator(
        user_prompt=query,
        search_query=query,
        pdf_text=pdf_text,
        pdf_filename=pdf_filename,
        report_obj=report_obj,
        theme_id=theme.id,
        number_of_outcomes=10,
        search_complexity="medium",
        report_type="impact_case_study",
        enable_credibility_check=True,
        enable_relevance_check=True
    )
    report_id, use_cases = generator.run()

thread = threading.Thread(target=run_report_generation)
thread.start()

# IMMEDIATELY return theme info to frontend
return Response(theme_serialized_data, status=200)
```

**Key Point**: The API returns immediately with theme info. The actual report generation happens in the background thread.

---

### Phase 4: FRONTEND RECEIVES IMMEDIATE RESPONSE

**Frontend Code**: [ReportGenerationPage.tsx](frontend/src/features/feature_data/pages/ReportGenerationPage.tsx#L71)

```typescript
if (response.id) {
  setCurrentTheme({
    id: response.id,
    title: response.title
  });
  setReportId(response.report_id);  // Will use for Pusher subscription
  setIsGenerating(true);
  // UI shows: "Generating report..."
}
```

**UI State**:
- Show loading spinner
- Show progress bar (0%)
- Show live use cases list (will populate as results arrive)
- Activate Pusher listener

---

### Phase 5: BACKGROUND THREAD EXECUTES LANGGRAPH

**File**: [backend/core/llm/langchain/langgraph/structured_report_generator.py](backend/core/llm/langchain/langgraph/structured_report_generator.py#L1426)

#### 5.1 LangGraph State Machine Architecture

**State Definition**:
```python
GraphState = {
    "tasks": List[Dict],              # Search/scrape/extract tasks
    "current_task_index": int,        # Which task running now
    "search_results": Dict,           # Results from Tavily API
    "scraped_pages": List[Dict],      # HTML content fetched
    "page_contents": Dict,            # {url: full_text}
    "use_cases": List[ExtractedUseCase], # Extracted findings
    "thoughts": List[str],            # Processing notes
    "use_case_types": List[str],      # Available use case categories
    "pdf_uploaded": bool,
    "pdf_text": str,
    "pdf_filename": str
}
```

**Graph Structure**:
```
Entry Point: PLANNING NODE
    ↓
    ├─ If PDF uploaded: Create 1 task "Extract from PDF"
    └─ If Web search: LLM generates N tasks with queries
    
    ↓
    
TASK EXECUTION LOOP (serial, one task at a time)
    │
    ├─ SEARCH NODE
    │   ├─ For each query in task
    │   │   ├─ Call TavilySearchResults API
    │   │   ├─ Get results: {title, link, snippet}
    │   │   └─ Stream progress via Pusher
    │   └─ Accumulate all search results
    │
    ├─ SCRAPE NODE
    │   ├─ Extract unique URLs from search results
    │   ├─ Batch URLs (5 per batch)
    │   ├─ For each batch (parallel asyncio):
    │   │   ├─ Fetch HTML from each URL
    │   │   ├─ Extract title and page text
    │   │   └─ Stream progress via Pusher
    │   └─ Accumulate page_contents
    │
    └─ EXTRACT NODE
        ├─ If PDF mode: Extract from PDF text only
        ├─ If Web mode: For each scraped page:
        │   │   ├─ LLM extraction (REF_EXTRACTION_PROMPT)
        │   │   ├─ Parse JSON response
        │   │   ├─ Create UseCase DB record
        │   │   ├─ Stream via Pusher
        │   │   ├─ Run credibility & relevance checks (parallel threads)
        │   │   └─ Save scores to UseCase record
        │   └─ Stop if max_use_cases reached
        └─ Return extracted use_cases

Exit: All tasks complete → Save final report HTML
```

---

#### 5.2 PLANNING NODE in Detail

**Function**: `_planning_node()`

**Input**: Empty GraphState

**Process**:

1. **If PDF Uploaded**:
   - Create single task: "Extract quantitative PDF impacts"
   - No web search needed
   - Skip to EXTRACT

2. **If Web Search**:
   - Call LLM with `REF_PLANNING_PROMPT`
   - Input:
     ```
     User Prompt: {user_prompt}
     Max Tasks: {max_tasks_based_on_complexity}
     Today: {date}
     Theme: {theme_title}
     ```
   - LLM returns JSON:
     ```json
     {
       "tasks": [
         {
           "task_name": "Search for commercial AI implementations in banking",
           "search_queries": [
             "AI in European banking loan origination",
             "GenAI risk assessment financial institutions",
             "..."
           ]
         },
         { "task_name": "...", "search_queries": [...] }
       ]
     }
     ```
   - Add UUID to each task

**Output**: GraphState with tasks array populated

**Streaming**: Progress "Planning: 1/1 - completed" → Pusher

---

#### 5.3 SEARCH NODE in Detail

**Function**: `_search_node()`

**Input**: GraphState with populated tasks

**Process for each task**:

1. **Get current task** from index
2. **For each search query** in task.search_queries:
   - Call `TavilySearchResults.run(query)`
   - Returns list of results:
     ```python
     [
       {"title": "...", "url": "...", "content": "..."},
       {"title": "...", "url": "...", "content": "..."},
       ...
     ]
     ```
   - **Skip already processed URLs** (if theme exists and skip_processed_urls=True):
     ```python
     processed_urls = UseCase.objects.filter(
         theme_id=theme_id
     ).values_list('source', flat=True)
     ```
   - Rank results by relevance
   - Keep top N results (max_results based on complexity)
   - Add to results dict

**Complexity Mapping** (example):
```
Complexity    Search Depth   Max Results Per Query   Max Links to Scrape
─────────────────────────────────────────────────────────────────────
simple        basic          3                       100
medium        advanced       8                       300
complex       advanced       12                      600
advanced      advanced       15                      1000
```

**Optimization**: If max_use_cases already reached, skip remaining queries

**Output**: `search_results = {query: [results]}`

**Streaming**: Progress per query → Pusher: "Query 2/5: 'GenAI banking impact'"

---

#### 5.4 SCRAPE NODE in Detail

**Function**: `_scrape_node()`

**Input**: search_results dict from SEARCH node

**Process**:

1. **Collect unique URLs**:
   ```python
   urls = []
   for docs in search_results.values():
       for doc in docs[:max_results]:
           if doc["link"] not in processed_urls:
               urls.append(doc["link"])
   ```

2. **Batch URLs** (batch_size=5):
   - For each batch, create async tasks

3. **For each URL**, run async scraper:
   ```python
   async def scrape_url(url):
       # Fetch HTML
       # Parse with BeautifulSoup/similar
       # Extract title and text content
       # Return (url, title, text)
   ```

4. **Create event loop and run batch**:
   ```python
   loop = asyncio.new_event_loop()
   batch_results = loop.run_until_complete(
       asyncio.gather(*batch_tasks)
   )
   ```

5. **Process results**:
   - Add to `page_contents` dict
   - Update `scraped_pages` list

**Output**: `scraped_pages = [{"url": "...", "title": "...", "text": "..."}]`

**Streaming**: Progress per URL → Pusher: "URL 3/42: https://example.com/article"

---

#### 5.5 EXTRACT NODE in Detail

**Function**: `_extract_node()`

**Input**: scraped_pages from SCRAPE node

**Process for PDF-only mode** (if pdf_text provided):

1. Skip all web sources
2. Call LLM with `PDF_QUANTITATIVE_EXTRACTION_PROMPT`:
   ```
   Article: {pdf_text_first_200k_chars}
   User Prompt: {user_prompt}
   Schema: {json_schema}
   Theme: {theme_title}
   Max Use Cases: {max_use_cases}
   ```
3. LLM returns JSON matching schema
4. For each extracted item:
   - Set `source = pdf_filename`
   - Set `source_type = "PDF"`
   - Create UseCase DB record
   - Stream via Pusher

**Process for Web mode** (default):

**For each scraped page** (up to max_links):

1. **Prepare text**:
   ```python
   cleaned_text = clean_text_for_db(page["text"])  # Remove noise
   ```

2. **Extract use cases via LLM**:
   ```python
   prompt = REF_EXTRACTION_PROMPT.format(
       article=cleaned_text,
       user_prompt=user_prompt,
       schema=json.dumps(schema),
       theme_title=theme_title,
       use_case_type_options=json.dumps(use_case_types),
       today=datetime.now().strftime("%Y-%m-%d")
   )
   ```

3. **LLM Response** (JSON array of matches):
   ```json
   [
     {
       "use_case_name": "GenAI Loan Origination at BankX",
       "company": "BankX",
       "use_case_type": "Loan Origination Automation",
       "industry": "Banking",
       "performance_impact": "30% reduction in processing time",
       "use_case_date": "2024",
       "use_case_description": "...",
       "tools": "GPT-4, LangChain",
       "geography": "Europe",
       "country": "UK",
       ...
     },
     { ... more use cases ... }
   ]
   ```

4. **For each extracted use case**:

   a. **Create database record**:
      ```python
      db_use_case = UseCase.objects.create(
          report=report_obj,
          theme_id=theme_id,
          use_case_name=data["use_case_name"],
          company=data["company"],
          ...all fields...
          source=page["url"],
          source_type="Web",
          source_reference=page["url"]
      )
      uc.id = db_use_case.id
      ```

   b. **Run Credibility & Relevance Checks** (parallel threads):
      
      **Thread 1 - Credibility Check**:
      ```python
      prompt = CREDIBILITY_CHECK_PROMPT.format(
          article=page_text,
          use_case=json.dumps(use_case_dict)
      )
      # LLM Response:
      {
          "credibility_score": 0.75,  # 0-1
          "is_credible": true,
          "reasoning": "Source is peer-reviewed..."
      }
      ```
      
      **Thread 2 - Relevance Check**:
      ```python
      prompt = REF_RELEVANCE_CHECK_PROMPT.format(
          user_prompt=user_prompt,
          use_case=json.dumps(use_case_dict),
          theme_title=theme_title
      )
      # LLM Response:
      {
          "relevance_score": 0.85,  # 0-1
          "is_relevant": true,
          "reasoning": "Directly addresses GenAI banking impact..."
      }
      ```
      
      Both threads run in parallel, join before continuing.

   c. **Save scores to database**:
      ```python
      UseCase.objects.filter(id=db_use_case.id).update(
          credibility_score=credibility_score,
          is_credible=is_credible,
          credibility_reasoning=credibility_reasoning,
          relevance_score=relevance_score,
          is_relevant=is_relevant,
          relevance_reasoning=relevance_reasoning
      )
      ```

   d. **Check relevance gate**:
      ```python
      if not _passes_relevance_gate(use_case):  # relevance_score < threshold
          UseCase.objects.filter(id=db_use_case.id).delete()
          continue
      ```

   e. **Stream to frontend**:
      ```python
      self._stream(f'<usecase>{json.dumps(uc.to_dict())}</usecase>')
      ```

   f. **Increment counter**:
      ```python
      self.total_use_cases_created += 1
      if self.total_use_cases_created >= self.max_use_cases:
          return state  # Stop extraction
      ```

**Output**: use_cases list populated with all extracted findings

**Streaming**: Each use case as JSON wrapped in `<usecase>` tags

---

### Phase 6: REAL-TIME STREAMING VIA PUSHER

**Backend Streaming Function**: `_stream(message, progress)`

**Pusher Trigger**:
```python
self.pusher_service.trigger(
    channel=f"stream-{report_id}",
    event="stream_thought",
    data={
        "thought": message,
        "progress": progress_percentage
    }
)
```

**Frontend Listening**: [PusherListener.tsx](frontend/src/features/feature_chat/components/PusherListener.tsx#L18)

```typescript
const channel = pusher.subscribe(`stream-${report_id}`);

channel.bind('stream_thought', (data) => {
  const thought = data.thought;
  const progress = data.progress;
  
  // Check for use case JSON wrapped in <usecase> tags
  const useCaseMatch = thought.match(/<usecase>(.*?)<\/usecase>/)?.[1];
  
  if (useCaseMatch) {
    const useCase = JSON.parse(useCaseMatch);
    onUseCaseReceived(useCase);  // Add to list in real-time
  }
  
  onProgress(progress);  // Update progress bar
});
```

**Frontend Handler** in ReportGenerationPage:
```typescript
const handleUseCaseReceived = (useCase: any) => {
  setUseCases(prev => [...prev, useCase]);  // Real-time list update
};

const handleProgress = (progress: number) => {
  setProgress(progress);  // Update progress bar
};
```

---

### Phase 7: REPORT GENERATION & STORAGE

**Trigger**: After graph completes (run() method completes)

**Function**: `_save_generated_report()`

**Process**:

1. **Determine report format**:
   ```python
   if report_type == "impact_case_study":
       html = self._build_impact_case_study_markdown(use_cases)
   else:
       html = self._build_generated_report_html(use_cases)
   ```

2. **Build Impact Case Study Markdown** (for REF reports):

   ```markdown
   # GenAI in European Banking
   
   ## Executive Summary
   This report extracts and analyzes 10 impact finding(s), 
   with 8 marked as credible...
   
   ## Underpinning Research
   [First 3 use cases summarized]
   
   ## References to the Research
   - [europe.example.com/study1](https://...)
   - [research.org/paper2](https://...)
   
   ## Details of the Impact
   ### Impact Finding 1
   **Title:** GenAI Loan Origination at BankX
   **Organization:** BankX
   **Impact Type:** Process Automation
   **Sector:** Financial Services
   **Quantitative Outcome:** 30% reduction in processing time
   **Timeframe:** 2023-2024
   **Evidence:** Verified through case study documentation...
   
   [More findings...]
   
   ## Sources to Corroborate the Impact
   [All sources with credibility notes]
   
   ## References
   [HTML table with all links]
   ```

3. **Build HTML Table Report** (for general reports):
   ```html
   <h3>GenAI in European Banking</h3>
   <div class="alert alert-info">
     <strong>REF evidence summary:</strong> 10 impact finding(s) extracted; 
     8 marked credible...
   </div>
   
   <h4>Extracted impact evidence</h4>
   <table class="table table-striped">
     <thead>
       <tr>
         <th>Title / Product name</th>
         <th>Organisation</th>
         <th>Impact type</th>
         <th>Sector</th>
         <th>Quantitative outcome</th>
         <th>Dates</th>
         <th>Source URL</th>
         <th>Verified?</th>
         <th>Notes</th>
       </tr>
     </thead>
     <tbody>
       <tr>
         <td>GenAI Loan Origination</td>
         <td>BankX</td>
         <td>Process Automation</td>
         <td>Financial Services</td>
         <td>30% processing time reduction</td>
         <td>2023-2024</td>
         <td><a href="..." target="_blank">source.com/case1</a></td>
         <td>Yes</td>
         <td>Verified through documentation</td>
       </tr>
       [More rows...]
     </tbody>
   </table>
   
   <h4>References</h4>
   <table class="table">
     <thead>
       <tr>
         <th>#</th>
         <th>Link</th>
         <th>Title</th>
         <th>Evidence Quality</th>
       </tr>
     </thead>
     <tbody>
       <tr>
         <td>1</td>
         <td><a href="..." target="_blank">europe.example.com/study</a></td>
         <td>GenAI Loan Origination</td>
         <td>Credible</td>
       </tr>
     </tbody>
   </table>
   ```

4. **Save to database**:
   ```python
   Report.objects.filter(id=report_obj.id).update(
       generated_report=html_content,
       updated_at=now()
   )
   report_obj.metadata["status"] = "COMPLETED"
   report_obj.save()
   ```

5. **Send final Pusher event**:
   ```python
   self._stream("Search completed successfully!", 100)
   ```

---

### Phase 8: FRONTEND RECEIVES COMPLETION

**Pusher Event**: stream_thought with message "Search completed successfully!" and progress=100

**Frontend Handler**:
```typescript
// From PusherListener
channel.bind('stream_thought', (data) => {
  if (data.thought.includes("completed successfully")) {
    onComplete('success');
  }
});

// In ReportGenerationPage
const handleComplete = (status: 'success' | 'stopped' | 'error') => {
  setIsGenerating(false);
  setProgress(100);
  // Now fetch the final report
  loadFinalReport();
};

const loadFinalReport = async () => {
  const report = await ContentHttpService.loadReport(reportId);
  // report.generated_report contains the HTML/Markdown
  displayReport(report);
};
```

---

### Phase 9: RESULT DISPLAY

**Components Involved**:

1. **UseCasesWidget**: 
   - Displays real-time use cases as they arrive
   - Shows credibility/relevance scores
   - Expandable details

2. **Final Report Display**:
   ```typescript
   <div dangerouslySetInnerHTML={{ 
     __html: report.generated_report 
   }} />
   ```

3. **Report Actions**:
   - Export to PDF: [ReportPdfExportView](backend/content/views.py#L349)
   - Save to database: Already done
   - Copy/Share: Frontend utilities

---

## Frontend Component Flow

```
ReportGenerationPage.tsx (Main Container)
│
├─ State:
│  ├─ formData: { query, report_type, ... }
│  ├─ isGenerating: boolean
│  ├─ reportId: number | null
│  ├─ currentTheme: { id, title }
│  ├─ useCases: UseCase[]
│  ├─ progress: 0-100
│  └─ pdfFileName: string | null
│
├─ Lifecycle:
│  └─ handleSubmit()
│     └─ ContentHttpService.generateReport(formData)
│        └─ Response: { id, report_id, title }
│           ├─ setCurrentTheme()
│           ├─ setReportId()
│           ├─ setIsGenerating(true)
│           └─ Activate PusherListener
│
├─ Child Components:
│  ├─ PromptManagerWidget
│  │  └─ Loads/saves/selects prompt templates
│  │
│  ├─ PDF Upload Input
│  │  └─ File input → extractTextFromPdf() → setPdfExtractedText()
│  │
│  ├─ PusherListener
│  │  ├─ onThoughtReceived: (thought) => handleThoughtReceived()
│  │  ├─ onUseCaseReceived: (useCase) => handleUseCaseReceived()
│  │  ├─ onProgress: (progress) => setProgress()
│  │  └─ onComplete: (status) => handleComplete()
│  │
│  ├─ Progress Bar
│  │  └─ Displays current progress percentage
│  │
│  └─ UseCasesWidget
│     └─ Lists extracted use cases in real-time
│        └─ Each item expandable to UseCaseDetails
│
└─ After Completion:
   └─ Poll /content/reports/{reportId}/
      └─ Display final Report HTML/Markdown
```

---

## API Communication

### 1. Generate Report
```
POST /content/report-generation/
Content-Type: application/json

Request:
{
  "query": "string",
  "report_type": "impact_case_study" | "",
  "prompt_id": number | null,
  "theme_id": number | null,
  "theme_is_featured": boolean,
  "pdf_filename": string (optional),
  "pdf_text": string (optional),
  "number_of_outcomes": "5" | "10" | "20" (string),
  "search_complexity": "simple" | "medium" | "complex" | "advanced",
  "impact_sections": [],
  "include_summary": boolean
}

Response (200/201):
{
  "id": 42,                    // Theme ID
  "title": "GenAI in banking",
  "report_id": 128,            // Report ID for polling
  "description": "...",
  "featured": false
}
```

### 2. Fetch Report
```
GET /content/reports/{id}/

Response (200):
{
  "id": 128,
  "theme": 42,
  "query": "GenAI in banking",
  "prompt": null,
  "generated_report": "<h3>GenAI...</h3>...",  // HTML content
  "thoughts": ["planned", "..."],
  "metadata": {
    "status": "COMPLETED",
    "report_type": "impact_case_study",
    "pdf_uploaded": false
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:45:30Z"
}
```

### 3. Stop Report Generation
```
POST /content/reports/{theme_id}/stop/

Response (200):
{
  "status": "stopped",
  "message": "Report generation stopped"
}
```

### 4. Export to PDF
```
GET /content/reports/{id}/export-pdf/

Response (200):
Content-Type: application/pdf
[Binary PDF file]
```

---

## Backend Processing Pipeline

### LLM Prompts Used

#### REF_PLANNING_PROMPT
- **Input**: user_prompt, max_tasks, theme_title, today
- **Output**: JSON with array of tasks and search_queries
- **Purpose**: Break down user request into parallel search tasks

#### REF_EXTRACTION_PROMPT
- **Input**: article (page text), user_prompt, schema, theme_title, use_case_type_options, date
- **Output**: JSON array of extracted use cases matching schema
- **Purpose**: Extract structured impact findings from web page

#### PDF_QUANTITATIVE_EXTRACTION_PROMPT
- **Input**: article (PDF text), user_prompt, schema, theme_title, max_use_cases
- **Output**: JSON array of extracted use cases from PDF
- **Purpose**: Extract findings from uploaded PDF document

#### CREDIBILITY_CHECK_PROMPT
- **Input**: article, use_case JSON
- **Output**: { credibility_score, is_credible, reasoning }
- **Purpose**: Assess source credibility for extracted finding

#### REF_RELEVANCE_CHECK_PROMPT
- **Input**: user_prompt, use_case JSON, theme_title
- **Output**: { relevance_score, is_relevant, reasoning }
- **Purpose**: Assess relevance of finding to original query

#### REF_CASE_STUDY_SYNTHESIS_PROMPT
- **Input**: user_prompt, theme_title, impact_sections, impact_evidence
- **Output**: Formatted REF 2029-compliant markdown
- **Purpose**: Synthesize findings into structured report format

---

## LangGraph State Machine

### Nodes & Edges

```
PLANNING NODE
├─ Input: Empty GraphState
├─ Process:
│  ├─ If PDF uploaded: Create 1 PDF extraction task
│  └─ If web: LLM generates N search tasks
├─ Output: tasks[], current_task_index=0
└─ Stream: "Planning: 1/1 - completed"

         │
         ▼

TASK EXECUTION LOOP (Conditional Edge)
│ while current_task_index < len(tasks):
│
├─ SUB-GRAPH: SEARCH → SCRAPE → EXTRACT
│
│  SEARCH NODE
│  ├─ For each query in current task
│  ├─ Call TavilySearchResults
│  └─ Stream: "Query 2/5: 'term'"
│
│  SCRAPE NODE
│  ├─ Batch fetch URLs async
│  └─ Stream: "URL 3/42: https://..."
│
│  EXTRACT NODE
│  ├─ For each page
│  ├─ LLM extract → Create DB → Run checks
│  └─ Stream: "<usecase>{json}</usecase>"
│
│  current_task_index++
│
└─ Conditional Edge:
   if current_task_index < len(tasks):
       → TASK EXECUTION (loop again)
   else:
       → END

EXIT
├─ Filter use cases by relevance
├─ Save final report HTML to Report.generated_report
└─ Stream: "Search completed successfully!"
```

### Use Case Filtering

After all tasks complete:

```python
filtered_use_cases = _apply_relevance_filtering(use_cases)

# Fetch from DB with relevance_score >= threshold * 10
# Threshold based on complexity:
#   - simple: 0.85
#   - medium: 0.70
#   - complex: 0.60
#   - advanced: 0.50
```

---

## Database Operations

### Models

```python
# Report Model
class Report(models.Model):
    theme = ForeignKey('UseCaseTheme')
    query = CharField(max_length=1000)
    prompt = ForeignKey('Prompt', null=True, blank=True)
    generated_report = TextField()  # HTML or Markdown
    thoughts = JSONField(default=list)
    metadata = JSONField(default=dict)
    # {
    #   "status": "processing|completed|failed|stopped",
    #   "report_type": "impact_case_study",
    #   "pdf_uploaded": true/false,
    #   "pdf_filename": "...",
    #   "source_priority": "PDF_FIRST|WEB_FIRST",
    #   "progress": {"current": 0, "total": 10},
    #   "started_at": "2024-01-15T10:30:00Z",
    #   "error": "..."
    # }
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

# UseCase Model (created during extraction)
class UseCase(models.Model):
    report = ForeignKey('Report')
    theme = ForeignKey('UseCaseTheme')
    
    # Impact details
    use_case_name = CharField()
    company = CharField()
    use_case_type = CharField()  # "Loan Origination", "Risk Assessment"
    use_case_description = TextField()
    industry = CharField()  # "Banking", "Healthcare"
    performance_impact = TextField()  # "30% reduction in time"
    performance_improvement_category = CharField()
    
    # Temporal & geographic
    use_case_date = CharField()
    geography = CharField()
    country = CharField()
    
    # Technical
    tools = CharField()  # "GPT-4, LangChain"
    
    # Source info
    source = URLField()
    source_type = CharField()  # "Web" or "PDF"
    source_reference = CharField()
    
    # Quality scoring
    credibility_score = FloatField(null=True)
    is_credible = BooleanField(null=True)
    credibility_reasoning = TextField()
    
    relevance_score = FloatField(null=True)
    is_relevant = BooleanField(null=True)
    relevance_reasoning = TextField()
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

# UseCaseTheme Model
class UseCaseTheme(models.Model):
    title = CharField()
    description = TextField()
    featured = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

# Prompt Model
class Prompt(models.Model):
    content = TextField()
    title = CharField(max_length=200)
    created_at = DateTimeField(auto_now_add=True)
```

### Database Operations During Flow

1. **Theme Lookup/Creation**:
   ```python
   UseCaseTheme.objects.get_or_create(
       title=theme_name,
       defaults={"description": query}
   )
   ```

2. **Report Creation**:
   ```python
   Report.objects.create(
       theme=theme,
       query=query,
       generated_report="",
       metadata={"status": "processing"}
   )
   ```

3. **Use Case Creation** (during extraction):
   ```python
   UseCase.objects.create(
       report=report_obj,
       theme_id=theme_id,
       use_case_name=data["use_case_name"],
       company=data["company"],
       ...all fields...
   )
   ```

4. **Score Updates** (after credibility/relevance checks):
   ```python
   UseCase.objects.filter(id=use_case_id).update(
       credibility_score=score,
       is_credible=is_credible,
       relevance_score=score,
       is_relevant=is_relevant
   )
   ```

5. **Report Finalization**:
   ```python
   Report.objects.filter(id=report_id).update(
       generated_report=html_content,
       updated_at=now()
   )
   ```

---

## Real-Time Updates with Pusher

### Architecture

```
Backend (StructuredReportGenerator)
├─ self.pusher_service = PusherService()
└─ Call: self._stream(message, progress)
    └─ pusher_service.trigger(
        channel=f"stream-{report_id}",
        event="stream_thought",
        data={"thought": message, "progress": progress}
      )

                   ↕ Pusher API (WebSocket)

Frontend (PusherListener.tsx)
├─ pusher.subscribe(`stream-${report_id}`)
└─ channel.bind('stream_thought', (data) => {
    // Parse use cases from <usecase> tags
    // Update progress
    // Trigger callbacks
})
```

### Message Types

**1. Planning**:
```
"Planning: 1/1 - generating use case types"
"Planning: 1/1 - completed"
```

**2. Task Progress**:
```
"Task: Search for commercial AI implementations in banking (1/3) - starting"
"Query 2/5: 'GenAI loan origination European banks'"
```

**3. URL Processing**:
```
"URL 3/42: https://example.com/case-study - scraping"
"URL 3/42: https://example.com/case-study - extracting"
```

**4. Use Cases**:
```
<usecase>{
  "use_case_name": "GenAI Loan Origination at BankX",
  "company": "BankX",
  "industry": "Banking",
  ...
}</usecase>
```

**5. Completion**:
```
"✓ PDF extraction complete. Found 10 finding(s) from document."
"Search completed successfully!"
```

### Progress Calculation

```python
def calculate_progress(task_num, total_tasks):
    planning = 5
    per_task = 90 // total_tasks
    url_extraction = 5
    
    return planning + (task_num * per_task) + url_extraction
```

---

## Report Generation & Storage

### Format Decision

```python
if report_type == "impact_case_study":
    # Generate REF 2029-compliant markdown
    report_html = _build_impact_case_study_markdown(use_cases)
else:
    # Generate table-based HTML
    report_html = _build_generated_report_html(use_cases)
```

### Impact Case Study Markdown Sections

```markdown
# {Theme Title}

## Executive Summary
- Brief overview
- Total findings: {count}
- Credible findings: {count}

## Underpinning Research
- First 3 use cases summarized
- Research focus and dates

## References to the Research
- Markdown links to all unique sources

## Details of the Impact
- Full impact details for each use case
- Structured with subheadings

## Sources to Corroborate the Impact
- All sources listed
- Credibility reasoning included

## Summary of the Impact
- Sector analysis
- Credibility statistics

## References
- HTML table with all links
```

### HTML Table Format

```html
<h3>{Theme Title}</h3>

<!-- Summary Alert -->
<div class="alert alert-info">
  <strong>REF evidence summary:</strong> {count} finding(s) extracted; 
  {credible_count} marked credible...
</div>

<!-- Impact Evidence Table -->
<table class="table">
  <thead>
    <tr>
      <th>Title</th>
      <th>Organisation</th>
      <th>Impact Type</th>
      <th>Sector</th>
      <th>Quantitative Outcome</th>
      <th>Dates</th>
      <th>Source URL</th>
      <th>Verified?</th>
      <th>Notes</th>
    </tr>
  </thead>
  <tbody>
    <!-- One row per use case -->
  </tbody>
</table>

<!-- References Table -->
<table class="table">
  <thead>
    <tr>
      <th>#</th>
      <th>Link</th>
      <th>Title</th>
      <th>Evidence Quality</th>
    </tr>
  </thead>
  <tbody>
    <!-- One row per unique source -->
  </tbody>
</table>
```

### Data Escaping & Security

All user-controlled content HTML-escaped:
```python
from html import escape

source_html = (
    f'<a href="{escape(source_url)}" target="_blank">'
    f'{escape(shortened_url)}</a>'
)
```

Prevents XSS attacks.

---

## Result Display

### Final Report View

**After completion**, frontend displays:

1. **Metrics Dashboard**:
   - Total findings: N
   - Credible findings: N
   - Average credibility: X%
   - Average relevance: X%

2. **Formatted Report**:
   - Rendered HTML from `report.generated_report`
   - Markdown or table format based on report_type

3. **Use Cases List**:
   - Expandable cards with all extracted use cases
   - Click to see full details

4. **Actions**:
   - Export to PDF
   - Copy to clipboard
   - Share report link
   - Regenerate with different settings

---

## Summary Diagram: Complete Data Flow

```
USER INPUT (Frontend)
    │
    ├─ Query + PDF (optional)
    ├─ Report type & settings
    └─ Submit
        │
        ▼
    FRONTEND → API
        │
        ├─ POST /content/report-generation/
        └─ RECEIVE: {theme_id, report_id}
            │
            ▼
        BACKEND (Synchronous)
            │
            ├─ Parse request
            ├─ Extract PDF (if provided)
            ├─ Create Report model
            └─ START BACKGROUND THREAD
                │
                ▼
            BACKGROUND THREAD (Asynchronous)
                │
                ├─ StructuredReportGenerator.run()
                │
                ├─ LANGGRAPH EXECUTION
                │  ├─ Planning Node: Generate tasks
                │  │
                │  ├─ Task Execution Loop:
                │  │  ├─ Search Node: TavilySearchResults
                │  │  ├─ Scrape Node: Async URL fetching
                │  │  └─ Extract Node: LLM + DB create
                │  │     ├─ Credibility checks (parallel)
                │  │     ├─ Relevance checks (parallel)
                │  │     └─ Stream via Pusher
                │  │
                │  └─ Final: Save report HTML
                │
                └─ Update Report.generated_report
                    │
                    ▼ (Pusher Streaming)
                FRONTEND (Real-time)
                    │
                    ├─ Receive <usecase> events
                    ├─ Update use cases list
                    ├─ Update progress bar
                    └─ On completion: Fetch final report
                        │
                        ▼
                    GET /content/reports/{id}/
                        │
                        ├─ RECEIVE: Report with generated_report HTML
                        └─ DISPLAY: Formatted report
```

---

## Key Takeaways

1. **Non-blocking API**: Report generation happens in background thread; frontend gets immediate response
2. **Real-time Streaming**: Pusher pushes progress and findings to frontend as they're extracted
3. **Database-centric**: Each use case persisted to DB immediately upon extraction
4. **Parallel Processing**: Credibility & relevance checks run in parallel threads
5. **LLM-driven**: All extraction, validation, and synthesis done via GPT-4o
6. **Web Search**: TavilySearchResults provides web search; SimpleHtmlScraper fetches content
7. **REF Compliance**: Reports formatted according to REF 2029 guidelines
8. **Graceful Degradation**: If LLM synthesis fails, falls back to template format
9. **Scalability**: Complexity mapping allows tuning API calls per user needs
10. **Quality Gates**: Relevance threshold filters low-quality findings

---

## External Dependencies

| Service | Purpose | Function |
|---------|---------|----------|
| **OpenAI GPT-4o** | LLM | Planning, extraction, synthesis, validation |
| **TavilySearchResults** | Web search | Find relevant web pages |
| **SimpleHtmlScraper** | Web scraping | Extract text from HTML |
| **Pusher** | Real-time messaging | Stream progress to frontend |
| **Django ORM** | Database | Persist reports and use cases |
| **LangChain** | LLM orchestration | Prompt management, tool calling |
| **LangGraph** | State machine | Workflow orchestration |

---

Generated: 2024-01-15
