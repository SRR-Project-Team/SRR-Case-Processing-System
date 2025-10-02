"""
RCC (Regional Coordinating Committee) PDF数据提取模块

本模块负责从RCC的PDF文件中提取SRR案件数据，主要处理RCC开头的PDF文件。
由于RCC文件可能是扫描件或加密文件，需要特殊处理。

RCC PDF文件结构特点：
- 斜坡編號 对应 G_slope_no
- 案件编号 对应 C_1823_case_no
- 日期信息 对应 A_date_received
- 来源信息 对应 B_source
- 联系信息 对应 E_caller_name, F_contact_no

作者: AI Assistant
版本: 1.0
"""
import re
import os
import pdfplumber
import PyPDF2
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ai_case_type_classifier import classify_case_type_ai
from ai.ai_subject_matter_classifier import classify_subject_matter_ai
from ai.ai_request_summarizer import generate_ai_request_summary
from utils.slope_location_mapper import get_location_from_slope_no
from utils.source_classifier import classify_source_smart


def parse_date(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串为datetime对象（用于计算），失败返回None
    
    Args:
        date_str (str): 日期字符串，支持多种格式
        
    Returns:
        Optional[datetime]: 解析成功返回datetime对象，失败返回None
    """
    if not date_str:
        return None
    
    # 尝试多种日期格式
    date_formats = [
        "%Y-%m-%d",      # "2025-01-21"
        "%Y/%m/%d",      # "2025/03/18"
        "%d/%m/%Y",      # "21/01/2025"
        "%d-%m-%Y",      # "21-01-2025"
        "%d %B %Y",      # "21 January 2025"
        "%Y年%m月%d日",   # "2025年01月21日"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def format_date(dt: Optional[datetime]) -> str:
    """
    将datetime对象格式化为dd-MMM-yyyy格式，None返回空
    
    Args:
        dt (Optional[datetime]): 要格式化的datetime对象
        
    Returns:
        str: dd-MMM-yyyy格式的日期字符串，如 "15-Jan-2024"
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
    """
    if not base_date:
        return ""
    return format_date(base_date + timedelta(days=days))


def extract_content_with_multiple_methods(pdf_path: str) -> str:
    """
    使用多种方法提取PDF内容，包括处理旋转页面
    
    Args:
        pdf_path (str): PDF文件路径
        
    Returns:
        str: 提取的文本内容
    """
    content = ""
    
    # 方法1: 使用pdfplumber，处理旋转页面
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # 检查页面旋转
                rotation = getattr(page, 'rotation', 0)
                if rotation:
                    print(f"检测到页面{i+1}旋转: {rotation}度")
                
                # 尝试原始提取
                text = page.extract_text()
                if text:
                    content += text + "\n"
                else:
                    # 如果原始提取失败，尝试不同的参数
                    try:
                        # 尝试不同的文本提取参数
                        text = page.extract_text(
                            x_tolerance=3,
                            y_tolerance=3,
                            layout=True,
                            x_density=7.25,
                            y_density=13
                        )
                        if text:
                            content += text + "\n"
                            print(f"使用特殊参数成功提取页面{i+1}文本")
                    except Exception as e:
                        print(f"特殊参数提取失败: {e}")
                        
    except Exception as e:
        print(f"pdfplumber提取失败: {e}")
    
    # 方法2: 使用PyPDF2
    if not content:
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        content += text + "\n"
                    else:
                        # 尝试不同的提取方法
                        try:
                            # 尝试提取文本流
                            if hasattr(page, 'get_contents'):
                                contents = page.get_contents()
                                if contents:
                                    print(f"页面{i+1}包含内容流，但无法直接提取文本")
                        except Exception as e:
                            print(f"页面{i+1}内容流提取失败: {e}")
        except Exception as e:
            print(f"PyPDF2提取失败: {e}")
    
    # 方法3: 尝试快速OCR (如果安装了相关库)
    if not content:
        try:
            content = extract_text_with_ocr_fast(pdf_path)
        except Exception as e:
            print(f"快速OCR提取失败: {e}")
    
    return content


def extract_text_with_ocr_fast(pdf_path: str) -> str:
    """
    快速OCR处理，优先速度，限制处理时间
    """
    import time
    start_time = time.time()
    max_processing_time = 60  # 最大处理时间60秒
    content = ""
    
    # 只使用最快的EasyOCR方法
    try:
        import easyocr
        import fitz  # PyMuPDF
        from PIL import Image
        import io
        
        print("使用快速EasyOCR提取文本...")
        
        # 初始化EasyOCR (只使用英文，最快设置)
        reader = easyocr.Reader(['en'], gpu=False, verbose=False, download_enabled=False)
        
        doc = fitz.open(pdf_path)
        
        # 只处理前2页，避免处理时间过长
        max_pages = min(2, len(doc))
        
        for page_num in range(max_pages):
            # 检查处理时间限制
            if time.time() - start_time > max_processing_time:
                print(f"⏰ 快速OCR处理超时({max_processing_time}秒)，停止处理")
                break
                
            page = doc.load_page(page_num)
            
            # 使用更低的分辨率，优先速度
            mat = fitz.Matrix(1.5, 1.5)  # 进一步降低到1.5倍分辨率
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # 使用PIL打开图像
            image = Image.open(io.BytesIO(img_data))
            
            # 转换为numpy数组 (EasyOCR需要numpy数组)
            import numpy as np
            image_array = np.array(image)
            
            # 使用EasyOCR进行OCR，降低置信度阈值
            results = reader.readtext(image_array)
            
            # 提取文本
            page_text = ""
            for (bbox, text, confidence) in results:
                if confidence > 0.2:  # 进一步降低置信度阈值
                    page_text += text + " "
            
            if page_text.strip():
                content += page_text.strip() + "\n"
                print(f"快速OCR成功提取页面{page_num+1}文本: {len(page_text)}字符")
        
        doc.close()
        
        if content.strip():
            processing_time = time.time() - start_time
            print(f"✅ 快速OCR完成，耗时: {processing_time:.2f}秒")
            return content
        
    except ImportError:
        print("EasyOCR未安装，跳过快速OCR")
    except Exception as e:
        print(f"快速OCR提取异常: {e}")
    
    # 如果快速OCR失败，回退到传统方法
    print("快速OCR失败，回退到传统OCR方法...")
    return extract_text_with_ocr_traditional(pdf_path)


def extract_text_with_ocr(pdf_path: str) -> str:
    """
    使用OCR技术从PDF中提取文本，优先速度
    
    Args:
        pdf_path (str): PDF文件路径
        
    Returns:
        str: OCR提取的文本内容
    """
    # 直接使用快速OCR，跳过AI增强处理
    print("使用快速OCR提取文本...")
    return extract_text_with_ocr_fast(pdf_path)


def extract_text_with_ocr_traditional(pdf_path: str) -> str:
    """
    传统OCR方法作为备选，限制处理时间
    """
    import time
    start_time = time.time()
    max_processing_time = 90  # 最大处理时间90秒
    content = ""
    
    # 方法1: 尝试EasyOCR 
    try:
        import easyocr
        import fitz  # PyMuPDF
        from PIL import Image
        import io
        
        print("使用传统EasyOCR提取文本...")
        
        # 初始化EasyOCR (只使用英文，避免语言冲突，提高速度)
        reader = easyocr.Reader(['en'], gpu=False, verbose=False, download_enabled=False)
        
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            # 检查处理时间限制
            if time.time() - start_time > max_processing_time:
                print(f"⏰ OCR处理超时({max_processing_time}秒)，停止处理")
                break
                
            page = doc.load_page(page_num)
            
            # 获取页面图像，处理旋转 (进一步降低分辨率以提高速度)
            mat = fitz.Matrix(1.8, 1.8)  # 降低到1.8倍分辨率，优先速度
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # 使用PIL打开图像
            image = Image.open(io.BytesIO(img_data))
            
            # 转换为numpy数组 (EasyOCR需要numpy数组)
            import numpy as np
            image_array = np.array(image)
            
            # 使用EasyOCR进行OCR
            results = reader.readtext(image_array)
            
            # 提取文本
            page_text = ""
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # 降低置信度阈值以获取更多文本
                    page_text += text + " "
            
            if page_text.strip():
                content += page_text.strip() + "\n"
                print(f"EasyOCR成功提取页面{page_num+1}文本: {len(page_text)}字符")
        
        doc.close()
        return content
        
    except ImportError:
        print("EasyOCR未安装，尝试其他方法...")
    except Exception as e:
        print(f"EasyOCR提取异常: {e}")
    
    # 方法2: 尝试Tesseract OCR (备选)
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
        import io
        
        print("使用Tesseract OCR提取文本...")
        
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # 获取页面图像 (进一步降低分辨率以提高速度)
            mat = fitz.Matrix(1.8, 1.8)  # 降低到1.8倍分辨率，优先速度
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # 使用PIL打开图像
            image = Image.open(io.BytesIO(img_data))
            
            # 使用Tesseract进行OCR
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            if text.strip():
                content += text + "\n"
                print(f"Tesseract成功提取页面{page_num+1}文本")
        
        doc.close()
        return content
        
    except ImportError:
        print("Tesseract OCR未安装，跳过OCR提取")
        return ""
    except Exception as e:
        print(f"Tesseract OCR提取异常: {e}")
        return ""
    
    # 方法3: 尝试pdf2image + OCR
    try:
        from pdf2image import convert_from_path
        import easyocr
        
        print("使用pdf2image + EasyOCR提取文本...")
        
        # 将PDF转换为图像 (进一步降低DPI以提高速度)
        images = convert_from_path(pdf_path, dpi=150)
        
        # 初始化EasyOCR (优化速度)
        reader = easyocr.Reader(['en'], gpu=False, verbose=False, download_enabled=False)
        
        for i, image in enumerate(images):
            # 转换为numpy数组 (EasyOCR需要numpy数组)
            import numpy as np
            image_array = np.array(image)
            
            # 使用EasyOCR进行OCR
            results = reader.readtext(image_array)
            
            # 提取文本
            page_text = ""
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # 降低置信度阈值以获取更多文本
                    page_text += text + " "
            
            if page_text.strip():
                content += page_text.strip() + "\n"
                print(f"pdf2image+EasyOCR成功提取页面{i+1}文本: {len(page_text)}字符")
        
        return content
        
    except ImportError:
        print("pdf2image未安装，跳过此方法")
        return ""
    except Exception as e:
        print(f"pdf2image+OCR提取异常: {e}")
        return ""
    
    print("所有OCR方法都不可用，请安装相关库")
    return ""


def extract_rcc_case_number(content: str, pdf_path: str = None) -> str:
    """
    提取RCC案件编号
    
    优先从文件名提取RCC#后面的数字，如果没有则从PDF内容中提取
    
    Args:
        content (str): PDF文本内容
        pdf_path (str): PDF文件路径
        
    Returns:
        str: RCC案件编号
    """
    # 优先从文件名提取RCC#后面的数字
    if pdf_path:
        filename = os.path.basename(pdf_path)
        filename_match = re.search(r'RCC[#\s]*(\d+)', filename, re.IGNORECASE)
        if filename_match:
            case_number = filename_match.group(1)
            print(f"✅ 从文件名提取RCC案件编号: {case_number}")
            return case_number
    
    # 如果文件名中没有，则从PDF内容中提取
    patterns = [
        r'Call\s+Reference\s+No[:\s]+(\d+)',  # Call Reference No: 84878800
        r'RCC[#\s]*(\d+)',                    # RCC#84878800
        r'案件編號[：:]\s*([A-Z0-9\-]+)',      # 案件編號: XXX
        r'Case\s+No\.?\s*([A-Z0-9\-]+)',      # Case No. XXX
        r'編號[：:]\s*([A-Z0-9\-]+)',         # 編號: XXX
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            case_number = match.group(1).strip()
            print(f"✅ 从PDF内容提取RCC案件编号: {case_number}")
            return case_number
    
    print("⚠️ 未找到RCC案件编号")
    return ""


def extract_slope_number(content: str) -> str:
    """
    提取斜坡编号
    
    Args:
        content (str): PDF文本内容
        
    Returns:
        str: 斜坡编号
    """
    # 匹配各种可能的斜坡编号格式
    patterns = [
        r'斜坡編號[：:為为]?\s*([A-Z0-9\-/]+)',  # 斜坡編號: XXX
        r'Slope\s+No\.?\s*([A-Z0-9\-/]+)',      # Slope No. XXX
        r'斜坡牌號[：:為为]?\s*([A-Z0-9\-/]+)',  # 斜坡牌號: XXX
        r'編號[：:]\s*([A-Z0-9\-/]+)',         # 編號: XXX
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip().upper()
    
    return ""


def extract_date_from_content(content: str) -> str:
    """
    从RCC内容中提取日期信息
    
    Args:
        content (str): RCC文本内容
        
    Returns:
        str: 日期字符串
    """
    # 优先匹配Handle Date (OCR可能识别为IIandle)
    date_patterns = [
        r'[Hh]andle\s+[Dd]ate[:\s]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'IIandle\s+[Dd]ate[:\s]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # OCR可能将H识别为II
        r'Call-in\s+Date[:\s]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'Date[:\s]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # YYYY/MM/DD 或 YYYY-MM-DD
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # DD/MM/YYYY 或 DD-MM-YYYY
        r'(\d{1,2}\s+\w+\s+\d{4})',  # DD Month YYYY
        r'(\w+\s+\d{1,2},?\s+\d{4})'  # Month DD, YYYY
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            # 清理日期字符串，移除时间部分
            date_str = re.sub(r'\s+\d{1,2}:\d{2}:\d{2}', '', date_str)
            return date_str
    
    return ""


def extract_source_info(content: str) -> str:
    """
    提取来源信息
    
    Args:
        content (str): PDF文本内容
        
    Returns:
        str: 来源信息
    """
    # 匹配来源信息
    patterns = [
        r'來源[：:]\s*([^\n]+)',      # 來源: XXX
        r'Source[：:]\s*([^\n]+)',    # Source: XXX
        r'From[：:]\s*([^\n]+)',      # From: XXX
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            source = match.group(1).strip()
            if "RCC" in source.upper():
                return "RCC"
            return source
    
    return "RCC"  # 默认返回RCC


def extract_contact_info(content: str) -> Tuple[str, str]:
    """
    提取联系人信息
    
    Args:
        content (str): PDF文本内容
        
    Returns:
        Tuple[str, str]: (联系人姓名, 联系电话)
    """
    # 匹配联系人信息 - 优化OCR识别
    name_patterns = [
        r'Name\s*:\s*of\s*Client[:\s]+([A-Za-z\s]+?)(?=\s+Contact\s+Tel\s+No)',  # Name: of Client: Sung Man Contact Tel No
        r'Name\s+of\s+Client[:\s]+([A-Za-z\s]+?)(?=\s+Contact\s+Tel\s+No)',  # Name of Client: Sung Man Contact Tel No
        r'Nale\s+of\s+Client[:\s]+([A-Za-z\s]+?)(?=\s+Contact\s+Tel\s+No)',  # Nale of Client: (OCR可能将Name识别为Nale)
        r'Name\s+of\s+client[:\s]+([A-Za-z\s]+?)(?=\s+Contact\s+Tel\s+No)',  # Name of client: Sung Man Contact Tel No
        r'Contact\s+person\s+\'s\s+Name\s+\(on\s+Site\)[:\s]+([^\n]+?)(?=\s+Title)',  # Contact person's Name (on Site): XXX
        r'聯絡人[：:]\s*([^\n]+)',      # 聯絡人: XXX
        r'Contact[：:]\s*([^\n]+)',      # Contact: XXX
        r'姓名[：:]\s*([^\n]+)',        # 姓名: XXX
        r'Name[：:]\s*([^\n]+)',        # Name: XXX
    ]
    
    phone_patterns = [
        r'Contact\s+Tel\s+No[:\s]+(\d+)',  # Contact Tel No: 25300155
        r'電話[：:]\s*([^\n]+)',       # 電話: XXX
        r'Phone[：:]\s*([^\n]+)',       # Phone: XXX
        r'聯絡電話[：:]\s*([^\n]+)',    # 聯絡電話: XXX
        r'Tel[：:]\s*([^\n]+)',        # Tel: XXX
    ]
    
    name = ""
    phone = ""
    
    for pattern in name_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # 清理OCR错误，如"of Client: Sung Man" -> "Sung Man"
            if "of Client:" in name:
                name = name.replace("of Client:", "").strip()
            break
    
    for pattern in phone_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            phone = match.group(1).strip()
            break
    
    return name, phone


def extract_slope_number(content: str) -> str:
    """
    提取斜坡编号，支持多种模式并去除干扰信息
    
    支持的提取模式：
    1. slope.no 后面的内容
    2. Form 2 ref. no 后面的内容中提取
    3. 斜坡编号 后面的内容
    
    Args:
        content (str): PDF文本内容
        
    Returns:
        str: 清理后的斜坡编号
    """
    print("🔍 RCC开始提取斜坡编号...")
    
    # 模式1: slope.no 后面的内容
    slope_no_patterns = [
        r'slope\.?\s*no\.?\s*[:\s]+([A-Z0-9\-/#\s]+)',  # slope.no: 11SW-D/CR995
        r'slope\s+no\.?\s*[:\s]+([A-Z0-9\-/#\s]+)',     # slope no: 11SW-D/CR995
        r'slope\s*[:\s]+([A-Z0-9\-/#\s]+)',             # slope: 11SW-D/CR995
    ]
    
    for pattern in slope_no_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            slope_no = clean_slope_number_rcc(match.group(1))
            if slope_no:
                print(f"✅ 从slope.no提取斜坡编号: {slope_no}")
                return slope_no
    
    # 模式2: Form 2 ref. no 后面的内容中提取
    form_ref_patterns = [
        r'Form\s+2\s+ref\.?\s+no\.?\s*[:\s]+form2-([A-Z0-9/#\s]+?)(?:-\d{8}-\d{3}|$)',  # Form 2 ref. no: form2-11SWB/F199-20241028-002
        r'form2-([A-Z0-9/#\s]+?)(?:-\d{8}-\d{3}|$)',  # form2-11SWB/F199-20241028-002，只提取斜坡编号部分
    ]
    
    for pattern in form_ref_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            extracted = match.group(1)
            # 格式化斜坡编号
            slope_no = format_slope_number_rcc(extracted)
            
            if slope_no:
                print(f"✅ 从Form 2 ref. no提取斜坡编号: {slope_no}")
                return slope_no
    
    # 模式3: 斜坡编号 后面的内容
    chinese_patterns = [
        r'斜坡[（(]編號[）)][:\s]+([A-Z0-9\-/#\s]+)',  # 斜坡（編號）: 11SW-D/CR995
        r'斜坡編號[:\s]+([A-Z0-9\-/#\s]+)',           # 斜坡編號: 11SW-D/CR995
        r'斜坡编号[:\s]+([A-Z0-9\-/#\s]+)',           # 斜坡编号: 11SW-D/CR995
        r'Slope\s+No\.?[:\s]+([A-Z0-9\-/#\s]+)',      # Slope No: 11SW-D/CR995
    ]
    
    for pattern in chinese_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            slope_no = clean_slope_number_rcc(match.group(1))
            if slope_no:
                print(f"✅ 从斜坡编号提取: {slope_no}")
                return slope_no
    
    # 模式4: 通用斜坡编号格式匹配
    general_patterns = [
        r'(\d+SW[-\s]*[A-Z][-\s]*/?[A-Z]*\d+)',        # 11SW-D/CR995
        r'([A-Z0-9]+SW[-\s]*[A-Z][-\s]*/?[A-Z]*\d+)',  # 通用格式
        r'(\d{2}[A-Z]{2}[-\s]*[A-Z][-\s]*/?[A-Z]*\d+)', # 11SW-D/995
    ]
    
    for pattern in general_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            slope_no = clean_slope_number_rcc(match.group(1))
            if slope_no:
                print(f"✅ 从通用格式提取斜坡编号: {slope_no}")
                return slope_no
    
    print("⚠️ RCC未找到斜坡编号")
    return ""


def clean_slope_number_rcc(slope_text: str) -> str:
    """
    清理RCC斜坡编号，去除干扰信息
    
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
    
    # 修正OCR错误
    if cleaned.startswith('LSW') or cleaned.startswith('ISW') or cleaned.startswith('JSW'):
        cleaned = '11SW' + cleaned[3:]
    elif cleaned.startswith('lSW') or cleaned.startswith('iSW') or cleaned.startswith('jSW'):
        cleaned = '11SW' + cleaned[3:]
    elif cleaned.startswith('1SW') and len(cleaned) > 3:
        # 处理 1SW-D/CR995 -> 11SW-D/CR995
        cleaned = '11SW' + cleaned[3:]
    
    # 确保格式正确
    if cleaned and len(cleaned) >= 4:
        # 标准化连字符格式
        if 'SW' in cleaned and '-' not in cleaned:
            # 在SW后添加连字符，如11SWD -> 11SW-D
            cleaned = re.sub(r'(SW)([A-Z])', r'\1-\2', cleaned)
    
    return cleaned


def format_slope_number_rcc(slope_no: str) -> str:
    """
    格式化RCC斜坡编号，转换为标准格式
    
    Args:
        slope_no (str): 原始斜坡编号
        
    Returns:
        str: 格式化后的斜坡编号
    """
    if not slope_no:
        return ""
    
    # 去除#号、空格和其他干扰字符
    cleaned = re.sub(r'[#\s]+', '', slope_no.strip())
    
    # 只保留字母、数字、连字符和斜杠
    cleaned = re.sub(r'[^A-Z0-9\-/]', '', cleaned.upper())
    
    # 转换格式：11SWB/F199 -> 11SW-B/F199
    if 'SWB' in cleaned and 'SW-B' not in cleaned:
        cleaned = cleaned.replace('SWB', 'SW-B')
    elif 'SWD' in cleaned and 'SW-D' not in cleaned:
        cleaned = cleaned.replace('SWD', 'SW-D')
    elif 'SWC' in cleaned and 'SW-C' not in cleaned:
        cleaned = cleaned.replace('SWC', 'SW-C')
    elif 'SWA' in cleaned and 'SW-A' not in cleaned:
        cleaned = cleaned.replace('SWA', 'SW-A')
    
    return cleaned


def extract_location_info(content: str) -> str:
    """
    提取位置信息
    
    Args:
        content (str): PDF文本内容
        
    Returns:
        str: 位置信息
    """
    # 优先匹配Address字段（支持OCR识别的格式）
    address_patterns = [
        r'Address[:\s]+([A-Za-z0-9\s,.-]+?)(?=\s*\(slope\s+no)',  # Address: Broadwood Road Mini Park(slope no
        r'Address[:\s]+([A-Za-z0-9\s,.-]+?)(?=\s+Contact\s+person)',  # Address: 实际地址 Contact person
        r'地址[:\s]+([A-Za-z0-9\s,.-]+?)(?=\s+Contact\s+person)',     # 地址: 实际地址 Contact person
    ]
    
    for pattern in address_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            address = match.group(1).strip()
            # 检查是否包含有效地址信息
            if address and not any(keyword in address.lower() for keyword in ['contact', 'person', 'title', 'mr', 'mobile']):
                return address
    
    # 查找包含GARDEN、BOTANICAL等关键词的位置信息
    garden_patterns = [
        r'([A-Z\s]+GARDEN[A-Z\s]*)',  # ZOOLOGICAL AND BOTANICAL GARDEN
        r'([A-Z\s]+BOTANICAL[A-Z\s]*)',  # BOTANICAL GARDEN
        r'([A-Z\s]+ZOOLOGICAL[A-Z\s]*)',  # ZOOLOGICAL GARDEN
    ]
    
    for pattern in garden_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            garden_name = match.group(1).strip()
            if len(garden_name) > 10:  # 确保是完整的地名
                return garden_name
    
    # 备选：Location Code
    location_code_match = re.search(r'Location\s+Code[:\s]+([A-Z0-9]+)', content, re.IGNORECASE)
    if location_code_match:
        return f"Location Code: {location_code_match.group(1)}"
    
    # 备选位置信息
    patterns = [
        r'位置[：:]\s*([^\n]+)',        # 位置: XXX
        r'Location[：:]\s*([^\n]+)',    # Location: XXX
        r'地點[：:]\s*([^\n]+)',        # 地點: XXX
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""


def extract_nature_of_request(content: str) -> str:
    """
    提取请求性质
    
    Args:
        content (str): PDF文本内容
        
    Returns:
        str: 请求性质摘要
    """
    # 匹配请求性质
    patterns = [
        r'性質[：:]\s*([^\n]+)',        # 性質: XXX
        r'Nature[：:]\s*([^\n]+)',      # Nature: XXX
        r'內容[：:]\s*([^\n]+)',       # 內容: XXX
        r'Description[：:]\s*([^\n]+)', # Description: XXX
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            desc = match.group(1).strip()
            return desc[:100] + "..." if len(desc) > 100 else desc
    
    return ""


# 注意：get_location_from_slope_no 函数现在从 slope_location_mapper 模块导入


def extract_case_data_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    从RCC PDF文件中提取所有案件数据，返回字典格式
    
    这是主要的RCC数据提取函数，按照A-Q字段规则提取：
    - A: 案件接收日期
    - B: 来源 (RCC)
    - C: 1823案件号 (RCC案件编号)
    - D: 案件类型 (根据内容判断)
    - E: 来电人姓名 (联系人)
    - F: 联系电话
    - G: 斜坡编号
    - H: 位置 (从Excel数据获取)
    - I: 请求性质摘要
    - J: 事项主题
    - K: 10天规则截止日期 (A+10天)
    - L: ICC临时回复截止日期 (不适用)
    - M: ICC最终回复截止日期 (不适用)
    - N: 工程完成截止日期 (取决于D)
    - O1: 发给承包商的传真日期 (通常同A)
    - O2: 邮件发送时间 (不适用)
    - P: 传真页数 (PDF页数)
    - Q: 案件详情
    
    Args:
        pdf_path (str): PDF文件路径
        
    Returns:
        Dict[str, Any]: 包含所有A-Q字段的字典
    """
    result = {}
    
    # 提取PDF内容
    content = extract_content_with_multiple_methods(pdf_path)
    
    if not content:
        print("警告: 无法从PDF文件中提取文本内容，可能是扫描件或加密文件")
        print("提示: 请使用OCR工具将PDF转换为文本，或提供可编辑的PDF文件")
        
        # 即使无法提取文本，也提供一些基本信息
        result = {}
        
        # 从文件名提取基本信息
        # B: 来源（智能分类）
        result['B_source'] = classify_source_smart(
            file_path=pdf_path, 
            content="", 
            email_content=None, 
            file_type='pdf'
        )
        
        filename = os.path.basename(pdf_path)
        # 尝试从文件名提取案件编号
        result['C_case_number'] = extract_rcc_case_number("", pdf_path)
        
        # 设置默认值
        result['A_date_received'] = ""
        result['D_type'] = "General"
        result['E_caller_name'] = ""
        result['F_contact_no'] = ""
        result['G_slope_no'] = ""
        result['H_location'] = ""
        result['I_nature_of_request'] = "RCC案件处理 - 无法提取具体请求内容"
        result['J_subject_matter'] = "Others"
        result['K_10day_rule_due_date'] = ""
        result['L_icc_interim_due'] = ""
        result['M_icc_final_due'] = ""
        result['N_works_completion_due'] = ""
        result['O1_fax_to_contractor'] = ""
        result['O2_email_send_time'] = ""
        
        # 获取PDF页数
        try:
            with pdfplumber.open(pdf_path) as pdf:
                result['P_fax_pages'] = str(len(pdf.pages))
        except:
            result['P_fax_pages'] = ""
        
        result['Q_case_details'] = f"RCC案件处理 - 文件: {filename} (无法提取文本内容)"
        
        return result
    
    # A: 案件接收日期
    date_str = extract_date_from_content(content)
    result['A_date_received'] = format_date(parse_date(date_str))
    A_date = parse_date(date_str)
    
    # B: 来源（智能分类）
    result['B_source'] = classify_source_smart(
        file_path=pdf_path, 
        content=content, 
        email_content=None, 
        file_type='pdf'
    )
    
    # C: 案件编号 (RCC案件编号，优先从文件名提取)
    result['C_case_number'] = extract_rcc_case_number(content, pdf_path)
    
    # D: 案件类型 (使用AI分类)
    try:
        print("🤖 RCC使用AI分类案件类型...")
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
        print(f"✅ RCC AI分类完成: {result['D_type']} (置信度: {ai_result.get('confidence', 0):.2f})")
    except Exception as e:
        print(f"⚠️ RCC AI分类失败，使用传统方法: {e}")
        # 传统分类方法作为备用
        if "urgent" in content.lower() or "紧急" in content:
            result['D_type'] = "Urgent"
        elif "emergency" in content.lower() or "紧急" in content:
            result['D_type'] = "Emergency"
        else:
            result['D_type'] = "General"
    
    # E: 来电人姓名；F: 联系电话
    result['E_caller_name'], result['F_contact_no'] = extract_contact_info(content)
    
    # G: 斜坡编号
    result['G_slope_no'] = extract_slope_number(content)
    
    # H: 位置 (优先从Address字段获取，否则从Excel数据获取)
    address_location = extract_location_info(content)
    if address_location:
        result['H_location'] = address_location
    else:
        result['H_location'] = get_location_from_slope_no(result['G_slope_no'])
    
    # I: 请求性质摘要 (使用AI从PDF内容生成具体请求摘要)
    try:
        print("🤖 RCC使用AI生成请求摘要...")
        ai_summary = generate_ai_request_summary(content, None, 'pdf')
        result['I_nature_of_request'] = ai_summary
        print(f"✅ RCC AI请求摘要生成成功: {ai_summary}")
    except Exception as e:
        print(f"⚠️ RCC AI摘要生成失败，使用备用方法: {e}")
        # 备用方法：使用原有的请求性质提取
        result['I_nature_of_request'] = extract_nature_of_request(content)
    
    # J: 事项主题 (使用AI分类器)
    try:
        print("🤖 RCC使用AI分类主题...")
        subject_data_for_ai = {
            'I_nature_of_request': result.get('I_nature_of_request', ''),
            'J_subject_matter': "RCC案件处理",
            'Q_case_details': result.get('Q_case_details', ''),
            'content': content
        }
        ai_subject_result = classify_subject_matter_ai(subject_data_for_ai)
        result['J_subject_matter'] = ai_subject_result.get('predicted_category', 'Others')
        print(f"✅ RCC主题分类完成: {result['J_subject_matter']} (置信度: {ai_subject_result.get('confidence', 0):.2f})")
    except Exception as e:
        print(f"⚠️ RCC主题分类失败，使用默认: {e}")
        result['J_subject_matter'] = "Others"
    
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
    
    # O2: 邮件发送时间 (RCC不适用)
    result['O2_email_send_time'] = ""
    
    # P: 传真页数 (PDF页数)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            result['P_fax_pages'] = str(len(pdf.pages))
    except:
        result['P_fax_pages'] = ""
    
    # Q: 案件详情
    result['Q_case_details'] = f"RCC案件处理 - {result['I_nature_of_request']}"
    
    return result
