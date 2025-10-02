# PDF文件处理支持

## 概述

SRR案件处理API现在支持处理PDF文件，根据文件名自动选择相应的处理模块：

- **TXT文件**: 使用 `extractFromTxt.py` 模块
- **ASD开头的PDF文件**: 使用 `extractFromTMO.py` 模块  
- **RCC开头的PDF文件**: 使用 `extractFromRCC.py` 模块

## 新增模块

### 1. extractFromTMO.py
处理TMO (Tree Management Office) 的PDF文件，主要针对ASD开头的文件。

**主要功能**:
- 提取Date of Referral (对应A_date_received)
- 提取From字段信息 (对应B_source)
- 提取TMO Ref. (对应C_1823_case_no)
- 提取检查员信息和联系方式
- 提取评论和后续行动信息

**字段映射**:
- A_date_received ← Date of Referral
- B_source ← From字段 (简化为"TMO")
- C_1823_case_no ← TMO Ref.
- E_caller_name ← Inspection Officer
- F_contact_no ← Contact
- I_nature_of_request ← COMMENTS FROM TMO
- Q_case_details ← FOLLOW-UP ACTIONS

### 2. extractFromRCC.py
处理RCC (Regional Coordinating Committee) 的PDF文件，主要针对RCC开头的文件。

**主要功能**:
- 支持多种PDF文本提取方法
- 处理中文和英文混合内容
- 提取斜坡编号 (斜坡編號)
- 提取案件编号和联系信息

**字段映射**:
- G_slope_no ← 斜坡編號
- C_1823_case_no ← RCC案件编号
- E_caller_name ← 聯絡人/Contact
- F_contact_no ← 電話/Phone
- B_source ← 来源信息 (默认为"RCC")

## API使用

### 支持的文件类型
- `text/plain` (TXT文件)
- `application/pdf` (PDF文件)

### 文件命名规则
- **TXT文件**: 任意名称，扩展名为.txt
- **ASD PDF文件**: 文件名以"ASD"开头，扩展名为.pdf
- **RCC PDF文件**: 文件名以"RCC"开头，扩展名为.pdf

### 示例请求

```bash
# 处理TXT文件
curl -X POST "http://localhost:8001/api/process-srr-file" \
  -F "file=@case.txt"

# 处理ASD PDF文件
curl -X POST "http://localhost:8001/api/process-srr-file" \
  -F "file=@ASD-WC-20250089-PP.pdf"

# 处理RCC PDF文件  
curl -X POST "http://localhost:8001/api/process-srr-file" \
  -F "file=@RCC#84878800.pdf"
```

### 响应格式
所有文件类型都返回相同的JSON格式，包含A-Q字段的结构化数据。

## 技术实现

### 依赖库
- `pdfplumber`: 主要PDF文本提取库
- `PyPDF2`: 备用PDF处理库
- `pandas`: Excel数据处理
- `fastapi`: Web API框架

### 错误处理
- 支持多种PDF文本提取方法
- 扫描件或加密文件会返回警告信息
- 所有字段都有默认值，确保JSON输出完整

### 性能优化
- 模块化设计，按需加载
- 临时文件自动清理
- 支持大文件处理

## 注意事项

1. **RCC文件处理**: 由于RCC文件可能是扫描件，文本提取可能失败，会返回空字段
2. **文件大小限制**: 建议PDF文件不超过10MB
3. **编码支持**: 支持UTF-8编码的文本内容
4. **错误恢复**: 即使部分字段提取失败，也会返回其他成功提取的字段

## 扩展性

系统设计支持轻松添加新的文件类型处理模块：
1. 创建新的提取模块 (如 `extractFromXXX.py`)
2. 在 `main.py` 中添加文件类型判断逻辑
3. 更新API文档和测试用例
