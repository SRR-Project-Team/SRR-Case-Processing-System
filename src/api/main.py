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
from fastapi import FastAPI, UploadFile, File
from typing import List, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile

# Import custom modules
# Set Python path to import project modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from utils.file_utils import read_file_with_encoding

# Set database module path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_db_manager  # data库管理器

# initializedata库manager
# create全局data库managerinstance，用于process案件data的storage和检索
db_manager = get_db_manager()

# importLLMservice
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.services.llm_service import get_llm_service
from config.settings import LLM_API_KEY

# createFastAPI应用instance
# configurationAPI基本information，包括标题和版本号
app = FastAPI(
    title="SRR案件processAPI（A-Q新规则）", 
    version="1.0",
    description="智能SRR案件process系统，支持TXT、TMO PDF、RCC PDF文件格式"
)

# configurationCORSmiddleware
# 允许前端应用（React）CORS访问API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 前端开发service器地址
    allow_credentials=True,  # 允许携带认证information
    allow_methods=["*"],  # 允许所有HTTPmethod（GET、POST等）
    allow_headers=["*"],  # 允许所有请求头
)

# 在应用启动时initializeLLMservice
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # initializeLLMservice
    from src.services.llm_service import init_llm_service
    from config.settings import LLM_PROVIDER, OPENAI_PROXY_URL, OPENAI_USE_PROXY
    init_llm_service(LLM_API_KEY, LLM_PROVIDER, OPENAI_PROXY_URL, OPENAI_USE_PROXY)
    
    # Initialize historical case matcher (integrates Excel/CSV historical data)
    from src.services.historical_case_matcher import init_historical_matcher
    import os
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    db_path = os.path.join(data_dir, 'srr_cases.db')
    init_historical_matcher(data_dir, db_path)
    print("✅ Historical case matcher initialized with Excel/CSV data")

# create临时目录
# 用于storageupload的file，process完成后automaticcleanup
TEMP_DIR = tempfile.mkdtemp()
print(f"📁 临时文件目录: {TEMP_DIR}")


