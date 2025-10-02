import React, { useState, useRef, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Send, Upload, FileText, Bot, User } from 'lucide-react';
import { Message, ChatState } from '../types';
import { processFile, processMultipleFiles, queryCase, BatchProcessingResponse } from '../services/api';
import ExtractedInfoDisplay from './ExtractedInfoDisplay';

const ChatbotInterface: React.FC = () => {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [
      {
        id: '1',
        type: 'bot',
        content: '您好！我是SRR案件处理助手。请上传PDF或TXT文件（支持多文件批量处理），我将为您提取案件信息并回答相关问题。',
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

  // 自动滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatState.messages]);

  // 添加消息
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

  // 处理文件选择 (不立即处理，只选择文件)
  const handleFileSelection = (files: File[]) => {
    if (files.length === 0) return;

    // 验证文件类型和大小
    const allowedTypes = ['text/plain', 'application/pdf'];
    const maxSize = 10 * 1024 * 1024; // 10MB限制
    
    const invalidFiles = files.filter(file => 
      !allowedTypes.includes(file.type) || file.size > maxSize
    );
    
    if (invalidFiles.length > 0) {
      const errorMsg = invalidFiles.map(file => {
        if (!allowedTypes.includes(file.type)) {
          return `${file.name}: 不支持的文件类型`;
        }
        if (file.size > maxSize) {
          return `${file.name}: 文件大小超过10MB限制`;
        }
        return `${file.name}: 未知错误`;
      }).join('\n');
      
      addMessage('bot', `以下文件无法处理：\n${errorMsg}\n\n只支持TXT和PDF文件，且文件大小不超过10MB。`);
      
      // 过滤掉无效文件
      const validFiles = files.filter(file => 
        allowedTypes.includes(file.type) && file.size <= maxSize
      );
      
      if (validFiles.length === 0) return;
      files = validFiles;
    }

    // 累加到现有文件列表（避免重复）
    const newFiles = files.filter(newFile => 
      !selectedFiles.some(existingFile => 
        existingFile.name === newFile.name && existingFile.size === newFile.size
      )
    );
    
    if (newFiles.length === 0) {
      addMessage('bot', '所选文件已存在于列表中。');
      return;
    }
    
    setSelectedFiles(prev => [...prev, ...newFiles]);
    
    // 显示文件选择消息
    if (newFiles.length === 1) {
      addMessage('user', `添加文件: ${newFiles[0].name}`, {
        name: newFiles[0].name,
        size: newFiles[0].size,
        type: newFiles[0].type,
      });
    } else {
      const fileNames = newFiles.map(f => f.name).join(', ');
      addMessage('user', `添加 ${newFiles.length} 个文件: ${fileNames}`);
    }
    
    // 显示当前总文件数
    const totalFiles = selectedFiles.length + newFiles.length;
    if (totalFiles === 1) {
      addMessage('bot', '文件已添加到列表，点击"开始处理"按钮来处理文件。');
    } else {
      addMessage('bot', `当前共有 ${totalFiles} 个文件，点击"开始批量处理"按钮来处理所有文件。`);
    }
  };

  // 处理文件上传 (实际处理选中的文件)
  const handleFileUpload = async () => {
    const files = selectedFiles;
    if (files.length === 0) {
      addMessage('bot', '请先选择要处理的文件。');
      return;
    }

    // 单文件处理
    if (files.length === 1) {
      const file = files[0];
      const fileInfo = {
        name: file.name,
        size: file.size,
        type: file.type,
      };

      addMessage('user', `上传文件: ${file.name}`, fileInfo);

      // 根据文件类型提供不同的处理提示
      let processingMessage = '正在处理您的文件，请稍候...';
      if (file.name.toLowerCase().startsWith('rcc') && file.type === 'application/pdf') {
        processingMessage = '正在处理RCC PDF文件，由于需要进行OCR识别，可能需要1-2分钟，请耐心等待...';
      } else if (file.type === 'application/pdf') {
        processingMessage = '正在处理PDF文件，请稍候...';
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

          addMessage('bot', `文件处理成功！我已经提取了案件信息。您可以在右侧查看详细信息，或者询问我关于这个案件的任何问题。

例如，您可以问：
• "这个案件的基本信息是什么？"
• "联系人信息"
• "斜坡相关信息"
• "重要日期"
• "案件性质"`);
          
          // 清空选中的文件列表
          setSelectedFiles([]);
        } else {
          setChatState(prev => ({ ...prev, isLoading: false }));
          addMessage('bot', `文件处理失败: ${result.message || result.error || '未知错误'}`);
          // 处理失败时也清空文件列表
          setSelectedFiles([]);
        }
      } catch (error) {
        setChatState(prev => ({ ...prev, isLoading: false }));
        addMessage('bot', `处理文件时发生错误: ${error instanceof Error ? error.message : '未知错误'}`);
        // 处理出错时也清空文件列表
        setSelectedFiles([]);
      }
    } 
    // 多文件批量处理
    else {
      const fileNames = files.map(f => f.name).join(', ');
      addMessage('user', `批量上传 ${files.length} 个文件: ${fileNames}`);
      
      addMessage('bot', `正在批量处理 ${files.length} 个文件，请耐心等待...
      
${files.some(f => f.name.toLowerCase().startsWith('rcc')) ? 
  '⚠️ 检测到RCC文件，OCR处理可能需要较长时间。' : ''}`);

      setChatState(prev => ({
        ...prev,
        isLoading: true,
        currentFile: { name: `${files.length} 个文件`, size: 0, type: 'batch' },
      }));

      try {
        const result: BatchProcessingResponse = await processMultipleFiles(files);
        
        setChatState(prev => ({
          ...prev,
          isLoading: false,
        }));

        // 显示批量处理结果
        const successFiles = result.results.filter(r => r.status === 'success');
        const failedFiles = result.results.filter(r => r.status === 'error');
        
        let resultMessage = `📊 批量处理完成！
        
📈 处理统计:
• 总文件数: ${result.total_files}
• 成功处理: ${result.successful} 个
• 处理失败: ${result.failed} 个`;

        if (successFiles.length > 0) {
          resultMessage += `\n\n✅ 成功处理的文件:
${successFiles.map(f => `• ${f.filename}`).join('\n')}`;
        }

        if (failedFiles.length > 0) {
          resultMessage += `\n\n❌ 处理失败的文件:
${failedFiles.map(f => `• ${f.filename}: ${f.message}`).join('\n')}`;
        }

        if (successFiles.length > 0) {
          resultMessage += `\n\n💡 提示: 由于批量处理了多个文件，右侧信息面板显示最后一个成功处理的文件。您可以询问特定文件的信息。`;
          
          // 设置最后一个成功文件的数据到右侧面板
          const lastSuccessFile = successFiles[successFiles.length - 1];
          if (lastSuccessFile.structured_data) {
            setChatState(prev => ({
              ...prev,
              extractedData: lastSuccessFile.structured_data,
            }));
          }
        }

        addMessage('bot', resultMessage);
        
        // 批量处理完成后清空文件列表
        setSelectedFiles([]);
        
      } catch (error) {
        setChatState(prev => ({
          ...prev,
          isLoading: false,
        }));
        
        addMessage('bot', `批量处理文件时发生错误: ${error instanceof Error ? error.message : '未知错误'}`);
        
        // 处理出错时也清空文件列表
        setSelectedFiles([]);
      }
    }
  };

  // 处理用户查询
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
      addMessage('bot', `查询失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  // 拖拽上传配置 (支持多文件)
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileSelection,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 10, // 最多支持10个文件
    multiple: true, // 支持多文件选择
  });

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  return (
    <div className="chatbot-container">
      {/* 左侧聊天区域 */}
      <div className="chat-section">
        <div className="chat-header">
          <h1>SRR案件处理助手</h1>
          <p>智能文件处理与案件查询系统</p>
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
                  处理中...
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
              placeholder={chatState.extractedData ? "询问案件相关问题..." : "请先上传文件..."}
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

      {/* 右侧信息展示区域 */}
      <div className="info-section">
        <div className="info-header">
          <h2>文件处理</h2>
          <p>拖拽或点击上传PDF/TXT文件 (支持多文件)</p>
        </div>

        <div className="info-content">
          {/* 文件上传区域 */}
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            <div className="dropzone-content">
              <Upload size={32} className="dropzone-icon" />
              <div className="dropzone-text">
                {isDragActive ? (
                  <span>放下文件以添加到列表</span>
                ) : (
                  <>
                    <strong>点击或拖拽文件到此处添加</strong>
                    <br />
                    支持 PDF 和 TXT 格式 (可多次添加文件)
                    <br />
                    <small>最大文件大小: 10MB，最多10个文件</small>
                    <br />
                    <small style={{color: '#666', marginTop: '5px'}}>可多次选择文件累加到列表，然后点击"开始处理"</small>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* 选中文件列表和确认按钮 */}
          {selectedFiles.length > 0 && (
            <div className="selected-files-section">
              <h3>
                <FileText size={16} />
                已选择的文件 ({selectedFiles.length})
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
                          addMessage('bot', '已清空文件选择。');
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
                  {chatState.isLoading ? '处理中...' : 
                    selectedFiles.length === 1 ? '开始处理' : `开始批量处理 (${selectedFiles.length} 个文件)`
                  }
                </button>
                <button 
                  className="clear-files-btn"
                  onClick={() => {
                    setSelectedFiles([]);
                    addMessage('bot', '已清空文件选择。');
                  }}
                  disabled={chatState.isLoading}
                >
                  清空选择
                </button>
              </div>
            </div>
          )}

          {/* 当前文件信息 */}
          {chatState.currentFile && (
            <div className="extracted-info">
              <h3>
                <FileText size={16} />
                当前文件
              </h3>
              <div className="info-item">
                <div className="info-label">文件名</div>
                <div className="info-value">{chatState.currentFile.name}</div>
              </div>
              <div className="info-item">
                <div className="info-label">大小</div>
                <div className="info-value">
                  {(chatState.currentFile.size / 1024).toFixed(1)} KB
                </div>
              </div>
              <div className="info-item">
                <div className="info-label">类型</div>
                <div className="info-value">{chatState.currentFile.type}</div>
              </div>
            </div>
          )}

          {/* 提取的信息展示 */}
          {chatState.extractedData && (
            <ExtractedInfoDisplay data={chatState.extractedData} />
          )}

          {/* 状态提示 */}
          {chatState.isLoading && (
            <div className="loading">
              <div className="loading-spinner"></div>
              正在处理文件...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatbotInterface;
