import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardBody, CardHeader, Spinner, Alert, Button } from "react-bootstrap";
import MainLayout from "core/components/layout/MainLayout";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import PromptManagerWidget from "../components/PromptManagerWidget";
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf';
import CustomModal from "core/components/shared/CustomModal";
import PusherListener from "features/feature_chat/components/PusherListener";
import UseCasesWidget from '../components/UseCasesWidget';
import HelpAccordion from '../components/HelpAccordion';
import { ReportGenerationHelpText } from '../constants/helpTexts';
import { ContentHttpService } from "../services";
import { useToast } from '../hooks/useToast';

const getPdfWorkerSrc = () => {
  if (typeof window === 'undefined') return '';
  const publicUrl = process.env.PUBLIC_URL || '';
  return `${publicUrl}/pdf.worker.min.js`;
};

// Configure PDF.js worker to use the public worker file for CRA and Docker builds
if (typeof window !== 'undefined' && pdfjsLib?.GlobalWorkerOptions) {
  pdfjsLib.GlobalWorkerOptions.workerSrc = getPdfWorkerSrc();
}

interface ReportFormData {
  query: string;
  report_length: string;
  prompt_id?: number;
  theme_id: number | null;
  theme_is_featured: boolean;
  number_of_outcomes: string;
  search_complexity: string;
  relevance_threshold: string;
}

const ReportGenerationPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [formData, setFormData] = useState<ReportFormData>({
    query: "",
    report_length: "detailed",
    prompt_id: undefined,
    theme_id: null,
    theme_is_featured: false,
    number_of_outcomes: "5",
    search_complexity: "medium",
    relevance_threshold: ""
  });
  const [selectedPrompt, setSelectedPrompt] = useState<{ id: number; title: string; content: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [reportId, setReportId] = useState<number | null>(null);
  const [useCases, setUseCases] = useState<any[]>([]);
  const [currentTheme, setCurrentTheme] = useState<{ id: number; title: string } | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [isProcessingPdf, setIsProcessingPdf] = useState(false);
  const [pdfFileName, setPdfFileName] = useState<string | null>(null);
  const [pdfExtractedText, setPdfExtractedText] = useState<string | null>(null);
  const pdfInputRef = useRef<HTMLInputElement | null>(null);
  const selectedPromptTextareaRef = useRef<HTMLTextAreaElement | null>(null);

  const fitPromptTextarea = (textarea: HTMLTextAreaElement | null) => {
    if (!textarea) return;
    const maxHeight = 520;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(Math.max(textarea.scrollHeight, 180), maxHeight)}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  };

  useEffect(() => {
    fitPromptTextarea(selectedPromptTextareaRef.current);
  }, [formData.query, selectedPrompt]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setIsGenerating(true);
    setError(null);
    setReportId(null);
    setCurrentTheme(null);

    try {
      const payload = {
        ...formData,
        prompt_id: selectedPrompt?.id,
        ...(pdfExtractedText ? { pdf_filename: pdfFileName ?? undefined, pdf_text: pdfExtractedText } : {}),
        report_type: "impact_case_study",
      };

      const response = await ContentHttpService.generateReport(payload);

      console.log('Response:', response);

      if (response.id) {
        setCurrentTheme({
          id: response.id,
          title: response.title
        });
        setReportId(response.report_id);
         // Stop the initial loading state
      }
      else {
        console.log('Error:', response.errorMessage);
        setError(response.errorMessage);

      }
      setIsLoading(false);
      setIsGenerating(false);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate report");
      setIsGenerating(false);
      setIsLoading(false);
    }
  };

  const _reset = () => {
    setIsGenerating(false);
    setCurrentTheme(null);
    setUseCases([]);
    setReportId(null);
    setPdfFileName(null);
  };

  const handleRemovePdfAttachment = () => {
    setPdfFileName(null);
    setPdfExtractedText(null);
    if (pdfInputRef.current) {
      pdfInputRef.current.value = '';
    }
  };

  const handleStopGeneration = async () => {
    if (!currentTheme?.id) return;
    
    try {
      await ContentHttpService.stopReportGeneration(currentTheme.id);
      _reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop report generation");
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePromptSelect = (prompt: { id: number; title: string; content: string }) => {
    setSelectedPrompt(prompt);
    setFormData(prev => ({ ...prev, query: prompt.content }));
    setPdfFileName(null);
    setPdfExtractedText(null);
  };

  const extractTextFromPdf = async (file: File): Promise<string> => {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    let text = "";

    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const textContent = await page.getTextContent();
      const pageText = textContent.items.map((item: any) => item.str).join(' ');
      text += pageText + '\n';
    }

    return text.trim();
  };

  const handlePdfFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || file.type !== 'application/pdf') return;

    setIsProcessingPdf(true);
    try {
      const extractedText = await extractTextFromPdf(file);
      setPdfFileName(file.name);
      setPdfExtractedText(extractedText);
      setError(null);
    } catch (err) {
      console.error('Error extracting PDF text:', err);
      setError(`Failed to read PDF: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsProcessingPdf(false);
      if (pdfInputRef.current) {
        pdfInputRef.current.value = '';
      }
    }
  };

  const handlePdfUploadClick = () => {
    pdfInputRef.current?.click();
  };

  const handleThoughtReceived = (_thought: string) => {
    // Keep the stream subscription compatible while intentionally hiding thoughts in the UI.
  };

  const handleUseCaseReceived = (useCase: any) => {
    console.log('Raw use case received:', useCase);
    
    // Ensure we have a valid use case object
    if (!useCase || typeof useCase !== 'object') {
      console.error('Invalid use case received:', useCase);
      return;
    }

    // If the use case is a string, try to parse it
    if (typeof useCase === 'string') {
      try {
        useCase = JSON.parse(useCase);
      } catch (e) {
        console.error('Failed to parse use case string:', e);
        return;
      }
    }

    console.log('Processed use case:', useCase);
    setUseCases(prev => [...prev, useCase]);
  };

  const handleProgress = (progress: number) => {
    console.log('Received progress:', progress);

    if(progress!=undefined) {
      setProgress(progress);
    }
    
  };

  const handleComplete = (status: 'success' | 'stopped' | 'error') => {
    setIsGenerating(false);
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
          message: 'An error occurred during the use case search.'
        });
        break;
    }
  };

  return (
    <MainLayout>
      <div className="container">
        
        <BreadcrumbWidget
          mainTitle="Search Use Case"
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Use Case Library", url: "/usecases" },
            { title: "Search Use Case" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <HelpAccordion helpText={ReportGenerationHelpText} />
          </div>

          <div className="col-xl-12 mt-4">
            <Card className="mb-4">
              
              <CardBody>
                <form onSubmit={handleSubmit}>
                  <div className="position-relative">
                    
                    <div className="mb-3 d-flex justify-content-between">
                      <div style={{width: "calc(100%)"}}>
                        {selectedPrompt ? (
                          <div className="selected-prompt">
                            <div className="d-flex justify-content-between align-items-center mb-2">
                              <h6 className="mb-0">{selectedPrompt.title}</h6>
                              <Button
                                variant="outline-secondary"
                                size="sm"
                                onClick={() => {
                                  setSelectedPrompt(null);
                                  setFormData(prev => ({ ...prev, query: "" }));
                                }}
                              >
                                <i className="bi bi-x"></i>
                              </Button>
                            </div>
                            <textarea
                              ref={selectedPromptTextareaRef}
                              className="form-control prompt-textarea-auto-expand"
                              rows={10}
                              value={formData.query}
                              onChange={(event) => {
                                setFormData(prev => ({ ...prev, query: event.target.value }));
                                fitPromptTextarea(event.target);
                              }}
                              onInput={(event) => fitPromptTextarea(event.target as HTMLTextAreaElement)}
                            />
                          </div>
                        ) : (
                          <PromptManagerWidget
                            value={formData.query}
                            onChange={(value) => setFormData(prev => ({ ...prev, query: value }))}
                            onPromptSelect={handlePromptSelect}
                            onSubmit={handleSubmit}
                          />
                        )}
                      </div>
                    </div>
                    {pdfFileName && (
                      <div className="alert alert-secondary d-flex justify-content-between align-items-center mt-3 mb-0">
                        <div>
                          <strong>PDF attached:</strong> {pdfFileName}
                        </div>
                        <Button type="button" variant="outline-danger" size="sm" onClick={handleRemovePdfAttachment}>
                          Remove
                        </Button>
                      </div>
                    )}
                  </div>
                  <div className="d-flex justify-content-end gap-2 mt-3">
                    <div className="d-flex gap-3">
                      <div className="form-group">
                        <label htmlFor="numberOfOutcomes" className="form-label me-2">
                          Number of Outcomes:
                        </label>
                        <select 
                          id="numberOfOutcomes"
                          className="form-select form-select-sm"
                          value={formData.number_of_outcomes}
                          onChange={(e) => setFormData(prev => ({ ...prev, number_of_outcomes: e.target.value }))}
                          style={{ width: '150px' }}
                        >
                          <option value="5">5</option>
                          <option value="10">10</option>
                          <option value="25">25</option>
                          <option value="50">50</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label htmlFor="searchComplexity" className="form-label me-2">
                          Search Complexity:
                        </label>
                        <select 
                          id="searchComplexity"
                          className="form-select form-select-sm"
                          value={formData.search_complexity}
                          onChange={(e) => setFormData(prev => ({ ...prev, search_complexity: e.target.value }))}
                          style={{ width: '150px' }}
                        >
                          <option value="low">Lowest cost (targeted REF evidence)</option>
                          <option value="simple">Simple</option>
                          <option value="medium">Medium</option>
                          <option value="complex">Complex</option>
                          <option value="advanced">Advanced</option>
                        </select>
                      </div>

                      <div className="form-group">
                        <label htmlFor="relevanceThreshold" className="form-label me-2">
                          Result filtering:
                        </label>
                        <select
                          id="relevanceThreshold"
                          className="form-select form-select-sm"
                          value={formData.relevance_threshold}
                          onChange={(e) => setFormData(prev => ({ ...prev, relevance_threshold: e.target.value }))}
                          style={{ width: '220px' }}
                          title="Credibility score is never filtered automatically - this only controls the relevance cutoff"
                        >
                          <option value="">Standard (recommended)</option>
                          <option value="0.3">Loose - show more, lower confidence</option>
                          <option value="0">Show everything - no relevance filter</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-check form-switch d-flex pt-2 gap-2">
                      <input
                        className="form-check-input"
                        type="checkbox"
                        id="themeIsFeaturedSwitch"
                        checked={formData.theme_is_featured || false}
                        onChange={(e) => setFormData(prev => ({ ...prev, theme_is_featured: e.target.checked }))}
                      />
                      <label className="form-check-label" htmlFor="themeIsFeaturedSwitch">
                        Save as Featured Theme
                      </label>
                    </div>

                    <input
                      ref={pdfInputRef}
                      type="file"
                      accept="application/pdf"
                      style={{ display: 'none' }}
                      onChange={handlePdfFileChange}
                    />

                    <Button
                      type="button"
                      variant="outline-secondary"
                      size="sm"
                      onClick={handlePdfUploadClick}
                      disabled={isProcessingPdf}
                    >
                      {isProcessingPdf ? (
                        <>
                          <i className="ri-loader-4-line spinning"></i> Extracting PDF...
                        </>
                      ) : (
                        <>
                          <i className="ri-file-pdf-line"></i> Upload PDF
                        </>
                      )}
                    </Button>

                    <button 
                      type="submit" 
                      className="btn btn-primary"
                      disabled={isLoading || (!formData.query && !pdfExtractedText)}
                    >
                      {isLoading ? (
                        <>
                          <Spinner
                            as="span"
                            animation="border"
                            size="sm"
                            role="status"
                            aria-hidden="true"
                            className="me-2"
                          />
                          Searching...
                        </>
                      ) : (
                        "Search Use Cases"
                      )}
                    </button>
                  </div>
                </form>
              </CardBody>
            </Card>

            

            {currentTheme && (
              <>
                <Card className="mb-4">
                  {progress!=undefined && (
                      <div className="mb-3">
                        <div className="progress" style={{ height: '8px' }}>
                          <div className="progress-bar progress-bar-striped progress-bar-animated bg-info" style={{ width: `${progress}%` }}></div>
                        </div>
                      </div>
                    )}
                  <CardHeader>
                    <div className="d-flex justify-content-between align-items-center">
                      <h5 className="card-title mb-0">Searching Use Cases for Theme: {currentTheme.title}</h5>
                      <div className="d-flex gap-2">
                        
                        {isGenerating && (
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={handleStopGeneration}
                          >
                            Stop Generation
                          </Button>
                        )}
                        <Button
                          variant="outline-primary"
                          size="sm"
                          onClick={() => {
                            const reportQuery = reportId ? `?report_id=${reportId}` : '';
                            navigate(`/usecases/${currentTheme.id}/${currentTheme.title.replace(/\s+/g, '-')}${reportQuery}`);
                          }}
                        >
                          View Theme Page
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardBody>
                    {isGenerating && (
                      <div className="alert alert-info">
                        <Spinner
                          as="span"
                          animation="border"
                          size="sm"
                          role="status"
                          aria-hidden="true"
                          className="me-2"
                        />
                        Searching for use cases... This may take a few minutes.
                      </div>
                    )}

                    {error && (
                      <div className="alert alert-danger mt-3" role="alert">
                        {error}
                      </div>
                    )}

                    <UseCasesWidget useCases={useCases} />

                    
                  </CardBody>
                </Card>

                <PusherListener
                  streamKey={`use_cases_${currentTheme.id}`}
                  onThoughtReceived={handleThoughtReceived}
                  onUseCaseReceived={handleUseCaseReceived}
                  onProgress={handleProgress}
                  onComplete={handleComplete}
                />
              </>
            )}

            

            {error && (
              <Alert variant="danger" className="mb-4">
                {error}
              </Alert>
            )}

          </div>
        </div>
      </div>

      <CustomModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        title="Options"
        showFooter={false}
      >
        <div className="mb-3">
          
        </div>
        <div className="d-flex justify-content-end gap-2">
          <Button variant="outline-secondary" onClick={() => setIsSettingsModalOpen(false)}>
            Close
          </Button>
        </div>
      </CustomModal>
    </MainLayout>
  );
};

export default ReportGenerationPage; 
