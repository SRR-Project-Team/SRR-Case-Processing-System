"""
SRR Case Processing API Main Program

This program provides RESTful API interfaces for processing SRR case TXT files and extracting structured data.
Adopts modular design, separating data extraction and output logic into independent modules.

Main functions:
1. Receive TXT file uploads
2. Validate file types
3. Call data extraction modules to process file content
4. Call output modules to format results
5. Return JSON format processing results

API endpoints:
- POST /api/process-srr-file: Process SRR case files
- GET /health: Health check

Author: Project3 Team
Version: 1.0
"""
from fastapi import FastAPI, UploadFile, File, Request, status
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
import tempfile
import time
import traceback
import logging

# Configure logging for debug visibility
# Set logging level based on environment variable, default to INFO for production
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
if log_level == "DEBUG":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    print("🔍 DEBUG logging enabled")
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Calculate backend directory path (used for .env file and module imports)
# From main.py (backend/src/api/main.py), we need to go up 3 levels:
#   1st dirname: backend/src/api/main.py -> backend/src/api
#   2nd dirname: backend/src/api -> backend/src  
#   3rd dirname: backend/src -> backend
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file (for local development)
# IMPORTANT: This must be done BEFORE importing config.settings
try:
    from dotenv import load_dotenv
    # Load .env file from backend directory
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        # Use override=True to ensure .env file values take precedence
        # This is important if environment variables are already set
        load_dotenv(env_path, override=True)
        print(f"✅ Loaded environment variables from {env_path}", flush=True)
        
        # Debug: Check if OPENAI_API_KEY was loaded (masked for security)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print(f"   ✓ OPENAI_API_KEY found (starts with: {api_key[:7]}...)", flush=True)
        else:
            print(f"   ⚠️  OPENAI_API_KEY not found in .env file", flush=True)
    else:
        print(f"ℹ️  No .env file found at {env_path}, using system environment variables", flush=True)
        print(f"   Looking for .env at: {env_path}", flush=True)
except ImportError:
    print("ℹ️  python-dotenv not installed, using system environment variables only")
    print("   Install with: pip install python-dotenv")

# Import custom modules
# Set Python path to import project modules
import sys
import os
# Add backend/src to path for importing core modules (core, utils, services, database)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add backend directory to path for importing config module
sys.path.append(backend_dir)

# Import core processing modules
from core.extractFromTxt import extract_case_data_from_txt  # TXT file processor
from core.extractFromTMO import extract_case_data_from_pdf as extract_tmo_data  # TMO PDF processor
from core.extractFromRCC import extract_case_data_from_pdf as extract_rcc_data  # RCC PDF processor
from core.output import (  # Output formatting module
    create_structured_data, 
    create_success_result, 
    create_error_result,
    validate_file_type,
    get_file_type_error_message,
    ProcessingResult
)
from utils.smart_file_pairing import SmartFilePairing  # Smart file pairing utility
from utils.file_utils import read_file_with_encoding,extract_text_from_pdf_fast,extract_content_with_multiple_methods

# Set database module path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_db_manager  # Database manager

# Initialize database manager
# Create global database manager instance for storing and retrieving case data
db_manager = get_db_manager()

# Import LLM service
from services.llm_service import get_llm_service
from config.settings import LLM_API_KEY

# Log API key status at module load time
if LLM_API_KEY:
    print(f"📝 Module loaded: OPENAI_API_KEY is configured (starts with: {LLM_API_KEY[:7]}...)", flush=True)
else:
    print(f"⚠️  Module loaded: OPENAI_API_KEY is NOT configured", flush=True)

# Create FastAPI application instance
# Configure API basic information, including title and version
app = FastAPI(
    title="SRR Case Processing API (A-Q New Rules)", 
    version="1.0",
    description="Intelligent SRR case processing system, supports TXT, TMO PDF, and RCC PDF file formats"
)

# Enable remote debugging if DEBUG_PORT is set (for Cloud Run debugging)
DEBUG_PORT = os.getenv("DEBUG_PORT")
if DEBUG_PORT:
    try:
        import debugpy
        debugpy.listen(("0.0.0.0", int(DEBUG_PORT)))
        print(f"🐛 Remote debugger listening on port {DEBUG_PORT}", flush=True)
        # Optional: Wait for debugger to attach before continuing
        # debugpy.wait_for_client()  # Uncomment if you want to wait for debugger
    except ImportError:
        print(f"⚠️  debugpy not installed. Install with: pip install debugpy", flush=True)
    except Exception as e:
        print(f"⚠️  Failed to start debugger: {e}", flush=True)

# Configure CORS middleware
# Allow frontend application (React) to access API via CORS
# Read allowed origins from environment variables, support both development and production environments
# Format: CORS_ALLOWED_ORIGINS="http://localhost:3000,https://your-firebase-app.web.app"
cors_allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if cors_allowed_origins_env:
    # Parse multiple origins from environment variable (comma-separated)
    allowed_origins = [origin.strip() for origin in cors_allowed_origins_env.split(",") if origin.strip()]
else:
    # Default to allow local development addresses
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

print(f"🌐 CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Frontend addresses read from environment variables (development and production)
    allow_credentials=True,  # Allow credentials
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all request headers
)

