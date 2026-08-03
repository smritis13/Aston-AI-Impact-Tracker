import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Container, Row, Col, Card, CardBody, Spinner, Alert, ProgressBar } from "react-bootstrap";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import MainLayout from "core/components/layout/MainLayout";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import PusherListener from "features/feature_chat/components/PusherListener";
import ImpactCaseStudyForm from "../components/ImpactCaseStudyForm";
import { ContentHttpService } from "../services";
import { useToast } from "../hooks/useToast";
import { DEFAULT_IMPACT_SECTIONS } from "../constants/impactCaseStudyConstants";
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf';
import "./ImpactCaseStudyPage.css";

const getPdfWorkerSrc = () => {
  if (typeof window === 'undefined') return '';
  const publicUrl = process.env.PUBLIC_URL || '';
  return `${publicUrl}/pdf.worker.min.js`;
};

// Configure PDF.js worker
if (typeof window !== 'undefined' && pdfjsLib?.GlobalWorkerOptions) {
  pdfjsLib.GlobalWorkerOptions.workerSrc = getPdfWorkerSrc();
}

export interface ImpactSection {
  id: string;
  title: string;
  description: string;
  maxWords: number;
}

export interface ImpactCaseStudyFormData {
  prompt: string;
  theme_id: number | null;
  sections: ImpactSection[];
  includeSummary: boolean;
  uploadedFiles: File[];
  numberOfOutcomes: string;
  searchComplexity: string;
  relevanceThreshold: string;
  sourceMode: "search" | "existing";
  skipReportGeneration: boolean;
}

interface GeneratedImpactReport {
  generated_report?: string;
  metadata?: {
    status?: string;
    error?: string | null;
    progress?: {
      percent?: number;
    };
    completeness?: {
      requested: number;
      found: number;
      stopped_reason: string;
    };
    report_generation_skipped?: boolean;
    theme_id?: number;
    token_usage?: TokenUsage;
    search_api_usage?: SearchApiUsage;
    content_provenance?: ContentProvenance;
  };
}

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  calls: number;
}

interface SearchApiUsage {
  provider: string;
  calls_total: number;
  calls_failed: number;
}

interface ContentProvenance {
  total_evidence_items: number;
  items_with_verbatim_quote: number;
  items_with_quantitative_metric: number;
  items_with_specific_citation_location: number;
  note: string;
}

interface ReportCompleteness {
  requested: number;
  found: number;
  stopped_reason: string;
}

// Fiona/Brenda/Kate's review feedback: the REF Readiness Assessment table's
// "Current strength" column implies a level of judgement that doesn't hold
// across Units of Assessment. Hidden rather than removed from the generation
// prompt (ref_prompts.py) - flip back to true to restore it, no data loss.
const SHOW_REF_STRENGTH_COLUMN = false;

/**
 * Removes any column whose header cell text matches one of headerNames
 * (case-insensitive) from a raw Markdown pipe-table (the "REF Readiness
 * Assessment" table is plain Markdown, not embedded HTML).
 */
const stripMarkdownTableColumn = (content: string, headerNames: string[]): string => {
  const targets = new Set(headerNames.map((h) => h.toLowerCase()));
  const isTableRow = (line: string) => /^\s*\|.*\|\s*$/.test(line);
  const isSeparatorRow = (line: string) => /^\s*\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$/.test(line);
  const splitCells = (line: string) =>
    line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
  const joinCells = (cells: string[]) => `| ${cells.join(" | ")} |`;

  const lines = content.split("\n");
  const result: string[] = [];
  let dropIndex: number | null = null;
  let inTable = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const next = lines[i + 1];
    if (!inTable && isTableRow(line) && next !== undefined && isSeparatorRow(next)) {
      inTable = true;
      const headerCells = splitCells(line);
      dropIndex = headerCells.findIndex((c) => targets.has(c.toLowerCase()));
      if (dropIndex === -1) {
        result.push(line);
      } else {
        const cells = [...headerCells];
        cells.splice(dropIndex, 1);
        result.push(joinCells(cells));
      }
      continue;
    }
    if (inTable && (isTableRow(line) || isSeparatorRow(line))) {
      if (dropIndex === null || dropIndex === -1) {
        result.push(line);
      } else {
        const cells = splitCells(line);
        if (dropIndex < cells.length) cells.splice(dropIndex, 1);
        result.push(joinCells(cells));
      }
      continue;
    }
    inTable = false;
    dropIndex = null;
    result.push(line);
  }
  return result.join("\n");
};

// Maps the backend's machine-readable stopped_reason codes (see
// _record_completeness in structured_report_generator.py) to a short,
// reviewer-facing explanation.
const COMPLETENESS_REASON_LABELS: Record<string, string> = {
  no_new_qualifying_evidence_after_two_rounds:
    "no further qualifying evidence was found after two extra search rounds",
  replanning_round_cap_reached: "the maximum number of extra search rounds was reached",
  search_api_unavailable: "the web search provider became unavailable partway through the run",
  replanning_response_unparseable: "a search-planning step returned an unusable response",
  replanning_produced_no_new_tasks: "no further new search angles could be generated",
  search_call_budget_reached: "this run's search API budget was reached, to avoid excess API usage",
};

const splitReportAndCommentary = (content: string) => {
  const commentaryMarker = "# REF Readiness Commentary";
  if (!content) return { main: "", commentary: "" };

  if (content.includes(commentaryMarker)) {
    const [main, rest] = content.split(commentaryMarker, 2);
    return {
      main: main.replace(/[\r\n]+-{3,}\s*$/, "").trim(),
      commentary: rest.trim(),
    };
  }

  const readinessHeading = "## 6. REF Readiness Assessment";
  if (content.includes(readinessHeading)) {
    const [main, rest] = content.split(readinessHeading, 2);
    return {
      main: main.trim(),
      commentary: `${readinessHeading}${rest}`.trim(),
    };
  }

  return { main: content, commentary: "" };
};

