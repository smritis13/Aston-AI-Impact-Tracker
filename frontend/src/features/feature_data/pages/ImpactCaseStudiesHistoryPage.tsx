import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Container, Row, Col, Card, CardBody, Table, Spinner, Alert, Button } from "react-bootstrap";
import MainLayout from "core/components/layout/MainLayout";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import { ContentHttpService } from "../services";
import { useToast } from "../hooks/useToast";
import "./ImpactCaseStudyPage.css";

interface ImpactCaseStudy {
  id: number;
  title: string;
  theme?: string;
  created_at: string;
  status: string;
  summary?: string;
}

const ImpactCaseStudiesHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [studies, setStudies] = useState<ImpactCaseStudy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchStudies();
  }, []);

  const fetchStudies = async () => {
    try {
      setIsLoading(true);
      setError(null);
      // Fetch impact case studies from the backend (stored as reports)
      const response: any = await ContentHttpService.loadReports();
      if (response) {
        // Filter reports to show only impact case studies that were actually
        // compiled. Every search run creates a Report row too (it's how live
        // progress/status/cost tracking works while a search is in flight),
        // but a search-only run never writes a narrative - report_generation_skipped
        // is set on those - so it isn't a "report" from the user's point of view
        // and shouldn't clutter this history list.
        const reportList = Array.isArray(response.results) ? response.results : (Array.isArray(response) ? response : []);
        setStudies(reportList
          .filter((report: any) => report.metadata?.report_type === 'impact_case_study' && !report.metadata?.report_generation_skipped)
          .map((report: any) => ({
            id: report.id,
            title: report.query || report.topic || 'Untitled Report',
            theme: report.metadata?.theme_id || '-',
            created_at: report.created_at,
            status: (report.metadata?.status || (report.generated_report ? 'completed' : 'error')).toLowerCase(),
            summary: report.generated_report ? 'Generated REF evidence pack' : ''
          })));
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.error || err?.message || "Failed to load case studies";
      setError(errorMessage);
      showToast({ message: errorMessage, type: "error" });
      console.error("Failed to fetch case studies:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, studyId: number) => {
    e.stopPropagation();
    setDeletingId(studyId);
  };

  const confirmDelete = async (studyId: number) => {
    try {
      setIsDeleting(true);
      // Delete the report from the backend
      await ContentHttpService.deleteReport(studyId);
      showToast({ 
        message: "Case study deleted successfully", 
        type: "success" 
      });
      setDeletingId(null);
      // Refresh the list
      fetchStudies();
    } catch (err: any) {
      const errorMessage = err?.response?.data?.error || err?.message || "Failed to delete case study";
      showToast({ 
        message: errorMessage, 
        type: "error" 
      });
      console.error("Failed to delete case study:", err);
    } finally {
      setIsDeleting(false);
    }
  };

  const cancelDelete = () => {
    setDeletingId(null);
  };

  return (
    <MainLayout>
      <div className="impact-case-study-container">
        <Container fluid style={{ minHeight: '100%' }}>
          <Row className="mb-4">
            <Col>
              <BreadcrumbWidget 
                mainTitle="Impact Case Studies" 
                breadcrumbs={[]} 
              />
            </Col>
          </Row>

          <Row className="mb-4">
            <Col>
              <h1 className="page-title">Impact Case Studies History</h1>
              <p className="page-subtitle">
                View all previously generated impact case study reports
              </p>
            </Col>
          </Row>

          {error && (
            <Row className="mb-3">
              <Col>
                <Alert variant="danger" dismissible onClose={() => setError(null)}>
                  {error}
                </Alert>
              </Col>
            </Row>
          )}

          <Row>
            <Col>
              <Card className="history-card">
                <CardBody>
                  {isLoading ? (
                    <div className="text-center py-5">
                      <Spinner animation="border" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </Spinner>
                      <p className="mt-3">Loading case studies...</p>
                    </div>
                  ) : studies.length === 0 ? (
                    <div className="text-center py-5">
                      <p className="text-muted">No case studies found yet. Create one to get started!</p>
                    </div>
                  ) : (
                    <div className="table-responsive">
                      <Table hover className="mb-0">
                        <thead>
                          <tr>
                            <th style={{ width: '80px' }}>ID</th>
                            <th>Title</th>
                            <th>Theme</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Summary</th>
                            <th style={{ width: '120px' }}>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {studies.map((study) => (
                            <tr 
                              key={study.id}
                              onClick={() => navigate(`/impact-case-studies/${study.id}`)}
                              style={{ cursor: 'pointer' }}
                              role="button"
                              tabIndex={0}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                  navigate(`/impact-case-studies/${study.id}`);
                                }
                              }}
                            >
                              <td className="fw-bold">#{study.id}</td>
                              <td className="fw-bold">{study.title}</td>
                              <td>{study.theme || '-'}</td>
                              <td>
                                <span className={`badge bg-${study.status === 'completed' ? 'success' : ['failed', 'error'].includes(study.status) ? 'danger' : 'warning'}`}>
                                  {study.status}
                                </span>
                              </td>
                              <td>{formatDate(study.created_at)}</td>
                              <td className="text-truncate" style={{ maxWidth: '200px' }}>
                                {study.summary || '-'}
                              </td>
                              <td onClick={(e) => e.stopPropagation()}>
                                {deletingId === study.id ? (
                                  <div className="d-flex gap-2">
                                    <Button 
                                      variant="danger" 
                                      size="sm"
                                      onClick={() => confirmDelete(study.id)}
                                      disabled={isDeleting}
                                    >
                                      {isDeleting ? 'Deleting...' : 'Confirm'}
                                    </Button>
                                    <Button 
                                      variant="secondary" 
                                      size="sm"
                                      onClick={cancelDelete}
                                      disabled={isDeleting}
                                    >
                                      Cancel
                                    </Button>
                                  </div>
                                ) : (
                                  <Button 
                                    variant="outline-danger" 
                                    size="sm"
                                    onClick={(e) => handleDeleteClick(e, study.id)}
                                  >
                                    Delete
                                  </Button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </div>
                  )}
                </CardBody>
              </Card>
            </Col>
          </Row>
        </Container>
      </div>
    </MainLayout>
  );
};

export default ImpactCaseStudiesHistoryPage;
