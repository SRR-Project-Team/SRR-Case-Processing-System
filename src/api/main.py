"""
SRR案件处理API主程序

本程序提供RESTful API接口，用于处理SRR案件的TXT文件并提取结构化数据。
采用模块化设计，将数据提取和输出逻辑分离到独立模块中。

主要功能：
1. 接收TXT文件上传
2. 验证文件类型
3. 调用数据提取模块处理文件内容
4. 调用输出模块格式化结果
5. 返回JSON格式的处理结果

API端点：
- POST /api/process-srr-file: 处理SRR案件文件
- GET /health: 健康检查

作者: Project3 Team
版本: 1.0
"""
from fastapi import FastAPI, UploadFile, File
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile

# 导入自定义模块
# 设置Python路径以导入项目模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入核心处理模块
from core.extractFromTxt import extract_case_data_from_txt  # TXT文件处理器
from core.extractFromTMO import extract_case_data_from_pdf as extract_tmo_data  # TMO PDF处理器
from core.extractFromRCC import extract_case_data_from_pdf as extract_rcc_data  # RCC PDF处理器
from core.output import (  # 输出格式化模块
    create_structured_data, 
    create_success_result, 
    create_error_result,
    validate_file_type,
    get_file_type_error_message,
    ProcessingResult
)
from utils.smart_file_pairing import SmartFilePairing  # 智能文件配对器

# 设置数据库模块路径
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_db_manager  # 数据库管理器

# 初始化数据库管理器
# 创建全局数据库管理器实例，用于处理案件数据的存储和检索
db_manager = get_db_manager()

# 创建FastAPI应用实例
# 配置API基本信息，包括标题和版本号
app = FastAPI(
    title="SRR案件处理API（A-Q新规则）", 
    version="1.0",
    description="智能SRR案件处理系统，支持TXT、TMO PDF、RCC PDF文件格式"
)

# 配置CORS中间件
# 允许前端应用（React）跨域访问API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 前端开发服务器地址
    allow_credentials=True,  # 允许携带认证信息
    allow_methods=["*"],  # 允许所有HTTP方法（GET、POST等）
    allow_headers=["*"],  # 允许所有请求头
)

# 创建临时目录
# 用于存储上传的文件，处理完成后自动清理
TEMP_DIR = tempfile.mkdtemp()
print(f"📁 临时文件目录: {TEMP_DIR}")


