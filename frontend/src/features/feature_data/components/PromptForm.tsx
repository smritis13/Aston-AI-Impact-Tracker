import React, { useState } from 'react';
import { Form } from 'react-bootstrap';
import { useMutation, useQueryClient } from 'react-query';
import { ContentHttpService } from '../services';

interface Prompt {
  id?: number;
  title: string;
  content: string;
  json_structure?: string;
}

interface PromptFormProps {
  prompt?: Prompt;
  onSuccess: () => void;
}

const PromptForm: React.FC<PromptFormProps> = ({ prompt, onSuccess }) => {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<Prompt>({
    title: prompt?.title || '',
    content: prompt?.content || '',
    json_structure: prompt?.json_structure || '',
    id: prompt?.id,
  });
  const [errors, setErrors] = useState<Partial<Prompt>>({});

  const mutation = useMutation({
    mutationFn: (data: Prompt) => ContentHttpService.savePrompt(data, prompt?.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] });
      onSuccess();
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Partial<Prompt> = {};
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }
    if (!formData.content.trim()) {
      newErrors.content = 'Content is required';
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
    const { name, value } = e.target;
    setFormData((prev: Prompt) => ({
      ...prev,
      [name]: value
    }));
    if (errors[name as keyof Prompt]) {
      setErrors((prev: Partial<Prompt>) => ({
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
        <Form.Label>Prompt Content</Form.Label>
        <Form.Control
          as="textarea"
          rows={3}
          name="content"
          value={formData.content}
          onChange={handleChange}
          isInvalid={!!errors.content}
        />
        <Form.Control.Feedback type="invalid">
          {errors.content}
        </Form.Control.Feedback>
      </Form.Group>

      <Form.Group className="mb-3">
        <Form.Label>JSON Structure (optional)</Form.Label>
        <Form.Control
          as="textarea"
          rows={2}
          name="json_structure"
          value={formData.json_structure}
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
            'Save Prompt'
          )}
        </button>
      </div>
    </Form>
  );
};

export default PromptForm; 