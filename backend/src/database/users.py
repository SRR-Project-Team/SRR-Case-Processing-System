from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import pytz

# 复用SQLAlchemy基础class（和SRRCase共用同一个Base）
Base = declarative_base()

class User(Base):
    # 表名
    __tablename__ = "users"
    
    # 主键ID自增长
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 核心用户字段
    username = Column(String(50), nullable=False, unique=False)  # 用户名，非空，长度限制50
    email = Column(String(100), nullable=False, unique=False)  # 用户邮箱，非空, 长度限制100
    phone = Column(String(20), nullable=False, unique=False)       # 用户电话号码，非空，长度限制20
    password = Column(String(255), nullable=False, unique=False)  # 用户密码，非空，预留足够长度存加密密码
    
    # 系统字段
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai'))) # 创建时间（北京时间）
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Shanghai'))) # 更新时间（北京时间）
    is_active = Column(Boolean, default=True) # 是否激活（软删除标识）