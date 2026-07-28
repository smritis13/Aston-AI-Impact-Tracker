import React, { useState, useEffect } from 'react';
import { Form, Button, InputGroup, Row, Col, Modal } from 'react-bootstrap';

interface RetailSDLCUseCasesSearchProps {
  onSearch: (queryString: string) => void;
}

const RetailSDLCUseCasesSearch: React.FC<RetailSDLCUseCasesSearchProps> = ({ onSearch }) => {
  const [searchText, setSearchText] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [filters, setFilters] = useState({
    company: '',
    industrySegment: '',
    sdlcTools: '',
    metricImpact: '',
    dateRange: {
      startDate: '',
      endDate: ''
    },
  });
  const [hasFilters, setHasFilters] = useState(false);

  // Check if any filters are applied
  useEffect(() => {
    const hasActiveFilters = 
      filters.company !== '' || 
      filters.industrySegment !== '' || 
      filters.sdlcTools !== '' || 
      filters.metricImpact !== '' || 
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
    if (filters.company) {
      queryString += `&company=${encodeURIComponent(filters.company)}`;
    }
    
    if (filters.industrySegment) {
      queryString += `&industry_segment=${encodeURIComponent(filters.industrySegment)}`;
    }
    
    if (filters.sdlcTools) {
      queryString += `&sdlc_tools=${encodeURIComponent(filters.sdlcTools)}`;
    }
    
    if (filters.metricImpact) {
      queryString += `&metric_impact=${encodeURIComponent(filters.metricImpact)}`;
    }
    
    if (filters.dateRange.startDate && filters.dateRange.endDate) {
      queryString += `&start_date=${filters.dateRange.startDate}&end_date=${filters.dateRange.endDate}`;
    }

    onSearch(queryString);
  };

  const handleReset = () => {
    setSearchText('');
    setFilters({
      company: '',
      industrySegment: '',
      sdlcTools: '',
      metricImpact: '',
      dateRange: {
        startDate: '',
        endDate: ''
      },
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
    <div className="">
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
                <Form.Label>Company</Form.Label>
                <Form.Control
                  placeholder="Enter company name"
                  value={filters.company}
                  onChange={(e) => setFilters({ ...filters, company: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Industry Segment</Form.Label>
                <Form.Control
                  placeholder="Enter industry segment"
                  value={filters.industrySegment}
                  onChange={(e) => setFilters({ ...filters, industrySegment: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>SDLC Tools</Form.Label>
                <Form.Control
                  placeholder="Enter SDLC tools"
                  value={filters.sdlcTools}
                  onChange={(e) => setFilters({ ...filters, sdlcTools: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Metric Impact</Form.Label>
                <Form.Control
                  placeholder="Enter metric impact"
                  value={filters.metricImpact}
                  onChange={(e) => setFilters({ ...filters, metricImpact: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={12}>
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

export default RetailSDLCUseCasesSearch; 