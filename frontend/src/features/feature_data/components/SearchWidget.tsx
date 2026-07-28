import React, { useState } from 'react';

interface SearchWidgetProps {
  onSearch: (query: string) => void;
}

const SearchWidget: React.FC<SearchWidgetProps> = ({ onSearch }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSearch(query);
  };

  return (
    <div className="search-widget">
      <input
        type="text"
        className="form-control"
        placeholder="Search use cases..."
        value={searchQuery}
        onChange={handleSearch}
      />
    </div>
  );
};

export default SearchWidget; 