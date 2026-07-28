import React, { useState, useEffect } from 'react';
import { Form, Button, InputGroup, Row, Col, Modal } from 'react-bootstrap';

interface AISDLCUseCasesSearchProps {
  onSearch: (queryString: string) => void;
}

const AISDLCUseCasesSearch: React.FC<AISDLCUseCasesSearchProps> = ({ onSearch }) => {
  const [searchText, setSearchText] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [filters, setFilters] = useState({
    phase: '',
    dateRange: {
      startDate: '',
      endDate: ''
    },
    tools: '',
    performanceImprovements: '',
  });
  const [hasFilters, setHasFilters] = useState(false);

  // Check if any filters are applied
  useEffect(() => {
    const hasActiveFilters = 
      filters.phase !== '' || 
      filters.tools !== '' || 
      filters.performanceImprovements !== '' || 
      (filters.dateRange.startDate !== '' && filters.dateRange.endDate !== '');
    
    setHasFilters(hasActiveFilters);
  }, [filters]);

  const handleSearch = () => {
    let queryString = '';
    
    // Add basic search if exists
    if (searchText) {
      queryString += `&search=${encodeURIComponent(searchText)}`;
    }

    // Add advanced filters if they exist
    if (filters.phase) {
      queryString += `&phase=${encodeURIComponent(filters.phase)}`;
    }
    
    if (filters.tools) {
      queryString += `&tools=${encodeURIComponent(filters.tools)}`;
    }
    
    if (filters.performanceImprovements) {
      queryString += `&performance_improvements=${encodeURIComponent(filters.performanceImprovements)}`;
    }
    
    if (filters.dateRange.startDate && filters.dateRange.endDate) {
      queryString += `&start_date=${filters.dateRange.startDate}&end_date=${filters.dateRange.endDate}`;
    }

    onSearch(queryString);
  };

  const handleReset = () => {
    setSearchText('');
    setFilters({
      phase: '',
      dateRange: {
        startDate: '',
        endDate: ''
      },
      tools: '',
      performanceImprovements: '',
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

  return (
    <div className="" style={{ }}>
      <Form onSubmit={handleSubmit}>
        <InputGroup className="">
          <Form.Control
            placeholder="Search use cases..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyPress={handleKeyPress}
            size="sm"
          />
          <Button variant="primary" size="sm" onClick={handleSearch}>
            <i className="ri-search-2-line"></i>
          </Button>
          <Button 
            variant={hasFilters ? "success" : "outline-secondary"}
            size="sm" 
            onClick={() => setShowModal(true)}
            title="Advanced Filters"
          >
            <i className="ri-filter-line"></i>
          </Button>
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
        </InputGroup>
      </Form>

      {/* Advanced Filters Modal */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Advanced Filters</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row className="g-3">
            <Col md={6}>
              <Form.Group>
                <Form.Label>Phase</Form.Label>
                <Form.Select
                  value={filters.phase}
                  onChange={(e) => setFilters({ ...filters, phase: e.target.value })}
                >
                  <option value="">Select Phase</option>
                  <option value="planning">Planning</option>
                  <option value="development">Development</option>
                  <option value="testing">Testing</option>
                  <option value="deployment">Deployment</option>
                  <option value="maintenance">Maintenance</option>
                </Form.Select>
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Tools</Form.Label>
                <Form.Control
                  placeholder="Enter tools"
                  value={filters.tools}
                  onChange={(e) => setFilters({ ...filters, tools: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Performance Improvements</Form.Label>
                <Form.Control
                  placeholder="Enter improvements"
                  value={filters.performanceImprovements}
                  onChange={(e) => setFilters({ ...filters, performanceImprovements: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Date Range</Form.Label>
                <Row className="g-2">
                  <Col>
                    <Form.Control
                      type="date"
                      value={filters.dateRange.startDate}
                      onChange={(e) => setFilters({
                        ...filters,
                        dateRange: { ...filters.dateRange, startDate: e.target.value }
                      })}
                    />
                  </Col>
                  <Col>
                    <Form.Control
                      type="date"
                      value={filters.dateRange.endDate}
                      onChange={(e) => setFilters({
                        ...filters,
                        dateRange: { ...filters.dateRange, endDate: e.target.value }
                      })}
                    />
                  </Col>
                </Row>
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
    </div>
  );
};

export default AISDLCUseCasesSearch; 