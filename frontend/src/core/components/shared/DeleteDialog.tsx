import React, { useState } from "react";
import CustomModal from "./CustomModal";

type DeleteDialogProps = {
  deleteFunction: (id: number) => any; // Function to delete item by ID
  itemId: number; // ID of the item to delete
  isOpen: boolean; // Control the modal visibility
  setOpen: (open: boolean) => void; // Function to toggle the modal
  notifyDone?: () => void; // Callback function to notify when done
};

const DeleteDialog: React.FC<DeleteDialogProps> = ({
  deleteFunction,
  itemId,
  isOpen,
  setOpen,
  notifyDone,
}) => {
  const [loading, setLoading] = useState(false);

  const handleDelete = () => {
    if (loading) return;
    setLoading(true);

    deleteFunction(itemId)
      .then(() => {
        setLoading(false);
        if (notifyDone) notifyDone();
        setOpen(false); // Close the dialog after successful deletion
      })
      .catch(() => {
        setLoading(false);
        // Handle errors if needed
      });
  };

  return (
    <CustomModal isOpen={isOpen} onClose={() => setOpen(false)} title="Are you sure?" showFooter={false}>
      <p className="text-dark">This action cannot be undone.</p>
      <div className="modal-footer">
        <button className="btn btn-secondary" onClick={() => setOpen(false)}>
          No
        </button>
        <button className="btn btn-danger" onClick={handleDelete} disabled={loading}>
          {loading ? <span className="spinner-border spinner-border-sm"></span> : "Yes"}
        </button>
      </div>
    </CustomModal>
  );
};

export default DeleteDialog;
