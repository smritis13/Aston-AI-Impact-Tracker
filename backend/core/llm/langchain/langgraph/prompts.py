from ast import arg
from langchain.prompts import PromptTemplate

"""
Prompts used in the LangGraphChatEngine.
This file contains all the system prompts used in the LangGraphChatEngine for better maintainability.
"""


CHAT_ENGINE_CLASSIFY_QUERY_PROMPT = """You are an AI assistant classifying if a user's query needs deep research.

Respond with just one word: "simple" if it's a greeting or chit-chat, or "complex" if it requires research.

Examples:
- "Hello" => simple
- "How's the weather?" => simple
- "What is the impact of climate change on agriculture?" => complex
- "Tell me a joke" => simple
- "Explain quantum computing" => complex

Query: {query}
Answer:"""


# Prompt for breaking down a user query into sub-questions
CHAT_ENGINE_PLAN_QUERY_PROMPT = """
You are an AI assistant tasked with breaking a user query into sub-questions **only if** it requires research.

First, classify the query as either "simple" or "complex":
- "simple" means it's a greeting, casual question, or something that does not need research.
- "complex" means it requires research and should be broken down into sub-questions.

Respond with **one of the following JSON objects only**:

1. For simple questions:
{{
  "type": "simple",
  "response": "Hi there! How can I help you today?"  // or an appropriate direct reply
}}

2. For complex questions:
{{
  "type": "complex",
  "sub_questions": ["question 1", "question 2", ...]  // 5 to 10 sub-questions
}}

Query: {query}
"""

# Prompt for summarizing search results
CHAT_ENGINE_SUMMARIZE_PROMPT = """Analyze the following information with the explicit goal of identifying **real‑world research impacts** according to our tracker’s definition.

Impact is an effect, change or benefit to the economy, society, culture, public policy or services, health, the environment or quality of life beyond academia. This may include changes in activity, attitude, awareness, behaviour, capacity, opportunity, performance, policy, practice, process or understanding for any audience, beneficiary, community, constituency, organisation or individuals at any geographic scale. It also includes reduction or prevention of harm, risk, cost or other negative effects. Impacts that solely advance academic knowledge are excluded; student, teaching and professional‑practice impacts are included.

Your response should include:
1. A concise summary of the main information (2‑3 sentences)
2. 3‑5 key impact insights or findings that highlight real‑world change
3. Any relevant data points, statistics, or metrics mentioned
4. Notable examples or case studies that demonstrate actual change
5. Potential implications, beneficiaries, or trends that emerge from the evidence

Always emphasise concrete outcomes and verifiable metrics rather than general observations. Format your response with clear headings and bullet points for readability."""
# Prompt for synthesizing the final answer
CHAT_ENGINE_SYNTHESIZE_PROMPT = """You are an expert research‑impact analyst. Your task is to produce a comprehensive, structured response designed to support an AI‑assisted impact tracker.

Remember that impact for this tool means:
• an effect, change or benefit to the economy, society, culture, public policy or services, health, the environment or quality of life beyond academia
• this can involve changes in activity, attitude, awareness, behaviour, capacity, opportunity, performance, policy, practice, process or understanding for any audience, beneficiary, community, constituency, organisation or individual, at any geographic scale
• it also includes reduction or prevention of harm, risk, cost or other negative effects
• impacts that only advance academic knowledge are excluded; impacts on students, teaching, and professional practice are included

Follow these guidelines:
1. Begin with an executive summary (2‑3 paragraphs) that highlights the most significant real‑world impacts found
2. Structure your response with clear headings and subheadings reflecting impact domains (economic, social, health, environment, etc.)
3. Include relevant data tables, charts, or bullet points where appropriate
4. Provide detailed analysis with supporting evidence and verifiable sources
5. Include specific examples and case studies when available, noting beneficiaries and geographic scope
6. If the user’s query refers to a specific company or organisation, focus the analysis on impacts tied to that entity. Do not require the user to list any column headings in their question – the output format is fixed.
7. End with a summary table listing each impact with the following hard‑coded column headers:
   • Title / Product name
   • Organisation / Beneficiary
   • Impact type
   • Sector
   • Quantitative outcome (numbers only)
   • Dates / timeframe
   • Source URL
   • Verified?
   • Notes / corrections
   Output the table in HTML <table class="table"> format unless instructed otherwise.
8. Add numeric values (e.g. 10% improvement, 20% reduction) to the table when available
9. Use clear, professional language suitable for research impact or policy stakeholders
10. Cite sources appropriately using footnotes or references

Your response should demonstrate deep analytical thinking and focus on evidence of change or benefit beyond academia."""