def determine_file_processing_type(filename: str, content_type: str) -> str:
    """
    根据文件名和内容class型确定process方式
    
    Args:
        filename (str): 文件名
        content_type (str): 文件MIMEclass型
        
    Returns:
        str: processclass型 ("txt", "tmo", "rcc", "unknown")
    """
    # checkfile扩展名
    if filename.lower().endswith('.txt'):
        return "txt"
    elif filename.lower().endswith('.pdf'):
        # 根据file名前缀判断PDFclass型
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
    扩展的文件class型validate，支持TXT和PDF文件
    
    Args:
        content_type (str): 文件MIMEclass型
        filename (str): 文件名
        
    Returns:
        bool: 是否为支持的文件class型
    """
    # 支持的fileclass型
    supported_types = ["text/plain", "application/pdf"]
    return content_type in supported_types


def get_file_type_error_message_extended() -> str:
    """
    获取扩展的文件class型errorinformation
    
    Returns:
        str: 文件class型errorinformation
    """
    return "仅支持TXT和PDF文件格式"


async def process_paired_txt_file(main_file_path: str, email_file_path: str = None) -> dict:
    """
    process配对的TXT文件（包含可选的邮件文件）
    
    Args:
        main_file_path: 主TXTfile path
        email_file_path: 邮件file path（可选）
        
    Returns:
        dict: extract的案件data
    """
    if email_file_path:
        # 如果有邮件file，需要manualprocess配对
        from core.extractFromTxt import extract_case_data_with_email
        from utils.file_utils import read_file_with_encoding
        
        # readfile内容
        main_content = read_file_with_encoding(main_file_path)
        email_content = read_file_with_encoding(email_file_path)
        
        # 使用配对process
        return extract_case_data_with_email(main_content, email_content, main_content)
    else:
        # 单独processTXTfile（会automatic检测邮件file）
        return extract_case_data_from_txt(main_file_path)


# 添加summarizefunctionfunction
async def generate_file_summary(file_content: str, filename: str, file_path: str = None) -> Dict[str, Any]:
    """
    生成文件内容summarize
    
    Args:
        file_content: 文件内容
        filename: 文件名
        file_path: file path（可选，用于直接文件process）
        
    Returns:
        包含summarizeresult的字典
    """
    try:
        # getLLMservice
        llm = get_llm_service()
        
        # 优先使用file path进行summarize（支持PDF等复杂file）
        if file_path:
            summary = llm.summarize_file(file_path, max_length=150)
        else:
            # 使用text content进行summarize
            summary = llm.summarize_text(file_content, max_length=150)
        
        if summary:
            return {
                "success": True,
                "summary": summary,
                "filename": filename,
                "source": "AI Summary"
            }
        else:
            return {
                "success": False,
                "error": "summarize生成failed",
                "filename": filename
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"summarizeprocessexception: {str(e)}",
            "filename": filename
        }

@app.post("/api/process-srr-file", response_model=ProcessingResult)
async def process_srr_file(file: UploadFile = File(...)):
    """
    processSRR案件文件，按新A-Q规则生成结构化data
    
    接收上传的TXT或PDF文件，根据文件class型和文件名自动选择相应的processmodule：
    - TXT文件：使用extractFromTxtmodule
    - ASD开头的PDF文件：使用extractFromTMOmodule
    - RCC开头的PDF文件：使用extractFromRCCmodule
    
    process流程：
    1. validate文件class型（支持text/plain和application/pdf）
    2. 根据文件名确定processclass型
    3. 保存文件到临时目录
    4. 调用相应的extractmodule
    5. 调用outputmodule创建结构化data
    6. returnprocessresult
    7. 清理临时文件
    
    Args:
        file (UploadFile): 上传的文件（TXT或PDF）
        
    Returns:
        ProcessingResult: 包含process状态和结构化data的响应object
        
    Raises:
        Exception: 文件process过程中的任何error都会被捕获并returnerrorresult
        
    Example:
        POST /api/process-srr-file
        Content-Type: multipart/form-data
        Body: file=ASD-WC-20250089-PP.pdf
        
        Response:
        {
            "filename": "ASD-WC-20250089-PP.pdf",
            "status": "success",
            "message": "SRR案件processsuccess",
            "structured_data": {
                "A_date_received": "2025-01-21T00:00:00",
                "B_source": "TMO",
                ...
            }
        }
    """
    try:
        # validatefileclass型
        if not validate_file_type_extended(file.content_type, file.filename):
            return create_error_result(file.filename, get_file_type_error_message_extended())
        
        # 确定processclass型
        processing_type = determine_file_processing_type(file.filename, file.content_type)
        
        if processing_type == "unknown":
            return create_error_result(
                file.filename, 
                f"不支持的文件class型或文件名格式。支持：TXT文件，或ASD/RCC开头的PDF文件"
            )
        
        # saveupload的file到临时目录
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # 根据processclass型调用相应的extractmodule
        if processing_type == "txt":
            # processTXTfile (使用智能encoding检测)
            extracted_data = extract_case_data_from_txt(file_path)
            
        elif processing_type == "tmo":
            # processTMO PDFfile
            extracted_data = extract_tmo_data(file_path)
            
        elif processing_type == "rcc":
            # processRCC PDFfile
            extracted_data = extract_rcc_data(file_path)
            
        else:
            return create_error_result(file.filename, "未知的processclass型")
        
        # 使用outputmodulecreate结构化data
        structured_data = create_structured_data(extracted_data)

        # save案件data到data库
        try:
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
            print(f"✅ 案件保存success，ID: {case_id}")
        except Exception as db_error:
            print(f"⚠️ data库保存failed: {db_error}")

        # read file content for summary
        try:
            file_content = read_file_with_encoding(file_path)
            
            # generate AI summary (传入file path以支持PDF等复杂file)
            summary_result = await generate_file_summary(file_content, file.filename, file_path)
            
        except Exception as e:
            # summary failed independent of main functionality
            summary_result = {
                "success": False,
                "error": f"summarize生成failed: {str(e)}"
            }

        # returnsuccessresult
        return create_success_result(file.filename, structured_data, summary_result)
        
        
    except Exception as e:
        # 捕获所有exception并returnerrorresult
        return create_error_result(
            file.filename if 'file' in locals() else "unknown",
            f"processfailed: {str(e)}"
        )
    finally:
        # cleanup临时file
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)


@app.post("/api/process-multiple-files")
async def process_multiple_files(files: List[UploadFile] = File(...)):
    """
    智能批量process多个SRR案件文件
    
    支持智能文件配对：自动识别TXT案件文件和对应的邮件文件，进行配对process。
    - TXT文件 + 对应的emailcontent_*.txt文件 → 配对process（包含邮件information）
    - 单独的TXT文件 → 独立process（自动检测邮件文件）
    - 单独的PDF文件 → 独立process
    - 独立的邮件文件 → 跳过process
    
    Args:
        files: 上传的文件列table
        
    Returns:
        dict: 包含所有文件processresult的字典
        {
            "total_files": 上传的文件总数,
            "processed_cases": 实际process的案件数,
            "successful": successprocess的案件数,
            "failed": failed的案件数,
            "skipped": 跳过的文件数,
            "results": [
                {
                    "case_id": "案件ID",
                    "main_file": "主文件名",
                    "email_file": "邮件文件名（如果有）",
                    "status": "success|error|skipped",
                    "message": "process消息",
                    "structured_data": {...} // 仅success时包含
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
                "message": "没有上传任何文件"
            }]
        }
    
    print(f"🚀 开始智能批量process {len(files)} 个文件...")
    
    # 第一步：create智能filepairing
    pairing = SmartFilePairing()
    
    # save所有file到临时目录并添加到pairing
    temp_files = {}
    for file in files:
        # validatefileclass型
        if not validate_file_type_extended(file.content_type, file.filename):
            print(f"⚠️ 跳过不支持的文件class型: {file.filename}")
            continue
        
        # savefile到临时目录
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        temp_files[file.filename] = file_path
        pairing.add_file(file.filename, file.content_type)
    
    # 第二步：get智能配对process计划
    processing_summary = pairing.get_processing_summary()
    processing_plan = processing_summary['processing_plan']
    
    print(f"📋 智能配对result:")
    print(f"   - 完整配对: {processing_summary['txt_with_email']} 个")
    print(f"   - 单独TXT: {processing_summary['txt_only']} 个")
    print(f"   - 跳过文件: {processing_summary['skipped']} 个")
    
    # 第三步：按照process计划执行
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
            
            print(f"\n📁 process计划 {i}/{len(processing_plan)}: {plan['description']}")
            
            if plan_type == 'skip':
                # 跳过独立的邮件file
                result = {
                    "case_id": case_id,
                    "main_file": main_file.filename,
                    "email_file": None,
                    "status": "skipped",
                    "message": f"跳过独立邮件文件（无对应TXT文件）"
                }
                results.append(result)
                skipped_count += 1
                print(f"⏭️ 跳过文件: {main_file.filename}")
                continue
            
            try:
                # getfile path
                main_file_path = temp_files.get(main_file.filename)
                email_file_path = temp_files.get(email_file.filename) if email_file else None
                
                if not main_file_path or not os.path.exists(main_file_path):
                    raise FileNotFoundError(f"主文件不存在: {main_file.filename}")
                
                # 根据fileclass型process
                if main_file.filename.lower().endswith('.txt'):
                    # processTXTfile（可能包含邮件配对）
                    extracted_data = await process_paired_txt_file(main_file_path, email_file_path)
                    
                elif main_file.filename.lower().endswith('.pdf'):
                    # processPDFfile
                    processing_type = determine_file_processing_type(main_file.filename, main_file.content_type)
                    
                    if processing_type == "tmo":
                        extracted_data = extract_tmo_data(main_file_path)
                    elif processing_type == "rcc":
                        extracted_data = extract_rcc_data(main_file_path)
                    else:
                        raise ValueError(f"不支持的PDF文件class型: {main_file.filename}")
                else:
                    raise ValueError(f"不支持的文件格式: {main_file.filename}")
                
                # create结构化data
                structured_data = create_structured_data(extracted_data)
                
                # successresult
                result = {
                    "case_id": case_id,
                    "main_file": main_file.filename,
                    "email_file": email_file.filename if email_file else None,
                    "status": "success",
                    "message": f"案件 {case_id} processsuccess" + (f"（包含邮件information）" if email_file else ""),
                    "structured_data": structured_data
                }
                results.append(result)
                successful_count += 1
                print(f"✅ 案件 {case_id} processsuccess")
        
            except Exception as e:
                # processfailed
                result = {
                    "case_id": case_id,
                    "main_file": main_file.filename,
                    "email_file": email_file.filename if email_file else None,
                    "status": "error",
                    "message": f"processfailed: {str(e)}"
                }
                results.append(result)
                failed_count += 1
                print(f"❌ 案件 {case_id} processfailed: {str(e)}")
    
    except Exception as outer_e:
        print(f"❌ 批量process过程中发生严重error: {str(outer_e)}")
        # 这里可以添加更多的errorprocess逻辑
    
    finally:
        # cleanup所有临时file
        for file_path in temp_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
    
    processed_cases = successful_count + failed_count
    print(f"\n📊 智能批量process完成:")
    print(f"   - 上传文件: {len(files)} 个")
    print(f"   - process案件: {processed_cases} 个")
    print(f"   - success: {successful_count} 个")
    print(f"   - failed: {failed_count} 个")
    print(f"   - 跳过: {skipped_count} 个")
    
    return {
        "total_files": len(files),
        "processed_cases": processed_cases,
        "successful": successful_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "results": results
    }


