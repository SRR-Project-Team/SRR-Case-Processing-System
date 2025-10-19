"""
LLM API Service Module

Provides interaction functionality with Large Language Model APIs, including text summarization, Q&A, etc.
Supports both OpenAI API (with proxy) and Volcengine (Doubao) API.
"""

import os
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
import httpx
# from volcenginesdkarkruntime import Ark  # Volcengine API (kept for future use)

class LLMService:
    """
    LLM API Service Class
    
    Provides interaction functionality with Large Language Model APIs, including text summarization, Q&A, etc.
    Supports both OpenAI API (with proxy) and Volcengine (Doubao) API.
    """
    
    def __init__(self, api_key: str, provider: str = "openai", proxy_url: str = None, use_proxy: bool = False):
        """
        Initialize LLM Service
        
        Args:
            api_key: API key
            provider: API provider, "openai" or "volcengine" (default: "openai")
            proxy_url: Proxy URL (e.g., "http://127.0.0.1:7890")
            use_proxy: Whether to use proxy (default: False)
        """
        self.api_key = api_key
        self.provider = provider
        self.proxy_url = proxy_url
        self.use_proxy = use_proxy
        self.logger = logging.getLogger(__name__)
        
        # Validate API key
        if not self.api_key:
            self.logger.warning("⚠️ API key not set, AI summarization will be unavailable")
            self.client = None
        else:
            # Initialize client based on provider
            try:
                if provider == "openai":
                    # Configure proxy if needed
                    if use_proxy and proxy_url:
                        self.logger.info(f"🌐 Using proxy: {proxy_url}")
                        http_client = httpx.Client(proxy=proxy_url, timeout=30.0)
                        self.client = OpenAI(api_key=self.api_key, http_client=http_client)
                    else:
                        self.client = OpenAI(api_key=self.api_key)
                    self.logger.info("✅ OpenAI LLM client initialized successfully")
                elif provider == "volcengine":
                    # Volcengine API (commented out, kept for future use)
                    # from volcenginesdkarkruntime import Ark
                    # self.client = Ark(api_key=self.api_key)
                    # self.logger.info("✅ Volcengine LLM client initialized successfully")
                    self.logger.warning("⚠️ Volcengine API is currently disabled")
                    self.client = None
                else:
                    self.logger.error(f"❌ Unknown provider: {provider}")
                    self.client = None
            except Exception as e:
                self.logger.error(f"❌ LLM client initialization failed: {e}")
                self.client = None
    
    def summarize_text(self, text: str, max_length: int = 600) -> Optional[str]:
        """
        Use LLM API to summarize text in one sentence
        
        Args:
            text: Text to be summarized
            max_length: Maximum length of the summary
            
        Returns:
            Summary result, returns None on failure
        """
        try:
            # Check API key and client
            if not self.api_key or not self.client:
                self.logger.warning("⚠️ API key not set or client not initialized, cannot generate AI summary")
                return None
            
            # Build request message
            message = f'''Summarize the text with key elements(case type, caller name and etc) in a natural and fluent sentence. 
            In addition, the summary should include the short answer of the duration of the case open up to end date or now, 
            the number of departments it has been handled by, and whether it falls under the responsibility of the slope and tree maintenance department.
            No more than {max_length} words.:\n\n{text[:9000]} '''  # Limit text length
            
            # Call API based on provider
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Using GPT-4o-mini for cost efficiency
                    messages=[{"role": "user", "content": message}],
                    max_tokens=300,
                    temperature=0.3
                )
                
                # Extract response content
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content and content.strip():
                        self.logger.info("✅ OpenAI AI summary generated successfully")
                        return content.strip()
            
            elif self.provider == "volcengine":
                # Volcengine API (commented out, kept for future use)
                # response = self.client.chat.completions.create(
                #     model="doubao-seed-1-6-flash-250828",
                #     messages=[{"content": message, "role": "user"}]
                # )
                # 
                # if response and response.choices and len(response.choices) > 0:
                #     content = response.choices[0].message.content
                #     if content and content.strip():
                #         self.logger.info("✅ Volcengine AI summary generated successfully")
                #         return content.strip()
                self.logger.warning("⚠️ Volcengine API is currently disabled")
                return None
            
            self.logger.warning("⚠️ API response is empty or invalid")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ AI summary generation failed: {e}")
            return None

    def summarize_file(self, file_path: str, max_length: int = 100) -> Optional[str]:
        """
        Use LLM API to summarize file
        
        Args:
            file_path: File path
            max_length: Maximum length of summary
            
        Returns:
            Summary result, returns None on failure
        """
        try:
            # Check API key and client
            if not self.api_key or not self.client:
                self.logger.warning("⚠️ API key not set or client not initialized, cannot generate AI summary")
                return None
            
            # Extract content based on file type
            file_content = self._extract_file_content(file_path)
            if not file_content:
                self.logger.error(f"❌ Unable to extract file content: {file_path}")
                return None
            
            # Call text summarization method
            return self.summarize_text(file_content, max_length)
            
        except Exception as e:
            self.logger.error(f"❌ File summarization processing exception: {e}")
            return None
    
    def _extract_file_content(self, file_path: str) -> Optional[str]:
        """
        Extract content based on file type
        
        Args:
            file_path: File path
            
        Returns:
            File content, returns None on failure
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"❌ File does not exist: {file_path}")
                return None
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                # Process text file
                return self._extract_txt_content(file_path)
                
            elif file_extension == '.pdf':
                # Process PDF file
                return self._extract_pdf_content(file_path)
                
            else:
                self.logger.warning(f"⚠️ Unsupported file type: {file_extension}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ File content extraction exception: {e}")
            return None
    
    def _extract_txt_content(self, file_path: str) -> Optional[str]:
        """
        Extract TXT file content
        
        Args:
            file_path: TXT file path
            
        Returns:
            File content, returns None on failure
        """
        try:
            from ..utils.file_utils import read_file_with_encoding
            return read_file_with_encoding(file_path)
        except Exception as e:
            self.logger.error(f"❌ TXT file content extraction failed: {e}")
            return None
    
    def _extract_pdf_content(self, file_path: str) -> Optional[str]:
        """
        Extract PDF file content
        
        Args:
            file_path: PDF file path
            
        Returns:
            PDF text content, returns None on failure
        """
        try:
            # First try to use existing PDF processing logic in the project
            from ..core.extractFromTMO import extract_text_from_pdf_fast
            from ..core.extractFromRCC import extract_text_with_ocr_fast
            
            # Try to use TMO module fast text extraction
            try:
                text = extract_text_from_pdf_fast(file_path)
                if text and text.strip():
                    return text.strip()
            except Exception as e:
                self.logger.warning(f"⚠️ TMO fast PDF extraction failed: {e}")
            
            # Try to use RCC module OCR extraction
            try:
                text = extract_text_with_ocr_fast(file_path)
                if text and text.strip():
                    return text.strip()
            except Exception as e:
                self.logger.warning(f"⚠️ RCC OCR extraction failed: {e}")
            
            # If all fail, use basic PyPDF2
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text.strip()
            except Exception as e:
                self.logger.error(f"❌ PyPDF2 extraction failed: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ PDF content extraction exception: {e}")
            return None


# Global LLM service instance
_llm_service = None

def init_llm_service(api_key: str, provider: str = "openai", proxy_url: str = None, use_proxy: bool = False):
    """
    Initialize global LLM service instance
    
    Args:
        api_key: API key
        provider: API provider, "openai" or "volcengine" (default: "openai")
        proxy_url: Proxy URL (e.g., "http://127.0.0.1:7890")
        use_proxy: Whether to use proxy (default: False)
    """
    global _llm_service
    _llm_service = LLMService(api_key, provider, proxy_url, use_proxy)

def get_llm_service() -> LLMService:
    """
    Get global LLM service instance
    
    Returns:
        LLMService instance
    """
    global _llm_service
    if _llm_service is None:
        raise RuntimeError("LLM service not initialized, please call init_llm_service() first")
    return _llm_service