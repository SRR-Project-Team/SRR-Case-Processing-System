import React, { useState, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Send, Upload, FileText, Bot, User } from 'lucide-react';
import { Message, ChatState, FileSummary } from '../types';
import { processFile, processMultipleFiles, queryCase, BatchProcessingResponse } from '../services/api';
import ExtractedInfoDisplay from './ExtractedInfoDisplay';
import logoImage from '../images/system_logo.png'; 
import universityLogo from '../images/university_logo.png'; 

const ChatbotInterface: React.FC = () => {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [
      {
        id: '1',
        type: 'bot',
        content: 'Hello! I am the SRR case processing assistant. Please upload PDF or TXT files (supports multi-file batch processing), and I will extract case information and answer related questions for you.',
        timestamp: new Date(),
      }
    ],
    isLoading: false,
    extractedData: null,
    currentFile: null,
  });

  const [inputMessage, setInputMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  // 在组件状态中添加总结相关状态
  const [summaryResult, setSummaryResult] = useState<FileSummary | null>(null);


  // Auto scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatState.messages]);

  // Add message
  const addMessage = (type: 'user' | 'bot', content: string, fileInfo?: any) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
      fileInfo,
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));
  };

  // Handle file selection (not immediate processing, just file selection)
  const handleFileSelection = (files: File[]) => {
    if (files.length === 0) return;

    // Validate file types and sizes
    const allowedTypes = ['text/plain', 'application/pdf'];
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
      
      addMessage('bot', `The following files cannot be processed:\n${errorMsg}\n\nOnly TXT and PDF files are supported, with a maximum file size of 10MB.`);
      
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
    
    // Display file selection message
    if (newFiles.length === 1) {
      addMessage('user', `Add file: ${newFiles[0].name}`, {
        name: newFiles[0].name,
        size: newFiles[0].size,
        type: newFiles[0].type,
      });
    } else {
      const fileNames = newFiles.map(f => f.name).join(', ');
      addMessage('user', `Add ${newFiles.length} files: ${fileNames}`);
    }
    
    // Display current total file count
    const totalFiles = selectedFiles.length + newFiles.length;
    if (totalFiles === 1) {
      addMessage('bot', 'File added to list, click "Start Processing" button to process the file.');
    } else {
      addMessage('bot', `Currently have ${totalFiles} files, click "Start Batch Processing" button to process all files.`);
    }
  };

  // Handle file upload (actual processing of selected files)
  const handleFileUpload = async () => {
    const files = selectedFiles;
    if (files.length === 0) {
      addMessage('bot', 'Please select files to process first.');
      return;
    }

    // Single file processing
    if (files.length === 1) {
      const file = files[0];
      const fileInfo = {
        name: file.name,
        size: file.size,
        type: file.type,
      };

      addMessage('user', `Upload file: ${file.name}`, fileInfo);

      // Provide different processing hints based on file type
      let processingMessage = 'Processing your file, please wait...';
      if (file.name.toLowerCase().startsWith('rcc') && file.type === 'application/pdf') {
        processingMessage = 'Processing RCC PDF file, OCR recognition may take 1-2 minutes, please be patient...';
      } else if (file.type === 'application/pdf') {
        processingMessage = 'Processing PDF file, please wait...';
      }
      addMessage('bot', processingMessage);

      setChatState(prev => ({
        ...prev,
        isLoading: true,
        currentFile: fileInfo,
      }));

      try {
        const result = await processFile(file);
        
        if (result.status === 'success' && result.data) {
          setChatState(prev => ({
            ...prev,
            isLoading: false,
            extractedData: result.data!,
          }));

          addMessage('bot', `File processing successful! I have extracted the case information. You can view detailed information on the right side, or ask me any questions about this case.

For example, you can ask:
• "What is the basic information of this case?"
• "Contact information"
• "Slope-related information"
• "Important dates"
• "Nature of the case"`);
          
          // display AI summary
        if (result.summary) {
          setSummaryResult(result.summary);
          
          if (result.summary.success && result.summary.summary) {
            addMessage('bot', `🤖 AI Summary:\n\n"${result.summary.summary}"`, {
              type: 'summary',
              summary: result.summary
            });
          } else {
            addMessage('bot', `⚠️ AI summary generation failed: ${result.summary.error || 'Unknown error'}`, {
              type: 'summary-error'
            });
          }
        }

          // Clear selected file list
          setSelectedFiles([]);
        } else {
          setChatState(prev => ({ ...prev, isLoading: false }));
          addMessage('bot', `File processing failed: ${result.message || result.error || 'Unknown error'}`);
          // Clear file list on failure
          setSelectedFiles([]);
        }
      } catch (error) {
        setChatState(prev => ({ ...prev, isLoading: false }));
        addMessage('bot', `Error processing file: ${error instanceof Error ? error.message : 'Unknown error'}`);
        // Clear file list on error
        setSelectedFiles([]);
      }
    } 
    // Multi-file batch processing
    else {
      const fileNames = files.map(f => f.name).join(', ');
      addMessage('user', `Batch upload ${files.length} files: ${fileNames}`);
      
      addMessage('bot', `Processing ${files.length} files in batch, please wait...
      
${files.some(f => f.name.toLowerCase().startsWith('rcc')) ? 
  '⚠️ RCC files detected, OCR processing may take longer time.' : ''}`);

      setChatState(prev => ({
        ...prev,
        isLoading: true,
        currentFile: { name: `${files.length} files`, size: 0, type: 'batch' },
      }));

      try {
        const result: BatchProcessingResponse = await processMultipleFiles(files);
        
        setChatState(prev => ({
          ...prev,
          isLoading: false,
        }));

        // Display batch processing results
        const successFiles = result.results.filter(r => r.status === 'success');
        const failedFiles = result.results.filter(r => r.status === 'error');
        
        let resultMessage = `📊 Batch processing completed!
        
📈 Processing Statistics:
• Total files: ${result.total_files}
• Successfully processed: ${result.successful}
• Processing failed: ${result.failed}`;

        if (successFiles.length > 0) {
          resultMessage += `\n\n✅ Successfully processed files:
${successFiles.map(f => `• ${f.filename}`).join('\n')}`;
        }

        if (failedFiles.length > 0) {
          resultMessage += `\n\n❌ Failed to process files:
${failedFiles.map(f => `• ${f.filename}: ${f.message}`).join('\n')}`;
        }

        if (successFiles.length > 0) {
          resultMessage += `\n\n💡 Tip: Since multiple files were processed in batch, the right information panel shows the last successfully processed file. You can ask about specific file information.`;
          
          // Set the last successful file's data to the right panel
          const lastSuccessFile = successFiles[successFiles.length - 1];
          if (lastSuccessFile.structured_data) {
            setChatState(prev => ({
              ...prev,
              extractedData: lastSuccessFile.structured_data,
            }));
          }
        }

        addMessage('bot', resultMessage);
        
        // Clear file list after batch processing
        setSelectedFiles([]);
        
      } catch (error) {
        setChatState(prev => ({
          ...prev,
          isLoading: false,
        }));
        
        addMessage('bot', `Error in batch processing files: ${error instanceof Error ? error.message : 'Unknown error'}`);
        
        // Clear file list on error
        setSelectedFiles([]);
      }
    }
  };

  // Handle user queries
  const handleQuery = async () => {
    if (!inputMessage.trim()) return;

    const userQuery = inputMessage.trim();
    setInputMessage('');
    addMessage('user', userQuery);

    setChatState(prev => ({ ...prev, isLoading: true }));

    try {
      const response = await queryCase({
        query: userQuery,
        context: chatState.extractedData || undefined,
      });

      setChatState(prev => ({ ...prev, isLoading: false }));
      addMessage('bot', response);
    } catch (error) {
      setChatState(prev => ({ ...prev, isLoading: false }));
      addMessage('bot', `Query failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Drag and drop upload configuration (supports multiple files)
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileSelection,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 10, // Support up to 10 files
    multiple: true, // Support multiple file selection
  });

  // Handle keyboard events
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  return (
    <div className="chatbot-container">

      {/* Left information display area */}
      <div className="info-section">
        <div className="info-header">
          <h2>File Processing</h2>
          <p>Drag or click to upload PDF/TXT files (supports multiple files)</p>
        </div>

        <div className="info-content">
          {/* File upload area */}
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            <div className="dropzone-content">
              <Upload size={32} className="dropzone-icon" />
              <div className="dropzone-text">
                {isDragActive ? (
                  <span>Drop files to add to list</span>
                ) : (
                  <>
                    <strong>Click or drag files here to add</strong>
                    <br />
                    Supports PDF and TXT formats (can add files multiple times)
                    <br />
                    <small>Maximum file size: 10MB, up to 10 files</small>
                    <br />
                    <small style={{color: '#666', marginTop: '5px'}}>You can select files multiple times to accumulate in the list, then click "Start Processing"</small>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Selected files list and confirmation button */}
          {selectedFiles.length > 0 && (
            <div className="selected-files-section">
              <h3>
                <FileText size={16} />
                Selected Files ({selectedFiles.length})
              </h3>
              <div className="selected-files-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="selected-file-item">
                    <div className="file-info">
                      <div className="file-name">{file.name}</div>
                      <div className="file-details">
                        {(file.size / 1024).toFixed(1)} KB • {file.type}
                      </div>
                    </div>
                    <button 
                      className="remove-file-btn"
                      onClick={() => {
                        const newFiles = selectedFiles.filter((_, i) => i !== index);
                        setSelectedFiles(newFiles);
                        if (newFiles.length === 0) {
                          addMessage('bot', 'File selection cleared.');
                        }
                      }}
                      disabled={chatState.isLoading}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
              <div className="file-actions">
                <button 
                  className="process-files-btn"
                  onClick={handleFileUpload}
                  disabled={chatState.isLoading}
                >
                  {chatState.isLoading ? 'Processing...' : 
                    selectedFiles.length === 1 ? 'Start Processing' : `Start Batch Processing (${selectedFiles.length} files)`
                  }
                </button>
                <button 
                  className="clear-files-btn"
                  onClick={() => {
                    setSelectedFiles([]);
                    addMessage('bot', 'File selection cleared.');
                  }}
                  disabled={chatState.isLoading}
                >
                  Clear Selection
                </button>
              </div>
            </div>
          )}

          {/* Current file information */}
          {chatState.currentFile && (
            <div className="extracted-info">
              <h3>
                <FileText size={16} />
                Current File
              </h3>
              <div className="info-item">
                <div className="info-label">File Name</div>
                <div className="info-value">{chatState.currentFile.name}</div>
              </div>
              <div className="info-item">
                <div className="info-label">Size</div>
                <div className="info-value">
                  {(chatState.currentFile.size / 1024).toFixed(1)} KB
                </div>
              </div>
              <div className="info-item">
                <div className="info-label">Type</div>
                <div className="info-value">{chatState.currentFile.type}</div>
              </div>
            </div>
          )}

          {/* Extracted information display */}
          {chatState.extractedData && (
            <ExtractedInfoDisplay data={chatState.extractedData} />
          )}

          {/* Status prompt */}
          {chatState.isLoading && (
            <div className="loading">
              <div className="loading-spinner"></div>
              Processing file...
            </div>
          )}
        </div>
      </div>

      {/* Right chat area */}
      <div className="chat-section">
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
          {chatState.messages.map((message) => (
            <div key={message.id} className={`message ${message.type}`}>
              {message.type === 'bot' && (
                <div className="message-avatar">
                  <Bot size={16} />
                </div>
              )}
              <div className="message-content">
                {message.fileInfo && (
                  <div style={{ marginBottom: '8px', fontSize: '12px', opacity: 0.8 }}>
                    <FileText size={14} style={{ display: 'inline', marginRight: '4px' }} />
                    {message.fileInfo.name} ({(message.fileInfo.size / 1024).toFixed(1)} KB)
                  </div>
                )}

                {/* summary message special display */}

                <div style={{ whiteSpace: 'pre-line' }}>
                  {message.content}
                </div>

              </div>
              {message.type === 'user' && (
                <div className="message-avatar">
                  <User size={16} />
                </div>
              )}
            </div>
          ))}
          
          {chatState.isLoading && (
            <div className="message bot">
              <div className="message-avatar">
                <Bot size={16} />
              </div>
              <div className="message-content">
                <div className="loading">
                  <div className="loading-spinner"></div>
                  Processing...
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input">
          <div className="input-container">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={chatState.extractedData ? "Ask questions about the case..." : "Please upload files first..."}
              disabled={chatState.isLoading}
            />
            <button
              className="send-button"
              onClick={handleQuery}
              disabled={!inputMessage.trim() || chatState.isLoading}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatbotInterface;