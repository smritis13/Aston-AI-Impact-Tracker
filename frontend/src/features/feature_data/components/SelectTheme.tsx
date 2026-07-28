import React, { useState } from 'react';
import { Form } from 'react-bootstrap';
import { useThemes } from '../hooks/useThemes';
import { useMutation, useQueryClient } from 'react-query';
import { ContentHttpService, Theme, ThemeFormData } from '../services';

interface SelectThemeProps {
  value: number | null;
  onChange: (value: number | null) => void;
  featured?: boolean;
  className?: string;
  required?: boolean;
}

const SelectTheme: React.FC<SelectThemeProps> = ({ value, onChange, featured, className, required = false }) => {
  const [showModal, setShowModal] = useState(false);
  const queryClient = useQueryClient();
  const { themes, loading, error } = useThemes({ page: 1, pageSize: 100, featured });

  const mutation = useMutation({
    mutationFn: (data: ThemeFormData) => ContentHttpService.saveTheme(data),
    onSuccess: (newTheme: Theme) => {
      queryClient.invalidateQueries('themes');
      onChange(newTheme.id);
      setShowModal(false);
    },
  });

  if (loading) {
    return <Form.Select disabled><option>Loading themes...</option></Form.Select>;
  }

  if (error) {
    return <Form.Select disabled><option>Error loading themes</option></Form.Select>;
  }

  return (
    <>
      <div className="d-flex gap-2">
        <Form.Select
          value={value || ''}
          onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
          required={required}
          className={`flex-grow-1 ${className}`}
        >
          <option value="">Select a theme</option>
          {themes.map((theme) => (
            <option key={theme.id} value={theme.id}>
              {theme.title}
            </option>
          ))}
        </Form.Select>
        {/* <button
          type="button"
          className="btn btn-outline-primary"
          onClick={() => setShowModal(true)}
          title="Generate new theme"
        >
          <i className="ri-add-line"></i>
        </button>
        <Link
          to="/themes"
          className="btn btn-outline-secondary"
          title="Manage themes"
        >
          <i className="ri-settings-4-line"></i>
        </Link> */}
      </div>

      {/* <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Generate New Theme</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ThemeForm onSuccess={() => setShowModal(false)} />
        </Modal.Body>
      </Modal> */}
    </>
  );
};

export default SelectTheme; 
