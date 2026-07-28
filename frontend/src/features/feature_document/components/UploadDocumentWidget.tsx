import React, { useState } from "react";
import FileDropzone from "./FileDropZone";
import useUploadFile from "../hooks/useUploadFile";
import SelectCategory from "./SelectCategory";

const UploadDocumentWidget: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);

  const { uploadFileMutation, uploadProgress } = useUploadFile();

  const handleDocumentsSelected = (files: File[]) => {
    setSelectedFiles(files);
  };

  const handleCategorySelect = (categoryId: number | null) => {
    setSelectedCategory(categoryId);
  };

  const handleUpload = async () => {
    if (!selectedCategory || selectedFiles.length === 0) {
      alert("Please select a category and at least one document.");
      return;
    }


    for (const file of selectedFiles) {
      uploadFileMutation.mutate({ file, categoryId: selectedCategory });
    }
  };

  return (
    <>
      <button
        className="btn btn-sm btn-outline-secondary d-flex align-items-center justify-content-center btn-wave waves-light"
        data-bs-toggle="modal"
        data-bs-target="#create-file"
      >
        <i className="ri-add-circle-line align-middle me-1"></i>
        Upload Document
      </button>

      <div
        className="modal fade"
        id="create-file"
        aria-labelledby="create-file"
        data-bs-keyboard="false"
        aria-hidden="true"
      >
        <div className="modal-dialog modal-lg modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-header">
              <h6 className="modal-title" id="staticBackdropLabel1">
                Upload Document
              </h6>
              <button
                type="button"
                className="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
              ></button>
            </div>
            <div className="modal-body">
              <div className="form-group mb-3">
                <SelectCategory onCategorySelect={handleCategorySelect} />
              </div>
              <div style={{ minHeight: "200px", margin: "auto" }}>
                <FileDropzone onDocumentsSelected={handleDocumentsSelected} />
              </div>
              

              {/* Upload Progress UI */}
              {selectedFiles.length > 0 && (
                <div className="mt-3">
                  <h6>Upload Progress</h6>
                  <ul style={{ listStyle: "none", padding: 0 }}>
                    {selectedFiles.map((file) => {
                      const progressData = uploadProgress[file.name] || { progress: 0, status: "pending" };
                      return (
                        <li key={file.name} style={{ marginBottom: "10px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <span>{file.name}</span>
                            <span>
                              {progressData.status === "done" ? (
                                <i className="ri-check-line" style={{ color: "green" }}></i>
                              ) : progressData.status === "error" ? (
                                <i className="ri-error-warning-line" style={{ color: "red" }}></i>
                              ) : (
                                `${progressData.progress}%`
                              )}
                            </span>
                          </div>
                          <div className="progress" style={{ height: "8px", backgroundColor: "#ccc" }}>
                            <div
                              className="progress-bar"
                              role="progressbar"
                              style={{
                                width: `${progressData.progress}%`,
                                backgroundColor:
                                  progressData.status === "done"
                                    ? "green"
                                    : progressData.status === "error"
                                    ? "red"
                                    : "#007bff",
                              }}
                              aria-valuenow={progressData.progress}
                              aria-valuemin={0}
                              aria-valuemax={100}
                            ></div>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}

              <div className="text-end">
                <button
                  className="btn btn-primary mt-3"
                  onClick={handleUpload}
                  disabled={uploadFileMutation.isLoading}
                >
                  {uploadFileMutation.isLoading ? "Uploading..." : "Upload Files"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default UploadDocumentWidget;