RELEVANCE_CHECK_PROMPT = PromptTemplate(
    input_variables=["user_prompt", "use_case", "theme_title"],
    template="""
You are a relevance assessment expert. Evaluate if the following use case is relevant to the user's requirements and theme.

User Requirements:
{user_prompt}

Theme: {theme_title}

Use Case to Evaluate:
{use_case}

Analyze the following aspects:
1. Theme Alignment:
   - Does the use case match the specified theme?
   - Is the use_case_type appropriate for the specified theme domain?
   - Does the use case align with the theme's scope and objectives?

2. Content Quality:
   - Is the use_case_name clear and specific (not generic like "Process Improvement")?
   - Does the use_case_description provide concrete details about implementation?
   - Are specific tools or technologies mentioned?
   - Is there a measurable performance impact?

3. Industry/Company Relevance:
   - Does the company belong to the industry/sector specified in the user prompt?
   - If no industry is specified, is the company relevant to the process/topic?

4. Implementation Specificity:
   - Does it describe a real, tangible process or tool?
   - Are there concrete artifacts or keywords mentioned?
   - Is it more than just vague claims about "improving efficiency"?

5. Tool/Technology Relevance:
   - Are the tools mentioned relevant to the theme?
   - Are they actual development tools (not marketing/HR tools)?
   - The tool is not a hardware product or infrastructure. It is a software product or practice.
   - For other themes, are they appropriate for the domain?

6. Exclusion of Business Operations and Non-Theme Processes:
   - Does the use case focus on business operations, customer-facing features, or processes unrelated to the theme?
   - Exclude third-party integrations or external system connectors that are not core to the theme.
   - Exclude customer-facing or end-user features that are tangential to the theme's purpose.
   - Exclude operational analytics or business intelligence tools unless directly tied to the theme.
   - Focus on processes that are core to the specified theme domain, not peripheral business functions.

7. Exclusion of Generic Practices or Ideologies:
   - Does the use case describe only generic methodologies, frameworks, or standards without specific tools or concrete processes?
   - Ensure the use case specifies concrete, implementable practices tied to actual tools or technologies.
   - Generic training programs, policy adoption, or abstract methodology changes should be excluded unless tied to specific implementation.

8. Exclusion of Documentation or Non-Tool-Based Processes:
   - Does the use case focus purely on documentation creation or non-tool-based methodologies without technological implementation?
   - Exclude documentation-only processes unless they involve automation, specific tools, or technology enablement relevant to the theme.
   - Prioritize use cases that demonstrate technological adoption or process automation over manual documentation tasks.

9. Exclusion of Market Research and Non-Theme Analytics:
   - Does the use case focus on market research, business intelligence, or analytics unrelated to the theme's core domain?
   - Exclude analytics tools used for business purposes (e.g., customer behavior, sales trends, market research) unless they directly support the theme.
   - Prioritize analytics that directly measure or optimize processes within the theme's scope.

Return a JSON object with:
{{
    "relevance_score": <0-10 integer>,
    "is_relevant": <true/false>,
    "reasoning": "<brief explanation of the score, highlighting which aspects passed/failed>"
}}

Score guidelines:
- 0-2: Completely irrelevant to theme and requirements
- 3-4: Marginally relevant, some tangential connection
- 5-6: Moderately relevant, matches some aspects
- 7-8: Highly relevant, matches most requirements
- 9-10: Perfectly relevant, exactly matches all requirements

Important:
- Return ONLY a valid JSON object matching the schema above.
- Do not include Markdown fences (```), explanatory text, or any content outside the JSON object.
- Ensure the response is properly formatted and parseable as JSON.
"""
)

