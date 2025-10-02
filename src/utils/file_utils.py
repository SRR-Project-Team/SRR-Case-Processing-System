#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具模块
提供智能编码检测和文件读取功能
"""

import chardet
import os
from typing import Optional


def detect_file_encoding(file_path: str) -> str:
    """
    智能检测文件编码格式
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 检测到的编码格式
    """
    # 1. 检查BOM标记
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(4)
            
        # UTF-8 BOM
        if raw_data.startswith(b'\xef\xbb\xbf'):
            print("🔍 检测到UTF-8 BOM")
            return 'utf-8-sig'
        # UTF-16 LE BOM
        elif raw_data.startswith(b'\xff\xfe'):
            print("🔍 检测到UTF-16 LE BOM")
            return 'utf-16-le'
        # UTF-16 BE BOM
        elif raw_data.startswith(b'\xfe\xff'):
            print("🔍 检测到UTF-16 BE BOM")
            return 'utf-16-be'
    except Exception as e:
        print(f"⚠️ BOM检测失败: {e}")
    
    # 2. 使用chardet检测
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        result = chardet.detect(raw_data)
        if result and result['encoding']:
            confidence = result['confidence']
            encoding = result['encoding']
            print(f"🔍 chardet检测到编码: {encoding} (置信度: {confidence:.2f})")
            
            # 如果置信度较高，直接使用
            if confidence > 0.7:
                return encoding
            
    except Exception as e:
        print(f"⚠️ chardet检测失败: {e}")
    
    # 3. 尝试常见编码
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'big5', 'latin1', 'cp1252']
    
    for encoding in common_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1024)  # 尝试读取前1024字符
            print(f"🔍 成功验证编码: {encoding}")
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"⚠️ 编码 {encoding} 测试失败: {e}")
            continue
    
    # 4. 默认返回UTF-8
    print("⚠️ 无法确定编码，使用UTF-8作为默认")
    return 'utf-8'


def read_file_with_encoding(file_path: str) -> str:
    """
    使用智能编码检测读取文件内容
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 文件内容
        
    Raises:
        FileNotFoundError: 文件不存在
        Exception: 读取失败
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 检测编码
    detected_encoding = detect_file_encoding(file_path)
    
    # 尝试使用检测到的编码读取
    encodings_to_try = [detected_encoding]
    
    # 添加备用编码
    backup_encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1', 'cp1252']
    for enc in backup_encodings:
        if enc not in encodings_to_try:
            encodings_to_try.append(enc)
    
    last_error = None
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                content = f.read()
            print(f"✅ 使用 {encoding} 编码读取文件成功，文本长度: {len(content)} 字符")
            return content
            
        except UnicodeDecodeError as e:
            last_error = e
            print(f"⚠️ 编码 {encoding} 读取失败: {e}")
            continue
        except Exception as e:
            last_error = e
            print(f"⚠️ 使用编码 {encoding} 时发生错误: {e}")
            continue
    
    # 最后尝试忽略错误的方式读取
    try:
        print("🔄 尝试忽略编码错误的方式读取...")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        print(f"⚠️ 使用错误忽略模式读取成功，文本长度: {len(content)} 字符")
        return content
    except Exception as e:
        print(f"❌ 错误忽略模式也失败: {e}")
    
    # 如果所有方法都失败，抛出异常
    raise Exception(f"无法读取文件 {file_path}，最后错误: {last_error}")


def safe_file_read(file_path: str, default_content: str = "") -> str:
    """
    安全读取文件，失败时返回默认内容
    
    Args:
        file_path (str): 文件路径
        default_content (str): 默认内容
        
    Returns:
        str: 文件内容或默认内容
    """
    try:
        return read_file_with_encoding(file_path)
    except Exception as e:
        print(f"⚠️ 文件读取失败，使用默认内容: {e}")
        return default_content
