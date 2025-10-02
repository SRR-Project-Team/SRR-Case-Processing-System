"""
数据提取模块 - 从TXT文件中提取和解析SRR案件数据

本模块负责从SRR案件的TXT文件中提取结构化数据，包括：
- 案件基本信息（日期、来源、类型等）
- 联系人信息（姓名、电话）
- 斜坡相关信息（编号、位置）
- 时间节点（截止日期、回复时间等）
- 案件详情和附件信息

主要功能：
1. 解析各种日期格式
2. 提取案件来源和类型
3. 获取联系人和斜坡信息
4. 计算各种截止日期
5. 生成案件摘要和详情
6. AI增强文本处理和OCR能力

作者: AI Assistant
版本: 2.0 (AI增强版)
"""
import re
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ai_case_type_classifier import classify_case_type_ai
from utils.email_info_extractor import get_email_contact_info
from ai.ai_subject_matter_classifier import classify_subject_matter_ai
from ai.ai_request_summarizer import generate_ai_request_summary
from utils.file_utils import detect_file_encoding, read_file_with_encoding
from utils.slope_location_mapper import get_location_from_slope_no
from utils.source_classifier import classify_source_smart


def parse_date(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串为datetime对象（用于计算），失败返回None
    
    Args:
        date_str (str): 日期字符串，格式为 "YYYY-MM-DD HH:MM:SS"
        
    Returns:
        Optional[datetime]: 解析成功返回datetime对象，失败返回None
        
    Example:
        >>> parse_date("2024-01-15 10:30:00")
        datetime(2024, 1, 15, 10, 30, 0)
        >>> parse_date("")
        None
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def format_date(dt: Optional[datetime]) -> str:
    """
    将datetime对象格式化为dd-MMM-yyyy格式，None返回空
    
    Args:
        dt (Optional[datetime]): 要格式化的datetime对象
        
    Returns:
        str: dd-MMM-yyyy格式的日期字符串，如 "15-Jan-2024"
        
    Example:
        >>> format_date(datetime(2024, 1, 15, 10, 30, 0))
        "15-Jan-2024"
        >>> format_date(None)
        ""
    """
    return dt.strftime("%d-%b-%Y") if dt else ""


def calculate_due_date(base_date: Optional[datetime], days: int) -> str:
    """
    计算基准日期加days天后的日期，返回ISO字符串
    
    Args:
        base_date (Optional[datetime]): 基准日期
        days (int): 要添加的天数
        
    Returns:
        str: 计算后的日期ISO字符串
        
    Example:
        >>> base = datetime(2024, 1, 15, 10, 30, 0)
        >>> calculate_due_date(base, 10)
        "2024-01-25T10:30:00"
    """
    if not base_date:
        return ""
    return format_date(base_date + timedelta(days=days))


def extract_1823_case_no(content: str) -> str:
    """
    提取1823案件编号
    
    从TXT内容中搜索"1823 case:"后面的内容作为案件编号
    
    Args:
        content (str): TXT文件内容
        
    Returns:
        str: 提取的案件编号，未找到返回空字符串
        
    Example:
        >>> content = "1823 CASE: 3-8641924612"
        >>> extract_1823_case_no(content)
        "3-8641924612"
    """
    # 搜索"1823 case:"后面的内容（不区分大小写）
    match = re.search(r'1823\s+case:\s*([\w\-:]+)', content, re.IGNORECASE)
    if match:
        case_number = match.group(1).strip()
        print(f"✅ 提取到1823案件编号: {case_number}")
        return case_number
    
    print("⚠️ 未找到1823案件编号")
    return ""


def get_source_from_content(content: str) -> str:
    """
    提取来源B（根据内容中的渠道/提交方式判断）
    
    从Channel字段判断案件来源，支持以下映射：
    - Web -> 1823
    - RCC/ICC -> 保持原值
    
    Args:
        content (str): TXT文件内容
        
    Returns:
        str: 案件来源标识
        
    Example:
        >>> content = "Channel : Web"
        >>> get_source_from_content(content)
        "1823"
    """
    # 示例逻辑：从Channel字段或Contact History提取
    channel_match = re.search(r'Channel :\s*(.*?)\n', content)
    if channel_match:
        channel = channel_match.group(1).strip()
        # 映射规则：Web->1823，其他可能值RCC/ICC需根据实际文本调整
        if channel == "Web":
            return "1823"
        elif re.search(r'RCC|ICC', channel, re.IGNORECASE):
            return channel.upper()
    return ""


def get_caller_info_by_source(content: str, source: str) -> Tuple[str, str]:
    """
    根据来源B提取联系人姓名(E)和电话(F)
    
    从CONTACT INFORMATION部分提取联系人的姓名和电话号码，
    支持RCC、ICC、1823等来源格式
    
    Args:
        content (str): TXT文件内容
        source (str): 案件来源（RCC/ICC/1823等）
        
    Returns:
        Tuple[str, str]: (姓名, 电话号码)
        
    Example:
        >>> content = "Last Name : 张\nFirst Name : 三\nDaytime No. : 12345678"
        >>> get_caller_info_by_source(content, "1823")
        ("张 三", "12345678")
    """
    # 不同来源的提取规则
    if source in ["RCC", "ICC", "1823"]:
        # 从VI. CONTACT INFORMATION提取
        last_name = re.search(r'Last Name :\s*(.*?)\n', content)
        first_name = re.search(r'First Name :\s*(.*?)\n', content)
        phone = re.search(r'Daytime No. :\s*(.*?)\n', content) or re.search(r'Mobile :\s*(.*?)\n', content)
        
        full_name = f"{last_name.group(1).strip() if last_name else ''} {first_name.group(1).strip() if first_name else ''}".strip()
        contact_no = phone.group(1).strip() if phone else ""
        return (full_name, contact_no)
    # 其他来源的规则可扩展
    return ("", "")


def classify_case_type_ai_enhanced(case_data: dict) -> str:
    """使用AI增强的案件类型分类 - 基于历史数据和SRR规则"""
    try:
        print("🤖 使用AI分类案件类型...")
        
        # 调用AI分类器
        ai_result = classify_case_type_ai(case_data)
        
        predicted_type = ai_result.get('predicted_type', 'General')
        confidence = ai_result.get('confidence', 0.5)
        method = ai_result.get('method', 'unknown')
        
        print(f"✅ AI分类完成: {predicted_type} (置信度: {confidence:.2f}, 方法: {method})")
        
        return predicted_type
        
    except Exception as e:
        print(f"⚠️ AI分类失败，使用传统方法: {e}")
        return classify_case_type_traditional(case_data.get('content', ''))

def classify_case_type_traditional(content: str) -> str:
    """传统的案件类型分类方法（备用）"""
    desc = re.search(r'Description :\s*(.*?)\n', content, re.DOTALL)
    if not desc:
        return "General"
    desc_text = desc.group(1).lower()
    
    # 关键词匹配示例
    if "emergency" in desc_text or "紧急" in desc_text:
        return "Emergency"
    elif "urgent" in desc_text or "紧急" in desc_text:
        return "Urgent"
    else:
        return "General"


def generate_nature_summary(content: str) -> str:
    """
    生成请求性质摘要I - 使用NLP增强技术
    
    Args:
        content (str): TXT文件内容（已AI增强处理）
        
    Returns:
        str: 请求性质摘要
    """
    # 直接使用NLP增强技术进行智能总结
    try:
        from nlp_enhanced_processor import get_nlp_enhanced_nature_of_request
        
        # 检查是否有对应的邮件文件
        email_content = None
        # 尝试推断邮件文件路径
        # 这里可以根据当前处理的文件名来推断
        # 例如: 3-3YXXSJV.txt -> emailcontent_3-3YXXSJV.txt
        
        # 使用NLP技术总结诉求内容
        nlp_summary = get_nlp_enhanced_nature_of_request(content, email_content)
        if nlp_summary:
            print(f"✅ NLP增强摘要成功: {nlp_summary}")
            return nlp_summary
            
    except ImportError:
        print("⚠️ NLP增强处理器不可用，使用传统方法")
    except Exception as e:
        print(f"⚠️ NLP处理失败: {e}，使用传统方法")
    
    # 传统方法作为备选
    if len(content) > 100:
        return content[:100] + "..."
    else:
        return content


def generate_nature_summary_from_original(original_content: str) -> str:
    """
    从原始文件内容生成简洁的NLP总结
    
    Args:
        original_content (str): 原始TXT文件内容
        
    Returns:
        str: 简洁的请求性质摘要
    """
    try:
        from nlp_enhanced_processor import get_nlp_enhanced_nature_of_request
        
        # 检查是否有对应的邮件文件
        email_content = None
        
        # 使用原始内容进行NLP总结，生成简洁结果
        nlp_summary = get_nlp_enhanced_nature_of_request(original_content, email_content)
        if nlp_summary:
            print(f"✅ 原始内容NLP摘要成功: {nlp_summary}")
            return nlp_summary
            
    except ImportError:
        print("⚠️ NLP增强处理器不可用，使用传统方法")
    except Exception as e:
        print(f"⚠️ NLP处理失败: {e}，使用传统方法")
    
    # 传统方法作为备选
    if len(original_content) > 100:
        return original_content[:100] + "..."
    else:
        return original_content


def get_slope_no(content: str) -> str:
    """提取斜坡编号G（从补充信息或描述中）"""
    # 匹配"斜坡编号为XXX"或"[请提供斜坡牌...](XXX)"
    slope_match = re.search(r'斜坡編號為([\w\-/]+)', content) or re.search(r'\((11sw-c/nd31)\)', content, re.IGNORECASE)
    return slope_match.group(1).strip().upper() if slope_match else ""


# 注意：get_location_from_slope_no 函数现在从 slope_location_mapper 模块导入


def get_last_interim_reply_time(content: str) -> str:
    """提取最后一个实质处理的Interim Reply时间"""
    # 查找所有DUE DATE部分
    due_date_sections = re.findall(r'DUE DATE:.*?(?=\d+st DUE DATE:|$)', content, re.DOTALL)
    
    if not due_date_sections:
        return ""
    
    # 遍历所有DUE DATE部分，找到最后一个有Interim Reply时间的
    last_interim_reply = ""
    for section in due_date_sections:
        interim_match = re.search(r'Interim Reply\s*:\s*([^\n]+)', section)
        if interim_match and interim_match.group(1).strip():
            last_interim_reply = interim_match.group(1).strip()
    
    return last_interim_reply


def get_last_final_reply_time(content: str) -> str:
    """提取最后一个实质处理的Final Reply时间"""
    # 查找所有DUE DATE部分
    due_date_sections = re.findall(r'DUE DATE:.*?(?=\d+st DUE DATE:|$)', content, re.DOTALL)
    
    if not due_date_sections:
        return ""
    
    # 遍历所有DUE DATE部分，找到最后一个有Final Reply时间的
    last_final_reply = ""
    for section in due_date_sections:
        final_match = re.search(r'Final Reply\s*:\s*([^\n]+)', section)
        if final_match and final_match.group(1).strip():
            last_final_reply = final_match.group(1).strip()
    
    return last_final_reply


def format_date_only(dt: Optional[datetime]) -> str:
    """将datetime对象格式化为仅日期字符串（YYYY-MM-DD），None返回空"""
    return dt.strftime("%Y-%m-%d") if dt else ""


def format_time_only(dt: Optional[datetime]) -> str:
    """将datetime对象格式化为仅时间字符串（HH:MM:SS），None返回空"""
    return dt.strftime("%H:%M:%S") if dt else ""


# 删除AI增强处理函数，直接使用原始文件内容


def extract_case_data_from_txt(txt_path: str) -> dict:
    """
    从TXT文件中提取所有案件数据，返回字典格式
    
    这是主要的数据提取函数，整合了所有提取逻辑，按照A-Q字段规则提取：
    - A: 案件接收日期
    - B: 来源
    - C: 1823案件号（仅RCC/ICC）
    - D: 案件类型
    - E: 来电人姓名
    - F: 联系电话
    - G: 斜坡编号
    - H: 位置（从Excel数据获取）
    - I: 请求性质摘要（使用NLP增强技术）
    - J: 事项主题
    - K: 10天规则截止日期
    - L: ICC临时回复截止日期
    - M: ICC最终回复截止日期
    - N: 工程完成截止日期
    - O1: 发给承包商的传真日期
    - O2: 邮件发送时间
    - P: 传真页数
    - Q: 案件详情
    
    Args:
        txt_path (str): TXT文件路径
        
    Returns:
        dict: 包含所有A-Q字段的字典
    """
    # 使用智能编码检测读取原始文件内容
    try:
        content = read_file_with_encoding(txt_path)
    except Exception as e:
        print(f"⚠️ 无法读取TXT文件: {e}")
        return {key: "" for key in ['A_date_received', 'B_source', 'C_case_number', 'D_type', 
                                   'E_caller_name', 'F_contact_no', 'G_slope_no', 'H_location',
                                   'I_nature_of_request', 'J_subject_matter', 'K_10day_rule_due_date',
                                   'L_icc_interim_due', 'M_icc_final_due', 'N_works_completion_due',
                                   'O1_fax_to_contractor', 'O2_email_send_time', 'P_fax_pages', 'Q_case_details']}
    
    # 检查是否有对应的邮件文件
    email_content = None
    try:
        # 根据TXT文件名推断邮件文件路径
        # 例如: exampleInput/txt/3-3YXXSJV.txt -> exampleInput/txt/emailcontent_3-3YXXSJV.txt
        dir_path = os.path.dirname(txt_path)
        base_name = os.path.splitext(os.path.basename(txt_path))[0]
        email_path = os.path.join(dir_path, f"emailcontent_{base_name}.txt")
        
        if os.path.exists(email_path):
            print(f"📧 发现邮件文件: {email_path}")
            try:
                email_content = read_file_with_encoding(email_path)
            except Exception as e:
                print(f"⚠️ 邮件文件读取失败: {e}")
                email_content = None
        else:
            print(f"⚠️ 未找到邮件文件: {email_path}")
            
    except Exception as e:
        print(f"⚠️ 邮件文件处理失败: {e}")
    
    # 调用原有的提取逻辑，并传递邮件内容用于NLP处理
    return extract_case_data_with_email(content, email_content, content, txt_path)


def extract_case_data_with_email(content: str, email_content: str = None, original_content: str = None, txt_path: str = None) -> dict:
    """
    从TXT内容中提取所有案件数据，支持邮件内容用于NLP处理和联系信息提取
    
    Args:
        content (str): TXT文件内容
        email_content (str): 邮件内容（可选）
        original_content (str): 原始内容（用于NLP处理）
        
    Returns:
        dict: 包含所有A-Q字段的字典
    """
    # 调用原有的提取逻辑，传递文件路径
    result = extract_case_data(content, original_content, email_content, txt_path)
    
    # 如果有邮件内容，进行增强处理
    if email_content:
        # 1. 使用AI生成具体的请求摘要（优先使用邮件内容）
        try:
            print("🤖 使用AI从邮件内容生成请求摘要...")
            ai_summary = generate_ai_request_summary(content, email_content, 'txt')
            if ai_summary and ai_summary != "无法提取具体请求内容":
                result['I_nature_of_request'] = ai_summary
                print(f"✅ AI邮件请求摘要生成成功: {ai_summary}")
            
        except Exception as e:
            print(f"⚠️ AI邮件摘要生成失败: {e}，使用原有摘要")
        
        # 2. 从邮件内容提取联系信息（E_caller_name和F_contact_no）
        try:
            email_contact_info = get_email_contact_info(email_content, content)
            
            # 如果邮件中有联系信息，优先使用邮件信息
            if email_contact_info.get('E_caller_name'):
                result['E_caller_name'] = email_contact_info['E_caller_name']
                print(f"✅ 从邮件提取联系人姓名: {email_contact_info['E_caller_name']}")
            
            if email_contact_info.get('F_contact_no'):
                result['F_contact_no'] = email_contact_info['F_contact_no']
                print(f"✅ 从邮件提取联系电话: {email_contact_info['F_contact_no']}")
                
        except Exception as e:
            print(f"⚠️ 邮件联系信息提取失败: {e}，使用原有信息")
    
    return result


# 删除AI增强处理相关函数，直接使用原始文件内容


def extract_case_data(content: str, original_content: str = None, email_content: str = None, file_path: str = None) -> dict:
    """
    从TXT内容中提取所有案件数据，返回字典格式
    
    这是主要的数据提取函数，整合了所有提取逻辑，按照A-Q字段规则提取：
    - A: 案件接收日期
    - B: 来源
    - C: 1823案件号（仅RCC/ICC）
    - D: 案件类型
    - E: 来电人姓名
    - F: 联系电话
    - G: 斜坡编号
    - H: 位置（从Excel数据获取）
    - I: 请求性质摘要
    - J: 事项主题
    - K: 10天规则截止日期
    - L: ICC临时回复截止日期
    - M: ICC最终回复截止日期
    - N: 工程完成截止日期
    - O1: 发给承包商的传真日期
    - O2: 邮件发送时间
    - P: 传真页数
    - Q: 案件详情
    
    Args:
        content (str): TXT文件内容
        
    Returns:
        dict: 包含所有A-Q字段的字典
        
    Example:
        >>> content = "Case Creation Date : 2024-01-15 10:30:00\\nChannel : Web..."
        >>> data = extract_case_data(content)
        >>> data['A_date_received']
        "2024-01-15T10:30:00"
    """
    result = {}
    
    # A: 案件接收日期（AIMS生成，对应Case Creation Date）
    creation_date_match = re.search(r'Case Creation Date :\s*(.*?)\n', content)
    A_date = parse_date(creation_date_match.group(1)) if creation_date_match else None
    result['A_date_received'] = format_date(A_date)
    
    # B: 来源（智能分类）
    result['B_source'] = classify_source_smart(
        file_path=file_path, 
        content=content, 
        email_content=email_content, 
        file_type='txt'
    )
    
    # C: 案件编号 (搜索所有文本中"1823 case:"后面的内容)
    result['C_case_number'] = extract_1823_case_no(content)
    
    # D: 案件类型（使用AI分类）
    # 准备AI分类所需的数据
    case_data_for_ai = {
        'I_nature_of_request': result.get('I_nature_of_request', ''),
        'J_subject_matter': result.get('J_subject_matter', ''),
        'Q_case_details': result.get('Q_case_details', ''),
        'B_source': result.get('B_source', ''),
        'G_slope_no': result.get('G_slope_no', ''),
        'F_contact_no': result.get('F_contact_no', ''),
        'content': content
    }
    result['D_type'] = classify_case_type_ai_enhanced(case_data_for_ai)
    
    # E: 来电人姓名；F: 联系电话（取决于B）
    result['E_caller_name'], result['F_contact_no'] = get_caller_info_by_source(content, result['B_source'])
    
    # G: 斜坡编号
    result['G_slope_no'] = get_slope_no(content)
    
    # H: 位置（从slope data.xlsx获取）
    result['H_location'] = get_location_from_slope_no(result['G_slope_no'])
    
    # I: 请求性质摘要 - 使用AI从邮件或内容中生成具体请求摘要
    try:
        print("🤖 TXT使用AI生成请求摘要...")
        source_content = original_content if original_content else content
        ai_summary = generate_ai_request_summary(source_content, email_content, 'txt')
        result['I_nature_of_request'] = ai_summary
        print(f"✅ TXT AI请求摘要生成成功: {ai_summary}")
    except Exception as e:
        print(f"⚠️ TXT AI摘要生成失败，使用备用方法: {e}")
        # 备用方法：使用原有的NLP处理
        if original_content:
            result['I_nature_of_request'] = generate_nature_summary_from_original(original_content)
        else:
            result['I_nature_of_request'] = generate_nature_summary(content)
    
    # J: 事项主题（根据历史记录和规则，示例逻辑）
    subject_match = re.search(r'Subject Matter :\s*(.*?)\n', content)
    extracted_subject = subject_match.group(1).strip() if subject_match else ""
    
    # 使用AI分类器增强J_subject_matter
    try:
        print("🤖 TXT使用AI分类主题...")
        subject_data_for_ai = {
            'I_nature_of_request': result.get('I_nature_of_request', ''),
            'J_subject_matter': extracted_subject,
            'Q_case_details': result.get('Q_case_details', ''),
            'content': original_content if 'original_content' in locals() else content
        }
        ai_subject_result = classify_subject_matter_ai(subject_data_for_ai)
        result['J_subject_matter'] = ai_subject_result.get('predicted_category', extracted_subject or 'Others')
        print(f"✅ TXT主题分类完成: {result['J_subject_matter']} (置信度: {ai_subject_result.get('confidence', 0):.2f})")
    except Exception as e:
        print(f"⚠️ TXT主题分类失败，使用原始提取: {e}")
        result['J_subject_matter'] = extracted_subject or "Others"
    
    # K: 10天规则截止日期（A+10天）
    result['K_10day_rule_due_date'] = calculate_due_date(A_date, 10)
    
    # L: ICC临时回复截止日期（A+10个日历日）
    result['L_icc_interim_due'] = calculate_due_date(A_date, 10)
    
    # M: ICC最终回复截止日期（A+21个日历日）
    result['M_icc_final_due'] = calculate_due_date(A_date, 21)
    
    # N: 工程完成截止日期（取决于D）
    days_map = {"Emergency": 1, "Urgent": 3, "General": 12}
    result['N_works_completion_due'] = calculate_due_date(A_date, days_map.get(result['D_type'], 0))
    
    # O1: 发给承包商的传真日期（仅日期部分，通常同A）
    result['O1_fax_to_contractor'] = format_date_only(A_date)
    
    # O2: 邮件发送时间（从书面联系详情提取时间部分，如果没有Transaction Time则使用Case Creation Date的时间）
    email_time_match = re.search(r'Transaction Time:\s*(.*?)\n', content)
    if email_time_match:
        email_dt = parse_date(email_time_match.group(1))
        result['O2_email_send_time'] = format_time_only(email_dt)
    else:
        # 如果没有Transaction Time，使用Case Creation Date的时间部分
        result['O2_email_send_time'] = format_time_only(A_date)
    
    # P: 传真页数（从附件信息提取）
    file_upload_match = re.search(r'File upload:\s*(\d+)\s*file', content)
    result['P_fax_pages'] = f"1 + {file_upload_match.group(1)}" if file_upload_match else ""
    
    # Q: 案件详情（带建议截止日期）
    # 整合描述和建议截止日期
    # 重用I列的结果，避免重复NLP处理
    detail_text = result['I_nature_of_request']
    if result['N_works_completion_due']:
        detail_text += f"\n建议工程完成截止日期: {result['N_works_completion_due']}"
    result['Q_case_details'] = detail_text
    
    return result
