#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI主题分类器 - J_subject_matter字段智能分类
基于历史数据和规则进行智能分类，支持17个预定义类别
"""

import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_utils import read_file_with_encoding
from .ai_model_cache import get_cached_model, cache_model


# 预定义的主题类别映射
SUBJECT_MATTER_CATEGORIES = {
    0: "Endangered Tree",
    1: "Drainage Blockage", 
    2: "Fallen Tree",
    3: "Grass Cutting",
    4: "Remove Debris",
    5: "Mosquito Breeding",
    6: "Tree Trimming/ Pruning",
    7: "Landslide",
    8: "Fallen Rock/ Boulders",
    9: "Water Seepage",
    10: "Hazardous tree",
    11: "Others",
    12: "Tree Transplantation / Felling",
    13: "Cracked slope/Wall Surface",
    14: "Repair slope fixture/furniture",
    15: "Surface erosion",
    16: "Repeated case",
    17: "Reminder for outstanding works"
}

# 反向映射
CATEGORY_TO_ID = {v: k for k, v in SUBJECT_MATTER_CATEGORIES.items()}


def load_historical_subject_data(data_path: str) -> pd.DataFrame:
    """
    加载历史主题分类数据
    
    Args:
        data_path: 数据文件路径
        
    Returns:
        pd.DataFrame: 清洗后的历史数据
    """
    try:
        print(f"📊 加载历史主题数据: {data_path}")
        
        if data_path.endswith('.csv'):
            # 读取CSV文件
            csv_content = read_file_with_encoding(data_path)
            with open('temp_subject_data.csv', 'w', encoding='utf-8') as f:
                f.write(csv_content)
            df = pd.read_csv('temp_subject_data.csv')
            os.remove('temp_subject_data.csv')
        else:
            # 读取Excel文件
            df = pd.read_excel(data_path, usecols='A:AZ')
        
        print(f"✅ 原始数据加载成功: {len(df)} 条记录")
        
        # 查找相关列
        nature_col = None
        aims_col = None
        
        for col in df.columns:
            if 'nature of complaint' in col.lower():
                nature_col = col
            elif 'aims complaint type' in col.lower():
                aims_col = col
        
        if not nature_col and not aims_col:
            print("⚠️ 未找到主题相关列，使用默认数据")
            return pd.DataFrame()
        
        # 清洗数据
        cleaned_data = []
        
        # 使用AIMS Complaint Type作为主要数据源
        if aims_col:
            aims_data = df[aims_col].dropna()
            for complaint_type in aims_data:
                if complaint_type and str(complaint_type).strip():
                    cleaned_data.append({
                        'complaint_text': str(complaint_type).strip(),
                        'source': 'AIMS'
                    })
        
        # 补充Nature of complaint数据
        if nature_col:
            nature_data = df[nature_col].dropna()
            for nature in nature_data:
                if nature and str(nature).strip():
                    cleaned_data.append({
                        'complaint_text': str(nature).strip(),
                        'source': 'Nature'
                    })
        
        result_df = pd.DataFrame(cleaned_data)
        print(f"✅ 清洗后数据: {len(result_df)} 条记录")
        
        return result_df
        
    except Exception as e:
        print(f"❌ 加载历史数据失败: {e}")
        return pd.DataFrame()


def create_keyword_mapping() -> Dict[str, List[str]]:
    """
    创建关键词到类别的映射
    
    Returns:
        Dict[str, List[str]]: 类别到关键词的映射
    """
    keyword_mapping = {
        "Endangered Tree": [
            "endangered tree", "危险树木", "tree danger", "tree risk", "unstable tree"
        ],
        "Drainage Blockage": [
            "drainage", "blockage", "blocked drain", "排水", "堵塞", "drainage clearance",
            "drain block", "water block", "排水堵塞"
        ],
        "Fallen Tree": [
            "fallen tree", "tree fall", "倒塌树木", "fallen trees", "tree fallen",
            "tree collapse", "倒树"
        ],
        "Grass Cutting": [
            "grass cutting", "grass cut", "trimming", "割草", "修剪草坪", 
            "grass maintenance", "lawn cutting"
        ],
        "Remove Debris": [
            "remove debris", "debris removal", "清理碎片", "remove refuse", 
            "rubbish removal", "清理垃圾", "debris clear"
        ],
        "Mosquito Breeding": [
            "mosquito", "breeding", "蚊虫滋生", "mosquito control", "pest control",
            "insect breeding"
        ],
        "Tree Trimming/ Pruning": [
            "tree trimming", "pruning", "tree pruning", "修剪树木", "tree maintenance",
            "branch cutting", "tree cut"
        ],
        "Landslide": [
            "landslide", "slope failure", "山泥倾泻", "土石流", "slope collapse",
            "land slip", "slope instability"
        ],
        "Fallen Rock/ Boulders": [
            "fallen rock", "boulder", "rock fall", "石头掉落", "岩石滑落",
            "rock slide", "stone fall"
        ],
        "Water Seepage": [
            "water seepage", "seepage", "渗水", "water leak", "water infiltration",
            "observe water seepage", "water penetration"
        ],
        "Hazardous tree": [
            "hazardous tree", "dangerous tree", "tree hazard", "危险树木",
            "unsafe tree", "tree safety"
        ],
        "Tree Transplantation / Felling": [
            "tree transplantation", "tree felling", "tree removal", "移植树木",
            "砍伐树木", "tree relocation"
        ],
        "Cracked slope/Wall Surface": [
            "crack", "cracked slope", "wall crack", "裂缝", "slope crack",
            "surface crack", "wall surface"
        ],
        "Repair slope fixture/furniture": [
            "repair", "slope fixture", "furniture", "维修", "slope maintenance",
            "fixture repair", "slope repair"
        ],
        "Surface erosion": [
            "erosion", "surface erosion", "土壤侵蚀", "slope erosion",
            "surface wear", "weathering"
        ],
        "Repeated case": [
            "repeated", "repeat case", "重复案例", "duplicate", "recurring",
            "repeated case"
        ],
        "Reminder for outstanding works": [
            "reminder", "outstanding", "follow up", "提醒", "未完成工作",
            "pending work", "outstanding work"
        ],
        "Others": [
            "others", "other", "其他", "miscellaneous", "general", "unspecified"
        ]
    }
    
    return keyword_mapping


class SubjectMatterClassifier:
    """主题分类器"""
    
    def __init__(self, historical_data_paths: List[str]):
        """
        初始化分类器，使用缓存优化
        
        Args:
            historical_data_paths: 历史数据文件路径列表
        """
        # 尝试从缓存获取分类器
        cache_key = "subject_matter_classifier"
        cached_classifier = get_cached_model(cache_key)
        
        if cached_classifier:
            # 使用缓存的分类器
            self.historical_data = cached_classifier.get('historical_data')
            self.keyword_mapping = cached_classifier.get('keyword_mapping')
            self.vectorizer = cached_classifier.get('vectorizer')
            self.model = cached_classifier.get('model')
            self.label_encoder = cached_classifier.get('label_encoder')
            print("🚀 使用缓存的主题分类器")
            return
        
        # 缓存未命中，正常初始化
        self.historical_data = self._load_all_historical_data(historical_data_paths)
        self.keyword_mapping = create_keyword_mapping()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.label_encoder = LabelEncoder()
        self._train_model()
        
        # 缓存分类器
        try:
            classifier_cache = {
                'historical_data': self.historical_data,
                'keyword_mapping': self.keyword_mapping,
                'vectorizer': self.vectorizer,
                'model': self.model,
                'label_encoder': self.label_encoder
            }
            cache_model(cache_key, classifier_cache)
        except Exception as e:
            print(f"⚠️ 缓存主题分类器失败: {e}")
    
    def _load_all_historical_data(self, data_paths: List[str]) -> pd.DataFrame:
        """加载所有历史数据"""
        all_data = []
        
        for path in data_paths:
            if os.path.exists(path):
                df = load_historical_subject_data(path)
                if not df.empty:
                    all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            print(f"✅ 总历史数据: {len(combined_df)} 条记录")
            return combined_df
        else:
            print("⚠️ 未找到有效历史数据")
            return pd.DataFrame()
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        if not text:
            return ""
        
        # 转换为小写
        text = str(text).lower()
        
        # 移除特殊字符，保留字母、数字和空格
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _map_to_standard_category(self, complaint_text: str) -> str:
        """将历史数据映射到标准类别"""
        text_lower = complaint_text.lower()
        
        # 直接匹配
        for category, keywords in self.keyword_mapping.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        # 特殊映射规则
        mapping_rules = {
            'trimming': 'Tree Trimming/ Pruning',
            'withered tree': 'Hazardous tree',
            'to observe': 'Others',
            'slope maintenance': 'Repair slope fixture/furniture',
            'drainage clearance': 'Drainage Blockage',
            'remove refuse': 'Remove Debris'
        }
        
        for pattern, category in mapping_rules.items():
            if pattern in text_lower:
                return category
        
        return "Others"
    
    def _train_model(self):
        """训练机器学习模型"""
        if self.historical_data.empty:
            print("⚠️ 无历史数据，仅使用规则分类")
            return
        
        print("🤖 训练主题分类模型...")
        
        # 准备训练数据
        texts = []
        labels = []
        
        for _, row in self.historical_data.iterrows():
            complaint_text = row['complaint_text']
            processed_text = self._preprocess_text(complaint_text)
            
            if processed_text:
                # 映射到标准类别
                category = self._map_to_standard_category(complaint_text)
                texts.append(processed_text)
                labels.append(category)
        
        if len(texts) < 10:
            print("⚠️ 训练数据不足，仅使用规则分类")
            return
        
        # 编码标签
        encoded_labels = self.label_encoder.fit_transform(labels)
        
        # 向量化文本
        X = self.vectorizer.fit_transform(texts)
        
        # 分割训练测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, encoded_labels, test_size=0.2, random_state=42, stratify=encoded_labels
        )
        
        # 训练模型
        self.model.fit(X_train, y_train)
        
        # 评估模型
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ 模型训练完成，准确率: {accuracy:.2f}")
        
        # 显示分类报告
        try:
            target_names = self.label_encoder.classes_
            print("\n模型评估:")
            print(classification_report(y_test, y_pred, target_names=target_names, zero_division=0))
        except Exception as e:
            print(f"\n⚠️ 分类报告生成失败: {e}")
            print(f"模型准确率: {accuracy:.2f}")
    
    def _rule_based_classify(self, case_data: Dict[str, Any]) -> Tuple[Optional[str], float, str]:
        """基于规则的分类"""
        # 收集所有文本信息
        text_sources = [
            case_data.get('I_nature_of_request', ''),
            case_data.get('J_subject_matter', ''),
            case_data.get('Q_case_details', ''),
            case_data.get('content', '')
        ]
        
        combined_text = ' '.join(filter(None, text_sources)).lower()
        
        if not combined_text.strip():
            return None, 0.0, "no_content"
        
        # 关键词匹配评分
        category_scores = {}
        
        for category, keywords in self.keyword_mapping.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    # 根据关键词重要性给分
                    if len(keyword) > 10:  # 长关键词更精确
                        score += 3
                    elif len(keyword) > 5:
                        score += 2
                    else:
                        score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'keywords': matched_keywords
                }
        
        if category_scores:
            # 选择得分最高的类别
            best_category = max(category_scores.keys(), key=lambda x: category_scores[x]['score'])
            max_score = category_scores[best_category]['score']
            confidence = min(max_score / 10.0, 1.0)  # 归一化置信度
            
            return best_category, confidence, f"rule_based (keywords: {category_scores[best_category]['keywords'][:3]})"
        
        return None, 0.0, "no_match"
    
    def _ml_classify(self, case_data: Dict[str, Any]) -> Tuple[str, float, str]:
        """基于机器学习的分类"""
        if not hasattr(self.model, 'predict'):
            return "Others", 0.3, "ml_not_available"
        
        # 收集文本信息
        text_sources = [
            case_data.get('I_nature_of_request', ''),
            case_data.get('J_subject_matter', ''),
            case_data.get('Q_case_details', ''),
            case_data.get('content', '')
        ]
        
        combined_text = ' '.join(filter(None, text_sources))
        processed_text = self._preprocess_text(combined_text)
        
        if not processed_text:
            return "Others", 0.3, "no_text_for_ml"
        
        try:
            # 向量化
            X = self.vectorizer.transform([processed_text])
            
            # 预测
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            
            # 解码标签
            predicted_category = self.label_encoder.inverse_transform([prediction])[0]
            confidence = max(probabilities)
            
            return predicted_category, confidence, f"machine_learning"
            
        except Exception as e:
            print(f"⚠️ ML分类失败: {e}")
            return "Others", 0.3, "ml_error"
    
    def classify(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        主分类方法
        
        Args:
            case_data: 案件数据
            
        Returns:
            Dict: 分类结果
        """
        print("🔍 开始主题分类...")
        
        # 1. 尝试规则分类
        rule_result, rule_confidence, rule_method = self._rule_based_classify(case_data)
        
        # 2. 尝试ML分类
        ml_result, ml_confidence, ml_method = self._ml_classify(case_data)
        
        # 3. 决策逻辑
        if rule_result and rule_confidence >= 0.7:
            # 高置信度规则分类
            final_category = rule_result
            final_confidence = rule_confidence
            final_method = rule_method
        elif rule_result and ml_result == rule_result:
            # 规则和ML一致
            final_category = rule_result
            final_confidence = (rule_confidence + ml_confidence) / 2
            final_method = f"consensus ({rule_method} + {ml_method})"
        elif ml_confidence >= 0.6:
            # 高置信度ML分类
            final_category = ml_result
            final_confidence = ml_confidence
            final_method = ml_method
        elif rule_result:
            # 使用规则分类
            final_category = rule_result
            final_confidence = rule_confidence
            final_method = rule_method
        else:
            # 默认分类
            final_category = "Others"
            final_confidence = 0.3
            final_method = "default"
        
        # 获取类别ID
        category_id = CATEGORY_TO_ID.get(final_category, 11)  # 默认为Others
        
        result = {
            'predicted_category': final_category,
            'category_id': category_id,
            'confidence': final_confidence,
            'method': final_method,
            'rule_result': rule_result,
            'ml_result': ml_result
        }
        
        print(f"✅ 主题分类完成: {final_category} (ID: {category_id}, 置信度: {final_confidence:.2f})")
        
        return result


