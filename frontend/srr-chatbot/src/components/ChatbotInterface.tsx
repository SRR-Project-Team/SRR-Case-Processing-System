import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, FileText, Cpu, Trash2 } from 'lucide-react';
import { Message, FileSummary, ExtractedData } from '../types';
import { useChat } from '../contexts/ChatContext';
import { processFileStream, processMultipleFiles, queryCaseStream, findSimilarCases, getCaseStatistics, generateReplyDraft, generateReplyDraftStream, deleteConversationDraft, BatchProcessingResponse, getLlmModels } from '../services/api';
import logoImage from '../images/system_logo.png'; 
import universityLogo from '../images/university_logo.png';
import FileUploadModal from './FileUploadModal';
import FileInfoModal from './FileInfoModal';
import CaseDetailModal from './CaseDetailModal';
import SuggestedQuestions from './SuggestedQuestions';
import botIcon from '../images/bot_icon.jpeg';  
import userIcon from '../images/user_icon.jpeg';
import './ChatbotInterface.css';  

const INPUT_HISTORY_KEY = 'chat_input_history';
const INPUT_HISTORY_MAX = 10;

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  type: 'bot',
  content: 'Hello! I am the SRR case processing assistant. Please upload PDF or TXT files (supports multi-file batch processing), and I will extract case information and answer related questions for you.',
  timestamp: new Date(),
};

