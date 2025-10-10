import React from 'react';
import { FileText, Calendar, User, AlertCircle, X } from 'lucide-react';
import { ExtractedData, FileInfo } from '../types';
import ExtractedInfoDisplay from './ExtractedInfoDisplay';

interface FileInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileInfo: FileInfo | null;
  extractedData: ExtractedData | null;
  summaryResult?: any;
}

const FileInfoModal: React.FC<FileInfoModalProps> = ({
  isOpen,
  onClose,
  fileInfo,
  extractedData,
  summaryResult
}) => {
  if (!isOpen) return null;

  const formatFileSize = (bytes: number) => {
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  const getFileTypeIcon = (type: string) => {
    return type.includes('pdf') ? '📄' : '📝';
  };

  const getProcessingStatus = () => {
    if (extractedData) {
      const filledFields = Object.values(extractedData).filter(value => value && value !== 'N/A').length;
      const totalFields = Object.keys(extractedData).length;
      const completionRate = Math.round((filledFields / totalFields) * 100);

      if (completionRate >= 80) return { status: 'excellent', rate: completionRate, color: '#10b981' };
      if (completionRate >= 60) return { status: 'good', rate: completionRate, color: '#f59e0b' };
      if (completionRate >= 40) return { status: 'fair', rate: completionRate, color: '#ef4444' };
      return { status: 'poor', rate: completionRate, color: '#dc2626' };
    }
    return { status: 'unknown', rate: 0, color: '#6b7280' };
  };

  const processingStatus = getProcessingStatus();

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content file-info-modal" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title">
            <FileText size={20} className="modal-icon" />
            File Processing Details
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* File Information Section */}
          {fileInfo && (
            <div className="detail-section">
              <h3 className="section-title">
                <FileText size={16} />
                File Information
              </h3>
              <div className="file-info-grid">
                <div className="info-item">
                  <div className="info-label">File Name</div>
                  <div className="info-value">
                    <span className="file-icon">{getFileTypeIcon(fileInfo.type)}</span>
                    {fileInfo.name}
                  </div>
                </div>
                <div className="info-item">
                  <div className="info-label">File Size</div>
                  <div className="info-value">{formatFileSize(fileInfo.size)}</div>
                </div>
                <div className="info-item">
                  <div className="info-label">File Type</div>
                  <div className="info-value">{fileInfo.type}</div>
                </div>
                <div className="info-item">
                  <div className="info-label">Upload Time</div>
                  <div className="info-value">
                    {new Date().toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Processing Status Section */}
          {extractedData && (
            <div className="detail-section">
              <h3 className="section-title">
                <AlertCircle size={16} />
                Processing Status
              </h3>
              <div className="processing-status">
                <div className="status-item">
                  <span className="status-label">Data Completion:</span>
                  <div className="status-bar">
                    <div
                      className="status-fill"
                      style={{
                        width: `${processingStatus.rate}%`,
                        backgroundColor: processingStatus.color
                      }}
                    ></div>
                  </div>
                  <span className="status-rate" style={{ color: processingStatus.color }}>
                    {processingStatus.rate}%
                  </span>
                </div>
                <div className="status-item">
                  <span className="status-label">Processing Quality:</span>
                  <span className={`status-badge ${processingStatus.status}`}>
                    {processingStatus.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* AI Summary Section */}
          {summaryResult && (
            <div className="detail-section">
              <h3 className="section-title">
                <Calendar size={16} />
                AI Summary
              </h3>
              <div className="summary-content">
                {summaryResult.summary ? (
                  <div className="summary-success">
                    <div className="summary-text">
                      "{summaryResult.summary}"
                    </div>
                    <div className="summary-meta">
                      <span className="summary-source">
                        Generated by AI • {summaryResult.confidence || 'High'} confidence
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="summary-error">
                    <AlertCircle size={16} className="error-icon" />
                    AI summary generation failed
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Extracted Data Section */}
          {extractedData && (
            <div className="detail-section">
              <h3 className="section-title">
                <User size={16} />
                Extracted Case Data
              </h3>
              <ExtractedInfoDisplay data={extractedData} />
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
          {extractedData && fileInfo && (
            <button className="btn-primary" onClick={() => {
              const exportData = {
                fileInfo: {
                  name: fileInfo.name,
                  size: fileInfo.size,
                  type: fileInfo.type,
                  uploadTime: new Date().toISOString()
                },
                extractedData,
                summaryResult,
                processingStatus: processingStatus,
                exportTime: new Date().toISOString()
              };

              const dataStr = JSON.stringify(exportData, null, 2);
              const dataBlob = new Blob([dataStr], { type: 'application/json' });
              const url = URL.createObjectURL(dataBlob);
              const link = document.createElement('a');
              link.href = url;
              link.download = `srr_case_${fileInfo.name.replace(/\.[^/.]+$/, '')}_${new Date().toISOString().split('T')[0]}.json`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              URL.revokeObjectURL(url);
            }}>
              Export Data
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileInfoModal;
