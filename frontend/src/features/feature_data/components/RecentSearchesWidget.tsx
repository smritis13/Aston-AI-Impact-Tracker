import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spinner, Card, CardBody, Alert } from 'react-bootstrap';
import TimeAgoWidget from 'core/components/shared/TimeAgoWidget';
import ExpandableDescription from 'core/components/shared/ExpandableDescription';
import { ContentHttpService } from '../services';
import './RecentSearchesWidget.css';

interface RecentReport {
  id: number;
  query: string;
  topic: string;
  created_at: string;
  metadata?: {
    report_type?: string;
  };
}

interface RecentSearchesWidgetProps {
  limit?: number;
  showViewAll?: boolean;
  title?: string;
  className?: string;
}

const RecentSearchesWidget: React.FC<RecentSearchesWidgetProps> = ({
  limit = 5,
  showViewAll = true,
  title = "Recent Searches",
  className = ""
}) => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<RecentReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRecentReports();
  }, []);

  const fetchRecentReports = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response: any = await ContentHttpService.loadReports();
      
      if (response && Array.isArray(response.results)) {
        // Sort by created_at and get the most recent ones
        const sorted = response.results
          .sort((a: any, b: any) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          )
          .slice(0, limit);
        
        setReports(sorted);
      } else if (Array.isArray(response)) {
        const sorted = response
          .sort((a: any, b: any) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          )
          .slice(0, limit);
        
        setReports(sorted);
      }
    } catch (err: any) {
      console.error('Error fetching recent reports:', err);
      setError('Failed to load recent searches');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReportClick = (reportId: number, reportType?: string) => {
    if (reportType === 'impact_case_study') {
      navigate(`/impact-case-studies/${reportId}`);
    } else {
      navigate(`/report/${reportId}`);
    }
  };

  return (
    <Card className={`recent-searches-widget ${className}`}>
      <CardBody className="p-4">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="card-title mb-0">{title}</h5>
          {reports.length > 0 && showViewAll && (
            <button
              className="btn btn-link btn-sm"
              onClick={() => navigate('/reports')}
              style={{ textDecoration: 'none' }}
            >
              View All →
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="text-center py-4">
            <Spinner animation="border" size="sm" className="mb-2" />
            <p className="text-muted small">Loading searches...</p>
          </div>
        ) : error ? (
          <Alert variant="warning" className="mb-0">
            {error}
          </Alert>
        ) : reports.length === 0 ? (
          <div className="text-center py-4">
            <p className="text-muted mb-0">No searches yet. Create one to get started!</p>
          </div>
        ) : (
          <div className="recent-searches-list">
            {reports.map((report, index) => (
              <div
                key={report.id}
                className="recent-search-item"
                onClick={() => handleReportClick(report.id, report.metadata?.report_type)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleReportClick(report.id, report.metadata?.report_type);
                  }
                }}
              >
                <div className="search-item-header">
                  <div className="search-query">
                    <span className="search-number">{index + 1}.</span>
                    <ExpandableDescription 
                      text={report.query || report.topic || 'Untitled'} 
                      maxLength={60} 
                    />
                  </div>
                  {report.metadata?.report_type === 'impact_case_study' && (
                    <span className="badge bg-info ms-2">Impact Case Study</span>
                  )}
                </div>
                <div className="search-item-meta">
                  <TimeAgoWidget date={report.created_at} />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default RecentSearchesWidget;
