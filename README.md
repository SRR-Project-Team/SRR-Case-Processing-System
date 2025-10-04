# 🏗️ SRR Case Processing System

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node-16+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)

An AI-powered document processing system that automatically extracts and classifies case data from Slope Risk Reports (SRR) in multiple file formats.

## 🎯 Overview

Transform unstructured documents (TXT, TMO PDFs, RCC PDFs) into standardized case records with AI-powered classification and data extraction.

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r config/requirements.txt
pip install -r config/requirements_ocr.txt

# 2. Start the system
python start.py

# 3. Access the web interface
# Frontend: http://localhost:3000
# API: http://localhost:8001
```

## 🚀 Key Features

- **Multi-format Processing**: TXT files, TMO PDFs, RCC PDFs
- **AI Classification**: 92% accuracy case type, 98% subject matter
- **OCR Processing**: Advanced text recognition for scanned documents
- **Batch Processing**: Handle multiple files simultaneously
- **Web Interface**: Modern chatbot-style interface

## 📁 Project Structure

```
project3/
├── 🚀 start.py              # System startup script
├── 📋 WORKFLOW_DESIGN.md    # Complete workflow documentation
├── src/                     # Source code
│   ├── api/                # FastAPI backend
│   ├── core/               # Document processors
│   ├── ai/                 # AI/ML models
│   └── utils/              # Utility functions
├── frontend/               # React web interface
├── data/                   # Training data & rules
├── config/                 # Configuration files
└── docs/                   # Documentation
```

## 📊 Processing Pipeline

```
File Upload → Classification → Content Extraction → AI Processing → Structured Output
     ↓              ↓               ↓                ↓               ↓
Multi-format    TXT/TMO/RCC    Text/OCR/PDF      Case Type      A-Q Columns
  Support       Detection      Extraction      Classification    JSON Data
```

## 🔧 System Requirements

- **Python 3.8+** with ML libraries
- **Node.js 16+** for frontend
- **4GB+ RAM** for AI models
- **10GB storage** for dependencies

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [📋 WORKFLOW_DESIGN.md](WORKFLOW_DESIGN.md) | **Complete system workflow and architecture** |
| [🗄️ Database Guide](docs/DATABASE_GUIDE.md) | **Database usage and management** |
| [📖 Documentation Index](docs/DOCUMENTATION_INDEX.md) | Complete documentation collection |
| [🔌 API Documentation](docs/API_DOCUMENTATION.md) | API endpoints and usage |
| [🚀 Deployment Guide](docs/DEPLOYMENT_GUIDE.md) | Production deployment instructions |

## 🎯 Performance Metrics

- **TXT Files**: < 5 seconds processing
- **TMO PDFs**: < 60 seconds with AI
- **RCC PDFs**: < 120 seconds including OCR
- **Accuracy**: 95%+ field completion rate

## 🛠️ Development

```bash
# Run system checks
python start.py check

# Clean up existing processes
python start.py cleanup

# Start individual components
cd src/api && python main.py          # Backend only
cd frontend/srr-chatbot && npm start  # Frontend only

# View help
python start.py help
```

## 🔧 Advanced Usage

### Smart Process Management
The startup script automatically detects and cleans up existing processes:

```bash
# System will auto-detect and clean existing processes before starting
python start.py

# Manual cleanup if needed
python start.py cleanup

# Check system status without starting
python start.py check
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### How to Contribute
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For questions or issues:
1. Check the [WORKFLOW_DESIGN.md](WORKFLOW_DESIGN.md) for complete system documentation
2. Review the [Documentation Index](docs/DOCUMENTATION_INDEX.md) for detailed guides
3. Open an [Issue](https://github.com/[USERNAME]/SRR-Case-Processing-System/issues) for bug reports or feature requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- Built with FastAPI and React
- AI models powered by Transformers and scikit-learn
- OCR capabilities using EasyOCR and Tesseract
- Document processing with PyMuPDF and pdfplumber

---

**🎉 Ready to process your first case? Run `python start.py` and visit http://localhost:3000**
