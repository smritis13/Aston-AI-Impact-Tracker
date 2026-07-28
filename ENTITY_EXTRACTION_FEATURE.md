# Entity Extraction & Strict Filtering Feature

## Overview

The Aston AI Research Tool now includes **Entity Extraction** capabilities that automatically identify companies and people mentioned in your search queries, then filter results to show only relevant cases for those specific entities. This solves the problem of getting mixed, irrelevant results from multiple companies when searching for a specific organization or person.

## Problem Solved

**Before:** Searching for "Siemens" would return results from:
- Siemens (the actual company you wanted)
- Brewer Science (mentioned in related cases)
- GE Vernova (industry competitors)
- General manufacturing sector findings

**After:** Searching for "Siemens" with entity extraction enabled returns ONLY results directly related to Siemens.

## How It Works

### 1. **Auto-Detection (Default Enabled)**

When you type a search query mentioning a company or person name, the system:

1. **Extracts the entity** from your search (e.g., "Siemens reduces CO2" → entity: "Siemens")
2. **Filters results** to prioritize that company/person
3. **Shows a visual indicator** of what entity was detected

**Supported Patterns:**
- Company names: `Siemens`, `Microsoft Corp`, `"Apple Inc"`
- Person names: `Prof. John Smith`, `"Jane Doe"`
- Industry leaders: Any capitalized entity names

### 2. **Two Filtering Modes**

#### Mode 1: **Flexible Matching** (Default)
- Detects the entity from your search
- Prioritizes results for that entity
- Still shows related industry findings if there's a match
- **Use this when:** You want the entity to be the priority but don't mind seeing related context

```
Search: "Siemens sustainability initiatives"
Entity Extracted: Siemens (company)
Results: Siemens cases + related manufacturing sustainability cases
```

#### Mode 2: **Strict Entity Matching**
- Detects the entity from your search
- ONLY shows results for that specific entity
- No mixed results from competitors or industry peers
- **Use this when:** You want 100% focused results on one company/person

```
Search: "Siemens sustainability initiatives"
Entity Extracted: Siemens (company)
Results: ONLY Siemens-related cases
```

## How to Use

### Step 1: Search with a Company/Person Name

In the search box, type your query mentioning the company or person:

```
Examples:
- "Siemens carbon emissions reduction"
- "Prof. John Smith research impact"
- "Microsoft AI implementation"
- "research by Tesla"
```

### Step 2: Open Advanced Filters

Click the **"Advanced Filters"** button to see entity extraction options.

### Step 3: Configure Entity Extraction

Three options are available:

| Option | Setting | Effect |
|--------|---------|--------|
| **Auto-detect Company/Person** | Checkbox (default: ON) | System identifies entity from your search query |
| **Strict Entity Matching** | Checkbox (default: OFF) | Only show results for the detected entity; disable to see related results |
| **Sort By** | Dropdown | Choose relevance, credibility, date, etc. |

### Step 4: Apply and Search

Click **"Apply Filters"** to execute the search with your selected settings.

### Interpreting Results

After searching, you'll see:

- **No entity detected?** The search works as before (full-text search)
- **Entity detected:** Look for results where the detected company appears in the "Organisation/Beneficiary" column
- **Too narrow?** Disable "Strict Entity Matching" to expand results

## Query Parameters (For API Developers)

The backend supports these new parameters:

```
GET /content/use-cases/?
  search=Siemens%20sustainability
  extract_entity=true           # Enable entity extraction
  enforce_entity_match=false    # If true, only exact entity matches
  entity_name=Siemens           # (Optional) Override extraction
  entity_type=company           # (Optional) Specify type: 'company' or 'person'
```

**Example Requests:**

```bash
# Flexible matching with auto-detection
curl "http://localhost:8000/content/use-cases/?search=Siemens&extract_entity=true&enforce_entity_match=false"

# Strict matching - only Siemens results
curl "http://localhost:8000/content/use-cases/?search=Siemens&extract_entity=true&enforce_entity_match=true"

# Manual entity specification
curl "http://localhost:8000/content/use-cases/?entity_name=Siemens&entity_type=company&enforce_entity_match=true"
```

## Technical Details

### Backend Implementation

**New File:** `backend/content/entity_extractor.py`

Provides:
- `EntityExtractor.extract_entity()` - Identifies company/person from text
- `EntityExtractor.filter_by_entity()` - Filters QuerySet by entity
- `EntityExtractor.extract_and_filter()` - Combined extraction + filtering
- `EntityExtractor.get_entity_suggestions()` - Autocomplete suggestions

**Modified File:** `backend/content/views.py`