SDLC_USECASE_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text", "structure"],
    template="""
You are extracting structured SDLC use cases from web content for any industry.

Extract a list of use cases into the following JSON structure:
{structure}

Instructions:
- Extract only **real-world SDLC applications** used by real companies in the relevant sector.
- Use specific **company names** (e.g., "Pfizer", "Moderna", "Novartis").
- Include specific **SDLC tools** tied to software development phases (e.g., "Jira" for planning, "GitHub" for development, "Jenkins" for deployment, "Selenium" for testing).
- The **use_case_description** must:
  - Specify *how* the tools are used in the SDLC process.
  - Tie the usage to a specific SDLC phase (Planning, Design, Development, Testing, Deployment, Maintenance).
  - Describe the problem solved or process improved (e.g., "Automated testing with Selenium in the Testing phase to reduce bugs in clinical data systems").
- Include **metric_impact** if available (e.g., "Reduced drug development cycle by 6 months"). Leave blank if not specified.
- If **date** is unavailable, leave it blank.
- Return a valid **JSON array** of use cases (no markdown, no commentary).

Example:
[
  {{
    "company": "Walmart",
    "industry_segment": "General Merchandise",
    "sdlc_tools": "Jira, GitHub Actions",
    "use_case_description": "Walmart uses Jira for sprint planning in the Planning phase and GitHub Actions for automated deployments in the Deployment phase to streamline software releases.",
    "metric_impact": "Improved release cycle by 25%",
    "date": "2024-05-01",
    "source": "https://example.com/article",
  }}
]

Now analyze this text:
\"\"\"{text}\"\"\"
"""
)

SDLC_RELEVANCE_CHECK_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""
Evaluate the following text to determine if it is relevant for SDLC use case extraction in any sector.

The text is relevant if it includes:
1. **SDLC-specific tools or practices** tied to software development phases (e.g., "Jira" for planning, "Jenkins" for CI/CD, "Selenium" for testing, "Kubernetes" for deployment).
2. Applied within a real company relevant to the sector (e.g., "Walmart", "Siemens").
3. Describes **real-world usage** of SDLC tools or practices in software development (not general tech like robotics or customer-facing AI unless part of SDLC).

Return JSON only:
- `{{"relevance": true}}` if relevant
- `{{"relevance": false}}` if not

Text to analyze:
\"\"\"{text}\"\"\"
"""
)


AI_SDLC_USECASE_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text", "structure"],
    template="""
# 🧠 AI Use Case Extraction Prompt for SDLC Phases

## Identity

You are an AI assistant specialized in analyzing web content to identify real-world applications of AI within the Software Development Life Cycle (SDLC). Your goal is to extract and structure information about how AI is utilized across various SDLC phases.

## Instructions

- **Scope**: Focus exclusively on real-world AI applications within the following SDLC phases:
  - Requirements Engineering
  - Design
  - Development
  - Testing
  - Deployment
  - Maintenance & Operations

- **Extraction Criteria**:
  - **phase**: One of the specified SDLC phases.
  - **use_case**: A concise and specific title of the AI application (e.g., "Automated Test Case Generation").
  - **description**: 
    - Detail how AI is applied in the specified SDLC phase.
    - Describe the problem solved or the process improved.
    - Mention the company or organization implementing the solution.
    - Provide 2-3 sentences for clarity.
  - **tools**: List specific tools used, including their versions if available (e.g., "GitHub Copilot v1.10"). Leave blank if not specified.
  - **performance_improvements**: Include quantitative metrics (e.g., "Reduced test creation time by 40-65%") or qualitative outcomes (e.g., "Enhanced test coverage"). If not specified, state "Not specified".
  - **source**: The URL of the web page where the information was found.
  - **date**: The publication date of the source in "YYYY-MM-DD" format. Leave blank if not available.

- **Output Format**:
  - Return a valid JSON array of objects, each representing a unique use case.
  - Do not include any additional text or commentary outside the JSON array.

## Example

```json
[
  {{
    "phase": "Testing",
    "use_case": "Automated Test Case Generation",
    "description": "Company A utilizes AI to analyze requirements and automatically generate test cases during the Testing phase, integrating with CI/CD pipelines to reduce manual effort and minimize human error.",
    "tools": "Testim v2.3, Mabl v1.8",
    "performance_improvements": "Reduced test creation time by 40-65%",
    "source": "https://example.com/article",
    "date": "2024-06-01"
  }}
]
```

## Context

