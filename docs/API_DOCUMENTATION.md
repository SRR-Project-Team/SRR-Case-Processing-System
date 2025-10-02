# API Documentation

## 🚀 SRR Case Processing API

The SRR Case Processing System provides RESTful APIs for document processing and case data extraction.

## 📡 Base URL

```
http://localhost:8001
```

## 🔗 Endpoints

### 1. Process Single File

**Endpoint:** `POST /api/process-file`

**Description:** Process a single file and extract structured case data.

**Request:**
```http
POST /api/process-file
Content-Type: multipart/form-data

file: [binary file data]
```

**Response:**
```json
{
  "success": true,
  "message": "File processed successfully",
  "filename": "example.txt",
  "file_type": "txt",
  "processing_time": 2.34,
  "structured_data": {
    "A_date_received": "06-Mar-2025",
    "B_source": "E-mail",
    "C_case_number": "3-8641924612",
    "D_type": "Urgent",
    "E_caller_name": "John Doe",
    "F_contact_no": "12345678",
    "G_slope_no": "11SW-B/F199",
    "H_location": "Victoria Park",
    "I_nature_of_request": "Tree risk assessment required",
    "J_subject_matter": "Hazardous tree",
    "K_10day_rule_due_date": "16-Mar-2025",
    "L_icc_interim_due": "16-Mar-2025",
    "M_icc_final_due": "27-Mar-2025",
    "N_field": "",
    "O_field": "",
    "P_field": "",
    "Q_case_details": "Complete case information"
  }
}
```

### 2. Process Multiple Files

**Endpoint:** `POST /api/process-multiple-files`

**Description:** Process multiple files in batch and return structured data for each.

**Request:**
```http
POST /api/process-multiple-files
Content-Type: multipart/form-data

files: [array of binary file data]
```

**Response:**
```json
{
  "success": true,
  "message": "Batch processing completed",
  "total_files": 3,
  "processed_files": 3,
  "failed_files": 0,
  "total_processing_time": 15.67,
  "results": [
    {
      "filename": "case1.txt",
      "file_type": "txt",
      "success": true,
      "processing_time": 2.34,
      "structured_data": { /* A-Q columns */ }
    },
    {
      "filename": "case2.pdf",
      "file_type": "tmo",
      "success": true,
      "processing_time": 45.23,
      "structured_data": { /* A-Q columns */ }
    }
  ]
}
```

### 3. Health Check

**Endpoint:** `GET /health`

**Description:** Check API server health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-03T10:30:00Z",
  "version": "1.0.0"
}
```

## 📋 Supported File Types

| File Type | Extension | Processing Method | Average Time |
|-----------|-----------|-------------------|--------------|
| **TXT** | `.txt` | Text processing + AI | < 5 seconds |
| **TMO** | `.pdf` (ASD-*) | PDF extraction + AI | < 60 seconds |
| **RCC** | `.pdf` (RCC#*) | OCR + AI processing | < 120 seconds |

## 🔧 Request Parameters

### File Upload Requirements
- **Maximum file size:** 50MB per file
- **Supported formats:** TXT, PDF
- **Encoding:** UTF-8, GBK, GB2312, UTF-16, Big5, Latin1
- **Batch limit:** 10 files per request

### Response Format
All responses follow a consistent JSON structure:
```json
{
  "success": boolean,
  "message": string,
  "data": object,
  "error": string (optional)
}
```

## 📊 A-Q Column Structure

The system extracts data into a standardized 17-column format:

| Column | Field Name | Description | Example |
|--------|------------|-------------|---------|
| **A** | `date_received` | Case received date | "06-Mar-2025" |
| **B** | `source` | Source of case | "E-mail" |
| **C** | `case_number` | Case reference number | "3-8641924612" |
| **D** | `type` | Case priority type | "Urgent" |
| **E** | `caller_name` | Contact person name | "John Doe" |
| **F** | `contact_no` | Contact phone number | "12345678" |
| **G** | `slope_no` | Slope identification | "11SW-B/F199" |
| **H** | `location` | Physical location | "Victoria Park" |
| **I** | `nature_of_request` | AI-generated summary | "Tree risk assessment" |
| **J** | `subject_matter` | Case category | "Hazardous tree" |
| **K** | `10day_rule_due_date` | Due date (A + 10 days) | "16-Mar-2025" |
| **L** | `icc_interim_due` | Interim due (A + 10 days) | "16-Mar-2025" |
| **M** | `icc_final_due` | Final due (A + 21 days) | "27-Mar-2025" |
| **N-Q** | `additional_fields` | Reserved fields | "" |

## ⚠️ Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "success": false,
  "message": "Invalid file format",
  "error": "File type not supported"
}
```

#### 413 Payload Too Large
```json
{
  "success": false,
  "message": "File size exceeds limit",
  "error": "Maximum file size is 50MB"
}
```

#### 422 Unprocessable Entity
```json
{
  "success": false,
  "message": "File processing failed",
  "error": "Unable to extract text from PDF"
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "message": "Internal server error",
  "error": "AI model processing failed"
}
```

## 🔒 Security Considerations

### File Upload Security
- **File type validation:** Only TXT and PDF files accepted
- **Content scanning:** Basic malware detection
- **Temporary storage:** Files deleted after processing
- **Size limits:** Prevent resource exhaustion

### Data Privacy
- **No persistent storage:** Files processed in memory
- **Secure transmission:** HTTPS recommended for production
- **Access logging:** All requests logged for audit

## 📈 Performance Guidelines

### Optimization Tips
- **Batch processing:** Use multiple file endpoint for efficiency
- **File size:** Smaller files process faster
- **File quality:** Clear scans improve OCR accuracy
- **Concurrent requests:** Limit to 5 simultaneous requests

### Monitoring
- **Processing time:** Monitor response times
- **Success rate:** Track processing success percentage
- **Error patterns:** Identify common failure modes
- **Resource usage:** Monitor CPU and memory consumption

## 🚀 Getting Started

### Quick Start Example

```python
import requests

# Single file processing
with open('case.txt', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/process-file',
        files={'file': f}
    )
    
result = response.json()
print(f"Success: {result['success']}")
print(f"Case Number: {result['structured_data']['C_case_number']}")
```

### JavaScript Example

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/process-file', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Processing result:', data);
});
```

---

For additional support or questions about the API, please refer to the project documentation or contact the development team.
