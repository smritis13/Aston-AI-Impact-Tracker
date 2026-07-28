import React, { useState } from 'react';

interface TruncatedDescriptionWidgetProps {
  description: string;
  maxLength?: number;
}

const TruncatedDescriptionWidget: React.FC<TruncatedDescriptionWidgetProps> = ({ 
  description, 
  maxLength = 100 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!description || description.length <= maxLength) {
    return <span>{description}</span>;
  }
  
  const truncatedText = description.substring(0, maxLength) + '...';
  
  return (
    <div>
      <span>{isExpanded ? description : truncatedText}</span>
      <button 
        type="button"
        className="btn btn-link text-muted btn-sm p-0 ms-1" 
        onClick={(event) => {
          event.stopPropagation();
          setIsExpanded(!isExpanded);
        }}
      >
        {isExpanded ? 'Show less' : 'Show more'}
      </button>
    </div>
  );
};

export default TruncatedDescriptionWidget; 
