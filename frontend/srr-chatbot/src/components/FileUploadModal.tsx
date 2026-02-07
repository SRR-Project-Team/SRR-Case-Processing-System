import React from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import './FileUploadModal.css';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFilesSelected: (files: File[]) => void;
  selectedFiles: File[];
  onRemoveFile: (index: number) => void;
  onClearAll: () => void;
  onProcessFiles: () => void;
  isLoading: boolean;
}

const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  onClose,
  onFilesSelected,
  selectedFiles,
  onRemoveFile,
  onClearAll,
  onProcessFiles,
  isLoading
}) => {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onFilesSelected,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    maxFiles: 10
  });

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content file-upload-modal" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title">
            <Upload size={20} className="modal-icon" />
            File Upload & Processing
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* File Upload Area */}
          <div className="upload-section">
            <div {...getRootProps()} className={`file-dropzone ${isDragActive ? 'active' : ''}`}>
              <input {...getInputProps()} />
              <div className="dropzone-content">
                <Upload size={32} className="dropzone-icon" />
                <div className="dropzone-text">
                  {isDragActive ? (
                    <span>Drop files here</span>
                  ) : (
                    <>
                      <strong>Click or drag files here</strong>
                      <br />
                      <small>Supports PDF and TXT files (max 10MB each, up to 10 files)</small>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div className="selected-files-section">
              <div className="files-header">
                <h3>
                  <FileText size={16} />
                  Selected Files ({selectedFiles.length})
                </h3>
                <button 
                  className="clear-all-btn"
                  onClick={onClearAll}
                  disabled={isLoading}
                >
                  Clear All
                </button>
              </div>
              
              <div className="files-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <span className="file-icon">
                        {file.type.includes('pdf') ? '📄' : '📝'}
                      </span>
                      <div className="file-details">
                        <div className="file-name">{file.name}</div>
                        <div className="file-size">
                          {(file.size / 1024).toFixed(1)} KB • {file.type}
                        </div>
                      </div>
                    </div>
                    <button 
                      className="remove-file-btn"
                      onClick={() => onRemoveFile(index)}
                      disabled={isLoading}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              {/* Process Button */}
              <div className="process-section">
                <button 
                  className="process-btn"
                  onClick={onProcessFiles}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <div className="loading-spinner-small"></div>
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload size={16} />
                      {selectedFiles.length === 1 ? 'Process File' : `Process ${selectedFiles.length} Files`}
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUploadModal;
