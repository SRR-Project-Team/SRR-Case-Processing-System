from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .users import Base, User
import os

# 用户数据库管理器类
class UserDatabaseManager:
    
    # 构造函数
    def __init__(self, db_path="data/users.db"):
        # 确保使用绝对路径，避免相对路径问题
        if not os.path.isabs(db_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            db_path = os.path.join(project_root, db_path)
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        Base.metadata.create_all(bind=self.engine)
        print(f"数据库初始化完成: {db_path}")

    # 查看数据库会话
    def get_session(self):
        return self.SessionLocal()
    
    # 保存用户数据
    def save_user(self, user_data: dict) -> int:
        session = self.get_session()
        try:
            user = User(**user_data)
            session.add(user)
            session.commit()
            user_id = user.id
            print(f"成功创建用户账号：用户ID-{user_id}")
            return user_id
        except Exception as e:
            session.rollback()
            print(f"用户信息保存失败: {e}")
            raise e
        finally:
            session.close()
    
    # 获取用户数据
    def get_user(self, email: str, password: str) -> dict:
        session = self.get_session()
        try:
            # 根据 email 查询用户
            user = session.query(User).filter(User.email == email).first()
            # 检查用户是否存在且密码匹配
            if user and user.password == password:
                return self._user_to_dict(user)
            # 找不到用户或密码不匹配
            return None
        finally:
            session.close()

    # ID获取用户数据
    def get_user_by_ID(self, id : int) -> dict:
        session = self.get_session()
        try:
            # 根据 id 查询用户
            user = session.query(User).filter(User.id == id).first()
            # 检查用户是否存在
            if user:
                return self._user_to_dict(user)
            # 找不到用户
            return None
        except Exception as e:
            raise e
        finally:
            session.close()
    
    # 将用户数据转化为字典形式
    def _user_to_dict(self, user) -> dict:
        return {
            'id': user.id,
            'username' : user.username,
            'email' : user.email,
            'phone' : user.phone
        }
    

# 全局用户数据库管理器实例对象
_user_db_manager = None

# 用户数据库实例
def get_user_db_manager():
    global _user_db_manager
    if _user_db_manager is None:
        _user_db_manager = UserDatabaseManager()
    return _user_db_manager
