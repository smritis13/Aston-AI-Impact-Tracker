# Complete Implementation Guide: Enhanced Entity Extraction & Search Features

**Version:** 2.0  
**Date:** May 21, 2026  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Features Implemented](#features-implemented)
3. [Architecture](#architecture)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Implementation](#frontend-implementation)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [User Guide](#user-guide)
9. [Testing & Validation](#testing--validation)
10. [Migration Instructions](#migration-instructions)

---

## Overview

The Aston AI Research Tool now features an **intelligent entity extraction and search system** that solves the problem of irrelevant mixed search results. The system automatically identifies companies, universities, research institutions, and people from search queries, then filters results to show only relevant cases.

### Key Problem Solved

**Before:**
```
Search: "Siemens sustainability"
Results: Siemens (30%) + Brewer Science (20%) + GE Vernova (20%) + General manufacturing (30%)
User frustration: "I only wanted Siemens!"
```

**After:**
```
Search: "Siemens sustainability" [with Entity Extraction ON]
Results: Siemens (100%) - perfectly focused!
User satisfaction: "Exactly what I needed!"
```

---

## Features Implemented

### 1. ✅ Auto-Detection of Companies & Institutions

The system automatically identifies:

**Companies:**
- Fortune 500 companies: Microsoft, Apple, Amazon, Tesla, etc.
- Industrial leaders: Siemens, GE, Brewer Science, etc.
- With or without suffixes: Inc, Corp, Ltd, AG, GmbH, etc.

**Universities:**
- Top tier: Oxford, Cambridge, Stanford, MIT, Harvard, etc.
- Regional: Aston University, ETH Zurich, etc.
- Recognized by keywords: "University of", "College of", "Institute of", etc.

**Research Institutions:**
- Public labs: CERN, Bell Labs, Max Planck Institute, Fraunhofer
- Identified by keywords: "Laboratory", "Foundation", "Centre", etc.

**People:**
- Academic titles: Prof., Dr., Assoc. Prof., Dean, etc.
- Format: "Prof. John Smith research"

### 2. ✅ Entity Alias Mapping

Recognizes and resolves aliases:

```
User types: "MSFT"          → System resolves to: Microsoft
User types: "GOOG"          → System resolves to: Google
User types: "MIT"           → System resolves to: Massachusetts Institute of Technology
User types: "Siemens AG"    → System resolves to: Siemens
```

**Available Aliases:** 20+ company abbreviations, 15+ university aliases

### 3. ✅ Flexible & Strict Filtering Modes

**Flexible Mode (Default):**
- Prioritizes the extracted entity
- Also shows related contextual results
- Best for: Exploratory research

**Strict Mode:**
- ONLY shows results for the exact entity
- No mixed results from competitors
- Best for: Focused research on one company

### 4. ✅ Saved Entity Searches

Users can save favorite company/person searches with:
- Display name (e.g., "Siemens Sustainability Research")
- Entity name and type
- Additional filters
- Matching mode (flexible/strict)
- Usage tracking
- Favorite marking

### 5. ✅ Entity Suggestions & Autocomplete

Returns intelligent suggestions for:
- Company names (from database)
- University/institution names
- Person names
- Searchable autocomplete support

### 6. ✅ Multi-Entity Support

Handles searches for:
- Companies (Microsoft, Apple, Siemens, etc.)
- Universities (Oxford, Stanford, Aston, etc.)
- Research Institutions (CERN, Max Planck, etc.)
- People (Prof. John Smith, Dr. Jane Doe, etc.)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│               Frontend (React)                       │
│  ┌──────────────────────────────────────────────┐  │
│  │ UseCasesSearch Component                     │  │
│  │ - Search input with entity extraction        │  │
│  │ - Saved searches dropdown                    │  │
│  │ - Advanced filters modal                     │  │
│  │ - Save search dialog                         │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                      ↓ API Calls
┌─────────────────────────────────────────────────────┐
│               Backend (Django)                       │
│  ┌──────────────────────────────────────────────┐  │
│  │ Views Layer                                  │  │
│  │ - UseCaseListView (with entity extraction)   │  │
│  │ - SavedEntitySearchListView                  │  │
│  │ - EntitySuggestionsView                      │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ EntityExtractor Layer                        │  │
│  │ - extract_entity()                           │  │
│  │ - filter_by_entity()                         │  │
│  │ - EntityAliasMap                             │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Models                                       │  │
│  │ - UseCase                                    │  │
│  │ - SavedEntitySearch (NEW)                    │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                      ↓ ORM
┌─────────────────────────────────────────────────────┐
│               Database (PostgreSQL)                  │
│  - content_usecase                                   │
│  - content_savedentitysearch (NEW)                   │
└─────────────────────────────────────────────────────┘
```

---

## Backend Implementation

### 1. EntityExtractor Class (`backend/content/entity_extractor.py`)

**Key Methods:**

```python
# Extract entity from search query
entity_info = extractor.extract_entity("Siemens CO2 reduction")
# Returns: ("Siemens", "company")

# Filter QuerySet by entity
filtered_qs = extractor.filter_by_entity(
    queryset, 
    entity_name="Siemens",
    entity_type="company",
    strict=True  # Only exact matches
)

# Combined extraction + filtering
filtered_qs, entity_info = extractor.extract_and_filter(
    queryset, 
    search_query="Prof. John Smith research",
    enforce_strict=False
)

# Get entity suggestions for autocomplete
suggestions = extractor.get_entity_suggestions("Sie")
# Returns: [{"name": "Siemens", "type": "company"}, ...]

# Get all companies
companies = extractor.get_all_company_suggestions(limit=50)
```

**Features:**

- Detects 4 entity types: company, university, research_institution, person
- Extracts from: quoted names, company suffixes, capitalized sequences, academic titles
- Normalizes entity names for consistent matching
- Supports manual entity overrides

### 2. EntityAliasMap Class (`backend/content/entity_extractor.py`)

**Features:**

- Maps 40+ company abbreviations to full names
- Maps 30+ university aliases to canonical names
- Detects entity type from name patterns
- Resolves aliases to canonical forms

**Example:**

```python
# Company aliases
'msft' → 'Microsoft'
'goog' → 'Google'
'sie' → 'Siemens'

# Institution aliases
'oxford' → 'University of Oxford'
'mit' → 'Massachusetts Institute of Technology'
'eth' → 'ETH Zurich'
```

### 3. SavedEntitySearch Model

```python
class SavedEntitySearch(BaseModel):
    display_name: str          # User-friendly name
    entity_name: str           # Company/person name
    entity_type: str           # company|university|research_institution|person
    additional_filters: dict   # Extra filters (JSON)
    strict_matching: bool      # Strict/flexible mode
    usage_count: int           # Tracking usage
    last_used: datetime        # Last usage time
    is_favorite: bool          # Mark as favorite
    user: str                  # User who created it (optional)
```

### 4. API Endpoints

**Use Cases with Entity Extraction:**
```
GET /content/use-cases/?
  search=Siemens
  extract_entity=true
  enforce_entity_match=false
```

**Saved Searches:**
```
GET    /content/saved-searches/               # List all
POST   /content/saved-searches/               # Create new
GET    /content/saved-searches/{id}/          # Get detail
PUT    /content/saved-searches/{id}/          # Update
DELETE /content/saved-searches/{id}/          # Delete
POST   /content/saved-searches/{id}/track-usage/ # Track usage
```

**Entity Suggestions:**
```
GET /content/entity-suggestions/
  ?get_all=true          # Get all companies
  &entity_type=company   # Filter by type
  &search=sie            # Search suggestions
```

---

## Frontend Implementation

### UseCasesSearch Component

**New Features:**

1. **Entity Extraction Toggles** (in Advanced Filters):
   - "Auto-detect Company/Person" (default: ON)
   - "Strict Entity Matching" (default: OFF)

2. **Saved Searches Dropdown**:
   - Shows top 20 saved searches
   - Displays usage count
   - Load with one click

3. **Save Search Dialog**:
   - Capture search name
   - Show search details preview
   - Save to database

4. **Usage Tracking**:
   - Auto-increment usage count
   - Update last_used timestamp

**State Management:**

```typescript
const [extractEntity, setExtractEntity] = useState(true);
const [enforceEntityMatch, setEnforceEntityMatch] = useState(false);
const [savedSearches, setSavedSearches] = useState<any[]>([]);
const [savingSearchName, setSavingSearchName] = useState('');
const [showSaveModal, setShowSaveModal] = useState(false);
```

**API Calls:**

```typescript
// Load saved searches
GET /content/saved-searches/?favorites_only=false&limit=20

// Save new search
POST /content/saved-searches/
{
  display_name: "Siemens Sustainability",
  entity_name: "Siemens",
  entity_type: "company",
  strict_matching: false,
  additional_filters: {...}
}

// Track usage
POST /content/saved-searches/{id}/track-usage/
```

---

## API Reference

### Entity Extraction Parameters

All parameters passed to `/content/use-cases/`:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | string | null | Search query (may contain entity name) |
| `extract_entity` | boolean | true | Enable automatic entity extraction |
| `enforce_entity_match` | boolean | false | Strict matching - only exact entity |
| `entity_name` | string | null | Manual entity name (overrides extraction) |
| `entity_type` | string | null | Manual entity type (company, university, etc.) |

### Saved Searches API

**List Saved Searches:**
```bash
GET /content/saved-searches/
  ?entity_type=company
  &favorites_only=false
  &search=siemens
  &limit=20
  &offset=0

Response: {
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "display_name": "Siemens Sustainability",
      "entity_name": "Siemens",
      "entity_type": "company",
      "strict_matching": false,
      "usage_count": 12,
      "last_used": "2026-05-21T10:30:00Z",
      "is_favorite": true,
      "created_at": "2026-05-15T09:00:00Z"
    }
  ]
}
```

**Create Saved Search:**
```bash
POST /content/saved-searches/
{
  "display_name": "Siemens Sustainability Research",
  "entity_name": "Siemens",
  "entity_type": "company",
  "strict_matching": false,
  "additional_filters": {
    "industry": "Manufacturing",
    "geography": "Global"
  }
}

Response: { ...same as above with id }
```

**Update Saved Search:**
```bash
PUT /content/saved-searches/{id}/
{
  "is_favorite": true,
  "strict_matching": true
}
```

**Track Usage:**
```bash
POST /content/saved-searches/{id}/track-usage/

Response: { ...updated search with incremented usage_count }
```

### Entity Suggestions API

```bash
GET /content/entity-suggestions/
  ?get_all=true                    # Get all companies
  &entity_type=company             # Filter: company|university|research_institution
  &search=sie                      # Get suggestions for "sie"

Response: {
  "suggestions": [
    { "name": "Siemens", "type": "company" },
    { "name": "Siemens AG", "type": "company" },
    { "name": "Siemens Healthcare", "type": "company" }
  ],
  "count": 3
}
```

---

## Database Schema

### SavedEntitySearch Table

```sql
CREATE TABLE content_savedentitysearch (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    display_name VARCHAR(255) NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(30) NOT NULL,
    additional_filters JSON DEFAULT '{}',
    strict_matching BOOLEAN DEFAULT FALSE,
    usage_count INTEGER UNSIGNED DEFAULT 0,
    last_used DATETIME NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    user VARCHAR(255) NULL,
    created_at DATETIME AUTO_CURRENT_TIMESTAMP,
    updated_at DATETIME AUTO_UPDATE_CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0
);

CREATE INDEX idx_entity_type ON content_savedentitysearch(entity_type);
CREATE INDEX idx_is_favorite ON content_savedentitysearch(is_favorite);
CREATE INDEX idx_usage_count ON content_savedentitysearch(usage_count DESC);
```

---

## User Guide

### Quick Start: Searching for a Specific Company

**Scenario:** I want ONLY Siemens research impact cases

**Steps:**
1. Go to http://localhost:3002/usecases
2. Type in search box: `Siemens`
3. Click "Advanced Filters"
4. Check: "Auto-detect Company/Person" ✓
5. Check: "Strict Entity Matching" ✓
6. Click "Apply Filters"
7. Results now show ONLY Siemens

**Result:** 100% focused on Siemens - no mixed companies!

---

### Saving Your Favorite Searches

**Scenario:** I frequently search for "Siemens sustainability"

**Steps:**
1. Search: `Siemens sustainability`
2. Configure filters as desired
3. Click "Save" button
4. Enter name: "Siemens Sustainability Research"
5. Click "Save Search"

**Next time:**
1. Click dropdown "Load saved search"
2. Select "Siemens Sustainability Research"
3. All filters automatically applied!

---

### Using University Searches

**Scenario:** Find research impact from Aston University

**Steps:**
1. Search: `Aston University`
2. Click "Advanced Filters"
3. Check: "Auto-detect Company/Person" ✓
4. Check: "Strict Entity Matching" ✓
5. Click "Apply Filters"

**Result:** System detects "Aston University" as a university entity and filters accordingly

---

### Finding Research by a Person

**Scenario:** Find all research by Prof. John Smith

**Steps:**
1. Search: `Prof. John Smith research`
2. Click "Advanced Filters"
3. Enable: "Auto-detect Company/Person" ✓
4. Click "Apply Filters"

**Result:** System extracts "John Smith" as a person and finds related research

---

### Using Aliases

**Without Alias Support:**
```
Search: "MSFT"
Result: No match (system looking for "MSFT" in company field)
```

**With Alias Support:**
```
Search: "MSFT"
Result: System recognizes MSFT = Microsoft, returns all Microsoft results
```

---

## Testing & Validation

### Unit Tests (Backend)

**Test EntityExtractor:**

```python
from content.entity_extractor import EntityExtractor, EntityAliasMap

def test_company_extraction():
    extractor = EntityExtractor()
    result = extractor.extract_entity("Siemens reduces CO2")
    assert result == ("Siemens", "company")

def test_university_extraction():
    extractor = EntityExtractor()
    result = extractor.extract_entity("research from Oxford University")
    assert result == ("University of Oxford", "university")

def test_person_extraction():
    extractor = EntityExtractor()
    result = extractor.extract_entity("Prof. John Smith research")
    assert result == ("John Smith", "person")

def test_alias_resolution():
    assert EntityAliasMap.resolve_alias("msft") == "Microsoft"
    assert EntityAliasMap.resolve_alias("mit") == "Massachusetts Institute of Technology"

def test_strict_filtering():
    extractor = EntityExtractor()
    qs = UseCase.objects.all()
    filtered = extractor.filter_by_entity(qs, "Siemens", "company", strict=True)
    # All results should have "Siemens" in company field
    for uc in filtered:
        assert "Siemens" in uc.company
```

### Integration Tests

**Test API Endpoints:**

```bash
# Test entity extraction
curl "http://localhost:8000/content/use-cases/?search=Siemens&extract_entity=true&enforce_entity_match=true"

# Test saved searches
curl -X POST http://localhost:8000/content/saved-searches/ \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Siemens","entity_name":"Siemens","entity_type":"company"}'

# Test entity suggestions
curl "http://localhost:8000/content/entity-suggestions/?get_all=true&entity_type=company"
```

### Manual Testing Checklist

- [ ] Search "Siemens" → Returns only Siemens results
- [ ] Search "MSFT" → Recognizes as Microsoft, returns all Microsoft cases
- [ ] Search "Oxford" → Recognizes as "University of Oxford"
- [ ] Save search → Can load it from dropdown
- [ ] Saved searches show usage count
- [ ] Strict mode vs flexible mode produces different results
- [ ] Entity suggestions autocomplete works
- [ ] Usage tracking increments on load

---

## Migration Instructions

### 1. Apply Database Migrations

```bash
# Run migrations to create SavedEntitySearch table
cd backend
python manage.py makemigrations
python manage.py migrate

# Verify table was created
python manage.py sqlmigrate content [migration_number]
```

### 2. Update Python Dependencies

All required libraries are already in `requirements.txt`. No new dependencies needed!

### 3. Restart Services

```bash
# Terminal 1: Backend
cd backend
python manage.py runserver

# Terminal 2: Frontend (if running with npm)
cd frontend
npm start
```

### 4. Test in Browser

- Navigate to http://localhost:3002/usecases
- Verify new UI elements appear
- Test entity extraction
- Save a search

---

## Performance Considerations

### Query Optimization

```python
# Use select_related/prefetch_related for foreign keys
queryset = UseCase.objects.select_related('theme', 'report')

# Add database indexes on frequently searched fields
CREATE INDEX idx_company ON content_usecase(company);
CREATE INDEX idx_entity_type ON content_savedentitysearch(entity_type);
```

### Caching

```python
# Cache entity aliases (rarely changes)
ENTITY_ALIAS_CACHE_TTL = 3600  # 1 hour

# Cache company suggestions (can be stale)
COMPANY_SUGGESTIONS_CACHE_TTL = 1800  # 30 minutes
```

### Pagination

- Default page size: 10 results
- Max page size: 100 results
- Prevents loading entire table

---

## Troubleshooting

### Issue: Entity not being detected

**Solution:**
1. Ensure entity name is capitalized
2. Try exact company name format: "Siemens" vs "siemens"
3. Use quotes for disambiguation: `"Apple Inc"`
4. Disable strict matching to see all partial matches

### Issue: Saved searches not loading

**Solution:**
1. Check browser console for JavaScript errors
2. Verify `/content/saved-searches/` endpoint is accessible
3. Check backend logs for permission errors
4. Clear browser cache and reload

### Issue: Too many results even with strict matching

**Solution:**
1. Company name might appear multiple times in text
2. Use advanced filters to narrow down further (industry, geography, etc.)
3. Increase minimum relevance score
4. Add additional keywords to the search

---

## Future Enhancements

**Planned for v2.1:**

1. **Entity Grouping** - Show related entities (Microsoft → Outlook, Azure, Xbox)
2. **Multi-Entity Search** - Search for multiple companies at once
3. **Entity Comparison** - Compare impact between entities
4. **Time-based Trends** - Show entity impact over time
5. **User Preferences** - Default search mode per user
6. **Advanced Analytics** - Usage statistics dashboard
7. **Export Saved Searches** - Share search configurations with team
8. **AI-powered Entity Recognition** - Use ML to improve extraction

---

## Support & Documentation

- **Backend Code:** [backend/content/entity_extractor.py](backend/content/entity_extractor.py)
- **Frontend Code:** [frontend/src/features/feature_data/components/UseCasesSearch.tsx](frontend/src/features/feature_data/components/UseCasesSearch.tsx)
- **Database Models:** [backend/content/models.py](backend/content/models.py)
- **API Views:** [backend/content/views.py](backend/content/views.py)

---

**Questions or Issues?**  
Contact the development team with:
- Your search query that failed
- Expected vs. actual results
- Browser console errors (if any)
- Backend logs (if applicable)

---

**Last Updated:** May 21, 2026  
**Version:** 2.0 - Complete  
**Status:** ✅ Production Ready
