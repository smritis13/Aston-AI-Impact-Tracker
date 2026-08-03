
"""
REF 2029-Aligned Prompts for Impact Case Study Generation

This module provides enhanced prompts aligned with Research Excellence Framework (REF 2029)
standards for generating high-quality impact case studies. REF defines impact as:

"An effect, change or benefit to the economy, society, culture, public policy or services,
health, the environment or quality of life beyond academia."

Key REF 2029 Requirements:
- REF Impact Case Studies (ICS) limit: 2,200 words total (REF 2029)
- REF 2021 was: ~1,500-2,000 words total
- Sections: Summary (~100 words), Underpinning Research (~600 words), 
           Details of Impact (~1,500 words), Supporting Evidence (up to 6 references)
- Emphasis on: Reach (breadth of beneficiaries), Significance (depth of impact),
              Engagement (stakeholder collaboration), Evidence (verifiable sources)

Reference: https://2029.ref.ac.uk/guidance/section-6-engagement-and-impact-guidance/
"""

# ════════════════════════════════════════════════════════════════════════════
# REF CASE STUDY PLANNING PROMPT
# ════════════════════════════════════════════════════════════════════════════

REF_PLANNING_PROMPT = """
You are a research impact analyst specializing in REF (Research Excellence Framework) case studies.

**User Prompt**: 
<user_prompt>
  {user_prompt}
</user_prompt>

**Theme**: {theme_title}

**Goal**
Generate a task list to identify and gather evidence for REF 2029-compliant impact case studies.

**REF 2029 Eligible Periods (apply automatically - the user prompt does not need to restate this)**
- Underpinning research: 1 January 2008 - 31 December 2028. Research the impact rests on can be
  much older than the impact itself, so don't discard an old paper/output on age alone.
- Impact occurrence: 1 August 2020 - 31 July 2028. Impact evidence (deployment, adoption, policy
  change, reach) should fall in this window - prioritise it, though older impact evidence can still
  be worth surfacing as background/pathway context even if it won't itself count toward the REF
  submission.
- Today's date is {today} - use it to judge "recent" relative to now, not any date baked into an
  example elsewhere in this prompt.

**REF Impact Definition**
Impact = an effect, change, or benefit to:
- Economy (jobs, growth, market adoption, revenue)
- Society (behavioral change, accessibility, quality of life improvement)
- Culture (public engagement, cultural heritage)
- Public Policy or Services (policy influence, service delivery improvements)
- Health (clinical outcomes, patient access, preventive measures)
- Environment (emissions reduction, conservation, sustainability)
- Quality of Life (wellbeing, safety, inclusion)

**REF 2029 Key Metrics**
1. **Reach**: Number, type, and geographic distribution of beneficiaries
   - Individual beneficiaries (students, patients, professionals)
   - Organizational beneficiaries (companies, government agencies, NGOs, communities)
   - Geographic scale (local, national, international)

2. **Significance**: Depth and importance of impact
   - Magnitude of change (% improvement, cost savings, lives affected)
   - Duration of impact (months to years)
   - Strategic importance to beneficiaries
   - Evidence of sustained change

3. **Evidence Quality**: 
   - Verifiable sources (peer review, publications, policy documents, testimonials)
   - Quantifiable metrics (funding secured, jobs created, policy changes adopted)
   - Independent corroboration (third-party validation, media coverage)

**Instructions**

1. **Task Generation**:
   - Generate ≤ {max_tasks} research tasks, each covering a DISTINCT impact domain or application area (don't split one domain across several tasks)
   - For each task, return a JSON object with:
     - "focus_area": The specific impact domain or application area
     - "search_queries": **4-6 high-precision queries that each target a DIFFERENT angle of evidence** within that focus area, collectively designed to uncover:
       - **Real-world deployments** with quantifiable outcomes (% savings, jobs created, lives impacted)
       - **Beneficiary evidence** (who benefits, how many, geographic scope)
       - **Implementation details** (timelines, institutional involvement, stakeholder collaboration)
       - **Independent verification** (academic papers, policy documents, media coverage, case studies)
       - **A varied external-source mix**: use distinct queries for journal or conference publications, funder/project-consortium records, government/regulator or professional-body material, named beneficiary/partner evidence, and independent media where relevant. Include every source type that can substantiate the claim; do not restrict discovery to a fixed list of domains.
       - **Distinct sub-populations, sectors, regions, or organisations** within the focus area
       - **Recent examples** (last 2-3 years unless specified otherwise, today is {today})

1a. **Underpinning Research Queries (required within every task)**:
   - Of the 4-6 queries in each task, **at least 1-2 must target the underpinning
     research itself** — the peer-reviewed papers, preprints, datasets, patents,
     or funded outputs the impact rests on — not the impact/deployment evidence.
   - These queries should be phrased to surface research-quality sources: add
     terms like "peer reviewed", "journal article", "preprint", "conference
     paper", "grant", "funded by", or use `site:` operators for independent
     research repositories/publishers (`site:researchgate.net`,
     `site:arxiv.org`, `site:ncbi.nlm.nih.gov`, journal/publisher domains,
     or a DOI lookup).
   - Never use `site:aston.ac.uk` (or any aston.ac.uk subdomain, including
     research.aston.ac.uk and publications.aston.ac.uk) in any query - no
     Aston-hosted source, including Aston's own repository copy of a paper,
     counts as independent evidence. Searching for one wastes search and
     extraction budget on results that will be discarded; find the
     publisher/journal/DOI copy or independent coverage instead.
   - External partner and beneficiary pages are useful search targets: look for
     project deliverables, implementation reports, annual reports, technical
     documentation, awards, professional-body publications, funder records,
     patents, standards, datasets and conference proceedings. Their own
     announcements may be used when they state a concrete, checkable outcome;
     do not exclude them merely because they are not a journal or newspaper.
   - Example underpinning-research queries: `"Paul Harper" Aston peer reviewed
     coherent Raman communications journal`, `Xtera Raman amplification EPSRC
     grant funded research paper`, `submarine cable capacity research
     site:arxiv.org`.

1b. **Institutional Affiliation Queries (required once, in the FIRST task only)**:
   - If the user prompt names specific researchers, include 1-2 queries PER NAMED RESEARCHER
     in the FIRST task (not every task, and not 1-2 total when multiple researchers are named -
     each one needs their own affiliation-history queries, since finding one person's Aston
     start date says nothing about another's) aimed specifically at discovering WHEN each named
     researcher joined, left, or was affiliated with Aston or another institution - not their
     impact or research output, their career/employment timeline.
   - When several researchers are named (a research group or multi-author case study), this
     alone can use most of the first task's query budget - that's expected and correct, not
     wasteful, since each researcher's attribution window is independently required for the
     report to distinguish Aston's institutional role per person later.
   - Never use `site:aston.ac.uk` for this either - the same independence rule applies. Look
     instead for LinkedIn profiles, prior-employer staff pages noting a departure, appointment
     press releases, ORCID/Google Scholar affiliation history, or news coverage mentioning when
     they joined.
   - Example: `"Patricia Thornley" LinkedIn`, `"Patricia Thornley" joined Aston University
     professor`, `"Patricia Thornley" previously University of Manchester`, `"Andrew Ellis"
     Aston appointed professor photonics`.
   - This is required so the report can automatically state the researcher's Aston affiliation
     window without it having to be manually supplied - do not skip it even if the rest of the
     task is unrelated to career history.

2. **Diversity Rule (critical - read before writing queries)**:
   - No two queries in the same task may be paraphrases of each other. Before adding a query, check whether it would plausibly surface DIFFERENT source pages than the queries already listed for that task. If it would mostly return the same articles, drop it and pick a different angle instead.
   - **Reject this pattern** (these are the same query reworded three times and will all surface the same handful of articles):
     * "AI healthcare implementation 5000+ patients impact case study 2024"
     * "AI healthcare adoption metrics case study 2024"
     * "healthcare AI impact study 2024"
   - **Use this pattern instead** (each query points at a different slice of evidence - a different beneficiary group, geography, mechanism, metric type, or source type):
     * "hospital AI diagnostic tool improved patient outcomes quantified 2024"
     * "NHS trust AI rollout cost savings million 2024 case study"
     * "AI medical imaging diagnostic accuracy peer reviewed validation 2024"
     * "telemedicine AI underserved rural communities access impact 2024"
   - Within one task's query list, vary the geography, organisation, sector, and metric across queries rather than repeating the same one with different adjectives.

3. **Researcher/Partner Anchoring (critical — read before writing queries)**:
   - If the user prompt names specific researchers, academics, or partner organisations,
     **at least half of all search queries must include one of those named entities
     directly in the query string**.
   - Never generate queries that are purely thematic with no named-entity anchor when
     names are provided — such queries return generic industry articles that cannot be
     attributed to the specific research group.
   - Correct pattern (named-entity anchored):
     * `"Andrew Ellis" Aston optical fibre deployment impact`
     * `Xtera Raman amplification submarine network commercial deployment`
     * `"Paul Harper" Aston coherent Raman communications industry`
   - Wrong pattern (topic-only — will return any company in the field):
     * `coherent optics industry adoption 400G 2024`
     * `submarine cable capacity increase fibre pair 2024`

4. **Search Query Strategy**:
   - Combine specific keywords with outcome metrics:
     * "X improved by Y%" / "X saved Z million" / "X benefited N users"
     * "policy implemented" / "regulatory change" / "industry adoption"
     * "case study" / "impact report" / "white paper"
   - Use advanced operators for academic/policy sources:
     * `site:.gov` / `site:.edu` / `site:researchgate.net`
     * Include recent dates relative to today ({today}) - e.g. this year and last year, not
       whatever hardcoded years happen to be in an example

4a. **Newest-first ordering (impact-evidence queries only, not underpinning-research
    queries — research outputs can legitimately be much older)**:
   - Within each task's query list, put the queries most likely to surface the last 1-2
     years of evidence FIRST, and older/broader-timeframe queries LAST. The pipeline's
     search ranking already prioritises newer sources when choosing which results to
     scrape, but ordering the queries themselves the same way means the freshest angles
     get explored before less specific ones dilute the query budget.
   - Later replanning rounds (chasing a still-unmet target count) may broaden beyond the
     last 1-2 years if recent evidence is scarce - don't keep repeating recent-only
     queries once they've stopped surfacing anything new.

5. **Output Format** - JSON ONLY:

json
{{
  "tasks": [
    {{
      "focus_area": "Healthcare AI Implementation",
      "search_queries": [
        "hospital AI diagnostic tool improved patient outcomes quantified 2024",
        "NHS trust AI rollout cost savings million 2024 case study",
        "AI medical imaging diagnostic accuracy peer reviewed validation 2024",
        "telemedicine AI underserved rural communities access impact 2024",
        "AI clinical decision support regulatory approval MHRA FDA 2024",
        "low-income country AI healthcare deployment beneficiaries 2024",
        "AI healthcare workforce training adoption professional practice 2024",
        "AI diagnostic tool international deployment WHO partnership 2024"
      ]
    }},
    {{
      "focus_area": "Policy Influence through Research",
      "search_queries": [
        "university research cited government white paper policy change 2024",
        "academic evidence influenced parliamentary committee report 2024",
        "research-informed regulation industry standard adopted 2024",
        "think tank research shaped local council policy decision 2024"
      ]
    }}
  ]
}}
"""

