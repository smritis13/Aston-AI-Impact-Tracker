import HttpService from 'core/services/Http/HttpService';
import React from 'react';
import { Dropdown } from 'react-bootstrap';


interface ExportButtonsProps {
  endpointUrl: string;
  queryParams?: Record<string, string>;
  searchQuery?: string;
  themeId?: number;
}

const ExportButtons: React.FC<ExportButtonsProps> = ({ endpointUrl, queryParams = {}, searchQuery = '',themeId }) => {
  const handleExport = (format: string) => {

    var httpService = new HttpService();
    var baseUrl = httpService.getApiUrl();

    var finalUrl = baseUrl + endpointUrl;
    // Create a URL with the export parameter
    const url = new URL(finalUrl, window.location.origin);
    
    // Add the export format parameter
    url.searchParams.append('export', format);

    if (themeId) {
      url.searchParams.append('theme_id', themeId.toString());
    }
    
    // Add any additional query parameters
    Object.entries(queryParams).forEach(([key, value]) => {
      if (value) {
        url.searchParams.append(key, value);
      }
    });
    
    // If searchQuery is provided and it's a full query string (starts with &)
    if (searchQuery) {
      // Remove the leading & if present
      const queryString = searchQuery.startsWith('&') ? searchQuery.substring(1) : searchQuery;
      
      // Parse the query string and add each parameter to the URL
      const searchParams = new URLSearchParams(queryString);
      searchParams.forEach((value, key) => {
        url.searchParams.append(key, value);
      });
    }
    
    // Open the URL in a new tab
    window.open(url.toString(), '_blank');
  };

  return (
    <Dropdown>
      <Dropdown.Toggle variant="outline-secondary" size="sm" id="export-dropdown">
        <i className="ri-download-2-line me-1"></i> Export
      </Dropdown.Toggle>

      <Dropdown.Menu>
        <Dropdown.Item onClick={() => handleExport('csv')}>
          <i className="ri-file-list-3-line me-2"></i> CSV
        </Dropdown.Item>
        <Dropdown.Item onClick={() => handleExport('excel')}>
          <i className="ri-file-excel-2-line me-2"></i> Excel
        </Dropdown.Item>
        <Dropdown.Item onClick={() => handleExport('json')}>
          <i className="ri-code-s-slash-line me-2"></i> JSON
        </Dropdown.Item>
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default ExportButtons; 