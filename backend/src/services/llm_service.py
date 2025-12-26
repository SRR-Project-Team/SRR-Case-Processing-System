"""
LLM API Service Module

Provides interaction functionality with Large Language Model APIs, including text summarization, Q&A, etc.
Supports OpenAI API (with proxy).
"""

import os
import logging
import time
from typing import Optional, Dict, Any
from openai import OpenAI
import httpx

class LLMService:
    """
    LLM API Service Class
    
    Provides interaction functionality with Large Language Model APIs, including text summarization, Q&A, etc.
    Supports OpenAI API (with proxy).
    """
    
    def __init__(self, api_key: str, provider: str = "openai", proxy_url: str = None, use_proxy: bool = False):
        """
        Initialize LLM Service
        
        Args:
            api_key: API key
            provider: API provider, "openai" (default: "openai")
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
                else:
                    self.logger.error(f"❌ Unknown provider: {provider}. Only 'openai' is supported.")
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
            else:
                self.logger.warning(f"⚠️ Unsupported provider: {self.provider}. Only 'openai' is supported.")
                return None
            
            self.logger.warning("⚠️ API response is empty or invalid")
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
            # Handle file paths that may contain special characters like #
            # Ensure the path is properly handled (no URL decoding needed for file paths)
            original_path = file_path
            
            # Convert to absolute path for reliable checking
            # Note: os.path.abspath handles # correctly, but we need to ensure
            # the path hasn't been URL-decoded incorrectly
            abs_file_path = os.path.abspath(file_path)
            
            # Log path information for debugging
            self.logger.debug(f"📄 Extracting content from file:")
            self.logger.debug(f"   Original path: {original_path}")
            self.logger.debug(f"   Absolute path: {abs_file_path}")
            self.logger.debug(f"   File exists: {os.path.exists(abs_file_path)}")
            
            if not os.path.exists(abs_file_path):
                # Try to find the file in common temp directories
                # Sometimes the file might be in a different location
                temp_dirs = ['/tmp', '/var/tmp', os.path.join(os.getcwd(), 'temp')]
                found_alternative = False
                
                for temp_dir in temp_dirs:
                    if os.path.exists(temp_dir):
                        # Try to find file by basename in temp directory
                        basename = os.path.basename(file_path)
                        alt_path = os.path.join(temp_dir, basename)
                        if os.path.exists(alt_path):
                            self.logger.info(f"✅ Found file in alternative location: {alt_path}")
                            abs_file_path = alt_path
                            found_alternative = True
                            break
                
                if not found_alternative:
                    self.logger.error(f"❌ File does not exist: {abs_file_path}")
                    self.logger.error(f"   Original path: {original_path}")
                    self.logger.error(f"   Current working directory: {os.getcwd()}")
                    # List files in the directory if it exists
                    dir_path = os.path.dirname(abs_file_path)
                    if os.path.exists(dir_path):
                        try:
                            files_in_dir = os.listdir(dir_path)
                            self.logger.error(f"   Files in directory: {files_in_dir[:10]}")  # Show first 10 files
                        except Exception as e:
                            self.logger.error(f"   Cannot list directory: {e}")
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

    def extract_fields_from_image(self, image_path: str, file_type: str) -> Optional[Dict[str, Any]]:
        """
        Use OpenAI Vision API to extract A-Q fields from PDF image
        
        Args:
            image_path: Path to the image file (PNG/JPEG)
            file_type: Type of file ("RCC" or "TMO") - must be explicitly specified
            
        Returns:
            Dictionary containing extracted A-Q fields, or None on failure
        """
        try:
            # Check API key and client
            if not self.api_key or not self.client:
                self.logger.warning("⚠️ API key not set or client not initialized, cannot use Vision API")
                return None
            
            # Read image file and encode to base64
            import base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Determine file extension
            import os
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext == '.png':
                image_format = "image/png"
            elif file_ext in ['.jpg', '.jpeg']:
                image_format = "image/jpeg"
            else:
                self.logger.error(f"❌ Unsupported image format: {file_ext}")
                return None
            
            # Validate file type
            if file_type not in ["RCC", "TMO"]:
                self.logger.error(f"❌ Invalid file_type: {file_type}. Must be 'RCC' or 'TMO'")
                return None
            
            # Build prompt - unified for both RCC and TMO with bilingual hints
            doc_type_hint = "RCC" if file_type == "RCC" else "TMO"
            
            prompt = f"""Extract the following fields from this {doc_type_hint} document image. Return a JSON object with these exact keys:
{{
  "A_date_received": "案件接收日期 (Date of Referral) (dd-MMM-yyyy format, e.g., 15-Jan-2024)",
  "B_source": "来源 (Source). 必须是以下4个值之一: 'TMO','ICC','RCC','Others'. 根据文档类型: 如果是TXT文件，返回'ICC'; 如果是ASD开头的PDF文件, 返回'TMO'; 如果是RCC开头的PDF文件, 返回'RCC'; 其他情况返回'Others'.",
  "C_case_number": "1823案件号 (Case Number)",
  "D_type": "案件类型 (Case Type: Emergency/Urgent/General)",
  "E_caller_name": "来电人姓名/检查员姓名 (Caller Name/Inspection Officer)",
  "F_contact_no": "联系电话 (Contact Number)",
  "G_slope_no": "斜坡编号 (Slope Number, e.g., 11SW-D/CR995 or 11SW-B/F199)",
  "H_location": "位置信息 (Location/District)",
  "I_nature_of_request": "请求性质摘要 (Nature of Request/Comments)",
  "J_subject_matter": "事项主题 (Subject Matter, usually Tree Trimming/Pruning)",
  "K_10day_rule_due_date": "10天规则截止日期 (10-day Rule Due Date) (dd-MMM-yyyy)",
  "L_icc_interim_due": "ICC临时回复截止日期 (ICC Interim Reply Due Date) (dd-MMM-yyyy)",
  "M_icc_final_due": "ICC最终回复截止日期 (ICC Final Reply Due Date) (dd-MMM-yyyy)",
  "N_works_completion_due": "工程完成截止日期 (Works Completion Due Date) (dd-MMM-yyyy)",
  "O1_fax_to_contractor": "发给承包商的传真日期 (Fax to Contractor Date) (YYYY-MM-DD)",
  "O2_email_send_time": "邮件发送时间 (Email Send Time) (if applicable)",
  "P_fax_pages": "传真页数 (Fax Pages)",
  "Q_case_details": "案件详情 (Case Details/Follow-up Actions)"
}}
特殊规则:
1. 如果来源(B)是TMO: E姓名格式为 "{{Name}} of TMO (DEVB)", F联系方式为 "TMO (DEVB)"
2. 如果来源(B)是1823: 从联系信息中提取姓名和电话/邮箱
3. 如果来源(B)是RCC: 从传真文件中提取信息
4. 如果投诉人匿名,E和F填"NA"

