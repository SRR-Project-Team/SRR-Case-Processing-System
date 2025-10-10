# SRR Case Processing System - Project Structure

## 📁 Directory Overview

```
project3/
├── 📁 config/                    # Configuration files
├── 📁 data/                      # Database and runtime data
├── 📁 docs/                      # Documentation
├── 📁 frontend/                  # React frontend application
├── 📁 images/                    # Screenshots and assets
├── 📁 models/                    # AI models and cached data
├── 📁 src/                       # Source code
├── 📄 LICENSE                    # MIT License
├── 📄 README.md                  # Main project documentation
├── 📄 WORKFLOW_DESIGN.md         # System workflow design
├── 📄 PROJECT_STRUCTURE.md       # This file
└── 📄 start.py                   # System startup script
```

## 🔧 Configuration (`config/`)

```
config/
├── 📄 settings.py                # Application settings
└── 📄 requirements.txt           # Python dependencies
```

### Key Files
- **settings.py**: Environment variables and API configuration
- **requirements.txt**: Python package dependencies

## 💾 Data Storage (`data/`)

```
data/
└── 📄 srr_cases.db               # SQLite database
```

### Database Schema
- **Cases Table**: Stores processed case records
- **Fields**: A-Q columns + metadata (created_at, updated_at)

## 📚 Documentation (`docs/`)

```
docs/
├── 📄 README.md                  # Documentation index
├── 📄 API_DOCUMENTATION.md       # API endpoints and usage
├── 📄 DATABASE_GUIDE.md          # Database operations
├── 📄 DEPLOYMENT_GUIDE.md        # Production deployment
├── 📄 DEVELOPMENT_GUIDE.md       # Development setup
├── 📄 AI_FEATURES.md             # AI functionality details
└── 📄 DESIGN_PROTOTYPE.md        # Interface design prototype
```

### Documentation Structure
- **README.md**: Main documentation hub
- **API_DOCUMENTATION.md**: RESTful API reference
- **DATABASE_GUIDE.md**: Database schema and operations
- **DEPLOYMENT_GUIDE.md**: Production deployment instructions
- **DEVELOPMENT_GUIDE.md**: Development environment setup
- **AI_FEATURES.md**: AI model details and usage
- **DESIGN_PROTOTYPE.md**: Interface design specifications and prototype

## 🎨 Frontend (`frontend/`)

```
frontend/
└── 📁 srr-chatbot/               # React application
    ├── 📁 build/                 # Production build
    ├── 📁 public/                # Static assets
    ├── 📁 src/                   # Source code
    │   ├── 📁 components/        # React components
    │   ├── 📁 services/          # API services
    │   ├── 📁 types/             # TypeScript types
    │   └── 📄 *.tsx              # React components
    ├── 📄 package.json           # Node.js dependencies
    └── 📄 README.md              # Frontend documentation
```

### Frontend Components
- **ChatbotInterface.tsx**: Main integrated chat interface
- **FileUploadModal.tsx**: File upload and management popup
- **FileInfoModal.tsx**: File processing details popup
- **ExtractedInfoDisplay.tsx**: Results display component
- **UploadDetailsModal.tsx**: Upload details modal (legacy)
- **api.ts**: API communication service
- **config.ts**: Frontend configuration

## 🤖 AI Models (`models/`)

```
models/
├── 📁 ai_models/                 # Cached AI models
├── 📁 config/                    # Model configurations
└── 📁 mapping_rules/             # Data mapping rules
```

### Model Files
- **training_data.pkl**: Cached training data
- **keyword_rules.json**: Classification rules
- **srr_rules.json**: SRR-specific rules
- **slope_location_mapping.json**: Location mappings

## 💻 Source Code (`src/`)

```
src/
├── 📁 ai/                        # AI processing modules
├── 📁 api/                       # FastAPI application
├── 📁 core/                      # Core processing logic
├── 📁 database/                  # Database management
├── 📁 services/                  # External services
└── 📁 utils/                     # Utility modules
```

### Core Modules

