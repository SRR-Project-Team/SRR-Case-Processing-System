"""
语言检测工具模块

本模块负责检测文本的语言类型，支持中文和英文的自动识别。

主要功能：
1. 检测文本是中文还是英文
2. 统计中文字符比例
3. 返回标准语言代码

作者: Project3 Team
版本: 1.0
"""
import re
from typing import Literal


def detect_language(text: str, threshold: float = 0.3) -> Literal['zh', 'en']:
    """
    检测文本的主要语言
    
    通过统计中文字符的比例来判断文本是中文还是英文。
    中文字符包括：汉字（CJK统一表意文字）、中文标点等。
    
    Args:
        text: 要检测的文本字符串
        threshold: 中文字符比例阈值，默认0.3（30%）
                  超过此阈值判定为中文，否则为英文
    
    Returns:
        'zh': 中文
        'en': 英文
    
    Examples:
        >>> detect_language("这是一段中文文本")
        'zh'
        >>> detect_language("This is English text")
        'en'
        >>> detect_language("混合文本 mixed text")  # 依据阈值判断
        'zh' or 'en'
    """
    if not text or not text.strip():
        # 空文本默认返回中文
        return 'zh'
    
    # 移除空白字符
    text = text.strip()
    
    # 统计总字符数（排除空格）
    total_chars = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
    
    if total_chars == 0:
        return 'zh'
    
    # 统计中文字符数量
    # 包括：
    # - CJK统一表意文字：\u4e00-\u9fff
    # - CJK扩展A：\u3400-\u4dbf
    # - 中文标点：\u3000-\u303f
    chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f]')
    chinese_chars = len(chinese_pattern.findall(text))
    
    # 计算中文字符比例
    chinese_ratio = chinese_chars / total_chars
    
    # 判断语言
    if chinese_ratio >= threshold:
        return 'zh'
    else:
        return 'en'


def get_language_name(language_code: str) -> str:
    """
    获取语言代码对应的语言名称
    
    Args:
        language_code: 语言代码 ('zh' 或 'en')
    
    Returns:
        语言名称字符串
    """
    language_names = {
        'zh': '中文',
        'en': 'English'
    }
    return language_names.get(language_code, '未知')


def is_chinese_text(text: str) -> bool:
    """
    判断文本是否主要为中文
    
    Args:
        text: 要检测的文本
    
    Returns:
        True: 中文为主
        False: 英文为主
    """
    return detect_language(text) == 'zh'


def is_english_text(text: str) -> bool:
    """
    判断文本是否主要为英文
    
    Args:
        text: 要检测的文本
    
    Returns:
        True: 英文为主
        False: 中文为主
    """
    return detect_language(text) == 'en'


def get_chinese_char_count(text: str) -> int:
    """
    统计文本中的中文字符数量
    
    Args:
        text: 要统计的文本
    
    Returns:
        中文字符数量
    """
    chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
    return len(chinese_pattern.findall(text))


def get_english_word_count(text: str) -> int:
    """
    统计文本中的英文单词数量
    
    Args:
        text: 要统计的文本
    
    Returns:
        英文单词数量（粗略统计）
    """
    # 提取英文单词（连续的字母）
    english_pattern = re.compile(r'[a-zA-Z]+')
    return len(english_pattern.findall(text))
