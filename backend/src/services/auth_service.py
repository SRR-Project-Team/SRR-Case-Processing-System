#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证服务模块

本模块提供用户认证相关功能，包括：
1. 密码哈希和验证（使用bcrypt）
2. JWT token生成和验证
3. 用户登录验证

技术栈：
- passlib: 密码哈希
- python-jose: JWT处理

作者: Project3 Team
版本: 1.0
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os

# 密码上下文配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置（从环境变量读取，如果没有则使用默认值）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-please-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 默认24小时


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码匹配返回True，否则返回False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"❌ 密码验证失败: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码到token中的数据（通常包含用户标识）
        expires_delta: token过期时间，默认使用配置的过期时间
        
    Returns:
        str: JWT token字符串
        
    Example:
        token = create_access_token({"sub": "1234567890"})
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        print(f"❌ JWT编码失败: {e}")
        raise e


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT访问令牌
    
    Args:
        token: JWT token字符串
        
    Returns:
        Optional[Dict[str, Any]]: 解码后的数据，失败返回None
        
    Example:
        payload = decode_access_token(token)
        if payload:
            phone_number = payload.get("sub")
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"❌ JWT解码失败: {e}")
        return None
    except Exception as e:
        print(f"❌ Token验证异常: {e}")
        return None


def verify_token(token: str) -> Optional[str]:
    """
    验证token并返回用户电话号码
    
    Args:
        token: JWT token字符串
        
    Returns:
        Optional[str]: 用户电话号码，失败返回None
    """
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    phone_number: str = payload.get("sub")
    if phone_number is None:
        return None
    
    return phone_number
