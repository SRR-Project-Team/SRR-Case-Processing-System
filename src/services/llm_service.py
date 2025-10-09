"""
大模型API服务模块

提供与大模型API的交互功能，包括文本总结、问答等。
使用火山引擎官方SDK。
"""

import os
import logging
from typing import Optional, Dict, Any
from volcenginesdkarkruntime import Ark

class LLMService:
    """
    大模型API服务类
    
    提供与大模型API的交互功能，包括文本总结、问答等。
    使用火山引擎官方SDK。
    """
    
    def __init__(self, api_key: str):
        """
        初始化LLM服务
        
        Args:
            api_key: API密钥
        """
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # 验证API密钥
        if not self.api_key:
            self.logger.warning("⚠️ API密钥未设置，AI总结功能将不可用")
            self.client = None
        else:
            # 初始化火山引擎客户端
            try:
                self.client = Ark(api_key=self.api_key)
                self.logger.info("✅ 火山引擎LLM客户端初始化成功")
            except Exception as e:
                self.logger.error(f"❌ 火山引擎LLM客户端初始化失败: {e}")
                self.client = None
    
    def summarize_text(self, text: str, max_length: int = 200) -> Optional[str]:
        """
        使用大模型API对文本进行一句话总结
        
        Args:
            text: 需要总结的文本
            max_length: 总结的最大长度
            
        Returns:
            总结结果，失败时返回None
        """
        try:
            # 检查API密钥和客户端
            if not self.api_key or not self.client:
                self.logger.warning("⚠️ API密钥未设置或客户端未初始化，无法生成AI总结")
                return None
            
            # 构建请求消息
            message = f'''Summarize the content of the following text in one sentence, 
           and no more than {max_length} characters.:\n\n{text[:3000]} '''  # 限制文本长度
            
            # 调用火山引擎API
            response = self.client.chat.completions.create(
                model="doubao-seed-1-6-flash-250828",
                messages=[{"content": message, "role": "user"}]
            )
            
            # 提取响应内容
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content and content.strip():
                    self.logger.info("✅ AI总结生成成功")
                    return content.strip()
            
            self.logger.warning("⚠️ API响应为空或无效")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ AI总结生成失败: {e}")
            return None

    def summarize_file(self, file_path: str, max_length: int = 100) -> Optional[str]:
        """
        使用大模型API对文件进行总结
        
        Args:
            file_path: 文件路径
            max_length: 总结的最大长度
            
        Returns:
            总结结果，失败时返回None
        """
        try:
            # 检查API密钥和客户端
            if not self.api_key or not self.client:
                self.logger.warning("⚠️ API密钥未设置或客户端未初始化，无法生成AI总结")
                return None
            
            # 根据文件类型提取内容
            file_content = self._extract_file_content(file_path)
            if not file_content:
                self.logger.error(f"❌ 无法提取文件内容: {file_path}")
                return None
            
            # 调用文本总结方法
            return self.summarize_text(file_content, max_length)
            
        except Exception as e:
            self.logger.error(f"❌ 文件总结处理异常: {e}")
            return None
    
    def _extract_file_content(self, file_path: str) -> Optional[str]:
        """
        根据文件类型提取内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容，失败时返回None
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"❌ 文件不存在: {file_path}")
                return None
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                # 处理文本文件
                return self._extract_txt_content(file_path)
                
            elif file_extension == '.pdf':
                # 处理PDF文件
                return self._extract_pdf_content(file_path)
                
            else:
                self.logger.warning(f"⚠️ 不支持的文件类型: {file_extension}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 文件内容提取异常: {e}")
            return None
    
    def _extract_txt_content(self, file_path: str) -> Optional[str]:
        """
        提取TXT文件内容
        
        Args:
            file_path: TXT文件路径
            
        Returns:
            文件内容，失败时返回None
        """
        try:
            from ..utils.file_utils import read_file_with_encoding
            return read_file_with_encoding(file_path)
        except Exception as e:
            self.logger.error(f"❌ TXT文件内容提取失败: {e}")
            return None
    
    def _extract_pdf_content(self, file_path: str) -> Optional[str]:
        """
        提取PDF文件内容
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            PDF文本内容，失败时返回None
        """
        try:
            # 首先尝试使用项目中已有的PDF处理逻辑
            from ..core.extractFromTMO import extract_text_from_pdf_fast
            from ..core.extractFromRCC import extract_text_with_ocr_fast
            
            # 尝试使用TMO模块的快速文本提取
            try:
                text = extract_text_from_pdf_fast(file_path)
                if text and text.strip():
                    return text.strip()
            except Exception as e:
                self.logger.warning(f"⚠️ TMO快速PDF提取失败: {e}")
            
            # 尝试使用RCC模块的OCR提取
            try:
                text = extract_text_with_ocr_fast(file_path)
                if text and text.strip():
                    return text.strip()
            except Exception as e:
                self.logger.warning(f"⚠️ RCC OCR提取失败: {e}")
            
            # 如果都失败，使用基础的PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
            except Exception as e:
                self.logger.error(f"❌ PyPDF2提取失败: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ PDF内容提取异常: {e}")
            return None


# 全局LLM服务实例
_llm_service = None

def init_llm_service(api_key: str):
    """
    初始化全局LLM服务实例
    
    Args:
        api_key: API密钥
    """
    global _llm_service
    _llm_service = LLMService(api_key)

def get_llm_service() -> LLMService:
    """
    获取全局LLM服务实例
    
    Returns:
        LLMService实例
    """
    global _llm_service
    if _llm_service is None:
        raise RuntimeError("LLM服务未初始化，请先调用init_llm_service()")
    return _llm_service