# Global exception handler - ensure CORS headers are returned even on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler, ensures CORS headers are returned even on errors"""
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": str(request.url),
        "method": request.method
    }
    # Print detailed error information to logs
    print(f"❌ Global exception caught: {error_detail}")
    traceback.print_exc()
    
    # Get the Origin header from the request
    origin = request.headers.get("origin")
    # Check if it's in the allowed origins list
    cors_headers = {}
    if origin and origin in allowed_origins:
        cors_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_detail,
        headers=cors_headers
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Request validation exception handler"""
    origin = request.headers.get("origin")
    cors_headers = {}
    if origin and origin in allowed_origins:
        cors_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
        headers=cors_headers
    )

# Initialize LLM service on application startup
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    # Initialize LLM service
    from services.llm_service import init_llm_service
    # Re-import settings to get fresh values (in case .env was loaded)
    import importlib
    import config.settings as settings_module
    importlib.reload(settings_module)
    from config.settings import LLM_API_KEY, LLM_PROVIDER, OPENAI_PROXY_URL, OPENAI_USE_PROXY
    
    # Also check directly from environment variable as fallback
    import os
    api_key = LLM_API_KEY or os.getenv("OPENAI_API_KEY")
    
    # Check if API key is configured
    if not api_key:
        print("⚠️  WARNING: OPENAI_API_KEY environment variable is not set!", flush=True)
        print("   AI summary generation will be disabled.", flush=True)
        print("   To enable AI features, please:", flush=True)
        print("   1. Set the OPENAI_API_KEY environment variable:", flush=True)
        print("      export OPENAI_API_KEY='your-api-key-here'", flush=True)
        print("   2. Or create a .env file in backend/ directory with:", flush=True)
        print("      OPENAI_API_KEY=your-api-key-here", flush=True)
        print("   3. Or set it in your shell before starting the server", flush=True)
    else:
        print(f"✅ OPENAI_API_KEY is configured (key starts with: {api_key[:7]}...)", flush=True)
    
    init_llm_service(api_key, LLM_PROVIDER, OPENAI_PROXY_URL, OPENAI_USE_PROXY)
    
    # Initialize historical case matcher (integrates Excel/CSV historical data)
    from services.historical_case_matcher import init_historical_matcher
    import os
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    db_path = os.path.join(data_dir, 'srr_cases.db')
    init_historical_matcher(data_dir, db_path)
    print("✅ Historical case matcher initialized with Excel/CSV data")

# Create temporary directory
# Used for storing uploaded files, automatically cleaned up after processing
TEMP_DIR = tempfile.mkdtemp()
print(f"📁 Temporary file directory: {TEMP_DIR}")


def determine_file_processing_type(filename: str, content_type: str) -> str:
    """
    Determine processing method based on filename and content type
    
    Args:
        filename (str): File name
        content_type (str): File MIME type
        
    Returns:
        str: Processing type ("txt", "tmo", "rcc", "unknown")
    """
    # Check file extension
    if filename.lower().endswith('.txt'):
        return "txt"
    elif filename.lower().endswith('.pdf'):
        # Determine PDF type based on filename prefix
        if filename.upper().startswith('ASD'):
            return "tmo"
        elif filename.upper().startswith('RCC'):
            return "rcc"
        else:
            return "unknown"
    else:
        return "unknown"


def validate_file_type_extended(content_type: str, filename: str) -> bool:
    """
    Extended file type validation, supports TXT and PDF files
    
    Args:
        content_type (str): File MIME type
        filename (str): File name
        
    Returns:
        bool: Whether it's a supported file type
    """
    # Supported file types
    supported_types = ["text/plain", "application/pdf"]
    return content_type in supported_types


def get_file_type_error_message_extended() -> str:
    """
    Get extended file type error information
    
    Returns:
        str: File type error information
    """
    return "Only TXT and PDF file formats are supported"


async def process_paired_txt_file(main_file_path: str, email_file_path: str = None) -> dict:
    """
    Process paired TXT files (including optional email file)
    
    Args:
        main_file_path: Main TXT file path
        email_file_path: Email file path (optional)
        
    Returns:
        dict: Extracted case data
    """
    if email_file_path:
        # If email file exists, need to manually process pairing
        from core.extractFromTxt import extract_case_data_with_email
        from utils.file_utils import read_file_with_encoding
        
        # Read file content
        main_content = read_file_with_encoding(main_file_path)
        email_content = read_file_with_encoding(email_file_path)
        
        # Use paired processing
        return extract_case_data_with_email(main_content, email_content, main_content)
    else:
        # Process TXT file separately (will automatically detect email file)
        return extract_case_data_from_txt(main_file_path)


# Add summary function
async def generate_file_summary(file_content: str, filename: str, file_path: str = None) -> Dict[str, Any]:
    """
    Generate file content summary
    
    Args:
        file_content: File content
        filename: File name
        file_path: File path (optional, for direct file processing)
        
    Returns:
        Dictionary containing summary result
    """
    try:
        # Get LLM service
        llm = get_llm_service()
        
        # Prefer using file path for summarization (supports complex files like PDF)
        summary = None
        if file_path:
            # Check if file still exists before attempting to read it
            # File might have been cleaned up or moved
            import os
            if os.path.exists(file_path) and os.path.isfile(file_path):
                summary = llm.summarize_file(file_path, max_length=150)
                
                # If file-based extraction failed (e.g. unsupported/corrupted PDF),
                # gracefully fall back to using the already-read text content.
                if not summary and file_content:
                    print("ℹ️ File-based AI summary failed, falling back to text-content summarization", flush=True)
                    summary = llm.summarize_text(file_content, max_length=150)
            else:
                # File doesn't exist (may have been cleaned up), use text content instead
                print(f"⚠️ File no longer exists at {file_path}, using text content for summarization", flush=True)
                if file_content:
                    summary = llm.summarize_text(file_content, max_length=150)
                else:
                    print("⚠️ No file content available for summarization", flush=True)
        else:
            # Use text content for summarization
            summary = llm.summarize_text(file_content, max_length=150)
        
        if summary:
            return {
                "success": True,
                "summary": summary,
                "filename": filename,
                "source": "AI Summary"
            }
        else:
            # Provide specific error message based on LLM service state
            error_message = "AI summary generation failed. Please check backend logs for details."
            
            # Check LLM service configuration
            if not llm.api_key or not llm.client:
                error_message = (
                    "AI service not configured. OPENAI_API_KEY environment variable is missing or invalid.\n"
                    "Please set the environment variable:\n"
                    "  export OPENAI_API_KEY='your-api-key-here'\n"
                    "Or create a .env file with:\n"
                    "  OPENAI_API_KEY=your-api-key-here"
                )
            elif file_path:
                # If using file path, might be file extraction issue
                import os
                if not os.path.exists(file_path):
                    error_message = "File not found. Unable to extract content for summary."
                else:
                    error_message = "Unable to extract content from file. The file may be corrupted or in an unsupported format."
            else:
                # If using text content, might be API call issue
                error_message = "AI API call failed. Please check API configuration and network connection."
            
            return {
                "success": False,
                "error": error_message,
                "filename": filename
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Summary processing exception: {str(e)}",
            "filename": filename
        }

@app.post("/api/process-srr-file", response_model=ProcessingResult)
async def process_srr_file(file: UploadFile = File(...)):
    """
    Process SRR case files, generate structured data according to new A-Q rules
    
    Receives uploaded TXT or PDF files, automatically selects the appropriate processing module based on file type and filename:
    - TXT files: Use extractFromTxt module
    - PDF files starting with ASD: Use extractFromTMO module
    - PDF files starting with RCC: Use extractFromRCC module
    
    Processing flow:
    1. Validate file type (supports text/plain and application/pdf)
    2. Determine processing type based on filename
    3. Save file to temporary directory
    4. Call corresponding extraction module
    5. Call output module to create structured data
    6. Return processing result
    7. Clean up temporary files
    
    Args:
        file (UploadFile): Uploaded file (TXT or PDF)
        
    Returns:
        ProcessingResult: Response object containing processing status and structured data
        
    Raises:
        Exception: Any errors during file processing will be caught and return error result
        
    Example:
        POST /api/process-srr-file
        Content-Type: multipart/form-data
        Body: file=ASD-WC-20250089-PP.pdf
        
        Response:
        {
            "filename": "ASD-WC-20250089-PP.pdf",
            "status": "success",
            "message": "SRR case processing successful",
            "structured_data": {
                "A_date_received": "2025-01-21T00:00:00",
                "B_source": "TMO",
                ...
            }
        }
    """
    start_time = time.time()
    file_path = None
    
    try:
        # Add detailed logging - request start
        print(f"📥 [{time.strftime('%Y-%m-%d %H:%M:%S')}] File upload request received")
        print(f"   Filename: {file.filename}")
        print(f"   Content-Type: {file.content_type}")
        print(f"   Temporary directory: {TEMP_DIR}")
        
        # Validate file type
        if not validate_file_type_extended(file.content_type, file.filename):
            print(f"❌ File type validation failed: {file.content_type}")
            return create_error_result(file.filename, get_file_type_error_message_extended())
        
        # Determine processing type
        processing_type = determine_file_processing_type(file.filename, file.content_type)
        print(f"📋 File processing type: {processing_type}")
        
        if processing_type == "unknown":
            print(f"❌ Unsupported file type: {file.filename}")
            return create_error_result(
                file.filename, 
                f"Unsupported file type or filename format. Supported: TXT files, or PDF files starting with ASD/RCC"
            )
        
        # Save uploaded file to temporary directory - use chunked reading to optimize memory usage
        file_path = os.path.join(TEMP_DIR, file.filename)
        print(f"💾 Starting to save file to: {file_path}")
        
        file_size = 0
        with open(file_path, "wb") as buffer:
            # Chunked reading, 8KB per chunk, avoid loading large files into memory at once
            chunk_size = 8192
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                buffer.write(chunk)
                file_size += len(chunk)
        
        print(f"✅ File save completed: {file.filename}, size: {file_size} bytes ({file_size / 1024:.2f} KB)")
        
        read_time = time.time() - start_time
        print(f"⏱️  File reading time: {read_time:.2f} seconds")
        
        # Call corresponding extraction module based on processing type
        extract_start = time.time()
        print(f"🔄 Starting data extraction, processing type: {processing_type}")
        
        if processing_type == "txt":
            # Process TXT file (using intelligent encoding detection)
            content = read_file_with_encoding(file_path)
            extracted_data = extract_case_data_from_txt(file_path)
            
        elif processing_type == "tmo":
            # Process TMO PDF file
            content = extract_text_from_pdf_fast(file_path)
            extracted_data = extract_tmo_data(file_path)
            
        elif processing_type == "rcc":
            # Process RCC PDF file
            # extractPDF内容
            content = extract_content_with_multiple_methods(file_path)
            extracted_data = extract_rcc_data(file_path)
            
        else:
            print(f"❌ Unknown processing type: {processing_type}")
            return create_error_result(file.filename, "Unknown processing type")
        
        extract_time = time.time() - extract_start
        print(f"✅ Data extraction completed, time: {extract_time:.2f} seconds")
        
        # Use output module to create structured data
        print(f"📊 Starting to create structured data")
        structured_data = create_structured_data(extracted_data)
        print(f"✅ Structured data creation completed")

        # Save case data to database
        try:
            print(f"💾 Starting to save case data to database")
            case_data = {
                'A_date_received': structured_data.A_date_received,
                'B_source': structured_data.B_source,
                'C_case_number': structured_data.C_case_number,
                'D_type': structured_data.D_type,
                'E_caller_name': structured_data.E_caller_name,
                'F_contact_no': structured_data.F_contact_no,
                'G_slope_no': structured_data.G_slope_no,
                'H_location': structured_data.H_location,
                'I_nature_of_request': structured_data.I_nature_of_request,
                'J_subject_matter': structured_data.J_subject_matter,
                'K_10day_rule_due_date': structured_data.K_10day_rule_due_date,
                'L_icc_interim_due': structured_data.L_icc_interim_due,
                'M_icc_final_due': structured_data.M_icc_final_due,
                'N_works_completion_due': structured_data.N_works_completion_due,
                'O1_fax_to_contractor': structured_data.O1_fax_to_contractor,
                'O2_email_send_time': structured_data.O2_email_send_time,
                'P_fax_pages': structured_data.P_fax_pages,
                'Q_case_details': structured_data.Q_case_details,
                'original_filename': file.filename,
                'file_type': processing_type
            }
            case_id = db_manager.save_case(case_data)
            print(f"✅ Case saved successfully, ID: {case_id}")
        except Exception as db_error:
            print(f"⚠️ Database save failed: {db_error}")
            import traceback
            traceback.print_exc()

        # Read file content for summary
        try:
            print(f"🤖 Starting to generate AI summary", flush=True)
            
            # Generate AI summary (pass file path to support complex files like PDF)
            summary_result = await generate_file_summary(content, file.filename, file_path)
            print(f"✅ AI summary generation completed", flush=True)
            
        except Exception as e:
            # Summary failed independent of main functionality
            print(f"⚠️ AI summary generation failed: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            summary_result = {
                "success": False,
                "error": f"Summary generation failed: {str(e)}"
            }

        # Return success result
        total_time = time.time() - start_time
        print(f"🎉 File processing completed: {file.filename}, total time: {total_time:.2f} seconds")
        return create_success_result(file.filename, structured_data, summary_result)
        
        
    except Exception as e:
        # Catch all exceptions and return error result
        total_time = time.time() - start_time if 'start_time' in locals() else 0
        error_msg = str(e)
        print(f"❌ File processing failed: {file.filename if 'file' in locals() else 'unknown'}")
        print(f"   Error message: {error_msg}")
        print(f"   Time taken: {total_time:.2f} seconds")
        traceback.print_exc()
        
        return create_error_result(
            file.filename if 'file' in locals() else "unknown",
            f"Processing failed: {error_msg}"
        )
    finally:
        # Clean up temporary file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️  Temporary file cleaned up: {file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to clean up temporary file: {cleanup_error}")


@app.post("/api/process-multiple-files")
async def process_multiple_files(files: List[UploadFile] = File(...)):
    """
    Intelligently batch process multiple SRR case files
    
    Supports intelligent file pairing: automatically identifies TXT case files and corresponding email files for paired processing.
    - TXT file + corresponding emailcontent_*.txt file → Paired processing (includes email information)
    - Standalone TXT file → Independent processing (automatically detects email file)
    - Standalone PDF file → Independent processing
    - Standalone email file → Skip processing
    
    Args:
        files: List of uploaded files
        
    Returns:
        dict: Dictionary containing processing results for all files
        {
            "total_files": Total number of uploaded files,
            "processed_cases": Actual number of processed cases,
            "successful": Number of successfully processed cases,
            "failed": Number of failed cases,
            "skipped": Number of skipped files,
            "results": [
                {
                    "case_id": "Case ID",
                    "main_file": "Main file name",
                    "email_file": "Email file name (if any)",
                    "status": "success|error|skipped",
                    "message": "Processing message",
                    "structured_data": {...} // Only included on success
                },
                ...
            ]
        }
    """
    if not files:
        return {
            "total_files": 0,
            "processed_cases": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "results": [{
                "case_id": "none",
                "main_file": "none",
                "email_file": None,
                "status": "error",
                "message": "No files uploaded"
            }]
        }
    
    print(f"🚀 Starting intelligent batch processing of {len(files)} files...")
    
    # Step 1: Create intelligent file pairing
    pairing = SmartFilePairing()
    
    # Save all files to temporary directory and add to pairing
    temp_files = {}
    for file in files:
        # Validate file type
        if not validate_file_type_extended(file.content_type, file.filename):
            print(f"⚠️ Skipping unsupported file type: {file.filename}")
            continue
        
        # Save file to temporary directory
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        temp_files[file.filename] = file_path
        pairing.add_file(file.filename, file.content_type)
    
    # Step 2: Get intelligent pairing processing plan
    processing_summary = pairing.get_processing_summary()
    processing_plan = processing_summary['processing_plan']
    
    print(f"📋 Intelligent pairing results:")
    print(f"   - Complete pairs: {processing_summary['txt_with_email']} files")
    print(f"   - Standalone TXT: {processing_summary['txt_only']} files")
    print(f"   - Skipped files: {processing_summary['skipped']} files")
    
    # Step 3: Execute according to processing plan
    results = []
    successful_count = 0
    failed_count = 0
    skipped_count = 0
    
    try:
        for i, plan in enumerate(processing_plan, 1):
            case_id = plan['case_id']
            plan_type = plan['type']
            main_file = plan['main_file']
            email_file = plan.get('email_file')
            
            print(f"\n📁 Processing plan {i}/{len(processing_plan)}: {plan['description']}")
            
            if plan_type == 'skip':
                # Skip standalone email file
                result = {
                    "case_id": case_id,
                    "main_file": main_file.filename,
                    "email_file": None,
                    "status": "skipped",
                    "message": f"Skipping standalone email file (no corresponding TXT file)"
                }
                results.append(result)
                skipped_count += 1
                print(f"⏭️ Skipping file: {main_file.filename}")
                continue
            
            try:
                # Get file path
                main_file_path = temp_files.get(main_file.filename)
                email_file_path = temp_files.get(email_file.filename) if email_file else None
                
                if not main_file_path or not os.path.exists(main_file_path):
                    raise FileNotFoundError(f"Main file does not exist: {main_file.filename}")
                
                # Process based on file type
                if main_file.filename.lower().endswith('.txt'):
                    # Process TXT file (may include email pairing)
                    extracted_data = await process_paired_txt_file(main_file_path, email_file_path)
                    
                elif main_file.filename.lower().endswith('.pdf'):
                    # Process PDF file
                    processing_type = determine_file_processing_type(main_file.filename, main_file.content_type)
                    
                    if processing_type == "tmo":
                        extracted_data = extract_tmo_data(main_file_path)
                    elif processing_type == "rcc":
                        extracted_data = extract_rcc_data(main_file_path)
                    else:
                        raise ValueError(f"Unsupported PDF file type: {main_file.filename}")
                else:
                    raise ValueError(f"Unsupported file format: {main_file.filename}")
                
                # Create structured data
                structured_data = create_structured_data(extracted_data)
                
                # Success result
                result = {
                    "case_id": case_id,
                    "main_file": main_file.filename,
                    "email_file": email_file.filename if email_file else None,
                    "status": "success",
                    "message": f"Case {case_id} processed successfully" + (f" (includes email information)" if email_file else ""),
                    "structured_data": structured_data
                }
                results.append(result)
                successful_count += 1
                print(f"✅ Case {case_id} processed successfully")
        
            except Exception as e:
                # Processing failed
                result = {
                    "case_id": case_id,
                    "main_file": main_file.filename,
                    "email_file": email_file.filename if email_file else None,
                    "status": "error",
                    "message": f"Processing failed: {str(e)}"
                }
                results.append(result)
                failed_count += 1
                print(f"❌ Case {case_id} processing failed: {str(e)}")
    
    except Exception as outer_e:
        print(f"❌ Serious error occurred during batch processing: {str(outer_e)}")
        # Can add more error processing logic here
    
    finally:
        # Clean up all temporary files
        for file_path in temp_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
    
    processed_cases = successful_count + failed_count
    print(f"\n📊 Intelligent batch processing completed:")
    print(f"   - Uploaded files: {len(files)} files")
    print(f"   - Processed cases: {processed_cases} cases")
    print(f"   - Successful: {successful_count} cases")
    print(f"   - Failed: {failed_count} cases")
    print(f"   - Skipped: {skipped_count} files")
    
    return {
        "total_files": len(files),
        "processed_cases": processed_cases,
        "successful": successful_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "results": results
    }


# Case management
@app.get("/api/cases")
async def get_cases(limit: int = 100, offset: int = 0):
    """Get case list"""
    cases = db_manager.get_cases(limit, offset)
    return {"cases": cases, "total": len(cases)}

@app.get("/api/cases/{case_id}")
async def get_case(case_id: int):
    """Get single case"""
    case = db_manager.get_case(case_id)
    if case:
        return case
    return {"error": "Case does not exist"}

@app.get("/api/cases/search")
async def search_cases(q: str):
    """Search cases"""
    cases = db_manager.search_cases(q)
    return {"cases": cases, "query": q}

@app.post("/api/find-similar-cases")
async def find_similar_cases(case_data: dict):
    """
    Find similar historical cases based on current case information
    Searches ONLY historical Excel/CSV data (database excluded):
    - Slopes Complaints 2021 (4,047 cases)
    - SRR data 2021-2024 (1,251 cases)
    Total: 5,298 historical cases
    
    Args:
        case_data: Dictionary containing case information to match against
        
    Returns:
        dict: Similar cases with similarity scores and match details
    """
    try:
        # Use the same module path as in startup_event to ensure the
        # global matcher singleton is shared and properly initialized
        from services.historical_case_matcher import get_historical_matcher
        
        matcher = get_historical_matcher()
        
        # Get parameters
        limit = case_data.get('limit', 10)
        min_similarity = case_data.get('min_similarity', 0.3)
        
        # Find similar cases across all historical data
        similar_cases = matcher.find_similar_cases(
            current_case=case_data,
            limit=limit,
            min_similarity=min_similarity
        )
        
        return {
            "status": "success",
            "total_found": len(similar_cases),
            "similar_cases": similar_cases,
            "search_criteria": {
                "location": case_data.get('H_location'),
                "slope_no": case_data.get('G_slope_no'),
                "caller_name": case_data.get('E_caller_name'),
                "subject_matter": case_data.get('J_subject_matter')
            },
            "data_sources": {
                "slopes_complaints_2021": "4,047 cases",
                "srr_data_2021_2024": "1,251 cases",
                "total_searchable": "5,298 historical cases (database excluded)"
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to find similar cases: {str(e)}"
        }


@app.get("/api/case-statistics")
async def get_case_statistics(
    location: str = None,
    slope_no: str = None,
    venue: str = None
):
    """
    Get comprehensive statistics from historical Excel/CSV data ONLY
    Searches across (database excluded):
    - Slopes Complaints 2021 (4,047 cases)
    - SRR data 2021-2024 (1,251 cases)
    Total: 5,298 historical cases
    
    Query parameters:
        location: Location to filter by
        slope_no: Slope number to filter by
        venue: Venue name to filter by
        
    Returns:
        dict: Comprehensive statistics from historical data only
    """
    try:
        # Use the same module path as in startup_event to ensure the
        # global matcher singleton is shared and properly initialized
        from services.historical_case_matcher import get_historical_matcher
        
        matcher = get_historical_matcher()
        
        stats = matcher.get_case_statistics(
            location=location,
            slope_no=slope_no,
            venue=venue
        )
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to get statistics: {str(e)}"
        }


@app.get("/api/tree-info")
async def get_tree_info(slope_no: str):
    """
    Get tree information for a specific slope
    Searches tree inventory (32405 trees)
    
    Query parameters:
        slope_no: Slope number to search for
        
    Returns:
        dict: List of trees on the slope with details
    """
    try:
        # Use the same module path as in startup_event to ensure the
        # global matcher singleton is shared and properly initialized
        from services.historical_case_matcher import get_historical_matcher
        
        matcher = get_historical_matcher()
        trees = matcher.get_tree_info(slope_no)
        
        return {
            "status": "success",
            "slope_no": slope_no,
            "total_trees": len(trees),
            "trees": trees
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get tree information: {str(e)}"
        }


@app.get("/api/location-slopes")
async def get_location_slopes(location: str):
    """
    Get slope numbers associated with a location
    Uses historical learning from 5,298 cases
    
    Query parameters:
        location: Location name or partial match
        
    Returns:
        dict: List of slope numbers found at this location
    """
    try:
        # Use the same module path as in startup_event to ensure the
        # global matcher singleton is shared and properly initialized
        from services.historical_case_matcher import get_historical_matcher
        
        matcher = get_historical_matcher()
        slopes = matcher.get_slopes_for_location(location)
        
        return {
            "status": "success",
            "location": location,
            "total_slopes": len(slopes),
            "slopes": slopes,
            "note": "Learned from historical complaint records"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get slopes for location: {str(e)}"
        }


@app.get("/health")
def health_check():
    """
    Health check endpoint
    
    Used to check if the API service is running normally, can be used by load balancers or monitoring systems
    Supports TXT and PDF file processing
    
    Returns:
        dict: Response containing service status
        
    Example:
        GET /health
        
        Response:
        {
            "status": "healthy",
            "message": "SRR case processing API is running normally"
        }
    """
    return {"status": "healthy", "message": "SRR case processing API is running normally, supports TXT and PDF files"}


if __name__ == "__main__":
    """
    Program entry point
    
    Start FastAPI server when running this file directly
    Configuration:
    - Host: 0.0.0.0 (allows external access)
    - Port: 8001
    - Auto reload: Enabled (development mode)
    
    Environment variables:
    - LOG_LEVEL=DEBUG: Enable debug logging (shows all debug messages)
    - PYTHONUNBUFFERED=1: Enable unbuffered output (immediate log visibility)
    
    Example:
        LOG_LEVEL=DEBUG python -u main.py
    """
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8001, reload=True)
    