def classify_subject_matter_ai(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI主题分类入口函数
    
    Args:
        case_data: 案件数据，包含以下字段：
            - I_nature_of_request: 请求性质
            - J_subject_matter: 主题事项
            - Q_case_details: 案件详情
            - content: 原始内容
            
    Returns:
        Dict: 分类结果
        {
            'predicted_category': str,  # 预测类别名称
            'category_id': int,         # 类别ID
            'confidence': float,        # 置信度
            'method': str,              # 分类方法
            'rule_result': str,         # 规则分类结果
            'ml_result': str            # ML分类结果
        }
    """
    try:
        # 历史数据路径
        historical_data_paths = [
            'depend_data/SRR data 2021-2024.csv',
            'depend_data/Slopes Complaints & Enquires Under             TC K928   4-10-2021.xlsx'
        ]
        
        # 创建分类器
        classifier = SubjectMatterClassifier(historical_data_paths)
        
        # 执行分类
        result = classifier.classify(case_data)
        
        return result
        
    except Exception as e:
        print(f"❌ 主题分类失败: {e}")
        return {
            'predicted_category': 'Others',
            'category_id': 11,
            'confidence': 0.3,
            'method': 'error_fallback',
            'rule_result': None,
            'ml_result': None
        }


def test_subject_matter_classifier():
    """测试主题分类器"""
    print("=== 主题分类器测试 ===\n")
    
    # 测试用例
    test_cases = [
        {
            'name': '草坪修剪',
            'data': {
                'I_nature_of_request': 'Request for grass cutting maintenance',
                'content': 'The grass on the slope is overgrown and needs cutting'
            }
        },
        {
            'name': '树木倒塌',
            'data': {
                'I_nature_of_request': 'Report fallen tree on slope',
                'Q_case_details': 'A large tree has fallen and is blocking the path'
            }
        },
        {
            'name': '排水堵塞',
            'data': {
                'I_nature_of_request': 'Drainage system blocked',
                'content': 'Water cannot flow properly due to blockage in drainage'
            }
        },
        {
            'name': '危险树木',
            'data': {
                'I_nature_of_request': 'Hazardous tree needs attention',
                'content': 'Tree appears unstable and poses safety risk'
            }
        },
        {
            'name': '渗水问题',
            'data': {
                'I_nature_of_request': 'Water seepage observed',
                'content': 'Water is seeping through the slope wall'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"📋 测试案例: {test_case['name']}")
        result = classify_subject_matter_ai(test_case['data'])
        
        print(f"   预测类别: {result['predicted_category']}")
        print(f"   类别ID: {result['category_id']}")
        print(f"   置信度: {result['confidence']:.2f}")
        print(f"   分类方法: {result['method']}")
        print()


if __name__ == "__main__":
    test_subject_matter_classifier()