# ════════════════════════════════════════════════════════════════════════════
# REF CASE STUDY EXTRACTION PROMPT
# ════════════════════════════════════════════════════════════════════════════

REF_EXTRACTION_PROMPT = """
You are a senior research analyst extracting REF 2029-compliant impact case studies.

**User Prompt**:
<user_prompt>
  {user_prompt}
</user_prompt>

**Theme**: {theme_title}

**Task**
You are given MULTIPLE numbered articles below (see <articles>). Extract complete,
evidence-rich use cases demonstrating real-world impact matching REF 2029 standards
from ALL of them. Each article may yield zero, one, or several distinct findings -
process every article independently and do not let one article's content bleed into
another's findings. Every finding you output MUST include an "article_index" field
set to the integer number of the "=== ARTICLE N ===" label it came from - this is
mandatory and must exactly match one of the article numbers shown; never invent an
index or guess when unsure.

**REF 2029 Impact Criteria** ✓ MUST MEET ALL THREE:

1. **Reach**: Clearly identify beneficiaries and scale
   ✓ Number of direct/indirect beneficiaries (individuals, organizations, communities)
   ✓ Geographic scope (local/regional/national/international)
   ✓ Sector or industry affected (healthcare, policy, business, society, etc.)

2. **Significance**: Demonstrate meaningful, sustained change
   ✓ Quantifiable outcomes (% improvement, £/€ economic value, policy adoption)
   ✓ Timeframe of impact (duration of effect)
   ✓ Strategic importance to beneficiaries or society
   ✓ Evidence of behavioral/operational/policy change

3. **Evidence**: Verifiable, corroborated information
   ✓ Source documentation (case studies, white papers, academic publications, policy documents)
   ✓ Third-party corroboration (independent validation, media coverage, testimonials)
   ✓ Quantified metrics from credible sources
   ✓ No speculative or claimed-only impacts

**Strict Extraction Filters**

**REJECT if ANY of the following apply:**
- ✗ No quantifiable outcome metric (% improvement, $ value, # beneficiaries, policy changes) AND
  no genuine policy-document citation AND no stated real-world adoption/deployment fact. The
  exception to "needs a number" is narrow and specific: (a) a policy/report citation with a
  locatable `source_reference` and, where possible, a verbatim `direct_quote`, (b) a plainly
  stated adoption fact naming who deployed/adopted what (e.g. "Coventry City Council deployed the
  system on two junctions"), even without a number attached to it, or (c) a named decision-maker
  stating, in their own words, that they changed a specific decision, ruling, policy position, or
  conclusion because of the research/advice (e.g. "the National Data Guardian states that Wilson's
  argument became a central plank of the view I provided to the committee"). (c) matters
  specifically for advisory/consultancy impact - ethics advice, legal/policy expertise, expert
  testimony - where the research's entire product is a change in someone's reasoning or ruling, not
  a deployed system; do not require a deployment-style fact from this kind of evidence just because
  no system was deployed. Being merely reported on, profiled, "featured in", demonstrated at a
  conference/event, or covered by media does NOT satisfy this exception on its own - that is
  awareness/promotion, not evidence of adoption, influence, or a policy citation, and must be
  rejected unless it also states a quantified reach (audience size, listener/viewer count, attendee
  count) or accompanies a genuine deployment/influence fact elsewhere in the same source
- ✗ Purely academic or theoretical (no beyond-academia impact whatsoever)
- ✗ Pure vendor marketing with no real implementation evidence
- ✗ Internal-only impacts (no external beneficiary at all)
- ✗ Contradicts REF exclusions: student teaching impacts are INCLUDED; pure academic knowledge is EXCLUDED
- ✗ Involves organisations not named in the user prompt AND the article makes no reference to
  the named researchers, institutions, or partner organisations — generic industry news about
  unrelated companies does not constitute discoverable evidence for this case study even if
  topically similar
- ✗ A source hosted on an aston.ac.uk domain (main site, news, research repository, publications
  repository, staff profile pages, or any other aston.ac.uk subdomain) whose claim — the same
  beneficiary, outcome, or fact — is also stated by a non-Aston source found for this case study.
  When both exist, extract from the non-Aston source and discard the Aston-hosted duplicate,
  including when the duplicate is Aston's own repository copy of a paper that is also available
  via the publisher/journal/DOI. See "Aston-hosted sources" below for when an aston.ac.uk source
  may still be extracted.

**ACCEPT if ALL of the following apply:**
✓ Topically relevant to the theme and research area (same subject field)
✓ At least one identifiable external beneficiary (organisation, sector, community)
✓ At least one quantifiable outcome metric (%, £, users, policy adoption, or similar) OR a genuine
  policy-document citation (`source_reference` page/section, ideally with a verbatim
  `direct_quote`) OR a plainly stated adoption/deployment fact naming who did what OR a named
  decision-maker's own testimony that they changed a decision/ruling/policy position because of
  the research (the last of these applies to ethics/legal/policy advisory impact specifically - see
  REJECT exception (c) above) - not mere media coverage, a magazine feature, or a conference demo
  with no reach figure, deployment fact, or decision-maker testimony attached (see REJECT above)
✓ Real implementation evidence: an actual, already-happened deployment, adoption, or influenced
  decision (not only planned or projected, and not just "was covered by" or "was featured in")
✓ Beyond-academia impact (external beneficiary exists)
✓ Connected to the named researchers, institutions, or partner organisations in the user prompt
  — OR a source that directly attributes or cites findings from that research group

Note: You do NOT need to verify that this specific university caused the impact directly.
However, the evidence must be linkable to the named researchers or their named partners.
Do not extract impact from companies or organisations that have no stated connection to the
research group — such records cannot support a REF case study and will be discarded.

**Special case — Aston-hosted sources**: an aston.ac.uk-hosted source (news article, press
release, staff profile, research repository entry) may be extracted only when it states a
beneficiary, outcome, or fact that no non-Aston source in this case study's evidence states.
It is never independent corroboration — mark its evidence as institutional, not third-party,
for the Evidence Quality/Independent corroboration criterion above — but a genuinely unique
fact from Aston's own site is still usable evidence, not a reason to discard the finding
outright. If a non-Aston source is later found stating the same fact, that source takes
priority: use it in place of the Aston-hosted one rather than keeping both.

**Special case — institutional affiliation records**: if a source states WHEN a named
researcher joined, left, or was affiliated with Aston or another institution (a LinkedIn-style
career summary, an appointment announcement, an author bio, a prior employer's staff page
noting a departure) but has NO qualifying impact evidence otherwise, still extract it as a
finding of its own rather than discarding the source. This does not need an external
beneficiary, a quantifiable metric, or beyond-academia impact - none of the REJECT/ACCEPT
criteria above apply to it. Set `use_case_type` to exactly "Researcher Affiliation Record",
`use_case_name` to something like "Institutional affiliation record: [Researcher Name]", and
populate `affiliation_note` with the verbatim statement (see field description below). This
exists purely so the report can automatically discover and state a researcher's Aston
affiliation window instead of requiring it to be manually supplied - it is metadata, not impact
evidence, and must never be presented in the final report as evidence of impact or reach.

**Special case — independent underpinning research**: retain a non-Aston peer-reviewed
paper, preprint, dataset, patent record, or funder/grant output that is clearly linked to
the named researcher, even where it does not itself demonstrate a beyond-academia outcome.
This is **Underpinning Research**, not an impact claim. Set `use_case_type` to exactly
"Underpinning Research", `content_type` to `peer_reviewed`, state the research finding in
`use_case_description`, and leave `performance_impact` blank unless the source itself
states a real-world outcome. Do not describe it as reach, significance, adoption, or REF
impact unless the source proves that separately. This permits the final case study to show
the independent research base while keeping impact evidence distinct.

**Extraction Fields**

For each valid impact case study, extract:

1. **use_case_name**: 
   - One-sentence title capturing the impact
   - Example: "AI Diagnostic Tool Improved Cancer Detection in 500+ Patients"

2. **company**:
   - Implementing organization (hospital, company, government agency, university)
   - Use the organisation's current, formal registered or trading name as stated in the source. If the source itself notes the organisation was previously known by a different name, or refers to it by an abbreviation alongside its full name, use the full current name, not the older name or abbreviation alone
   - Example: "NHS Trust Hospital / Stanford University / Government Ministry"

3. **performance_improvement_category**: 
   - Primary impact domain (choose one):
     * Economic: job creation, market adoption, cost savings, revenue growth, investor confidence
     * Health: clinical outcomes, patient access, preventive care, quality of life
     * Social: behavioral change, accessibility, inclusion, quality of life, safety
     * Environmental: emissions reduction, sustainability, conservation
     * Policy: regulation change, government adoption, service delivery improvement
     * Cultural: public engagement, heritage preservation, social awareness
     * Education: learning outcomes, student progression, accessibility

4. **industry**: 
   - Industry/sector affected
   - Example: "Healthcare", "Finance", "Government", "Manufacturing", "Education"

5. **use_case_type**:
   - The concrete REF impact mechanism
   - Examples: "Policy Influence", "Clinical Adoption", "Industry Adoption", "Professional Practice Change", "Public Engagement"

6. **performance_impact**:
   - Specific metric with magnitude, where the source states one
   - **Always include the currency symbol (£, €, $, etc.) with any monetary figure. Never write a monetary amount without its symbol (e.g. write "£5.2 million", not "5.2 million").**
   - **Only include numeric figures that are explicitly stated in the source text. Do not invent, estimate, or extrapolate numbers.**
   - If the source has no numeric figure but does state a policy/report citation, describe the
     citation itself as the impact (e.g. "Research cited in [Document Name], Section 3.2" or
     "Findings referenced in DfT Biomass Strategy consultation response") rather than leaving the
     field vague or inventing a number to fill it
   - Examples:
     * "40% reduction in diagnostic time"
     * "£5.2 million cost savings"
     * "500+ healthcare providers adopted"
     * "Policy implemented affecting 2 million citizens"
     * "3-year sustained adoption rate of 85%"

7. **use_case_description**: 
   - 100-200 word summary explaining:
     * What was implemented
     * Who benefited and how many
     * Measurable outcome achieved
     * Duration/sustainability of impact
     * Evidence of beyond-academia benefit
   - Example structure:
     "University researchers developed AI diagnostic tool adopted by NHS Trust.
      Tool trained on 100K medical images with 95% accuracy. Deployed across 12 hospital
      departments from 2022-2024. Impact: 500+ additional cancer diagnoses per year,
      detected 2-3 weeks earlier on average, improving treatment outcomes. ROI: £2M
      saved vs. manual screening. Sustained adoption: 8 of 10 hospitals continued use
      post-pilot, indicating credibility and organizational value."

8. **source**:
   - Exact URL or named source reference used as evidence
   - Prefer independent or beneficiary-authored sources over vendor marketing
   - Real REF case studies routinely corroborate impact with non-URL sources —
     a named testimonial or letter ("Letter from the Director of Operations,
     [Organisation]"), a patent number, an official statistic/report, or a
     policy document citation. Capture these exactly as named in the article;
     do not discard a strong claim just because it lacks a clickable URL

9. **geography** and **country**:
   - geography must use the schema region values
   - country should name the specific country if stated

10. **significance_score** (1-10):
    - Use this internally to judge quality, but output the value as **relevance_score** only if the schema includes it
    - Judge magnitude and evidence strength relative to what is plausible for
      this research's own subject and beneficiary population. REF panels score
      reach/significance against the context and audience the research
      addresses, not against a universal geographic ladder - a single-borough
      policy reform, a national professional-body guideline change, and a
      genuinely international rollout can each score 9-10 if the evidence
      shows it is the maximum plausible reach/significance for that specific
      impact, and each can equally score 1-3 if the evidence is thin,
      regardless of scale. A real REF2021 4* case study can rest entirely on
      one country's inquest system or one London borough's community
      programme - narrower footprint alone must never cap the score.
    - 1-3: Minor impact, weak or unstated evidence, no clear beneficiary
    - 4-6: Moderate impact for its context, credible but incomplete evidence
    - 7-8: Major impact for its context, strong and specific evidence
    - 9-10: Transformative impact for its context (the maximum plausible reach
      and significance for this subject/beneficiary population), excellent,
      well-corroborated evidence
    - State the geographic/organisational scale (local, regional, national,
      international) as a factual description of the reach in the extracted
      fields - it is not itself a scoring input, and must not be used to infer
      or justify the score in either direction

11. **use_case_date**:
    - When impact was achieved/deployed (YYYY-MM-DD)
    - Not announcement date; not future date
    - If range: use start date of implementation
    - Use only the precision actually stated in the source: "YYYY-MM" if only month and year are known, "YYYY" if only the year is known
    - If the source gives no date information at all, output null. Do not invent, estimate, or default to a date (e.g. the 1st of a month or year) that is not stated or clearly inferable from the source text

12. **article_index** (REQUIRED, integer):
    - The number of the "=== ARTICLE N ===" label (see <articles> below) this specific
      finding was extracted from. Must exactly match one of the provided article
      numbers - never invent, omit, or guess this value. Every finding must carry
      the correct index of its own source article, even when multiple articles
      describe similar or related topics.

**Processing Steps**

1. **Candidate Identification**: Scan article for mentions of:
   - Specific outcomes with numbers (%, £, beneficiary count)
   - Named organizations and beneficiaries
   - Implementation evidence (deployment, adoption, policy change)
   - Verifiable sources or evidence claims

2. **Reach-Significance Validation**: For each candidate, verify:
   - Can you identify WHO benefited? (organization, geography, population type)
   - Can you quantify SCALE? (number of beneficiaries, budget, duration)
   - Is impact BEYOND academia? (external user/organization/policy benefit)
   - Is impact SUSTAINED? (evidence of continued use/benefit beyond pilot)

3. **Evidence Quality Check**: Verify sources are:
   - Citable (specific URL, publication, or named document)
   - Independent where possible (third-party validation)
   - Recent (within 2-3 years of today's date: {today})

4. **Output**: Return VALID JSON array with NO explanatory text.

**Example Output** (showing expected JSON structure):

json
[
  {{
    "use_case_name": "AI Diagnostic System Improves Cancer Detection in 500+ NHS Patients",
    "company": "University of Manchester + NHS Trust Hospital",
    "performance_improvement_category": "Health Impact",
    "industry": "Healthcare",
    "use_case_type": "Clinical Adoption",
    "performance_impact": "40% faster diagnosis; 500+ additional cancer diagnoses per year; £2 million cost savings over 18 months",
    "use_case_description": "University researchers developed AI diagnostic system trained on 100,000 medical images with 95% accuracy. System deployed across 12 NHS hospital departments from 2022-2024. Impact: enabled detection of 500+ additional cancers per year, with earlier diagnosis improving treatment outcomes. Documented ROI: £2 million cost savings vs. manual screening over 18 months. Sustained adoption: 8 of 10 pilot hospitals continued deployment post-pilot period, indicating strong organizational value and clinical credibility.",
    "source": "https://example.org/nhs-ai-case-study-2024",
    "geography": "EMEA",
    "country": "United Kingdom",
    "use_case_date": "2022-03",
    "article_index": 1
  }},
  {{
    "use_case_name": "Research Evidence Drove Policy Change on Renewable Energy Adoption",
    "company": "European Union Commission + University Research Consortium",
    "performance_improvement_category": "Public Policy or Services Impact",
    "industry": "Environment & Sustainability",
    "use_case_type": "Policy Influence",
    "performance_impact": "EU policy affecting 450+ million citizens; 40% emissions-reduction target by 2030; 40+ government citations",
    "use_case_description": "Multi-year research program studied renewable energy scaling in 5 EU countries. Documented 15% cost reduction through distributed solar adoption. Research findings directly cited in EU Green Deal policy framework (2023). Member states now required to increase renewable energy targets by average 5% per annum. Estimated impact: avoiding 200+ million tonnes CO2 by 2030. Evidence: official EU policy document, 40+ government citations of research.",
    "source": "EU Green Deal Policy Document 2023",
    "geography": "EMEA",
    "country": "",
    "use_case_date": "2023",
    "article_index": 2
  }}
]

**CRITICAL REMINDERS**
✓ Only return VALID JSON (no text before/after)
✓ Every case must have Reach + Significance + Evidence
✓ Include quantifiable outcomes (no vague "improved efficiency")
✓ Sources must be specifically attributable and verifiable — a working URL, a
  named publication/report, or a clearly identified testimonial (e.g. "Letter
  from the CTO of X") — not a vague or generic reference
✓ Impact must be beyond-academia (external beneficiary required)
✓ Think REF: Would a REF panel accept this as evidence of real-world impact?
✓ Every finding's "article_index" must exactly match the article it was found in -
  this is how your findings get attributed back to the correct source URL, so an
  incorrect index causes a finding to be misattributed to the wrong source.

Use ONLY the field names in the schema below (plus the required "article_index" field
described above); do not output alternate keys such as organisation, impact_type,
sector, beneficiary_reach, quantitative_outcome, impact_narrative, evidence_sources,
reach_geographic, or date_implementation.

<schema>
{schema}
</schema>

<articles>
{articles}
</articles>
"""

