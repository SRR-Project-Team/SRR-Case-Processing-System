"""
data库manager
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, SRRCase
import os
from datetime import datetime
import pytz

class DatabaseManager:
    """data库管理器"""
    
    def __init__(self, db_path="data/srr_cases.db"):
        # 确保使用绝对路径，避免相对路径问题
        if not os.path.isabs(db_path):
            # get项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            db_path = os.path.join(project_root, db_path)
        
        # 确保data目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # createtable
        Base.metadata.create_all(bind=self.engine)
        print(f"✅ data库initialize完成: {db_path}")
    
    def get_session(self):
        """获取data库session"""
        return self.SessionLocal()
    
    def save_case(self, case_data: dict) -> int:
        """保存案件data"""
        session = self.get_session()
        try:
            case = SRRCase(**case_data)
            session.add(case)
            session.commit()
            case_id = case.id
            print(f"✅ 案件保存success，ID: {case_id}")
            return case_id
        except Exception as e:
            session.rollback()
            print(f"❌ 案件保存failed: {e}")
            raise e
        finally:
            session.close()
    
    def get_case(self, case_id: int) -> dict:
        """获取单个案件"""
        session = self.get_session()
        try:
            case = session.query(SRRCase).filter(SRRCase.id == case_id).first()
            if case:
                return self._case_to_dict(case)
            return None
        finally:
            session.close()
    
    def get_cases(self, limit=100, offset=0) -> list:
        """获取案件列table"""
        session = self.get_session()
        try:
            cases = session.query(SRRCase).filter(SRRCase.is_active == True)\
                .order_by(SRRCase.created_at.desc())\
                .offset(offset).limit(limit).all()
            return [self._case_to_dict(case) for case in cases]
        finally:
            session.close()
    
    def search_cases(self, keyword: str) -> list:
        """搜索案件"""
        session = self.get_session()
        try:
            cases = session.query(SRRCase).filter(
                SRRCase.is_active == True,
                (SRRCase.E_caller_name.contains(keyword) |
                 SRRCase.G_slope_no.contains(keyword) |
                 SRRCase.H_location.contains(keyword) |
                 SRRCase.I_nature_of_request.contains(keyword))
            ).all()
            return [self._case_to_dict(case) for case in cases]
        finally:
            session.close()
    
    def get_stats(self) -> dict:
        """获取统计information"""
        session = self.get_session()
        try:
            total_cases = session.query(SRRCase).filter(SRRCase.is_active == True).count()
            txt_cases = session.query(SRRCase).filter(SRRCase.file_type == 'txt').count()
            tmo_cases = session.query(SRRCase).filter(SRRCase.file_type == 'tmo').count()
            rcc_cases = session.query(SRRCase).filter(SRRCase.file_type == 'rcc').count()
            
            return {
                'total_cases': total_cases,
                'txt_cases': txt_cases,
                'tmo_cases': tmo_cases,
                'rcc_cases': rcc_cases
            }
        finally:
            session.close()
    
    def _case_to_dict(self, case) -> dict:
        """将案件object转换为字典"""
        return {
            'id': case.id,
            'A_date_received': case.A_date_received,
            'B_source': case.B_source,
            'C_case_number': case.C_case_number,
            'D_type': case.D_type,
            'E_caller_name': case.E_caller_name,
            'F_contact_no': case.F_contact_no,
            'G_slope_no': case.G_slope_no,
            'H_location': case.H_location,
            'I_nature_of_request': case.I_nature_of_request,
            'J_subject_matter': case.J_subject_matter,
            'K_10day_rule_due_date': case.K_10day_rule_due_date,
            'L_icc_interim_due': case.L_icc_interim_due,
            'M_icc_final_due': case.M_icc_final_due,
            'N_works_completion_due': case.N_works_completion_due,
            'O1_fax_to_contractor': case.O1_fax_to_contractor,
            'O2_email_send_time': case.O2_email_send_time,
            'P_fax_pages': case.P_fax_pages,
            'Q_case_details': case.Q_case_details,
            'original_filename': case.original_filename,
            'file_type': case.file_type,
            'processing_time': self._format_beijing_time(case.processing_time),
            'created_at': self._format_beijing_time(case.created_at)
        }
    
    def _format_beijing_time(self, dt):
        """格式化北京时间为友好显示"""
        if dt is None:
            return None
        
        # 如果已经是带时区的时间，转换为北京时间
        if dt.tzinfo is not None:
            beijing_tz = pytz.timezone('Asia/Shanghai')
            beijing_time = dt.astimezone(beijing_tz)
        else:
            # 如果是naive时间，假设已经是北京时间
            beijing_tz = pytz.timezone('Asia/Shanghai')
            beijing_time = beijing_tz.localize(dt)
        
        return beijing_time.strftime('%Y-%m-%d %H:%M:%S CST')

# 全局data库managerinstance
_db_manager = None

def get_db_manager():
    """获取data库管理器instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
