import React from "react";
import { Button, Modal } from "react-bootstrap";

interface CustomModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave?: () => void;
  title?: string;
  children: React.ReactNode;
  showFooter?: boolean;
  size?: "sm" | "lg" | "xl";
}

const CustomModal: React.FC<CustomModalProps> = ({
  isOpen,
  onClose,
  onSave,
  title = "Modal Title",
  children,
  showFooter = true,
  size = "sm",
}) => {
  return (
    <Modal show={isOpen} size={size ?? "sm"} onHide={onClose} centered>
      <Modal.Header closeButton> 
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>{children}</Modal.Body>
      {showFooter && (
        <Modal.Footer>
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          {onSave && (
            <Button variant="primary" onClick={onSave}>
              Save Changes
            </Button>
          )}
        </Modal.Footer>
      )}
    </Modal>
  );
};

export default CustomModal;
