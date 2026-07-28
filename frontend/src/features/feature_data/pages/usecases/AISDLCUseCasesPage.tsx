import React, { useState } from 'react';
import { useAISDLCReport } from '../../hooks/useAISDLCReport';
import MainLayout from "core/components/layout/MainLayout";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import UrlSourceWidget from '../../components/UrlSourceWidget';
import AISDLCUseCasesSearch from '../../components/AISDLCUseCasesSearch';
import TruncatedDescriptionWidget from '../../components/TruncatedDescriptionWidget';
import Pagination from 'core/components/shared/Pagination';
import ExportButtons from 'core/components/shared/ExportButtons';
import PusherListener from 'features/feature_chat/components/PusherListener';

const AISDLCUseCasesPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(30);
  const [searchQuery, setSearchQuery] = useState('');
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [currentThought, setCurrentThought] = useState<string>('');

  const { useCases, totalCount, isLoading, handleGenerateReport, isGenerating } = useAISDLCReport({
    page,
    pageSize,
    searchQuery
  });
  
  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString();
  };

  // Handle search from the new search widget
  const handleSearch = (queryString: string) => {
    setSearchQuery(queryString);
    console.log(queryString);
    setPage(1); // Reset to first page when searching
  };
  
  // Handle page change
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleThoughtReceived = (thought: string) => {
    console.log(thought);
    setThoughts([...thoughts, thought]);
    setCurrentThought(thought);
  };
  
  return (
    <MainLayout>
      <div className="container-fluid">
        <BreadcrumbWidget
          mainTitle={`AI SDLC Use Cases (${totalCount})`}
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Reports" },
            { title: "AI SDLC Use Cases" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">
              <div className="card-header  d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0 "></h5>
                <div className="d-flex align-items-center gap-2">
                  <AISDLCUseCasesSearch onSearch={handleSearch} />
                  <ExportButtons endpointUrl="/content/ai-sdlc-use-cases/" searchQuery={searchQuery} />
                </div>
              </div>
              
              <div className="card-body">
                
                
                {isLoading && <Loading isLoading={isLoading} />}
                
                {!isLoading && (!useCases || useCases.length === 0) && (
                  <div className="alert alert-info" role="alert">
                    No AI SDLC use cases found. Generate a report to get started.
                  </div>
                )}
                
                {useCases && useCases.length > 0 && (
                  <>
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
                          {useCases.map((useCase) => (
                            <tr key={useCase.id}>
                              <td>{useCase.id}</td>
                              <td className="col-md-2">{useCase.company}</td>
                              <td className="col-md-2">{useCase.phase}</td>
                              <td className="col-md-2">{useCase.use_case}</td>
                              <td className="col-md-4">
                                <TruncatedDescriptionWidget description={useCase.description} maxLength={100} />
                              </td>
                              <td>
                                {useCase.tools.split(',').map((tool: string, index: number) => (
                                  <span key={index} className="badge bg-primary me-1 mb-1" style={{ maxWidth: '150px', fontWeight: 'normal', fontSize: '12px', overflowWrap: 'break-word', whiteSpace: 'normal' }}>
                                    {tool.trim()}
                                  </span>
                                ))}
                              </td>
                              <td className="col-md-4"><TruncatedDescriptionWidget description={useCase.performance_improvements} maxLength={100} /></td>
                              <td>{formatDate(useCase.date)}</td>
                              <td>
                                {useCase.source ? (
                                  <UrlSourceWidget source={useCase.source} />
                                ) : (
                                  ''
                                )}
                              </td>
                              <td>
                                <TimeAgoWidget date={useCase.created_at} />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>

                      <div className="d-flex justify-content-between align-items-center mt-3">
                        <div className="last-update">
                          <div className="d-flex align-items-center gap-2">
                            <div
                              className="btn-md me-2"
                              onClick={() => handleGenerateReport('')}
                            >
                              {isGenerating ? (
                                <>
                                  <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                                  Generating...
                                </>
                              ) : (
                                <>
                                  <i className="ri-play-circle-line align-middle me-1"></i>
                                  Generate Report
                                </>
                              )}
                            </div>
                            Last updated: <TimeAgoWidget date={new Date().toISOString()} />

                            
                          </div>
                        </div>

                        <Pagination
                          currentPage={page}
                          totalItems={totalCount}
                          pageSize={pageSize}
                          onPageChange={handlePageChange}
                        />
                      </div>

                      <PusherListener streamKey="ai_sdlc" onThoughtReceived={handleThoughtReceived} />
                          {currentThought && (
                            <div className="alert alert-info mt-3" role="alert">
                              {currentThought}
                            </div>
                          )}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default AISDLCUseCasesPage; 