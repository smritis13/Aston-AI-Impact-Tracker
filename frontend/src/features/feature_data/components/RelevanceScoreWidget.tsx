import React from 'react';

interface RelevanceScoreWidgetProps {
  score: number;
}

const RelevanceScoreWidget: React.FC<RelevanceScoreWidgetProps> = ({ score }) => {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'success';
    if (score >= 5) return 'warning';
    return 'danger';
  };

  return (
    <span 
      title="Relevancy score based on how relevant the use case is to the prompt. 10 is the highest and 1 is the lowest."
      className={`badge bg-${getScoreColor(score)}`}
    >
      {score}
    </span>
  );
};

export default RelevanceScoreWidget; 