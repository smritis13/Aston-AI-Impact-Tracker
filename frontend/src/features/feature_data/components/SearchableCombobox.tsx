import React, { useState, useEffect, useRef } from 'react';
import { Form, InputGroup } from 'react-bootstrap';

interface SearchableComboboxProps {
  options: string[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  label: string;
}

const SearchableCombobox: React.FC<SearchableComboboxProps> = ({
  options,
  value,
  onChange,
  placeholder,
  label
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchText, setSearchText] = useState(value);
  const [filteredOptions, setFilteredOptions] = useState<string[]>(options);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    setFilteredOptions(
      options.filter(option =>
        option.toLowerCase().includes(searchText.toLowerCase())
      )
    );
  }, [searchText, options]);

  const handleSelect = (option: string) => {
    onChange(option);
    setSearchText(option);
    setIsOpen(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setSearchText(newValue);
    onChange(newValue);
    setIsOpen(true);
  };

  return (
    <Form.Group ref={containerRef} className="position-relative">
      <Form.Label>{label}</Form.Label>
      <InputGroup>
        <Form.Control
          type="text"
          placeholder={placeholder}
          value={searchText}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
        />
        <InputGroup.Text
          onClick={() => setIsOpen(!isOpen)}
          style={{ cursor: 'pointer' }}
        >
          <i className={`ri-arrow-${isOpen ? 'up' : 'down'}-s-line`}></i>
        </InputGroup.Text>
      </InputGroup>
      {isOpen && filteredOptions.length > 0 && (
        <div
          className="position-absolute w-100 bg-white border rounded mt-1"
          style={{ zIndex: 1000, maxHeight: '200px', overflowY: 'auto' }}
        >
          {filteredOptions.map((option, index) => (
            <div
              key={index}
              className="p-2 hover-bg-light cursor-pointer"
              onClick={() => handleSelect(option)}
              style={{ cursor: 'pointer' }}
            >
              {option}
            </div>
          ))}
        </div>
      )}
    </Form.Group>
  );
};

export default SearchableCombobox; 