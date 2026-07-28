# Quick Testing Guide - Entity Extraction Feature

## Setup & Verification

### 1. **Verify Files Are in Place**

```bash
# Check backend entity extractor exists
ls -la backend/content/entity_extractor.py

# Check frontend component was updated
grep -n "extractEntity\|enforceEntityMatch" frontend/src/features/feature_data/components/UseCasesSearch.tsx
```

### 2. **Start the Application**

```bash
# Terminal 1: Backend
cd backend
python manage.py runserver

# Terminal 2: Frontend  
cd frontend
npm start
```

---

## Test Scenarios

### Test 1: Basic Entity Extraction

**Steps:**
1. Navigate to http://localhost:3002/usecases
2. In the search box, type: `Siemens`
3. Click the search button
4. Observe: Results should show Siemens cases

**Expected:**
- Search executes
- Results prioritize Siemens
- Look for "Siemens" in the "Organisation/Beneficiary" column

**If Failing:**
- Check browser console for errors (F12 → Console)
- Check backend logs for Python errors
- Verify entity_extractor.py is being imported

---

### Test 2: Flexible Matching Mode (Default)

**Steps:**
1. Search: `Siemens sustainability`
2. Click "Advanced Filters"
3. Verify: "Auto-detect Company/Person" is checked ✓
4. Verify: "Strict Entity Matching" is unchecked ✗
5. Click "Apply Filters"

**Expected:**
- Results show Siemens cases
- May also show manufacturing/sustainability cases
- More results than strict mode

---

### Test 3: Strict Entity Matching

**Steps:**
1. Search: `Siemens CO2 emissions`
2. Click "Advanced Filters"
3. Check "Auto-detect Company/Person" ✓
4. Check "Strict Entity Matching" ✓
5. Click "Apply Filters"

**Expected:**
- ONLY Siemens results
- Fewer results than flexible mode
- No results from other companies

**If No Results:**
- Entity name might not match exactly
- Try disabling strict matching and see what variations appear
- Check the "Organisation/Beneficiary" field for exact company names

---

### Test 4: Disable Auto-Detection

**Steps:**
1. Search: `Siemens`
2. Click "Advanced Filters"
3. Uncheck "Auto-detect Company/Person" ✗
4. Click "Apply Filters"

**Expected:**
- Works like old search (substring matching)
- Finds "Siemens" in any field
- No entity filtering

---

### Test 5: Person Name Extraction

**Steps:**
1. Search: `Prof. John Smith research`
2. Click "Advanced Filters"
3. Verify: "Auto-detect Company/Person" is checked ✓
4. Click "Apply Filters"

**Expected:**
- Attempts to extract "John Smith" as person name
- Shows related cases if any person names match

**Note:** Person matching may be limited depending on data structure

---

### Test 6: Manual Entity Override

**Browser Console Test:**
```javascript
// Open DevTools (F12), go to Console tab, paste:

// Change current URL to add entity_name parameter
const params = new URLSearchParams(window.location.search);
params.set('entity_name', 'Brewer Science');
params.set('entity_type', 'company');
params.set('enforce_entity_match', 'true');
window.location.search = params.toString();
```

**Expected:**
- Results filtered to "Brewer Science" only
- Demonstrates manual entity override works

---

## Browser Developer Tools Testing

### Check Network Requests

1. Open DevTools (F12)
2. Go to "Network" tab
3. Click search button
4. Find request to `/content/use-cases/`
5. In Query String Parameters, verify:
   ```
   extract_entity: true
   enforce_entity_match: false
   search: Siemens (or your search term)
   ```

### Check Console for Errors

1. Open DevTools (F12)
2. Go to "Console" tab
3. Should see no red errors
4. If errors appear, note them and check:
   - Backend logs for server errors
   - entity_extractor.py for import issues

---

## Backend API Testing

### Test with curl

```bash
# Test 1: Flexible matching
curl "http://localhost:8000/content/use-cases/?search=Siemens&extract_entity=true&enforce_entity_match=false&limit=5" \
  -H "Accept: application/json"

# Test 2: Strict matching
curl "http://localhost:8000/content/use-cases/?search=Siemens&extract_entity=true&enforce_entity_match=true&limit=5" \
  -H "Accept: application/json"

# Test 3: Manual entity override
curl "http://localhost:8000/content/use-cases/?entity_name=Siemens&entity_type=company&enforce_entity_match=true&limit=5" \
  -H "Accept: application/json"

# Test 4: No entity extraction
curl "http://localhost:8000/content/use-cases/?search=Siemens&extract_entity=false&limit=5" \
  -H "Accept: application/json"
```

### Verify Entity Extraction Works

Open a Python shell in the backend directory:

```python
from content.entity_extractor import EntityExtractor

extractor = EntityExtractor()

# Test company extraction
print(extractor.extract_entity("Siemens reduces CO2 emissions"))
# Expected: ('Siemens', 'company')

# Test person extraction  
print(extractor.extract_entity("Prof. John Smith research"))
# Expected: ('John Smith', 'person')

# Test with complex query
print(extractor.extract_entity("research by Microsoft Corporation on AI"))
# Expected: ('Microsoft Corporation', 'company')

# Test extraction with quoted name
print(extractor.extract_entity("\"Apple Inc\" sustainability report"))
# Expected: ('Apple Inc', 'company')
```

---

## Expected Behavior Summary

| Test | Action | Expected Result | Status |
|------|--------|-----------------|--------|
| 1 | Search "Siemens" | Results prioritize Siemens | ✓ |
| 2 | Flexible mode | Siemens + related results | ✓ |
| 3 | Strict mode | Only Siemens results | ✓ |
| 4 | Disable auto-detect | Full-text search behavior | ✓ |
| 5 | Person name | Extract "John Smith" | ✓ |
| 6 | Manual override | Respect entity_name param | ✓ |
| API | curl request | Filter by company | ✓ |
| Python | Entity extraction | Return (name, type) tuple | ✓ |

---

## Troubleshooting Checklist

- [ ] entity_extractor.py exists in backend/content/
- [ ] Import line added to backend/content/views.py
- [ ] UseCasesSearch.tsx has extractEntity and enforceEntityMatch states
- [ ] Advanced Filters modal shows new Entity Extraction section
- [ ] No Python errors in backend logs
- [ ] No JavaScript errors in browser console
- [ ] Search query includes extract_entity and enforce_entity_match parameters
- [ ] Results change between flexible and strict modes
- [ ] Manual entity override works via query parameters

---

## Known Limitations

1. **Person Name Extraction:** Limited by data structure - only works if person names are in specific fields
2. **Company Name Variations:** "Siemens", "Siemens AG", "SIEMENS" must be normalized
3. **Acronyms:** "MSFT" won't extract as "Microsoft" (no alias mapping yet)
4. **Generic Terms:** Very common words might not extract properly

---

## Next Steps if Testing Fails

1. **Check backend logs:** `python manage.py runserver` output
2. **Check frontend console:** Browser F12 → Console tab
3. **Check entity_extractor imports:** Run Python test above
4. **Verify changes saved:** grep for new code in modified files
5. **Clear browser cache:** Ctrl+Shift+Delete (Windows) or Cmd+Shift+Delete (Mac)
6. **Restart dev servers:** Kill and restart both backend and frontend

---

**Test Date:** May 21, 2026  
**Tester:** [Your Name]  
**Status:** [ ] Passed | [ ] Failed (describe below)

**Notes:**
```
[Add any issues or observations here]
```
