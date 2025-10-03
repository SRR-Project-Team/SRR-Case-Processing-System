"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import pytz

Base = declarative_base()

class SRRCase(Base):
    """SRR案件数据表"""
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
