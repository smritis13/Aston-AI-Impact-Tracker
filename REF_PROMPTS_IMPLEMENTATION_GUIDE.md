# REF 2029 Prompt Enhancement Implementation Guide

## Overview

This guide explains how to integrate REF 2029-aligned prompts into the Aston AI Research Tool to generate higher-quality impact case studies that meet Research Excellence Framework standards.

## What Changed

### New File
- `backend/core/llm/langchain/langgraph/ref_prompts.py` - Contains REF 2029-aligned prompts

### New Prompts Provided

1. **REF_PLANNING_PROMPT**
   - Guides task generation for finding REF-compliant case studies
   - Emphasizes Reach, Significance, and Evidence quality
   - Uses targeted search queries for quantifiable impacts
   - Aligns with REF 2029 standards

2. **REF_EXTRACTION_PROMPT**
   - Extracts case studies meeting ALL REF criteria
   - Validates: Reach (beneficiary scale), Significance (quantifiable outcome), Evidence (verifiable sources)
   - Rejects generic claims without specifics
   - Includes detailed validation filters
   - Produces structured JSON with significance scoring

3. **REF_RELEVANCE_CHECK_PROMPT**
   - Validates extracted case studies against REF standards
   - Scores 0-10 based on Reach, Significance, Evidence, Beyond-Academia criteria
   - Returns relevance assessment for filtering

4. **REF_IMPACT_SUMMARY_PROMPT**
   - Generates REF-compliant 100-word summaries
   - Follows REF 2029 summary structure
   - Ensures all key elements (who, what, outcome, evidence) are included

## How to Use

### Option 1: Quick Integration (Replace Existing Prompts)

In `backend/core/llm/langchain/langgraph/structured_report_generator.py`:

```python
# Add import
from core.llm.langchain.langgraph.ref_prompts import (
    REF_PLANNING_PROMPT,
    REF_EXTRACTION_PROMPT,
    REF_RELEVANCE_CHECK_PROMPT,
)

# Replace in __init__:
# Change from:
self.planning_prompt = PLANNING_PROMPT
self.base_extract_prompt = EXTRACTION_PROMPT

# Change to:
self.planning_prompt = REF_PLANNING_PROMPT
self.base_extract_prompt = REF_EXTRACTION_PROMPT
```

### Option 2: Gradual Integration (Parallel Prompts)

Run both old and new prompts, comparing outputs:

```python
from core.llm.langchain.langgraph.ref_prompts import REF_EXTRACTION_PROMPT
from core.llm.langchain.langgraph.prompts import EXTRACTION_PROMPT

# In structured_report_generator.py, add conditional:
if enable_ref_mode:
    extract_prompt = REF_EXTRACTION_PROMPT
else:
    extract_prompt = EXTRACTION_PROMPT
```

### Option 3: Custom Integration

Use REF prompts for specific themes or use cases:

```python
# Add to StructuredReportGenerator.__init__:
self.use_ref_prompts = use_ref_prompts or False

# In extraction step:
if self.use_ref_prompts:
    prompt = REF_EXTRACTION_PROMPT
else:
    prompt = EXTRACTION_PROMPT
```

## Key Improvements in REF Prompts

### 1. Reach Validation
**Before**: "Beneficiary type mentioned" ❌  
**After**: 
- Specific beneficiary count (e.g., "500+ patients")
- Geographic scope ("UK-wide", "European Union")
- Beneficiary type ("Healthcare professionals, patients, policy makers")

### 2. Significance Validation
**Before**: "Outcome mentioned" ❌  
**After**:
- MUST have quantified metric (%, £, user count, policy change)
- MUST be meaningful (>5% improvement or similar)
- MUST show sustained change (>12 months evidence)
- Examples given for each impact type

### 3. Evidence Quality
**Before**: "Source mentioned" ❌  
**After**:
- Independent verification (third-party sources)
- Specific citable URLs or publications
- Policy documents or media coverage
- No vendor marketing or unverifiable claims

### 4. Beyond-Academia Filter
**Before**: "External application mentioned" ❌  
**After**:
- MUST have external beneficiary (not just academic publication)
- MUST show real-world change (adoption, policy, behavioral change)
- Rejects: pure knowledge advancement, student-only impacts
- Accepts: teaching/professional practice impacts

## Output Examples

### REF-Compliant Extraction Output

