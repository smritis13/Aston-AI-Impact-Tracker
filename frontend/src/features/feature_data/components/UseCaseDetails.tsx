import React from 'react';
import { Modal, ModalHeader, ModalBody, ModalFooter, Button } from 'react-bootstrap';
import TimeAgoWidget from "core/components/shared/TimeAgoWidget";
import UrlSourceWidget from './UrlSourceWidget';

interface UseCase {
  id: number;
  use_case_name: string;
  use_case_type: string;
  company: string;
  industry: string;
  tools: string;
  use_case_description: string;
  performance_impact: string;
  performance_improvement_category: string | null;
  geography: string | null;
  country: string | null;
  use_case_date: string;
  published_date: string | null;
  source: string;
  source_reference: string | null;
  domain: string | null;
  publisher: string | null;
  content_type: string | null;
  direct_quote: string | null;
  ref_period_status: "within_period" | "outside_period" | null;
  reference_number: number | null;
  created_at: string;
  credibility_reasoning: string;
  credibility_score: number;
  is_credible: boolean;
  is_relevant: boolean;
  relevance_reasoning: string;
  relevance_score: number;
  url_validation_score: number;
}

// Flags press_release/news as needing a second look, since these can't be
// used as underpinning-research evidence and Aston's own press releases
// should already have been filtered out at extraction time - if one still
// shows up here, it's worth checking. Exported so UseCasesPage's table can
// render the same badge without duplicating the label/colour mapping.
export const CONTENT_TYPE_LABELS: Record<string, { label: string; variant: string }> = {
  press_release: { label: "Press Release", variant: "warning" },
  peer_reviewed: { label: "Peer-Reviewed", variant: "success" },
  news: { label: "News", variant: "secondary" },
  policy: { label: "Policy Document", variant: "info" },
  testimonial: { label: "Testimonial/Letter", variant: "primary" },
  other: { label: "Other", variant: "secondary" },
};

interface UseCaseDetailsProps {
  useCase: any;
  show: boolean;
  onHide: () => void;
}

