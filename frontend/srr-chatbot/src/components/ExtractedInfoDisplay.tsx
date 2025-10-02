import React from 'react';
import { FileText, Calendar, User, MapPin, Phone, AlertTriangle } from 'lucide-react';
import { ExtractedData } from '../types';

interface ExtractedInfoDisplayProps {
  data: ExtractedData;
}

const ExtractedInfoDisplay: React.FC<ExtractedInfoDisplayProps> = ({ data }) => {
  const formatValue = (value: string | undefined | null) => {
    return value && value.trim() ? value : '未提供';
  };

  const isEmptyValue = (value: string | undefined | null) => {
    return !value || !value.trim();
  };

  return (
    <div className="extracted-info">
      <h3>
        <FileText size={16} />
        提取的案件信息
      </h3>
      
      <div className="info-grid">
        {/* 基本信息 */}
        <div className="info-item">
          <div className="info-label">
            <Calendar size={12} style={{ display: 'inline', marginRight: '4px' }} />
            接收日期 (A)
          </div>
          <div className={`info-value ${isEmptyValue(data.A_date_received) ? 'empty' : ''}`}>
            {formatValue(data.A_date_received)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">来源 (B)</div>
          <div className={`info-value ${isEmptyValue(data.B_source) ? 'empty' : ''}`}>
            {formatValue(data.B_source)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">案件编号 (C)</div>
          <div className={`info-value ${isEmptyValue(data.C_case_number) ? 'empty' : ''}`}>
            {formatValue(data.C_case_number)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">案件类型 (D)</div>
          <div className={`info-value ${isEmptyValue(data.D_type) ? 'empty' : ''}`}>
            {formatValue(data.D_type)}
          </div>
        </div>

        {/* 联系信息 */}
        <div className="info-item">
          <div className="info-label">
            <User size={12} style={{ display: 'inline', marginRight: '4px' }} />
            来电人姓名 (E)
          </div>
          <div className={`info-value ${isEmptyValue(data.E_caller_name) ? 'empty' : ''}`}>
            {formatValue(data.E_caller_name)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">
            <Phone size={12} style={{ display: 'inline', marginRight: '4px' }} />
            联系电话 (F)
          </div>
          <div className={`info-value ${isEmptyValue(data.F_contact_no) ? 'empty' : ''}`}>
            {formatValue(data.F_contact_no)}
          </div>
        </div>

        {/* 斜坡信息 */}
        <div className="info-item">
          <div className="info-label">
            <AlertTriangle size={12} style={{ display: 'inline', marginRight: '4px' }} />
            斜坡编号 (G)
          </div>
          <div className={`info-value ${isEmptyValue(data.G_slope_no) ? 'empty' : ''}`}>
            {formatValue(data.G_slope_no)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">
            <MapPin size={12} style={{ display: 'inline', marginRight: '4px' }} />
            位置 (H)
          </div>
          <div className={`info-value ${isEmptyValue(data.H_location) ? 'empty' : ''}`}>
            {formatValue(data.H_location)}
          </div>
        </div>

        {/* 请求性质 */}
        <div className="info-item">
          <div className="info-label">请求性质 (I)</div>
          <div className={`info-value ${isEmptyValue(data.I_nature_of_request) ? 'empty' : ''}`}>
            {formatValue(data.I_nature_of_request)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">事项主题 (J)</div>
          <div className={`info-value ${isEmptyValue(data.J_subject_matter) ? 'empty' : ''}`}>
            {formatValue(data.J_subject_matter)}
          </div>
        </div>

        {/* 重要日期 */}
        <div className="info-item">
          <div className="info-label">
            <Calendar size={12} style={{ display: 'inline', marginRight: '4px' }} />
            10天规则截止日期 (K)
          </div>
          <div className={`info-value ${isEmptyValue(data.K_10day_rule_due_date) ? 'empty' : ''}`}>
            {formatValue(data.K_10day_rule_due_date)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">ICC临时回复截止日期 (L)</div>
          <div className={`info-value ${isEmptyValue(data.L_icc_interim_due) ? 'empty' : ''}`}>
            {formatValue(data.L_icc_interim_due)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">ICC最终回复截止日期 (M)</div>
          <div className={`info-value ${isEmptyValue(data.M_icc_final_due) ? 'empty' : ''}`}>
            {formatValue(data.M_icc_final_due)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">工程完成截止日期 (N)</div>
          <div className={`info-value ${isEmptyValue(data.N_works_completion_due) ? 'empty' : ''}`}>
            {formatValue(data.N_works_completion_due)}
          </div>
        </div>

        {/* 其他信息 */}
        <div className="info-item">
          <div className="info-label">发给承包商的传真日期 (O1)</div>
          <div className={`info-value ${isEmptyValue(data.O1_fax_to_contractor) ? 'empty' : ''}`}>
            {formatValue(data.O1_fax_to_contractor)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">邮件发送时间 (O2)</div>
          <div className={`info-value ${isEmptyValue(data.O2_email_send_time) ? 'empty' : ''}`}>
            {formatValue(data.O2_email_send_time)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">传真页数 (P)</div>
          <div className={`info-value ${isEmptyValue(data.P_fax_pages) ? 'empty' : ''}`}>
            {formatValue(data.P_fax_pages)}
          </div>
        </div>

        <div className="info-item">
          <div className="info-label">案件详情 (Q)</div>
          <div className={`info-value ${isEmptyValue(data.Q_case_details) ? 'empty' : ''}`}>
            {formatValue(data.Q_case_details)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExtractedInfoDisplay;
