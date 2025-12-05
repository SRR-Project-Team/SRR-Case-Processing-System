# SRR System Features Guide

## Core Features

### 1. Multi-Format File Processing

**Supported Formats**:
- TXT files (with automatic email detection)
- TMO PDF (form-based extraction)
- RCC PDF (OCR-based extraction)

**Capabilities**:
- Automatic file type detection
- Smart file pairing (TXT + email)
- Batch processing support
- Drag-and-drop interface

### 2. AI-Powered Data Extraction

**AI Models**:
- Case Type Classifier (92% accuracy)
- Subject Matter Classifier (98% accuracy, 17 categories)
- Request Summarizer (LLM-based)
- Source Classifier (rule-based)

**Extracted Fields (A-Q)**:
- A: Date Received
- B: Source (12 types)
- C: Case Number
- D: Type (Emergency/Urgent/General)
- E: Caller Name
- F: Contact Number
- G: Slope Number
- H: Location
- I: Nature of Request (AI summary)
- J: Subject Matter (17 categories)
- K-Q: Additional fields and dates

### 3. Historical Case Matching

**Data Sources** (5,298 historical cases):
- Slopes Complaints 2021 (4,047 cases)
- SRR Data 2021-2024 (1,251 cases)
- Tree Inventory (32,405 trees)

**Matching Algorithm**:
```
Weighted Multi-Criteria Scoring:
- Location:        40% (fuzzy matching)
- Slope/Tree:      30% (exact matching)
- Subject:         15% (keyword matching)
- Caller Name:     10% (fuzzy matching)
- Phone:            5% (exact matching)

Duplicate Threshold: ≥ 70%
```

**Features**:
- Automatic similar case detection
- Location-slope mapping (403 learned associations)
- Tree information extraction
- Inspector remarks parsing
- Statistical analysis

### 4. Integrated Chat Interface

**Design Philosophy**: Popup-based file management within chat

**Components**:
- Main chat area (full screen)
- File Upload Modal (popup)
- File Info Modal (popup)
- Smart button system (context-aware)

**User Experience**:
- All file operations in popups
- Chat always visible
- Automatic similar case search
- Real-time processing feedback

### 5. Database Management

**Storage**:
- SQLite database (current cases)
- Automatic case saving
- Query and search capabilities
- Excluded from similarity search (avoid self-matching)

**API Endpoints**:
- `POST /api/process-srr-file` - Process single file
- `POST /api/process-multiple-files` - Batch processing
- `POST /api/find-similar-cases` - Find similar cases
- `GET /api/case-statistics` - Get statistics
- `GET /api/cases` - List cases
- `GET /api/tree-info` - Get tree information
- `GET /api/location-slopes` - Get location mappings

## Enhanced Features

### Tree Information Extraction

**Extracted Data**:
- Tree ID (e.g., TS036)
- Tree count
- Inspector remarks
- Tree species (from inventory)

**Sources**:
- Remarks column (AZ) in Excel
- Tree inventory database
- Inspector comments

### Complete Complaint Details

**Combined Sources**:
- Nature of complaint column
- Remarks column (full context)
- Inspector findings

**Display**: Up to 300 characters with intelligent truncation

### Verified Slope Numbers

**Prioritization**:
1. Verified Slope No. (inspector confirmed)
2. Original Slope no
3. Extracted from inspector remarks

**Benefit**: Ensures accurate location identification

### Location-Slope Learning

**Auto-Learning**: System learns location name variations from historical data

**Examples**:
- "Broadwood Road" / "Broadwood Rd" → Same slopes
- "Chai Wan" → 106 different slopes
- Handles address variations automatically

**API Access**:
```bash
GET /api/location-slopes?location=Broadwood
```

## LLM Integration

### Supported Providers

**Primary**: OpenAI
- Model: gpt-4o-mini
- Features: Request summarization, text analysis
- Proxy support: Yes (for regional restrictions)

**Alternative**: Volcengine (Doubao)
- Model: Doubao-lite-4k
- Features: Same as OpenAI
- Region: China-optimized

### Configuration

```bash
# OpenAI (Primary)
OPENAI_API_KEY="your-key"
LLM_PROVIDER="openai"

# Proxy (if needed)
OPENAI_PROXY_URL="socks5://localhost:7890"
="true"

# Volcengine (Alternative)
ARK_API_KEY="your-key"
LLM_PROVIDER="volcengine"
```

## Performance

### Processing Speed
- TXT files: < 5 seconds
- TMO PDF: < 60 seconds
- RCC PDF: < 120 seconds
- Similarity search: < 2 seconds (5,298 cases)

### Accuracy
- Case type: 92%
- Subject matter: 98%
- Similar case matching: High precision (weighted scoring)

### Resource Usage
- Memory: ~250MB (with cached data)
- Storage: ~500MB (models + data)
- Concurrent requests: Supported

## Usage Examples

### Basic File Processing

```typescript
// Frontend
const result = await processFile(file);
// Returns: structured case data + AI summary
```

### Find Similar Cases

```typescript
const similar = await findSimilarCases({
  H_location: "Broadwood Road",
  G_slope_no: "11SW-D/CR995",
  J_subject_matter: "Slope maintenance"
});
// Returns: similar cases with scores
```

### Get Location Statistics

```typescript
const stats = await getCaseStatistics({
  location: "Broadwood"
});
// Returns: case counts, date ranges, breakdowns
```

## Quick Start

### 1. Start System
```bash
python start.py start
```

### 2. Access Interface
```
http://localhost:3000
```

### 3. Upload Files
- Click "Upload Files" button
- Drag & drop or select files
- Click "Process Files"
- View results in chat

### 4. View Similar Cases
- Automatically shown after processing
- Click "View Details" for full information
- Review statistics and patterns

## Feature Highlights

✅ **Multi-format support** (TXT, PDF)  
✅ **AI-powered extraction** (92-98% accuracy)  
✅ **Historical case matching** (5,298 cases)  
✅ **Tree information tracking** (32,405 trees)  
✅ **Location-slope learning** (403 mappings)  
✅ **Integrated chat interface** (popup-based)  
✅ **Batch processing** (multiple files)  
✅ **Database management** (SQLite)  
✅ **LLM integration** (OpenAI/Volcengine)  
✅ **Proxy support** (for regional restrictions)  

## Documentation

See also:
- `docs/API_DOCUMENTATION.md` - Complete API reference
- `docs/DEVELOPMENT_GUIDE.md` - Setup and development
- `docs/CASE_SIMILARITY_SEARCH.md` - Matching algorithms
- `docs/OPENAI_API_SETUP.md` - LLM configuration
- `PROJECT_STRUCTURE.md` - Code organization
- `WORKFLOW_DESIGN.md` - System architecture

---

**Last Updated**: 2025-10-19  
**Version**: 2.0

**For detailed usage instructions, see `HOW_TO_USE.md`**

