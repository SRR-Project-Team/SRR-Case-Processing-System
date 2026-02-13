import axios from 'axios';
import { ApiResponse, QueryRequest, RAGFile, RAGFileDetails, FilePreview, RAGFileUploadResponse } from '../types';

// Authentication related types
export interface User {
  phone_number: string;
  full_name: string;
  department: string;
  role: string;
  email: string;
}

export interface LoginRequest {
  phone_number: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  phone_number: string;
  password: string;
  full_name: string;
  department?: string;
  role?: string;
  email?: string;
}

export interface ChatMessageRequest {
  session_id: string;
  message_type: string;
  content: string;
  case_id?: number;
  file_info?: any;
}

export interface ChatMessage {
  id: number;
  user_phone: string;
  session_id: string;
  message_type: string;
  content: string;
  case_id?: number;
  file_info?: any;
  created_at: string;
}

export interface Session {
  session_id: string;
  message_count: number;
  last_message_time: string;
}

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

// Stage 1 of token hardening: centralize token-clearing behavior.
// Stage 2 (planned): migrate to HttpOnly secure cookies and remove localStorage token usage.
const clearAuthState = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.dispatchEvent(new Event('auth:unauthorized'));
};

// Request interceptor: automatically add token to headers
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: handle 401 unauthorized errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthState();
    }
    return Promise.reject(error);
  }
);

export interface ProcessFileStreamCallbacks {
  onExtracted?: (data: { structured_data: any; case_id: number | null; raw_content?: string }) => void;
  onSummaryChunk?: (text: string) => void;
  onSummaryFull?: (summary: string, success: boolean) => void;
  onSimilarCases?: (similar_cases: any[]) => void;
  onDone?: (result: { filename: string; case_id: number | null }) => void;
  onDuplicate?: (data: { filename: string; message: string; structured_data: any; case_id: number }) => void;
  onError?: (message: string) => void;
}

const API_BASE_URL_EXPORT = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const attachAuthHeader = (headers: Record<string, string> = {}): Record<string, string> => {
  const token = localStorage.getItem('token');
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
};

const fetchWithAuth = async (input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> => {
  const headers: Record<string, string> = attachAuthHeader((init.headers as Record<string, string>) || {});
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401) {
    clearAuthState();
  }
  return response;
};

export const processFileStream = async (
  file: File,
  options?: { forceReprocess?: boolean },
  callbacks?: ProcessFileStreamCallbacks
): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);
  if (options?.forceReprocess) {
    formData.append('force_reprocess', 'true');
  }
  const res = await fetchWithAuth(`${API_BASE_URL_EXPORT}/api/process-srr-file`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    callbacks?.onError?.(text || `Request failed: ${res.status}`);
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    callbacks?.onError?.('No response body');
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = '';

  const parseLine = (line: string): void => {
    if (line.startsWith('event: ')) {
      currentEvent = line.slice(7).trim();
      return;
    }
    if (line.startsWith('data: ')) {
      const payload = line.slice(6);
      try {
        const data = JSON.parse(payload);
        switch (currentEvent) {
          case 'duplicate':
            callbacks?.onDuplicate?.({
              filename: data.filename,
              message: data.message,
              structured_data: data.structured_data,
              case_id: data.case_id,
            });
            break;
          case 'extracted':
            callbacks?.onExtracted?.({
              structured_data: data.structured_data,
              case_id: data.case_id ?? null,
              raw_content: data.raw_content,
            });
            break;
          case 'summary':
            if (data.summary != null) callbacks?.onSummaryFull?.(data.summary, data.success !== false);
            break;
          case 'summary_chunk':
            if (typeof data.text === 'string') callbacks?.onSummaryChunk?.(data.text);
            break;
          case 'summary_end':
            if (data.summary != null) callbacks?.onSummaryFull?.(data.summary, data.success !== false);
            else if (data.error) callbacks?.onSummaryFull?.('', false);
            break;
          case 'similar_cases':
            callbacks?.onSimilarCases?.(data.similar_cases ?? []);
            break;
          case 'done':
            callbacks?.onDone?.({ filename: data.filename, case_id: data.case_id ?? null });
            break;
          case 'error':
            callbacks?.onError?.(data.error ?? 'Unknown error');
            break;
          default:
            break;
        }
      } catch {
        // ignore parse errors for non-JSON lines
      }
      currentEvent = '';
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      parseLine(line);
    }
  }
  if (buffer) {
    for (const line of buffer.split('\n')) {
      parseLine(line);
    }
  }
};


// Multi-file batch processing API (SSE stream)
export interface ProcessMultipleFilesStreamCallbacks {
  onFileResult?: (result: BatchProcessingResponse['results'][0]) => void;
  onBatchDone?: (summary: { total_files: number; successful: number; failed: number; skipped: number }) => void;
  onError?: (message: string) => void;
}

