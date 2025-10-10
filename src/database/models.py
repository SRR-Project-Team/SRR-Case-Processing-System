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
版本: 2.0
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import pytz

# createSQLAlchemy基础class
Base = declarative_base()

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
    
    # 系统field
    original_filename = Column(String(255))
    file_type = Column(String(20))  # txt, tmo, rcc
    processing_time = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    is_active = Column(Boolean, default=True)
