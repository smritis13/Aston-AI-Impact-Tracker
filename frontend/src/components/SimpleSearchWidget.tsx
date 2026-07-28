import React, { useState } from 'react';
import './SearchWidget.css';

interface SimpleSearchWidgetProps {
  onSearch: (query: string) => void;
  placeholder?: string;
}

const SimpleSearchWidget: React.FC<SimpleSearchWidgetProps> = ({ 
  onSearch, 
  placeholder = "Search..." 
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  return (
    <div className="search-widget">
      <form onSubmit={handleSearch} className="d-flex align-items-center">
        <div className="input-group">
          <span className="input-group-text bg-white border-end-0">
            <i className="bi bi-search text-muted"></i>
          </span>
          <input
            type="text"
            className="form-control border-start-0"
            placeholder={placeholder}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button
            type="submit"
            className="btn btn-primary"
          >
            Search
          </button>
        </div>
      </form>
    </div>
  );
};

export default SimpleSearchWidget; 