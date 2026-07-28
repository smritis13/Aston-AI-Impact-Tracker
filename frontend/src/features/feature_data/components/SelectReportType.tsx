import React from 'react';
import { Form } from 'react-bootstrap';

export interface ReportType {
  id: string;
  label: string;
}

export const REPORT_TYPES: ReportType[] = [
  {
    id: 'retail_ai',
    label: 'Retail AI Use Cases',
  },
  {
    id: 'retail_sdlc',
    label: 'Retail SDLC Use Cases',
  },
  {
    id: 'ai_sdlc',
    label: 'AI SDLC Use Cases',
  }
];

interface SelectReportTypeProps {
  value: string;
  onChange: (value: string) => void;
}

const SelectReportType: React.FC<SelectReportTypeProps> = ({ value, onChange }) => {
  return (
    <Form.Group className="mb-3">
      <Form.Select
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Select a report type...</option>
        {REPORT_TYPES.map((type) => (
          <option key={type.id} value={type.id}>
            {type.label}
          </option>
        ))}
      </Form.Select>
      
    </Form.Group>
  );
};

export default SelectReportType; 