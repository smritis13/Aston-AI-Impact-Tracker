import React, { useState } from "react";

interface TagsWidgetProps {
  tags: string[];
}

const TagsWidget: React.FC<TagsWidgetProps> = ({ tags }) => {
  const [expanded, setExpanded] = useState(false);

  const displayedTags = expanded ? tags : tags.slice(0, 3);

  return (
    <div>
      {displayedTags.map((tag, index) => (
        <span key={index} className="badge bg-primary me-1">
          {tag}
        </span>
      ))}
      {tags.length > 3 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="btn btn-link p-0"
        >
          {expanded ? "View Less" : "View More"}
        </button>
      )}
    </div>
  );
};

export default TagsWidget;
