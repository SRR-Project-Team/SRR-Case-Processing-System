"""
TMO (Tree Management Office) PDFdataextractmodule

本module负责从TMO的PDFfile中extractSRR案件data，mainprocessASD开头的PDFfile。
基于extractFromTxt.py的process逻辑，针对TMO PDFfile的特殊结构进行适配。

TMO PDFfile结构特点：
- Date of Referral 对应 A_date_received
- From field对应 B_source
- TMO Ref. 对应案件编号
- 包含check员information和联系方式
- 有具体的check项目和评论

AI增强function：
- CNN图像预process
- 多引擎OCR融合
- 智能文本cleanup和error纠正
- 自适应格式识别

作者: Project3 Team
版本: 2.0 (AI增强版)
"""
import re
import pdfplumber
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import os
import PyPDF2
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ai_case_type_classifier import classify_case_type_ai
from ai.ai_subject_matter_classifier import classify_subject_matter_ai
from ai.ai_request_summarizer import generate_ai_request_summary
from utils.slope_location_mapper import get_location_from_slope_no
from utils.source_classifier import classify_source_smart


def extract_text_from_pdf_fast(pdf_path: str) -> str:
    """
    快速PDF文本extract，优先速度
    """
    content = ""
    
    # method1: 使用pdfplumber (通常最快)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    content += page_text + "\n"
        if content.strip():
            print(f"✅ pdfplumber快速extractsuccess: {len(content)}字符")
            return content
    except Exception as e:
        print(f"⚠️ pdfplumberextractfailed: {e}")
    
    # method2: 使用PyPDF2 (备选)
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    content += page_text + "\n"
        if content.strip():
            print(f"✅ PyPDF2快速extractsuccess: {len(content)}字符")
            return content
    except Exception as e:
        print(f"⚠️ PyPDF2extractfailed: {e}")
    
    print("⚠️ 快速PDFextractfailed，回退到AI增强process")
    # 回退到AI增强process
    try:
        from ai_enhanced_processor import get_ai_enhanced_content
        return get_ai_enhanced_content(pdf_path)
    except Exception as e:
        print(f"⚠️ AI增强process也failed: {e}")
        return ""


