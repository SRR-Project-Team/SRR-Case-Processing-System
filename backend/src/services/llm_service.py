"""
LLM API Service Module

Provides interaction functionality with Large Language Model APIs, including text summarization, Q&A, etc.
Supports both OpenAI API (with proxy) and Volcengine (Doubao) API.
"""

import os
import logging
import time
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
        
        # Ensure logger level matches root logger for debug visibility
        root_logger = logging.getLogger()
        if root_logger.level <= logging.DEBUG:
            self.logger.setLevel(logging.DEBUG)
        
        # Validate API key
        if not self.api_key:
            self.logger.warning("⚠️ API key not set, AI summarization will be unavailable")
            self.client = None
        else:
            # Initialize client based on provider
            try:
                if provider == "openai":
                    # NOTE:
                    #   We intentionally do NOT pass any custom `proxies` argument here,
                    #   because that can conflict with the versions of `openai` / `httpx`
                    #   installed and lead to errors like:
                    #       Client.__init__() got an unexpected keyword argument 'proxies'
                    #
                    #   Instead, we:
                    #   - Log the detected httpx version (to help debug env issues)
                    #   - Rely on environment variables (HTTP_PROXY/HTTPS_PROXY, etc.)
                    #     or OpenAI's own configuration for proxy handling.
                    try:
                        self.logger.info(f"ℹ️ Using httpx version: {httpx.__version__}")
                    except Exception:
                        # Best-effort logging only
                        pass

                    # configure timeout settings (connect timeout: 30s, read timeout: 60s)
                    timeout = httpx.Timeout(30.0, read=60.0, connect=30.0)
                    
                    # check for proxy configuration from environment variables or parameters
                    proxy_url_configured = None
                    
                    # Priority 1: Check environment variables (HTTPS_PROXY or HTTP_PROXY)
                    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
                    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
                    
                    if https_proxy:
                        proxy_url_configured = https_proxy
                        self.logger.info(f"🌐 Detected HTTPS_PROXY from environment: {https_proxy}")
                    elif http_proxy:
                        proxy_url_configured = http_proxy
                        self.logger.info(f"🌐 Detected HTTP_PROXY from environment: {http_proxy}")
                    
                    # Priority 2: Use proxy_url parameter if provided
                    if not proxy_url_configured and use_proxy and proxy_url:
                        proxy_url_configured = proxy_url
                        self.logger.info(f"🌐 Using proxy from parameter: {proxy_url}")
                    
                    # create custom http_client with timeout configuration
                    # httpx automatically reads proxy from environment variables when trust_env=True (default)
                    # We rely on environment variables (HTTPS_PROXY/HTTP_PROXY) for proxy configuration
                    http_client = httpx.Client(
                        timeout=timeout,
                        trust_env=True  # Allow reading proxy from environment variables
                    )
                    
                    if proxy_url_configured:
                        self.logger.info(f"✅ HTTP client configured with proxy from environment: {proxy_url_configured}")
                    else:
                        # Check if proxy is in environment
                        env_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
                        if env_proxy:
                            self.logger.info(f"✅ HTTP client will use proxy from environment variable: {env_proxy}")
                        else:
                            self.logger.info("ℹ️ HTTP client configured for direct connection (no proxy)")
                    
                    # use custom http_client to configure timeout and proxy
                    # Note: OpenAI SDK automatically sets the following headers:
                    # - Authorization: Bearer {api_key} (from api_key parameter)
                    # - Content-Type: application/json (automatically set by SDK)
                    self.client = OpenAI(
                        api_key=self.api_key,
                        http_client=http_client
                    )
                    
                    # Log API key status (masked for security)
                    api_key_preview = f"{self.api_key[:7]}...{self.api_key[-4:]}" if len(self.api_key) > 11 else "***"
                    self.logger.info(f"✅ OpenAI LLM client initialized successfully")
                    self.logger.debug(f"   - API Key: {api_key_preview}")
                    self.logger.debug(f"   - Headers: Authorization (Bearer) and Content-Type (application/json) are auto-configured")
                    self.logger.info(f"   - Timeout settings: connect=30s, read=60s")
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
            
            # Validate input text
            if text is None:
                self.logger.warning("⚠️ None text provided for summarization")
                return None
            
            if not isinstance(text, str):
                self.logger.error(f"❌ Invalid text type: {type(text)}, expected str")
                return None
            
            if not text.strip():
                self.logger.warning("⚠️ Empty or whitespace-only text provided for summarization")
                return None
            
            # Build request message (use single line string to avoid whitespace problem)
            text_snippet = text[:9000] if len(text) > 9000 else text
            message = (
                "Summarize the following text into a single fluent English sentence (max 150 words). "
                "The summary must include: "
                "1) case type, "
                "2) caller name, "
                "3) caller department, "
                "4) call-in date, "
                "5) key location, "
                "6) number of departments involved (infer if unclear), "
                "7) whether it falls under the slope and tree maintenance department, "
                "8) duration: from case open date to end date (or to now if missing). "
                "If information is unclear, infer cautiously from context. "
                f"Here is the text: {text_snippet}"
            )
            
            # Call API based on provider
            if self.provider == "openai":
                # 配置重试参数
                max_retries = 3
                retry_delay = 2  # initial delay 2 seconds
                
                for attempt in range(1, max_retries + 1):
                    try:
                        self.logger.info(f"🔄 Attempting OpenAI API call (attempt {attempt}/{max_retries})...")
                        
                        # API call to OpenAI
                        # Note: The following HTTP headers are automatically set by OpenAI SDK:
                        # - Authorization: Bearer {api_key} (from client initialization)
                        # - Content-Type: application/json (automatically set)
                        # These do not need to be manually specified in the API call.
                        response = self.client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are an expert case-log extraction assistant. You must interpret messy, noisy text logs and extract structured information reliably."
                                },
                                {
                                    "role": "user",
                                    "content": message
                                }
                            ],
                            max_tokens=300,
                            temperature=0.3
                        )
                        
                        # Extract response content
                        if response and response.choices and len(response.choices) > 0:
                            content = response.choices[0].message.content
                            if content and content.strip():
                                self.logger.info("✅ OpenAI AI summary generated successfully")
                                return content.strip()
                        
                        self.logger.warning("⚠️ API response is empty or invalid")
                        return None
                        
                    except Exception as api_error:
                        error_type = type(api_error).__name__
                        error_msg = str(api_error)
                        
                        # check if it is a timeout error or retryable error
                        is_timeout_error = "timeout" in error_msg.lower() or "APITimeoutError" in error_type
                        is_retryable = is_timeout_error or "rate limit" in error_msg.lower() or "503" in error_msg or "502" in error_msg
                        
                        if is_retryable and attempt < max_retries:
                            # calculate backoff delay (exponential backoff)
                            delay = retry_delay * (2 ** (attempt - 1))
                            self.logger.warning(
                                f"⚠️ OpenAI API call failed (attempt {attempt}/{max_retries}): {error_type} - {error_msg}. "
                                f"Retrying in {delay} seconds..."
                            )
                            time.sleep(delay)
                            continue
                        else:
                            # non-retryable error or maximum retry attempts reached
                            self.logger.error(f"❌ OpenAI API call failed after {attempt} attempt(s): {error_type} - {error_msg}")
                            
                            # log more detailed error information
                            import traceback
                            if is_timeout_error:
                                self.logger.error(
                                    "⏱️ Request timed out. This might be due to:\n"
                                    "  - Slow network connection\n"
                                    "  - OpenAI API server issues\n"
                                    "  - Request payload too large\n"
                                    "Consider reducing the input text length or checking your network connection."
                                )
                            self.logger.debug(f"Full traceback:\n{traceback.format_exc()}")
                            
                            return None
            
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
            
            self.logger.warning("⚠️ Unknown provider or API response is empty")
            return None
            
        except Exception as e:
            # catch all other exceptions
            error_type = type(e).__name__
            error_msg = str(e)
            self.logger.error(f"❌ AI summary generation failed: {error_type} - {error_msg}")
            
            # log full stack trace for debugging
            import traceback
            self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
            
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
            file_path: File path (can be relative or absolute)
            
        Returns:
            File content, returns None on failure
        """
        try:
            # Convert to absolute path for reliable checking
            abs_file_path = os.path.abspath(file_path)
            
            if not os.path.exists(abs_file_path):
                self.logger.error(f"❌ File does not exist: {abs_file_path}")
                self.logger.error(f"   Original path: {file_path}")
                self.logger.error(f"   Current working directory: {os.getcwd()}")
                return None
            
            if not os.path.isfile(abs_file_path):
                self.logger.error(f"❌ Path is not a file: {abs_file_path}")
                return None
            
            # Use absolute path for further processing
            file_path = abs_file_path
            
            file_extension = os.path.splitext(file_path)[1].lower()
            # Log debug info - will show if LOG_LEVEL=DEBUG is set
            self.logger.debug(f"📄 Processing file: {file_path}, type: {file_extension}")
            # Also print for immediate visibility in development
            print(f"📄 Processing file: {os.path.basename(file_path)}, type: {file_extension}", flush=True)
            
            if file_extension == '.txt':
                # Process text file
                return self._extract_txt_content(file_path)
                
            elif file_extension == '.pdf':
                # Process PDF file
                return self._extract_pdf_content(file_path)
                
            else:
                self.logger.warning(f"⚠️ Unsupported file type: {file_extension} for file: {file_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ File content extraction exception: {e}")
            self.logger.error(f"   File path: {file_path}")
            import traceback
            self.logger.error(traceback.format_exc())
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
            # NOTE:
            #   We intentionally use an absolute import here instead of a
            #   relative one (e.g. ``from ..utils...``), because ``services``
            #   is loaded as a namespace package when ``backend/src`` is added
            #   to ``sys.path`` (see ``main.py``). Using a relative import
            #   would fail if the package metadata is incomplete, which breaks
            #   AI summarization.
            from utils.file_utils import read_file_with_encoding
            return read_file_with_encoding(file_path)
        except Exception as e:
            self.logger.error(f"❌ TXT file content extraction failed: {e}")
            return None
    
    def _extract_pdf_content(self, file_path: str) -> Optional[str]:
        """
        Extract PDF file content for AI summarization.
        
        NOTE:
        - This method is intentionally kept lightweight and independent from the
          heavy OCR / business logic in `core.extractFromTMO` / `core.extractFromRCC`
          to avoid circular / fragile imports (which were causing
          "attempted relative import beyond top-level package" errors).
        - The main SRR extraction logic still uses those core modules; here we
          just need *some* text for the LLM to work with.
        """
        try:
            # First, try pdfplumber which usually gives the best text layout.
            try:
                import pdfplumber  # type: ignore
                text_parts = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                if text_parts:
                    return "\n".join(text_parts).strip()
            except Exception as e:
                self.logger.warning(f"⚠️ pdfplumber PDF extraction failed: {e}")
            
            # Fallback: basic PyPDF2 text extraction.
            try:
                import PyPDF2  # type: ignore
                text = ""
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text.strip() if text.strip() else None
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