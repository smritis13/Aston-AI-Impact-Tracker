import React from 'react';
import { useSLDCReport } from '../hooks/useSLDCReport';
import Loading from "core/components/Loading";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import UrlSourceWidget from './UrlSourceWidget';

interface SDLCUseCaseListViewProps {
  report_id?: number;
}

const SDLCUseCaseListView: React.FC<SDLCUseCaseListViewProps> = ({ report_id }) => {
  const { useCases, isLoading } = useSLDCReport({ report_id: report_id, page: 1, pageSize: 100 });
  
  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };
  
  // Get credibility score class
  const getCredibilityClass = (score: number) => {
    if (score >= 4) return 'badge bg-success';
    if (score >= 3) return 'badge bg-info';
    if (score >= 2) return 'badge bg-warning';
    return 'badge bg-danger';
  };
  
  return (
    <div className="mb-3">
      {isLoading && <Loading isLoading={isLoading} />}
      
      {!isLoading && (!useCases || useCases.length === 0) && (
        <div className="alert alert-info" role="alert">
          No SDLC use cases found.
        </div>
      )}
      
      {useCases && useCases.length > 0 && (
        <div className="table-responsive">
          <table className="table table-bordered">
            <thead className="table-light">
              <tr>
                <th>#</th>
                <th>Company</th>
                <th>Industry Segment</th>
                <th>SDLC Tools</th>
                <th>Use Case Description</th>
                <th>Metric Impact</th>
                <th>Date</th>
                <th>Credibility</th>
                <th>Source</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {useCases.map((useCase) => (
                <tr key={useCase.id}>
                  <td>{useCase.id}</td>
                  <td>{useCase.company}</td>
                  <td>{useCase.industry_segment || 'N/A'}</td>
                  <td>
                    {useCase.sdlc_tools.split(',').map((tool, index) => (
                      <span key={index} className="badge bg-primary me-1">
                        {tool.trim()}
                      </span>
                    ))}
                  </td>
                  <td>{useCase.use_case_description}</td>
                  <td>{useCase.metric_impact || 'N/A'}</td>
                  <td>{formatDate(useCase.date)}</td>
                  <td>
                    <span className={getCredibilityClass(useCase.credibility_score)}>
                      {useCase.credibility_score.toFixed(1)}
                    </span>
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
      )}
    </div>
  );
};

export default SDLCUseCaseListView; 