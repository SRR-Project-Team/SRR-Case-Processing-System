import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, FileText, Bot, User } from 'lucide-react';
import { Message, ChatState, FileSummary } from '../types';
import { processFile, processMultipleFiles, queryCase, BatchProcessingResponse } from '../services/api';
import logoImage from '../images/system_logo.png'; 
import universityLogo from '../images/university_logo.png';
import FileUploadModal from './FileUploadModal';
import FileInfoModal from './FileInfoModal'; 

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
  const [summaryResult, setSummaryResult] = useState<FileSummary | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isFileInfoModalOpen, setIsFileInfoModalOpen] = useState(false);


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

          // Display extracted case data in chat
          const caseData = result.data;
          addMessage('bot', `✅ **File Processing Successful!**

📋 **Extracted Case Information:**

📅 **Date Received:** ${caseData.A_date_received || 'N/A'}
📋 **Source:** ${caseData.B_source || 'N/A'}
🔢 **Case Number:** ${caseData.C_case_number || 'N/A'}
⚡ **Type:** ${caseData.D_type || 'N/A'}
👤 **Caller:** ${caseData.E_caller_name || 'N/A'}
📞 **Contact:** ${caseData.F_contact_no || 'N/A'}
🏗️ **Slope Number:** ${caseData.G_slope_no || 'N/A'}
📍 **Location:** ${caseData.H_location || 'N/A'}
📝 **Nature of Request:** ${caseData.I_nature_of_request || 'N/A'}
🏷️ **Subject Matter:** ${caseData.J_subject_matter || 'N/A'}
⏰ **10-day Due:** ${caseData.K_10day_rule_due_date || 'N/A'}
⏰ **ICC Interim Due:** ${caseData.L_icc_interim_due || 'N/A'}
⏰ **ICC Final Due:** ${caseData.M_icc_final_due || 'N/A'}

💬 **You can now ask me questions about this case, such as:**
• "What is the basic information of this case?"
• "Contact information"
• "Slope-related information"
• "Important dates"
• "Nature of the case"

📊 Click "View Details" to see complete file information and processing status.`);
          

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

  // Note: Drag and drop functionality is now handled in FileUploadModal component

  // Handle keyboard events
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

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
              placeholder={
                chatState.isLoading 
                  ? "Processing..." 
                  : selectedFiles.length > 0 && !chatState.extractedData
                    ? "Click 'Process Files' to start processing or ask questions..."
                    : chatState.extractedData 
                      ? "Ask questions about the case..." 
                      : "Type your message or upload files to get started..."
              }
              disabled={chatState.isLoading}
            />
            
            <div className="input-actions">
              {/* File Upload Button */}
              <button
                className="action-button upload-button"
                onClick={() => setIsUploadModalOpen(true)}
                disabled={chatState.isLoading}
                title="Upload files"
              >
                <Upload size={18} />
              </button>

              {/* Process Files Button (shown when files are selected but not processed) */}
              {selectedFiles.length > 0 && !chatState.extractedData && (
                <button
                  className="action-button process-button"
                  onClick={handleFileUpload}
                  disabled={chatState.isLoading}
                  title="Process selected files"
                >
                  {chatState.isLoading ? (
                    <div className="loading-spinner-small"></div>
                  ) : (
                    <>
                      <Upload size={18} />
                      Process
                    </>
                  )}
                </button>
              )}

              {/* View Details Button (shown when data is extracted) */}
              {chatState.extractedData && (
                <button
                  className="action-button details-button"
                  onClick={() => setIsFileInfoModalOpen(true)}
                  title="View file details"
                >
                  <FileText size={18} />
                </button>
              )}

              {/* Send Button */}
              <button
                className="action-button send-button"
                onClick={handleQuery}
                disabled={!inputMessage.trim() || chatState.isLoading}
                title="Send message"
              >
                <Send size={18} />
              </button>
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
        isLoading={chatState.isLoading}
      />

      {/* File Info Modal */}
      <FileInfoModal
        isOpen={isFileInfoModalOpen}
        onClose={() => setIsFileInfoModalOpen(false)}
        fileInfo={chatState.currentFile}
        extractedData={chatState.extractedData}
        summaryResult={summaryResult}
      />
    </div>
  );
};

export default ChatbotInterface;