import React, { useState, useEffect, useCallback } from 'react';
import { useUseCases } from '../../hooks/useUseCases';
import { useTheme } from '../../hooks/useTheme';
import { useParams, useSearchParams } from 'react-router-dom';
import MainLayout from "core/components/layout/MainLayout";
import Loading from "core/components/Loading";
import Error from "core/components/Error";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import UrlSourceWidget from '../../components/UrlSourceWidget';
import UseCasesSearch from '../../components/UseCasesSearch';
import TruncatedDescriptionWidget from '../../components/TruncatedDescriptionWidget';
import Pagination from 'core/components/shared/Pagination';
import ExportButtons from 'core/components/shared/ExportButtons';
import PusherListener from 'features/feature_chat/components/PusherListener';
import UseCaseDetails, { CONTENT_TYPE_LABELS } from '../../components/UseCaseDetails';
import RelevanceScoreWidget from '../../components/RelevanceScoreWidget';
import FeatureThemeWidget from '../../components/FeatureThemeWidget';
import {ContentHttpService} from '../../services/index';
import Utils from 'core/utils';
import { useToast } from '../../hooks/useToast';

const UseCasesPage: React.FC = () => {
  const { themeId, themeSlug } = useParams<{ themeId: string; themeSlug?: string }>();
  const [searchParams] = useSearchParams();
  const reportIdParam = searchParams.get('report_id');
  const reportId = reportIdParam ? parseInt(reportIdParam) : undefined;
  const { showToast } = useToast();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('basic');
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [currentThought, setCurrentThought] = useState<string>('');
  const [errorMessages, setErrorMessages] = useState<string[]>([]);
  const [selectedUseCase, setSelectedUseCase] = useState<any>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [activeReportId, setActiveReportId] = useState<number | null>(reportId || null);
  const [progress, setProgress] = useState<number>(0);
  const [prevThemeId, setPrevThemeId] = useState(themeId);

  // Reset to page 1 whenever the selected theme changes. UseCasesPage is reused
  // across /usecases/:themeId navigations (React Router doesn't remount it), so
  // without this the page number from the previously viewed theme carries over
  // and can be out of range for a theme with fewer results.
  if (themeId !== prevThemeId) {
    setPrevThemeId(themeId);
    setPage(1);
  }

  const { theme, loading: themeLoading } = useTheme(themeId ? parseInt(themeId) : undefined);
  const { useCases, totalCount, isLoading, handleGenerateReport, handleDeleteUseCase, refetch, silentRefetch } = useUseCases({
    page,
    pageSize,
    searchQuery,
    themeId: themeId ? parseInt(themeId) : undefined,
    reportId,
    sortBy: 'relevance_score',
    sortDirection: 'desc'
  });



  useEffect(() => {
    const checkReportStatus = async () => {
      if (themeId) {
        try {
          const report:any = await ContentHttpService.findReportByTheme(parseInt(themeId));
          
          setReport(report);
          setIsGenerating(report.metadata?.status === 'RUNNING');
        } catch (error) {
          console.error('Error checking report status:', error);
          setIsGenerating(false);
        }
      }
    };

    checkReportStatus();
  }, [themeId]);

  // Memoized so its identity stays stable across renders — it's passed to
  // PusherListener, whose subscription effect resubscribes (dropping the live
  // connection, and with it any events sent during the reconnect gap)
  // whenever this reference changes.
  const handleThoughtReceived = useCallback((thought: string) => {
    setThoughts(prev => [...prev, thought]);
    setCurrentThought(thought);
    if (
      thought.startsWith('[ERROR]') ||
      thought.startsWith('Web search request failed') ||
      thought.startsWith('Search failed due to an error')
    ) {
      const clean = thought
        .replace(/^\[ERROR\]\s*/, '')
        .replace(/^Web search request failed:\s*/, 'Search provider error: ')
        .replace(/^Search failed due to an error:\s*/, 'Fatal error: ');
      setErrorMessages(prev => [...prev, clean]);
    }
  }, []);
  
  const handleStopGeneration = async () => {
    try {
      await ContentHttpService.stopReportGeneration(themeId ? parseInt(themeId) : undefined);
      setIsGenerating(false);
    } catch (error) {
      console.error('Error stopping report generation:', error);
    }
  };

  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    // Year-only (e.g. "2024") or year-month (e.g. "2024-03") — display as-is
    // to avoid JS parsing "2024" as 1 Jan 2024 UTC.
    if (/^\d{4}$/.test(dateString)) return dateString;
    if (/^\d{4}-\d{2}$/.test(dateString)) {
      const [year, month] = dateString.split('-');
      return `${month}/${year}`;
    }
    return new Date(dateString).toLocaleDateString();
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

  const handleUseCaseClick = (useCase: any) => {
    setSelectedUseCase(useCase);
    setShowDetails(true);
  };

  const handleUseCaseReceived = useCallback((_useCase: any) => {
    silentRefetch();
  }, [silentRefetch]);

  const handleProgress = useCallback((progress: number) => {
    setProgress(progress);
  }, []);

  const handleStartGeneration = useCallback(async () => {
    setIsGenerating(true);
    setErrorMessages([]);
    setCurrentThought('');
    setProgress(0);
    try {
      const response: any = await handleGenerateReport(themeId ? parseInt(themeId) : undefined);
      if (response?.report_id) {
        // The backend streams on a report-specific channel. Subscribing with
        // the theme id meant the page missed every live result until refresh.
        setActiveReportId(response.report_id);
        setReport((previous: any) => ({ ...(previous || {}), id: response.report_id, metadata: { status: 'RUNNING' } }));
      }
    } catch {
      setIsGenerating(false);
    }
  }, [handleGenerateReport, themeId]);

  const handleComplete = useCallback((status: 'success' | 'stopped' | 'error', message?: string) => {
    setIsGenerating(false);
    setActiveReportId(null);
    setCurrentThought('');
    switch (status) {
      case 'success':
        showToast({
          type: 'success',
          title: 'Search completed',
          message: 'Use case search completed successfully.'
        });
        break;
      case 'stopped':
        showToast({
          type: 'warning',
          title: 'Search stopped',
          message: 'Use case search was stopped by user request.'
        });
        break;
      case 'error':
        showToast({
          type: 'error',
          title: 'Search failed',
          message: message || 'An error occurred during the use case search.'
        });
        if (message) {
          setErrorMessages(prev => [
            ...prev,
            message.replace(/^Search failed due to an error:\s*/, 'Fatal error: ')
          ]);
        }
        break;
    }
    refetch();
  }, [showToast, refetch]);

  // Pusher-only completion detection has no fallback if a single event is
  // missed (tab backgrounded, brief reconnect) - the UI is then stuck
  // showing "generating" forever even though the backend already finished.
  // ImpactCaseStudyPage already polls as a safety net for exactly this;
  // this page didn't, so a missed event here left users staring at a
  // search that looked stuck when it had actually completed.
  useEffect(() => {
    if (!isGenerating || !themeId) return;

    const pollReportStatus = async () => {
      try {
        const latestReport: any = await ContentHttpService.findReportByTheme(parseInt(themeId));
        setReport(latestReport);
        const status = (latestReport?.metadata?.status || '').toLowerCase();
        const percent = latestReport?.metadata?.progress?.percent;
        if (typeof percent === 'number') {
          setProgress(Math.round(percent));
        }
        if (status === 'completed') {
          handleComplete('success');
        } else if (status === 'failed' || status === 'error') {
          handleComplete('error', latestReport?.metadata?.error);
        } else if (status === 'stopped') {
          handleComplete('stopped');
        }
      } catch (err) {
        console.error('Error polling report status:', err);
      }
    };

    const intervalId = window.setInterval(pollReportStatus, 5000);
    return () => window.clearInterval(intervalId);
  }, [isGenerating, themeId, handleComplete]);

  return (
    <MainLayout>
      <div className="container-fluid">
        <BreadcrumbWidget
          mainTitle={`Use Cases ${themeId ? `- ${theme?.title.replace('-', ' ') || themeSlug || `Theme ${themeId}`}` : ''}`}
          subTitle={totalCount ? `(${(page - 1) * pageSize + 1}-${Math.min(page * pageSize, totalCount)} of ${totalCount})` : ''}
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Use Case Library", url: "/usecases" },
            { title: themeId ? theme?.title.replace('-', ' ') || themeSlug || `Theme ${themeId}` : "All Use Cases" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="card-title mb-0">
                <UseCasesSearch 
                    onSearch={handleSearch}
                    themeId={themeId ? parseInt(themeId) : undefined}
                    pageSize={pageSize}
                    onPageSizeChange={(newSize) => {
                      setPageSize(newSize);
                      setPage(1); // Reset to page 1 when changing page size
                    }}
                    searchType={searchType}
                    onSearchTypeChange={(newType) => {
                      setSearchType(newType);
                      setPage(1); // Reset to page 1 when changing search type
                    }}
                  />
                </h5>
                <div className="d-flex align-items-center gap-2">
                  
                  <ExportButtons endpointUrl="/content/use-cases/" searchQuery={searchQuery} themeId={themeId ? parseInt(themeId) : undefined} />

                    <div className="last-update">
                      {themeId && (
                        <div className="d-flex align-items-center gap-2">
                              <>
                                {isGenerating ? (
                                  <button
                                    className="btn btn-outline-danger p-1 me-2"
                                    onClick={handleStopGeneration}
                                  >
                                    <i className="ri-stop-circle-line align-middle me-1"></i>
                                    Stop                                 </button>
                                ) : (
                                  <button
                                    className="btn btn-outline-success p-1 me-2"
                                  onClick={handleStartGeneration}
                                  >
                                    <i className="ri-play-circle-line align-middle me-1"></i>
                                    Refresh
                                  </button>
                                )}
                              </>
                            <small style={{ fontSize: "10px" }}>Last updated: <TimeAgoWidget date={report?.updated_at} /></small>
                            {report?.metadata?.token_usage && (
                              <small className="text-muted ms-2" style={{ fontSize: "10px" }} title="OpenAI LLM usage for the run that populated this theme">
                                <i className="ri-flashlight-line me-1"></i>
                                OpenAI: {report.metadata.token_usage.calls} call{report.metadata.token_usage.calls === 1 ? "" : "s"} ·{" "}
                                {report.metadata.token_usage.total_tokens.toLocaleString()} tokens
                              </small>
                            )}
                            {report?.metadata?.search_api_usage && (
                              <small className="text-muted ms-2" style={{ fontSize: "10px" }} title="Tavily web search calls for the run that populated this theme">
                                <i className="ri-search-line me-1"></i>
                                Tavily: {report.metadata.search_api_usage.calls_total} call{report.metadata.search_api_usage.calls_total === 1 ? "" : "s"}
                              </small>
                            )}
                            {report?.metadata?.tavily_usage && (
                              <small
                                className={`ms-2 ${report.metadata.tavily_usage.status === 'available' ? 'text-muted' : 'text-danger'}`}
                                style={{ fontSize: "10px" }}
                                title={report.metadata.tavily_usage.message || 'Tavily API credit status'}
                              >
                                <i className="ri-coins-line me-1"></i>
                                {report.metadata.tavily_usage.status === 'available'
                                  ? `Tavily credits: ${report.metadata.tavily_usage.key_usage ?? '?'} / ${report.metadata.tavily_usage.key_limit ?? '?'}`
                                  : `Tavily: ${report.metadata.tavily_usage.message || 'usage unavailable'}`}
                              </small>
                            )}
                          </div>
                        )}
                    </div>
                    {themeId && <FeatureThemeWidget themeId={parseInt(themeId)} />}

                </div>
              </div>
              
              <div className="card-body">
                {/* Progress bar for report generation */}
                {progress>0 && (
                  <div className="mb-3">
                    <div className="progress" style={{ height: '8px' }}>
                      <div
                        className="progress-bar progress-bar-striped progress-bar-animated bg-info"
                        role="progressbar"
                        style={{ width: `${progress}%` }}
                        aria-valuenow={progress}
                        aria-valuemin={0}
                        aria-valuemax={100}
                      ></div>
                    </div>
                    <div className="text-end small text-muted mt-1">{progress}%</div>
                  </div>
                )}
                
                {/* Error panel — shown whenever the backend streams an error during generation */}
                {errorMessages.length > 0 && (
                  <div className="alert alert-danger mb-3" role="alert">
                    <div className="d-flex justify-content-between align-items-start">
                      <strong><i className="ri-error-warning-line me-1"></i>Issues detected during search</strong>
                      <button
                        type="button"
                        className="btn-close"
                        aria-label="Dismiss"
                        onClick={() => setErrorMessages([])}
                      />
                    </div>
                    <ul className="mb-0 mt-2 ps-3">
                      {errorMessages.map((msg, i) => (
                        <li key={i} style={{ fontSize: '0.875rem' }}>{msg}</li>
                      ))}
                    </ul>
                    {errorMessages.some(m =>
                      m.toLowerCase().includes('quota') ||
                      m.toLowerCase().includes('billing') ||
                      m.toLowerCase().includes('exceeded')
                    ) && (
                      <div className="mt-2 small">
                        <strong>Tip:</strong> This looks like an API credit limit. Check your OpenAI or Tavily account dashboard and top up before retrying.
                      </div>
                    )}
                  </div>
                )}

                {/* Live progress thought */}
                {currentThought && isGenerating && (
                  <div className="alert alert-info py-2 mb-3" role="alert" style={{ fontSize: '0.85rem' }}>
                    <i className="ri-loader-4-line align-middle me-1"></i>{currentThought}
                  </div>
                )}

                {isLoading && <Loading isLoading={isLoading} />}

                {!isLoading && ['failed', 'error'].includes((report?.metadata?.status || '').toLowerCase()) && (
                  <div className="alert alert-danger" role="alert">
                    {String(report?.metadata?.error || '').toLowerCase().includes('insufficient_quota') ||
                    String(report?.metadata?.error || '').toLowerCase().includes('quota') ? (
                      <>
                        <strong>OpenAI credit limit reached — the search did not start.</strong>{' '}
                        Add OpenAI API credit or update the OpenAI billing limit, then press Refresh. No Tavily searches were used for this failed run.
                      </>
                    ) : (
                      <>
                        <strong>Search could not be completed.</strong>{' '}
                        {report?.metadata?.error || 'Please retry once the search service is available.'}
                      </>
                    )}
                  </div>
                )}

                {(!isLoading && (!useCases || useCases.length === 0) && !currentThought && !isGenerating) && (
                  <div className="alert alert-info" role="alert">
                    {report?.metadata?.completeness?.stopped_reason === 'no_ref_ready_evidence' ? (
                      <>
                        <strong>No REF-ready evidence was admitted.</strong> The search completed, but none of
                        the sources proved a trusted, attributable real-world outcome with both reach and
                        significance. Add the professor&apos;s research area, named project, partner, technology,
                        or beneficiary and search again.
                      </>
                    ) : (
                      <>No use cases found. {themeId && "Start a new search to get started."}</>
                    )}
                  </div>
                )}
                
                {useCases && useCases.length > 0 && (
                  <>
                    {/* {searchQuery && (
                      <div className="alert alert-info mb-3">
                        Showing results for: <strong>{decodeURIComponent(searchQuery.replace(/&/g, ', ').replace(/=/g, ': '))}</strong>
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
                    )} */}

                    <div className="table-responsive">
                      <table className="table table-bordered">
                        <thead className="table-light">
                          <tr>
                            <th>Research Finding / Impact Claim</th>
                            <th>Organisation / Beneficiary</th>
                            <th>Impact Type</th>
                            <th>Sector</th>
                            <th>Quantitative Outcome</th>
                            <th>Published / Impact Date</th>
                            <th>Source URL</th>
                            <th>Source Type</th>
                            <th>Direct Quote / Exact Citation Location</th>
                            <th>Credibility Score</th>
                            <th>Relevance Score</th>
                            <th></th>
                          </tr>
                        </thead>
                        <tbody>
                          {useCases.map((useCase) => (
                            <tr key={useCase.id}>
                              <td className="col-md-2">
                                {useCase.use_case_name ? (
                                  <a
                                    href="#"
                                    className="text-decoration-none"
                                    onClick={(e) => {
                                      e.preventDefault();
                                      handleUseCaseClick(useCase);
                                    }}
                                  >
                                    <TruncatedDescriptionWidget description={useCase.use_case_name} maxLength={90} />
                                  </a>
                                ) : 'N/A'}
                              </td>
                              <td className="col-md-1">{useCase.company || 'N/A'}</td>
                              <td className="col-md-1">{useCase.use_case_type || 'N/A'}</td>
                              <td className="col-md-1">{useCase.industry || 'N/A'}</td>
                              <td className="col-md-2">
                                {useCase.performance_impact ? (
                                  <TruncatedDescriptionWidget description={useCase.performance_impact} maxLength={80} />
                                ) : 'N/A'}
                              </td>
                              <td className="col-md-1">
                                <div>
                                  <span className="text-muted" style={{ fontSize: '11px' }}>Published: </span>
                                  {useCase.published_date ? formatDate(useCase.published_date) : (
                                    <span className="text-muted" style={{ fontSize: '11px' }}>not stated</span>
                                  )}
                                </div>
                                <div>
                                  <span className="text-muted" style={{ fontSize: '11px' }}>Impact: </span>
                                  {formatDate(useCase.use_case_date) || 'N/A'}
                                </div>
                                {useCase.ref_period_status === "outside_period" && (
                                  <div className="text-warning" style={{ fontSize: '11px' }}>&#9888; outside REF period</div>
                                )}
                              </td>
                              <td className="col-md-2">
                                {useCase.source ? (
                                  <UrlSourceWidget showScore={false} source={useCase.source} urlValidationScore={useCase.url_validation_score} />
                                ) : 'N/A'}
                              </td>
                              <td className="text-center">
                                {useCase.content_type ? (
                                  <span className={`badge bg-${CONTENT_TYPE_LABELS[useCase.content_type]?.variant || 'secondary'}`}>
                                    {CONTENT_TYPE_LABELS[useCase.content_type]?.label || useCase.content_type}
                                  </span>
                                ) : (
                                  <span className="text-muted" style={{ fontSize: '11px' }}>Not classified</span>
                                )}
                              </td>
                              <td className="col-md-2">
                                {useCase.direct_quote ? (
                                  <>
                                    <div className="fst-italic" style={{ fontSize: '12px' }}>
                                      &ldquo;<TruncatedDescriptionWidget description={useCase.direct_quote} maxLength={90} />&rdquo;
                                    </div>
                                    <div className="text-muted" style={{ fontSize: '11px' }}>
                                      {useCase.source_reference || 'Location not stated'}
                                    </div>
                                  </>
                                ) : (
                                  <span className="text-muted" style={{ fontSize: '11px' }}>
                                    No verbatim quote extracted
                                    {useCase.source_reference && useCase.source_reference !== useCase.source && (
                                      <div>Ref: {useCase.source_reference}</div>
                                    )}
                                  </span>
                                )}
                              </td>
                              <td className="text-center">
                                {useCase.credibility_score !== null ? useCase.credibility_score : 'N/A'}
                              </td>
                              <td className="text-center">
                                <RelevanceScoreWidget score={useCase.relevance_score} />
                              </td>
                              <td className="text-center">
                                <button
                                  className="btn btn-sm btn-outline-danger p-1"
                                  title="Remove this result"
                                  onClick={() => handleDeleteUseCase(useCase.id)}
                                >
                                  <i className="ri-delete-bin-line"></i>
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>



                    <div className="d-flex justify-content-between align-items-center mt-3">
                      <Pagination
                        currentPage={page}
                        totalItems={totalCount}
                        pageSize={pageSize}
                        onPageChange={handlePageChange}
                      />
                      {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, totalCount)} of {totalCount}
                    </div>
                    
                    
                  </>
                )}

              </div>
            </div>
          </div>
        </div>
      </div>

      {themeId && (activeReportId || report?.id) && (
        <PusherListener
          streamKey={`use_cases_${activeReportId || report.id}`}
          onThoughtReceived={handleThoughtReceived}
          onUseCaseReceived={handleUseCaseReceived}
          onProgress={handleProgress}
          onComplete={handleComplete}
        />
      )}

      <UseCaseDetails
        useCase={selectedUseCase}
        show={showDetails}
        onHide={() => setShowDetails(false)}
      />
    </MainLayout>
  );
};

export default UseCasesPage; 
