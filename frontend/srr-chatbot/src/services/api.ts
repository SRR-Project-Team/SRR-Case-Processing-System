import axios from 'axios';
import { ApiResponse, QueryRequest } from '../types';

// 批量处理响应类型
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

// API基础配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120秒超时 (2分钟) - 为RCC OCR处理预留更多时间
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// 单文件处理API
export const processFile = async (file: File): Promise<ApiResponse> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/api/process-srr-file', formData);
    
    // 转换后端响应格式到前端期望格式
    const backendResponse = response.data;
    return {
      filename: backendResponse.filename,
      status: backendResponse.status,
      message: backendResponse.message,
      data: backendResponse.structured_data, // 将 structured_data 映射到 data
      error: backendResponse.error,
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || '文件处理失败');
    }
    throw new Error('网络连接失败');
  }
};

// 多文件批量处理API
export const processMultipleFiles = async (files: File[]): Promise<BatchProcessingResponse> => {
  try {
    const formData = new FormData();
    
    // 添加所有文件到FormData
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await apiClient.post('/api/process-multiple-files', formData);
    
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || '批量文件处理失败');
    }
    throw new Error('网络连接失败');
  }
};

// 健康检查API
export const healthCheck = async (): Promise<{ status: string; message: string }> => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    throw new Error('API服务不可用');
  }
};

// 查询案件信息API (模拟实现)
export const queryCase = async (request: QueryRequest): Promise<string> => {
  try {
    // 这里可以实现实际的查询逻辑
    // 目前返回模拟响应
    const { query, context } = request;
    
    if (!context) {
      return '请先上传文件以获取案件信息。';
    }

    // 简单的查询匹配逻辑
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('案件') || lowerQuery.includes('case')) {
      return `案件编号: ${context.C_case_number || '未知'}\n来源: ${context.B_source || '未知'}`;
    }
    
    if (lowerQuery.includes('日期') || lowerQuery.includes('date')) {
      return `接收日期: ${context.A_date_received || '未知'}\n10天规则截止日期: ${context.K_10day_rule_due_date || '未知'}`;
    }
    
    if (lowerQuery.includes('联系') || lowerQuery.includes('contact')) {
      return `来电人: ${context.E_caller_name || '未知'}\n联系电话: ${context.F_contact_no || '未知'}`;
    }
    
    if (lowerQuery.includes('斜坡') || lowerQuery.includes('slope')) {
      return `斜坡编号: ${context.G_slope_no || '未知'}\n位置: ${context.H_location || '未知'}`;
    }
    
    if (lowerQuery.includes('性质') || lowerQuery.includes('nature')) {
      return `请求性质: ${context.I_nature_of_request || '未知'}`;
    }
    
    // 默认返回案件概要
    return `案件概要:
• 案件编号: ${context.C_case_number || '未知'}
• 来源: ${context.B_source || '未知'}
• 接收日期: ${context.A_date_received || '未知'}
• 来电人: ${context.E_caller_name || '未知'}
• 斜坡编号: ${context.G_slope_no || '未知'}
• 请求性质: ${context.I_nature_of_request || '未知'}`;
    
  } catch (error) {
    throw new Error('查询失败，请稍后重试');
  }
};

const apiService = {
  processFile,
  processMultipleFiles,
  healthCheck,
  queryCase,
};

export default apiService;
