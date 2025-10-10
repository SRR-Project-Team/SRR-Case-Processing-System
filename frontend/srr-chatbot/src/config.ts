// Application configuration
export const config = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8001',
  version: process.env.REACT_APP_VERSION || '1.0.0',
  maxFileSize: 10 * 1024 * 1024, // 10MB
  supportedFileTypes: ['text/plain', 'application/pdf'],
  apiTimeout: 120000, // 120 seconds (2 minutes) - Reserved more time for RCC OCR processing
};
