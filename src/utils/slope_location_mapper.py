#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斜坡位置映射模块
根据斜坡编号从models/mapping_rules/slope_location_mapping.json查找对应的venue值
"""

import json
import os
import re
from typing import Optional

def load_slope_mapping():
    """加载斜坡位置映射数据"""
    mapping_file = 'models/mapping_rules/slope_location_mapping.json'
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print("⚠️ 斜坡映射文件不存在，使用空映射")
        return {}

def get_location_from_slope_no(slope_no: str) -> str:
    """
    根据斜坡编号获取位置信息
    
    Args:
        slope_no: 斜坡编号，如 "11SW-D/805"
    
    Returns:
        str: 位置信息，如果找不到则返回空字符串
    """
    if not slope_no or not isinstance(slope_no, str):
        return ""
    
    # 加载映射数据
    slope_mapping = load_slope_mapping()
    
    if not slope_mapping:
        print("⚠️ 斜坡映射数据未加载")
        return ""
    
    # 直接查找
    if slope_no in slope_mapping:
        return slope_mapping[slope_no]
    
    # 尝试多种匹配方式
    cleaned_slope = clean_slope_number(slope_no)
    if cleaned_slope in slope_mapping:
        return slope_mapping[cleaned_slope]
    
    # 模糊匹配
    for mapped_slope, venue in slope_mapping.items():
        if is_slope_match(slope_no, mapped_slope):
            return venue
    
    return ""

def clean_slope_number(slope_no: str) -> str:
    """
    清理斜坡编号，去除干扰信息
    
    Args:
        slope_no: 原始斜坡编号
    
    Returns:
        str: 清理后的斜坡编号
    """
    if not slope_no:
        return ""
    
    # 去除前后空格
    cleaned = slope_no.strip()
    
    # 去除#号等干扰字符
    cleaned = re.sub(r'[#\s]+', '', cleaned)
    
    # 确保以数字开头
    if not re.match(r'^\d', cleaned):
        # 如果开头不是数字，尝试提取数字部分
        match = re.search(r'\d+[A-Za-z]+[-/][A-Za-z0-9]+', cleaned)
        if match:
            cleaned = match.group()
    
    return cleaned

def is_slope_match(slope1: str, slope2: str) -> bool:
    """
    判断两个斜坡编号是否匹配
    
    Args:
        slope1: 斜坡编号1
        slope2: 斜坡编号2
    
    Returns:
        bool: 是否匹配
    """
    if not slope1 or not slope2:
        return False
    
    # 清理两个编号
    clean1 = clean_slope_number(slope1)
    clean2 = clean_slope_number(slope2)
    
    # 直接匹配
    if clean1 == clean2:
        return True
    
    # 提取核心部分进行匹配
    core1 = extract_slope_core(clean1)
    core2 = extract_slope_core(clean2)
    
    return core1 == core2 and core1 != ""

def extract_slope_core(slope_no: str) -> str:
    """
    提取斜坡编号的核心部分
    
    Args:
        slope_no: 斜坡编号
    
    Returns:
        str: 核心部分
    """
    if not slope_no:
        return ""
    
    # 匹配模式：数字+字母+斜杠+字母数字
    match = re.search(r'(\d+[A-Za-z]+[-/][A-Za-z0-9]+)', slope_no)
    if match:
        return match.group(1)
    
    return ""

def get_all_slope_locations() -> dict:
    """
    获取所有斜坡位置映射
    
    Returns:
        dict: 斜坡编号到位置的映射字典
    """
    return load_slope_mapping()

def search_slope_by_location(location_keyword: str) -> list:
    """
    根据位置关键词搜索斜坡编号
    
    Args:
        location_keyword: 位置关键词
    
    Returns:
        list: 匹配的斜坡编号列表
    """
    slope_mapping = load_slope_mapping()
    matches = []
    
    if not slope_mapping:
        return matches
    
    location_keyword = location_keyword.lower()
    
    for slope_no, venue in slope_mapping.items():
        if location_keyword in venue.lower():
            matches.append(slope_no)
    
    return matches

# 测试函数
def test_slope_mapping():
    """测试斜坡映射功能"""
    print("🧪 测试斜坡映射功能...")
    
    test_slopes = ["11SW-D/805", "11SW-B/F199", "11SW-D/CR995"]
    
    for slope in test_slopes:
        location = get_location_from_slope_no(slope)
        print(f"斜坡 {slope}: {location}")
    
    # 测试搜索功能
    search_results = search_slope_by_location("Aberdeen")
    print(f"包含'Aberdeen'的斜坡: {search_results[:3]}")

if __name__ == "__main__":
    test_slope_mapping()