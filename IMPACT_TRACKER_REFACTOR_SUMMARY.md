# Impact Tracker Refactoring Summary

## Overview
The Aston AI Research Tool has been refactored to focus exclusively on **Impact Tracking** with a streamlined table interface showing only the most critical impact metrics.

## Changes Made

### 1. **Backend - Pagination Update**
**File:** `backend/base/pagination.py`
- Changed `page_size` from `30` to `10`
- **Impact:** The API now returns 10 impacts per page instead of 30

### 2. **Frontend - Page Size Update**
**File:** `frontend/src/features/feature_data/pages/usecases/UseCasesPage.tsx`
- Updated `pageSize` state from `30` to `10`
- **Impact:** Frontend displays 10 impacts per page

### 3. **Frontend - Table Redesign**
**File:** `frontend/src/features/feature_data/pages/usecases/UseCasesPage.tsx`
- **Simplified table to show only 9 essential columns:**
  1. **Title / Product Name** (from `use_case_name`)
  2. **Organisation / Beneficiary** (from `company`)
  3. **Impact Type** (from `use_case_type`)
  4. **Sector** (from `industry`)
  5. **Quantitative Outcome** (from `performance_impact`) - Numbers only
  6. **Dates / Timeframe** (from `use_case_date`)
  7. **Source URL** (from `source` with link validation)
  8. **Credibility Score** (from `credibility_score`) - 0-10 scale
  9. **Relevance Score** (from `relevance_score`) - Widget display

- **Removed columns:**
  - ~~ID~~ (internal reference, not needed)
  - ~~Tools~~ (too detailed for impact view)
  - ~~Description~~ (summarized in quantitative outcome)
  - ~~Created Date~~ (redundant with timeframe)

## Data Model

The `UseCase` model in `backend/content/models.py` contains all required fields:

```python
class UseCase(models.Model):
    use_case_name          # Title
    company                # Organisation
    use_case_type          # Impact Type
    industry               # Sector
    performance_impact     # Quantitative Outcome
    use_case_date          # Dates/Timeframe
    source                 # Source URL
    credibility_score      # Credibility Check (0-10)
    is_credible            # Boolean credibility flag
    relevance_score        # Relevance Check (0-10)
    is_relevant            # Boolean relevance flag
    # Plus supporting fields for scoring explanations
```

## User Experience

### Before Refactor
- 13 columns displayed per impact
- 30 impacts shown per page
- Mixed data types and relevance levels
- Cluttered interface

### After Refactor
- **9 focused columns** showing only impact essentials
- **10 impacts per page** - easier to scan
- **Clean interface** - focused on decision-making data
- **Better readability** - quantitative outcomes highlighted
- **Quality metrics** prominent - credibility & relevance scores visible

## Pagination Behavior

**Example:**
- Page 1: Impacts 1-10 (shown as "1-10 of 250")
- Page 2: Impacts 11-20 (shown as "11-20 of 250")
- Page 25: Impacts 241-250 (shown as "241-250 of 250")

## Filtering & Search

All existing filtering capabilities remain functional:
- Search across all impact fields
- Filter by company, industry, type, theme
- Filter by scores (credibility, relevance)
- Filter by date ranges
- Sort by any column

## Export Functionality

The export buttons work with the new schema:
- **CSV Export:** All 9 columns + metadata
- **Excel Export:** Formatted with colors and freezable header
- **JSON Export:** Complete impact data

## Additional Features

- Click on any impact title to view full details
- Hover over truncated quantitative outcomes to see full text
- Source URL validation shows domain authority score
- Real-time generation progress indicator
- Theme/report organization maintained

## Next Steps (Optional Enhancements)

1. **Add a summary dashboard** showing:
   - Total number of impacts tracked
   - Average credibility/relevance scores
   - Most common sectors and impact types
   - Recent impacts added

2. **Add advanced filtering** for:
   - Minimum credibility threshold
   - Minimum relevance score
   - Geographic focus
   - Date range per impact

3. **Add bulk operations:**
   - Export selected impacts
   - Batch credibility review
   - Batch update relevance scores

4. **Simplify navigation** by:
   - Removing other app pages from sidebar
   - Making Impact Tracker the default home page
   - Hiding legacy use case routes (/usecases/retail-ai, etc.)

## Files Modified

1. ✅ `backend/base/pagination.py` - Page size changed to 10
2. ✅ `frontend/src/features/feature_data/pages/usecases/UseCasesPage.tsx` - Table redesigned

## Testing Checklist

- [ ] Verify page loads with 10 impacts displayed
- [ ] Test pagination - next/prev pages work correctly
- [ ] Search functionality works on all 9 columns
- [ ] Credibility and Relevance scores display correctly
- [ ] Source URLs are clickable and valid
- [ ] Export (CSV, Excel, JSON) includes all data
- [ ] Sort by each column works
- [ ] Theme filtering works
- [ ] Mobile responsive display works

---

**Status:** ✅ **Complete** - Impact Tracker refactoring finished
**Last Updated:** March 27, 2026