```json
{
  "use_case_name": "AI Diagnostic Tool Improves Cancer Detection in 500+ NHS Patients",
  "organisation": "University of Manchester + NHS Trust Hospital",
  "impact_type": "Health",
  "sector": "Healthcare",
  "beneficiary_reach": "500+ patients across 12 hospital departments",
  "quantitative_outcome": "40% faster diagnosis (average 3 weeks earlier detection)",
  "impact_narrative": "University researchers developed AI diagnostic system trained on 100,000 medical images with 95% accuracy. System deployed across 12 NHS hospital departments from 2022-2024. Impact: enabled detection of 500+ additional cancers per year, with earlier diagnosis improving treatment outcomes. Documented ROI: £2 million cost savings vs. manual screening over 18 months. Sustained adoption: 8 of 10 pilot hospitals continued deployment post-pilot period, indicating strong organizational value and clinical credibility.",
  "evidence_sources": [
    "https://nhs-case-study.org/ai-diagnostic-2024",
    "Published in The Lancet Digital Health 2024"
  ],
  "reach_geographic": "National (UK-wide NHS adoption potential)",
  "significance_score": 8,
  "date_implementation": "2022-03-01"
}
```

### REF-Compliant Summary (100 words)

"University of Manchester developed an AI diagnostic system achieving 40% faster cancer detection. Deployed across 12 NHS hospital departments (2022-2024), the system detected 500+ additional cancers annually, with earlier diagnosis improving treatment outcomes. Implementation involved training the system on 100,000 medical images to 95% accuracy. Economic impact: £2 million cost savings vs. manual screening. Evidence: published in The Lancet Digital Health 2024. Sustainability: 8 of 10 pilot hospitals continued use post-pilot, demonstrating strong organizational value and clinical credibility for continued national deployment."

## Implementation Checklist

- [ ] Copy `ref_prompts.py` to backend directory
- [ ] Update `structured_report_generator.py` imports
- [ ] Modify prompt assignments in `__init__` method
- [ ] Test with sample queries focusing on:
  - [ ] Case studies with quantified outcomes
  - [ ] Clear beneficiary identification
  - [ ] Reach and significance metrics
  - [ ] Evidence quality verification
- [ ] Update frontend to show REF alignment badges/indicators
- [ ] Create admin dashboard to monitor REF score distribution
- [ ] Document for users: "How to Write REF-Compliant Case Studies"

## REF 2029 Word Count Guidelines

For reference when using these prompts:

| Section | REF 2021 | REF 2029 |
|---------|----------|---------|
| Summary of Impact | ~100 words | ~100 words |
| Underpinning Research | ~600 words | ~600 words |
| Details of Impact | ~750 words | ~1,500 words |
| Supporting Evidence | References only | References only (max 6) + 10 corroborating sources |
| **TOTAL** | **~1,450-2,000** | **~2,200 words max** |

## REF Impact Types

When using the prompts, impact_type should be one of:

- **Economic**: job creation, market adoption, cost savings, revenue growth, investor confidence
- **Health**: clinical outcomes, patient access, preventive care, quality of life improvement
- **Social**: behavioral change, accessibility, inclusion, safety, quality of life
- **Environmental**: emissions reduction, sustainability, conservation
- **Policy**: regulation change, government adoption, service delivery improvement
- **Cultural**: public engagement, heritage preservation, social awareness
- **Education**: learning outcomes, student progression, accessibility

## Testing & Validation

### Test Case 1: Strong REF Case Study
**Input**: "Healthcare AI tool adopted by 500+ NHS patients with 40% faster diagnosis"  
**Expected**: ✅ Full extraction with significance_score 8-10

### Test Case 2: Weak Case Study (Missing Reach)
**Input**: "Company A used AI tools to improve efficiency"  
**Expected**: ❌ Rejected - no quantified beneficiary count

### Test Case 3: Weak Case Study (Purely Academic)
**Input**: "Researchers published findings on AI applications"  
**Expected**: ❌ Rejected - no beyond-academia impact

### Test Case 4: Policy Impact
**Input**: "Research influenced EU Green Deal policy affecting 450+ million citizens"  
**Expected**: ✅ Full extraction with significance_score 9-10

## Monitoring Impact Quality

After integration, track in dashboard:

```
Average Significance Score: [target: 7+]
% with Quantified Outcomes: [target: 95%+]
% with Clear Beneficiary Reach: [target: 100%]
% with Verifiable Evidence: [target: 90%+]
% REF-Compliant: [target: 85%+]
```

## References

- **REF 2029 Guidance**: https://2029.ref.ac.uk/guidance/section-6-engagement-and-impact-guidance/
- **REF 2021 Impact Case Studies**: https://results2021.ref.ac.uk/impact
- **UK Research & Innovation**: https://www.ukri.org/

## Support

For questions about REF standards or implementation:
1. Refer to official REF 2029 guidance (link above)
2. Review example case studies in the REF database
3. Check this integration guide for specific prompt details

