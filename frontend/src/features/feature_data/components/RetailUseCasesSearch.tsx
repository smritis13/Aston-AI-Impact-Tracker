import React, { useState, useEffect } from 'react';
import { Form, Button, InputGroup, Row, Col, Modal } from 'react-bootstrap';

interface RetailUseCasesSearchProps {
  onSearch: (queryString: string) => void;
}

const RetailUseCasesSearch: React.FC<RetailUseCasesSearchProps> = ({ onSearch }) => {
  const [searchText, setSearchText] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [filters, setFilters] = useState({
    company: '',
    industry: '',
    technology: '',
    impact: '',
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
      filters.industry !== '' || 
      filters.technology !== '' || 
      filters.impact !== '' || 
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
    
    if (filters.industry) {
      queryString += `&industry=${encodeURIComponent(filters.industry)}`;
    }
    
    if (filters.technology) {
      queryString += `&technology=${encodeURIComponent(filters.technology)}`;
    }
    
    if (filters.impact) {
      queryString += `&impact=${encodeURIComponent(filters.impact)}`;
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
      industry: '',
      technology: '',
      impact: '',
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
            placeholder="Search retail use cases..."
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
      <Modal show={showModal} onHide={() => setShowModal(false)}>
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
                <Form.Label>Industry</Form.Label>
                <Form.Control
                  placeholder="Enter industry"
                  value={filters.industry}
                  onChange={(e) => setFilters({ ...filters, industry: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Technology</Form.Label>
                <Form.Control
                  placeholder="Enter technology"
                  value={filters.technology}
                  onChange={(e) => setFilters({ ...filters, technology: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Impact</Form.Label>
                <Form.Control
                  placeholder="Enter impact"
                  value={filters.impact}
                  onChange={(e) => setFilters({ ...filters, impact: e.target.value })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>Start Date</Form.Label>
                <Form.Control
                  type="date"
                  value={filters.dateRange.startDate}
                  onChange={(e) => setFilters({ 
                    ...filters, 
                    dateRange: { ...filters.dateRange, startDate: e.target.value } 
                  })}
                />
              </Form.Group>
            </Col>

            <Col md={6}>
              <Form.Group>
                <Form.Label>End Date</Form.Label>
                <Form.Control
                  type="date"
                  value={filters.dateRange.endDate}
                  onChange={(e) => setFilters({ 
                    ...filters, 
                    dateRange: { ...filters.dateRange, endDate: e.target.value } 
                  })}
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
    </div>
  );
};

export default RetailUseCasesSearch; 