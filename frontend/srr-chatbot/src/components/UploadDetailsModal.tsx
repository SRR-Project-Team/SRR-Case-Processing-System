
import React from 'react';
import { X, FileText, Calendar, User, MapPin, Phone, AlertCircle } from 'lucide-react';
import { ExtractedData, FileInfo } from '../types';

interface UploadDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileInfo: FileInfo | null;
  extractedData: ExtractedData | null;
  summaryResult?: any;
}

const UploadDetailsModal: React.FC<UploadDetailsModalProps> = ({
  isOpen,
  onClose,
  fileInfo,
  extractedData,
  summaryResult
}) => {
  if (!isOpen) return null;

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileTypeIcon = (type: string) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('text')) return '📝';
    return '📁';
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title">
            <FileText className="modal-icon" />
            <span>File Upload Details</span>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* File Information Section */}
          <div className="detail-section">
            <h3 className="section-title">
              📁 File Information
            </h3>
            <div className="file-info-grid">
              <div className="info-item">
                <span className="info-label">File Name:</span>
                <span className="info-value">{fileInfo?.name}</span>
              </div>
              <div className="info-item">
                <span className="info-label">File Size:</span>
                <span className="info-value">{fileInfo ? formatFileSize(fileInfo.size) : 'N/A'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">File Type:</span>
                <span className="info-value">
                  {getFileTypeIcon(fileInfo?.type || '')} {fileInfo?.type || 'N/A'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Upload Time:</span>
                <span className="info-value">{new Date().toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* AI Summary Section */}
          {summaryResult && (
            <div className="detail-section">
              <h3 className="section-title">
                🤖 AI Summary
              </h3>
              <div className="summary-content">
                {summaryResult.success ? (
                  <div className="summary-success">
                    <div className="summary-text">{summaryResult.summary}</div>
                    <div className="summary-meta">
                      <span className="summary-source">Source: {summaryResult.source}</span>
                    </div>
                  </div>
                ) : (
                  <div className="summary-error">
                    <AlertCircle className="error-icon" />
                    <span>Summary generation failed: {summaryResult.error}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Extracted Data Section */}
          {extractedData && (
            <div className="detail-section">
              <h3 className="section-title">
                📊 Extracted Case Data
              </h3>
              <div className="extracted-data-grid">
                <div className="data-row">
                  <div className="data-item">
                    <Calendar className="data-icon" />
                    <span className="data-label">Date Received:</span>
                    <span className="data-value">{extractedData.A_date_received || 'N/A'}</span>
                  </div>
                </div>
                
                <div className="data-row">
                  <div className="data-item">
                    <span className="data-label">Source:</span>
                    <span className="data-value">{extractedData.B_source || 'N/A'}</span>
                  </div>
                  <div className="data-item">
                    <span className="data-label">Case Number:</span>
                    <span className="data-value">{extractedData.C_case_number || 'N/A'}</span>
                  </div>
                </div>

                <div className="data-row">
                  <div className="data-item">
                    <span className="data-label">Type:</span>
                    <span className={`data-value case-type ${extractedData.D_type?.toLowerCase()}`}>
                      {extractedData.D_type || 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="data-row">
                  <div className="data-item">
                    <User className="data-icon" />
                    <span className="data-label">Caller:</span>
                    <span className="data-value">{extractedData.E_caller_name || 'N/A'}</span>
                  </div>
                  <div className="data-item">
                    <Phone className="data-icon" />
                    <span className="data-label">Contact:</span>
                    <span className="data-value">{extractedData.F_contact_no || 'N/A'}</span>
                  </div>
                </div>

                <div className="data-row">
                  <div className="data-item">
                    <span className="data-label">Slope Number:</span>
                    <span className="data-value">{extractedData.G_slope_no || 'N/A'}</span>
                  </div>
                </div>

                <div className="data-row">
                  <div className="data-item full-width">
                    <MapPin className="data-icon" />
                    <span className="data-label">Location:</span>
                    <span className="data-value">{extractedData.H_location || 'N/A'}</span>
                  </div>
                </div>

                <div className="data-row">
                  <div className="data-item full-width">
                    <span className="data-label">Nature of Request:</span>
                    <span className="data-value">{extractedData.I_nature_of_request || 'N/A'}</span>
                  </div>
                </div>

                <div className="data-row">
                  <div className="data-item">
                    <span className="data-label">Subject Matter:</span>
                    <span className="data-value">{extractedData.J_subject_matter || 'N/A'}</span>
                  </div>
                </div>

                <div className="data-row">
                  <div className="data-item">
                    <span className="data-label">10-day Due:</span>
                    <span className="data-value">{extractedData.K_10day_rule_due_date || 'N/A'}</span>
                  </div>
                  <div className="data-item">
                    <span className="data-label">ICC Interim Due:</span>
                    <span className="data-value">{extractedData.L_icc_interim_due || 'N/A'}</span>
                  </div>
                </div>

                <div className="data-row">
                  <div className="data-item">
                    <span className="data-label">ICC Final Due:</span>
                    <span className="data-value">{extractedData.M_icc_final_due || 'N/A'}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
          <button className="btn-primary" onClick={() => {
            // Can add export functionality
            console.log('Export data');
            onClose();
          }}>
            Export Data
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadDetailsModal;