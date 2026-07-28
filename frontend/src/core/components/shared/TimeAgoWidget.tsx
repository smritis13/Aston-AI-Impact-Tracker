import React, { useState } from "react";
import Utils from "core/utils";

interface TimeAgoWidgetProps {
  date: string | Date;
}

const TimeAgoWidget: React.FC<TimeAgoWidgetProps> = ({ date }) => {
  const [showFullDate, setShowFullDate] = useState(false);
  const dateObj = new Date(date);
  const today = new Date();
  
  // Check if the provided date is the same day as today.
  const isSameDay = dateObj.toDateString() === today.toDateString();

  // Set the circle icon class based on whether it's today or not.
  const circleClass = isSameDay ? "text-success bx bxs-circle me-1" : "text-secondary bx bxs-circle me-1";

  const toggleDisplay = () => {
    setShowFullDate((prev) => !prev);
  };

  const displayText = showFullDate 
    ? Utils.formatDate(dateObj,true)
    : Utils.timeAgo(date);

  return (
    <span 
      onClick={toggleDisplay} 
      style={{ cursor: "pointer", fontSize: "10px" }} 
      title="Click to toggle display"
    >
      <i className={circleClass}></i>
      {displayText}
    </span>
  );
};

export default TimeAgoWidget;