const ChatbotInterface: React.FC = () => {
  const {
    messages,
    extractedData,
    currentFile,
    chatModel,
    setChatModel,
    addMessage: contextAddMessage,
    updateMessageContent,
    removeMessage,
    setExtractedData,
    setCurrentFile,
    saveMessageToSession,
    setSessionData,
    setProcessingSessionId,
    rawFileContent,
    setRawFileContent,
    isLoading: sessionLoading,
    sessionId,
  } = useChat();
  const [isProcessing, setIsProcessing] = useState(false);

  const [inputMessage, setInputMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  // Input history: last 10 entries, ArrowUp/Down to cycle (index -1 = not browsing)
  const [inputHistory, setInputHistory] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem(INPUT_HISTORY_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as string[];
        return Array.isArray(parsed) ? parsed.slice(0, INPUT_HISTORY_MAX) : [];
      }
    } catch {
      /* ignore */
    }
    return [];
  });
  const [historyIndex, setHistoryIndex] = useState(-1);
  const inputBeforeHistoryRef = useRef('');
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const [streamingDisplayLength, setStreamingDisplayLength] = useState(0);
  const streamingContentRef = useRef<string>('');
  const streamingRevealRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [streamEnded, setStreamEnded] = useState(false);
  const pendingFinalTextRef = useRef<string | null>(null);
  const streamingSessionIdRef = useRef<string | null>(null);
  /** When set, the stream-end effect adds the bot message with this fileInfo (e.g. file summary) */
  const pendingStreamFileInfoRef = useRef<any>(null);
  /** Id of the bot message used for chat-query streaming (single-message update); null when not streaming that way */
  const streamingMessageIdRef = useRef<string | null>(null);
  streamingContentRef.current = streamingContent ?? '';
  const [summaryResult, setSummaryResult] = useState<FileSummary | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isFileInfoModalOpen, setIsFileInfoModalOpen] = useState(false);
  const [currentCaseId, setCurrentCaseId] = useState<number | null>(null);
  const [replyDraftState, setReplyDraftState] = useState<{ conversationId: number; replyType: string } | null>(null);
  const [suggestedActionsDismissed, setSuggestedActionsDismissed] = useState(false);
  const [caseDetailModalId, setCaseDetailModalId] = useState<number | null>(null);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const modelDropdownRef = useRef<HTMLDivElement>(null);
  /** Stores the file from duplicate upload for reuse by the Reprocess button */
  const reprocessFileRef = useRef<File | null>(null);

  const OPENAI_MODELS_DEFAULT = ['gpt-4o-mini', 'gpt-4o'];
  const OLLAMA_MODELS_DEFAULT = ['llama3.2', 'llama3.1', 'qwen2.5:7b', 'mistral'];
  const [fetchedModels, setFetchedModels] = useState<{ openai: string[]; ollama: string[] } | null>(null);
  const openaiModels = (fetchedModels?.openai?.length ? fetchedModels.openai : OPENAI_MODELS_DEFAULT);
  const ollamaModels = (fetchedModels?.ollama?.length ? fetchedModels.ollama : OLLAMA_MODELS_DEFAULT);
  const currentModels = chatModel.provider === 'ollama' ? ollamaModels : openaiModels;
  /** Latest extracted case data during current file processing (for similar cases + stats) */
  const processingCaseDataRef = useRef<any>(null);

  // Track current session for async guards: ignore results if user switched session mid-request
  const sessionIdRef = useRef(sessionId);
  /** Session that started the current processing; only that session may show the Processing UI */
  const processingSessionIdRef = useRef<string | null>(null);
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  const displayMessages = sessionLoading ? [] : (messages.length === 0 ? [WELCOME_MESSAGE] : messages);
  const showProcessingUI = isProcessing && sessionIdRef.current === processingSessionIdRef.current;
  const isLoading = sessionLoading || showProcessingUI;

  // Reset local UI/flow state when switching session so the new session doesn't show the previous one's state
  useEffect(() => {
    setSelectedFiles([]);
    setIsProcessing(false);
    setStreamingContent(null);
    setSummaryResult(null);
    setReplyDraftState(null);
    setSuggestedActionsDismissed(false);
    setCurrentCaseId(null);
    pendingFinalTextRef.current = null;
    streamingSessionIdRef.current = null;
    streamingMessageIdRef.current = null;
    processingSessionIdRef.current = null;
  }, [sessionId]);

  // If current model was removed from list (e.g. gpt-4o-nano), fall back to first available
  useEffect(() => {
    if (currentModels.length && !currentModels.includes(chatModel.model)) {
      setChatModel(chatModel.provider, currentModels[0]);
    }
  }, [currentModels, chatModel.provider, chatModel.model, setChatModel]);

  const effectiveCaseId = currentCaseId ?? (currentFile as { case_id?: number })?.case_id ?? null;

  useEffect(() => {
    if (!extractedData) {
      setCurrentCaseId(null);
      setReplyDraftState(null);
      setSuggestedActionsDismissed(false);
    } else if (currentFile && (currentFile as { case_id?: number }).case_id) {
      setCurrentCaseId((currentFile as { case_id: number }).case_id);
    }
  }, [currentFile, extractedData]);

  const scrollToBottom = (instant = false) => {
    messagesEndRef.current?.scrollIntoView({ behavior: instant ? 'auto' : 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, displayMessages]);

  useEffect(() => {
    if (!modelDropdownOpen) return;
    const onDocClick = (e: MouseEvent) => {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(e.target as Node)) {
        setModelDropdownOpen(false);
      }
    };
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, [modelDropdownOpen]);

  useEffect(() => {
    if (modelDropdownOpen) {
      getLlmModels()
        .then(setFetchedModels)
        .catch(() => setFetchedModels(null));
    }
  }, [modelDropdownOpen]);

  // Typewriter reveal: gradually show streaming content char-by-char for "逐字蹦出來" effect
  const prevStreamingRef = useRef<string | null>(null);
  const streamMessageAddedRef = useRef(false);
  /** When true, hide streaming bubble immediately so we don't show bubble + new message in same/next frame */
  const streamBubbleHiddenRef = useRef(false);
  useEffect(() => {
    if (streamingContent === null) {
      setStreamingDisplayLength(0);
      setStreamEnded(false);
      pendingFinalTextRef.current = null;
      prevStreamingRef.current = null;
      streamMessageAddedRef.current = false;
      streamBubbleHiddenRef.current = false;
      if (streamingRevealRef.current) {
        clearInterval(streamingRevealRef.current);
        streamingRevealRef.current = null;
      }
      return;
    }
    if (prevStreamingRef.current === null) setStreamingDisplayLength(0);
    prevStreamingRef.current = streamingContent;
    if (!streamingRevealRef.current) {
      const interval = setInterval(() => {
        const targetLen = streamingContentRef.current.length;
        setStreamingDisplayLength((prev) => Math.min(prev + 2, targetLen));
      }, 25);
      streamingRevealRef.current = interval;
    }
    return () => {
      if (streamingRevealRef.current) {
        clearInterval(streamingRevealRef.current);
        streamingRevealRef.current = null;
      }
    };
  }, [streamingContent]);

  // When stream has ended, wait for typewriter to finish revealing, then add final message (only if still same session)
  useEffect(() => {
    if (!streamEnded || streamingContent === null) return;
    if (streamingSessionIdRef.current !== null && sessionIdRef.current !== streamingSessionIdRef.current) {
      if (streamingMessageIdRef.current) {
        removeMessage(streamingMessageIdRef.current);
        streamingMessageIdRef.current = null;
      }
      setStreamingContent(null);
      setStreamEnded(false);
      pendingFinalTextRef.current = null;
      pendingStreamFileInfoRef.current = null;
      streamingSessionIdRef.current = null;
      setIsProcessing(false);
      streamMessageAddedRef.current = false;
      streamBubbleHiddenRef.current = false;
      return;
    }
    const targetLen = streamingContent.length;
    if (streamingDisplayLength < targetLen) return;
    if (streamMessageAddedRef.current) return;
    streamMessageAddedRef.current = true;
    const finalText = pendingFinalTextRef.current ?? streamingContent;
    const fileInfo = pendingStreamFileInfoRef.current ?? undefined;
    const displayText = (fileInfo?.type === 'summary' && (fileInfo?.summary?.summary != null))
      ? `🤖 AI Summary:\n\n"${fileInfo.summary.summary}"`
      : (finalText || 'No response received.');
    setStreamingContent(null);
    setStreamEnded(false);
    pendingFinalTextRef.current = null;
    pendingStreamFileInfoRef.current = null;
    streamingSessionIdRef.current = null;
    setIsProcessing(false);
    streamBubbleHiddenRef.current = true;
    const sid = streamingMessageIdRef.current;
    if (fileInfo === undefined && sid) {
      // Chat query: update the single streaming message (no second message)
      updateMessageContent(sid, displayText, { saveToBackend: true });
      streamingMessageIdRef.current = null;
    } else {
      addMessage('bot', displayText, fileInfo);
    }
  }, [streamEnded, streamingContent, streamingDisplayLength]);

  const streamingDisplayText = streamingContent === null ? '' : streamingContent.slice(0, streamingDisplayLength);

  // Auto-scroll during streaming; use instant scroll so content doesn't lag
  useEffect(() => {
    if (streamingContent !== null) scrollToBottom(true);
  }, [streamingContent, streamingDisplayLength]);

  const addMessage = (type: 'user' | 'bot', content: string, fileInfo?: any) => {
    contextAddMessage({
      type,
      content,
      timestamp: new Date(),
      fileInfo,
    });
  };

  // Handle file selection (not immediate processing, just file selection)
  const handleFileSelection = (files: File[]) => {
    if (files.length === 0) return;

    // Validate file types and sizes
    const allowedTypes = ['text/plain', 
                          'application/pdf',
                          'application/vnd.ms-excel', // .xls
                          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' // .xlsx
                         ];
    const maxSize = 10 * 1024 * 1024; // 10MB limit
    
    const invalidFiles = files.filter(file => 
      !allowedTypes.includes(file.type) || file.size > maxSize
    );
    
    if (invalidFiles.length > 0) {
      const errorMsg = invalidFiles.map(file => {
        if (!allowedTypes.includes(file.type)) {
          return `${file.name}: Unsupported file type`;
        }
        if (file.size > maxSize) {
          return `${file.name}: File size exceeds 10MB limit`;
        }
        return `${file.name}: Unknown error`;
      }).join('\n');
      
      addMessage('bot', `The following files cannot be processed:\n${errorMsg}\n\nOnly TXT, PDF, XLS, and XLSX files are supported, with a maximum file size of 10MB.`);
      
      // Filter out invalid files
      const validFiles = files.filter(file => 
        allowedTypes.includes(file.type) && file.size <= maxSize
      );
      
      if (validFiles.length === 0) return;
      files = validFiles;
    }

    // Add to existing file list (avoid duplicates)
    const newFiles = files.filter(newFile => 
      !selectedFiles.some(existingFile => 
        existingFile.name === newFile.name && existingFile.size === newFile.size
      )
    );
    
    if (newFiles.length === 0) {
      addMessage('bot', 'Selected files already exist in the list.');
      return;
    }
    
    setSelectedFiles(prev => [...prev, ...newFiles]);
    
    // Display file selection message in chat
    if (newFiles.length === 1) {
      addMessage('user', `📁 Added file: ${newFiles[0].name}`, {
        name: newFiles[0].name,
        size: newFiles[0].size,
        type: newFiles[0].type,
      });
    } else {
      const fileNames = newFiles.map(f => f.name).join(', ');
      addMessage('user', `📁 Added ${newFiles.length} files: ${fileNames}`);
    }
    
    // Display current total file count
    const totalFiles = selectedFiles.length + newFiles.length;
    addMessage('bot', `✅ Files added successfully! Total: ${totalFiles} file${totalFiles > 1 ? 's' : ''}.\n\nClick the "📁 Upload Files" button to view and manage your files, or click "Process Files" to start processing.`);
  };

  const handleRemoveFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    if (newFiles.length === 0) {
      addMessage('bot', 'All files removed from selection.');
    } else {
      addMessage('bot', `File removed. ${newFiles.length} file${newFiles.length > 1 ? 's' : ''} remaining.`);
    }
  };

  const handleClearAllFiles = () => {
    setSelectedFiles([]);
    addMessage('bot', 'All files cleared from selection.');
  };

  // Handle file upload (actual processing of selected files)
  // When reprocessOverride is provided, process that file with force_reprocess to bypass duplicate check
  const handleFileUpload = async (reprocessOverride?: { file: File }) => {
    setIsUploadModalOpen(false);
    const files = reprocessOverride ? [reprocessOverride.file] : selectedFiles;
    const forceReprocess = !!reprocessOverride;
    if (files.length === 0) {
      addMessage('bot', 'Please select files to process first.');
      return;
    }

    // Single file processing (SSE stream)
    if (files.length === 1) {
      const file = files[0];
      const fileInfo = {
        name: file.name,
        size: file.size,
        type: file.type,
      };

      addMessage('user', `Upload file: ${file.name}`, fileInfo);

      let processingMessage = 'Processing your file, please wait...';
      if (file.name.toLowerCase().startsWith('rcc') && file.type === 'application/pdf') {
        processingMessage = 'Processing RCC PDF file, OCR recognition may take 1-2 minutes, please be patient...';
      } else if (file.type === 'application/pdf') {
        processingMessage = 'Processing PDF file, please wait...';
      }
      addMessage('bot', processingMessage);

      const sessionIdAtStart = sessionIdRef.current;
      processingSessionIdRef.current = sessionIdAtStart;
      setProcessingSessionId(sessionIdAtStart);
      setIsProcessing(true);
      setCurrentFile(fileInfo);
      processingCaseDataRef.current = null;

      const buildExtractedMessage = (d: any) => `✅ File Processing Successful!

📋 Extracted Case Information:

📅 Date Received: ${d.A_date_received || 'N/A'}
📋 Source: ${d.B_source || 'N/A'}
🔢 Case Number: ${d.C_case_number || 'N/A'}
⚡ Type: ${d.D_type || 'N/A'}
👤 Caller: ${d.E_caller_name || 'N/A'}
📞 Contact: ${d.F_contact_no || 'N/A'}
🏗️ Slope Number: ${d.G_slope_no || 'N/A'}
📍 Location: ${d.H_location || 'N/A'}
📝 Nature of Request: ${d.I_nature_of_request || 'N/A'}
🏷️ Subject Matter: ${d.J_subject_matter || 'N/A'}
⏰ 10-day Due: ${d.K_10day_rule_due_date || 'N/A'}
⏰ ICC Interim Due: ${d.L_icc_interim_due || 'N/A'}
⏰ ICC Final Due: ${d.M_icc_final_due || 'N/A'}`;

      processFileStream(
        file,
        forceReprocess ? { forceReprocess: true } : undefined,
        {
          onExtracted: (data) => {
            const sd = data.structured_data;
            const switched = sessionIdRef.current !== sessionIdAtStart;
            if (switched) {
              setSessionData(sessionIdAtStart, { extractedData: sd, currentFile: fileInfo, raw_content: data.raw_content ?? null });
              saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: buildExtractedMessage(sd), file_info: { type: 'parsed-success' } }).catch(() => {});
              return;
            }
            setExtractedData(sd);
            const rawContent = data.raw_content ?? undefined;
            setRawFileContent(rawContent ?? null);
            if (data.case_id != null) setCurrentCaseId(data.case_id);
            processingCaseDataRef.current = sd;
            setSessionData(sessionIdAtStart, { extractedData: sd, currentFile: fileInfo, raw_content: rawContent ?? null });
            addMessage('bot', buildExtractedMessage(sd), { type: 'parsed-success' });
          },
          onSummaryChunk: (text) => {
            if (sessionIdRef.current !== sessionIdAtStart) return;
            streamingSessionIdRef.current = sessionIdAtStart;
            setStreamingContent((prev) => (prev ?? '') + text);
          },
          onSummaryFull: (summary, success) => {
            const switched = sessionIdRef.current !== sessionIdAtStart;
            if (switched) {
              const content = success && summary ? `🤖 AI Summary:\n\n"${summary}"` : `⚠️ AI summary generation failed: ${summary || 'Unknown error'}`;
              saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content, file_info: success ? { type: 'summary', summary: { success, summary } } : { type: 'summary-error' } }).catch(() => {});
              return;
            }
            setSummaryResult({ success, summary: success ? summary : undefined, error: success ? undefined : summary });
            if (streamingContentRef.current === '' || streamingContentRef.current === null) {
              if (success && summary) {
                addMessage('bot', `🤖 AI Summary:\n\n"${summary}"`, { type: 'summary', summary: { success, summary } });
              } else {
                addMessage('bot', `⚠️ AI summary generation failed: ${summary || 'Unknown error'}`, { type: 'summary-error' });
              }
            } else {
              setStreamEnded(true);
              pendingStreamFileInfoRef.current = { type: 'summary', summary: { success, summary: success ? summary : undefined } };
            }
          },
          onSimilarCases: async (similar_cases: any[]) => {
            const caseData = processingCaseDataRef.current;
            const saveSimilarCasesToSession = async () => {
              try {
                const cases = similar_cases ?? [];
                if (cases.length > 0) {
                  let message = `📚 **Found ${cases.length} Similar Historical Cases:**\n\n`;
                  cases.forEach((item: any, index: number) => {
                    const c = item.case ?? item;
                    const score = ((item.similarity_score ?? 0) * 100).toFixed(1);
                    const isDup = item.is_potential_duplicate ? ' 🔴 **POTENTIAL DUPLICATE**' : '';
                    const source = item.data_source || 'Unknown';
                    message += `**${index + 1}. [${source}] Case #${c.C_case_number || 'N/A'}** (${score}% match)${isDup}\n`;
                    message += `   📅 Date: ${c.A_date_received || 'N/A'}\n`;
                    message += `   📍 Location: ${c.H_location || 'N/A'}\n`;
                    message += `   🏗️ Slope: ${c.G_slope_no || 'N/A'}\n`;
                    message += `   📝 Subject: ${c.J_subject_matter || 'N/A'}\n`;
                    if (c.E_caller_name || c.F_contact_no) {
                      message += `   👤 Caller: ${c.E_caller_name || 'N/A'}\n`;
                      message += `   📞 Phone: ${c.F_contact_no || 'N/A'}\n`;
                    }
                    if (c.tree_id || c.tree_count) {
                      if (c.tree_id) message += `   🌳 Tree ID: ${c.tree_id}\n`;
                      if (c.tree_count) message += `   🌲 Number of Trees: ${c.tree_count}\n`;
                    }
                    if (c.I_nature_of_request && c.I_nature_of_request !== 'N/A' && c.I_nature_of_request.trim()) {
                      const nature = c.I_nature_of_request.length > 150 ? c.I_nature_of_request.substring(0, 150) + '...' : c.I_nature_of_request;
                      message += `   📄 Complaint Details: ${nature}\n`;
                    }
                    if (c.inspector_remarks) message += `   🔍 Inspector Remarks: ${c.inspector_remarks}\n`;
                    message += '\n';
                  });
                  await saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: message, file_info: { type: 'similar-cases' } });
                  if (caseData?.H_location) {
                    const statsResult = await getCaseStatistics({ location: caseData.H_location });
                    if (statsResult.status === 'success' && statsResult.statistics) {
                      const stats = statsResult.statistics;
                      const isFrequent = stats.is_frequent_complaint;
                      let statsMessage = `📊 **Location Statistics:**\n\n📍 Location: ${caseData.H_location}\n📈 Total Cases: ${stats.total_cases}\n⚠️ Frequent Complaint: ${isFrequent ? 'YES 🔴' : 'NO ✅'}\n\n`;
                      if (isFrequent) statsMessage += `⚠️ **This location has received ${stats.total_cases} complaints, indicating a recurring issue that may require attention.**`;
                      await saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: statsMessage, file_info: { type: 'location-stats' } });
                    }
                  }
                } else {
                  await saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: '✅ No similar historical cases found. This appears to be a unique case.' });
                }
              } catch (err) {
                console.error('Similar case display error:', err);
                await saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: '⚠️ Unable to show similar cases, but file processing was successful.' });
              }
            };
            const switchedSimilar = sessionIdRef.current !== sessionIdAtStart;
            if (switchedSimilar) {
              saveSimilarCasesToSession().catch(() => {});
              return;
            }
            try {
              const cases = similar_cases ?? [];
              if (cases.length > 0) {
                let message = `📚 **Found ${cases.length} Similar Historical Cases:**\n\n`;
                cases.forEach((item: any, index: number) => {
                  const c = item.case ?? item;
                  const score = ((item.similarity_score ?? 0) * 100).toFixed(1);
                  const isDup = item.is_potential_duplicate ? ' 🔴 **POTENTIAL DUPLICATE**' : '';
                  const source = item.data_source || 'Unknown';
                  message += `**${index + 1}. [${source}] Case #${c.C_case_number || 'N/A'}** (${score}% match)${isDup}\n`;
                  message += `   📅 Date: ${c.A_date_received || 'N/A'}\n`;
                  message += `   📍 Location: ${c.H_location || 'N/A'}\n`;
                  message += `   🏗️ Slope: ${c.G_slope_no || 'N/A'}\n`;
                  message += `   📝 Subject: ${c.J_subject_matter || 'N/A'}\n`;
                  if (c.E_caller_name || c.F_contact_no) {
                    message += `   👤 Caller: ${c.E_caller_name || 'N/A'}\n`;
                    message += `   📞 Phone: ${c.F_contact_no || 'N/A'}\n`;
                  }
                  if (c.tree_id || c.tree_count) {
                    if (c.tree_id) message += `   🌳 Tree ID: ${c.tree_id}\n`;
                    if (c.tree_count) message += `   🌲 Number of Trees: ${c.tree_count}\n`;
                  }
                  if (c.I_nature_of_request && c.I_nature_of_request !== 'N/A' && c.I_nature_of_request.trim()) {
                    const nature = c.I_nature_of_request.length > 150 ? c.I_nature_of_request.substring(0, 150) + '...' : c.I_nature_of_request;
                    message += `   📄 Complaint Details: ${nature}\n`;
                  }
                  if (c.inspector_remarks) message += `   🔍 Inspector Remarks: ${c.inspector_remarks}\n`;
                  message += '\n';
                });
                addMessage('bot', message, { type: 'similar-cases' });
                if (caseData?.H_location) {
                  const statsResult = await getCaseStatistics({ location: caseData.H_location });
                  if (sessionIdRef.current !== sessionIdAtStart) return;
                  if (statsResult.status === 'success' && statsResult.statistics) {
                    const stats = statsResult.statistics;
                    const isFrequent = stats.is_frequent_complaint;
                    let statsMessage = `📊 **Location Statistics:**\n\n📍 Location: ${caseData.H_location}\n📈 Total Cases: ${stats.total_cases}\n⚠️ Frequent Complaint: ${isFrequent ? 'YES 🔴' : 'NO ✅'}\n\n`;
                    if (isFrequent) statsMessage += `⚠️ **This location has received ${stats.total_cases} complaints, indicating a recurring issue that may require attention.**`;
                    addMessage('bot', statsMessage, { type: 'location-stats' });
                  }
                }
              } else {
                addMessage('bot', '✅ No similar historical cases found. This appears to be a unique case.');
              }
            } catch (err) {
              console.error('Similar case display error:', err);
              addMessage('bot', '⚠️ Unable to show similar cases, but file processing was successful.');
            }
          },
          onDone: (result) => {
            if (sessionIdRef.current !== sessionIdAtStart) return;
            if (result.case_id != null) setCurrentCaseId(result.case_id);
            setIsProcessing(false);
            setProcessingSessionId(null);
            if (!forceReprocess) setSelectedFiles([]);
            setIsUploadModalOpen(false);
          },
          onDuplicate: (data) => {
            reprocessFileRef.current = file;
            if (sessionIdRef.current !== sessionIdAtStart) {
              setProcessingSessionId(null);
              saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: data.message, file_info: { duplicateCaseId: data.case_id } }).catch(() => {});
              return;
            }
            setIsProcessing(false);
            setProcessingSessionId(null);
            setStreamingContent(null);
            setSessionData(sessionIdAtStart, { extractedData: data.structured_data, currentFile: fileInfo });
            addMessage('bot', data.message, { duplicateCaseId: data.case_id });
            if (!forceReprocess) setSelectedFiles([]);
            setIsUploadModalOpen(false);
          },
          onError: (message) => {
            if (sessionIdRef.current !== sessionIdAtStart) {
              setProcessingSessionId(null);
              saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: message }).catch(() => {});
              return;
            }
            setIsProcessing(false);
            setProcessingSessionId(null);
            setStreamingContent(null);
            addMessage('bot', message);
            setSelectedFiles([]);
            setIsUploadModalOpen(false);
          },
        }
      ).catch((error) => {
        if (sessionIdRef.current !== sessionIdAtStart) {
          setProcessingSessionId(null);
          saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: `Error processing file: ${error instanceof Error ? error.message : 'Unknown error'}` }).catch(() => {});
          return;
        }
        setIsProcessing(false);
        setProcessingSessionId(null);
        setStreamingContent(null);
        addMessage('bot', `Error processing file: ${error instanceof Error ? error.message : 'Unknown error'}`);
        setSelectedFiles([]);
        setIsUploadModalOpen(false);
      });
    } 
    // Multi-file batch processing
    else {
      const fileNames = files.map(f => f.name).join(', ');
      addMessage('user', `Batch upload ${files.length} files: ${fileNames}`);
      
      addMessage('bot', `Processing ${files.length} files in batch, please wait...
      ${files.some(f => f.name.toLowerCase().startsWith('rcc')) ? 
      '⚠️ RCC files detected, OCR processing may take longer time.' : ''}`);

      const sessionIdAtStartBatch = sessionIdRef.current;
      processingSessionIdRef.current = sessionIdAtStartBatch;
      setIsProcessing(true);
      setCurrentFile({ name: `${files.length} files`, size: 0, type: 'batch' } as any);

      try {
        const result: BatchProcessingResponse = await processMultipleFiles(files);
        if (sessionIdRef.current !== sessionIdAtStartBatch) {
          setIsProcessing(false);
          setStreamingContent(null);
          const successFiles = result.results.filter((r: { status: string }) => r.status === 'success');
          const failedFiles = result.results.filter((r: { status: string }) => r.status === 'error');
          const skippedFiles = result.results.filter((r: { status: string }) => r.status === 'skipped');
          let resultMessage = `📊 Batch processing completed!

📈 Processing Statistics:
• Total files: ${result.total_files}
• Successfully processed: ${result.successful}
• Processing failed: ${result.failed}
• Skipped files: ${result.skipped}`;
          if (successFiles.length > 0) {
            resultMessage += `\n\n✅ Successfully processed files (${successFiles.length}):`;
            successFiles.forEach((f: any, index: number) => {
              resultMessage += `\n\n${index + 1}. ${f.main_file}`;
              if (f.email_file) resultMessage += ` (paired with ${f.email_file})`;
              resultMessage += `\n   Case ID: ${f.case_id || 'N/A'}\n   Status: ${f.message}`;
              if (f.structured_data) resultMessage += `\n   📋 Extracted: Date=${f.structured_data.A_date_received || 'N/A'}, Case=${f.structured_data.C_case_number || 'N/A'}, Location=${f.structured_data.H_location || 'N/A'}`;
            });
          }
          if (failedFiles.length > 0) {
            resultMessage += `\n\n❌ Failed to process files (${failedFiles.length}):`;
            failedFiles.forEach((f: any, index: number) => {
              resultMessage += `\n${index + 1}. ${f.main_file}\n   Case ID: ${f.case_id || 'N/A'}\n   Error: ${f.message}`;
            });
          }
          if (skippedFiles.length > 0) {
            resultMessage += `\n\n⏭️ Skipped files (${skippedFiles.length}):`;
            skippedFiles.forEach((f: any, index: number) => {
              resultMessage += `\n${index + 1}. ${f.main_file}\n   Case ID: ${f.case_id || 'N/A'}\n   Reason: ${f.message}`;
            });
          }
          if (successFiles.length > 0) {
            resultMessage += `\n\n💡 Note: The right information panel shows the last successfully processed file (${successFiles[successFiles.length - 1].main_file}).`;
            resultMessage += `\n   All ${successFiles.length} files have been processed successfully.`;
            resultMessage += `\n   You can ask questions about any of the processed cases.`;
            const lastSuccessFile = successFiles[successFiles.length - 1];
            if (lastSuccessFile.structured_data) {
              setSessionData(sessionIdAtStartBatch, { extractedData: lastSuccessFile.structured_data, currentFile: { name: `${result.total_files} files`, size: 0, type: 'batch' } as any });
            }
          }
          saveMessageToSession(sessionIdAtStartBatch, { message_type: 'bot', content: resultMessage }).catch(() => {});
          return;
        }
        
        setIsProcessing(false);

        // Display batch processing results - 显示所有文件的结果，包括跳过的
        const successFiles = result.results.filter(r => r.status === 'success');
        const failedFiles = result.results.filter(r => r.status === 'error');
        const skippedFiles = result.results.filter(r => r.status === 'skipped');  // 新增
        
        let resultMessage = `📊 Batch processing completed!

📈 Processing Statistics:
• Total files: ${result.total_files}
• Successfully processed: ${result.successful}
• Processing failed: ${result.failed}
• Skipped files: ${result.skipped}`;  // 添加跳过统计

        // 显示成功文件（包含详细信息）
        if (successFiles.length > 0) {
          resultMessage += `\n\n✅ Successfully processed files (${successFiles.length}):`;
          successFiles.forEach((f, index) => {
            resultMessage += `\n\n${index + 1}. ${f.main_file}`;
            if (f.email_file) {
              resultMessage += ` (paired with ${f.email_file})`;
            }
            resultMessage += `\n   Case ID: ${f.case_id || 'N/A'}`;
            resultMessage += `\n   Status: ${f.message}`;
            if (f.structured_data) {
              resultMessage += `\n   📋 Extracted: Date=${f.structured_data.A_date_received || 'N/A'}, Case=${f.structured_data.C_case_number || 'N/A'}, Location=${f.structured_data.H_location || 'N/A'}`;
            }
          });
        }

        // 显示失败文件
        if (failedFiles.length > 0) {
          resultMessage += `\n\n❌ Failed to process files (${failedFiles.length}):`;
          failedFiles.forEach((f, index) => {
            resultMessage += `\n${index + 1}. ${f.main_file}`;
            resultMessage += `\n   Case ID: ${f.case_id || 'N/A'}`;
            resultMessage += `\n   Error: ${f.message}`;
          });
        }

        // 显示跳过的文件（新增）
        if (skippedFiles.length > 0) {
          resultMessage += `\n\n⏭️ Skipped files (${skippedFiles.length}):`;
          skippedFiles.forEach((f, index) => {
            resultMessage += `\n${index + 1}. ${f.main_file}`;
            resultMessage += `\n   Case ID: ${f.case_id || 'N/A'}`;
            resultMessage += `\n   Reason: ${f.message}`;
          });
        }

        if (successFiles.length > 0) {
          resultMessage += `\n\n💡 Note: The right information panel shows the last successfully processed file (${successFiles[successFiles.length - 1].main_file}).`;
          resultMessage += `\n   All ${successFiles.length} files have been processed successfully.`;
          resultMessage += `\n   You can ask questions about any of the processed cases.`;
          
          // 设置最后一个成功文件的数据到右侧面板
          const lastSuccessFile = successFiles[successFiles.length - 1];
          if (lastSuccessFile.structured_data) {
            setExtractedData(lastSuccessFile.structured_data);
          }
          // Batch processing does not save to DB, so case_id is string (filename). No numeric case_id for reply draft.
        }

        addMessage('bot', resultMessage);
        
        // Clear file list after batch processing
        setSelectedFiles([]);
        setIsUploadModalOpen(false);
        
      } catch (error) {
        if (sessionIdRef.current !== sessionIdAtStartBatch) {
          setIsProcessing(false);
          setStreamingContent(null);
          saveMessageToSession(sessionIdAtStartBatch, { message_type: 'bot', content: `Error in batch processing files: ${error instanceof Error ? error.message : 'Unknown error'}` }).catch(() => {});
          return;
        }
        setIsProcessing(false);
        addMessage('bot', `Error in batch processing files: ${error instanceof Error ? error.message : 'Unknown error'}`);
        
        // Clear file list on error
        setSelectedFiles([]);
        setIsUploadModalOpen(false);
      }
    }
  };

  const handleLoadCaseForDraft = async (caseId: number, filename: string, caseData: any) => {
    try {
      const extracted: ExtractedData = {
        A_date_received: caseData.A_date_received ?? '',
        B_source: caseData.B_source ?? '',
        C_case_number: caseData.C_case_number ?? '',
        D_type: caseData.D_type ?? '',
        E_caller_name: caseData.E_caller_name ?? '',
        F_contact_no: caseData.F_contact_no ?? '',
        G_slope_no: caseData.G_slope_no ?? '',
        H_location: caseData.H_location ?? '',
        I_nature_of_request: caseData.I_nature_of_request ?? '',
        J_subject_matter: caseData.J_subject_matter ?? '',
        K_10day_rule_due_date: caseData.K_10day_rule_due_date ?? '',
        L_icc_interim_due: caseData.L_icc_interim_due ?? '',
        M_icc_final_due: caseData.M_icc_final_due ?? '',
        N_works_completion_due: caseData.N_works_completion_due ?? '',
        O1_fax_to_contractor: caseData.O1_fax_to_contractor ?? '',
        O2_email_send_time: caseData.O2_email_send_time ?? '',
        P_fax_pages: caseData.P_fax_pages ?? '',
        Q_case_details: caseData.Q_case_details ?? ''
      };
      setExtractedData(extracted);
      setCurrentFile({ name: filename, size: 0, type: '', case_id: caseId });
      setCurrentCaseId(caseId);
      setCaseDetailModalId(null);
    } catch (err) {
      console.error('Load case for draft error:', err);
      addMessage('bot', `Failed to load case: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleReplyTemplateClick = async (replyType: string, skipQuestions: boolean) => {
    const cid = effectiveCaseId;
    if (cid == null || typeof cid !== 'number') {
      addMessage('bot', '⚠️ Cannot generate draft reply: please process a single file first, or load a case from the case list.');
      return;
    }
    const sessionIdAtStart = sessionIdRef.current;
    processingSessionIdRef.current = sessionIdAtStart;
    setIsProcessing(true);
    addMessage('user', skipQuestions ? `Generate ${replyType} reply directly` : `Draft ${replyType} reply`);
    try {
      if (skipQuestions) {
        setStreamingContent('');
        const { fullText, conversation_id } = await generateReplyDraftStream(
          { case_id: cid, reply_type: replyType, is_initial: true, skip_questions: true },
          (chunk) => {
            if (sessionIdRef.current === sessionIdAtStart) {
              setStreamingContent((prev) => (prev ?? '') + chunk);
            }
          }
        );
        if (sessionIdRef.current !== sessionIdAtStart) {
          setStreamingContent(null);
          setIsProcessing(false);
          saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: fullText ? `📝 **回覆草稿 (${replyType})**\n\n${fullText}` : 'Draft reply generated.' }).catch(() => {});
          return;
        }
        setStreamingContent(null);
        setIsProcessing(false);
        addMessage('bot', fullText ? `📝 **回覆草稿 (${replyType})**\n\n${fullText}` : 'Draft reply generated.', { type: 'draft-reply', conversationId: conversation_id });
      } else {
        const res = await generateReplyDraft({
          case_id: cid,
          reply_type: replyType,
          is_initial: true,
          skip_questions: false
        });
        if (sessionIdRef.current !== sessionIdAtStart) {
          setIsProcessing(false);
          const content = res.is_question ? res.message : (res.draft_reply ? `📝 **回覆草稿 (${replyType})**\n\n${res.draft_reply}` : (res.message || 'Draft reply generated.'));
          saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content }).catch(() => {});
          return;
        }
        setIsProcessing(false);
        if (res.is_question) {
          setReplyDraftState({ conversationId: res.conversation_id, replyType });
          addMessage('bot', res.message);
        } else if (res.draft_reply) {
          addMessage('bot', `📝 **回覆草稿 (${replyType})**\n\n${res.draft_reply}`, { type: 'draft-reply', conversationId: res.conversation_id });
        } else {
          addMessage('bot', res.message || 'Draft reply generated.');
        }
      }
    } catch (err) {
      if (sessionIdRef.current !== sessionIdAtStart) {
        setStreamingContent(null);
        setIsProcessing(false);
        saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: `Draft reply generation failed: ${err instanceof Error ? err.message : 'Unknown error'}` }).catch(() => {});
        return;
      }
      setStreamingContent(null);
      setIsProcessing(false);
      addMessage('bot', `Draft reply generation failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Handle user queries
  const handleQuery = async () => {
    if (!inputMessage.trim()) return;

    const userQuery = inputMessage.trim();
    setInputMessage('');
    setHistoryIndex(-1);

    // If replying to a draft question, route to generateReplyDraftStream (streaming)
    if (replyDraftState) {
      const { conversationId, replyType } = replyDraftState;
      const sessionIdAtStart = sessionIdRef.current;
      processingSessionIdRef.current = sessionIdAtStart;
      setReplyDraftState(null);
      addMessage('user', userQuery);
      setIsProcessing(true);
      setStreamingContent('');
      try {
        const { fullText, conversation_id } = await generateReplyDraftStream(
          {
            case_id: effectiveCaseId!,
            reply_type: replyType,
            conversation_id: conversationId,
            user_message: userQuery,
            is_initial: false,
            skip_questions: false
          },
          (chunk) => {
            if (sessionIdRef.current === sessionIdAtStart) {
              setStreamingContent((prev) => (prev ?? '') + chunk);
            }
          }
        );
        if (sessionIdRef.current !== sessionIdAtStart) {
          setStreamingContent(null);
          setIsProcessing(false);
          const finalContent = fullText ? `📝 **回覆草稿 (${replyType})**\n\n${fullText}` : 'Done.';
          saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: finalContent }).catch(() => {});
          return;
        }
        const finalContent = fullText ? `📝 **回覆草稿 (${replyType})**\n\n${fullText}` : 'Done.';
        setIsProcessing(false);
        pendingFinalTextRef.current = finalContent;
        pendingStreamFileInfoRef.current = { type: 'draft-reply', conversationId: conversation_id };
        streamingSessionIdRef.current = sessionIdAtStart;
        setStreamEnded(true);
      } catch (err) {
        if (sessionIdRef.current !== sessionIdAtStart) {
          setStreamingContent(null);
          setIsProcessing(false);
          saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: `Draft reply generation failed: ${err instanceof Error ? err.message : 'Unknown error'}` }).catch(() => {});
          return;
        }
        setStreamingContent(null);
        setIsProcessing(false);
        addMessage('bot', `Draft reply generation failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
      return;
    }

    // Append to input history (avoid duplicate with latest, keep last 10)
    if (userQuery && (inputHistory.length === 0 || inputHistory[0] !== userQuery)) {
      const nextHistory = [userQuery, ...inputHistory].slice(0, INPUT_HISTORY_MAX);
      setInputHistory(nextHistory);
      try {
        localStorage.setItem(INPUT_HISTORY_KEY, JSON.stringify(nextHistory));
      } catch {
        /* ignore */
      }
    }

    addMessage('user', userQuery);

    const streamingId = `streaming-${Date.now()}`;
    streamingMessageIdRef.current = streamingId;
    contextAddMessage({ id: streamingId, type: 'bot', content: '', timestamp: new Date() });
    const sessionIdAtStart = sessionIdRef.current;
    processingSessionIdRef.current = sessionIdAtStart;
    setIsProcessing(true);
    setStreamingContent('');

    try {
      const effectiveModel = currentModels.includes(chatModel.model) ? chatModel.model : currentModels[0];
      const fullText = await queryCaseStream(
        {
          query: userQuery,
          context: extractedData || undefined,
          raw_content: rawFileContent ?? undefined,
          provider: chatModel.provider,
          model: effectiveModel,
        },
        (chunk) => {
          if (sessionIdRef.current === sessionIdAtStart) {
            setStreamingContent((prev) => (prev ?? '') + chunk);
          }
        }
      );

      if (sessionIdRef.current !== sessionIdAtStart) {
        if (streamingMessageIdRef.current) {
          removeMessage(streamingMessageIdRef.current);
          streamingMessageIdRef.current = null;
        }
        setStreamingContent(null);
        setIsProcessing(false);
        saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: fullText || 'No response received.' }).catch(() => {});
        return;
      }
      // Ensure streaming state has the full text before ending, so effect uses correct length and no race with batched chunk updates
      const finalTextForQuery = fullText || 'No response received.';
      setIsProcessing(false);
      pendingFinalTextRef.current = finalTextForQuery;
      streamingSessionIdRef.current = sessionIdAtStart;
      setStreamingContent(finalTextForQuery);
      setStreamEnded(true);
    } catch (error) {
      if (sessionIdRef.current !== sessionIdAtStart) {
        if (streamingMessageIdRef.current) {
          removeMessage(streamingMessageIdRef.current);
          streamingMessageIdRef.current = null;
        }
        setStreamingContent(null);
        setIsProcessing(false);
        saveMessageToSession(sessionIdAtStart, { message_type: 'bot', content: `Query failed: ${error instanceof Error ? error.message : 'Unknown error'}` }).catch(() => {});
        return;
      }
      setStreamingContent(null);
      setIsProcessing(false);
      const errMsg = `Query failed: ${error instanceof Error ? error.message : 'Unknown error'}`;
      if (streamingMessageIdRef.current) {
        updateMessageContent(streamingMessageIdRef.current, errMsg, { saveToBackend: true });
        streamingMessageIdRef.current = null;
      } else {
        addMessage('bot', errMsg);
      }
    }
  };

  // Handle keyboard: Enter to send; ArrowUp/ArrowDown to cycle input history
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (inputHistory.length === 0) return;
      if (historyIndex === -1) inputBeforeHistoryRef.current = inputMessage;
      const nextIndex = historyIndex === -1 ? inputHistory.length - 1 : Math.min(historyIndex + 1, inputHistory.length - 1);
      setHistoryIndex(nextIndex);
      setInputMessage(inputHistory[nextIndex]);
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex <= 0) {
        setHistoryIndex(-1);
        setInputMessage(inputBeforeHistoryRef.current);
        return;
      }
      const nextIndex = historyIndex - 1;
      setHistoryIndex(nextIndex);
      setInputMessage(inputHistory[nextIndex]);
    }
  };

  // Note: Drag and drop functionality is now handled in FileUploadModal component

  return (
    <div className="chatbot-container">
      {/* Single integrated chat area */}
      <div className="chat-section-full">
        <div className="chat-header">
          <div className="header-content">
            <img src={universityLogo} alt="SRR Logo" className="header-logo" />
            <img src={logoImage} alt="SRR Logo" className="header-logo" />
            <div className="header-text">
              <h1>SRR Case Processing Assistant</h1>
              <p>Intelligent File Processing & Case Query System</p>
            </div>
          </div>
        </div>

        <div className="chat-messages">
          {sessionLoading && (
            <div className="message bot">
              <div className="message-avatar">
                <img src={botIcon} alt="Bot" className="avatar-image" />
              </div>
              <div className="message-content">
                <div className="loading">
                  <div className="loading-spinner"></div>
                  Loading session...
                </div>
              </div>
            </div>
          )}
          {displayMessages.map((message, index) => (
            <div key={message.id ?? `msg-${index}`} className={`message ${message.type}`}>
              {message.type === 'bot' && (
                <div className="message-avatar">
                  <img src={botIcon} alt="Bot" className="avatar-image" />
                </div>
              )}
              <div className="message-content">
                {message.fileInfo && message.fileInfo.size != null && (() => {
                  const fi = message.fileInfo as { name?: string; filename?: string; size: number };
                  const label = fi.name ?? fi.filename ?? 'File';
                  return (
                    <div className="message-file-info-inline">
                      <FileText size={22} aria-hidden />
                      <span>{label} ({(fi.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  );
                })()}

                <div className="message-text">
                  {message.id === streamingMessageIdRef.current && streamingContent !== null ? (
                    <>
                      {streamingDisplayText}
                      <span className="streaming-cursor">▌</span>
                    </>
                  ) : (
                    /* 僅第一次即時輸出使用流式；歷史加載的訊息直接顯示完整內容，不再做 ProgressiveReveal */
                    message.content
                  )}
                </div>
                {((message.fileInfo as { type?: string; conversationId?: number })?.type === 'draft-reply' || message.content.startsWith('📝 **回覆草稿')) && (
                  <div className="message-actions">
                    <button
                      type="button"
                      className="message-delete-draft"
                      onClick={() => {
                        removeMessage(message.id!);
                        const cid = (message.fileInfo as { conversationId?: number })?.conversationId;
                        if (cid != null) deleteConversationDraft(cid).catch(() => {});
                      }}
                      title="刪除草稿 / Delete draft"
                      aria-label="Delete draft"
                    >
                      <Trash2 size={16} />
                      <span>刪除草稿</span>
                    </button>
                  </div>
                )}
                {(message.fileInfo as { duplicateCaseId?: number } | undefined)?.duplicateCaseId != null && (
                  <div className="message-case-link">
                    <button
                      type="button"
                      className="message-case-detail-link"
                      onClick={() => setCaseDetailModalId((message.fileInfo as { duplicateCaseId: number }).duplicateCaseId)}
                    >
                      View case details
                    </button>
                    <button
                      type="button"
                      className="message-case-detail-link reprocess"
                      onClick={() => {
                        const f = reprocessFileRef.current;
                        if (f) handleFileUpload({ file: f });
                      }}
                    >
                      Reprocess
                    </button>
                  </div>
                )}
              </div>
              {message.type === 'user' && (
                <div className="message-avatar">
                  <img src={userIcon} alt="User" className="avatar-image" />
                </div>
              )}
            </div>
          ))}

          {streamingContent !== null && !streamBubbleHiddenRef.current && (streamingMessageIdRef.current === null || displayMessages[displayMessages.length - 1]?.id !== streamingMessageIdRef.current) && (
            <div className="message bot">
              <div className="message-avatar">
                <img src={botIcon} alt="Bot" className="avatar-image" />
              </div>
              <div className="message-content">
                <div className="message-text">
                  {streamingDisplayText}
                  <span className="streaming-cursor">▌</span>
                </div>
              </div>
            </div>
          )}
          
          {showProcessingUI && streamingContent === null && !sessionLoading && (
            <div className="message bot">
              <div className="message-avatar">
                <img src={botIcon} alt="Bot" className="avatar-image" />
              </div>
              <div className="message-content">
                <div className="loading">
                  <div className="loading-spinner"></div>
                  Processing...
                </div>
              </div>
            </div>
          )}

          {extractedData && effectiveCaseId != null && typeof effectiveCaseId === 'number' && !suggestedActionsDismissed && (
            <div className="message bot">
              <div className="message-avatar">
                <img src={botIcon} alt="Bot" className="avatar-image" />
              </div>
              <div className="message-content">
                <SuggestedQuestions
                  onQuestionClick={(type, skipQuestions) => { void handleReplyTemplateClick(type, skipQuestions ?? false); }}
                  disabled={isLoading}
                  embedded
                  showEndButton={true}
                  onEndDraft={() => { setReplyDraftState(null); setSuggestedActionsDismissed(true); }}
                />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-bottom-area">
          <div className="chat-input">
          <div className="input-container">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isLoading 
                  ? "Processing..." 
                  : selectedFiles.length > 0 && !extractedData
                    ? "Click 'Process Files' to start processing or ask questions..."
                    : extractedData 
                      ? "Ask questions about the case..." 
                      : "Type your message or upload files to get started..."
              }
              disabled={isLoading}
            />
            
            <div className="input-actions">
              <button
                className="action-button upload-button"
                onClick={() => setIsUploadModalOpen(true)}
                disabled={isLoading}
                title="Upload files"
              >
                <Upload size={25} />
              </button>

              {selectedFiles.length > 0 && !extractedData && (
                <button
                  className="action-button process-button"
                  onClick={() => handleFileUpload()}
                  disabled={isLoading}
                  title="Process selected files"
                >
                  {isLoading ? (
                    <div className="loading-spinner-small"></div>
                  ) : (
                    <Upload size={22} />
                  )}
                </button>
              )}

              {extractedData && (
                <button
                  className="action-button details-button"
                  onClick={() => setIsFileInfoModalOpen(true)}
                  title="View file details"
                >
                  <FileText size={22} />
                </button>
              )}

              <div className="model-select-wrapper" ref={modelDropdownRef}>
                <button
                  type="button"
                  className="action-button model-button"
                  onClick={() => setModelDropdownOpen((o) => !o)}
                  disabled={isLoading}
                  title={`Model: ${chatModel.provider} / ${chatModel.model}`}
                >
                  <Cpu size={22} />
                </button>
                {modelDropdownOpen && (
                  <div className="model-dropdown">
                    <div className="model-dropdown-section">
                      <span className="model-dropdown-label">Provider</span>
                      <button
                        type="button"
                        className={`model-dropdown-item ${chatModel.provider === 'openai' ? 'active' : ''}`}
                        onClick={() => setChatModel('openai', openaiModels.includes(chatModel.model) ? chatModel.model : openaiModels[0])}
                      >
                        OpenAI
                      </button>
                      <button
                        type="button"
                        className={`model-dropdown-item ${chatModel.provider === 'ollama' ? 'active' : ''}`}
                        onClick={() => setChatModel('ollama', ollamaModels.includes(chatModel.model) ? chatModel.model : ollamaModels[0])}
                      >
                        Ollama
                      </button>
                    </div>
                    <div className="model-dropdown-section">
                      <span className="model-dropdown-label">Model</span>
                      {currentModels.map((m) => (
                        <button
                          key={m}
                          type="button"
                          className={`model-dropdown-item ${chatModel.model === m ? 'active' : ''}`}
                          onClick={() => {
                            setChatModel(chatModel.provider, m);
                            setModelDropdownOpen(false);
                          }}
                        >
                          {m}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <button
                className="action-button send-button"
                onClick={handleQuery}
                disabled={!inputMessage.trim() || isLoading}
                title="Send message"
              >
                <Send size={25} />
              </button>
            </div>
          </div>
        </div>
        </div>
      </div>

      {/* File Upload Modal */}
      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onFilesSelected={handleFileSelection}
        selectedFiles={selectedFiles}
        onRemoveFile={handleRemoveFile}
        onClearAll={handleClearAllFiles}
        onProcessFiles={handleFileUpload}
        isLoading={isLoading}
      />

      {/* File Info Modal */}
      <FileInfoModal
        isOpen={isFileInfoModalOpen}
        onClose={() => setIsFileInfoModalOpen(false)}
        fileInfo={currentFile}
        extractedData={extractedData}
        summaryResult={summaryResult}
      />

      {/* Case Detail Modal (e.g. from "already processed" link) */}
      <CaseDetailModal
        caseId={caseDetailModalId}
        onClose={() => setCaseDetailModalId(null)}
        onLoadForQuery={handleLoadCaseForDraft}
      />
    </div>
  );
};

export default ChatbotInterface;