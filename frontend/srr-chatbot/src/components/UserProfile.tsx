import React from 'react';
import './UserProfile.css';

// 独立全屏个人中心页面（无组件嵌套，直接作为页面渲染）
const UserProfile = () => {
  return (
    // 根容器：对应 CSS 里的全屏居中容器
    <div className="profile-container">
      {/* 卡片容器：对应 CSS 里的白色卡片样式 */}
      <div className="profile-card">
        {/* 顶部返回按钮（固定在卡片左上角） */}
        <button className="back-btn">← 返回</button>

        {/* 中间头像核心区域（复用 CSS 里的头像样式） */}
        <div className="profile-header">
          <div className="profile-avatar">
            <img 
              src="https://picsum.photos/180/180" 
              alt="用户头像" 
              style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }}
            />
            {/* 更换头像按钮（悬浮显示） */}
            <div className="avatar-change">更换头像</div>
          </div>
        </div>

        {/* 功能按钮组（复用 CSS 里的按钮样式） */}
        <div className="profile-actions">
          <button className="profile-btn secondary-btn">修改密码</button>
          <button className="profile-btn logout-btn">注销账号</button>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;