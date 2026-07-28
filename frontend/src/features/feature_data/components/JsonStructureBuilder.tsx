import CustomModal from 'core/components/shared/CustomModal';
import React, { useState, useEffect } from 'react';
import { Button, Form, ListGroup } from 'react-bootstrap';

interface JsonField {
  key: string;
  value: string;
}

interface JsonStructureBuilderProps {
  value: string;
  onChange: (value: string) => void;
}

const JsonStructureBuilder: React.FC<JsonStructureBuilderProps> = ({ value, onChange }) => {
  const [fields, setFields] = useState<JsonField[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isJsonMode, setIsJsonMode] = useState(false);
  const [newField, setNewField] = useState<JsonField>({
    key: '',
    value: ''
  });

  // Parse initial JSON structure if provided
  useEffect(() => {
    if (value) {
      try {
        const parsedJson = JSON.parse(value);
        const parsedFields = Object.entries(parsedJson).map(([key, value]) => ({
          key,
          value: String(value)
        }));
        setFields(parsedFields);
      } catch (error) {
        console.error('Failed to parse JSON structure:', error);
      }
    }
  }, [value]);

  const handleAddField = () => {
    if (newField.key) {
      setFields([...fields, newField]);
      setNewField({ key: '', value: '' });
      updateJsonString([...fields, newField]);
      setIsModalOpen(false);
    }
  };

  const handleRemoveField = (index: number) => {
    const updatedFields = fields.filter((_, i) => i !== index);
    setFields(updatedFields);
    updateJsonString(updatedFields);
  };

  const handleFieldChange = (index: number, field: keyof JsonField, value: string) => {
    const updatedFields = fields.map((f, i) => 
      i === index ? { ...f, [field]: value } : f
    );
    setFields(updatedFields);
    updateJsonString(updatedFields);
  };

  const updateJsonString = (updatedFields: JsonField[]) => {
    const jsonObject = updatedFields.reduce((acc, field) => {
      acc[field.key] = field.value;
      return acc;
    }, {} as Record<string, any>);
    
    onChange(JSON.stringify(jsonObject, null, 2));
  };

  const handleJsonChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    try {
      const parsedJson = JSON.parse(newValue);
      const parsedFields = Object.entries(parsedJson).map(([key, value]) => ({
        key,
        value: String(value)
      }));
      setFields(parsedFields);
    } catch (error) {
      console.error('Failed to parse JSON:', error);
    }
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h6 className="mb-0">Output Structure (Optional)</h6>
        <div className="d-flex gap-2">
          <Button
            variant="outline-secondary"
            size="sm"
            onClick={() => setIsJsonMode(!isJsonMode)}
            title={isJsonMode ? "Switch to Form View" : "Switch to JSON View"}
          >
            <i className={`bi ${isJsonMode ? 'bi-code-square' : 'bi-code-square'}`}></i>
          </Button>
          {!isJsonMode && (
            <Button
              variant="outline-primary"
              size="sm"
              onClick={() => setIsModalOpen(true)}
            >
              <i className="bi bi-plus-lg"></i> Add Field
            </Button>
          )}
        </div>
      </div>

      {!isJsonMode ? (
        <>
          <ListGroup>
            {fields.map((field, index) => (
              <ListGroup.Item key={index} className="d-flex justify-content-between align-items-center">
                <div className="flex-grow-1">
                  <div className="d-flex gap-2 align-items-center">
                    <strong>{field.key}</strong>
                    {field.value && (
                      <small className="text-muted">({field.value})</small>
                    )}
                  </div>
                </div>
                <Button
                  variant="outline-danger"
                  size="sm"
                  onClick={() => handleRemoveField(index)}
                >
                  <i className="bi bi-trash"></i>
                </Button>
              </ListGroup.Item>
            ))}
          </ListGroup>

          
        </>
      ) : (
        <Form.Control
          as="textarea"
          rows={6}
          value={value}
          onChange={handleJsonChange}
          placeholder="Enter JSON structure..."
          className="mt-3"
        />
      )}

      <CustomModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Field"
        showFooter={false}
      >
        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Key</Form.Label>
            <Form.Control
              type="text"
              value={newField.key}
              onChange={(e) => setNewField({ ...newField, key: e.target.value })}
              placeholder="Enter field key"
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              type="text"
              value={newField.value}
              onChange={(e) => setNewField({ ...newField, value: e.target.value })}
              placeholder="Enter field description"
            />
          </Form.Group>

          <div className="d-flex justify-content-end gap-2">
            <Button
              variant="outline-secondary"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleAddField}
              disabled={!newField.key}
            >
              Add Field
            </Button>
          </div>
        </Form>
      </CustomModal>
    </div>
  );
};

export default JsonStructureBuilder; 