Please analyze the provided web search results to identify relevant AI applications within the SDLC. Extract and structure the information as per the instructions above.

<web_search_results>
\"\"\"{text}\"\"\"
</web_search_results>
"""
)

AI_SDLC_RELEVANCE_CHECK_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""
Evaluate the following text to determine if it is relevant for AI use case extraction in the **Software Development Lifecycle (SDLC)**.

The text is relevant if it includes:
1. **AI-specific applications or tools** tied to SDLC phases.
2. Describes **real-world usage** of AI in one of the SDLC phases: Requirements Engineering, Design, Development, Testing, Deployment, Maintenance & Operations.
3. Focuses on **software development processes** (not general AI applications like customer-facing chatbots unless explicitly tied to SDLC).

Return JSON only:
- `{{"relevance": true}}` if relevant
- `{{"relevance": false}}` if not

Text to analyze:
\"\"\"{text}\"\"\"
"""
)


# 1. Initial planning: break the user's query into top-level sub-questions.
DEEPRESEARCH_PLAN_PROMPT = """
You are a methodical research assistant. 
Given a user's research question, decompose it into 5-15 distinct, high-level sub-questions that together cover the full scope of the inquiry.
Return ONLY a JSON array of strings, e.g. ["What is X?", "How do Y work?", …].
"""

# 2. (Optional) Multi-level subplanning: break a previous sub-question further down if needed.
DEEPRESEARCH_SUBPLAN_PROMPT = """
You are a deep-dive researcher. 
Given an existing set of sub-questions and any current findings, identify 3-5 targeted follow-up sub-questions that will fill gaps in the research.
Return ONLY a JSON array of strings.
"""

# 3. Summarization of search snippets for a single question.
DEEPRESEARCH_SUMMARIZE_PROMPT = """
You are an expert summarizer. 
Given a collection of text snippets (excerpts and summaries of search results), produce a concise, coherent summary paragraph that answers the question. 
Cite any critical claims inline , but keep it under 500 words.
"""

# 4. Refinement check: decide whether to iterate deeper.
DEEPRESEARCH_REFINE_CHECK_PROMPT = """
You are a research auditor. 
Review the current findings (provided as JSON mapping each sub-question to its summary). 
Answer "YES" if deeper sub-questions are needed to fully address the user's original query; otherwise answer "NO". 
Do NOT provide any other text.
"""

# 5. Refinement planning: generate follow-up sub-questions when needed.
DEEPRESEARCH_REFINE_PLAN_PROMPT = """
You are a strategic researcher tasked with conducting comprehensive and thorough investigations.

Given the current findings and the list of previously asked sub-questions, identify any remaining gaps, overlooked aspects, or areas that require further exploration to fully address the user's query.

Your objectives are:

1. **Gap Analysis**: Examine the existing findings and sub-questions to pinpoint missing information or perspectives that have not been covered.

2. **Comprehensive Coverage**: For requests involving specific quantities (e.g., "20 use cases"), ensure that the number of sub-questions aligns with the user's expectations, aiming to fulfill or exceed the requested amount.

3. **Diverse Perspectives**: Consider various angles, including technical, practical, historical, and future-oriented aspects, to provide a well-rounded exploration of the topic.

4. **Actionable Sub-Questions**: Formulate clear, concise, and researchable sub-questions that can guide further investigation and yield valuable insights.

Return ONLY a JSON array of strings containing the new sub-questions. Do not include any explanations or additional text outside the JSON array.

"""

# 6. Final synthesis: weave all collected summaries into the user's final answer.
DEEPRESEARCH_SYNTHESIZE_PROMPT = """
You are an authoritative, well-informed writer. 
Given a series of bulletized research summaries—each headed by its sub-question—produce a unified, in-depth answer to the user's original query. 
Structure your response clearly, use headings for each major theme, and integrate insights across sub-questions into a cohesive narrative.
if there is a table, return it in HTML format over Markdown for better formatting. Use a clean, Bootstrap-compatible HTML table with <table class="table"> and proper <thead> and <tbody> tags. do not add ``` html or ``` to the beginning or end of the table. Always use the following column headers when generating impact tables: Title / Product name; Organisation / Beneficiary; Impact type; Sector; Quantitative outcome (numbers only); Dates / timeframe; Source URL; Verified?; Notes / corrections. When the user mentions a specific company, ensure the table highlights entries for that company and ignore any user-supplied headings.

"""


