#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
来源分类器
根据文件类型、内容和语义智能判断B_source字段的值
"""

import re
import os
from typing import Optional, Dict, List


class SourceClassifier:
    """来源分类器"""
    
    def __init__(self):
        """初始化分类器"""
        self.source_options = {
            "": "",
            "1": "ICC",
            "2": "Telephone", 
            "3": "E-mail",
            "4": "RCC",
            "5": "Memo/Letter",
            "6": "Fax",
            "7": "Audit Report",
            "8": "TMO",
            "9": "BDRC",
            "10": "DC",
            "11": "Press",
            "12": "Others"
        }
        
        # 反向映射，用于查找
        self.source_name_to_id = {v: k for k, v in self.source_options.items() if v}
        
        # 关键词映射
        self.keyword_mappings = self._build_keyword_mappings()
    
    def _build_keyword_mappings(self) -> Dict[str, List[str]]:
        """构建关键词映射"""
        return {
            "ICC": [
                "icc", "inter-departmental", "interdepartmental", 
                "internal communication", "內部通訊"
            ],
            "Telephone": [
                "telephone", "phone", "tel:", "call", "致電", "電話", "通話"
            ],
            "E-mail": [
                "email", "e-mail", "mail", "electronic mail", "郵件", "電郵",
                "from:", "to:", "subject:", "sent:", "@", "inbox", "outbox"
            ],
            "RCC": [
                "rcc", "regional complaint", "complaint centre", "投訴中心"
            ],
            "Memo/Letter": [
                "memo", "memorandum", "letter", "correspondence", 
                "備忘錄", "信件", "函件", "通函"
            ],
            "Fax": [
                "fax", "facsimile", "傳真", "fax no", "fax number"
            ],
            "Audit Report": [
                "audit", "audit report", "auditing", "審計", "審核報告"
            ],
            "TMO": [
                "tmo", "tree management office", "樹木管理辦事處",
                "tree management", "arboriculture"
            ],
            "BDRC": [
                "bdrc", "building department", "屋宇署"
            ],
            "DC": [
                "dc", "district council", "區議會", "district councillor"
            ],
            "Press": [
                "press", "media", "newspaper", "journalist", "reporter",
                "新聞", "媒體", "記者", "報章"
            ]
        }
    
    def classify_source(self, file_path: str = None, content: str = "", 
                       email_content: str = None, file_type: str = "txt") -> str:
        """
        智能分类来源
        
        Args:
            file_path (str): 文件路径
            content (str): 文件内容
            email_content (str): 邮件内容（如果有）
            file_type (str): 文件类型 ('txt', 'pdf')
            
        Returns:
            str: 来源名称 (如 'E-mail', 'TMO', 'RCC' 等)
        """
        print(f"🔍 开始来源分类...")
        print(f"   文件路径: {file_path}")
        print(f"   文件类型: {file_type}")
        print(f"   有邮件内容: {'是' if email_content else '否'}")
        
        # 1. 优先级规则：邮件内容存在
        if email_content and email_content.strip():
            print("📧 检测到邮件内容，分类为 E-mail")
            return "E-mail"
        
        # 2. 文件名规则：ASD开头的PDF文件
        if file_path and file_type.lower() == "pdf":
            filename = os.path.basename(file_path).upper()
            if filename.startswith("ASD"):
                print("🌳 检测到ASD开头的PDF文件，分类为 TMO")
                return "TMO"
        
        # 3. 文件名规则：RCC开头的PDF文件
        if file_path and file_type.lower() == "pdf":
            filename = os.path.basename(file_path).upper()
            if filename.startswith("RCC"):
                print("📋 检测到RCC开头的PDF文件，分类为 RCC")
                return "RCC"
        
        # 4. 内容分析
        content_source = self._analyze_content(content)
        if content_source:
            print(f"📄 根据内容分析，分类为 {content_source}")
            return content_source
        
        # 5. 文件类型默认规则
        if file_type.lower() == "pdf":
            print("📄 PDF文件默认分类为 Others")
            return "Others"
        
        # 6. TXT文件的渠道分析
        if file_type.lower() == "txt":
            txt_source = self._analyze_txt_channel(content)
            if txt_source:
                print(f"📝 根据TXT渠道分析，分类为 {txt_source}")
                return txt_source
        
        # 7. 默认值
        print("❓ 无法确定来源，使用默认值 Others")
        return "Others"
    
    def _analyze_content(self, content: str) -> Optional[str]:
        """分析内容确定来源"""
        if not content:
            return None
        
        content_lower = content.lower()
        
        # 按优先级检查关键词
        priority_sources = [
            "TMO", "RCC", "ICC", "BDRC", "DC", 
            "E-mail", "Fax", "Telephone", "Press", 
            "Audit Report", "Memo/Letter"
        ]
        
        for source in priority_sources:
            keywords = self.keyword_mappings.get(source, [])
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    return source
        
        return None
    
    def _analyze_txt_channel(self, content: str) -> Optional[str]:
        """分析TXT文件的Channel字段"""
        if not content:
            return None
        
        # 提取Channel字段
        channel_match = re.search(r'Channel\s*:\s*([^\n]+)', content, re.IGNORECASE)
        if not channel_match:
            return None
        
        channel = channel_match.group(1).strip().lower()
        print(f"🔍 检测到Channel: {channel}")
        
        # Channel映射规则
        channel_mappings = {
            "email": "E-mail",
            "e-mail": "E-mail", 
            "web": "E-mail",  # Web通常通过邮件系统处理
            "telephone": "Telephone",
            "phone": "Telephone",
            "tel": "Telephone",
            "fax": "Fax",
            "letter": "Memo/Letter",
            "memo": "Memo/Letter",
            "rcc": "RCC",
            "icc": "ICC"
        }
        
        for pattern, source in channel_mappings.items():
            if pattern in channel:
                return source
        
        return None
    
    def get_source_name_by_id(self, source_id: str) -> str:
        """根据ID获取来源名称"""
        return self.source_options.get(source_id, "Others")
    
    def get_all_sources(self) -> Dict[str, str]:
        """获取所有来源选项"""
        return self.source_options.copy()


# 全局分类器实例
_source_classifier = None


def get_source_classifier() -> SourceClassifier:
    """获取全局来源分类器实例"""
    global _source_classifier
    if _source_classifier is None:
        _source_classifier = SourceClassifier()
    return _source_classifier


def classify_source_smart(file_path: str = None, content: str = "", 
                         email_content: str = None, file_type: str = "txt") -> str:
    """
    智能分类来源的便捷函数
    
    Args:
        file_path (str): 文件路径
        content (str): 文件内容
        email_content (str): 邮件内容（如果有）
        file_type (str): 文件类型
        
    Returns:
        str: 来源名称 (如 'E-mail', 'TMO', 'RCC' 等)
    """
    classifier = get_source_classifier()
    return classifier.classify_source(file_path, content, email_content, file_type)


def test_source_classifier():
    """测试来源分类器"""
    print("=== 来源分类器测试 ===\n")
    
    classifier = SourceClassifier()
    
    # 测试用例
    test_cases = [
        {
            'name': 'TXT文件带邮件内容',
            'file_path': 'case_123.txt',
            'content': 'Channel : Email\nRequest Type : Enquiry',
            'email_content': 'From: user@example.com\nTo: 1823@gov.hk\nSubject: Slope inquiry',
            'file_type': 'txt',
            'expected': 'E-mail'
        },
        {
            'name': 'ASD开头的PDF文件',
            'file_path': 'ASD-WC-20250089-PP.pdf',
            'content': 'Tree Management Office Form 2',
            'email_content': None,
            'file_type': 'pdf',
            'expected': 'TMO'
        },
        {
            'name': 'RCC开头的PDF文件',
            'file_path': 'RCC#84878800.pdf',
            'content': 'Regional Complaint Centre',
            'email_content': None,
            'file_type': 'pdf',
            'expected': 'RCC'
        },
        {
            'name': 'TXT文件电话渠道',
            'file_path': 'case_456.txt',
            'content': 'Channel : Telephone\nRequest Type : Complaint',
            'email_content': None,
            'file_type': 'txt',
            'expected': 'Telephone'
        },
        {
            'name': 'TXT文件传真渠道',
            'file_path': 'case_789.txt',
            'content': 'Channel : Fax\nFax No: 12345678',
            'email_content': None,
            'file_type': 'txt',
            'expected': 'Fax'
        }
    ]
    
    print("📋 测试案例:")
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        
        result = classifier.classify_source(
            test_case['file_path'],
            test_case['content'],
            test_case['email_content'],
            test_case['file_type']
        )
        
        expected = test_case['expected']
        
        if result == expected:
            print(f"   ✅ 正确: {result}")
            success_count += 1
        else:
            print(f"   ❌ 错误:")
            print(f"      期望: {expected}")
            print(f"      实际: {result}")
    
    accuracy = success_count / len(test_cases)
    print(f"\n📈 分类准确率: {accuracy:.1%} ({success_count}/{len(test_cases)})")
    
    # 显示所有来源选项
    print(f"\n📋 所有来源选项:")
    for source_id, source_name in classifier.get_all_sources().items():
        if source_name:  # 跳过空选项
            print(f"   {source_id}: {source_name}")


if __name__ == "__main__":
    test_source_classifier()
