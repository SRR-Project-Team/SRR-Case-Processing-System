#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fileprocessutilitymodule

本module提供智能的fileencoding检测和securityfilereadfunction，专门用于process
各种encoding格式的文本file，特别是中文文档和邮件内容。

mainfunction：
1. 智能encoding检测（支持BOM、chardet、常见encoding）
2. securityfileread（automaticencoding检测 + errorprocess）
3. 多encoding格式支持（UTF-8、GBK、GB2312、Big5等）
4. error恢复机制（encodingfailed时的降级process）

技术特点：
- 基于chardet库的智能encoding检测
- 支持BOM标记识别
- 多级encoding尝试机制
- error忽略和容错process

作者: Project3 Team
版本: 2.0
"""

import chardet
import os
from typing import Optional


def detect_file_encoding(file_path: str) -> str:
    """
    智能检测文件encoding格式
    
    使用多级检测策略：
    1. checkBOM标记（UTF-8、UTF-16等）
    2. 使用chardet库进行智能检测
    3. 尝试常见encoding格式
    
    Args:
        file_path (str): file path
        
    Returns:
        str: 检测到的encoding格式，默认return'utf-8'
        
    Example:
        >>> encoding = detect_file_encoding('test.txt')
        >>> print(f"文件encoding: {encoding}")
    """
    # 1. checkBOM标记
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
        print(f"⚠️ BOM检测failed: {e}")
    
    # 2. 使用chardet检测
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        result = chardet.detect(raw_data)
        if result and result['encoding']:
            confidence = result['confidence']
            encoding = result['encoding']
            print(f"🔍 chardet检测到encoding: {encoding} (confidence: {confidence:.2f})")
            
            # 如果confidence较高，直接使用
            if confidence > 0.7:
                return encoding
            
    except Exception as e:
        print(f"⚠️ chardet检测failed: {e}")
    
    # 3. 尝试常见encoding
    common_encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'big5', 'latin1', 'cp1252']
    
    for encoding in common_encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1024)  # 尝试读取前1024字符
            print(f"🔍 successvalidateencoding: {encoding}")
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"⚠️ encoding {encoding} 测试failed: {e}")
            continue
    
    # 4. 默认returnUTF-8
    print("⚠️ 无法确定encoding，使用UTF-8作为默认")
    return 'utf-8'


def read_file_with_encoding(file_path: str) -> str:
    """
    使用智能encoding检测读取文件内容
    
    Args:
        file_path (str): file path
        
    Returns:
        str: 文件内容
        
    Raises:
        FileNotFoundError: 文件不存在
        Exception: 读取failed
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 检测encoding
    detected_encoding = detect_file_encoding(file_path)
    
    # 尝试使用检测到的encodingread
    encodings_to_try = [detected_encoding]
    
    # 添加备用encoding
    backup_encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1', 'cp1252']
    for enc in backup_encodings:
        if enc not in encodings_to_try:
            encodings_to_try.append(enc)
    
    last_error = None
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                content = f.read()
            print(f"✅ 使用 {encoding} encoding读取文件success，文本长度: {len(content)} 字符")
            return content
            
        except UnicodeDecodeError as e:
            last_error = e
            print(f"⚠️ encoding {encoding} 读取failed: {e}")
            continue
        except Exception as e:
            last_error = e
            print(f"⚠️ 使用encoding {encoding} 时发生error: {e}")
            continue
    
    # 最后尝试忽略error的方式read
    try:
        print("🔄 尝试忽略encodingerror的方式读取...")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        print(f"⚠️ 使用error忽略模式读取success，文本长度: {len(content)} 字符")
        return content
    except Exception as e:
        print(f"❌ error忽略模式也failed: {e}")
    
    # 如果所有method都failed，抛出exception
    raise Exception(f"无法读取文件 {file_path}，最后error: {last_error}")


def safe_file_read(file_path: str, default_content: str = "") -> str:
    """
    安全读取文件，failed时return默认内容
    
    Args:
        file_path (str): file path
        default_content (str): 默认内容
        
    Returns:
        str: 文件内容或默认内容
    """
    try:
        return read_file_with_encoding(file_path)
    except Exception as e:
        print(f"⚠️ 文件读取failed，使用默认内容: {e}")
        return default_content
