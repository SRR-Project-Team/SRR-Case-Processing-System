from pydantic import BaseModel
import hashlib
from typing import Optional, Dict, Any

# 用户信息结构化数据
class StructuredUserData(BaseModel):
    # 用户数据类型
    username: str = ""
    email: str = ""
    phone: str = ""
    password: str = ""
    confirmPassword: str = ""

# 后端返回信息结构化数据
class UserProcessingResult(BaseModel):
    status: str = ""
    message: str = ""
    structured_data: Optional[Dict] = None

# 校验用户数据是否存在空字段
def validate_user_data(user_data: StructuredUserData) -> UserProcessingResult | None:
    try:
        # 遍历所有字段和值
        for field_name, value in user_data.model_dump().items():
            if not value.strip():
                return UserProcessingResult(status = "error",
                                            message = "Error: The field '{field_name}' cannot be empty!")
        return None
    except Exception as e:
        raise e

# 密码转Hash值
def hash_password_in_model(model_instance: StructuredUserData) -> dict:
    try:
        hash_obj = hashlib.sha256(model_instance.password.encode("utf-8"))
        hashed_password = hash_obj.hexdigest()
        model_instance.password = str(hashed_password)
        print(model_instance.password)
        return StructuredUserData_to_dict(model_instance)
    except Exception as e:
        raise e

# StructuredUserData转成字典
def StructuredUserData_to_dict(user : StructuredUserData) -> dict:
    return {
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "password": user.password
    }