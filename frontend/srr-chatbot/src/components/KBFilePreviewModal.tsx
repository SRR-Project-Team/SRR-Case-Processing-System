import React, { useState, useEffect } from 'react';
import './KBFilePreviewModal.css';
import { getRAGFileDetails, getRAGFilePreview } from '../services/api';
import { RAGFileDetails, FilePreview } from '../types/index';

interface KBFilePreviewModalProps {
  fileId: number;
  onClose: () => void;
}

const KBFilePreviewModal: React.FC<KBFilePreviewModalProps> = ({ fileId, onClose }) => {
  const [details, setDetails] = useState<RAGFileDetails | null>(null);
  const [preview, setPreview] = useState<FilePreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'info' | 'preview'>('info');

  useEffect(() => {
    loadFileData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileId]); // Only reload when fileId changes

  const loadFileData = async () => {
    try {
      setLoading(true);
      const [detailsData, previewData] = await Promise.all([
        getRAGFileDetails(fileId),
        getRAGFilePreview(fileId, { full: true })
      ]);
      setDetails(detailsData);
      setPreview(previewData);
      setError(null);
    } catch (err) {
      setError('Failed to load file info');
      console.error('Load file data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const formatFileType = (fileType: string): string => {
    const typeMap: { [key: string]: string } = {
      'excel': 'Excel',
      'word': 'Word',
      'powerpoint': 'PowerPoint',
      'pdf': 'PDF',
      'txt': 'TXT',
      'csv': 'CSV',
      'image': 'Image'
    };
    return typeMap[fileType] || fileType;
  };

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content preview-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>File preview</h2>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
          <div className="modal-body">
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !details) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content preview-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>File preview</h2>
            <button className="close-button" onClick={onClose}>×</button>
          </div>
          <div className="modal-body">
            <div className="error-state">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content preview-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{details.filename}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="preview-tabs">
          <button
            className={`preview-tab ${activeTab === 'info' ? 'active' : ''}`}
            onClick={() => setActiveTab('info')}
          >
            File info
          </button>
          <button
            className={`preview-tab ${activeTab === 'preview' ? 'active' : ''}`}
            onClick={() => setActiveTab('preview')}
          >
            Content preview
          </button>
        </div>

        <div className="modal-body">
          {activeTab === 'info' ? (
            <div className="file-info-section">
              <div className="info-grid">
                <div className="info-item">
                  <span className="info-label">File type: </span>
                  <span className="info-value">{formatFileType(details.file_type)}</span>
                </div>

                <div className="info-item">
                  <span className="info-label">File size: </span>
                  <span className="info-value">{formatFileSize(details.file_size)}</span>
                </div>

                <div className="info-item">
                  <span className="info-label">Upload time: </span>
                  <span className="info-value">
                    {new Date(details.upload_time).toLocaleString('zh-CN')}
                  </span>
                </div>

                <div className="info-item">
                  <span className="info-label">Processing status: </span>
                  <span className="info-value">
                    {details.processed ? (
                      <span className="status-badge success">✓ Processed</span>
                    ) : (
                      <span className="status-badge warning">⏳ Processing</span>
                    )}
                  </span>
                </div>

                <div className="info-item">
                  <span className="info-label">Chunk count: </span>
                  <span className="info-value">{details.chunk_count}</span>
                </div>

                <div className="info-item">
                  <span className="info-label">MIME type: </span>
                  <span className="info-value">{details.mime_type}</span>
                </div>
              </div>

              {details.processing_error && (
                <div className="error-message">
                  <h3>Processing error</h3>
                  <p>{details.processing_error}</p>
                </div>
              )}

              {details.metadata && Object.keys(details.metadata).length > 0 && (
                <div className="metadata-section">
                  <h3>File metadata</h3>
                  <div className="metadata-grid">
                    {Object.entries(details.metadata).map(([key, value]) => (
                      <div key={key} className="metadata-item">
                        <span className="metadata-label">{key}:</span>
                        <span className="metadata-value">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="preview-section">
              {preview?.preview_content ? (
                <>
                  <div className="preview-info">
                    <p>Loaded all {preview.total_length} characters (full content)</p>
                  </div>
                  <div className="preview-content">
                    <pre>{preview.preview_content}</pre>
                  </div>
                </>
              ) : (
                <div className="empty-preview">
                  <p>No preview content for this file</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="close-button-footer" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default KBFilePreviewModal;
