import React, { useState, useEffect, useCallback } from 'react';
import { Form, Button, InputGroup, Row, Col, Modal } from 'react-bootstrap';
import SearchableCombobox from './SearchableCombobox';
import UseFieldOptions from '../hooks/UseFieldOptions';
import DateRangeWidget from './DateRangeWidget';
import { ContentHttpService } from '../services';

interface UseCasesSearchProps {
  onSearch: (query: string) => void;
  themeId?: number;
  pageSize?: number;
  onPageSizeChange?: (pageSize: number) => void;
  searchType?: string;
  onSearchTypeChange?: (searchType: string) => void;
}


const GEOGRAPHY_REGIONS = [
  "Global",
  "EMEA",
  "AMER",
  "APAC"
];



type DateRangeWidgetValue = {
  preset: string;
  dateRange: { startDate: string; endDate: string };
  monthRange: { startMonth: number; startYear: number; endMonth: number; endYear: number };
  yearRange: { startYear: number; endYear: number };
};

const UseCasesSearch: React.FC<UseCasesSearchProps> = ({ onSearch, themeId, pageSize = 10, onPageSizeChange, searchType = 'basic' }) => {
  const [searchText, setSearchText] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [extractEntity, setExtractEntity] = useState(true);
  const [enforceEntityMatch, setEnforceEntityMatch] = useState(false);
  const [savedSearches, setSavedSearches] = useState<any[]>([]);
  const [savingSearchName, setSavingSearchName] = useState('');
  const [filters, setFilters] = useState({
    company: '',
    industry: '',
    technology: '',
    impact: '',
    useCaseType: '',
    performanceImprovementCategory: '',
    geography: '',
    country: '',
    tools: '',
    dateRange: { startDate: '', endDate: '' },
    datePreset: null as string | null,
    monthRange: { startMonth: 0, startYear: new Date().getFullYear(), endMonth: 0, endYear: new Date().getFullYear() },
    yearRange: { startYear: new Date().getFullYear(), endYear: new Date().getFullYear() },
    notNullField: '',
    minRelevanceScore: '',
  });
  const [sortConfig, setSortConfig] = useState({
    field: 'created_at',
    direction: 'desc'
  });
  const [hasFilters, setHasFilters] = useState(false);

  const { data: fieldOptions } = UseFieldOptions(themeId);


  // Define sortable fields
  const sortableFields = [
    { value: 'relevance_score', label: 'Relevance Score' },
    { value: 'credibility_score', label: 'Credibility Score' },
    { value: 'created_at', label: 'Created Date' },
    // { value: 'updated_at', label: 'Updated Date' },
    { value: 'use_case_date', label: 'Impact Date' },
    { value: 'published_date', label: 'Source Published Date' },
    { value: 'company', label: 'Company' },
    { value: 'industry', label: 'Industry' },
    { value: 'use_case_type', label: 'Use Case Type' },
    { value: 'performance_impact', label: 'Performance Impact' },
    { value: 'performance_improvement_category', label: 'Performance Improvement Category' },
    { value: 'geography', label: 'Geography' },
    { value: 'country', label: 'Country' },
    { value: 'tools', label: 'Tools' }
  ];

  // Check if any filters are applied
  useEffect(() => {
    const hasActiveFilters =
      filters.company !== '' ||
      filters.industry !== '' ||
      filters.technology !== '' ||
      filters.impact !== '' ||
      filters.useCaseType !== '' ||
      filters.performanceImprovementCategory !== '' ||
      filters.geography !== '' ||
      filters.country !== '' ||
      filters.tools !== '' ||
      filters.notNullField !== '' ||
      filters.minRelevanceScore !== '' ||
      (filters.datePreset !== null && filters.dateRange.startDate !== '' && filters.dateRange.endDate !== '');
    setHasFilters(Boolean(hasActiveFilters));
  }, [filters]);


  // Load saved searches on component mount
  const loadSavedSearches = useCallback(async () => {
    try {
      const data: any = await ContentHttpService.loadSavedSearches(false, 20);
      setSavedSearches(data.results || []);
    } catch (error) {
      console.error('Error loading saved searches:', error);
    }
  }, []);

  useEffect(() => {
    loadSavedSearches();
  }, [loadSavedSearches]);

  const handleSaveSearch = async () => {
    if (!savingSearchName.trim()) {
      alert('Please enter a name for this search');
      return;
    }

    try {
      await ContentHttpService.createSavedSearch({
        display_name: savingSearchName,
        entity_name: searchText,
        entity_type: 'company',
        strict_matching: enforceEntityMatch,
        additional_filters: filters,
      });

      setSavingSearchName('');
      setShowSaveModal(false);
      loadSavedSearches();
      alert('Search saved successfully!');
    } catch (error) {
      console.error('Error saving search:', error);
      alert('Error saving search');
    }
  };

  const handleLoadSavedSearch = async (savedSearch: any) => {
    setSearchText(savedSearch.entity_name);
    setEnforceEntityMatch(savedSearch.strict_matching);
    if (savedSearch.additional_filters) {
      setFilters({ ...filters, ...savedSearch.additional_filters });
    }

    // Track usage
    try {
      await ContentHttpService.trackSavedSearchUsage(savedSearch.id);
    } catch (error) {
      console.error('Error tracking usage:', error);
    }
    
    // Auto-execute search with loaded saved search
    setTimeout(() => {
      handleSearch();
    }, 100);
  };


  const handleSearch = () => {
    let queryString = '';
    
    // Add basic search if exists
    if (searchText.trim() !== '') {
      queryString += `&search=${encodeURIComponent(searchText.trim())}`;
      // Add entity extraction parameters
      queryString += `&extract_entity=${extractEntity}`;
      queryString += `&enforce_entity_match=${enforceEntityMatch}`;
    }

    // Add theme_id if it exists
    if (themeId) {
      queryString += `&theme_id=${themeId}`;
    }

    // Add sorting parameters
    queryString += `&sort_by=${sortConfig.field}&sort_direction=${sortConfig.direction}`;
    if(sortConfig.field !== 'created_at' || sortConfig.direction !== 'desc') {
      setHasFilters(true);
    }

    // Add advanced filters if they exist
    if (filters.company) {
      queryString += `&company=${encodeURIComponent(filters.company)}`;
    }
    
    if (filters.industry) {
      queryString += `&industry=${encodeURIComponent(filters.industry)}`;
    }
    
    if (filters.technology) {
      queryString += `&technology=${encodeURIComponent(filters.technology)}`;
    }
    
    if (filters.impact) {
      queryString += `&performance_impact=${encodeURIComponent(filters.impact)}`;
    }

    if (filters.useCaseType) {
      queryString += `&use_case_type=${encodeURIComponent(filters.useCaseType)}`;
    }

    if (filters.performanceImprovementCategory) {
      queryString += `&performance_improvement_category=${encodeURIComponent(filters.performanceImprovementCategory)}`;
    }

    if (filters.geography) {
      queryString += `&geography=${encodeURIComponent(filters.geography)}`;
    }

    if (filters.country) {
      queryString += `&country=${encodeURIComponent(filters.country)}`;
    }
    
    if (filters.tools) {
      queryString += `&tools=${encodeURIComponent(filters.tools)}`;
    }

    if (filters.dateRange.startDate && filters.dateRange.endDate) {
      queryString += `&start_date=${filters.dateRange.startDate}&end_date=${filters.dateRange.endDate}`;
    }

    // Add not null field filter if set
    if (filters.notNullField) {
      queryString += `&not_null_field=${encodeURIComponent(filters.notNullField)}`;
    }

    // Add minimum relevance score filter if set
    if (filters.minRelevanceScore) {
      queryString += `&min_relevance_score=${encodeURIComponent(filters.minRelevanceScore)}`;
    }

    onSearch(queryString);
  };

  const handleReset = () => {
    setSearchText('');
    setFilters({
      company: '',
      industry: '',
      technology: '',
      impact: '',
      useCaseType: '',
      performanceImprovementCategory: '',
      geography: '',
      country: '',
      tools: '',
      dateRange: { startDate: '', endDate: '' },
      datePreset: null as string | null,
      monthRange: { startMonth: 0, startYear: new Date().getFullYear(), endMonth: 0, endYear: new Date().getFullYear() },
      yearRange: { startYear: new Date().getFullYear(), endYear: new Date().getFullYear() },
      notNullField: '',
      minRelevanceScore: '',
    });
    setSortConfig({
      field: 'created_at',
      direction: 'desc'
    });
    onSearch('');
  };

  const handleApplyFilters = () => {
    handleSearch();
    setShowModal(false);
  };

  // Handle form submission to prevent page refresh
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  };

  // Handle key press in search input
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  };

  // Check if there's any search or filters applied
  const hasSearchOrFilters = searchText !== '' || hasFilters;

  // Build active filters display
  const activeFiltersList = () => {
    const active = [];
    if (filters.company) active.push({ label: 'Company', value: filters.company });
    if (filters.industry) active.push({ label: 'Industry', value: filters.industry });
    if (filters.technology) active.push({ label: 'Technology', value: filters.technology });
    if (filters.impact) active.push({ label: 'Impact', value: filters.impact });
    if (filters.useCaseType) active.push({ label: 'Use Case Type', value: filters.useCaseType });
    if (filters.performanceImprovementCategory) active.push({ label: 'Performance Category', value: filters.performanceImprovementCategory });
    if (filters.geography) active.push({ label: 'Region', value: filters.geography });
    if (filters.country) active.push({ label: 'Country', value: filters.country });
    if (filters.tools) active.push({ label: 'Tools', value: filters.tools });
    if (filters.minRelevanceScore) active.push({ label: 'Min Score', value: filters.minRelevanceScore });
    return active;
  };

  const clearFilter = (filterKey: string) => {
    switch (filterKey) {
      case 'company':
        setFilters({ ...filters, company: '' });
        break;
      case 'industry':
        setFilters({ ...filters, industry: '' });
        break;
      case 'technology':
        setFilters({ ...filters, technology: '' });
        break;
      case 'impact':
        setFilters({ ...filters, impact: '' });
        break;
      case 'useCaseType':
        setFilters({ ...filters, useCaseType: '' });
        break;
      case 'performanceImprovementCategory':
        setFilters({ ...filters, performanceImprovementCategory: '' });
        break;
      case 'geography':
        setFilters({ ...filters, geography: '' });
        break;
      case 'country':
        setFilters({ ...filters, country: '' });
        break;
      case 'tools':
        setFilters({ ...filters, tools: '' });
        break;
      case 'minRelevanceScore':
        setFilters({ ...filters, minRelevanceScore: '' });
        break;
    }
  };

  return (
    <div className="">
      <Form onSubmit={handleSubmit} className='d-flex align-items-center  gap-2'>
          <InputGroup className=""> 
            <Form.Control
              placeholder="Search use cases..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onKeyPress={handleKeyPress}
              size="sm"
            />
            <Button variant="primary"  size="sm" onClick={handleSearch}>
              <i className="ri-search-2-line"></i>
            </Button>
          </InputGroup>

          <div className="d-flex align-items-center gap-2">
            <label htmlFor="useCasesPageSize" className="me-1 mb-0" style={{ fontSize: '0.85rem' }}>Top results:</label>
            <select 
              id="useCasesPageSize"
              className="form-select form-select-sm"
              style={{ width: '70px' }}
              value={pageSize}
              onChange={(e) => {
                const newSize = parseInt(e.target.value);
                onPageSizeChange?.(newSize);
              }}
            >
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
            </select>
          </div>

          {/* Saved Searches Dropdown */}
          {savedSearches.length > 0 && (
            <div className="d-flex align-items-center gap-2">
              <label htmlFor="savedSearches" className="me-1 mb-0" style={{ fontSize: '0.85rem' }}>
                <i className="ri-bookmark-line"></i> Saved:
              </label>
              <select 
                id="savedSearches"
                className="form-select form-select-sm"
                style={{ width: '150px' }}
                defaultValue=""
                onChange={(e) => {
                  if (e.target.value) {
                    const saved = savedSearches.find(s => s.id === parseInt(e.target.value));
                    if (saved) {
                      handleLoadSavedSearch(saved);
                    }
                    // Reset dropdown
                    e.target.value = '';
                  }
                }}
              >
                <option value="">-- Load saved search --</option>
                {savedSearches.map(search => (
                  <option key={search.id} value={search.id}>
                    {search.display_name} ({search.usage_count} uses)
                  </option>
                ))}
              </select>
            </div>
          )}

          <Button 
            variant={hasFilters ? "success" : "outline-secondary"}
            size="sm" 
            onClick={() => setShowModal(true)}
            title="Advanced Filters"
            style={{width: '220px'}}
          >
            <i className="ri-filter-line"></i> Advanced Filters
          </Button>

          {/* Save Current Search Button */}
          {searchText.trim() && (
            <Button 
              variant="outline-info" 
              size="sm" 
              onClick={() => setShowSaveModal(true)}
              title="Save this search for quick access"
            >
              <i className="ri-bookmark-add-line"></i> Save
            </Button>
          )}

          {hasSearchOrFilters && (
            <Button 
              variant="outline-danger" 
              size="sm" 
              onClick={handleReset}
              title="Reset"
            >
              <i className="ri-close-line"></i>
            </Button>
          )}
      </Form>

      {/* Active Filters Display */}
      {activeFiltersList().length > 0 && (
        <div className="mt-3 p-3 bg-light rounded" style={{ borderLeft: '4px solid #0d6efd' }}>
          <div className="d-flex flex-wrap gap-2 align-items-center">
            <span style={{ fontSize: '0.85rem', fontWeight: '500', color: '#666' }}>
              <i className="ri-filter-2-line me-2"></i>Active Filters:
            </span>
            {activeFiltersList().map((filter, idx) => (
              <span
                key={idx}
                className="badge bg-primary d-flex align-items-center gap-1"
                style={{ fontSize: '0.8rem', padding: '0.5rem 0.75rem' }}
              >
                <strong>{filter.label}:</strong> {filter.value}
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  aria-label="Remove filter"
                  onClick={() => {
                    const keys = ['company', 'industry', 'technology', 'impact', 'useCaseType', 'performanceImprovementCategory', 'geography', 'country', 'tools', 'minRelevanceScore'];
                    const filterKey = keys.find(k => filters[k as keyof typeof filters] === filter.value);
                    if (filterKey) clearFilter(filterKey);
                  }}
                  style={{ width: '14px', height: '14px', marginLeft: '4px' }}
                />
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Filters Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Advanced Filters</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row className="g-3">
            {/* Entity Extraction Section */}
            {searchText.trim() !== '' && (
              <>
                <Col md={12} className="border-bottom pb-3">
                  <h6 className="mb-3">
                    <i className="ri-search-line me-2"></i>
                    Entity Extraction
                  </h6>
                  <Form.Group className="mb-3">
                    <Form.Check
                      type="checkbox"
                      id="extract-entity"
                      label="Auto-detect Company/Person from search query"
                      checked={extractEntity}
                      onChange={(e) => setExtractEntity(e.target.checked)}
                      className="mb-2"
                    />
                    <Form.Text className="text-muted d-block">
                      When enabled, the system will identify the company or person name in your search and prioritize results for that entity.
                    </Form.Text>
                  </Form.Group>
                  
                  <Form.Group className="mb-3">
                    <Form.Check
                      type="checkbox"
                      id="enforce-entity-match"
                      label="Strict Entity Matching (only show results for detected entity)"
                      checked={enforceEntityMatch}
                      onChange={(e) => setEnforceEntityMatch(e.target.checked)}
                      disabled={!extractEntity}
                      className="mb-2"
                    />
                    <Form.Text className="text-muted d-block">
                      When enabled, results will be limited to the specific company/person detected. Disable to see related results.
                    </Form.Text>
                  </Form.Group>
                </Col>
              </>
            )}
            
            <Col md={12}>
              <Form.Group>
                <Form.Label>Sort By</Form.Label>
                <Row className="g-2">
                  <Col md={8}>
                    <Form.Select
                      value={sortConfig.field}
                      onChange={(e) => setSortConfig({ ...sortConfig, field: e.target.value })}
                    >
                      {sortableFields.map(field => (
                        <option key={field.value} value={field.value}>
                          {field.label}
                        </option>
                      ))}
                    </Form.Select>
                  </Col>
                  <Col md={4}>
                    <Form.Select
                      value={sortConfig.direction}
                      onChange={(e) => setSortConfig({ ...sortConfig, direction: e.target.value })}
                    >
                      <option value="asc">Ascending</option>
                      <option value="desc">Descending</option>
                    </Form.Select>
                  </Col>
                </Row>
              </Form.Group>
            </Col>

            <Col md={6}>
              <SearchableCombobox
                options={fieldOptions?.useCaseTypes || []}
                value={filters.useCaseType}
                onChange={(value) => setFilters({ ...filters, useCaseType: value })}
                placeholder="Enter use case type"
                label="Use Case Type"
              />
            </Col>

            <Col md={6}>
              <SearchableCombobox
                options={fieldOptions?.companies || []}
                value={filters.company}
                onChange={(value) => setFilters({ ...filters, company: value })}
                placeholder="Enter company name"
                label="Company"
              />
            </Col>

            <Col md={6}>
              <SearchableCombobox
                options={fieldOptions?.industries || []}
                value={filters.industry}
                onChange={(value) => setFilters({ ...filters, industry: value })}
                placeholder="Enter industry"
                label="Industry"
              />
            </Col>

            <Col md={6}>
              <SearchableCombobox
                options={fieldOptions?.impacts || []}
                value={filters.impact}
                onChange={(value) => setFilters({ ...filters, impact: value })}
                placeholder="Enter impact"
                label="Performance Impact"
              />
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Region</Form.Label>
                <Form.Select
                  value={filters.geography}
                  onChange={(e) => setFilters({ ...filters, geography: e.target.value })}
                >
                  <option value="">Select a region</option>
                  {GEOGRAPHY_REGIONS.map(region => (
                    <option key={region} value={region}>
                      {region}
                    </option>
                  ))}
                </Form.Select>
              </Form.Group>
            </Col>

            <Col md={6}>
              <SearchableCombobox
                options={fieldOptions?.countries || []}
                value={filters.country}
                onChange={(value) => setFilters({ ...filters, country: value })}
                placeholder="Enter country"
                label="Country"
              />
            </Col>

            <Col md={6}>
              <SearchableCombobox
                options={fieldOptions?.tools || []}
                value={filters.tools}
                onChange={(value) => setFilters({ ...filters, tools: value })}
                placeholder="Enter tools"
                label="Tools"
              />
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Minimum Relevance Score</Form.Label>
                <Form.Control
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={filters.minRelevanceScore}
                  onChange={(e) => setFilters({ ...filters, minRelevanceScore: e.target.value })}
                  placeholder="e.g., 5"
                />
                <Form.Text className="text-muted">
                  Filter out results with relevance score below this value (0-10)
                </Form.Text>
              </Form.Group>
            </Col>

            <hr className='mt-3' />


            <Col md={12} className='mt-0'>
              <DateRangeWidget
                value={{
                  preset: filters.datePreset || '',
                  dateRange: filters.dateRange,
                  monthRange: filters.monthRange,
                  yearRange: filters.yearRange,
                }}
                onChange={(
                  { preset, dateRange, monthRange, yearRange }: DateRangeWidgetValue
                ) => {
                  setFilters({
                    ...filters,
                    datePreset: preset || null,
                    dateRange: dateRange,
                    monthRange: monthRange,
                    yearRange: yearRange,
                  });
                }}
              />
            </Col>

            <hr className='my-3' />

            <Col md={12}>
              <Form.Group>
                <Form.Check
                  type="checkbox"
                  id="not-null-performance-impact"
                  label="Only show use cases with Performance Impact"
                  checked={filters.notNullField === 'performance_impact'}
                  onChange={(e) => setFilters({ ...filters, notNullField: e.target.checked ? 'performance_impact' : '' })}
                />
              </Form.Group>
            </Col>
          </Row>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleApplyFilters}>
            Apply Filters
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Save Search Modal */}
      <Modal show={showSaveModal} onHide={() => setShowSaveModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Save Search</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group>
            <Form.Label>Search Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="e.g., Siemens Sustainability Research"
              value={savingSearchName}
              onChange={(e) => setSavingSearchName(e.target.value)}
            />
            <Form.Text className="text-muted">
              Give this search a memorable name so you can find it quickly later.
            </Form.Text>
          </Form.Group>
          <hr />
          <h6>Search Details:</h6>
          <small>
            <p><strong>Entity:</strong> {searchText}</p>
            <p><strong>Strict Matching:</strong> {enforceEntityMatch ? 'Yes' : 'No'}</p>
            <p><strong>Auto-detect:</strong> {extractEntity ? 'Enabled' : 'Disabled'}</p>
          </small>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowSaveModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSaveSearch}>
            Save Search
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default UseCasesSearch; 
