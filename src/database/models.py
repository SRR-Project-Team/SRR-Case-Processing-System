"""
数据库模型定义模块

本模块定义SRR案件处理系统的数据库模型，使用SQLAlchemy ORM框架
进行数据库操作。模型严格按照A-Q字段规范设计，确保数据一致性。

主要功能：
1. 定义SRR案件数据表结构
2. 映射A-Q字段到数据库列
3. 配置时间戳和索引
4. 支持软删除和审计功能

数据模型特点：
- 18个A-Q字段完整映射
- 北京时间时区支持
- 自动时间戳管理
- 软删除机制
- 系统审计字段

作者: Project3 Team
版本: 2.0
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import pytz

# 创建SQLAlchemy基础类
Base = declarative_base()

class SRRCase(Base):
    """
    SRR案件数据表模型
    
    映射SRR案件的所有字段到数据库表，包括：
    - A-Q字段：18个核心业务字段
    - 系统字段：ID、时间戳、状态等
    - 元数据字段：文件名、文件类型、处理时间等
    
    表名: srr_cases
    主键: id (自增整数)
    """
    __tablename__ = "srr_cases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # A-Q字段 (对应StructuredCaseData)
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
    
    # 系统字段
    original_filename = Column(String(255))
    file_type = Column(String(20))  # txt, tmo, rcc
    processing_time = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    is_active = Column(Boolean, default=True)
