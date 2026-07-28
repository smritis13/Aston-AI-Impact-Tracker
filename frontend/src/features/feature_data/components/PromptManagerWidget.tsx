import React, { useState, useRef, useEffect } from "react";
import CustomModal from "core/components/shared/CustomModal";
import { Button, Form, ListGroup } from "react-bootstrap";
import { ContentHttpService } from "../services";
import { useNavigate } from 'react-router-dom';
import { REF_PROMPT_STARTERS } from "../constants/refPromptStarters";
import "./PromptManagerWidget.css";

interface Prompt {
  id: number;
  title: string;
  content: string;
  json_structure?: string;
}

interface PromptManagerWidgetProps {
  value: string;
  onChange: (value: string) => void;
  onPromptSelect: (prompt: Prompt) => void;
  onSubmit: (e: React.FormEvent) => void;
}

const PromptManagerWidget: React.FC<PromptManagerWidgetProps> = ({
  value,
  onChange,
  onPromptSelect,
  onSubmit,
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPrompt, setNewPrompt] = useState({
    title: "",
    content: "",
    json_structure: "",
  });
  const [selectedStarterId, setSelectedStarterId] = useState("");
  const navigate = useNavigate();
  const promptTextareaRef = useRef<HTMLTextAreaElement>(null);

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
  }, [value]);

  const loadPrompts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await ContentHttpService.getPrompts();
      setPrompts(response.results as Prompt[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load prompts");
    } finally {
      setIsLoading(false);
    }
  };

  const handleModalOpen = () => {
    setIsModalOpen(true);
    loadPrompts();
  };

  const handleCreatePrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const response = await ContentHttpService.createPrompt(newPrompt);
      setPrompts([...prompts, response as Prompt]);
      setShowCreateForm(false);
      setNewPrompt({ title: "", content: "", json_structure: "" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create prompt");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPrompt = (prompt: Prompt) => {
    onPromptSelect(prompt);
    setIsModalOpen(false);
  };

  const handleApplyStarter = () => {
    const starter = REF_PROMPT_STARTERS.find((item) => item.id === selectedStarterId);
    if (starter) {
      onChange(starter.prompt);
    }
  };

  return (
    <>
      <div className="position-relative">
        <textarea
          ref={promptTextareaRef}
          className="form-control prompt-textarea-auto-expand"
          rows={10}
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            fitPromptTextarea(e.target);
          }}
          onInput={(e) => {
            const target = e.target as HTMLTextAreaElement;
            fitPromptTextarea(target);
          }}
          placeholder="Enter your prompt here..."
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              onSubmit(e);
            }
          }}
          style={{}}
        />
        <Button
          variant="outline-secondary"
          className="position-absolute"
          style={{ right: "10px", top: "10px" }}
          onClick={handleModalOpen}
        >
          <i className="ti ti-history"></i>&nbsp; Prompt History
        </Button>
        <div className="d-flex gap-2 mt-2">
          <Form.Select
            size="sm"
            value={selectedStarterId}
            onChange={(e) => setSelectedStarterId(e.target.value)}
            aria-label="REF prompt starter"
          >
            <option value="">REF prompt starter...</option>
            {REF_PROMPT_STARTERS.map((starter) => (
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
            disabled={!selectedStarterId}
          >
            Use
          </Button>
        </div>
      </div>

      <CustomModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        size="lg"
        title="Prompt History"
        showFooter={false}
      >
        {error && <div className="alert alert-danger">{error}</div>}
        
        {!showCreateForm ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-3">
              {/* <h6 className="mb-0">Saved Prompts</h6> */}
              {/* <Button
                variant="outline-primary"
                size="sm"
                onClick={() => setShowCreateForm(true)}
              >
                <i className="bi bi-plus-lg"></i> New Prompt
              </Button> */}
            </div>
            
            {isLoading ? (
              <div className="text-center py-3">
                <div className="spinner-border spinner-border-sm" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            ) : (
              <ListGroup>
                {Array.isArray(prompts) && prompts.map((prompt) => (
                  <ListGroup.Item
                    key={prompt.id}
                    action
                    onClick={() => handleSelectPrompt(prompt)}
                    className="d-flex justify-content-between align-items-center"
                  >
                    <div>
                      <h6 className="mb-1">{prompt.title}</h6>
                      {/* {prompt.json_structure && (
                        <small className="text-muted">Has JSON structure</small>
                      )} */}
                    </div>
                    <i className="bi bi-chevron-right"></i>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            )}

          <div className="d-flex justify-content-between align-items-center mt-3">
              <Button
                variant="outline-primary"
                size="sm"
                onClick={() => navigate('/prompts')}
              >
                <i className="bi bi-plus-lg"></i> Manage Prompts
              </Button>
            </div>
          </>
        ) : (
          <Form onSubmit={handleCreatePrompt}>
            <Form.Group className="mb-3">
              <Form.Label>Title</Form.Label>
              <Form.Control
                type="text"
                value={newPrompt.title}
                onChange={(e) => setNewPrompt({ ...newPrompt, title: e.target.value })}
                required
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Prompt Content</Form.Label>
              <Form.Control
                as="textarea"
                rows={4}
                value={newPrompt.content}
                onChange={(e) => setNewPrompt({ ...newPrompt, content: e.target.value })}
                required
              />
            </Form.Group>

            {/* <Form.Group className="mb-3">
              <JsonStructureBuilder
                value={newPrompt.json_structure || ""}
                onChange={(value) => setNewPrompt({ ...newPrompt, json_structure: value })}
              />
              <Form.Text className="text-muted">
                Define the structure of the output that should be returned by the report.
              </Form.Text>
            </Form.Group> */}
            
            <div className="d-flex justify-content-end gap-2">
              <Button
                variant="outline-secondary"
                onClick={() => setShowCreateForm(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Saving...
                  </>
                ) : (
                  "Save Prompt"
                )}
              </Button>
            </div>
          </Form>
        )}
      </CustomModal>
    </>
  );
};

export default PromptManagerWidget; 
