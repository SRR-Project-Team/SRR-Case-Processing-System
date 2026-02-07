import React, { useState, useEffect } from 'react';
import axios from 'axios'; // 导入axios
import './HistorySession.css';

// 历史会话记录子组件
const HistorySession: React.FC = () => {

  // 地址
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

  // 对话框数量

  const [sessionCount, setSessionCount] = useState<number[]>([]);

  // 生成对应数量的会话记录框
  const renderSessionItems = () => {
    const items = [];
    // 删除按钮
    for (let i = 0; i <= sessionCount.length-1; i++) {
      items.push(
        <div key={sessionCount[i]} className="history-session-item" onClick={(e) => handleSelectSession(i, e)}>
          Session {sessionCount[i]}
          <span className="delete-btn" onClick={(e) => handleDeleteSession(i, e)}> × </span>
        </div>
      );
    }
    return items;
  };

  // 选择对话框
  const handleSelectSession = (index: number, e: React.MouseEvent) => {
    console.log(sessionCount[index]);
  }

  // 新建对话框
  const handleNewSession = () => {
    const newSessionCount = [...sessionCount];
    if (newSessionCount.length === 0){
      setSessionCount([1]);
    }else{
      const lastNum = newSessionCount[newSessionCount.length - 1];
      const nextNum = lastNum + 1;
      newSessionCount.push(nextNum);
      setSessionCount(newSessionCount);
    }
    console.log('Add Session:', sessionCount);
  };

  // 删除对话框
  const handleDeleteSession = (index: number, e: React.MouseEvent) => {
    const newSessionCount = [...sessionCount];
    newSessionCount.splice(index, 1);
    setSessionCount(newSessionCount);
    console.log('Delete Session:', sessionCount[index]);
  };

  return (
    <div className="history-container">
      {/* 标题 */}
      <div className="history-title">Historical Records</div>
      {/* 添加新会话 */}
      <div className="history-new-session" onClick={handleNewSession}>
        <span className="history-add-new-session"> + New Session </ span>
      </div>
      {/* 会话框 */}
      <div className="history-session-list">
        {renderSessionItems()}
      </div>
    </div>
  );
};

export default HistorySession;