# ════════════════════════════════════════════════════════════════════════════
# REF RELEVANCE CHECK PROMPT
# ════════════════════════════════════════════════════════════════════════════

REF_RELEVANCE_CHECK_PROMPT = """
You are screening potential evidence for a REF impact case study. Your job is to
judge whether a use case is worth keeping as a piece of DISCOVERY evidence —
something a researcher could later use to demonstrate real-world impact in their
field. You are NOT verifying that this specific university caused the impact;
that attribution step is done later by the researcher.

**Calibration note**: this score feeds a discovery draft that the academic lead
will manually review before anything goes into a REF submission - it is not the
final report itself. Err toward the higher of two plausible scores rather than
the lower one. Only score a criterion low when it is clearly and obviously
absent from the text, not merely when it isn't stated with total certainty.

**Theme**: {theme_title}
**Research context**: {user_prompt}

**Use case to evaluate**:
{use_case}

**Score on five criteria:**

1. **Topical relevance** — Is this about the right subject area (the theme and
   research context above)? Score high if it is clearly in the same field.

2. **Real-world impact** — Is there evidence of actual deployment, adoption,
   policy change, or measurable benefit? Reject purely theoretical or planned
   work, marketing claims with no implementation evidence, or purely academic
   knowledge outputs with no external beneficiary. Being merely reported on,
   profiled, "featured in", or demonstrated at a conference/event is NOT itself
   real-world impact - score this low unless the source also states a
   quantified reach (audience size, listeners, attendees) or a genuine,
   already-happened deployment/adoption fact.

3. **Identifiable beneficiary** — Can you tell who benefited externally (a
   company, government body, community, patients, industry sector)? Internal
   academic-only impact does not count.

4. **Quantifiable outcome** — Is there at least one concrete metric: a
   percentage, £ value, number of beneficiaries, policy adopted, or similar?
   Estimated or approximate figures are acceptable. Pure qualitative statements
   with no numbers score lower but are not automatic rejections.

5. **Named-party connection** — Does this use case involve one of the named
   researchers, institutions, or partner organisations from the research context
   above? Score HIGH if the use case directly names or credits them. Score MEDIUM
   if the connection is indirect but traceable (e.g. the technology they developed
   is deployed by a named partner). Score LOW if the use case involves entirely
   different organisations with no stated link to the named parties — such records
   cannot be used in a REF case study for this research group even if topically
   similar.

**Scoring guide**:
- 8-10: Clearly relevant, real implementation, named beneficiaries, quantified
        outcome, AND directly involves a named researcher, institution, or partner
- 6-7:  Relevant, with real-world deployment/adoption evidence and at least a
        plausible, traceable connection to a named party (direct or indirect).
        The metric can be approximate or only partially stated - a clear
        real-world outcome matters more here than a precise number, and a
        connection that's reasonably inferable (e.g. the deploying
        organisation is using the named researcher's method/tool, even if the
        article doesn't repeat their name) still counts as traceable.
- 4-5:  Relevant topic but no discernible connection at all to any named
        researcher, institution, or partner, OR no real-world evidence beyond
        a vague/planned claim — marginal; do NOT include as discovery evidence
- 2-3:  Tangentially related or involves entirely unrelated organisations
- 0-1:  Off-topic, purely academic, speculative, or vendor marketing only

**Important**: A use case about a company or organisation with no plausible link
of any kind to the named researchers or partners - not even an indirect one
through their method, tool, or technology - should generally score 5 or below.
But if the connection is reasonably inferable rather than explicit, treat it as
indirect/traceable (6-7 territory), not an automatic cap at 5.

Set `is_relevant` to **true** only if the score is 6 or above.

**Output VALID JSON ONLY**:

json
{{
    "relevance_score": <0-10 integer>,
    "is_relevant": <true if score >= 6, else false>,
    "reach_verified": <true|false>,
    "significance_verified": <true|false>,
    "evidence_verified": <true|false>,
    "beyond_academia": <true|false>,
    "attribution_verified": false,
    "reasoning": "<40-word explanation of score>"
}}
"""