def determine_file_processing_type(filename: str, content_type: str) -> str:
    """
    根据文件名和内容类型确定处理方式
    
    Args:
        filename (str): 文件名
        content_type (str): 文件MIME类型
        
    Returns:
        str: 处理类型 ("txt", "tmo", "rcc", "unknown")
    """
    # 检查文件扩展名
    if filename.lower().endswith('.txt'):
        return "txt"
    elif filename.lower().endswith('.pdf'):
        # 根据文件名前缀判断PDF类型
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
    扩展的文件类型验证，支持TXT和PDF文件
    
    Args:
        content_type (str): 文件MIME类型
        filename (str): 文件名
        
    Returns:
        bool: 是否为支持的文件类型
    """
    # 支持的文件类型
    supported_types = ["text/plain", "application/pdf"]
    return content_type in supported_types


def get_file_type_error_message_extended() -> str:
    """
    获取扩展的文件类型错误信息
    
    Returns:
        str: 文件类型错误信息
    """
    return "仅支持TXT和PDF文件格式"


async def process_paired_txt_file(main_file_path: str, email_file_path: str = None) -> dict:
    """
    处理配对的TXT文件（包含可选的邮件文件）
    
    Args:
        main_file_path: 主TXT文件路径
        email_file_path: 邮件文件路径（可选）
        
    Returns:
        dict: 提取的案件数据
    """
    if email_file_path:
        # 如果有邮件文件，需要手动处理配对
        from core.extractFromTxt import extract_case_data_with_email
        from utils.file_utils import read_file_with_encoding
        
        # 读取文件内容
        main_content = read_file_with_encoding(main_file_path)
        email_content = read_file_with_encoding(email_file_path)
        
        # 使用配对处理
        return extract_case_data_with_email(main_content, email_content, main_content)
    else:
        # 单独处理TXT文件（会自动检测邮件文件）
        return extract_case_data_from_txt(main_file_path)




@app.post("/api/process-srr-file", response_model=ProcessingResult)
async def process_srr_file(file: UploadFile = File(...)):
    """
    处理SRR案件文件，按新A-Q规则生成结构化数据
    
    接收上传的TXT或PDF文件，根据文件类型和文件名自动选择相应的处理模块：
    - TXT文件：使用extractFromTxt模块
    - ASD开头的PDF文件：使用extractFromTMO模块
    - RCC开头的PDF文件：使用extractFromRCC模块
    
    处理流程：
    1. 验证文件类型（支持text/plain和application/pdf）
    2. 根据文件名确定处理类型
    3. 保存文件到临时目录
    4. 调用相应的提取模块
    5. 调用output模块创建结构化数据
    6. 返回处理结果
    7. 清理临时文件
    
    Args:
        file (UploadFile): 上传的文件（TXT或PDF）
        
    Returns:
        ProcessingResult: 包含处理状态和结构化数据的响应对象
        
    Raises:
        Exception: 文件处理过程中的任何错误都会被捕获并返回错误结果
        
    Example:
        POST /api/process-srr-file
        Content-Type: multipart/form-data
        Body: file=ASD-WC-20250089-PP.pdf
        
        Response:
        {
            "filename": "ASD-WC-20250089-PP.pdf",
            "status": "success",
            "message": "SRR案件处理成功",
            "structured_data": {
                "A_date_received": "2025-01-21T00:00:00",
                "B_source": "TMO",
                ...
            }
        }
    """
    try:
        # 验证文件类型
        if not validate_file_type_extended(file.content_type, file.filename):
            return create_error_result(file.filename, get_file_type_error_message_extended())
        
        # 确定处理类型
        processing_type = determine_file_processing_type(file.filename, file.content_type)
        
        if processing_type == "unknown":
            return create_error_result(
                file.filename, 
                f"不支持的文件类型或文件名格式。支持：TXT文件，或ASD/RCC开头的PDF文件"
            )
        
        # 保存上传的文件到临时目录
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # 根据处理类型调用相应的提取模块
        if processing_type == "txt":
            # 处理TXT文件 (使用智能编码检测)
            extracted_data = extract_case_data_from_txt(file_path)
            
        elif processing_type == "tmo":
            # 处理TMO PDF文件
            extracted_data = extract_tmo_data(file_path)
            
        elif processing_type == "rcc":
            # 处理RCC PDF文件
            extracted_data = extract_rcc_data(file_path)
            
        else:
            return create_error_result(file.filename, "未知的处理类型")
        
        # 使用output模块创建结构化数据
        structured_data = create_structured_data(extracted_data)

        # 保存案件数据到数据库
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
            print(f"✅ 案件保存成功，ID: {case_id}")
        except Exception as db_error:
            print(f"⚠️ 数据库保存失败: {db_error}")

        # 返回成功结果
        return create_success_result(file.filename, structured_data)
        
    except Exception as e:
        # 捕获所有异常并返回错误结果
        return create_error_result(
            file.filename if 'file' in locals() else "unknown",
            f"处理失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)


@app.post("/api/process-multiple-files")
async def process_multiple_files(files: List[UploadFile] = File(...)):
    """
    智能批量处理多个SRR案件文件
    
    支持智能文件配对：自动识别TXT案件文件和对应的邮件文件，进行配对处理。
    - TXT文件 + 对应的emailcontent_*.txt文件 → 配对处理（包含邮件信息）
    - 单独的TXT文件 → 独立处理（自动检测邮件文件）
    - 单独的PDF文件 → 独立处理
    - 独立的邮件文件 → 跳过处理
    
    Args:
        files: 上传的文件列表
        
    Returns:
        dict: 包含所有文件处理结果的字典
        {
            "total_files": 上传的文件总数,
            "processed_cases": 实际处理的案件数,
            "successful": 成功处理的案件数,
            "failed": 失败的案件数,
            "skipped": 跳过的文件数,
            "results": [
                {
                    "case_id": "案件ID",
                    "main_file": "主文件名",
                    "email_file": "邮件文件名（如果有）",
                    "status": "success|error|skipped",
                    "message": "处理消息",
                    "structured_data": {...} // 仅成功时包含
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
    
    print(f"🚀 开始智能批量处理 {len(files)} 个文件...")
    
    # 第一步：创建智能文件配对器
    pairing = SmartFilePairing()
    
    # 保存所有文件到临时目录并添加到配对器
    temp_files = {}
    for file in files:
        # 验证文件类型
        if not validate_file_type_extended(file.content_type, file.filename):
            print(f"⚠️ 跳过不支持的文件类型: {file.filename}")
            continue
        
        # 保存文件到临时目录
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        temp_files[file.filename] = file_path
        pairing.add_file(file.filename, file.content_type)
    
    # 第二步：获取智能配对处理计划
    processing_summary = pairing.get_processing_summary()
    processing_plan = processing_summary['processing_plan']
    
    print(f"📋 智能配对结果:")
    print(f"   - 完整配对: {processing_summary['txt_with_email']} 个")
    print(f"   - 单独TXT: {processing_summary['txt_only']} 个")
    print(f"   - 跳过文件: {processing_summary['skipped']} 个")
    
    # 第三步：按照处理计划执行
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
            
            print(f"\n📁 处理计划 {i}/{len(processing_plan)}: {plan['description']}")
            
            if plan_type == 'skip':
                # 跳过独立的邮件文件
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
                # 获取文件路径
                main_file_path = temp_files.get(main_file.filename)
                email_file_path = temp_files.get(email_file.filename) if email_file else None
                
                if not main_file_path or not os.path.exists(main_file_path):
                    raise FileNotFoundError(f"主文件不存在: {main_file.filename}")
                
                # 根据文件类型处理
                if main_file.filename.lower().endswith('.txt'):
                    # 处理TXT文件（可能包含邮件配对）
                    extracted_data = await process_paired_txt_file(main_file_path, email_file_path)
                    
                elif main_file.filename.lower().endswith('.pdf'):
                    # 处理PDF文件
                    processing_type = determine_file_processing_type(main_file.filename, main_file.content_type)
                    
                    if processing_type == "tmo":
                        extracted_data = extract_tmo_data(main_file_path)
                    elif processing_type == "rcc":
                        extracted_data = extract_rcc_data(main_file_path)
                    else:
                        raise ValueError(f"不支持的PDF文件类型: {main_file.filename}")
                else:
                    raise ValueError(f"不支持的文件格式: {main_file.filename}")
                
                # 创建结构化数据
                structured_data = create_structured_data(extracted_data)
                
                # 成功结果
                result = {
                    "case_id": case_id,
                    "main_file": main_file.filename,
                    "email_file": email_file.filename if email_file else None,
                    "status": "success",
                    "message": f"案件 {case_id} 处理成功" + (f"（包含邮件信息）" if email_file else ""),
                    "structured_data": structured_data
                }
                results.append(result)
                successful_count += 1
                print(f"✅ 案件 {case_id} 处理成功")
        
            except Exception as e:
                # 处理失败
                result = {
                    "case_id": case_id,
                    "main_file": main_file.filename,
                    "email_file": email_file.filename if email_file else None,
                    "status": "error",
                    "message": f"处理失败: {str(e)}"
                }
                results.append(result)
                failed_count += 1
                print(f"❌ 案件 {case_id} 处理失败: {str(e)}")
    
    except Exception as outer_e:
        print(f"❌ 批量处理过程中发生严重错误: {str(outer_e)}")
        # 这里可以添加更多的错误处理逻辑
    
    finally:
        # 清理所有临时文件
        for file_path in temp_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
    
    processed_cases = successful_count + failed_count
    print(f"\n📊 智能批量处理完成:")
    print(f"   - 上传文件: {len(files)} 个")
    print(f"   - 处理案件: {processed_cases} 个")
    print(f"   - 成功: {successful_count} 个")
    print(f"   - 失败: {failed_count} 个")
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
    """获取案件列表"""
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

@app.get("/health")
def health_check():
    """
    健康检查端点
    
    用于检查API服务是否正常运行，可用于负载均衡器或监控系统
    支持TXT和PDF文件处理
    
    Returns:
        dict: 包含服务状态的响应
        
    Example:
        GET /health
        
        Response:
        {
            "status": "healthy",
            "message": "SRR案件处理API运行正常"
        }
    """
    return {"status": "healthy", "message": "SRR案件处理API运行正常，支持TXT和PDF文件"}


if __name__ == "__main__":
    """
    程序入口点
    
    当直接运行此文件时启动FastAPI服务器
    配置：
    - 主机: 0.0.0.0 (允许外部访问)
    - 端口: 8001
    - 自动重载: 启用 (开发模式)
    """
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8001, reload=True)
    