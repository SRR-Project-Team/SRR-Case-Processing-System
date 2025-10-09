import React from 'react';
import { FileText, Calendar, User, MapPin, Phone, AlertTriangle } from 'lucide-react';
import { ExtractedData } from '../types';

interface ExtractedInfoDisplayProps {
  data: ExtractedData;
}

const ExtractedInfoDisplay: React.FC<ExtractedInfoDisplayProps> = ({ data }) => {
  const formatValue = (value: string | undefined | null) => {
    return value && value.trim() ? value : 'Not provided';
  };

  const isEmptyValue = (value: string | undefined | null) => {
    return !value || !value.trim();
  };

  return (
    <div className="extracted-info">
      <h3>
        <FileText size={16} />
        Extracted Case Information
      </h3>
      
      <div className="info-grid">
        {/* Basic Information */}
        <div className="info-item">
          <div className="info-label">
            <Calendar size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Date Received (A)
          </div>
          <div className={`info-value ${isEmptyValue(data.A_date_received) ? 'empty' : ''}`}>
            {formatValue(data.A_date_received)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">Source (B)</div>
          <div className={`info-value ${isEmptyValue(data.B_source) ? 'empty' : ''}`}>
            {formatValue(data.B_source)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">Case Number (C)</div>
          <div className={`info-value ${isEmptyValue(data.C_case_number) ? 'empty' : ''}`}>
            {formatValue(data.C_case_number)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">Case Type (D)</div>
          <div className={`info-value ${isEmptyValue(data.D_type) ? 'empty' : ''}`}>
            {formatValue(data.D_type)}
          </div>
        </div>

        {/* Contact Information */}
        <div className="info-item">
          <div className="info-label">
            <User size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Caller Name (E)
          </div>
          <div className={`info-value ${isEmptyValue(data.E_caller_name) ? 'empty' : ''}`}>
            {formatValue(data.E_caller_name)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">
            <Phone size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Contact Number (F)
          </div>
          <div className={`info-value ${isEmptyValue(data.F_contact_no) ? 'empty' : ''}`}>
            {formatValue(data.F_contact_no)}
          </div>
        </div>

        {/* Slope Information */}
        <div className="info-item">
          <div className="info-label">
            <AlertTriangle size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Slope Number (G)
          </div>
          <div className={`info-value ${isEmptyValue(data.G_slope_no) ? 'empty' : ''}`}>
            {formatValue(data.G_slope_no)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">
            <MapPin size={12} style={{ display: 'inline', marginRight: '4px' }} />
            Location (H)
          </div>
          <div className={`info-value ${isEmptyValue(data.H_location) ? 'empty' : ''}`}>
            {formatValue(data.H_location)}
          </div>
        </div>

        {/* Request Nature */}
        <div className="info-item">
          <div className="info-label">Nature of Request (I)</div>
          <div className={`info-value ${isEmptyValue(data.I_nature_of_request) ? 'empty' : ''}`}>
            {formatValue(data.I_nature_of_request)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">Subject Matter (J)</div>
          <div className={`info-value ${isEmptyValue(data.J_subject_matter) ? 'empty' : ''}`}>
            {formatValue(data.J_subject_matter)}
          </div>
        </div>

        {/* Important Dates */}
        <div className="info-item">
          <div className="info-label">
            <Calendar size={12} style={{ display: 'inline', marginRight: '4px' }} />
            10-Day Rule Due Date (K)
          </div>
          <div className={`info-value ${isEmptyValue(data.K_10day_rule_due_date) ? 'empty' : ''}`}>
            {formatValue(data.K_10day_rule_due_date)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">ICC Interim Reply Due Date (L)</div>
          <div className={`info-value ${isEmptyValue(data.L_icc_interim_due) ? 'empty' : ''}`}>
            {formatValue(data.L_icc_interim_due)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">ICC Final Reply Due Date (M)</div>
          <div className={`info-value ${isEmptyValue(data.M_icc_final_due) ? 'empty' : ''}`}>
            {formatValue(data.M_icc_final_due)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">Works Completion Due Date (N)</div>
          <div className={`info-value ${isEmptyValue(data.N_works_completion_due) ? 'empty' : ''}`}>
            {formatValue(data.N_works_completion_due)}
          </div>
        </div>

        {/* Other Information */}
        <div className="info-item">
          <div className="info-label">Fax to Contractor Date (O1)</div>
          <div className={`info-value ${isEmptyValue(data.O1_fax_to_contractor) ? 'empty' : ''}`}>
            {formatValue(data.O1_fax_to_contractor)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">Email Send Time (O2)</div>
          <div className={`info-value ${isEmptyValue(data.O2_email_send_time) ? 'empty' : ''}`}>
            {formatValue(data.O2_email_send_time)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">Fax Pages (P)</div>
          <div className={`info-value ${isEmptyValue(data.P_fax_pages) ? 'empty' : ''}`}>
            {formatValue(data.P_fax_pages)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">Case Details (Q)</div>
          <div className={`info-value ${isEmptyValue(data.Q_case_details) ? 'empty' : ''}`}>
            {formatValue(data.Q_case_details)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExtractedInfoDisplay;