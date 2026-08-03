import React, { useRef } from "react";
import { useParams } from "react-router-dom";
import { Dropdown } from "react-bootstrap";
import MainLayout from "core/components/layout/MainLayout";
import Loading from "core/components/Loading";
import ErrorMessage from "core/components/Error";
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import BreadcrumbWidget from "core/components/shared/BreadcrumbWidget";
import useReport from "../hooks/useReport";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { JsonTable, isJsonArray,cleanJsonString, JsonStructure } from "../components/JsonTable";
import ReportUseCases from "../components/ReportUseCases";
import rehypeRaw from 'rehype-raw'
import "./ReportDetailsPage.css";

/**
 * Removes any table column whose header cell text matches one of headerNames
 * (case-insensitive) from raw HTML/markdown-with-embedded-HTML content, before
 * it reaches ReactMarkdown/rehype-raw. Older stored reports have a "Where to
 * check" column baked in that duplicates the Link column.
 */
const stripTableColumns = (content: string, headerNames: string[]): string => {
  const targets = new Set(headerNames.map((h) => h.toLowerCase()));
  const cellRe = /<(th|td)\b[^>]*>([\s\S]*?)<\/\1>/g;
  const rowRe = /<tr\b[^>]*>[\s\S]*?<\/tr>/g;

  return content.replace(/<table\b[^>]*>[\s\S]*?<\/table>/g, (tableHtml) => {
    let dropIndices: number[] = [];
    let foundHeader = false;

    return tableHtml.replace(rowRe, (rowHtml) => {
      const cells = Array.from(rowHtml.matchAll(cellRe)).map((m) => ({
        index: m.index ?? 0,
        length: m[0].length,
        text: m[2].replace(/<[^>]+>/g, "").trim().toLowerCase(),
      }));
      if (cells.length === 0) return rowHtml;
      if (!foundHeader) {
        foundHeader = true;
        dropIndices = cells.reduce<number[]>((acc, c, i) => {
          if (targets.has(c.text)) acc.push(i);
          return acc;
        }, []);
      }
      if (dropIndices.length === 0) return rowHtml;
      let newRow = rowHtml;
      [...dropIndices].sort((a, b) => b - a).forEach((idx) => {
        if (idx < cells.length) {
          const cell = cells[idx];
          newRow = newRow.slice(0, cell.index) + newRow.slice(cell.index + cell.length);
        }
      });
      return newRow;
    });
  });
};

// Fiona/Brenda/Kate's review feedback: the REF Readiness Assessment table's
// "Current strength" column implies a level of judgement that doesn't hold
// across Units of Assessment. Hidden rather than removed from the generation
// prompt (ref_prompts.py) - flip back to true to restore it, no data loss.
const SHOW_REF_STRENGTH_COLUMN = false;

/**
 * Removes any column whose header cell text matches one of headerNames
 * (case-insensitive) from a raw Markdown pipe-table (the "REF Readiness
 * Assessment" table is plain Markdown, not embedded HTML, so stripTableColumns
 * above - which matches literal <th>/<td> tags - does not apply to it).
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

const ReportDetailsPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const numericReportId = reportId ? parseInt(reportId, 10) : undefined;
  const reportContentRef = useRef<HTMLDivElement | null>(null);

  const { data: report, isLoading, error } = useReport(numericReportId);


  if (isLoading) return <Loading isLoading={isLoading} />;
  if (error) return <ErrorMessage error={error + ""} />;
  if (!report) return <ErrorMessage error="Report not found" />;

  const reportSections = splitReportAndCommentary(report.generated_report || "");
  const commentarySection: string = reportSections.commentary;
  const mainContent: string = reportSections.main || report.generated_report;

  const completeness = report.metadata?.completeness;
  const isIncomplete = !!completeness && completeness.found < completeness.requested;

  const renderContent = () => {
    if (isJsonArray(report.generated_report)) {
      const jsonData = JSON.parse(cleanJsonString(report.generated_report));
      let structure: JsonStructure | undefined;

      // Check if prompt has json_structure
      if (report.prompt?.json_structure) {
        try {
          structure = JSON.parse(report.prompt.json_structure);
        } catch (e) {
          console.error('Failed to parse json_structure:', e);
        }
      }

      return <JsonTable data={jsonData} structure={structure} />;
    }
    return (
      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
        {stripTableColumns(mainContent, ["where to check"])}
      </ReactMarkdown>
    );
  };

  const getExportFileName = (extension: string) => {
    const baseName = (report.topic || report.query || `impact-case-study-${report.id}`)
      .toString()
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80) || `impact-case-study-${report.id}`;

    return `${baseName}.${extension}`;
  };

  const downloadFile = (content: BlobPart, type: string, extension: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = getExportFileName(extension);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const escapeHtml = (value: string) => {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  };

  const buildExportHtml = () => {
    const title = report.topic || report.query || "Impact Case Study Report";
    // reportContentRef's DOM was rendered from content already run through
    // stripTableColumns() in renderContent(), so it's already clean.
    const reportHtml = reportContentRef.current?.innerHTML || "";
    const generatedAt = report.created_at ? new Date(report.created_at).toLocaleString() : "";

    return `<!doctype html>
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(title)}</title>
  <!--[if gte mso 9]>
  <xml>
    <w:WordDocument>
      <w:View>Print</w:View>
      <w:Zoom>100</w:Zoom>
      <w:DoNotOptimizeForBrowser/>
    </w:WordDocument>
  </xml>
  <![endif]-->
  <style>
    @page Section1 {
      size: 21cm 29.7cm;
      margin: 2.5cm 2cm 2.5cm 2cm;
      mso-page-orientation: portrait;
    }
    div.Section1 { page: Section1; }
    body { color: #111827; font-family: Arial, Helvetica, sans-serif; font-size: 11pt; line-height: 1.45; margin: 0; }
    .export-title { color: #1e3a5f; font-size: 17pt; font-weight: 700; margin: 0 0 4px; border-bottom: 2pt solid #1e3a5f; padding-bottom: 6pt; }
    .export-meta { color: #6b7280; font-size: 9pt; margin: 0 0 18px; }
    h1 { color: #1e3a5f; font-size: 14.5pt; margin: 20px 0 8px; border-bottom: 1.5pt solid #1e3a5f; padding-bottom: 4pt; }
    h2 { color: #1e3a5f; font-size: 12pt; margin: 16px 0 6px; border-bottom: 0.5pt solid #9ca3af; padding-bottom: 3pt; }
    h3 { color: #374151; font-size: 10.5pt; margin: 12px 0 5px; }
    h4 { color: #374151; font-size: 10pt; font-style: italic; margin: 10px 0 4px; }
    p, li { font-size: 11pt; }
    table {
      table-layout: fixed;
      border-collapse: collapse;
      width: 100%;
      max-width: 100%;
      margin: 16px 0;
    }
    th, td {
      border: 1px solid #d1d5db;
      padding: 8px;
      text-align: left;
      vertical-align: top;
      word-wrap: break-word;
      overflow-wrap: break-word;
      word-break: break-word;
    }
    th { background: #1e3a5f; color: #ffffff; font-weight: 600; }
    tr:nth-child(even) td { background-color: #f8f9fa; }
    a { color: #1d4ed8; word-wrap: break-word; overflow-wrap: break-word; }
    img { max-width: 100%; }
  </style>
</head>
<body>
  <div class="Section1">
    <div class="export-title">${escapeHtml(title)}</div>
    ${generatedAt ? `<div class="export-meta">Generated: ${escapeHtml(generatedAt)}</div>` : ""}
    ${reportHtml}
  </div>
</body>
</html>`;
  };

  const handleExportMarkdown = () => {
    const title = report.topic || report.query || "Impact Case Study Report";
    const created = report.created_at ? `Generated: ${new Date(report.created_at).toLocaleString()}\n\n` : "";
    const body = SHOW_REF_STRENGTH_COLUMN
      ? report.generated_report || ""
      : stripMarkdownTableColumn(report.generated_report || "", ["current strength"]);
    downloadFile(`# ${title}\n\n${created}${body}`, "text/markdown;charset=utf-8", "md");
  };

  const handleExportHtml = () => {
    downloadFile(buildExportHtml(), "text/html;charset=utf-8", "html");
  };

  const handleExportWord = () => {
    downloadFile(buildExportHtml(), "application/msword;charset=utf-8", "doc");
  };

  const handleExportPdf = async () => {
    const apiUrl = process.env.REACT_APP_API_URL || "http://localhost:8000";
    const response = await fetch(`${apiUrl}/content/reports/${report.id}/export-pdf/`);

    if (!response.ok) {
      throw new Error("Unable to export PDF");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = getExportFileName("pdf");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <MainLayout>
      <div className="container">
        <BreadcrumbWidget
          mainTitle={report.topic}
          titleClassName="query-title"
          breadcrumbs={[
            { title: "Dashboard", url: "/" },
            { title: "Reports", url: "/reports" },
            { title: "Details" },
          ]}
        />

        <div className="row">
          <div className="col-xl-12">
            <div className="card custom-card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <div>
                  {/* <h2 className="fs-22 fw-semibold mb-3">{report.topic}</h2> */}
                  {/* <div className="text-muted">
                    Generated from query: {report.query}
                  </div> */}
                  <div className="text-muted">
                    <TimeAgoWidget date={report.created_at} />
                  </div>
                  {report.metadata?.token_usage && (
                    <div className="text-muted" style={{ fontSize: "12px" }} title="OpenAI LLM usage for this report's generation run">
                      <i className="ri-flashlight-line me-1"></i>
                      OpenAI: {report.metadata.token_usage.calls} call{report.metadata.token_usage.calls === 1 ? "" : "s"} ·{" "}
                      {report.metadata.token_usage.total_tokens.toLocaleString()} tokens (
                      {report.metadata.token_usage.prompt_tokens.toLocaleString()} prompt /{" "}
                      {report.metadata.token_usage.completion_tokens.toLocaleString()} completion)
                    </div>
                  )}
                  {report.metadata?.search_api_usage && (
                    <div className="text-muted" style={{ fontSize: "12px" }} title="Tavily web search calls for this report's generation run">
                      <i className="ri-search-line me-1"></i>
                      Tavily: {report.metadata.search_api_usage.calls_total} search call
                      {report.metadata.search_api_usage.calls_total === 1 ? "" : "s"}
                      {report.metadata.search_api_usage.calls_failed > 0 && (
                        <> ({report.metadata.search_api_usage.calls_failed} failed)</>
                      )}
                    </div>
                  )}
                </div>
                <Dropdown align="end">
                  <Dropdown.Toggle variant="outline-primary" size="sm" id="report-export-dropdown">
                    <i className="ri-download-2-line me-1"></i> Export
                  </Dropdown.Toggle>

                  <Dropdown.Menu>
                    <Dropdown.Item onClick={handleExportPdf}>
                      <i className="ri-file-pdf-line me-2"></i> PDF
                    </Dropdown.Item>
                    <Dropdown.Item onClick={handleExportWord}>
                      <i className="ri-file-word-2-line me-2"></i> Word
                    </Dropdown.Item>
                    <Dropdown.Item onClick={handleExportMarkdown}>
                      <i className="ri-markdown-line me-2"></i> Markdown
                    </Dropdown.Item>
                    <Dropdown.Item onClick={handleExportHtml}>
                      <i className="ri-code-s-slash-line me-2"></i> HTML
                    </Dropdown.Item>
                  </Dropdown.Menu>
                </Dropdown>
              </div>
              
              
              <div className="card-body">
                {isIncomplete && completeness && (
                  <div className="alert alert-warning d-flex align-items-start" role="alert">
                    <i className="ri-error-warning-line me-2 mt-1"></i>
                    <div>
                      <strong>
                        Found {completeness.found} of {completeness.requested} requested findings.
                      </strong>{" "}
                      Stopped because{" "}
                      {COMPLETENESS_REASON_LABELS[completeness.stopped_reason] || completeness.stopped_reason}.
                    </div>
                  </div>
                )}

                <div ref={reportContentRef}>
                  {report.generated_report && (
                    <div className="markdown-content">
                      {renderContent()}
                    </div>
                  )}

                  {commentarySection && (
                    <div
                      className="markdown-content mt-4 p-3"
                      style={{
                        border: "1px solid #f0b429",
                        borderLeft: "4px solid #f0b429",
                        borderRadius: "4px",
                        backgroundColor: "rgba(240, 180, 41, 0.08)",
                      }}
                    >
                      <h5 className="mb-2">
                        <i className="ri-flag-2-line me-2"></i>
                        REF Readiness Commentary
                      </h5>
                      <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                        {SHOW_REF_STRENGTH_COLUMN
                          ? commentarySection
                          : stripMarkdownTableColumn(commentarySection, ["current strength"])}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>

                {report.metadata?.content_provenance && (
                  <div className="card mb-4">
                    <div className="card-body">
                      <h6 className="card-subtitle mb-2 text-muted">
                        <i className="ri-quill-pen-line me-1"></i>
                        Content provenance: AI-written vs. directly pulled
                      </h6>
                      <p className="mb-2" style={{ fontSize: "13px" }}>{report.metadata.content_provenance.note}</p>
                      <div className="row g-2">
                        <div className="col-6 col-md-3">
                          <div className="text-muted" style={{ fontSize: "12px" }}>Evidence items</div>
                          <div className="fw-semibold">{report.metadata.content_provenance.total_evidence_items}</div>
                        </div>
                        <div className="col-6 col-md-3">
                          <div className="text-muted" style={{ fontSize: "12px" }}>With verbatim quote</div>
                          <div className="fw-semibold">{report.metadata.content_provenance.items_with_verbatim_quote}</div>
                        </div>
                        <div className="col-6 col-md-3">
                          <div className="text-muted" style={{ fontSize: "12px" }}>With quantitative metric</div>
                          <div className="fw-semibold">{report.metadata.content_provenance.items_with_quantitative_metric}</div>
                        </div>
                        <div className="col-6 col-md-3">
                          <div className="text-muted" style={{ fontSize: "12px" }}>With specific citation location</div>
                          <div className="fw-semibold">{report.metadata.content_provenance.items_with_specific_citation_location}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <ReportUseCases report={report} />



                {report.metadata?.research_summary && (
                  <div className="accordion mb-4" id="researchSummaryAccordion">
                    <div className="accordion-item">
                      <h2 className="accordion-header" id="headingResearchSummary">
                        <button className="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseResearchSummary" aria-expanded="false" aria-controls="collapseResearchSummary">
                          Research Summary
                        </button>
                      </h2>
                      <div id="collapseResearchSummary" className="accordion-collapse collapse" aria-labelledby="headingResearchSummary" data-bs-parent="#researchSummaryAccordion">
                        <div className="accordion-body">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>{report.metadata.research_summary}</ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default ReportDetailsPage;
