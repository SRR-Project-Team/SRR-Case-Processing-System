import axios from 'axios';
import { ApiResponse, QueryRequest } from '../types';

// Batch processing response type
export interface BatchProcessingResponse {
  total_files: number;
  successful: number;
  failed: number;
  skipped: number;  // 添加此字段
  results: Array<{
    case_id: string;
    main_file: string;
    email_file?: string | null;
    status: 'success' | 'error' | 'skipped';  // 添加 'skipped'
    message: string;
    structured_data?: any;  // 仅在 success 时存在
  }>;
}

// API base configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds timeout (2 minutes) - reserved for RCC OCR processing
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
      summary: backendResponse.summary,
      raw_content: backendResponse.raw_content // Include original file content for chat
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
    // context: extracted data raw_content: raw content of the file
    const { query, context, raw_content } = request;
    
    // Allow chat even without uploaded files - backend can handle general queries
    // and retrieve information from historical database
    const response = await axios.post(`${API_BASE_URL}/api/chat`, {
      query,
      context: context || {},
      raw_content: raw_content || ''
    }, {
      timeout: 30000 // 30 seconds timeout
    });

    // Ensure we always return a string (handle edge cases)
    const data = response.data;
    
    // If backend returns an object (shouldn't happen now, but handle gracefully)
    if (typeof data === 'object' && data !== null) {
      if ('message' in data) {
        return String(data.message);
      }
      return JSON.stringify(data);
    }
    
    // If data is null or undefined
    if (!data) {
      return 'No response received from the server.';
    }
    
    // Normal case: return as string
    return String(data);

    // Simple query matching logic
    // const lowerQuery = query.toLowerCase();
    
    // if (lowerQuery.includes('case')) {
    //   return `Case Number: ${context.C_case_number || 'Unknown'}\nSource: ${context.B_source || 'Unknown'}`;
    // }
    
    // if (lowerQuery.includes('date')) {
    //   return `Date Received: ${context.A_date_received || 'Unknown'}\n10-Day Rule Due Date: ${context.K_10day_rule_due_date || 'Unknown'}`;
    // }
    
    // if (lowerQuery.includes('contact')) {
    //   return `Caller: ${context.E_caller_name || 'Unknown'}\nContact Number: ${context.F_contact_no || 'Unknown'}`;
    // }
    
    // if (lowerQuery.includes('slope')) {
    //   return `Slope Number: ${context.G_slope_no || 'Unknown'}\nLocation: ${context.H_location || 'Unknown'}`;
    // }
    
    // if (lowerQuery.includes('nature')) {
    //   return `Nature of Request: ${context.I_nature_of_request || 'Unknown'}`;
    // }
    
    // Default return case summary
//     return `Case Summary:
// • Case Number: ${context.C_case_number || 'Unknown'}
// • Source: ${context.B_source || 'Unknown'}
// • Date Received: ${context.A_date_received || 'Unknown'}
// • Caller: ${context.E_caller_name || 'Unknown'}
// • Slope Number: ${context.G_slope_no || 'Unknown'}
// • Nature of Request: ${context.I_nature_of_request || 'Unknown'}`;
    
  } catch (error) {
    throw new Error('Query failed, please try again later');
  }
};

// Find similar cases API
export const findSimilarCases = async (caseData: any, limit: number = 10, minSimilarity: number = 0.3): Promise<any> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/find-similar-cases`, {
      ...caseData,
      limit,
      min_similarity: minSimilarity
    }, {
      timeout: 30000 // 30 seconds timeout
    });
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to find similar cases');
    }
    throw new Error('Network connection failed');
  }
};

// Get case statistics API
export const getCaseStatistics = async (filters: {
  location?: string;
  slope_no?: string;
  caller_name?: string;
}): Promise<any> => {
  try {
    const params = new URLSearchParams();
    if (filters.location) params.append('location', filters.location);
    if (filters.slope_no) params.append('slope_no', filters.slope_no);
    if (filters.caller_name) params.append('caller_name', filters.caller_name);
    
    const response = await axios.get(`${API_BASE_URL}/api/case-statistics?${params.toString()}`, {
      timeout: 30000
    });
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get statistics');
    }
    throw new Error('Network connection failed');
  }
};

const apiService = {
  processFile,
  processMultipleFiles,
  healthCheck,
  queryCase,
  findSimilarCases,
  getCaseStatistics,
};

export default apiService;