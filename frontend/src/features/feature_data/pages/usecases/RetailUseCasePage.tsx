import React, { useState } from 'react';
import { useRetailUseCases } from '../../hooks/useRetailUseCases';
import MainLayout from "core/components/layout/MainLayout";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import UrlSourceWidget from '../../components/UrlSourceWidget';
import RetailUseCasesSearch from '../../components/RetailUseCasesSearch';
import TruncatedDescriptionWidget from '../../components/TruncatedDescriptionWidget';
import Pagination from 'core/components/shared/Pagination';
import ExportButtons from 'core/components/shared/ExportButtons';
import PusherListener from 'features/feature_chat/components/PusherListener';
const RetailUseCasePage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(30);
  const [searchQuery, setSearchQuery] = useState('');
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [currentThought, setCurrentThought] = useState<string>('');
  const { useCases, totalCount, isLoading } = useRetailUseCases({ 
    page, 
    pageSize,
    searchQuery 
  });
  
  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString();
  };
  
  // Get credibility score class
  const getCredibilityClass = (score: number) => {
    if (score >= 4) return 'badge bg-success';
    if (score >= 3) return 'badge bg-info';
    if (score >= 2) return 'badge bg-warning';
    return 'badge bg-danger';
  };

  // Handle search from the search widget
  const handleSearch = (queryString: string) => {
    setSearchQuery(queryString);
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
          mainTitle={`Retail Use Cases (${totalCount})`}
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Reports" },
            { title: "Retail Use Cases" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0"></h5>
                <div className="d-flex align-items-center gap-2">
                  <RetailUseCasesSearch 
                    onSearch={handleSearch}
                  />
                  <ExportButtons endpointUrl="/content/retail-use-cases/" searchQuery={searchQuery} />
                </div>
              </div>
              
              <div className="card-body">
                {isLoading && <Loading isLoading={isLoading} />}
                
                {!isLoading && (!useCases || useCases.length === 0) && (
                  <div className="alert alert-info" role="alert">
                    No retail use cases found.
                  </div>
                )}
                
                {useCases && useCases.length > 0 && (
                  <>
                    {searchQuery && (
                      <div className="alert alert-info mb-3">
                        Showing results for: <strong>{searchQuery}</strong>
                        <button 
                          className="btn btn-sm btn-link float-end" 
                          onClick={() => {
                            setSearchQuery('');
                            setPage(1);
                          }}
                        >
                          Clear search
                        </button>
                      </div>
                    )}
                    
                    <div className="table-responsive">
                      <table className="table table-bordered">
                        <thead className="table-light">
                          <tr>
                            <th>ID</th>
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
                              <td>{useCase.id}</td>
                              <td className="col-md-2">{useCase.company}</td>
                              <td className="col-md-2">{useCase.use_case}</td>
                              <td className="col-md-4">
                                <TruncatedDescriptionWidget description={useCase.description} maxLength={100} />
                              </td>
                              <td>
                                {useCase.technology_used.split(',').map((tech: string, index: number) => (
                                  <span key={index} className="badge bg-primary me-1 mb-1" style={{ maxWidth: '150px', fontWeight: 'normal', fontSize: '12px', overflowWrap: 'break-word', whiteSpace: 'normal' }}>
                                    {tech.trim()}
                                  </span>
                                ))}
                              </td>
                              <td className="col-md-4"><TruncatedDescriptionWidget description={useCase.impact} maxLength={100} /></td>
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
                            Last updated: <TimeAgoWidget date={new Date().toISOString()} />
                          </div>
                        </div>
                        
                        {!searchQuery && (
                          <Pagination
                            currentPage={page}
                            totalItems={totalCount}
                            pageSize={pageSize}
                            onPageChange={handlePageChange}
                          />
                        )}
                      </div>

                      <PusherListener streamKey="ai_sdlc" onThoughtReceived={handleThoughtReceived} />
                        {currentThought && (
                          <div className="alert alert-info mt-3" role="alert">
                            {currentThought}
                          </div>
                        )}  
                    </div>
                    
                    {useCases.length === 0 && (
                      <div className="alert alert-warning" role="alert">
                        No results found matching your search criteria.
                      </div>
                    )}
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

export default RetailUseCasePage; 