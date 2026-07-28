import React from 'react';
import { Modal, Button } from 'react-bootstrap';
import { Theme } from '../services';

interface FeatureThemeModalProps {
  show: boolean;
  onHide: () => void;
  theme: Theme | null;
  onToggleFeatured: () => void;
}

const FeatureThemeModal: React.FC<FeatureThemeModalProps> = ({
  show,
  onHide,
  theme,
  onToggleFeatured,
}) => {
  if (!theme) return null;

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>
          {theme.featured ? 'Unfeature Theme' : 'Feature Theme'}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p className="mb-2">
          <strong>Theme:</strong> {theme.title.replace(/-/g, ' ')}
        </p>
        <p>
          {theme.featured
            ? 'This will remove it from the Main Menu.'
            : 'Featured themes will be visible in the Main Menu for quick access.'}
        </p>
        <p>
          {theme.featured
            ? 'Are you sure you want to unfeature this theme?'
            : 'Are you sure you want to feature this theme?'}
        </p>
        
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Cancel
        </Button>
        <Button
          variant={theme.featured ? 'warning' : 'primary'}
          onClick={() => {
            onToggleFeatured();
            onHide();
          }}
        >
          {theme.featured ? 'Unfeature' : 'Feature'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default FeatureThemeModal; 