const ImpactCaseStudyPage: React.FC = () => {
  const { showToast } = useToast();
  const [formData, setFormData] = useState<ImpactCaseStudyFormData>({
    prompt: "",
    theme_id: null,
    sections: DEFAULT_IMPACT_SECTIONS.map(s => ({ ...s })), // Create a copy to avoid mutations
    includeSummary: true,
    uploadedFiles: [],
    numberOfOutcomes: "10",
    searchComplexity: "medium",
    relevanceThreshold: "",
    sourceMode: "search",
    skipReportGeneration: true,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [reportId, setReportId] = useState<number | null>(null);
  const [generatedReport, setGeneratedReport] = useState<string>("");
  // The backend splits the LLM-synthesized narrative from the "REF Readiness
  // Assessment" reviewer commentary/caveats (see _split_draft_and_commentary)
  // so they can be shown separately, same as the saved report detail view.
  const [commentarySection, setCommentarySection] = useState<string>("");
  const [completeness, setCompleteness] = useState<ReportCompleteness | undefined>(undefined);
  const [reportGenerationSkipped, setReportGenerationSkipped] = useState(false);
  const [foundThemeId, setFoundThemeId] = useState<number | null>(null);
  const [tokenUsage, setTokenUsage] = useState<TokenUsage | undefined>(undefined);
  const [searchApiUsage, setSearchApiUsage] = useState<SearchApiUsage | undefined>(undefined);
  const [contentProvenance, setContentProvenance] = useState<ContentProvenance | undefined>(undefined);
  const [pusherKey, setPusherKey] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    setIsGenerating(true);
    setProgress(5);
    setReportId(null);
    setGeneratedReport("");
    setCommentarySection("");
    setReportGenerationSkipped(false);
    setFoundThemeId(null);
    setTokenUsage(undefined);
    setSearchApiUsage(undefined);
    setContentProvenance(undefined);

    try {
      if (formData.sourceMode === "existing") {
        if (!formData.theme_id) {
          showToast({ message: "Please select a theme to compile from its existing use cases", type: "error" });
          setIsLoading(false);
          setIsGenerating(false);
          return;
        }

        const response = await ContentHttpService.compileImpactCaseStudyFromUseCases({
          theme_id: formData.theme_id,
          prompt: formData.prompt,
          impact_sections: formData.sections,
          include_summary: formData.includeSummary,
        });

        if (response && response.report_id) {
          setReportId(response.report_id);
          setPusherKey(response.report_id ? `use_cases_${response.report_id}` : null);
          showToast({ message: "Compiling report from existing use cases!", type: "success" });
        } else {
          throw new Error("Report compilation did not return a report ID");
        }
        return;
      }

      if (!formData.prompt.trim() && !formData.theme_id && formData.uploadedFiles.length === 0) {
        showToast({ message: "Please enter a prompt, choose a theme, or upload a DOCX file", type: "error" });
        setIsLoading(false);
        setIsGenerating(false);
        return;
      }

      // Prepare request data
      const response = await ContentHttpService.generateImpactCaseStudyReport({
        query: formData.prompt,
        theme_id: formData.theme_id,
        report_type: "impact_case_study",
        impact_sections: formData.sections,
        include_summary: formData.includeSummary,
        number_of_outcomes: formData.numberOfOutcomes,
        search_complexity: formData.searchComplexity,
        uploaded_files: formData.uploadedFiles,
        skip_report_generation: formData.skipReportGeneration,
        relevance_threshold: formData.relevanceThreshold,
      });

      if (response && response.report_id) {
        setReportId(response.report_id);
        setPusherKey(response.report_id ? `use_cases_${response.report_id}` : null);
        showToast({
          message: "Search started - finding evidence only. Compile the report from the saved use cases when ready.",
          type: "success",
        });
      } else {
        throw new Error("Report generation did not return a report ID");
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.error || err?.message || "Failed to generate report";
      setError(errorMessage);
      setIsGenerating(false);
      setProgress(0);
      showToast({ message: errorMessage, type: "error" });
      console.error("Report generation error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormDataChange = (updatedData: ImpactCaseStudyFormData) => {
    setFormData(updatedData);
  };

  const handleReportGenerated = async () => {
    if (!reportId) return;
    const report = await ContentHttpService.loadReport(reportId) as GeneratedImpactReport | null;
    const skipped = !!report?.metadata?.report_generation_skipped;
    const sections = splitReportAndCommentary(report?.generated_report || "");
    setGeneratedReport(sections.main);
    setCommentarySection(sections.commentary);
    setCompleteness(report?.metadata?.completeness);
    setReportGenerationSkipped(skipped);
    setFoundThemeId(report?.metadata?.theme_id ?? null);
    setTokenUsage(report?.metadata?.token_usage);
    setSearchApiUsage(report?.metadata?.search_api_usage);
    setContentProvenance(report?.metadata?.content_provenance);
    setIsGenerating(false);
    setProgress(100);
    showToast({
      message: skipped ? "Evidence search complete - no report was generated." : "Report generated successfully!",
      type: "success",
    });
  };

  useEffect(() => {
    if (!isGenerating || !reportId) return;

    const pollReport = async () => {
      try {
        const report = await ContentHttpService.loadReport(reportId) as GeneratedImpactReport | null;
        const status = report?.metadata?.status?.toLowerCase();
        const percent = report?.metadata?.progress?.percent;

        if (typeof percent === "number") {
          setProgress(Math.max(5, Math.min(100, Math.round(percent))));
        }

        if (status === "completed") {
          const skipped = !!report?.metadata?.report_generation_skipped;
          const sections = splitReportAndCommentary(report?.generated_report || "");
          setGeneratedReport(sections.main);
          setCommentarySection(sections.commentary);
          setCompleteness(report?.metadata?.completeness);
          setReportGenerationSkipped(skipped);
          setFoundThemeId(report?.metadata?.theme_id ?? null);
          setTokenUsage(report?.metadata?.token_usage);
          setSearchApiUsage(report?.metadata?.search_api_usage);
          setContentProvenance(report?.metadata?.content_provenance);
          setIsGenerating(false);
          setProgress(100);
          showToast({
            message: skipped ? "Evidence search complete - no report was generated." : "Report generated successfully!",
            type: "success",
          });
        } else if (status === "failed" || status === "error") {
          const message = report?.metadata?.error || "Report generation failed";
          setError(message);
          setIsGenerating(false);
          setProgress(0);
          showToast({ message, type: "error" });
        }
      } catch (err: any) {
        const message = err?.message || "Unable to check report generation status";
        setError(message);
        setIsGenerating(false);
        setProgress(0);
      }
    };

    const intervalId = window.setInterval(pollReport, 5000);
    pollReport();

    return () => window.clearInterval(intervalId);
  }, [isGenerating, reportId, showToast]);

  return (
    <MainLayout>
      <div 
        className="impact-case-study-container"
      >
        <Container fluid style={{ minHeight: '100%' }}>
          <Row className="mb-4">
            <Col>
              <BreadcrumbWidget 
                mainTitle="Impact Case Study" 
                breadcrumbs={[{ title: "Home", url: "/" }]} 
              />
            </Col>
          </Row>

          <Row className="mb-4">
            <Col>
              <h1 className="page-title">Impact Case Study Report Generator</h1>
              <p className="page-subtitle">
                Create structured impact case study reports with customizable sections
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

          <Row className="main-content">
            <Col lg={7} className="form-column">
              <Card className="form-card">
                <CardBody>
                  <ImpactCaseStudyForm
                    formData={formData}
                    onFormDataChange={handleFormDataChange}
                    onSubmit={handleSubmit}
                    isLoading={isLoading}
                    isGenerating={isGenerating}
                    progress={progress}
                  />
                </CardBody>
              </Card>
            </Col>

            <Col lg={5} className="preview-column">
              <Card className="preview-card">
                <CardBody>
                  <div className="preview-header">
                    <h5>Preview</h5>
                  </div>
                  <div className="preview-content">
                    {isGenerating ? (
                      <div className="generating-preview">
                        <div className="generating-preview__status">
                          <Spinner animation="border" role="status" />
                          <div>
                            <h6>{formData.sourceMode === "existing" ? "Compiling impact case study report" : "Finding impact evidence"}</h6>
                            <p>
                              {formData.sourceMode === "existing"
                                ? "Compiling the report from the selected theme's existing use cases and your chosen sections."
                                : "Searching, validating, and saving use cases for this theme. The report is generated later from existing use cases."}
                            </p>
                          </div>
                        </div>
                        <ProgressBar now={progress} label={`${progress}%`} className="mb-3" />
                        <div className="generating-preview__sections">
                          {formData.sections.map((section) => (
                            <div key={section.id} className="generating-preview__section">
                              <span>{section.title || "Untitled section"}</span>
                              <small>Queued</small>
                            </div>
                          ))}
                          {formData.includeSummary && (
                            <div className="generating-preview__section">
                              <span>Summary</span>
                              <small>Queued</small>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : generatedReport ? (
                      <div className="generated-report">
                        {completeness && completeness.found < completeness.requested && (
                          <Alert variant="warning">
                            <strong>
                              Found {completeness.found} of {completeness.requested} requested findings.
                            </strong>{" "}
                            Stopped because{" "}
                            {COMPLETENESS_REASON_LABELS[completeness.stopped_reason] || completeness.stopped_reason}.
                          </Alert>
                        )}
                        {tokenUsage && (
                          <div className="text-muted mb-1" style={{ fontSize: "12px" }}>
                            <i className="ri-flashlight-line me-1"></i>
                            OpenAI: {tokenUsage.calls} call{tokenUsage.calls === 1 ? "" : "s"} ·{" "}
                            {tokenUsage.total_tokens.toLocaleString()} tokens (
                            {tokenUsage.prompt_tokens.toLocaleString()} prompt /{" "}
                            {tokenUsage.completion_tokens.toLocaleString()} completion)
                          </div>
                        )}
                        {searchApiUsage && (
                          <div className="text-muted mb-2" style={{ fontSize: "12px" }}>
                            <i className="ri-search-line me-1"></i>
                            Tavily: {searchApiUsage.calls_total} search call{searchApiUsage.calls_total === 1 ? "" : "s"}
                            {searchApiUsage.calls_failed > 0 && <> ({searchApiUsage.calls_failed} failed)</>}
                          </div>
                        )}
                        {contentProvenance && (
                          <div className="card mb-3">
                            <div className="card-body py-2">
                              <h6 className="card-subtitle mb-2 text-muted" style={{ fontSize: "13px" }}>
                                <i className="ri-quill-pen-line me-1"></i>
                                Content provenance: AI-written vs. directly pulled
                              </h6>
                              <p className="mb-2" style={{ fontSize: "12px" }}>{contentProvenance.note}</p>
                              <div className="row g-2" style={{ fontSize: "12px" }}>
                                <div className="col-6 col-md-3">
                                  <div className="text-muted">Evidence items</div>
                                  <div className="fw-semibold">{contentProvenance.total_evidence_items}</div>
                                </div>
                                <div className="col-6 col-md-3">
                                  <div className="text-muted">With verbatim quote</div>
                                  <div className="fw-semibold">{contentProvenance.items_with_verbatim_quote}</div>
                                </div>
                                <div className="col-6 col-md-3">
                                  <div className="text-muted">With quantitative metric</div>
                                  <div className="fw-semibold">{contentProvenance.items_with_quantitative_metric}</div>
                                </div>
                                <div className="col-6 col-md-3">
                                  <div className="text-muted">With citation location</div>
                                  <div className="fw-semibold">{contentProvenance.items_with_specific_citation_location}</div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                          {generatedReport}
                        </ReactMarkdown>
                        {commentarySection && (
                          <div
                            className="mt-4 p-3"
                            style={{
                              border: "1px solid #f0b429",
                              borderLeft: "4px solid #f0b429",
                              borderRadius: "4px",
                              backgroundColor: "rgba(240, 180, 41, 0.08)",
                            }}
                          >
                            <h6 className="mb-2">
                              <i className="ri-flag-2-line me-2"></i>
                              REF Readiness Commentary
                            </h6>
                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                              {SHOW_REF_STRENGTH_COLUMN
                                ? commentarySection
                                : stripMarkdownTableColumn(commentarySection, ["current strength"])}
                            </ReactMarkdown>
                          </div>
                        )}
                      </div>
                    ) : reportGenerationSkipped ? (
                      <div>
                        {completeness && (
                          <p className="text-muted mb-2">
                            Found {completeness.found} of {completeness.requested} requested findings.
                          </p>
                        )}
                        {tokenUsage && (
                          <div className="text-muted mb-1" style={{ fontSize: "12px" }}>
                            <i className="ri-flashlight-line me-1"></i>
                            OpenAI: {tokenUsage.calls} call{tokenUsage.calls === 1 ? "" : "s"} ·{" "}
                            {tokenUsage.total_tokens.toLocaleString()} tokens (
                            {tokenUsage.prompt_tokens.toLocaleString()} prompt /{" "}
                            {tokenUsage.completion_tokens.toLocaleString()} completion)
                          </div>
                        )}
                        {searchApiUsage && (
                          <div className="text-muted mb-2" style={{ fontSize: "12px" }}>
                            <i className="ri-search-line me-1"></i>
                            Tavily: {searchApiUsage.calls_total} search call{searchApiUsage.calls_total === 1 ? "" : "s"}
                            {searchApiUsage.calls_failed > 0 && <> ({searchApiUsage.calls_failed} failed)</>}
                          </div>
                        )}
                        <p className="text-muted">
                          Evidence search complete - report generation was skipped. Use "Compile from existing use
                          cases" for this theme whenever you're ready to generate the report.
                        </p>
                        {foundThemeId && (
                          <Link to={`/usecases/${foundThemeId}`} className="btn btn-outline-primary btn-sm">
                            <i className="ri-file-list-3-line me-1"></i> Review found use cases
                          </Link>
                        )}
                      </div>
                    ) : error ? (
                      <p className="text-muted">Report generation stopped before a preview was created.</p>
                    ) : reportId ? (
                      <p className="text-muted">Report request finished, but no preview content was returned. ID: {reportId}</p>
                    ) : (
                      <p className="text-muted">No preview yet.</p>
                    )}
                  </div>
                </CardBody>
              </Card>
            </Col>
          </Row>
        </Container>

        {pusherKey && reportId && (
          <PusherListener
            streamKey={pusherKey}
            onThoughtReceived={() => {}}
            onProgress={setProgress}
            onComplete={(status) => {
              if (status === 'success') {
                handleReportGenerated();
              } else {
                if (status === 'error') {
                  setError("Report generation failed");
                  showToast({ message: "Report generation failed", type: "error" });
                }
                setIsGenerating(false);
              }
            }}
          />
        )}
      </div>
    </MainLayout>
  );
};

export default ImpactCaseStudyPage;
