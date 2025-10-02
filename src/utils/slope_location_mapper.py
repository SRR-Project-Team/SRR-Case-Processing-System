#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
斜坡位置映射模块
根据G列斜坡编号从depend_data/Slope data.xlsx查找对应的venue值
处理两位数字开头的斜坡编号和可能的干扰信息
"""

import pandas as pd
import re
from typing import Optional, Dict, List
import os


class SlopeLocationMapper:
    """斜坡位置映射器"""
    
    def __init__(self):
        """初始化映射器"""
        self.slope_data = None
        self.slope_mapping = {}
        self._load_slope_data()
    
    def _load_slope_data(self):
        """加载斜坡数据"""
        try:
            excel_path = "depend_data/Slope data.xlsx"
            if not os.path.exists(excel_path):
                print(f"⚠️ 斜坡数据文件不存在: {excel_path}")
                return
            
            print(f"📊 加载斜坡数据: {excel_path}")
            self.slope_data = pd.read_excel(excel_path)
            
            if self.slope_data.empty:
                print("⚠️ 斜坡数据文件为空")
                return
            
            print(f"✅ 成功加载斜坡数据，共 {len(self.slope_data)} 条记录")
            
            # 检查必要的列
            if 'SlopeNo' not in self.slope_data.columns:
                print("❌ 斜坡数据缺少 SlopeNo 列")
                return
            
            if 'Venue' not in self.slope_data.columns:
                print("❌ 斜坡数据缺少 Venue 列")
                return
            
            # 构建映射字典
            self._build_mapping()
            
        except Exception as e:
            print(f"❌ 加载斜坡数据失败: {e}")
            self.slope_data = None
    
    def _build_mapping(self):
        """构建斜坡编号到位置的映射"""
        if self.slope_data is None or self.slope_data.empty:
            return
        
        print("🔧 构建斜坡编号映射...")
        
        # 清理和构建映射
        mapping_count = 0
        
        for _, row in self.slope_data.iterrows():
            slope_no = row.get('SlopeNo')
            venue = row.get('Venue')
            
            if pd.notna(slope_no) and pd.notna(venue):
                # 清理斜坡编号
                cleaned_slope_no = self._clean_slope_number(str(slope_no))
                if cleaned_slope_no:
                    # 存储原始和清理后的映射
                    self.slope_mapping[str(slope_no).strip().upper()] = str(venue).strip()
                    self.slope_mapping[cleaned_slope_no.upper()] = str(venue).strip()
                    mapping_count += 1
        
        print(f"✅ 构建映射完成，共 {mapping_count} 个有效映射")
        
        # 显示一些样例
        sample_mappings = list(self.slope_mapping.items())[:5]
        print("📝 映射样例:")
        for slope, venue in sample_mappings:
            print(f"   {slope} -> {venue}")
    
    def _clean_slope_number(self, slope_no: str) -> Optional[str]:
        """清理斜坡编号，提取标准格式"""
        if not slope_no or not isinstance(slope_no, str):
            return None
        
        # 移除多余的空格
        slope_no = slope_no.strip()
        
        # 匹配两位数字开头的斜坡编号模式
        # 例如: 11SW-D/C79, 15NW-B/C165, 11SE-A/C1 等
        patterns = [
            r'(\d{2}[A-Z]{2}-[A-Z]/[A-Z]*\d+)',  # 标准格式: 11SW-D/C79
            r'(\d{2}[A-Z]{2}-[A-Z]/[A-Z]{1,3}\d+)',  # 带字母前缀: 11SW-D/CR78
            r'(\d{2}[A-Z]{2}-[A-Z]/[A-Z]*\d+[A-Z]*)',  # 可能的变体
        ]
        
        for pattern in patterns:
            match = re.search(pattern, slope_no.upper())
            if match:
                return match.group(1)
        
        return None
    
    def _extract_slope_number_from_text(self, text: str) -> List[str]:
        """从文本中提取所有可能的斜坡编号"""
        if not text:
            return []
        
        # 多种斜坡编号提取模式
        patterns = [
            # 标准格式匹配
            r'(\d{2}[A-Z]{2}-[A-Z]/[A-Z]*\d+)',  # 标准格式: 11SW-D/C79
            r'(\d{2}[A-Z]{2}-[A-Z]/[A-Z]{1,3}\d+)',  # 带字母前缀: 11SW-D/CR78
            
            # 中文描述后的编号
            r'斜坡[编編号號]*[：:]?\s*(\d{2}[A-Z]{2}-[A-Z]/[A-Z]*\d+)',
            r'斜坡[编編号號]*[：:]?\s*(\d{2}[A-Z]{2}-[A-Z]/\d+)',  # 无字母前缀
            
            # 英文描述后的编号
            r'slope\s*no\.?\s*[：:]?\s*(\d{2}[A-Z]{2}-[A-Z]/[A-Z]*\d+)',
            r'slope\s*no\.?\s*[：:]?\s*(\d{2}[A-Z]{2}-[A-Z]/\d+)',  # 无字母前缀
            
            # 更宽松的匹配（处理可能的干扰）
            r'[：:]\s*(\d{2}[A-Z]{2}-[A-Z]/[A-Z]*\d+)',  # 冒号后的编号
            r'[：:]\s*(\d{2}[A-Z]{2}-[A-Z]/\d+)',  # 冒号后的编号（无字母前缀）
            
            # 处理维修工程等后缀
            r'(\d{2}[A-Z]{2}-[A-Z]/[A-Z]*\d+)[^A-Z0-9]*(?:维修|維修|工程|进度|進度)',
            r'(\d{2}[A-Z]{2}-[A-Z]/\d+)[^A-Z0-9]*(?:维修|維修|工程|进度|進度)',
        ]
        
        found_slopes = []
        text_upper = text.upper()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_upper, re.IGNORECASE)
            found_slopes.extend(matches)
        
        # 去重并返回
        unique_slopes = list(set(found_slopes))
        
        # 如果找到编号，记录日志
        if unique_slopes:
            print(f"🔍 从文本中提取到斜坡编号: {unique_slopes}")
        
        return unique_slopes
    
    def get_location_by_slope_number(self, slope_no: str) -> str:
        """
        根据斜坡编号获取位置信息
        
        Args:
            slope_no (str): 斜坡编号
            
        Returns:
            str: 对应的位置信息，如果未找到返回空字符串
        """
        if not slope_no or not isinstance(slope_no, str):
            return ""
        
        if not self.slope_mapping:
            print("⚠️ 斜坡映射数据未加载")
            return ""
        
        # 清理输入的斜坡编号
        cleaned_slope = slope_no.strip().upper()
        
        print(f"🔍 查找斜坡编号: {slope_no}")
        
        # 1. 直接匹配
        if cleaned_slope in self.slope_mapping:
            location = self.slope_mapping[cleaned_slope]
            print(f"✅ 直接匹配找到位置: {location}")
            return location
        
        # 2. 提取并匹配标准格式
        extracted_slopes = self._extract_slope_number_from_text(slope_no)
        for extracted in extracted_slopes:
            if extracted.upper() in self.slope_mapping:
                location = self.slope_mapping[extracted.upper()]
                print(f"✅ 提取匹配找到位置: {location} (提取的编号: {extracted})")
                return location
            
            # 对提取到的编号也进行智能匹配
            base_pattern = re.match(r'(\d{2}[A-Z]{2}-[A-Z]/)(\d+)', extracted.upper())
            if base_pattern:
                prefix = base_pattern.group(1)  # 例如: 11SW-D/
                number = base_pattern.group(2)  # 例如: 805
                
                # 查找所有以相同前缀开始并包含相同数字的编号
                for mapped_slope, venue in self.slope_mapping.items():
                    if mapped_slope.startswith(prefix) and number in mapped_slope:
                        print(f"✅ 提取智能匹配找到位置: {venue} (提取编号: {extracted}, 匹配编号: {mapped_slope})")
                        return venue
        
        # 3. 模糊匹配（去除可能的干扰字符）
        cleaned_for_fuzzy = self._clean_slope_number(slope_no)
        if cleaned_for_fuzzy and cleaned_for_fuzzy.upper() in self.slope_mapping:
            location = self.slope_mapping[cleaned_for_fuzzy.upper()]
            print(f"✅ 模糊匹配找到位置: {location} (清理后编号: {cleaned_for_fuzzy})")
            return location
        
        # 4. 智能部分匹配（处理缺少字母前缀的情况）
        # 例如: 11SW-D/805 应该匹配 11SW-D/R805, 11SW-D/C805 等
        base_pattern = re.match(r'(\d{2}[A-Z]{2}-[A-Z]/)(\d+)', cleaned_slope)
        if base_pattern:
            prefix = base_pattern.group(1)  # 例如: 11SW-D/
            number = base_pattern.group(2)  # 例如: 805
            
            # 查找所有以相同前缀开始并包含相同数字的编号
            for mapped_slope, venue in self.slope_mapping.items():
                if mapped_slope.startswith(prefix) and number in mapped_slope:
                    print(f"✅ 智能匹配找到位置: {venue} (匹配编号: {mapped_slope})")
                    return venue
        
        # 5. 通用部分匹配（对于可能有额外字符的情况）
        for mapped_slope, venue in self.slope_mapping.items():
            if cleaned_slope in mapped_slope or mapped_slope in cleaned_slope:
                # 确保是有意义的匹配（长度相近）
                if abs(len(cleaned_slope) - len(mapped_slope)) <= 3:
                    print(f"✅ 部分匹配找到位置: {venue} (匹配编号: {mapped_slope})")
                    return venue
        
        print(f"❌ 未找到斜坡编号 {slope_no} 对应的位置")
        return ""
    
    def search_locations_by_pattern(self, pattern: str) -> List[Dict[str, str]]:
        """
        根据模式搜索位置信息
        
        Args:
            pattern (str): 搜索模式
            
        Returns:
            List[Dict]: 匹配的结果列表
        """
        if not self.slope_mapping or not pattern:
            return []
        
        results = []
        pattern_upper = pattern.upper()
        
        for slope_no, venue in self.slope_mapping.items():
            if pattern_upper in slope_no or pattern_upper in venue.upper():
                results.append({
                    'slope_no': slope_no,
                    'venue': venue
                })
        
        return results[:10]  # 限制返回数量
    
    def get_statistics(self) -> Dict[str, int]:
        """获取映射统计信息"""
        if not self.slope_data is not None:
            return {
                'total_records': 0,
                'valid_mappings': 0,
                'slope_no_count': 0,
                'venue_count': 0
            }
        
        return {
            'total_records': len(self.slope_data),
            'valid_mappings': len(self.slope_mapping),
            'slope_no_count': self.slope_data['SlopeNo'].notna().sum(),
            'venue_count': self.slope_data['Venue'].notna().sum()
        }


# 全局映射器实例
_slope_mapper = None


def get_slope_location_mapper() -> SlopeLocationMapper:
    """获取全局斜坡位置映射器实例"""
    global _slope_mapper
    if _slope_mapper is None:
        _slope_mapper = SlopeLocationMapper()
    return _slope_mapper


def get_location_from_slope_no(slope_no: str) -> str:
    """
    根据斜坡编号获取位置信息的便捷函数
    
    Args:
        slope_no (str): 斜坡编号
        
    Returns:
        str: 对应的位置信息
    """
    mapper = get_slope_location_mapper()
    return mapper.get_location_by_slope_number(slope_no)


def test_slope_location_mapper():
    """测试斜坡位置映射器"""
    print("=== 斜坡位置映射器测试 ===\n")
    
    mapper = SlopeLocationMapper()
    
    # 测试用例
    test_cases = [
        "11SW-D/C79",
        "11SW-D/CR78", 
        "15NW-B/C165",
        "11SE-A/C1",
        "斜坡编号：11SW-D/805",
        "slope no: 11SW-D/R805",
        "11SW-D/805维修工程",
        "不存在的编号123"
    ]
    
    print("📋 测试案例:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试斜坡编号: {test_case}")
        location = mapper.get_location_by_slope_number(test_case)
        if location:
            print(f"   ✅ 找到位置: {location}")
        else:
            print(f"   ❌ 未找到位置")
    
    # 统计信息
    print(f"\n📊 映射统计:")
    stats = mapper.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    test_slope_location_mapper()
