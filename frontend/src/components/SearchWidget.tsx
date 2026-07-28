import React, { useState } from 'react';
import './SearchWidget.css';
import AdvancedSearchModal from './AdvancedSearchModal';

interface SearchWidgetProps {
  onSearch: (query: string) => void;
  onAdvancedSearch: (filters: any) => void;
}

const SearchWidget: React.FC<SearchWidgetProps> = ({ onSearch, onAdvancedSearch }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  const handleAdvancedSearch = (filters: any) => {
    onAdvancedSearch(filters);
    setIsModalOpen(false);
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
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={() => setIsModalOpen(true)}
          >
            <i className="bi bi-funnel me-1"></i>
            Filter
          </button>
        </div>
      </form>

      <AdvancedSearchModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSearch={handleAdvancedSearch}
      />
    </div>
  );
};

export default SearchWidget; 