const UseCaseDetails: React.FC<UseCaseDetailsProps> = ({ useCase, show, onHide }) => {
  if (!useCase) return null;

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const renderScore = (score: number | null) => {
    if (score === null) return 'N/A';
    return `${score}/10`;
  };

  const renderBoolean = (value: boolean | null) => {
    if (value === null) return 'N/A';
    return value ? 'Yes' : 'No';
  };

  return (
    <Modal show={show} onHide={onHide} size="lg" centered>
      <ModalHeader closeButton>
        <p className="modal-title line-height-2">{useCase.use_case_name}</p>
      </ModalHeader>
      <ModalBody>
        <div className="row g-3">
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Basic Information</h6>
                <dl className="row mb-0">
                  <dt className="col-sm-4">ID</dt>
                  <dd className="col-sm-8">{useCase.id}</dd>
                  
                  <dt className="col-sm-4">Type</dt>
                  <dd className="col-sm-8">{useCase.use_case_type}</dd>
                  
                  <dt className="col-sm-4">Company</dt>
                  <dd className="col-sm-8">{useCase.company}</dd>
                  
                  <dt className="col-sm-4">Industry</dt>
                  <dd className="col-sm-8">{useCase.industry || 'N/A'}</dd>
                  
                  <dt className="col-sm-4">Source Published</dt>
                  <dd className="col-sm-8">
                    {useCase.published_date ? formatDate(useCase.published_date) : (
                      <span className="text-muted">not stated</span>
                    )}
                  </dd>

                  <dt className="col-sm-4">Impact Date</dt>
                  <dd className="col-sm-8">
                    {formatDate(useCase.use_case_date)}
                    {useCase.ref_period_status === "outside_period" && (
                      <span className="badge bg-warning ms-2">&#9888; Outside REF period</span>
                    )}
                    {useCase.ref_period_status === "within_period" && (
                      <span className="badge bg-success ms-2">Within REF period</span>
                    )}
                  </dd>

                  <dt className="col-sm-4">Reference #</dt>
                  <dd className="col-sm-8">{useCase.reference_number ?? 'Not yet assigned'}</dd>

                  <dt className="col-sm-4">Created</dt>
                  <dd className="col-sm-8"><TimeAgoWidget date={useCase.created_at} /></dd>
                </dl>
              </div>
            </div>
          </div>
          
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Credibility & Relevance</h6>
                <dl className="row mb-0">
                  <dt className="col-sm-4">Credibility</dt>
                  <dd className="col-sm-8">{renderBoolean(useCase.is_credible)}</dd>
                  
                  <dt className="col-sm-4">Credibility Score</dt>
                  <dd className="col-sm-8">{renderScore(useCase.credibility_score)}</dd>
                  
                  <dt className="col-sm-4">Relevance</dt>
                  <dd className="col-sm-8">{renderBoolean(useCase.is_relevant)}</dd>
                  
                  <dt className="col-sm-4">Relevance Score</dt>
                  <dd className="col-sm-8">{renderScore(useCase.relevance_score)}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="col-12">
            <div className="card">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Provenance</h6>
                <dl className="row mb-0">
                  <dt className="col-sm-3">Source type</dt>
                  <dd className="col-sm-9">
                    {useCase.content_type ? (
                      <span
                        className={`badge bg-${CONTENT_TYPE_LABELS[useCase.content_type]?.variant || "secondary"}`}
                      >
                        {CONTENT_TYPE_LABELS[useCase.content_type]?.label || useCase.content_type}
                      </span>
                    ) : (
                      "Not classified"
                    )}
                  </dd>

                  <dt className="col-sm-3">Domain</dt>
                  <dd className="col-sm-9">{useCase.domain || "N/A"}</dd>

                  <dt className="col-sm-3">Publisher</dt>
                  <dd className="col-sm-9">{useCase.publisher || "N/A"}</dd>

                  <dt className="col-sm-3">Page/section reference</dt>
                  <dd className="col-sm-9">{useCase.source_reference || "N/A"}</dd>
                </dl>
              </div>
            </div>
          </div>

          {useCase.direct_quote && (
            <div className="col-12">
              <div className="card">
                <div className="card-body">
                  <h6 className="card-subtitle mb-2 text-muted">Direct Quote</h6>
                  <p className="card-text fst-italic">&ldquo;{useCase.direct_quote}&rdquo;</p>
                </div>
              </div>
            </div>
          )}

          <div className="col-12">
            <div className="card">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Tools</h6>
                <div className="mb-3">
                  {useCase.tools?.split(',').map((tool: string, index: number) => (
                    <span key={index} className="badge bg-primary me-1 mb-1" style={{ maxWidth: '150px', fontWeight: 'normal', fontSize: '12px', overflowWrap: 'break-word', whiteSpace: 'normal' }}>
                      {tool.trim()}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="col-12">
            <div className="card">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Description</h6>
                <p className="card-text">{useCase.use_case_description}</p>
              </div>
            </div>
          </div>

          <div className="col-12">
            <div className="card">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Performance Impact</h6>
                <dl className="row mb-0">
                  <dt className="col-sm-3">Impact</dt>
                  <dd className="col-sm-9">{useCase.performance_impact}</dd>
                  
                  <dt className="col-sm-3">Improvement Category</dt>
                  <dd className="col-sm-9">{useCase.performance_improvement_category || 'N/A'}</dd>
                  
                  <dt className="col-sm-3">Geography</dt>
                  <dd className="col-sm-9">{useCase.geography || 'N/A'}</dd>
                  
                  <dt className="col-sm-3">Country</dt>
                  <dd className="col-sm-9">{useCase.country || 'N/A'}</dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="col-12">
            <div className="card">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Credibility Reasoning</h6>
                <p className="card-text">{useCase.credibility_reasoning || 'N/A'}</p>
              </div>
            </div>
          </div>

          <div className="col-12">
            <div className="card">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Relevance Reasoning</h6>
                <p className="card-text">{useCase.relevance_reasoning || 'N/A'}</p>
              </div>
            </div>
          </div>

          <div className="col-12">
            <div className="card">
              <div className="card-body">
                <h6 className="card-subtitle mb-2 text-muted">Source</h6>
                {useCase.source ? (
                  <UrlSourceWidget source={useCase.source} urlValidationScore={useCase.url_validation_score} />
                ) : (
                  'N/A'
                )}
              </div>
            </div>
          </div>
        </div>
      </ModalBody>
      <ModalFooter>
        <Button variant="secondary" onClick={onHide}>
          Close
        </Button>
      </ModalFooter>
    </Modal>
  );
};

export default UseCaseDetails; 