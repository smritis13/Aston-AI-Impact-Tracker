import React from 'react';
import { useAISDLCReport } from '../hooks/useAISDLCReport';
import Loading from "core/components/Loading";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import UrlSourceWidget from './UrlSourceWidget';

interface AISDLCUseCaseListViewProps {
  report_id?: number;
}

const AISDLCUseCaseListView: React.FC<AISDLCUseCaseListViewProps> = ({ report_id }) => {
  const { useCases, isLoading } = useAISDLCReport({report_id: report_id,page:1, pageSize:30});
  
  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };
  
  return (
    <div className="mb-3">
      {isLoading && <Loading isLoading={isLoading} />}
      
      
      
      {!isLoading && (!useCases || useCases.length === 0) && (
        <div className="alert alert-info" role="alert">
          No AI SDLC use cases found.
        </div>
      )}
      
      {useCases && useCases.length > 0 && (
        <div className="table-responsive">
          <table className="table table-bordered">
            <thead className="table-light">
              <tr>
                <th>#</th>
                <th>Company</th>
                <th>Phase</th>
                <th>Use Case</th>
                <th>Description</th>
                <th>Tools</th>
                <th>Performance Improvements</th>
                <th>Date</th>
                <th>Source</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {useCases.map((useCase,index) => (
                <tr key={useCase.id}>
                  <td>{index+1}</td>
                  <td>{useCase.phase || 'N/A'}</td>
                  <td>{useCase.use_case || 'N/A'}</td>
                  <td>{useCase.description || 'N/A'}</td>
                  <td>
                    {useCase.tools ? (
                      useCase.tools.split(',').map((tool, index) => (
                        <span key={index} className="badge bg-primary me-1">
                          {tool.trim()}
                        </span>
                      ))
                    ) : (
                      ''
                    )}
                  </td>
                  <td>{useCase.performance_improvements || 'N/A'}</td>
                  <td>{formatDate(useCase.date)}</td>
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

export default AISDLCUseCaseListView; 