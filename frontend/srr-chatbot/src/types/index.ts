// 消息类型
export interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  fileInfo?: FileInfo;
}

// 文件信息
export interface FileInfo {
  name: string;
  size: number;
  type: string;
  summary?: FileSummary;  // 新增总结字段
}

// 提取的案件数据
export interface ExtractedData {
  A_date_received: string;
  B_source: string;
  C_case_number: string;
  D_type: string;
  E_caller_name: string;
  F_contact_no: string;
  G_slope_no: string;
  H_location: string;
  I_nature_of_request: string;
  J_subject_matter: string;
  K_10day_rule_due_date: string;
  L_icc_interim_due: string;
  M_icc_final_due: string;
  N_works_completion_due: string;
  O1_fax_to_contractor: string;
  O2_email_send_time: string;
  P_fax_pages: string;
  Q_case_details: string;
}

// 添加总结相关类型
export interface FileSummary {
  success: boolean;
  summary?: string;
  filename?: string;
  source?: string;
  error?: string;
}

// API响应类型
export interface ApiResponse {
  filename: string;
  status: 'success' | 'error';
  message: string;
  data?: ExtractedData;
  error?: string;
  summary?: FileSummary;  // 新增总结字段
}

// 聊天状态
export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  extractedData: ExtractedData | null;
  currentFile: FileInfo | null;
}

// 查询类型
export interface QueryRequest {
  query: string;
  context?: ExtractedData;
}