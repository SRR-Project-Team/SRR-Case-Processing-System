import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './KBFileUploadModal.css';
import { uploadRAGFile } from '../services/api';
import GradientButton from './GradientButton';

interface KBFileUploadModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const KBFileUploadModal: React.FC<KBFileUploadModalProps> = ({ onClose, onSuccess }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const acceptedFileTypes = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'application/pdf': ['.pdf'],
    'text/plain': ['.txt'],
    'text/csv': ['.csv'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif']
  };

  const maxFileSize = 100 * 1024 * 1024; // 100MB

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Filter out duplicates
    const newFiles = acceptedFiles.filter(
      (file) => !selectedFiles.some((f) => f.name === file.name && f.size === file.size)
    );
    setSelectedFiles((prev) => [...prev, ...newFiles]);
  }, [selectedFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFileTypes,
    maxSize: maxFileSize,
    multiple: true
  });

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setErrors({});
    const newProgress: { [key: string]: number } = {};
    selectedFiles.forEach(file => {
      newProgress[file.name] = 0;
    });
    setUploadProgress(newProgress);

    let successCount = 0;
    let errorCount = 0;

    try {
      for (const file of selectedFiles) {
        try {
          const uploaded = await uploadRAGFile(file, (progress) => {
            setUploadProgress((prev) => ({
              ...prev,
              [file.name]: progress
            }));
          });
          setUploadProgress((prev) => ({
            ...prev,
            [file.name]: 100
          }));
          successCount++;
          // File may be processing in background (processed === false)
          if (!uploaded.processed) {
            console.log(`File ${file.name} queued for background processing`);
          }
        } catch (error: any) {
          setErrors((prev) => ({
            ...prev,
            [file.name]: error.message || 'Upload failed'
          }));
          errorCount++;
        }
      }

      if (errorCount === 0) {
        alert(
          successCount === 1
            ? 'File uploaded. Processing in background (chunking and embedding). Refresh the list later to see when it\'s ready.'
            : `Successfully uploaded ${successCount} file(s). Processing in background. Refresh the list later to see when ready.`
        );
        onSuccess();
      } else {
        alert(`Upload complete: ${successCount} succeeded, ${errorCount} failed`);
      }
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const getFileIcon = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const iconMap: { [key: string]: string } = {
      'xlsx': '📊',
      'xls': '📊',
      'docx': '📄',
      'pptx': '📽️',
      'pdf': '📕',
      'txt': '📝',
      'csv': '📋',
      'jpg': '🖼️',
      'jpeg': '🖼️',
      'png': '🖼️',
      'gif': '🖼️'
    };
    return iconMap[ext || ''] || '📎';
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content kb-upload-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Upload knowledge base files</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            <div className="dropzone-content">
              <div className="dropzone-icon">📤</div>
              <p className="dropzone-text">
                {isDragActive ? 'Drop files to upload' : 'Drag files here or click to select'}
              </p>
              <p className="dropzone-hint">
                Supported: Excel, Word, PowerPoint, PDF, TXT, CSV, images
              </p>
              <p className="dropzone-hint">
                Max file size: 100MB
              </p>
            </div>
          </div>

          {selectedFiles.length > 0 && (
            <div className="selected-files">
              <h3>Selected files ({selectedFiles.length})</h3>
              <div className="files-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <span className="file-icon">{getFileIcon(file.name)}</span>
                      <div className="file-details">
                        <div className="file-name">{file.name}</div>
                        <div className="file-size">{formatFileSize(file.size)}</div>
                      </div>
                    </div>
                    
                    {uploading ? (
                      <div className="upload-progress">
                        <div 
                          className="progress-bar" 
                          style={{ width: `${uploadProgress[file.name] || 0}%` }}
                        />
                        <span className="progress-text">
                          {(uploadProgress[file.name] || 0) >= 100
                            ? 'Processing...'
                            : `${uploadProgress[file.name] || 0}%`}
                        </span>
                      </div>
                    ) : (
                      <button 
                        className="remove-button" 
                        onClick={() => removeFile(index)}
                        title="Remove"
                      >
                        ×
                      </button>
                    )}

                    {errors[file.name] && (
                      <div className="file-error">{errors[file.name]}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <GradientButton
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={uploading}
          >
            Cancel
          </GradientButton>
          <GradientButton
            variant="primary"
            size="sm"
            onClick={handleUpload}
            disabled={selectedFiles.length === 0 || uploading}
          >
            {uploading
              ? (Object.keys(uploadProgress).every((name) => (uploadProgress[name] || 0) >= 100)
                ? 'Processing...'
                : 'Uploading...')
              : `Upload ${selectedFiles.length} file(s)`}
          </GradientButton>
        </div>
      </div>
    </div>
  );
};

export default KBFileUploadModal;
