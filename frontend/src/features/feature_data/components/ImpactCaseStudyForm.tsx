import React, { useState, useRef, useEffect } from "react";
import { Button, Form, Card, Row, Col, Spinner, ProgressBar } from "react-bootstrap";
import { ImpactCaseStudyFormData, ImpactSection } from "../pages/ImpactCaseStudyPage";
import SelectTheme from "./SelectTheme";
import { REF_PROMPT_STARTERS, REF_REPORT_PROMPT_STARTERS } from "../constants/refPromptStarters";
import { ContentHttpService } from "../services";
import "./ImpactCaseStudyForm.css";

interface ImpactCaseStudyFormProps {
  formData: ImpactCaseStudyFormData;
  onFormDataChange: (data: ImpactCaseStudyFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  isGenerating: boolean;
  progress: number;
}

const ImpactCaseStudyForm: React.FC<ImpactCaseStudyFormProps> = ({
  formData,
  onFormDataChange,
  onSubmit,
  isLoading,
  isGenerating,
  progress,
}) => {
  const [uploadedFileName, setUploadedFileName] = useState<string>("");
  const [selectedStarterId, setSelectedStarterId] = useState("");
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [existingUseCaseCount, setExistingUseCaseCount] = useState<number | null>(null);
  const [isCheckingUseCaseCount, setIsCheckingUseCaseCount] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const promptTextareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (formData.sourceMode !== "existing" || !formData.theme_id) {
      setExistingUseCaseCount(null);
      return;
    }

    let cancelled = false;
    setIsCheckingUseCaseCount(true);
    ContentHttpService.loadUseCases(formData.theme_id, undefined, 1, 1)
      .then((data: any) => {
        if (!cancelled) {
          setExistingUseCaseCount(typeof data?.count === "number" ? data.count : 0);
        }
      })
      .catch(() => {
        if (!cancelled) setExistingUseCaseCount(null);
      })
      .finally(() => {
        if (!cancelled) setIsCheckingUseCaseCount(false);
      });

    return () => {
      cancelled = true;
    };
  }, [formData.sourceMode, formData.theme_id]);

  // Grow the prompt box while typing, then scroll only after a comfortable reading height.
  const fitPromptTextarea = (textarea: HTMLTextAreaElement | null) => {
    if (!textarea) return;
    const maxHeight = 520;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(Math.max(textarea.scrollHeight, 180), maxHeight)}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? "auto" : "hidden";
  };

  useEffect(() => {
    fitPromptTextarea(promptTextareaRef.current);
  }, [formData.prompt]);

  const toggleSectionExpanded = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const handlePromptChange = (value: string) => {
    onFormDataChange({
      ...formData,
      prompt: value,
    });
  };

  const handleThemeChange = (themeId: number | null) => {
    onFormDataChange({
      ...formData,
      theme_id: themeId,
    });
  };

  const handleSourceModeChange = (mode: "search" | "existing") => {
    onFormDataChange({
      ...formData,
      sourceMode: mode,
      skipReportGeneration: mode === "search" ? true : formData.skipReportGeneration,
    });
  };

  // Search mode feeds this prompt straight into the planning LLM as the seed
  // for what search queries to generate, so it needs REF_PROMPT_STARTERS
  // (rich searchSeeds/evidenceTargets aimed at finding new evidence).
  // Existing/compile mode only writes up evidence already gathered, so it
  // needs REF_REPORT_PROMPT_STARTERS (synthesis-focused reportPriorities)
  // instead - using the report starters in search mode was silently
  // starving the planner of the named-entity-anchored search angles that
  // make REF searches find the right sources in the first place.
  const activeStarters = formData.sourceMode === "existing" ? REF_REPORT_PROMPT_STARTERS : REF_PROMPT_STARTERS;

  const handleApplyStarter = () => {
    const starter = activeStarters.find((item) => item.id === selectedStarterId);
    if (starter) {
      handlePromptChange(starter.prompt);
    }
  };

  const handleSectionChange = (sectionId: string, field: keyof ImpactSection, value: any) => {
    const updatedSections = formData.sections.map((section) =>
      section.id === sectionId ? { ...section, [field]: value } : section
    );
    onFormDataChange({
      ...formData,
      sections: updatedSections,
    });
  };

  const handleAddSection = () => {
    const newId = Math.max(...formData.sections.map((s) => parseInt(s.id))) + 1;
    const newSection: ImpactSection = {
      id: newId.toString(),
      title: `Section ${newId}`,
      description: "",
      maxWords: 300,
    };
    onFormDataChange({
      ...formData,
      sections: [...formData.sections, newSection],
    });
  };

  const handleRemoveSection = (sectionId: string) => {
    const updatedSections = formData.sections.filter((section) => section.id !== sectionId);
    onFormDataChange({
      ...formData,
      sections: updatedSections,
    });
  };

  const handleIncludeSummaryChange = (value: boolean) => {
    onFormDataChange({
      ...formData,
      includeSummary: value,
    });
  };

  const handleNumberOfOutcomesChange = (value: string) => {
    onFormDataChange({
      ...formData,
      numberOfOutcomes: value,
    });
  };

  const handleSearchComplexityChange = (value: string) => {
    onFormDataChange({
      ...formData,
      searchComplexity: value,
    });
  };

  const handleRelevanceThresholdChange = (value: string) => {
    onFormDataChange({
      ...formData,
      relevanceThreshold: value,
    });
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const fileArray = Array.from(files);
      const supportedFiles = fileArray.filter(
        (file) =>
          file.type ===
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
          file.type === "application/pdf" ||
          file.name.toLowerCase().endsWith(".docx") ||
          file.name.toLowerCase().endsWith(".pdf")
      );

      if (supportedFiles.length !== fileArray.length) {
        alert("Please upload only PDF or DOCX files");
        return;
      }

      setUploadedFileName(supportedFiles.map((f) => f.name).join(", "));
      onFormDataChange({
        ...formData,
        uploadedFiles: supportedFiles,
      });
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const isExistingMode = formData.sourceMode === "existing";

  return (
    <Form onSubmit={onSubmit}>
      {/* Source Mode Section */}
      <div className="form-section mb-4">
        <label className="form-label">Evidence source</label>
        <div className="d-flex gap-3">
          <Form.Check
            type="radio"
            id="source-mode-search"
            name="sourceMode"
            label="Search the web for new evidence"
            checked={!isExistingMode}
            onChange={() => handleSourceModeChange("search")}
            disabled={isLoading || isGenerating}
          />
          <Form.Check
            type="radio"
            id="source-mode-existing"
            name="sourceMode"
            label="Use existing use cases for a theme"
            checked={isExistingMode}
            onChange={() => handleSourceModeChange("existing")}
            disabled={isLoading || isGenerating}
          />
        </div>
      </div>

      {/* Prompt Section */}
      <div className="form-section mb-4">
        <label className="form-label">
          Prompt {!isExistingMode && <span className="required">*</span>}
        </label>
        <Form.Control
          as="textarea"
          ref={promptTextareaRef}
          rows={isExistingMode ? 4 : 10}
          placeholder={
            isExistingMode
              ? "Optional: guide the tone/focus of the write-up (the evidence itself comes from the selected theme's existing use cases)"
              : "Enter your case study prompt"
          }
          value={formData.prompt}
          onChange={(e) => {
            handlePromptChange(e.target.value);
            fitPromptTextarea(promptTextareaRef.current);
          }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            fitPromptTextarea(target);
          }}
          disabled={isLoading || isGenerating}
          className="prompt-input prompt-textarea-auto-expand"
          style={{} as React.CSSProperties}
        />
        <div className="d-flex gap-2 mt-2">
          <Form.Select
            size="sm"
            value={selectedStarterId}
            onChange={(e) => setSelectedStarterId(e.target.value)}
            disabled={isLoading || isGenerating}
            aria-label="REF prompt starter"
          >
            <option value="">
              {isExistingMode ? "REF report prompt starter..." : "REF search prompt starter..."}
            </option>
            {activeStarters.map((starter) => (
              <option key={starter.id} value={starter.id}>
                {starter.label}
              </option>
            ))}
          </Form.Select>
          <Button
            type="button"
            variant="outline-primary"
            size="sm"
            onClick={handleApplyStarter}
            disabled={isLoading || isGenerating || !selectedStarterId}
          >
            Use
          </Button>
        </div>
      </div>

      {/* File Upload Section */}
      {!isExistingMode && (
        <div className="form-section mb-4">
          <label className="form-label">Upload PDF or DOCX evidence files (optional)</label>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.docx"
            multiple
            style={{ display: "none" }}
          />
          <Button
            variant="outline-secondary"
            onClick={handleUploadClick}
            disabled={isLoading || isGenerating}
            className="w-100"
          >
            Upload PDF/DOCX files as context
          </Button>
          {uploadedFileName && <p className="uploaded-file-name mt-2">{uploadedFileName}</p>}
        </div>
      )}

      {/* Theme Section */}
      <div className="form-section mb-4">
        <label className="form-label">
          Theme {isExistingMode ? <span className="required">*</span> : "(optional)"}
        </label>
        <SelectTheme
          value={formData.theme_id}
          onChange={handleThemeChange}
        />
        {isExistingMode && formData.theme_id && (
          <p className="mt-2 mb-0 text-muted small">
            {isCheckingUseCaseCount
              ? "Checking existing use cases for this theme..."
              : existingUseCaseCount === null
              ? "Unable to check existing use cases for this theme."
              : existingUseCaseCount === 0
              ? "No existing use cases found for this theme. Generate some first, or switch to a different theme."
              : `${existingUseCaseCount} existing use case(s) found for this theme.`}
          </p>
        )}
      </div>

      {/* Search Settings Section */}
      {!isExistingMode && (
      <div className="form-section mb-4">
        <label className="form-label">Search settings</label>
        <Row>
          <Col md={4}>
            <Form.Group>
              <Form.Label className="section-field-label">Number of outcomes</Form.Label>
              <Form.Select
                value={formData.numberOfOutcomes}
                onChange={(e) => handleNumberOfOutcomesChange(e.target.value)}
                disabled={isLoading || isGenerating}
              >
                <option value="5">5</option>
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label className="section-field-label">Search complexity</Form.Label>
              <Form.Select
                value={formData.searchComplexity}
                onChange={(e) => handleSearchComplexityChange(e.target.value)}
                disabled={isLoading || isGenerating}
              >
                <option value="low">Lowest cost (targeted REF evidence)</option>
                <option value="simple">Simple</option>
                <option value="medium">Medium</option>
                <option value="complex">Complex</option>
                <option value="advanced">Advanced</option>
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group>
              <Form.Label className="section-field-label">Result filtering</Form.Label>
              <Form.Select
                value={formData.relevanceThreshold}
                onChange={(e) => handleRelevanceThresholdChange(e.target.value)}
                disabled={isLoading || isGenerating}
              >
                <option value="">Standard (recommended)</option>
                <option value="0.3">Loose - show more, lower confidence</option>
                <option value="0">Show everything - no relevance filter</option>
              </Form.Select>
              <Form.Text className="text-muted" style={{ fontSize: "12px" }}>
                Credibility score is never filtered automatically - it's shown for you to judge. This only
                controls the relevance cutoff.
              </Form.Text>
            </Form.Group>
          </Col>
        </Row>
      </div>
      )}

      {/* Sections Configuration */}
      {isExistingMode && (
      <div className="form-section mb-4">
        <label className="form-label">
          Sections <span className="required">*</span>
        </label>

        <div className="sections-container">
          {formData.sections.map((section, index) => (
            <Card key={section.id} className="section-card mb-3">
              <Card.Body>
                <Row className="mb-3">
                  <Col md={8}>
                    <Form.Group>
                      <Form.Label className="section-field-label">Section {index + 1} Title</Form.Label>
                      <Form.Control
                        type="text"
                        placeholder="Section Title"
                        value={section.title}
                        onChange={(e) =>
                          handleSectionChange(section.id, "title", e.target.value)
                        }
                        disabled={isLoading || isGenerating}
                      />
                    </Form.Group>
                  </Col>
                  <Col md={4}>
                    <Form.Group>
                      <Form.Label className="section-field-label">Max Words</Form.Label>
                      <div className="d-flex align-items-center" style={{ gap: "4px" }}>
                        <Form.Control
                          type="number"
                          value={section.maxWords}
                          onChange={(e) => {
                            const v = parseInt(e.target.value);
                            if (!isNaN(v)) handleSectionChange(section.id, "maxWords", v);
                          }}
                          onBlur={(e) => {
                            const v = parseInt(e.target.value) || 50;
                            handleSectionChange(section.id, "maxWords", Math.min(10000, Math.max(50, v)));
                          }}
                          disabled={isLoading || isGenerating}
                        />
                        <div className="d-flex flex-column" style={{ gap: "2px", flexShrink: 0 }}>
                          <button
                            type="button"
                            className="btn btn-sm p-0"
                            style={{ lineHeight: 1, width: "22px", height: "18px", fontSize: "10px", background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.2)", color: "#fff", borderRadius: "3px" }}
                            onClick={() => handleSectionChange(section.id, "maxWords", Math.min(10000, (section.maxWords || 0) + 100))}
                            disabled={isLoading || isGenerating}
                            title="Increase by 100"
                          >▲</button>
                          <button
                            type="button"
                            className="btn btn-sm p-0"
                            style={{ lineHeight: 1, width: "22px", height: "18px", fontSize: "10px", background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.2)", color: "#fff", borderRadius: "3px" }}
                            onClick={() => handleSectionChange(section.id, "maxWords", Math.max(50, (section.maxWords || 0) - 100))}
                            disabled={isLoading || isGenerating}
                            title="Decrease by 100"
                          >▼</button>
                        </div>
                      </div>
                    </Form.Group>
                  </Col>
                </Row>

                <Form.Group className="mb-3">
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <Form.Label className="section-field-label mb-0">Section Description</Form.Label>
                    <Button
                      variant="link"
                      size="sm"
                      className="p-0"
                      onClick={() => toggleSectionExpanded(section.id)}
                      disabled={isLoading || isGenerating}
                    >
                      {expandedSections.has(section.id) ? (
                        <>
                          <i className="bi bi-chevron-up"></i> Hide
                        </>
                      ) : (
                        <>
                          <i className="bi bi-chevron-down"></i> Show More
                        </>
                      )}
                    </Button>
                  </div>
                  
                  {!expandedSections.has(section.id) ? (
                    <Form.Control
                      type="text"
                      placeholder="Click 'Show More' to edit section description..."
                      value={section.description.substring(0, 50) + (section.description.length > 50 ? "..." : "")}
                      disabled={true}
                      className="text-muted"
                      style={{ backgroundColor: '#f8f9fa' }}
                    />
                  ) : (
                    <Form.Control
                      as="textarea"
                      placeholder="Section description..."
                      className="section-textarea-auto-expand"
                      value={section.description}
                      onChange={(e) => {
                        handleSectionChange(section.id, "description", e.target.value);
                        // Auto-expand textarea
                        setTimeout(() => {
                          e.target.style.height = 'auto';
                          e.target.style.height = Math.max(120, e.target.scrollHeight) + 'px';
                        }, 0);
                      }}
                      onInput={(e) => {
                        const target = e.target as HTMLTextAreaElement;
                        target.style.height = 'auto';
                        target.style.height = Math.max(120, target.scrollHeight) + 'px';
                      }}
                      disabled={isLoading || isGenerating}
                      style={{} as React.CSSProperties}
                    />
                  )}
                </Form.Group>

                {formData.sections.length > 1 && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => handleRemoveSection(section.id)}
                    disabled={isLoading || isGenerating}
                    className="w-100"
                  >
                    Remove section {index + 1}
                  </Button>
                )}
              </Card.Body>
            </Card>
          ))}
        </div>

        <Button
          variant="outline-primary"
          onClick={handleAddSection}
          disabled={isLoading || isGenerating}
          className="w-100 mb-3"
        >
          + Add Section
        </Button>
      </div>
      )}

      {/* Include Summary Checkbox */}
      {isExistingMode && (
      <div className="form-section mb-4">
        <Form.Check
          type="checkbox"
          id="include-summary"
          label="Include Summary section at the end"
          checked={formData.includeSummary}
          onChange={(e) => handleIncludeSummaryChange(e.target.checked)}
          disabled={isLoading || isGenerating}
        />
      </div>
      )}

      {!isExistingMode && (
        <div className="form-section mb-4">
          <small className="text-muted d-block">
            This run will search and save use cases only. Use existing use cases for the theme to compile the
            professional REF report afterwards.
          </small>
        </div>
      )}

      {/* Progress Bar */}
      {isGenerating && (
        <div className="form-section mb-4">
          <ProgressBar now={progress} label={`${progress}%`} />
        </div>
      )}

      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        size="lg"
        className="w-100"
        disabled={
          isLoading ||
          isGenerating ||
          (isExistingMode
            ? !formData.theme_id || existingUseCaseCount === 0
            : !formData.prompt.trim() && !formData.theme_id && formData.uploadedFiles.length === 0)
        }
      >
        {isGenerating ? (
          <>
            <Spinner animation="border" size="sm" className="me-2" />
            {isExistingMode ? "Compiling Report..." : "Finding Evidence..."}
          </>
        ) : isLoading ? (
          <>
            <Spinner animation="border" size="sm" className="me-2" />
            Loading...
          </>
        ) : isExistingMode ? (
          "Compile Report from Existing Use Cases"
        ) : (
          "Find and Save Use Cases"
        )}
      </Button>
    </Form>
  );
};

export default ImpactCaseStudyForm;
