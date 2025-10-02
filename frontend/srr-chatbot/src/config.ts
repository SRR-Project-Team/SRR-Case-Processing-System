// 应用配置
export const config = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8001',
  version: process.env.REACT_APP_VERSION || '1.0.0',
  maxFileSize: 10 * 1024 * 1024, // 10MB
  supportedFileTypes: ['text/plain', 'application/pdf'],
  apiTimeout: 120000, // 120秒 (2分钟) - 为RCC OCR处理预留更多时间
};