PLANNING_PROMPT = """

You are a versatile research assistant capable of addressing a wide range of user prompts.

**User Prompt**: 

<user_prompt>
  {user_prompt}
</user_prompt>

**Theme**: {theme_title}

**Goal**
Generate a task list to gather detailed, actionable insights based on the specified theme.

**Instructions**

1. **Task Generation**:
   - Based on the user prompt and theme, generate **≤ {max_tasks} tasks**
   - For each task, return a JSON object with:
     - "company": The name of a company relevant to the theme
     - "search_queries": **5-10 diverse, Google-style queries** designed to uncover:
       - **Specific practices, tools, or processes** related to the theme
       - **Numerical impact metrics** (e.g., % improvement, cost savings, time reduction)
       - **Recent case studies, success stories, or technical documentation** (e.g., whitepapers, blog posts, press releases). Today's date is {today}
       - **Implementation details** (e.g., how tools/processes are applied, challenges faced)

2. **Company Selection**:
   - If no companies are mentioned but the prompt implies an industry, select relevant companies for that sector
   - Prioritize companies known for innovation or public documentation in the context
   - If companies are irrelevant, replace "company" with a "topic" field describing the research focus

3. **Query Design**:
   - Ensure queries are specific, concise, and likely to surface **recent (last 12 months unless specified)** information
   - Use advanced search techniques where applicable (e.g., `site:*.edu`, `site:*.gov`, `site:techcrunch.com`)
   - Vary query focus to cover different aspects of the topic

**Output JSON ONLY** - an object like:

json
{{
  "tasks": [
    {{
      "company": "JPMorgan Chase",
      "search_queries": [
        "JPMorgan Chase AI loan processing implementation 2025",
        "JPMorgan Chase AI banking efficiency metrics 2025",
        "JPMorgan Chase AI banking case study 2025 site:techcrunch.com",
        "JPMorgan Chase AI banking tools adoption 2025"
      ]
    }},
    {{
      "company": "HSBC",
      "search_queries": [
        "HSBC AI banking process improvement 2025",
        "HSBC AI banking automation impact 2025",
        "HSBC AI banking case study 2025 site:cio.com",
        "HSBC AI banking challenges 2025"
      ]
    }}
  ]
}}

"""


EXTRACTION_PROMPT = """ 

You are a senior research analyst.

**Task**  
Based on the provided user prompt and theme, read the ARTICLE below and extract every distinct use case related to the specified topic, process, or practice.

**User Prompt**: 

<user_prompt>
  {user_prompt}
</user_prompt>

**Theme**: {theme_title}


**Strict Filters**

1. **Company Relevance**:
   - If the user prompt specifies an industry or sector, the company must belong to that sector (e.g., for retail: Walmart, Amazon; for tech: Google, Microsoft).
   - If the user prompt does not specify an industry, include companies relevant to the process.
   - Exclude vendors, consultancies, or unrelated entities unless explicitly relevant to the user prompt. If unsure, omit the entry.
   - Example: For any sector, the company must be directly within that sector (e.g., a retailer for retail, a bank for finance) not a vendor or service provider, even if they work with companies in that sector.

2. **Process or Tool Specificity**:
   - The information must describe a **real, tangible process, tool, or practice** related to the user prompt.
   - A use case must be a real implementation that has been done, not a prediction or future plan.
   - A tool is not a hardware product or infrastructure. It is a software product or practice.
   - CI/CD pipelines are not tools - they are processes. Tools are specific software products used within these processes.
   - Tools must be directly connected to the improvement or outcome described in the use case.
   - Generate the use_case_type based on the theme and content. For example, if the theme is SDLC, the use_case_type MUST be one of:
     * Requirements Engineering
     * Design
     * Development
     * Testing
     * Deployment
     * Maintenance & Operations
   - For other themes, provide an appropriate category based on the theme and content.

3. **Numerical Impact Metrics**:
   - Prefer entries with at least one numerical impact metric (e.g., %, $, hours saved, error rate reduction).
   - If no metric is present, set `"performance_impact": ""` but retain the entry if it meets other criteria.

4. **Duplicate Handling**:
   - If multiple use cases are found for the same company and tool/process, keep only the most detailed entry.
   - If metrics differ, merge them into a single entry.

5. **Concrete Artefacts**:
   - The use case description must relate to a specific stage or aspect of the process.
   - It must mention a concrete artefact or keyword.
   - Ensure use case descriptions accurately reflect source URL content. the use case description should be extracted or summarised from the source URL content.
   - Reject vague phrases like "improving efficiency" without specific details.

6. **Tangible Description**:
   - Clearly state *what* was built, changed, or implemented and *how* it relates to the process or topic.
   - The description must explicitly explain how the tool is connected to the improvement or outcome.
   - Include specific details about the implementation and its impact.

7. **Allowed Tools or Technologies**:
   - If the user prompt involves specific tools or technologies (e.g., SDLC tools, AI frameworks), ensure the use case mentions tangible software, frameworks, or platforms relevant to the prompt.
   - Examples (for SDLC): Version control (Git, Bitbucket), CI/CD (Jenkins, GitHub Actions), Testing (JUnit, Selenium), IaC (Terraform, Kubernetes), Observability (Datadog, Prometheus), Languages/Frameworks (Python, React).
   - For other themes, adapt to relevant tools (e.g., for AI: TensorFlow, PyTorch; for supply chain: SAP, Oracle NetSuite).
   - Exclude unrelated tools (e.g., marketing, HR, or analytics tools) unless embedded in the process specified by the user prompt.
   - Focus only on tools that are directly involved in productivity improvement and are directly related to the use case itself.
   - Tools must have a clear, demonstrable impact on improving productivity in the specific use case context.

8. **Tool/Process Description**:
   - The use case description must explicitly mention the use of the specified tools, technologies, or practices and how they were applied.
   - Explain the direct connection between the tool usage and the improvement achieved.

9. **Use Case Name**:
   - Each use case must have a clear, concise name (one sentence maximum).

10. **Date Accuracy**:
    - its important to scan the content to find the date of the use case implementation.
    - The date field should reflect the actual implementation date of the use case, if not specified, use the publication date of the article.
    -  today's date is {today}. Do not use today's date or future dates for the use case implementation.
    - If the date is in format like Sep 2024, convert it to 2024-09-01.

11. **Hardware and Product Announcements**:
    - Exclude hardware-only implementations or product announcements.
    - Examples of excluded cases:
      * "Microsoft introduced new AI hardware"
      * "Company X launched a new product"
      * "New hardware implementation for process Y"
    - Only include cases where software, tools, or processes are actively used to solve a problem or improve a process.

12. **Exclusion of Business Operations and Non-SDLC Processes**:
    - Exclude use cases focused on business operations, customer-facing features, or non-SDLC processes (e.g., inventory synchronization, payment gateways, marketing, or customer data integration) unless they involve SDLC-specific tools or practices.
    - Examples of excluded cases:
      * Integration of external business systems (e.g., third-party APIs, Stripe).
      * Customer-facing features like virtual try-on, personalization, or chatbots.
      * Operational analytics like demand forecasting or sales trend analysis.
    - Ensure the use case directly relates to SDLC phases and uses development tools (e.g., CI/CD, Kubernetes, testing frameworks).

13. **Exclusion of Generic Practices or Ideologies**:
    - Exclude use cases that describe generic practices, methodologies, or ideologies (e.g., Agile practices, clean code standards, modular architecture) without specific SDLC tools or processes.
    - Examples of excluded cases:
      * Formation of Agile squads or feedback loops without tool specificity.
      * Adoption of clean code or documentation standards without development tools.
    - The use case must specify concrete SDLC tools or practices (e.g., Git, Jenkins, Selenium).

14. **Exclusion of Documentation or Non-Tool-Based Processes**:
    - Exclude use cases centered on documentation processes or non-tool-based methodologies (e.g., narrative documents, surveys) unless they involve SDLC-specific tools.
    - Examples of excluded cases:
      * Drafting six-page narratives or PR/FAQ documents.
      * Reverse-engineering and documenting legacy code without tool use.
    - Ensure the use case involves tangible SDLC tools or development processes.

15. **FOR SDLC THEMES**: Exclusion of Market Research and Non-SDLC Analytics**:
    - Exclude use cases focused on market research, exploratory data analysis, or other analytical processes not directly tied to SDLC (e.g., customer behavior analytics, sales trend analysis).
    - Examples of excluded cases:
      * Market research using Google Analytics or SurveyMonkey.
      * Feature prioritization via customer behavior analytics.
    - The use case must pertain to software development or lifecycle management.

16. **Instructions for use_case_type:**
- Choose the use_case_type from the provided list below if possible.
- If you must generate a new use_case_type, ensure it is mutually exclusive and collectively exhaustive (MECE) with the provided list, and do not overlap with existing types.

**Output Procedure**

**Think step-by-step but only show the final JSON**:
1. Identify candidate use cases from the article.
2. For each use case:
   - Determine the use case type based on the theme and content
   - For SDLC themes, ensure the type matches one of the required phases
3. Disqualify any that violate filters 1-15.
4. Output surviving use cases as a JSON array **exactly** matching the schema below.


**Allowed use_case_type options for the theme:**
<use_case_type_options>
{use_case_type_options}
</use_case_type_options>


<schema>
{schema}
</schema>

<article>
{article}
</article>

Important: Return in VALID JSON format with NO explanation text before or after.
"""

PDF_QUANTITATIVE_EXTRACTION_PROMPT = """
You are extracting quantitative real-world impact evidence from a PDF impact case study.

User request:
<user_prompt>
{user_prompt}
</user_prompt>

Theme: {theme_title}

Task:
Find quantitative impacts from this study and return only measurable real-world outcomes with numbers, dates/timeframes, and beneficiaries.

Rules:
1. Extract one row per distinct measurable outcome. Do not merge several outcomes into one broad row.
2. Prioritize outcomes with explicit numbers: percentages, counts, population coverage, guideline counts, website hits, completions, deaths prevented, disease cases prevented, events avoided, screening benefit, adoption reach, and model development/validation scale.
3. Keep the value as close to the PDF wording as possible. Do not invent values, dates, beneficiaries, or organizations.
4. Use the main beneficiary or implementing organization in "company" even if it is a public body such as NHS, NICE, GP practices, patients, or the public.
5. Use "Healthcare" for industry unless the PDF clearly indicates another sector.
6. Use "Health Impact", "Policy Influence", "Public Reach", "Clinical Adoption", "Disease Prevention", "Mortality Reduction", "Risk Prediction", or another concise impact category for use_case_type.
7. For "performance_impact", include the exact quantitative outcome and enough context to understand it.
8. For "use_case_description", briefly explain what changed in the real world and who benefited.
9. If a date is not explicit for that exact outcome, use the closest timeframe stated in the PDF. If no date/timeframe is available, leave "use_case_date" blank.
10. Return up to {max_use_cases} high-quality outcomes. If the PDF contains fewer measurable outcomes, return fewer.
11. Exclude generic background, academic-only findings, methods without real-world impact, and claims without a measurable outcome.

Output a JSON array exactly matching this schema:
<schema>
{schema}
</schema>

PDF text:
<article>
{article}
</article>

Return VALID JSON only. Do not include Markdown fences, commentary, or explanation text.
"""

# (planning prompt removed)


# (usecase extraction prompt removed)

# RETAIL_SDLC_RELEVANCE_PROMPT removed as it is no longer applicable


CREDIBILITY_CHECK_PROMPT = PromptTemplate(
    input_variables=["article", "use_case"],
    template="""
You are a credibility assessment expert. Evaluate the following use case extracted from an article for its credibility and trustworthiness.

Article:
{article}

Use Case to Evaluate:
{use_case}

Analyze the following aspects:
1. Source credibility (is it a reputable source?)
2. First-hand information (is it direct experience or hearsay?)
3. Specificity of details (are there concrete details or just vague claims?)
4. Evidence provided (are there metrics, examples, or specific implementations?)
5. Timeliness (is the information current?)
6. Claim-source match (does the article specifically name or clearly identify
   the exact organisation/product/claim in the use case, rather than only a
   general category it belongs to? A reputable source about something merely
   adjacent or similar is NOT credible evidence for this specific use case,
   even if the source itself is high quality.)
7. Date accuracy: find the actual date evidence in the article (a publication
   date, byline date, or an explicit date/timeframe stated in the body text).
   Compare it against the use case's "use_case_date" field.
   - If the article states a specific day/month/year and "use_case_date" gives
     a different day, month, or year, this is a date mismatch - treat it as a
     serious credibility problem and cap the score at 4 or below, regardless
     of how good the rest of the evidence is.
   - If "use_case_date" is more precise than the article supports (e.g. a full
     day when the article only gives a month or year), treat that invented
     precision the same as a mismatch.
   - If the article gives no date evidence at all, a null/empty "use_case_date"
     is correct and should not be penalised; a non-null value in that situation
     is unsupported and should lower the score.

Return a JSON object with:
{{
    "credibility_score": <0-10 integer>,
    "is_credible": <true/false>,
    "reasoning": "<brief explanation of the score, explicitly stating whether the source names the specific organisation/product in the use case, and whether use_case_date matches the article's actual date evidence>"
}}

Score guidelines:
- 0-2: Highly questionable, no credible source, vague claims
- 3-4: Some concerns, limited evidence, possible hearsay, or a date mismatch against the article
- 5-6: Moderately credible, some specific details but limited evidence
- 7-8: Good credibility, specific details and evidence provided
- 9-10: Highly credible, first-hand information with concrete evidence

Return ONLY the JSON object, no additional text.
"""
)

THEME_NAME_GENERATION_PROMPT = PromptTemplate(
    input_variables=["query", "existing_themes"],
    template="""
Generate a theme name for the following query: {query}. 
The theme name should be one or two words that captures the essence of the query.

Existing themes: {existing_themes}

If any existing theme is a good match for this query, return that theme name exactly as it appears in the list above.
If no existing theme is a good match, generate a new theme name following these examples:

    Query: 'give me use cases of sdlc in [sector] industry'
    Theme: '[Sector]-SDLC'
    Query: 'find use cases of AI in finance'
    Theme: 'AI-FINANCE'
    Query: 'find use cases of AI in manufacturing'
    Theme: 'AI-MANUFACTURING'
    Query: 'explore SDLC applications in AI'
    Theme: 'AI-SDLC'
    Query: 'investigate AI solutions in [sector]'
    Theme: '[Sector]-AI'

Important: just return the theme name, no other text. return it as text and dont add any other text or comments
"""
)

USE_CASE_TYPE_GENERATION_PROMPT = PromptTemplate(
    input_variables=["user_prompt", "theme_title", "existing_types"],
    template="""
You are an expert at categorizing and organizing use cases into logical, mutually exclusive and collectively exhaustive (MECE) categories.

**User Prompt**: {user_prompt}
**Theme**: {theme_title}
**Existing Use Case Types**: {existing_types}

**Task**: 
Generate a comprehensive list of use case types that would be appropriate for this theme and user prompt. If existing types are provided, analyze them and suggest additional types that would complement the existing list to create a complete MECE framework.

**Guidelines**:
1. **MECE Principle**: Categories should be Mutually Exclusive (no overlap) and Collectively Exhaustive (cover all possibilities)
2. **Theme Alignment**: Types should be relevant to the specific theme and user prompt
3. **Practical Focus**: Focus on actionable, implementable use case categories
4. **Industry Context**: Consider the industry or sector mentioned in the user prompt
5. **Existing Types**: If existing types are provided:
   - Analyze their coverage and identify gaps
   - Suggest additional types that would complement the existing ones
   - Ensure new types don't overlap with existing ones
   - Maintain consistency in naming and scope
6. **Maximum Limit**: Generate a maximum of 8 use case types total (including existing ones if provided)

**Special Cases**:
- For SDLC themes: Use standard SDLC phases (Requirements Engineering, Design, Development, Testing, Deployment, Maintenance & Operations)
- For AI themes: Consider AI application areas (e.g., Natural Language Processing, Computer Vision, Predictive Analytics, etc.)
- For industry-specific themes: Consider industry-specific processes and applications

**Output Format**:
Return a JSON array of strings containing the use case types. Include both existing types (if provided) and any new types you suggest. Maximum 8 types total.

Example output:
["Type 1", "Type 2", "Type 3", ...]

**Important**: Return ONLY the JSON array, no additional text or explanations. Maximum 8 types.
"""
)

