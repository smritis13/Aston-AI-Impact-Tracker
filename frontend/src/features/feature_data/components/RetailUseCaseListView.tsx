import React from 'react';
import { useRetailUseCases } from '../hooks/useRetailUseCases';
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import UrlSourceWidget from './UrlSourceWidget';
interface RetailUseCaseListViewProps {
  report_id?: number;
}

const RetailUseCaseListView: React.FC<RetailUseCaseListViewProps> = ({ report_id }) => {
  const { useCases, isLoading } = useRetailUseCases({ report_id: report_id, page: 1, pageSize: 100 });
  
  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };
  
  return (
    <div className="mb-3">
        {useCases && useCases.length > 0 && (
          <div className="table-responsive">
            <table className="table table-bordered">
              <thead className="table-light">
                <tr>
                  <th>Company</th>
                  <th>Use Case</th>
                  <th>Description</th>
                  <th>Technology Used</th>
                  <th>Impact</th>
                  <th>Date</th>
                  <th>Source</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {useCases.map((useCase) => (
                  <tr key={useCase.id}>
                    <td>{useCase.company}</td>
                    <td>{useCase.use_case}</td>
                    <td>{useCase.description}</td>
                    <td>
                      {useCase.technology_used.split(',').map((tech, index) => (
                        <span key={index} className="badge bg-primary me-1">
                          {tech.trim()}
                        </span>
                      ))}
                    </td>
                    <td>{useCase.impact || '-'}</td>
                    <td>{formatDate(useCase.date)}</td>
                    <td>
                      {useCase.source ? (
                        <UrlSourceWidget source={useCase.source} />
                      ) : (
                        '-'
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

export default RetailUseCaseListView; 