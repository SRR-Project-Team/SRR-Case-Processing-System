"""
统一模型加载器
"""
import json
import pickle
import os
from pathlib import Path

class ModelLoader:
    """模型加载器"""
    
    @staticmethod
    def load_ai_training_data():
        """加载AI训练数据"""
        data_file = 'models/ai_models/training_data.pkl'
        if os.path.exists(data_file):
            with open(data_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    @staticmethod
    def load_slope_mapping():
        """加载斜坡位置映射"""
        mapping_file = 'models/mapping_rules/slope_location_mapping.json'
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def load_srr_rules():
        """加载SRR规则"""
        rules_file = 'models/config/srr_rules.json'
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'content': [], 'paragraphs': 0}
    
    @staticmethod
    def load_keyword_rules():
        """加载关键词规则"""
        keywords_file = 'models/config/keyword_rules.json'
        if os.path.exists(keywords_file):
            with open(keywords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def get_model_metadata():
        """获取模型元数据"""
        metadata_file = 'models/metadata.json'
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