Updated `UseCaseListView.get_queryset()` to:
1. Check for entity extraction parameters
2. Extract entity if search query provided
3. Apply strict/flexible filtering based on settings
4. Return filtered results

### Frontend Implementation

**Modified File:** `frontend/src/features/feature_data/components/UseCasesSearch.tsx`

Added:
- `extractEntity` state - Toggle entity extraction ON/OFF
- `enforceEntityMatch` state - Toggle strict matching ON/OFF
- Entity extraction UI section in Advanced Filters modal
- Visual help text explaining each option

## Use Cases & Examples

### Example 1: Finding All Siemens Impact Cases

**Goal:** I want to find ALL impact cases specifically by or about Siemens

**Steps:**
1. Search: `"Siemens"`
2. Open Advanced Filters
3. Enable: "Auto-detect Company/Person" ✓
4. Enable: "Strict Entity Matching" ✓
5. Click "Apply Filters"

**Result:** Only Siemens cases returned

---

### Example 2: Exploring Siemens in Manufacturing Context

**Goal:** Find Siemens cases AND see related manufacturing sustainability context

**Steps:**
1. Search: `"Siemens manufacturing sustainability"`
2. Open Advanced Filters
3. Enable: "Auto-detect Company/Person" ✓
4. Disable: "Strict Entity Matching" 
5. Click "Apply Filters"

**Result:** Siemens cases prioritized + related manufacturing findings

---

### Example 3: Research by a Specific Professor

**Goal:** Find all research impact cases associated with Prof. John Smith

**Steps:**
1. Search: `"Prof. John Smith research"`
2. Open Advanced Filters
3. Enable: "Auto-detect Company/Person" ✓
4. Enable: "Strict Entity Matching" ✓
5. Click "Apply Filters"

**Result:** Only research cases involving Prof. John Smith

---

## Troubleshooting

### Issue: No Results After Enabling Strict Matching

**Possible Causes:**
- The entity name in your data doesn't exactly match what you typed
- Typo in the company/person name

**Solution:**
1. Disable "Strict Entity Matching" temporarily
2. See what variations appear in the results
3. Search again using the exact name from the data

### Issue: Entity Not Being Detected

**Possible Causes:**
- Entity is too generic or commonly used as a regular word
- Company name isn't capitalized in your search

**Solution:**
1. Use quotes: `"Siemens"` instead of `siemens`
2. Include company suffix: `"Siemens AG"` instead of just `"Siemens"`
3. Manually enter the company name in the Company filter

### Issue: Getting Too Many Unrelated Results

**Solution:**
1. Enable "Strict Entity Matching" to filter only to your entity
2. Increase "Minimum Relevance Score" to 7 or higher
3. Add additional filters (Industry, Use Case Type, etc.)

## Future Enhancements

Potential improvements planned:

1. **Saved Entity Searches** - Remember favorite company/person searches
2. **Entity Comparison** - Compare impact cases between multiple entities
3. **Entity Suggestions** - Autocomplete suggestions as you type
4. **Entity Aliasing** - Recognize "Microsoft Corp" = "MSFT" = "Microsoft"
5. **Entity Relationship Mapping** - Show related companies/people in results
6. **Feedback Loop** - Users can mark detected entities as correct/incorrect

## API Reference

### EntityExtractor Class

```python
from content.entity_extractor import EntityExtractor

extractor = EntityExtractor()

# Extract entity from text
entity_info = extractor.extract_entity("Siemens reduces CO2")
# Returns: ("Siemens", "company")

# Filter QuerySet by entity
filtered_qs = extractor.filter_by_entity(
    queryset=UseCase.objects.all(),
    entity_name="Siemens",
    entity_type="company",
    strict=True  # Only exact matches
)

# Combined extraction + filtering
filtered_qs, entity_info = extractor.extract_and_filter(
    queryset=UseCase.objects.all(),
    search_query="Siemens sustainability",
    enforce_strict=False
)
# Returns: (QuerySet, {"entity_name": "Siemens", "entity_type": "company", "source": "extracted"})

# Get entity suggestions for autocomplete
suggestions = extractor.get_entity_suggestions("Sie")
# Returns: ["Siemens", "Siemens AG", ...]
```

## Feedback & Issues

If you encounter issues or have suggestions for improvement:

1. Check the **Troubleshooting** section above
2. Review query parameters being sent (check browser Network tab)
3. Contact the development team with:
   - Your search query
   - Expected vs. actual results
   - Screenshot of Advanced Filters settings

---

**Last Updated:** May 21, 2026  
**Version:** 1.0  
**Status:** Production Ready
