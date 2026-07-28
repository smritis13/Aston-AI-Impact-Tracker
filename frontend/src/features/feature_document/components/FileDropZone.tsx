import React, { FC, useCallback, useState } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';

interface FileDropzoneProps {
  onDocumentsSelected: (files: File[]) => void;
}

const FileDropzone: FC<FileDropzoneProps> = ({ onDocumentsSelected }) => {
  // State to track selected files
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  /**
   * When files are added, update state and notify parent component.
   */
  const handleFilesAdded = (files: File[]) => {
    setSelectedFiles(files);
    onDocumentsSelected(files); // Notify parent component
  };

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      handleFilesAdded(acceptedFiles);
    },
    []
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
   });

  // Styles for the drop zone.
  const dropzoneStyle: React.CSSProperties = {
    border: '1px dashed rgba(204, 204, 204, 0.49)',
    borderRadius: '5px',
    padding: '20px',
    textAlign: 'center',
    cursor: 'pointer',
    background: isDragActive ? 'rgb(76 132 255 / 10%)' : 'rgb(37,39,62)',
    minHeight: '200px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    color: '#fff',
  };

  return (
    <div style={{ display: 'flex', gap: '20px' }}>
      {/* Left side: Drop zone */}
      <div style={{ flex: 1 }}>
        <div {...getRootProps()} style={dropzoneStyle}>
          <input {...getInputProps()} />
          {isDragActive ? (
            <p>Drop the files here ...</p>
          ) : (
            <p>Drag & drop some files here, or click to select files</p>
          )}
        </div>
      </div>

      {/* Right side: File Preview List */}
      {/* {selectedFiles.length > 0 && (
        <div style={{ flex: 1 }}>
          <h5 style={{ color: '#fff' }}>Selected Files</h5>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {selectedFiles.map((file, index) => (
              <li key={index} style={{ marginBottom: '10px', color: '#fff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>{file.name}</span>
                  <span>{(file.size / 1024).toFixed(2)} KB</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )} */}
    </div>
  );
};

export default FileDropzone;