export const processMultipleFilesStream = async (
  files: File[],
  callbacks?: ProcessMultipleFilesStreamCallbacks
): Promise<BatchProcessingResponse> => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const res = await fetchWithAuth(`${API_BASE_URL_EXPORT}/api/process-multiple-files/stream`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    const msg = text || `Request failed: ${res.status}`;
    callbacks?.onError?.(msg);
    throw new Error(msg);
  }

  const reader = res.body?.getReader();
  if (!reader) {
    callbacks?.onError?.('No response body');
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = '';
  const results: BatchProcessingResponse['results'] = [];
  let batchDone: BatchProcessingResponse | null = null;
  let streamError: string | null = null;

  const parseLine = (line: string): void => {
    if (line.startsWith('event: ')) {
      currentEvent = line.slice(7).trim();
      return;
    }
    if (line.startsWith('data: ')) {
      const payload = line.slice(6);
      try {
        const data = JSON.parse(payload);
        if (currentEvent === 'file_result') {
          results.push(data);
          callbacks?.onFileResult?.(data);
        } else if (currentEvent === 'batch_done') {
          batchDone = {
            total_files: data.total_files ?? 0,
            successful: data.successful ?? 0,
            failed: data.failed ?? 0,
            skipped: data.skipped ?? 0,
            results: data.results ?? results,
          };
          callbacks?.onBatchDone?.({
            total_files: batchDone.total_files,
            successful: batchDone.successful,
            failed: batchDone.failed,
            skipped: batchDone.skipped,
          });
        } else if (currentEvent === 'error') {
          streamError = data.error ?? 'Unknown error';
          callbacks?.onError?.(data.error ?? 'Unknown error');
        }
      } catch (_) {
        // ignore JSON parse errors for non-event lines
      }
      currentEvent = '';
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) parseLine(line);
  }
  if (buffer) {
    for (const line of buffer.split('\n')) parseLine(line);
  }

  if (streamError) throw new Error(streamError);
  if (batchDone) return batchDone;
  return {
    total_files: files.length,
    successful: results.filter((r) => r.status === 'success').length,
    failed: results.filter((r) => r.status === 'error').length,
    skipped: results.filter((r) => r.status === 'skipped').length,
    results,
  };
};

// Legacy non-streaming batch (uses stream under the hood, for compatibility)
export const processMultipleFiles = async (files: File[]): Promise<BatchProcessingResponse> => {
  try {
    return await processMultipleFilesStream(files);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Batch file processing failed');
    }
    throw new Error(error instanceof Error ? error.message : 'Network connection failed');
  }
};

export interface LlmModelsResponse {
  openai: string[];
  ollama: string[];
}

export const getLlmModels = async (): Promise<LlmModelsResponse> => {
  const res = await fetchWithAuth(`${API_BASE_URL}/api/llm-models`);
  if (!res.ok) throw new Error(`Failed to fetch LLM models: ${res.status}`);
  return res.json();
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

/**
 * Stream chat response via SSE. Calls onChunk for each text chunk, returns full text.
 */
export const queryCaseStream = async (
  request: QueryRequest,
  onChunk: (text: string) => void
): Promise<string> => {
  const { query, context, raw_content, provider, model } = request;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  attachAuthHeader(headers);

  const body: Record<string, unknown> = {
    query,
    context: context || {},
    raw_content: raw_content || '',
  };
  if (provider != null) body.provider = provider;
  if (model != null) body.model = model;

  const res = await fetchWithAuth(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(errBody || `Request failed: ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';
  let fullText = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const payload = line.slice(6);
        if (payload === '[DONE]') continue;
        try {
          const data = JSON.parse(payload);
          if (data.error) throw new Error(data.error);
          if (typeof data.text === 'string') {
            fullText += data.text;
            onChunk(data.text);
          }
        } catch (e) {
          if (e instanceof Error && e.message !== 'Unexpected end of JSON input') throw e;
        }
      }
    }
  }
  if (buffer.startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.slice(6));
      if (data.error) throw new Error(data.error);
      if (typeof data.text === 'string') {
        fullText += data.text;
        onChunk(data.text);
      }
    } catch {
      /* ignore trailing parse */
    }
  }
  return fullText;
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

// Reply draft generation API
export const generateReplyDraft = async (request: {
  case_id: number;
  reply_type: string;
  conversation_id?: number;
  user_message?: string;
  is_initial: boolean;
  skip_questions?: boolean;
}): Promise<{
  status: string;
  conversation_id: number;
  message: string;
  is_question: boolean;
  draft_reply?: string;
  language: string;
}> => {
  try {
    const response = await apiClient.post('/api/generate-reply-draft', request, {
      timeout: 60000 // 60 seconds for LLM processing
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to generate reply draft');
    }
    throw new Error('Network connection failed');
  }
};

/** Stream reply draft generation via SSE. Use when skip_questions=true or generating from user answer. */
export const generateReplyDraftStream = async (
  request: {
    case_id: number;
    reply_type: string;
    conversation_id?: number;
    user_message?: string;
    is_initial: boolean;
    skip_questions?: boolean;
  },
  onChunk: (text: string) => void
): Promise<{ conversation_id: number; fullText: string }> => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  attachAuthHeader(headers);
  const res = await fetchWithAuth(`${API_BASE_URL}/api/generate-reply-draft/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(errBody || `Request failed: ${res.status}`);
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error('No response body');
  const decoder = new TextDecoder();
  let buffer = '';
  let fullText = '';
  let conversationId = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const payload = line.slice(6);
      try {
        const data = JSON.parse(payload);
        if (data.type === 'meta' && data.conversation_id != null) conversationId = data.conversation_id;
        else if (data.type === 'text' && typeof data.text === 'string') {
          fullText += data.text;
          onChunk(data.text);
        } else if (data.type === 'error') throw new Error(data.error || 'Stream error');
        else if (data.type === 'done' && data.conversation_id != null) conversationId = data.conversation_id;
      } catch (e) {
        if (e instanceof Error && e.message !== 'Unexpected end of JSON input') throw e;
      }
    }
  }
  if (buffer.startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.slice(6));
      if (data.type === 'text' && typeof data.text === 'string') {
        fullText += data.text;
        onChunk(data.text);
      } else if (data.type === 'error') throw new Error(data.error || 'Stream error');
    } catch {
      /* ignore */
    }
  }
  return { conversation_id: conversationId, fullText };
};

