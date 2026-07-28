import React, { useState } from 'react';
import { Form } from 'react-bootstrap';
import { useMutation, useQueryClient } from 'react-query';
import { ContentHttpService, Theme, ThemeFormData } from '../services';

interface ThemeFormProps {
  theme?: Theme;
  onSuccess: () => void;
}

const ThemeForm: React.FC<ThemeFormProps> = ({ theme, onSuccess }) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<ThemeFormData>({
    title: theme?.title || '',
    description: theme?.description || '',
    featured: theme?.featured || false,
  });
  const [errors, setErrors] = useState<Partial<ThemeFormData>>({});

  const mutation = useMutation({
    mutationFn: (data: ThemeFormData) => ContentHttpService.saveTheme(data, theme?.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['themes'] });
      onSuccess();
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Partial<ThemeFormData> = {};
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      mutation.mutate(formData);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev: ThemeFormData) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
    // Clear error when user starts typing
    if (errors[name as keyof ThemeFormData]) {
      setErrors((prev: Partial<ThemeFormData>) => ({
        ...prev,
        [name]: undefined
      }));
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Group className="mb-3">
        <Form.Label>Title</Form.Label>
        <Form.Control
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          isInvalid={!!errors.title}
        />
        <Form.Control.Feedback type="invalid">
          {errors.title}
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>Description</Form.Label>
        <Form.Control
          as="textarea"
          rows={3}
          name="description"
          value={formData.description}
          onChange={handleChange}
          isInvalid={!!errors.description}
        />
        <Form.Control.Feedback type="invalid">
          {errors.description}
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Check
          type="checkbox"
          name="featured"
          label="Featured Theme"
          checked={formData.featured}
          onChange={handleChange}
        />
      </Form.Group>

      <div className="d-flex justify-content-end gap-2">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={mutation.isLoading}
        >
          {mutation.isLoading ? (
            <>
              <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
              Saving...
            </>
          ) : (
            'Save Theme'
          )}
        </button>
      </div>
    </Form>
  );
};

export default ThemeForm; 