# ════════════════════════════════════════════════════════════════════════════
# COMBINED CREDIBILITY + RELEVANCE CHECK PROMPT
# ════════════════════════════════════════════════════════════════════════════
# One call instead of two per extracted use case (previously CREDIBILITY_CHECK_PROMPT
# and REF_RELEVANCE_CHECK_PROMPT were sent to the LLM separately). This runs once per
# every extracted candidate - not just accepted ones - so merging it is the single
# biggest easy reduction in per-run API calls/tokens. The two rubrics are kept fully
# separate within the prompt (distinct headed sections, distinct score fields) so
# neither job's reasoning is meant to bleed into the other's score.

REF_CREDIBILITY_RELEVANCE_CHECK_PROMPT = """
You are screening potential evidence for a REF impact case study. You have two
separate jobs on this single use case - keep them distinct, do not let one
job's reasoning influence the other's score.

JOB 1 - CREDIBILITY: judge whether the article credibly supports the use case
as an accurate factual claim.
JOB 2 - RELEVANCE: judge whether the use case is worth keeping as DISCOVERY
evidence for this REF theme - something a researcher could later use to
demonstrate real-world impact in their field. You are NOT verifying that this
specific university caused the impact; that attribution step is done later by
the researcher.

**Calibration note**: both scores feed a discovery draft that the academic
lead will manually review before anything goes into a REF submission - this is
not the final report itself. Err toward the higher of two plausible scores
rather than the lower one. Only score a criterion low when it is clearly and
obviously absent from the text, not merely when it isn't stated with total
certainty.

**Theme**: {theme_title}
**Research context**: {user_prompt}

**Article** (may be truncated):
{article}

**Use case to evaluate**:
{use_case}

---

**JOB 1 - Credibility.** Analyse:
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

Credibility score guidelines:
- 0-2: Highly questionable, no credible source, vague claims
- 3-4: Some concerns, limited evidence, possible hearsay, or a date mismatch against the article
- 5-6: Moderately credible, some specific details but limited evidence
- 7-8: Good credibility, specific details and evidence provided
- 9-10: Highly credible, first-hand information with concrete evidence

**JOB 2 - Relevance.** Score on five criteria:

1. **Topical relevance** — Is this about the right subject area (the theme and
   research context above)? Score high if it is clearly in the same field.
2. **Real-world impact** — Is there evidence of actual deployment, adoption,
   policy change, or measurable benefit? Reject purely theoretical or planned
   work, marketing claims with no implementation evidence, or purely academic
   knowledge outputs with no external beneficiary. Being merely reported on,
   profiled, "featured in", or demonstrated at a conference/event is NOT itself
   real-world impact - score this low unless the source also states a
   quantified reach (audience size, listeners, attendees) or a genuine,
   already-happened deployment/adoption fact.
3. **Identifiable beneficiary** — Can you tell who benefited externally (a
   company, government body, community, patients, industry sector)? Internal
   academic-only impact does not count.
4. **Quantifiable outcome** — Is there at least one concrete metric: a
   percentage, £ value, number of beneficiaries, policy adopted, or similar?
   Estimated or approximate figures are acceptable. Pure qualitative statements
   with no numbers score lower but are not automatic rejections.
5. **Named-party connection** — Does this use case involve one of the named
   researchers, institutions, or partner organisations from the research context
   above? Score HIGH if the use case directly names or credits them. Score MEDIUM
   if the connection is indirect but traceable (e.g. the technology they developed
   is deployed by a named partner). Score LOW if the use case involves entirely
   different organisations with no stated link to the named parties — such records
   cannot be used in a REF case study for this research group even if topically
   similar.

Underpinning-research exception: A non-Aston peer-reviewed output, preprint,
dataset, patent, or funder record that directly names the researcher or research
group is relevant as Underpinning Research even if it has no external beneficiary
or impact metric. Score it 6-7 when that link is explicit, but do not call it
direct impact evidence.

Relevance scoring guide:
- 8-10: Clearly relevant, real implementation, named beneficiaries, quantified
        outcome, AND directly involves a named researcher, institution, or partner
- 6-7:  Relevant, with real-world deployment/adoption evidence and at least a
        plausible, traceable connection to a named party (direct or indirect).
        The metric can be approximate or only partially stated - a clear
        real-world outcome matters more here than a precise number, and a
        connection that's reasonably inferable (e.g. the deploying
        organisation is using the named researcher's method/tool, even if the
        article doesn't repeat their name) still counts as traceable.
- 4-5:  Relevant topic but no discernible connection at all to any named
        researcher, institution, or partner, OR no real-world evidence beyond
        a vague/planned claim — marginal; do NOT include as discovery evidence
- 2-3:  Tangentially related or involves entirely unrelated organisations
- 0-1:  Off-topic, purely academic, speculative, or vendor marketing only

**Important**: A use case about a company or organisation with no plausible link
of any kind to the named researchers or partners - not even an indirect one
through their method, tool, or technology - should generally score 5 or below.
But if the connection is reasonably inferable rather than explicit, treat it as
indirect/traceable (6-7 territory), not an automatic cap at 5.

Set `is_relevant` to **true** only if relevance_score is 6 or above.
Set `is_credible` to **true** only if credibility_score is 6 or above.

**JOB 3 - REF evidence admission.** A finding is REF-ready only where the
visible source itself verifies BOTH reach and significance. Do not treat a
planned benefit, a vendor claim, a paper merely describing a method, or a
number with no named beneficiary as verified impact. Mark `reach_verified`
true only when the source states who benefited plus a scale (number, coverage,
geography, organisations, or equivalent). Mark `significance_verified` true
only when it states a material outcome or change (for example a policy adopted,
clinical/practice change, cost/health/environmental outcome) with supporting
evidence. These flags must be false when you are inferring either element.

**Output VALID JSON ONLY** - a single object with both jobs' results:

json
{{
    "credibility_score": <0-10 integer>,
    "is_credible": <true|false>,
    "credibility_reasoning": "<brief explanation of the score, explicitly stating whether the source names the specific organisation/product in the use case, and whether use_case_date matches the article's actual date evidence>",
    "relevance_score": <0-10 integer>,
    "is_relevant": <true if relevance_score >= 6, else false>,
    "relevance_reasoning": "<40-word explanation of relevance score>",
    "reach_verified": <true only when beneficiary and scale are explicit>,
    "significance_verified": <true only when a material outcome/change is explicit>
}}
"""