#### AI Processing (`src/ai/`)
```
ai/
├── 📄 ai_case_type_classifier.py     # Case type classification
├── 📄 ai_model_cache.py              # Model caching system
├── 📄 ai_request_summarizer.py       # Request summarization
├── 📄 ai_subject_matter_classifier.py # Subject matter classification
└── 📄 nlp_enhanced_processor.py      # NLP processing
```

#### API Layer (`src/api/`)
```
api/
└── 📄 main.py                         # FastAPI application
```

#### Core Processing (`src/core/`)
```
core/
├── 📄 extractFromTxt.py              # TXT file processing
├── 📄 extractFromTMO.py              # TMO PDF processing
├── 📄 extractFromRCC.py              # RCC PDF processing
└── 📄 output.py                      # Output formatting
```

#### Database (`src/database/`)
```
database/
├── 📄 __init__.py                    # Package initialization
├── 📄 manager.py                     # Database operations
└── 📄 models.py                      # Database models
```

#### Services (`src/services/`)
```
services/
└── 📄 llm_service.py                 # Doubao API service
```

#### Utilities (`src/utils/`)
```
utils/
├── 📄 email_info_extractor.py        # Email parsing
├── 📄 file_utils.py                  # File operations
├── 📄 model_loader.py                # Model loading
├── 📄 slope_location_mapper.py       # Location mapping
├── 📄 smart_file_pairing.py          # File pairing logic
└── 📄 source_classifier.py           # Source classification
```

## 🚀 System Startup (`start.py`)

The main startup script that manages the entire system:

```python
Usage:
python start.py start [--logs]     # Start system
python start.py stop               # Stop system
python start.py check              # Check status
python start.py cleanup            # Clean processes
```

### Features
- **Process Management**: Start/stop backend and frontend
- **Log Monitoring**: Real-time log display
- **Health Checks**: System status verification
- **Cleanup**: Process cleanup and resource management

## 🔄 Data Flow

### 1. File Upload
```
User Interface → FastAPI → File Storage → Processing Pipeline
```

### 2. Processing Pipeline
```
File Type Detection → Content Extraction → AI Processing → Data Structuring → Database Storage
```

### 3. Response Generation
```
Database → JSON Formatting → API Response → Frontend Display
```

## 🛠️ Development Workflow

### 1. Backend Development
```bash
# Install dependencies
pip install -r config/requirements.txt

# Run backend
python src/api/main.py

# Run with logs
python start.py start --logs
```

### 2. Frontend Development
```bash
# Install dependencies
cd frontend/srr-chatbot
npm install

# Run development server
npm start
```

### 3. Full System
```bash
# Start complete system
python start.py start

# Check status
python start.py check
```

## 📊 Key Dependencies

### Python Backend
- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **EasyOCR**: OCR processing
- **volcengine-python-sdk**: Doubao API client
- **Pandas**: Data processing
- **scikit-learn**: Machine learning

### Node.js Frontend
- **React**: UI framework
- **TypeScript**: Type safety
- **Axios**: HTTP client
- **React-Dropzone**: File upload

## 🔧 Environment Configuration

### Required Environment Variables
```bash
ARK_API_KEY="your_doubao_api_key"  # Volcengine API key
```

### Optional Configuration
```bash
API_HOST="localhost"               # API host
API_PORT="8001"                   # API port
FRONTEND_PORT="3000"              # Frontend port
```

## 📈 Performance Considerations

### Memory Usage
- **AI Models**: ~2GB RAM for model caching
- **OCR Processing**: Additional memory for image processing
- **Database**: Minimal memory footprint

### Storage Requirements
- **Models**: ~500MB for cached models
- **Database**: Grows with case volume
- **Temporary Files**: Cleaned automatically

## 🔒 Security Considerations

### API Security
- **CORS**: Configured for frontend access
- **File Upload**: Temporary file handling
- **Data Validation**: Input sanitization

### Data Privacy
- **Temporary Files**: Automatic cleanup
- **Database**: Local SQLite storage
- **API Keys**: Environment variable storage

---

This project structure provides a clean, modular architecture that supports both development and production deployment while maintaining clear separation of concerns and easy maintenance.
