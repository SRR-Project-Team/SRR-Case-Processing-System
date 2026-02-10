"""
data库model定义module

本module定义SRR案件process系统的data库model，使用SQLAlchemy ORM框架
进行data库操作。model严格按照A-Qfield规范设计，确保data一致性。

mainfunction：
1. 定义SRR案件datatable结构
2. mapA-Qfield到data库列
3. configuration时间戳和索引
4. 支持软delete和审计function

datamodel特点：
- 18个A-Qfield完整map
- 北京时间时区支持
- automatic时间戳管理
- 软delete机制
- 系统审计field

作者: Project3 Team
版本: 2.1
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import pytz
import json

# createSQLAlchemy基础class
Base = declarative_base()

class User(Base):
    """
    用户数据表model
    
    用于存储系统用户信息，支持：
    - 电话号码作为主键（唯一标识）
    - 密码哈希存储（bcrypt）
    - 基本用户信息（姓名、部门、角色、邮箱）
    - 角色管理（admin, user, viewer）
    
    table名: users
    主键: phone_number (电话号码)
    """
    __tablename__ = "users"
    
    phone_number = Column(String(20), primary_key=True)  # 电话号码作为主键
    password_hash = Column(String(255), nullable=False)  # 密码哈希
    full_name = Column(String(100))  # 全名
    department = Column(String(100))  # 部门
    role = Column(String(50), default='user')  # 角色: admin, user, viewer
    email = Column(String(100))  # 邮箱
    is_active = Column(Boolean, default=True)  # 是否激活
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))


class ChatSession(Base):
    """
    聊天会话数据表model
    
    用于存储用户的聊天会话元数据，支持：
    - 会话管理（创建、删除、重命名）
    - 空会话持久化
    - 会话时间戳
    
    table名: chat_sessions
    主键: session_id (UUID字符串)
    """
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(50), primary_key=True)
    user_phone = Column(String(20), ForeignKey('users.phone_number'), nullable=False)
    title = Column(String(100), nullable=True)  # 会话标题（可选，未来支持自动生成）
    is_active = Column(Boolean, default=True)   # 软删除标记
    
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))


class SRRCase(Base):
    """
    SRR案件datatablemodel
    
    映射SRR案件的所有field到data库table，包括：
    - A-Qfield：18个核心业务field
    - 系统field：ID、时间戳、状态等
    - 元datafield：文件名、文件class型、process时间等
    
    table名: srr_cases
    主键: id (自增整数)
    """
    __tablename__ = "srr_cases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # A-Qfield (对应StructuredCaseData)
    A_date_received = Column(String(50))
    B_source = Column(String(50))
    C_case_number = Column(String(50))
    D_type = Column(String(50))
    E_caller_name = Column(String(100))
    F_contact_no = Column(String(50))
    G_slope_no = Column(String(50))
    H_location = Column(String(200))
    I_nature_of_request = Column(Text)
    J_subject_matter = Column(String(100))
    K_10day_rule_due_date = Column(String(50))
    L_icc_interim_due = Column(String(50))
    M_icc_final_due = Column(String(50))
    N_works_completion_due = Column(String(50))
    O1_fax_to_contractor = Column(String(50))
    O2_email_send_time = Column(String(50))
    P_fax_pages = Column(String(50))
    Q_case_details = Column(Text)
    
    # AI 與相似案件 field（案件詳情中體現並記錄）
    ai_summary = Column(Text, nullable=True)  # AI 生成摘要
    similar_historical_cases = Column(Text, nullable=True)  # 相似歷史案件 (JSON 格式)
    location_statistics = Column(Text, nullable=True)  # 地點統計 (JSON 格式)
    
    # 系统field
    original_filename = Column(String(255))
    file_type = Column(String(20))  # txt, tmo, rcc
    file_hash = Column(String(64), unique=True, nullable=True)  # SHA256哈希值用于去重
    uploaded_by = Column(String(20), ForeignKey('users.phone_number'), nullable=True)  # 上传者
    processing_time = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    is_active = Column(Boolean, default=True)


class ConversationHistory(Base):
    """
    对话历史数据表model
    
    用于存储回复草稿生成过程中的多轮对话历史，支持：
    - Interim reply 对话历史
    - Final reply 对话历史
    - Wrong referral reply 对话历史
    
    table名: conversation_history
    主键: id (自增整数)
    外键: case_id (关联到srr_cases表)
    """
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联用户
    user_phone = Column(String(20), ForeignKey('users.phone_number'), nullable=True)  # 关联用户（可为空以兼容旧数据）
    
    # 关联案件
    case_id = Column(Integer, ForeignKey('srr_cases.id'), nullable=False)
    
    # 对话类型
    conversation_type = Column(String(50), nullable=False)  # interim_reply, final_reply, wrong_referral_reply
    
    # 对话历史 (JSON格式存储)
    # 格式: [{"role": "user"/"assistant", "content": "...", "timestamp": "...", "language": "zh"/"en"}]
    messages = Column(Text, default='[]')
    
    # 对话语言
    language = Column(String(10), default='zh')  # zh, en
    
    # 生成的草稿回复
    draft_reply = Column(Text, nullable=True)
    
    # 对话状态
    status = Column(String(20), default='pending')  # pending, in_progress, completed
    
    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    
    def get_messages(self):
        """获取解析后的消息列表"""
        if self.messages:
            try:
                return json.loads(self.messages)
            except:
                return []
        return []
    
    def set_messages(self, messages_list):
        """设置消息列表"""
        self.messages = json.dumps(messages_list, ensure_ascii=False)
    
    def add_message(self, role, content, language='zh'):
        """添加新消息到对话历史"""
        messages = self.get_messages()
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(pytz.timezone('Asia/Shanghai')).isoformat(),
            "language": language
        })
        self.set_messages(messages)


class KnowledgeBaseFile(Base):
    """
    知识库文件数据表model
    
    用于存储RAG增强检索的知识库文件，支持：
    - Excel, Word, PowerPoint, PDF, TXT, CSV, 图片等多种文件类型
    - 文件元数据管理
    - 向量化处理状态追踪
    
    table名: knowledge_base_files
    主键: id (自增整数)
    """
    __tablename__ = "knowledge_base_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 文件基本信息
    filename = Column(String(255), nullable=False)  # 原始文件名
    file_type = Column(String(50), nullable=False)  # excel, word, powerpoint, pdf, txt, csv, image
    file_path = Column(String(500), nullable=False)  # 文件存储路径
    file_size = Column(Integer, nullable=False)  # 文件大小(bytes)
    mime_type = Column(String(100), nullable=False)  # MIME类型
    
    # 处理状态
    upload_time = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    processed = Column(Boolean, default=False)  # 是否已处理
    processing_error = Column(Text, nullable=True)  # 处理错误信息
    
    # 向量化信息
    chunk_count = Column(Integer, default=0)  # 文本块数量
    vector_ids = Column(Text, default='[]')  # SurrealDB中的向量ID列表(JSON格式)
    
    # 预览和元数据
    preview_text = Column(Text, nullable=True)  # 预览文本(前500字符)
    file_metadata = Column(Text, default='{}')  # 其他元数据(JSON格式: 页数、sheets等)
    
    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    is_active = Column(Boolean, default=True)  # 软删除标记
    
    def get_vector_ids(self):
        """获取解析后的向量ID列表"""
        if self.vector_ids:
            try:
                return json.loads(self.vector_ids)
            except:
                return []
        return []
    
    def set_vector_ids(self, ids_list):
        """设置向量ID列表"""
        self.vector_ids = json.dumps(ids_list, ensure_ascii=False)
    
    def get_metadata(self):
        """获取解析后的元数据"""
        if self.file_metadata:
            try:
                return json.loads(self.file_metadata)
            except:
                return {}
        return {}
    
    def set_metadata(self, metadata_dict):
        """设置元数据"""
        self.file_metadata = json.dumps(metadata_dict, ensure_ascii=False)


class ChatMessage(Base):
    """
    聊天消息数据表model
    
    用于存储用户与系统的普通对话消息，支持：
    - 按用户分组消息
    - 按会话（session）组织消息
    - 关联案件（可选）
    - 存储文件信息
    
    table名: chat_messages
    主键: id (自增整数)
    外键: user_phone (关联到users表), case_id (关联到srr_cases表，可选)
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联用户
    user_phone = Column(String(20), ForeignKey('users.phone_number'), nullable=False)
    
    # 会话信息
    session_id = Column(String(50), nullable=False)  # 会话ID，用于分组消息
    
    # 消息内容
    message_type = Column(String(10), nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)  # 消息内容
    
    # 关联信息（可选）
    case_id = Column(Integer, ForeignKey('srr_cases.id'), nullable=True)  # 关联案件（可选）
    file_info = Column(Text, nullable=True)  # JSON格式的文件信息
    
    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    
    def get_file_info(self):
        """获取解析后的文件信息"""
        if self.file_info:
            try:
                return json.loads(self.file_info)
            except:
                return None
        return None
    
    def set_file_info(self, file_info_dict):
        """设置文件信息"""
        if file_info_dict:
            self.file_info = json.dumps(file_info_dict, ensure_ascii=False)
        else:
            self.file_info = None
