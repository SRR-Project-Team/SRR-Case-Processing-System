"""
AI案件class型classify器module

本module实现基于machine learning和规则match的智能案件class型classify系统，能够automatic将SRR案件
classify为Emergency（紧急）、Urgent（紧急）或General（一般）三种class型。

mainfunction：
1. 基于历史案件data进行machine learningtraining
2. 结合SRR规则文档进行规则match
3. 使用混合method（ML + 规则）提高classifyaccuracy
4. 支持modelcache和增量学习
5. 提供详细的classify报告和confidenceevaluate

技术实现：
- machine learning：RandomForestClassifier + TF-IDFvector化
- 规则match：基于关key词和语义的规则引擎
- data来源：SRR历史data + 投诉案件data + SRR规则文档

作者: Project3 Team
版本: 2.0
"""

import pandas as pd

def load_srr_rules():
    """
    加载SRR规则文档data
    
    从预process的JSON文件中加载SRR规则内容，这些规则用于规则匹配classify。
    规则文件包含从SRR rules.docx文档中extract的关键词和classify标准。
    
    Returns:
        dict: 包含规则内容的字典
        {
            'content': list,  # 规则text content列table
            'paragraphs': int  # 段落数量
        }
        
    Example:
        >>> rules = load_srr_rules()
        >>> print(f"加载了 {rules['paragraphs']} 个规则段落")
    """
    import json
    import os
    
    rules_file = 'models/config/srr_rules.json'
    if os.path.exists(rules_file):
        with open(rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print("⚠️ SRR规则文件不存在")
        return {'content': [], 'paragraphs': 0}


def load_training_data():
    """
    加载机器学习trainingdata
    
    从预process的pickle文件中加载历史案件data，用于trainingclassifymodel。
    data包含SRR案件data和投诉案件data，已进行清洗和预process。
    
    Returns:
        tuple: (srr_data, complaints_data)
            - srr_data (list): SRR案件data列table
            - complaints_data (list): 投诉案件data列table
            
    Example:
        >>> srr_data, complaints_data = load_training_data()
        >>> print(f"SRRdata: {len(srr_data)}条, 投诉data: {len(complaints_data)}条")
    """
    import pickle
    import os
    
    data_file = 'models/ai_models/training_data.pkl'
    if os.path.exists(data_file):
        with open(data_file, 'rb') as f:
            data = pickle.load(f)
        return data.get('srr_data', []), data.get('complaints_data', [])
    else:
        print("⚠️ trainingdata文件不存在")
        return [], []

import numpy as np
import re
from typing import Dict, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
from .ai_model_cache import get_cached_model, cache_model

class SRRCaseTypeClassifier:
    """SRR案件class型AIclassify器"""
    
    def __init__(self, data_path: str = "models"):
        self.data_path = data_path
        self.model = None
        self.vectorizer = None
        self.label_encoder = None
        self.feature_names = []
        self.classification_rules = {}
        self.historical_data = None
        
        # 紧急关key词 (Emergency indicators)
        self.emergency_keywords = [
            'collapse', 'collapsed', 'falling', 'fallen', 'immediate danger', 
            'urgent repair', 'safety risk', 'hazard', 'emergency', 'critical',
            '倒塌', '崩塌', '緊急', '危險', '立即', '安全風險', '嚴重', '緊急修復'
        ]
        
        # 紧急案件class型
        self.urgent_types = [
            'hazardous tree', 'fallen tree', 'drainage blockage', 'water seepage',
            'remove debris', 'safety concern', 'structural damage'
        ]
        
        # 一般案件class型  
        self.general_types = [
            'grass cutting', 'tree trimming', 'pruning', 'maintenance',
            'routine inspection', 'general enquiry', 'information request'
        ]
        
    def load_historical_data(self) -> pd.DataFrame:
        """加载历史data"""
        try:
            # loadSRR历史data
            csv_path = os.path.join(self.data_path, "SRR data 2021-2024.csv")
            df = pd.read_csv(csv_path, encoding='latin1')
            
            print(f"✅ 加载历史datasuccess: {len(df)} 条record")
            
            # cleanup列名
            df.columns = [col.strip().replace('\n', ' ') for col in df.columns]
            
            # 找到class型列
            type_col = None
            for col in df.columns:
                if 'type' in col.lower() and ('emergency' in col.lower() or 'urgent' in col.lower()):
                    type_col = col
                    break
            
            if type_col:
                # cleanupclass型data
                df[type_col] = df[type_col].fillna('General')
                df = df[df[type_col].isin(['Emergency', 'Urgent', 'General'])]
                
                print(f"class型分布:")
                print(df[type_col].value_counts())
                
            self.historical_data = df
            return df
            
        except Exception as e:
            print(f"⚠️ 加载历史datafailed: {e}")
            return pd.DataFrame()
    
    def load_srr_rules(self) -> Dict:
        """加载SRR规则"""
        try:
            from docx import Document
            
            rules_path = os.path.join(self.data_path, "SRR rules.docx")
            doc = Document(rules_path)
            
            rules = {
                'emergency_criteria': [],
                'urgent_criteria': [],
                'general_criteria': []
            }
            
            current_section = None
            for para in doc.paragraphs:
                text = para.text.strip().lower()
                if not text:
                    continue
                    
                # 识别规则部分
                if 'emergency' in text:
                    current_section = 'emergency_criteria'
                elif 'urgent' in text:
                    current_section = 'urgent_criteria'
                elif 'general' in text:
                    current_section = 'general_criteria'
                elif current_section and len(text) > 10:
                    rules[current_section].append(text)
            
            print(f"✅ 加载SRR规则success")
            for section, items in rules.items():
                print(f"{section}: {len(items)} 条规则")
                
            self.classification_rules = rules
            return rules
            
        except Exception as e:
            print(f"⚠️ 加载SRR规则failed: {e}")
            # 使用默认规则
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict:
        """获取默认classify规则"""
        return {
            'emergency_criteria': [
                'immediate safety risk to public',
                'structural collapse or imminent collapse',
                'fallen tree blocking road or causing danger',
                'severe water seepage causing instability',
                'major drainage blockage causing flooding'
            ],
            'urgent_criteria': [
                'hazardous tree requiring immediate attention',
                'water seepage requiring prompt investigation',
                'drainage blockage affecting slope stability',
                'debris removal for safety reasons',
                'slope maintenance affecting public safety'
            ],
            'general_criteria': [
                'routine grass cutting and maintenance',
                'general tree trimming and pruning',
                'regular slope inspection',
                'information enquiry',
                'non-urgent maintenance work'
            ]
        }
    
    def extract_features(self, case_data: Dict) -> Dict:
        """从案件data中extractfeature"""
        features = {}
        
        # 文本feature
        text_fields = [
            case_data.get('I_nature_of_request', ''),
            case_data.get('J_subject_matter', ''),
            case_data.get('Q_case_details', ''),
            case_data.get('B_source', '')
        ]
        
        combined_text = ' '.join(str(field) for field in text_fields).lower()
        
        # 紧急关key词计数
        emergency_count = sum(1 for keyword in self.emergency_keywords 
                            if keyword.lower() in combined_text)
        features['emergency_keywords'] = emergency_count
        
        # 案件来源feature
        source = case_data.get('B_source', '').lower()
        features['source_rcc'] = 1 if 'rcc' in source else 0
        features['source_icc'] = 1 if 'icc' in source else 0
        features['source_1823'] = 1 if '1823' in source else 0
        
        # 时间feature (周末/节假日可能更紧急)
        try:
            date_str = case_data.get('A_date_received', '')
            if date_str:
                # 简单的时间feature
                features['is_weekend'] = 0  # 可以根据实际日期计算
        except:
            features['is_weekend'] = 0
        
        # 斜坡编号feature (某些区域可能更容易有紧急情况)
        slope_no = case_data.get('G_slope_no', '')
        features['has_slope_no'] = 1 if slope_no else 0
        
        # 联系informationfeature (有联系方式可能更紧急)
        contact = case_data.get('F_contact_no', '')
        features['has_contact'] = 1 if contact else 0
        
        # 文本长度feature (详细描述可能table示更复杂的问题)
        features['text_length'] = len(combined_text)
        features['word_count'] = len(combined_text.split())
        
        return features
    
    def rule_based_classification(self, case_data: Dict) -> Tuple[str, float]:
        """基于规则的classify"""
        text_fields = [
            case_data.get('I_nature_of_request', ''),
            case_data.get('J_subject_matter', ''),
            case_data.get('Q_case_details', '')
        ]
        
        combined_text = ' '.join(str(field) for field in text_fields).lower()
        
        # 紧急情况检测
        emergency_score = 0
        for keyword in self.emergency_keywords:
            if keyword.lower() in combined_text:
                emergency_score += 1
        
        # check紧急案件class型
        for urgent_type in self.urgent_types:
            if urgent_type.lower() in combined_text:
                emergency_score += 0.5
        
        # check一般案件class型
        general_score = 0
        for general_type in self.general_types:
            if general_type.lower() in combined_text:
                general_score += 1
        
        # 来源权重
        source = case_data.get('B_source', '').lower()
        if 'rcc' in source:
            emergency_score += 0.3  # RCC案件通常更紧急
        elif '1823' in source:
            emergency_score += 0.2  # 1823投诉可能较紧急
        
        # 决策逻辑
        if emergency_score >= 2:
            return 'Emergency', min(0.9, 0.5 + emergency_score * 0.1)
        elif emergency_score >= 1 or (emergency_score > 0 and general_score == 0):
            return 'Urgent', min(0.8, 0.4 + emergency_score * 0.1)
        else:
            return 'General', min(0.7, 0.3 + general_score * 0.1)
    
    def train_ml_model(self) -> bool:
        """training机器学习model"""
        try:
            if self.historical_data is None or len(self.historical_data) == 0:
                print("⚠️ 没有历史data，无法trainingMLmodel")
                return False
            
            df = self.historical_data.copy()
            
            # 找到class型列
            type_col = None
            for col in df.columns:
                if 'type' in col.lower() and ('emergency' in col.lower() or 'urgent' in col.lower()):
                    type_col = col
                    break
            
            if not type_col:
                print("⚠️ 未找到class型列")
                return False
            
            # 准备trainingdata
            nature_col = None
            for col in df.columns:
                if 'nature' in col.lower():
                    nature_col = col
                    break
            
            if not nature_col:
                print("⚠️ 未找到投诉性质列")
                return False
            
            # cleanupdata
            df = df.dropna(subset=[nature_col, type_col])
            df[nature_col] = df[nature_col].fillna('')
            
            X = df[nature_col].astype(str)
            y = df[type_col]
            
            # 文本vector化
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            
            X_vectorized = self.vectorizer.fit_transform(X)
            
            # trainingmodel
            X_train, X_test, y_train, y_test = train_test_split(
                X_vectorized, y, test_size=0.2, random_state=42, stratify=y
            )
            
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train, y_train)
            
            # evaluatemodel
            y_pred = self.model.predict(X_test)
            print("✅ MLmodeltraining完成")
            print("\nmodel评估:")
            print(classification_report(y_test, y_pred))
            
            return True
            
        except Exception as e:
            print(f"⚠️ MLmodeltrainingfailed: {e}")
            return False
    
    def ml_classification(self, case_data: Dict) -> Tuple[str, float]:
        """基于机器学习的classify"""
        if self.model is None or self.vectorizer is None:
            return 'General', 0.3
        
        try:
            # 准备文本
            text_fields = [
                case_data.get('I_nature_of_request', ''),
                case_data.get('J_subject_matter', ''),
                case_data.get('Q_case_details', '')
            ]
            
            combined_text = ' '.join(str(field) for field in text_fields)
            
            # vector化
            X = self.vectorizer.transform([combined_text])
            
            # prediction
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            
            # getconfidence
            class_names = self.model.classes_
            pred_idx = np.where(class_names == prediction)[0][0]
            confidence = probabilities[pred_idx]
            
            return prediction, confidence
            
        except Exception as e:
            print(f"⚠️ MLclassifyfailed: {e}")
            return 'General', 0.3
    
    def classify_case_type(self, case_data: Dict) -> Dict:
        """综合classify案件class型"""
        
        # 规则classify
        rule_type, rule_confidence = self.rule_based_classification(case_data)
        
        # MLclassify
        ml_type, ml_confidence = self.ml_classification(case_data)
        
        # 综合决策
        if rule_confidence > 0.7:
            # 高confidence规则classify
            final_type = rule_type
            final_confidence = rule_confidence
            method = 'rule_based'
        elif ml_confidence > 0.6:
            # 高confidenceMLclassify
            final_type = ml_type
            final_confidence = ml_confidence
            method = 'machine_learning'
        elif rule_confidence > ml_confidence:
            # 规则classifyconfidence更高
            final_type = rule_type
            final_confidence = rule_confidence
            method = 'rule_based'
        else:
            # MLclassifyconfidence更高
            final_type = ml_type
            final_confidence = ml_confidence
            method = 'machine_learning'
        
        # securitycheck：确保return有效class型
        if final_type not in ['Emergency', 'Urgent', 'General']:
            final_type = 'General'
            final_confidence = 0.5
            method = 'default'
        
        return {
            'predicted_type': final_type,
            'confidence': final_confidence,
            'method': method,
            'rule_prediction': {'type': rule_type, 'confidence': rule_confidence},
            'ml_prediction': {'type': ml_type, 'confidence': ml_confidence},
            'type_code': {'Emergency': '1', 'Urgent': '2', 'General': '3'}[final_type]
        }
    
    def initialize(self) -> bool:
        """initializeclassify器，使用cache优化"""
        print("🚀 initializeSRR案件class型AIclassify器...")
        
        # 尝试从cacheget完整的classify器
        cache_key = "srr_case_type_classifier"
        cached_classifier = get_cached_model(cache_key)
        
        if cached_classifier:
            # 使用cache的classify器
            self.model = cached_classifier.get('model')
            self.vectorizer = cached_classifier.get('vectorizer')
            self.label_encoder = cached_classifier.get('label_encoder')
            self.feature_names = cached_classifier.get('feature_names', [])
            self.classification_rules = cached_classifier.get('classification_rules', {})
            self.historical_data = cached_classifier.get('historical_data')
            print("✅ 使用cache的AIclassify器 (跳过training)")
            return True
        
        # cache未命中，正常initialize
        # load历史data
        self.srr_data, self.complaints_data = load_training_data()
        
        # loadSRR规则
        self.rules_data = load_srr_rules()
        
        # trainingMLmodel
        ml_success = self.train_ml_model()
        
        # cacheclassify器
        try:
            classifier_cache = {
                'model': self.model,
                'vectorizer': self.vectorizer,
                'label_encoder': self.label_encoder,
                'feature_names': self.feature_names,
                'classification_rules': self.classification_rules,
                'historical_data': self.historical_data
            }
            cache_model(cache_key, classifier_cache)
        except Exception as e:
            print(f"⚠️ cacheclassify器failed: {e}")
        
        if ml_success:
            print("✅ AIclassify器initialize完成 (规则 + ML)")
        else:
            print("✅ AIclassify器initialize完成 (仅规则)")
        
        return True
    
    def get_classification_explanation(self, case_data: Dict, result: Dict) -> str:
        """获取classify解释"""
        explanation_parts = []
        
        # 基本information
        explanation_parts.append(f"classifyresult: {result['predicted_type']}")
        explanation_parts.append(f"confidence: {result['confidence']:.2f}")
        explanation_parts.append(f"classifymethod: {result['method']}")
        
        # 关key因素
        text_fields = [
            case_data.get('I_nature_of_request', ''),
            case_data.get('J_subject_matter', ''),
            case_data.get('Q_case_details', '')
        ]
        combined_text = ' '.join(str(field) for field in text_fields).lower()
        
        # 检测到的关key词
        detected_keywords = []
        for keyword in self.emergency_keywords:
            if keyword.lower() in combined_text:
                detected_keywords.append(keyword)
        
        if detected_keywords:
            explanation_parts.append(f"检测到紧急关键词: {', '.join(detected_keywords)}")
        
        # 来源影响
        source = case_data.get('B_source', '')
        if source:
            explanation_parts.append(f"案件来源: {source}")
        
        return ' | '.join(explanation_parts)