Extract all visible information from the document. If a field is not found, use empty string. For dates, use the specified format."""
            
            # Call OpenAI Vision API
            self.logger.info(f"🔄 Calling OpenAI Vision API for {file_type} document...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use gpt-4o for vision capabilities
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert document extraction assistant. Extract structured information from document images and return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_format};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # Low temperature for accurate extraction
            )
            
            # Extract response content
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content and content.strip():
                    # Parse JSON response
                    import json
                    # Remove markdown code blocks if present
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    elif content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    try:
                        extracted_data = json.loads(content)
                        self.logger.info(f"✅ Successfully extracted {len(extracted_data)} fields from {file_type} document")
                        return extracted_data
                    except json.JSONDecodeError as e:
                        self.logger.error(f"❌ Failed to parse JSON response: {e}")
                        self.logger.debug(f"Response content: {content}")
                        return None
            
            self.logger.warning("⚠️ Vision API response is empty or invalid")
            return None
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            self.logger.error(f"❌ Vision API extraction failed: {error_type} - {error_msg}")
            import traceback
            self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return None

    def extract_fields_from_text(self, text_content: str, email_content: str = None) -> Optional[Dict[str, Any]]:
        """
        Use OpenAI API to extract A-Q fields from TXT content
        
        Args:
            text_content: TXT file content
            email_content: Optional email content for additional context
            
        Returns:
            Dictionary containing extracted A-Q fields, or None on failure
        """
        try:
            # Check API key and client
            if not self.api_key or not self.client:
                self.logger.warning("⚠️ API key not set or client not initialized, cannot use OpenAI API")
                return None
            
            # Combine text and email content if available
            full_content = text_content
            if email_content:
                full_content = f"Main Content:\n{text_content}\n\nEmail Content:\n{email_content}"
            
            # Limit content length to avoid token limits (keep first 8000 characters)
            if len(full_content) > 8000:
                full_content = full_content[:8000] + "\n\n[... content truncated ...]"
            
            # Build prompt for TXT extraction
            prompt = """Extract the following fields from this TXT case file content. Return a JSON object with these exact keys:
{
  "A_date_received": "案件接收日期 (Case Creation Date, dd-MMM-yyyy format, e.g., 15-Jan-2024)",
  "B_source": "来源 (Source). 必须是以下4个值之一: 'TMO','ICC','RCC','Others'. 根据文档类型: 如果是TXT文件，返回'ICC'; 如果是ASD开头的PDF文件, 返回'TMO'; 如果是RCC开头的PDF文件, 返回'RCC'; 其他情况返回'Others'.",
  "C_case_number": "1823案件号 (1823 case number, if available)",
  "D_type": "案件类型 (Emergency/Urgent/General)",
  "E_caller_name": "来电人姓名 (Caller Name)",
  "F_contact_no": "联系电话 (Contact Number)",
  "G_slope_no": "斜坡编号 (Slope Number, e.g., 11SW-D/CR995)",
  "H_location": "位置信息 (Location/Venue)",
  "I_nature_of_request": "请求性质摘要 (Nature of Request summary)",
  "J_subject_matter": "事项主题 (Subject Matter)",
  "K_10day_rule_due_date": "10天规则截止日期 (dd-MMM-yyyy)",
  "L_icc_interim_due": "ICC临时回复截止日期 (dd-MMM-yyyy)",
  "M_icc_final_due": "ICC最终回复截止日期 (dd-MMM-yyyy)",
  "N_works_completion_due": "工程完成截止日期 (dd-MMM-yyyy)",
  "O1_fax_to_contractor": "发给承包商的传真日期 (YYYY-MM-DD)",
  "O2_email_send_time": "邮件发送时间 (Transaction Time, HH:MM:SS format if available)",
  "P_fax_pages": "传真页数 (File upload count, e.g., '1 + 2' if 2 files uploaded)",
  "Q_case_details": "案件详情 (Case Details, including nature of request)"
}

