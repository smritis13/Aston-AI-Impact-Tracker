import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

interface GenerateReportFormProps {
  onClose: () => void;
}

const GenerateReportForm: React.FC<GenerateReportFormProps> = ({ onClose }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    topic: "",
    report_length: "detailed",
    industry: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onClose();
    // Navigate to the report generation page with form data
    navigate("/reports/generate", { state: formData });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-3">
        <label htmlFor="topic" className="form-label">Topic</label>
        <input
          type="text"
          className="form-control"
          id="topic"
          name="topic"
          value={formData.topic}
          onChange={handleChange}
          required
          placeholder="Enter report topic"
        />
      </div>

      <div className="mb-3">
        <label htmlFor="report_length" className="form-label">Report Length</label>
        <select
          className="form-select"
          id="report_length"
          name="report_length"
          value={formData.report_length}
          onChange={handleChange}
        >
          <option value="short">Short</option>
          <option value="medium">Medium</option>
          <option value="detailed">Detailed</option>
        </select>
      </div>

      <div className="mb-3">
        <label htmlFor="industry" className="form-label">Industry (Optional)</label>
        <input
          type="text"
          className="form-control"
          id="industry"
          name="industry"
          value={formData.industry}
          onChange={handleChange}
          placeholder="Enter industry focus"
        />
      </div>

      <div className="d-flex justify-content-end gap-2">
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary">
          Generate Report
        </button>
      </div>
    </form>
  );
};

export default GenerateReportForm; 