# 全局classify器instance
_classifier_instance = None

def get_classifier() -> SRRCaseTypeClassifier:
    """获取classify器instance (单例模式)"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SRRCaseTypeClassifier()
        _classifier_instance.initialize()
    return _classifier_instance

def classify_case_type_ai(case_data: Dict) -> Dict:
    """AIclassify案件class型的主要接口"""
    try:
        classifier = get_classifier()
        result = classifier.classify_case_type(case_data)
        
        # 添加解释
        explanation = classifier.get_classification_explanation(case_data, result)
        result['explanation'] = explanation
        
        print(f"🤖 AIclassifyresult: {result['predicted_type']} (confidence: {result['confidence']:.2f})")
        print(f"📝 classify依据: {explanation}")
        
        return result
        
    except Exception as e:
        print(f"⚠️ AIclassifyfailed: {e}")
        # return默认classify
        return {
            'predicted_type': 'General',
            'confidence': 0.5,
            'method': 'default',
            'type_code': '3',
            'explanation': f'AIclassifyfailed，使用默认classify: {e}'
        }

if __name__ == "__main__":
    # testclassify器
    print("🧪 测试SRR案件class型AIclassify器")
    
    # test案例
    test_cases = [
        {
            'I_nature_of_request': 'Fallen tree blocking road, immediate danger to public',
            'J_subject_matter': 'Emergency tree removal',
            'Q_case_details': 'Large tree fell across main road during storm, blocking traffic',
            'B_source': 'RCC',
            'G_slope_no': '11SW-D/R805'
        },
        {
            'I_nature_of_request': 'Grass cutting required for slope maintenance',
            'J_subject_matter': 'Routine maintenance',
            'Q_case_details': 'Regular grass cutting for slope upkeep',
            'B_source': 'ICC',
            'G_slope_no': '11SE-C/C805'
        },
        {
            'I_nature_of_request': 'Water seepage observed on slope',
            'J_subject_matter': 'Slope inspection required',
            'Q_case_details': 'Resident reported water seepage, needs investigation',
            'B_source': '1823',
            'G_slope_no': '11SW-B/F199'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试案例 {i} ---")
        result = classify_case_type_ai(test_case)
        print(f"predictionclass型: {result['predicted_type']}")
        print(f"class型代码: {result['type_code']}")
        print(f"解释: {result['explanation']}")
