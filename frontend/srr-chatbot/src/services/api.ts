import axios from 'axios';
import { ApiResponse, QueryRequest } from '../types';

// Batch processing response type
export interface BatchProcessingResponse {
  total_files: number;
  successful: number;
  failed: number;
  results: Array<{
    filename: string;
    status: 'success' | 'error';
    message: string;
    structured_data?: any;
  }>;
}

// API base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds timeout (2 minutes) - reserved for RCC OCR processing
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// Single file processing API
export const processFile = async (file: File): Promise<ApiResponse> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/api/process-srr-file', formData);
    
    // Convert backend response format to frontend expected format
    const backendResponse = response.data;
    return {
      filename: backendResponse.filename,
      status: backendResponse.status,
      message: backendResponse.message,
      data: backendResponse.structured_data, // Map structured_data to data
      error: backendResponse.error,
      summary: backendResponse.summary
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'File processing failed');
    }
    throw new Error('Network connection failed');
  }
};

// Multi-file batch processing API
export const processMultipleFiles = async (files: File[]): Promise<BatchProcessingResponse> => {
  try {
    const formData = new FormData();
    
    // Add all files to FormData
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await apiClient.post('/api/process-multiple-files', formData);
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Batch file processing failed');
    }
    throw new Error('Network connection failed');
  }
};

// Health check API
export const healthCheck = async (): Promise<{ status: string; message: string }> => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    throw new Error('API service unavailable');
  }
};

// Query case information API (simulated implementation)
export const queryCase = async (request: QueryRequest): Promise<string> => {
  try {
    // Here you can implement actual query logic
    // Currently returns simulated response
    const { query, context } = request;
    
    if (!context) {
      return 'Please upload files first to get case information.';
    }

    // Simple query matching logic
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('case') || lowerQuery.includes('案件')) {
      return `Case Number: ${context.C_case_number || 'Unknown'}\nSource: ${context.B_source || 'Unknown'}`;
    }
    
    if (lowerQuery.includes('date') || lowerQuery.includes('日期')) {
      return `Date Received: ${context.A_date_received || 'Unknown'}\n10-Day Rule Due Date: ${context.K_10day_rule_due_date || 'Unknown'}`;
    }
    
    if (lowerQuery.includes('contact') || lowerQuery.includes('联系')) {
      return `Caller: ${context.E_caller_name || 'Unknown'}\nContact Number: ${context.F_contact_no || 'Unknown'}`;
    }
    
    if (lowerQuery.includes('slope') || lowerQuery.includes('斜坡')) {
      return `Slope Number: ${context.G_slope_no || 'Unknown'}\nLocation: ${context.H_location || 'Unknown'}`;
    }
    
    if (lowerQuery.includes('nature') || lowerQuery.includes('性质')) {
      return `Nature of Request: ${context.I_nature_of_request || 'Unknown'}`;
    }
    
    // Default return case summary
    return `Case Summary:
• Case Number: ${context.C_case_number || 'Unknown'}
• Source: ${context.B_source || 'Unknown'}
• Date Received: ${context.A_date_received || 'Unknown'}
• Caller: ${context.E_caller_name || 'Unknown'}
• Slope Number: ${context.G_slope_no || 'Unknown'}
• Nature of Request: ${context.I_nature_of_request || 'Unknown'}`;
    
  } catch (error) {
    throw new Error('Query failed, please try again later');
  }
};

const apiService = {
  processFile,
  processMultipleFiles,
  healthCheck,
  queryCase,
};

export default apiService;