def parse_date(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串为datetimeobject（用于计算），failedreturnNone
    
    Args:
        date_str (str): 日期字符串，支持多种格式
        
    Returns:
        Optional[datetime]: 解析successreturndatetimeobject，failedreturnNone
    """
    if not date_str:
        return None
    
    # 尝试多种日期格式
    date_formats = [
        "%d %B %Y",      # "21 January 2025"
        "%Y-%m-%d",      # "2025-01-21"
        "%d/%m/%Y",      # "21/01/2025"
        "%d-%m-%Y",      # "21-01-2025"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def format_date(dt: Optional[datetime]) -> str:
    """
    将datetimeobject格式化为dd-MMM-yyyy格式，Nonereturn空
    
    Args:
        dt (Optional[datetime]): 要格式化的datetimeobject
        
    Returns:
        str: dd-MMM-yyyy格式的日期字符串，如 "15-Jan-2024"
    """
    return dt.strftime("%d-%b-%Y") if dt else ""


def calculate_due_date(base_date: Optional[datetime], days: int) -> str:
    """
    计算基准日期加days天后的日期，returnISO字符串
    
    Args:
        base_date (Optional[datetime]): 基准日期
        days (int): 要添加的天数
        
    Returns:
        str: 计算后的日期ISO字符串
    """
    if not base_date:
        return ""
    return format_date(base_date + timedelta(days=days))


def extract_tmo_reference(content: str) -> str:
    """
    extractTMO参考编号
    
    Args:
        content (str): PDFtext content
        
    Returns:
        str: TMO参考编号
    """
    # match "TMO Ref. ASD-WC-20250089-PP" 格式
    match = re.search(r'TMO Ref\.\s*([A-Z0-9\-]+)', content)
    return match.group(1).strip() if match else ""


def extract_referral_date(content: str) -> str:
    """
    extract转介日期 (Date of Referral)
    
    Args:
        content (str): PDFtext content
        
    Returns:
        str: 转介日期
    """
    # match "Date of Referral 21 January 2025" 格式
    # 使用更精确的正则table达式，只match日期部分
    match = re.search(r'Date of Referral\s+(\d{1,2}\s+\w+\s+\d{4})', content)
    if match:
        date_str = match.group(1).strip()
        parsed_date = parse_date(date_str)
        return format_date(parsed_date)
    return ""


def extract_source_from(content: str) -> str:
    """
    extract来源information (Fromfield)
    
    Args:
        content (str): PDFtext content
        
    Returns:
        str: 来源information
    """
    # match "From Tree Management Office (TMO)" 格式
    match = re.search(r'From\s+([^\n]+)', content)
    if match:
        source = match.group(1).strip()
        # 简化来源information
        if "Tree Management Office" in source or "TMO" in source:
            return "TMO"
        return source
    return ""


def extract_inspection_officers(content: str) -> Tuple[str, str]:
    """
    extractcheck员information
    
    Args:
        content (str): PDFtext content
        
    Returns:
        Tuple[str, str]: (check员姓名, 联系方式)
    """
    # matchcheck员information - 修复正则table达式以match实际格式
    # 实际格式: "Inspection Ms. Jennifer CHEUNG, FdO(TM)9"
    officer_match = re.search(r'Inspection\s+([^\n]+?)(?=\s+Officer|\s+Attn\.|$)', content, re.DOTALL)
    contact_match = re.search(r'Contact\s+([^\n]+)', content)
    
    officers = ""
    contact = ""
    
    if officer_match:
        officers = officer_match.group(1).strip()
        # cleanup格式，extract姓名
        officers = re.sub(r'\s+', ' ', officers)
        # 只保留姓名部分，去掉职位information
        officers = re.sub(r'\s*FdO\(TM\)\d+.*', '', officers).strip()
        # 进一步cleanup，只保留姓名
        officers = re.sub(r'\s*Ms\.\s*', 'Ms. ', officers)
        officers = re.sub(r'\s*Mr\.\s*', 'Mr. ', officers)
    
    if contact_match:
        contact = contact_match.group(1).strip()
    
    return officers, contact


def extract_district(content: str) -> str:
    """
    extract地区information
    
    Args:
        content (str): PDFtext content
        
    Returns:
        str: 地区information
    """
    # match "District Wan Chai" 格式
    match = re.search(r'District\s+([^\n]+)', content)
    return match.group(1).strip() if match else ""


def extract_form_reference(content: str) -> str:
    """
    extractForm 2参考编号
    
    Args:
        content (str): PDFtext content
        
    Returns:
        str: Form 2参考编号
    """
    # match "Form 2 ref. no. form2-11SWB/F199-20241028-002" 格式
    match = re.search(r'Form 2 ref\.\s+no\.\s+([^\n]+)', content)
    return match.group(1).strip() if match else ""


def extract_slope_no_from_form_ref(content: str) -> str:
    """
    从TMO内容中extract斜坡编号，支持多种模式
    
    支持的extract模式：
    1. slope.no 后面的内容
    2. Form 2 ref. no 后面的内容中extract
    3. 斜坡编号 后面的内容
    
    Args:
        content (str): PDFtext content
        
    Returns:
        str: extract并清理后的斜坡编号
    """
    print("🔍 TMO开始extract斜坡编号...")
    
    # 模式1: slope.no 后面的内容
    slope_patterns = [
        r'slope\.?\s*no\.?\s*[:\s]+([A-Z0-9\-/#\s]+)',  # slope.no: 11SW-B/F199
        r'slope\s+no\.?\s*[:\s]+([A-Z0-9\-/#\s]+)',     # slope no: 11SW-B/F199
        r'slope\s*[:\s]+([A-Z0-9\-/#\s]+)',             # slope: 11SW-B/F199
    ]
    
    for pattern in slope_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            slope_no = clean_slope_number_tmo(match.group(1))
            if slope_no:
                print(f"✅ 从slope.noextract斜坡编号: {slope_no}")
                return slope_no
    
    # 模式2: Form 2 ref. no 后面的内容中extract
    form_ref = extract_form_reference(content)
    if form_ref:
        # 从form2-11SWB/F199-20241028-002中extract11SWB/F199部分
        slope_match = re.search(r'form2-([A-Z0-9/#\s]+)', form_ref, re.IGNORECASE)
        if slope_match:
            slope_part = slope_match.group(1).upper()
            slope_no = format_slope_number_tmo(slope_part)
            if slope_no:
                print(f"✅ 从Form 2 ref. noextract斜坡编号: {slope_no}")
                return slope_no
    
    # 模式3: 斜坡编号 后面的内容
    chinese_patterns = [
        r'斜坡编号[:\s]+([A-Z0-9\-/#\s]+)',
        r'斜坡編號[:\s]+([A-Z0-9\-/#\s]+)',
        r'斜坡[:\s]+([A-Z0-9\-/#\s]+)',
    ]
    
    for pattern in chinese_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            slope_no = clean_slope_number_tmo(match.group(1))
            if slope_no:
                print(f"✅ 从斜坡编号extract: {slope_no}")
                return slope_no
    
    print("⚠️ TMO未找到斜坡编号")
    return ""


def clean_slope_number_tmo(slope_text: str) -> str:
    """
    清理TMO斜坡编号，去除干扰information
    
    Args:
        slope_text (str): 原始斜坡编号文本
        
    Returns:
        str: 清理后的斜坡编号
    """
    if not slope_text:
        return ""
    
    # 去除#号、空格和其他干扰字符
    cleaned = re.sub(r'[#\s]+', '', slope_text.strip())
    
    # 只保留字母、数字、连字符和斜杠
    cleaned = re.sub(r'[^A-Z0-9\-/]', '', cleaned.upper())
    
    # 修正OCRerror
    if cleaned.startswith('LSW') or cleaned.startswith('ISW') or cleaned.startswith('JSW'):
        cleaned = '11SW' + cleaned[3:]
    elif cleaned.startswith('lSW') or cleaned.startswith('iSW') or cleaned.startswith('jSW'):
        cleaned = '11SW' + cleaned[3:]
    elif cleaned.startswith('1SW') and len(cleaned) > 3:
        # process 1SW-D/CR995 -> 11SW-D/CR995
        cleaned = '11SW' + cleaned[3:]
    
    # format斜坡编号
    return format_slope_number_tmo(cleaned)


def format_slope_number_tmo(slope_no: str) -> str:
    """
    格式化TMO斜坡编号，转换为标准格式
    
    Args:
        slope_no (str): 原始斜坡编号
        
    Returns:
        str: 格式化后的斜坡编号
    """
    if not slope_no:
        return ""
    
    # 转换格式：11SWB/F199 -> 11SW-B/F199
    if 'SWB' in slope_no and 'SW-B' not in slope_no:
        slope_no = slope_no.replace('SWB', 'SW-B')
    elif 'SWD' in slope_no and 'SW-D' not in slope_no:
        slope_no = slope_no.replace('SWD', 'SW-D')
    elif 'SWC' in slope_no and 'SW-C' not in slope_no:
        slope_no = slope_no.replace('SWC', 'SW-C')
    elif 'SWA' in slope_no and 'SW-A' not in slope_no:
        slope_no = slope_no.replace('SWA', 'SW-A')
    
    return slope_no


def extract_comments(content: str) -> str:
    """
    extractTMO评论information
    
    Args:
        content (str): PDFtext content
        
    Returns:
        str: 评论information
    """
    # findCOMMENTS FROM TMO部分
    comments_section = re.search(r'COMMENTS FROM TMO(.*?)(?=Tree Management Office|$)', content, re.DOTALL)
    if comments_section:
        comments = comments_section.group(1).strip()
        # cleanup格式
        comments = re.sub(r'\s+', ' ', comments)
        return comments[:200] + "..." if len(comments) > 200 else comments
    return ""


def extract_follow_up_actions(content: str) -> str:
    """
    extract后续行动information
    
    Args:
        content (str): PDFtext content
        
    Returns:
        str: 后续行动information
    """
    # findFOLLOW-UP ACTIONS部分
    actions_section = re.search(r'FOLLOW-UP ACTIONS(.*?)(?=Tree Management Office|$)', content, re.DOTALL)
    if actions_section:
        actions = actions_section.group(1).strip()
        # cleanup格式
        actions = re.sub(r'\s+', ' ', actions)
        return actions[:200] + "..." if len(actions) > 200 else actions
    return ""


# 注意：get_location_from_slope_no function现在从 slope_location_mapper moduleimport


def get_ai_enhanced_content(pdf_path: str) -> str:
    """
    获取AI增强的PDFtext content
    
    Args:
        pdf_path (str): PDFfile path
        
    Returns:
        str: AI增强的text content
    """
    try:
        from ai_enhanced_processor import get_ai_enhanced_text
        
        # 使用AI增强process器
        enhanced_content = get_ai_enhanced_text(pdf_path, "tmo")
        
        if enhanced_content:
            print(f"✅ TMO AI增强processsuccess，文本长度: {len(enhanced_content)} 字符")
            return enhanced_content
        else:
            print("⚠️ TMO AI增强process未return内容，使用原始method")
            # 回退到原始method
            return extract_text_from_pdf_traditional(pdf_path)
                
    except ImportError:
        print("⚠️ TMO AI增强process器不可用，使用原始method")
        # 回退到原始method
        return extract_text_from_pdf_traditional(pdf_path)
    except Exception as e:
        print(f"⚠️ TMO AI增强processfailed: {e}，使用原始method")
        # 回退到原始method
        return extract_text_from_pdf_traditional(pdf_path)


def extract_text_from_pdf_traditional(pdf_path: str) -> str:
    """
    传统PDF文本extractmethod作为备选
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        print(f"传统PDFextractfailed: {e}")
        return ""


def extract_case_data_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    从TMO PDF文件中extract所有案件data，return字典格式
    
    这是主要的TMOdataextract函数，按照A-Qfield规则extract：
    - A: 案件接收日期 (Date of Referral)
    - B: 来源 (Fromfield)
    - C: 1823案件号 (TMO Ref.)
    - D: 案件class型 (根据内容判断)
    - E: 来电人姓名 (check员)
    - F: 联系电话 (Contact)
    - G: 斜坡编号 (从内容中extract)
    - H: 位置 (从Exceldata获取)
    - I: 请求性质摘要 (评论information)
    - J: 事项主题 (Form 2相关)
    - K: 10天规则截止日期 (A+10天)
    - L: ICC临时回复截止日期 (不适用)
    - M: ICC最终回复截止日期 (不适用)
    - N: 工程完成截止日期 (取决于D)
    - O1: 发给承包商的传真日期 (通常同A)
    - O2: 邮件发送时间 (不适用)
    - P: 传真页数 (PDF页数)
    - Q: 案件详情 (后续行动)
    
    Args:
        pdf_path (str): PDFfile path
        
    Returns:
        Dict[str, Any]: 包含所有A-Qfield的字典
    """
    result = {}
    
    # 优先使用快速文本extract，避免AI增强process
    content = extract_text_from_pdf_fast(pdf_path)
    
    if not content:
        print("⚠️ 无法extractPDFtext content")
        return {key: "" for key in ['A_date_received', 'B_source', 'C_case_number', 'D_type', 
                                   'E_caller_name', 'F_contact_no', 'G_slope_no', 'H_location',
                                   'I_nature_of_request', 'J_subject_matter', 'K_10day_rule_due_date',
                                   'L_icc_interim_due', 'M_icc_final_due', 'N_works_completion_due',
                                   'O1_fax_to_contractor', 'O2_email_send_time', 'P_fax_pages', 'Q_case_details']}
    
    # A: 案件接收日期 (Date of Referral)
    result['A_date_received'] = extract_referral_date(content)
    # 需要从原始内容中extract日期string进行parse
    import re
    date_match = re.search(r'Date of Referral\s+(\d{1,2}\s+\w+\s+\d{4})', content)
    A_date = parse_date(date_match.group(1).strip()) if date_match else None
    
    # B: 来源（智能classify）
    result['B_source'] = classify_source_smart(
        file_path=pdf_path, 
        content=content, 
        email_content=None, 
        file_type='pdf'
    )
    
    # C: 案件编号 (TMO部分没有案件编号)
    result['C_case_number'] = ""
    
    # D: 案件class型 (使用AIclassify)
    try:
        print("🤖 TMO使用AIclassify案件class型...")
        case_data_for_ai = {
            'I_nature_of_request': result.get('I_nature_of_request', ''),
            'J_subject_matter': result.get('J_subject_matter', ''),
            'Q_case_details': result.get('Q_case_details', ''),
            'B_source': result.get('B_source', ''),
            'G_slope_no': result.get('G_slope_no', ''),
            'F_contact_no': result.get('F_contact_no', ''),
            'content': content
        }
        ai_result = classify_case_type_ai(case_data_for_ai)
        result['D_type'] = ai_result.get('predicted_type', 'General')
        print(f"✅ TMO AIclassify完成: {result['D_type']} (confidence: {ai_result.get('confidence', 0):.2f})")
    except Exception as e:
        print(f"⚠️ TMO AIclassifyfailed，使用传统method: {e}")
        # 传统classifymethod作为备用
        if "urgent" in content.lower() or "紧急" in content:
            result['D_type'] = "Urgent"
        elif "emergency" in content.lower() or "紧急" in content:
            result['D_type'] = "Emergency"
        else:
            result['D_type'] = "General"
    
    # E: 来电人姓名；F: 联系电话 (check员information)
    result['E_caller_name'], result['F_contact_no'] = extract_inspection_officers(content)
    
    # G: 斜坡编号 (从Form 2 ref. no.中extract并转换格式)
    # 从Form 2 ref. no.中extract斜坡编号
    # 例如：11SWB/F199 -> 11SW-B/F199
    result['G_slope_no'] = extract_slope_no_from_form_ref(content)
    
    # H: 位置 (从Exceldataget)
    result['H_location'] = get_location_from_slope_no(result['G_slope_no'])
    
    # I: request性质摘要 (使用AI从PDF内容生成具体request摘要)
    try:
        print("🤖 TMO使用AI生成请求摘要...")
        ai_summary = generate_ai_request_summary(content, None, 'pdf')
        result['I_nature_of_request'] = ai_summary
        print(f"✅ TMO AI请求摘要生成success: {ai_summary}")
    except Exception as e:
        print(f"⚠️ TMO AI摘要生成failed，使用备用method: {e}")
        # 备用method：使用原有的评论extract
        result['I_nature_of_request'] = extract_comments(content)
    
    # J: 事项主题 (使用AIclassify器)
    try:
        print("🤖 TMO使用AIclassify主题...")
        subject_data_for_ai = {
            'I_nature_of_request': result.get('I_nature_of_request', ''),
            'J_subject_matter': "Tree Risk Assessment Form 2",
            'Q_case_details': result.get('Q_case_details', ''),
            'content': content
        }
        ai_subject_result = classify_subject_matter_ai(subject_data_for_ai)
        result['J_subject_matter'] = ai_subject_result.get('predicted_category', 'Tree Trimming/ Pruning')
        print(f"✅ TMO主题classify完成: {result['J_subject_matter']} (confidence: {ai_subject_result.get('confidence', 0):.2f})")
    except Exception as e:
        print(f"⚠️ TMO主题classifyfailed，使用默认: {e}")
        result['J_subject_matter'] = "Tree Trimming/ Pruning"
    
    # K: 10天规则截止日期 (A+10天)
    result['K_10day_rule_due_date'] = calculate_due_date(A_date, 10)
    
    # L: ICC临时回复截止日期 (A+10个日历日)
    result['L_icc_interim_due'] = calculate_due_date(A_date, 10)
    
    # M: ICC最终回复截止日期 (A+21个日历日)
    result['M_icc_final_due'] = calculate_due_date(A_date, 21)
    
    # N: 工程完成截止日期 (取决于D)
    days_map = {"Emergency": 1, "Urgent": 3, "General": 12}
    result['N_works_completion_due'] = calculate_due_date(A_date, days_map.get(result['D_type'], 0))
    
    # O1: 发给承包商的传真日期 (仅日期部分，通常同A)
    result['O1_fax_to_contractor'] = A_date.strftime("%Y-%m-%d") if A_date else ""
    
    # O2: 邮件发送时间 (TMO不适用)
    result['O2_email_send_time'] = ""
    
    # P: 传真页数 (PDF页数)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            result['P_fax_pages'] = str(len(pdf.pages))
    except:
        result['P_fax_pages'] = ""
    
    # Q: 案件详情 (后续行动)
    result['Q_case_details'] = extract_follow_up_actions(content)
    
    return result
