import React, { useState } from 'react';

interface ExpandableDescriptionProps {
  text: string;
  maxLength?: number;
  className?: string;
}

const ExpandableDescription: React.FC<ExpandableDescriptionProps> = ({
  text,
  maxLength = 100,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const shouldTruncate = text.length > maxLength;

  if (!shouldTruncate) {
    return <span className={className}>{text}</span>;
  }

  const displayText = isExpanded ? text : `${text.slice(0, maxLength)}...`;

  return (
    <span className={className}>
      {displayText}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="btn btn-link btn-sm p-0 ms-1 text-muted"
        style={{ textDecoration: 'none' }}
      >
        {isExpanded ? 'Show less' : 'Show more'}
      </button>
    </span>
  );
};

export default ExpandableDescription; 