// Get conversation history API
export const getConversation = async (conversationId: number): Promise<{
  status: string;
  conversation: any;
}> => {
  try {
    const response = await apiClient.get(`/api/conversation/${conversationId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get conversation');
    }
    throw new Error('Network connection failed');
  }
};

// Delete draft reply for a conversation (clears draft_reply on server)
export const deleteConversationDraft = async (conversationId: number): Promise<void> => {
  try {
    await apiClient.delete(`/api/conversation/${conversationId}/draft`);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to delete draft');
    }
    throw new Error('Network connection failed');
  }
};

// ============== RAG Knowledge Base File Management APIs ==============

// Upload RAG file
export const uploadRAGFile = async (
  file: File,
  onProgress?: (progress: number) => void
): Promise<RAGFile> => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<RAGFileUploadResponse>('/api/rag-files/upload', formData, {
      timeout: 60000, // 60s enough (processing is background; 202 returns quickly)
      validateStatus: (status) => (status >= 200 && status < 300) || status === 202,
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      }
    });

    // 200 or 202: success (202 = accepted, processing in background)
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'File upload failed');
    }
    throw new Error('Network connection failed');
  }
};

// Get all RAG files
export const getRAGFiles = async (): Promise<RAGFile[]> => {
  try {
    const response = await apiClient.get<{ status: string; data: RAGFile[] }>('/api/rag-files');
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get files');
    }
    throw new Error('Network connection failed');
  }
};

// Get RAG file details
export const getRAGFileDetails = async (fileId: number): Promise<RAGFileDetails> => {
  try {
    const response = await apiClient.get<{ status: string; data: RAGFileDetails }>(
      `/api/rag-files/${fileId}`
    );
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get file details');
    }
    throw new Error('Network connection failed');
  }
};

// Download RAG file
export const downloadRAGFile = async (fileId: number, filename: string): Promise<void> => {
  try {
    const response = await apiClient.get(`/api/rag-files/${fileId}/download`, {
      responseType: 'blob'
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error('File download failed');
    }
    throw new Error('Network connection failed');
  }
};

// Delete RAG file
export const deleteRAGFile = async (fileId: number): Promise<void> => {
  try {
    await apiClient.delete(`/api/rag-files/${fileId}`);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to delete file');
    }
    throw new Error('Network connection failed');
  }
};

// Get RAG file preview (optional: full content or paginated via offset/limit)
export const getRAGFilePreview = async (
  fileId: number,
  options?: { full?: boolean; offset?: number; limit?: number }
): Promise<FilePreview> => {
  try {
    const params = new URLSearchParams();
    if (options?.full) params.set('full', 'true');
    if (options?.offset != null) params.set('offset', String(options.offset));
    if (options?.limit != null) params.set('limit', String(options.limit));
    const query = params.toString();
    const url = query ? `/api/rag-files/${fileId}/preview?${query}` : `/api/rag-files/${fileId}/preview`;
    const response = await apiClient.get<{ status: string; data: FilePreview }>(url);
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get file preview');
    }
    throw new Error('Network connection failed');
  }
};

// Get all cases (for CaseFilesPanel)
export const getCases = async (limit: number = 100, offset: number = 0): Promise<any[]> => {
  try {
    const response = await apiClient.get(`/api/cases?limit=${limit}&offset=${offset}`);
    return response.data.cases || [];
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get cases');
    }
    throw new Error('Network connection failed');
  }
};

// Get single case by ID (full extracted data for query / draft)
export const getCase = async (caseId: number): Promise<any> => {
  try {
    const response = await apiClient.get(`/api/cases/${caseId}`);
    if (response.data?.error) {
      throw new Error(response.data.error);
    }
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get case');
    }
    throw new Error('Network connection failed');
  }
};

// Get case details (basic info, processing, conversations, attachments)
export const getCaseDetails = async (caseId: number): Promise<{
  case: any;
  conversations: any[];
  attachments: { name: string; type: string; note: string }[];
}> => {
  try {
    const response = await apiClient.get(`/api/cases/${caseId}/details`);
    if (response.data?.error) {
      throw new Error(response.data.error);
    }
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get case details');
    }
    throw new Error('Network connection failed');
  }
};

// ============== Authentication APIs ==============

/**
 * User login
 */
export const login = async (phone: string, password: string): Promise<LoginResponse> => {
  try {
    const formData = new FormData();
    formData.append('username', phone);
    formData.append('password', password);

    const response = await apiClient.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 20000, // 20s so UI does not hang when backend is down
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const msg = error.code === 'ECONNABORTED'
        ? 'Connection timed out. Is the backend running?'
        : (error.response?.data?.detail || error.message || 'Login failed');
      throw new Error(msg);
    }
    throw new Error('Network connection failed');
  }
};

/**
 * User registration
 */
export const register = async (userData: RegisterRequest): Promise<User> => {
  try {
    const response = await apiClient.post('/api/auth/register', userData);
    return response.data.user;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Registration failed');
    }
    throw new Error('Network connection failed');
  }
};

/**
 * Get current user info
 */
export const getCurrentUser = async (): Promise<User> => {
  try {
    const response = await apiClient.get('/api/auth/me');
    return response.data.user;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || error.message || 'Failed to get user info');
    }
    throw new Error('Network connection failed');
  }
};

/**
 * User logout
 */
export const logout = async (): Promise<void> => {
  try {
    await apiClient.post('/api/auth/logout');
  } catch (error) {
    // Logout errors are not critical, just log them
    console.error('Logout API call failed:', error);
  }
};

// ============== Chat History APIs ==============

/**
 * Get chat history
 */
export const getChatHistory = async (sessionId?: string, limit: number = 100): Promise<ChatMessage[]> => {
  try {
    const params: any = { limit };
    if (sessionId) {
      params.session_id = sessionId;
    }

    const response = await apiClient.get('/api/chat-history', { params });
    return response.data.messages || [];
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get chat history');
    }
    throw new Error('Network connection failed');
  }
};

/**
 * Create new session
 */
export const createSession = async (title?: string): Promise<any> => {
  try {
    const response = await apiClient.post('/api/chat-sessions', { title });
    return response.data.session;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to create session');
    }
    throw new Error('Network connection failed');
  }
};

/**
 * Delete session
 */
export const deleteSession = async (sessionId: string): Promise<void> => {
  try {
    await apiClient.delete(`/api/chat-sessions/${sessionId}`);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to delete session');
    }
    throw new Error('Network connection failed');
  }
};

/**
 * Save chat message
 */
export const saveChatMessage = async (message: ChatMessageRequest): Promise<number> => {
  try {
    const response = await apiClient.post('/api/chat-history', message);
    return response.data.message_id;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to save chat message');
    }
    throw new Error('Network connection failed');
  }
};

/**
 * Get user sessions
 */
export const getUserSessions = async (): Promise<Session[]> => {
  try {
    const response = await apiClient.get('/api/chat-sessions');
    return response.data.sessions || [];
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to get sessions');
    }
    throw new Error('Network connection failed');
  }
};

/**
 * Delete a chat session (removes all messages in that session for current user)
 */
export const deleteChatSession = async (sessionId: string): Promise<void> => {
  try {
    await apiClient.delete(`/api/chat-sessions/${encodeURIComponent(sessionId)}`);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.message || error.message || 'Failed to delete session');
    }
    throw new Error('Network connection failed');
  }
};

const apiService = {
  processFileStream,
  processMultipleFiles,
  healthCheck,
  findSimilarCases,
  getCaseStatistics,
  generateReplyDraft,
  getConversation,
  uploadRAGFile,
  getRAGFiles,
  getRAGFileDetails,
  downloadRAGFile,
  deleteRAGFile,
  getRAGFilePreview,
  getCases,
  login,
  register,
  getCurrentUser,
  logout,
  getChatHistory,
  saveChatMessage,
  getUserSessions,
  deleteChatSession,
};

export default apiService;