Extract all information from the text content. Look for patterns like:
- Case Creation Date : YYYY-MM-DD HH:MM:SS
- Channel : [source]
- 1823 case: [number]
- For ICC, enter {Last name} from contact information E_caller_name 
and enter ” {Mobile} / {Email Address}” in Contact No. 
Enter “NA” for (E) & (F) when the complainant is anonymous.
- Subject Matter : [subject]
- Transaction Time: [time]
- File upload: [count] file
- Contact information, slope numbers, locations, etc.

If a field is not found, use empty string. For dates, use the specified format."""
            
            # Call OpenAI API
            self.logger.info("🔄 Calling OpenAI API for TXT document extraction...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use gpt-4o-mini for text extraction (cost-effective)
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert case data extraction assistant. Extract structured information from case file text content and return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nText Content:\n{full_content}"
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # Low temperature for accurate extraction
            )
            
            # Extract response content
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content and content.strip():
                    # Parse JSON response
                    import json
                    # Remove markdown code blocks if present
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    elif content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    try:
                        extracted_data = json.loads(content)
                        self.logger.info(f"✅ Successfully extracted {len(extracted_data)} fields from TXT document")
                        return extracted_data
                    except json.JSONDecodeError as e:
                        self.logger.error(f"❌ Failed to parse JSON response: {e}")
                        self.logger.debug(f"Response content: {content}")
                        return None
            
            self.logger.warning("⚠️ OpenAI API response is empty or invalid")
            return None
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            self.logger.error(f"❌ Text extraction failed: {error_type} - {error_msg}")
            import traceback
            self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return None


# Global LLM service instance
_llm_service = None

def init_llm_service(api_key: str, provider: str = "openai", proxy_url: str = None, use_proxy: bool = False):
    """
    Initialize global LLM service instance
    
    Args:
        api_key: API key
        provider: API provider, "openai" (default: "openai")
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