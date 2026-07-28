import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from 'react-bootstrap';
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import UrlSourceWidget from './UrlSourceWidget';
import TruncatedDescriptionWidget from './TruncatedDescriptionWidget';
import UseCaseDetails from './UseCaseDetails';

interface UseCase {
  id: number;
  use_case_name: string;
  use_case_type: string;
  company: string;
  industry: string;
  tools: string;
  use_case_description: string;
  performance_impact: string;
  performance_improvement_category: string | null;
  geography: string | null;
  country: string | null;
  use_case_date: string;
  source: string;
  created_at: string;
  credibility_reasoning: string;
  credibility_score: number;
  is_credible: boolean;
  is_relevant: boolean;
  relevance_reasoning: string;
  relevance_score: number;
}

interface UseCasesWidgetProps {
  useCases: UseCase[];
}

const UseCasesWidget: React.FC<UseCasesWidgetProps> = ({ useCases }) => {
  const [selectedUseCase, setSelectedUseCase] = useState<UseCase | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  if (useCases.length === 0) return null;

  const handleUseCaseClick = (useCase: UseCase) => {
    setSelectedUseCase(useCase);
    setShowDetails(true);
  };

  return (
    <Card className="mb-4">
      
      <CardBody>
        <div className="table-responsive">
          <table className="table table-bordered">
            <thead className="table-light">
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Company</th>
                <th>Industry</th>
                <th>Tools</th>
                <th>Description</th>
                <th>Impact</th>
                <th>Source</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {useCases.map((useCase, index) => (
                <tr key={index}>
                  <td>
                    <a 
                      href="#" 
                      className="p-0 text-decoration-none" 
                      onClick={(e) => {
                        e.preventDefault();
                        handleUseCaseClick(useCase);
                      }}
                    >
                      {useCase.use_case_name}
                    </a>
                  </td>
                  <td>{useCase.use_case_type}</td>
                  <td>{useCase.company}</td>
                  <td>{useCase.industry}</td>
                  <td>
                    {useCase.tools.split(',').map((tool: string, index: number) => (
                      <span key={index} className="badge bg-primary me-1 mb-1" style={{ maxWidth: '150px', fontWeight: 'normal', fontSize: '12px', overflowWrap: 'break-word', whiteSpace: 'normal' }}>
                        {tool.trim()}
                      </span>
                    ))}
                  </td>
                  <td>
                    <TruncatedDescriptionWidget description={useCase.use_case_description} maxLength={100} />
                  </td>
                  <td>
                    <TruncatedDescriptionWidget description={useCase.performance_impact} maxLength={100} />
                  </td>
                  <td>
                    {useCase.source ? (
                      <UrlSourceWidget source={useCase.source} />
                    ) : (
                      'N/A'
                    )}
                  </td>
                  <td>
                    <TimeAgoWidget date={useCase.created_at} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardBody>

      <UseCaseDetails
        useCase={selectedUseCase}
        show={showDetails}
        onHide={() => setShowDetails(false)}
      />
    </Card>
  );
};

export default UseCasesWidget; 