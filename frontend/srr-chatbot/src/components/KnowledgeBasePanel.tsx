import React, { useState, useEffect } from 'react';
import './KnowledgeBasePanel.css';
import { getRAGFiles, deleteRAGFile, downloadRAGFile } from '../services/api';
import { RAGFile } from '../types/index';
import KBFileUploadModal from './KBFileUploadModal';
import KBFilePreviewModal from './KBFilePreviewModal';
import GradientButton from './GradientButton';

interface KnowledgeBasePanelProps {
  searchQuery?: string;
}

const KnowledgeBasePanel: React.FC<KnowledgeBasePanelProps> = ({ searchQuery = '' }) => {
  const [files, setFiles] = useState<RAGFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const response = await getRAGFiles();
      setFiles(response);
      setError(null);
    } catch (err) {
      setError('Failed to load file list');
      console.error('Load files error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleDelete = async (fileId: number, filename: string) => {
    if (!window.confirm(`Delete file "${filename}"?`)) {
      return;
    }

    try {
      await deleteRAGFile(fileId);
      setFiles(files.filter(f => f.id !== fileId));
      alert('File deleted successfully');
    } catch (err) {
      alert('Failed to delete file');
      console.error('Delete file error:', err);
    }
  };

  const handleDownload = async (fileId: number, filename: string) => {
    try {
      await downloadRAGFile(fileId, filename);
    } catch (err) {
      alert('Failed to download file');
      console.error('Download file error:', err);
    }
  };

  const handlePreview = (fileId: number) => {
    setSelectedFileId(fileId);
    setPreviewModalOpen(true);
  };

  const handleUploadSuccess = () => {
    setUploadModalOpen(false);
    loadFiles();
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

  const q = searchQuery.trim().toLowerCase();
  const filteredFiles = q
    ? files.filter(
        (f) =>
          (f.filename || '').toLowerCase().includes(q) ||
          (f.file_type || '').toLowerCase().includes(q)
      )
    : files;

  const getFileTypeColor = (fileType: string): string => {
    const colorMap: { [key: string]: string } = {
      'excel': '#217346',
      'word': '#2b579a',
      'powerpoint': '#d24726',
      'pdf': '#dc3545',
      'txt': '#6c757d',
      'csv': '#28a745',
      'image': '#17a2b8'
    };
    return colorMap[fileType] || '#6c757d';
  };

  if (loading) {
    return (
      <div className="knowledge-base-panel">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="knowledge-base-panel">
        <div className="error-state">
          <p>{error}</p>
          <GradientButton onClick={loadFiles} size="sm" variant="primary">
            Retry
          </GradientButton>
        </div>
      </div>
    );
  }

  return (
    <div className="knowledge-base-panel">
      <div className="panel-header">
        <div>
          <h2>Knowledge Base Files</h2>
          <p className="panel-description">
            Manage RAG knowledge base files
          </p>
        </div>
        <GradientButton
            className="upload-button"
            onClick={() => setUploadModalOpen(true)}
            size="md"
            variant="primary"
          >
            <span className="button-icon">⬆️</span>
            Upload file
          </GradientButton>
      </div>

      {filteredFiles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📚</div>
          <h3>{files.length === 0 ? 'No knowledge base files' : 'No matching files'}</h3>
          <p>{files.length === 0 ? 'Click "Upload file" to add knowledge base files' : `No results for "${searchQuery}"`}</p>
          {files.length === 0 && (
            <GradientButton
              className="upload-button-large"
              onClick={() => setUploadModalOpen(true)}
              size="lg"
              variant="primary"
            >
              Upload first file
            </GradientButton>
          )}
        </div>
      ) : (
        <div className="files-grid">
          {filteredFiles.map((file) => (
            <div key={file.id} className="file-card">
              <div className="file-card-header">
                <div 
                  className="file-type-icon" 
                  style={{ backgroundColor: getFileTypeColor(file.file_type) }}
                >
                  {formatFileType(file.file_type)}
                </div>
                <div className="file-status">
                  {file.processed ? (
                    <span className="status-badge success">✓ Processed</span>
                  ) : (
                    <span className="status-badge warning">⏳ Processing</span>
                  )}
                </div>
              </div>

              <div className="file-card-body">
                <h3 className="file-name" title={file.filename}>
                  {file.filename}
                </h3>
                <div className="file-meta">
                  <div className="meta-item">
                    <span className="meta-label">Size: </span>
                    <span className="meta-value">{formatFileSize(file.file_size)}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Chunks: </span>
                    <span className="meta-value">{file.processed ? file.chunk_count : '—'}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Uploaded: </span>
                    <span className="meta-value">
                      {new Date(file.upload_time).toLocaleDateString('zh-CN')}
                    </span>
                  </div>
                </div>

                {file.processing_error && (
                  <div className="error-message">
                    <span>⚠️ {file.processing_error}</span>
                  </div>
                )}
              </div>

              <div className="file-card-actions">
                <button 
                  className="action-button preview"
                  onClick={() => handlePreview(file.id)}
                  title="Preview"
                >
                  👁️ Preview
                </button>
                <button 
                  className="action-button download"
                  onClick={() => handleDownload(file.id, file.filename)}
                  title="Download"
                >
                  ⬇️ Download
                </button>
                <button 
                  className="action-button delete"
                  onClick={() => handleDelete(file.id, file.filename)}
                  title="Delete"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="panel-footer">
        <p>{filteredFiles.length === files.length ? `${files.length} knowledge base file(s)` : `${filteredFiles.length} of ${files.length} file(s)`}</p>
      </div>

      {uploadModalOpen && (
        <KBFileUploadModal
          onClose={() => setUploadModalOpen(false)}
          onSuccess={handleUploadSuccess}
        />
      )}

      {previewModalOpen && selectedFileId && (
        <KBFilePreviewModal
          fileId={selectedFileId}
          onClose={() => {
            setPreviewModalOpen(false);
            setSelectedFileId(null);
          }}
        />
      )}
    </div>
  );
};

export default KnowledgeBasePanel;