# 案件管理
@app.get("/api/cases")
async def get_cases(limit: int = 100, offset: int = 0):
    """获取案件列table"""
    cases = db_manager.get_cases(limit, offset)
    return {"cases": cases, "total": len(cases)}

@app.get("/api/cases/{case_id}")
async def get_case(case_id: int):
    """获取单个案件"""
    case = db_manager.get_case(case_id)
    if case:
        return case
    return {"error": "案件不存在"}

@app.get("/api/cases/search")
async def search_cases(q: str):
    """搜索案件"""
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
        from src.services.historical_case_matcher import get_historical_matcher
        
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
        from src.services.historical_case_matcher import get_historical_matcher
        
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
        from src.services.historical_case_matcher import get_historical_matcher
        
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
        from src.services.historical_case_matcher import get_historical_matcher
        
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
    健康check端点
    
    用于checkAPIservice是否正常运行，可用于负载均衡器或监控系统
    支持TXT和PDF文件process
    
    Returns:
        dict: 包含service状态的响应
        
    Example:
        GET /health
        
        Response:
        {
            "status": "healthy",
            "message": "SRR案件processAPI运行正常"
        }
    """
    return {"status": "healthy", "message": "SRR案件processAPI运行正常，支持TXT和PDF文件"}


if __name__ == "__main__":
    """
    程序入口点
    
    当直接运行此文件时启动FastAPIservice器
    configuration：
    - 主机: 0.0.0.0 (允许外部访问)
    - 端口: 8001
    - 自动重载: 启用 (开发模式)
    """
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8001, reload=True)
    