# ════════════════════════════════════════════════════════════════════════════
# REF IMPACT SUMMARY PROMPT (For generating REF-compliant summaries)
# ════════════════════════════════════════════════════════════════════════════

REF_IMPACT_SUMMARY_PROMPT = """
You are writing an impact summary aligned with REF 2029 standards.

Your task: Condense an impact case study into a 100-word REF-compliant summary.

**Summary Structure** (REF 2029):
1. Sentence 1-2: What was achieved and who benefited (beneficiary + metric)
2. Sentence 2-3: How it was achieved (implementation approach)
3. Sentence 3-4: Magnitude and reach (quantified outcome, geographic scope)
4. Sentence 5-6: Evidence and sustainability (verifiable outcomes, duration)

**Example Template**:
"[University] developed [tool/approach] to [solve problem] for [beneficiary type].
Deployed across [scale/geography], achieving [quantified outcome]. Implementation
involved [method], with evidence from [source]. Impact sustained over [timeframe],
benefiting [number/type] [beneficiary], with continued adoption to date."

**Word Limit**: 100 words maximum (REF 2029 guideline)

**Impact Case Study to Summarize**:
{impact_case_data}

**Output**: Plain text summary (no JSON, no markdown)
"""

REF_CASE_STUDY_SYNTHESIS_PROMPT = """
You are a senior REF impact case study editor. Write a REF-worthy impact case study
from the extracted evidence below. The output must be a polished Markdown report,
not JSON.

User prompt:
{user_prompt}

Theme:
{theme_title}

Researcher Aston affiliation windows (may be empty if none are known or found):
{researcher_affiliations}
Lines marked CONFIRMED were manually verified by a human - state them as fact.
Lines marked "FOUND DURING SEARCH" were pulled from a search result automatically and were
NOT independently verified - present these as a likely/reported affiliation window with the
source named, and explicitly note it should be confirmed by the academic team before
submission, rather than stating it with the same certainty as a CONFIRMED line.

Configured sections:
{impact_sections}

Extracted impact evidence:
{impact_evidence}

Write in the style of a strong UK REF impact case study. It must be better than a
list of findings: build a coherent argument that shows how research led to
change beyond academia. Calibrate tone against real 4-star REF case studies:
they state claims in short, blunt, declarative sentences anchored to exact
figures, named organisations, and date ranges (e.g. "Oslo Airport (19.5 million
passengers, Jan-Oct 2013) deployed..."), not academic hedging like "it is
suggested that" or "may have contributed to".

Required structure:

# {theme_title}

## 1. Summary of the Impact
- 90-130 words.
- State the impact claim, external beneficiaries, domains of impact, and the
  strongest reach/significance evidence.
- Do not use generic filler. Do not invent numbers.

## 2. Underpinning Research
- This section is about the RESEARCH itself, not the impact it led to - keep it
  strictly separate from Section 4. Draw primarily on evidence items whose
  `content_type` is `peer_reviewed`, `policy`, or `other`. Do NOT use
  `press_release` or `news` items as the basis for a research claim in this
  section - a press release or news article can describe impact (Section 4) but
  is not itself evidence of the underpinning research; if the only evidence for
  a claimed research output is a press release, say so explicitly as an
  evidence gap rather than treating the press release as if it were the paper.
- Explain what research insight, method, dataset, tool, intervention, or body of
  expertise underpinned the impact.
- Include dates, named researchers with role/tenure period where stated,
  institutions, research outputs, and quality markers when available.
- Cite funders, grant codes, or fellowship/award amounts exactly as given in the
  evidence (e.g. "EPSRC Grant GR/123456/01", "£65K Enterprise Fellowship,
  2019-2020") — REF panels treat this as core proof of research provenance.
  Never invent a grant code, amount, or date that is not stated in the evidence.
- Quality markers can include citation counts, peer-reviewed venues, patents
  citing the work, or independent replications, where stated in the evidence.
- **Aston's institutional role vs. each individual academic's role**: for any
  named researcher whose Aston affiliation window is supplied above, state
  explicitly which parts of the underpinning research were produced while
  that researcher was at Aston versus before/after their window - do this
  separately per researcher when more than one is named. Do not assume
  research is attributable to Aston by default for a researcher whose window
  isn't provided, or when a claim's date falls outside their stated window -
  flag it instead as "attribution to Aston needs verification" rather than
  silently crediting Aston.
- **Citations and direct quotes**: where the evidence states the research was
  cited in, referenced by, or informed a policy/document/decision, use the
  evidence item's `direct_quote` field verbatim (in quotation marks) so a
  reviewer can see the exact wording without re-reading the whole source. Do
  NOT also state the source_reference/page/section location in this prose -
  the appended References table lists the exact location for every source, so
  repeating it here just interrupts the narrative. If a citation is claimed
  but no `direct_quote` is available in the evidence, mark it as an evidence
  gap rather than paraphrasing an unverified citation as if it were confirmed.
- If the evidence is incomplete, state exactly what would need to be supplied by
  the academic team.

## 3. References to the Research
- List up to 10 research outputs or research-quality sources (use fewer if the
  evidence does not warrant it — quality over quantity).
- Use the provided reference_number values. Format every item as a hard-coded numbered reference, e.g. "1. [Title or source](URL) - why it supports research quality."
- State the source's `source_published_date` for every item (e.g. "Published: March 2023") -
  this is the date the source document itself was published, not the date of the
  impact/event it describes (`date_or_timeframe`); the two are often different and both
  matter for a reviewer checking currency and REF-period eligibility. If `source_published_date`
  is null, say "Publication date not stated" rather than omitting it or substituting the impact date.
- For each, explain why it helps establish research quality or attribution.
- Do not state the source_reference/page/section location in this prose - the
  appended References table gives the exact location for every source, so
  this section should stay focused on why each reference matters, not repeat
  where to find it.
- Mark weak or missing references as "evidence gap" rather than pretending they
  are complete.

## 4. Details of the Impact
Organise this section as a REF narrative, using these subheadings:

### Pathway from Research to Impact
Explain the causal route: research -> engagement/translation -> adoption/change.

### Reach
Identify who benefited, how many, where, and across what organisations/sectors.
Use only evidence present in the extracted data. Cite claims with bracketed
numbers such as [1] that match the numbered source list.
If the evidence contains eight or more distinct named organisations or
beneficiaries, open this subsection with a single sentence that states the
total count and geographic/sectoral spread before drilling into specifics —
this frames the breadth for the REF panel before the detail arrives.

### Significance
Explain the depth of change: policy/practice change, health/environment/economic
outcomes, cost/time savings, risk reduction, quality-of-life change, or strategic
importance. Use quantified outcomes where available and cite each major claim.
Where the evidence spans more than one impact domain (economic, social, health,
policy, environmental, cultural), make this explicit with bolded domain labels
(e.g. "**Economic impact:**", "**Social impact:**") rather than blending domains
into one undifferentiated paragraph — this mirrors how real REF case studies
(e.g. splitting "Economic Impact" / "Social Impact" / "Professional Services
Impact" into distinct labelled passages) present multi-domain impact.
If the evidence contains more than twelve distinct use cases, do not try to
mention every one; instead identify 4-6 strongest representative evidence
strands that together demonstrate breadth and depth, and note at the end of the
subsection how many additional corroborating sources support the same conclusion.

### Attribution to the Research
Separate what is evidenced from what still needs corroboration. Be careful not
to overclaim causality where the evidence only shows contribution.
For each named researcher whose Aston affiliation window is supplied above,
explicitly state which of the impact evidenced here occurred while that
researcher was at Aston versus after any stated departure - do this
separately per researcher when more than one is named. Impact occurring
after a stated departure should be flagged as needing verification of
Aston's residual institutional role (e.g. prior IP, continued grant-holding,
co-authorship agreed while at Aston) rather than credited to Aston by
default.

## 5. Sources to Corroborate the Impact
- Provide a source-by-source list using the exact provided reference_number
  values, e.g. "1. [Source](URL) - claim corroborated." For sources without a
  URL (a named testimonial, letter, patent, or official statistic), format as
  "1. [Source name/description] - claim corroborated" — do not invent a link.
- **Numeric order is mandatory and non-negotiable**: list items in strictly
  ascending reference_number order, top to bottom, with nothing else interspersed
  between them (Fiona's review specifically flagged out-of-order sources as
  hard to navigate). Do NOT split the list into separate headed groups by
  evidence type (e.g. a "**Policy documents:**" block followed by a
  "**Independent media:**" block) — that breaks ascending order the moment a
  later-numbered item belongs to an earlier group. Convey the evidence type
  as a short bold inline tag at the start of each item instead, e.g.
  "5. **[Policy document]** [Sciencewise evaluation](url) - claim corroborated...",
  so the type is still visible without needing separate group headers.
- State the source's `source_published_date` for every item, the same way as in
  References to the Research above (distinct from the impact date). Say
  "Publication date not stated" rather than omitting it or substituting the impact date.
- For each source, identify the claim it corroborates and whether it is
  independent, beneficiary-authored, academic, policy, testimonial, or uploaded
  evidence (use the inline bold tag above for this). A named testimonial letter
  from a specific role at the beneficiary organisation (e.g. "Letter from the
  Chief Technology Officer, [Company]") is strong REF-standard corroboration —
  flag it as such, not as weaker than a public URL.
- Where an evidence item has a `direct_quote`, include it verbatim in
  quotation marks next to the claim it corroborates so a reviewer can
  validate it without opening the source. Do not also state the
  source_reference/page/section location here - the appended References
  table lists the exact location for every source, so this list should stay
  focused on the claim and its corroboration, not repeat where to find it.
- When the evidence contains more than 12 use cases: prioritise the 12-15
  strongest and most varied corroborating sources, still as one continuous
  ascending-numbered list with inline type tags (never separate headed groups —
  see above). Do not list every source if many are redundant — note "X
  additional corroborating sources available on request" after the list instead.

## 6. REF Readiness Assessment
Create a Markdown table with columns:
Criterion | Current strength | Evidence found | Gaps to close before submission

Rows must include:
- Reach
- Significance
- Research attribution
- Independent corroboration
- Timeframe and eligibility
- Overall REF readiness

Quality rules:
- Use exact URLs/source names from the extracted evidence.
- Do not use unnumbered bullets for reference lists. References to the Research and Sources to Corroborate the Impact must be numbered lists.
- Every major reach, significance, and attribution claim must have a bracketed
  numbered citation matching Sources to Corroborate the Impact, or be marked
  as an evidence gap.
- Preserve numbers, dates, organisations, and beneficiaries.
- Do not fabricate missing metrics, citations, names, or sources.
- If evidence is weak, say so clearly and propose the missing evidence needed.
- Avoid marketing language. Write in confident but auditable REF prose.
- No fixed word-count target: let the evidence set the length. Cover every
  distinct use case, quote, citation, and reach/significance claim the
  extracted evidence supports, in enough detail for a reviewer to verify each
  one — then stop. This is a working discovery draft, not the final REF 2029
  submission (which has its own 2,200-word cap applied later, at finalisation,
  not here), so there is no benefit to trimming for length now.
- Do not pad with filler, restate the same claim in different words, or
  invent structure to reach any particular length.
- Do not compress or drop distinct evidence items to stay short. If the
  evidence set is large, use the "strongest representative strands" guidance
  in Reach/Significance above and the corroborating-sources cap in Section 5 -
  those are about avoiding an unreadable wall of near-duplicate mentions, not
  about hitting a word count.
"""

