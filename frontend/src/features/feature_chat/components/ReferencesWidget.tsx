import React, { useState } from 'react';
import CustomModal from 'core/components/shared/CustomModal';
import { Button } from 'react-bootstrap';

export interface Reference {
  title: string;
  url: string;
  file_type?: string;
  server_url?: string;
}

interface ReferencesProps {
  references: Reference[];
}

const References: React.FC<ReferencesProps> = ({ references }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const getIconClass = (ref: Reference): string => {
    if (ref.file_type) {
      const fileType = ref.file_type.toLowerCase();
      if (fileType === '.pdf') {
        return "fas fa-file-pdf";
      } else if (fileType === '.doc' || fileType === '.docx') {
        return "fas fa-file-word";
      } else if (fileType === '.xls' || fileType === '.xlsx') {
        return "fas fa-file-excel";
      } else {
        return "fas fa-file";
      }
    }
    return "fas fa-link";
  };

  return (
    <>
      <Button
        variant="outline-secondary"
        className="references-summary"
        onClick={() => setIsModalOpen(true)}
      >
        <i className="fas fa-link me-2"></i>
        {references.length} {references.length === 1 ? 'reference' : 'references'}
      </Button>

      <CustomModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="References"
        size="lg"
        showFooter={false}
      >
        <div className="references-list mt-3">
          {references.map((ref, index) => (
            <a
              key={index+'reference'}
              href={ref.url}
              target="_blank"
              rel="noopener noreferrer"
              className="reference-item mb-1 d-flex align-items-center p-2 border-bottom"
            >
              <i className={`${getIconClass(ref)} me-2`}></i>
              <span>{ref.title}</span>
            </a>
          ))}
        </div>
      </CustomModal>
    </>
  );
};

export default References;
