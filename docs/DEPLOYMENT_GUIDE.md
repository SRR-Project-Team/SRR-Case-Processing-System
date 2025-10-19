# Deployment Guide

## 🚀 SRR Case Processing System Deployment

This guide provides step-by-step instructions for deploying the SRR Case Processing System in production environments.

## 📋 Prerequisites

### System Requirements
- **Operating System:** Linux (Ubuntu 20.04+ recommended) or Windows 10+
- **Python:** Version 3.8 or higher
- **Node.js:** Version 16 or higher
- **Memory:** Minimum 4GB RAM (8GB recommended)
- **Storage:** 10GB free space for dependencies and temporary files
- **Network:** Internet access for package installation

### Required Software
- Git (for repository cloning)
- Python pip (package manager)
- Node.js npm (package manager)
- PM2 (process manager, optional but recommended)

## 🛠️ Installation Steps

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd project3
```

### Step 2: Backend Setup

#### 2.1 Create Virtual Environment
```bash
python -m venv venv

# On Linux/Mac
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

#### 2.2 Install Python Dependencies
```bash
pip install -r config/requirements.txt
pip install -r config/requirements_ocr.txt
```

#### 2.3 Verify Installation
```bash
python -c "import easyocr, transformers, sklearn; print('All dependencies installed successfully')"
```

### Step 3: Frontend Setup

#### 3.1 Install Node.js Dependencies
```bash
cd frontend/srr-chatbot
npm install
```

#### 3.2 Build Production Version
```bash
npm run build
```

### Step 4: Data Setup

#### 4.1 Verify Data Files
Ensure the following files exist in `data/depend_data/`:
- `Slope data.xlsx`
- `Slopes Complaints & Enquires Under TC K928 4-10-2021.xlsx`
- `SRR data 2021-2024.csv`
- `SRR rules.docx`

#### 4.2 Set Permissions
```bash
chmod 644 data/depend_data/*
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=false

# Frontend Configuration
FRONTEND_PORT=3000
REACT_APP_API_URL=http://localhost:8000

# Processing Configuration
MAX_FILE_SIZE=52428800  # 50MB
MAX_BATCH_SIZE=10
OCR_TIMEOUT=120
MODEL_CACHE_TIMEOUT=1800

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Production Settings

For production deployment, update the following:

```bash
# Production API URL
REACT_APP_API_URL=https://your-domain.com/api

# Security
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]

# Performance
WORKERS=4
MAX_REQUESTS=1000
```

## 🚀 Deployment Options

### Option 1: Development Deployment

#### Start Backend
```bash
cd src/api
python main.py
```

#### Start Frontend (separate terminal)
```bash
cd frontend/srr-chatbot
npm start
```

### Option 2: Production Deployment with PM2

#### 2.1 Install PM2
```bash
npm install -g pm2
```

#### 2.2 Create PM2 Configuration

Create `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [
    {
      name: 'srr-api',
      script: 'src/api/main.py',
      interpreter: 'python',
      cwd: '/path/to/project3',
      env: {
        NODE_ENV: 'production',
        API_PORT: 8000
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '2G'
    },
    {
      name: 'srr-frontend',
      script: 'serve',
      args: '-s build -l 3000',
      cwd: '/path/to/project3/frontend/srr-chatbot',
      env: {
        NODE_ENV: 'production'
      },
      instances: 1,
      exec_mode: 'fork'
    }
  ]
};
```

#### 2.3 Start Services
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Option 3: Docker Deployment

#### 3.1 Create Dockerfile for Backend
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY config/requirements*.txt ./
RUN pip install -r requirements.txt && \
    pip install -r requirements_ocr.txt

COPY src/ ./src/
COPY data/ ./data/

EXPOSE 8000

CMD ["python", "src/api/main.py"]
```

#### 3.2 Create Dockerfile for Frontend
```dockerfile
FROM node:16-alpine as build

WORKDIR /app
COPY frontend/srr-chatbot/package*.json ./
RUN npm install

COPY frontend/srr-chatbot/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 3.3 Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8001

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://localhost:8000
```

## 🔒 Security Configuration

### SSL/HTTPS Setup

#### Using Nginx Reverse Proxy
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Firewall Configuration
```bash
# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow SSH (if needed)
sudo ufw allow 22

# Enable firewall
sudo ufw enable
```

## 📊 Monitoring and Logging

### Log Configuration

Create log directory:
```bash
mkdir -p logs
chmod 755 logs
```

### Health Monitoring

#### System Health Check
```bash
# Check API health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000
```

#### PM2 Monitoring
```bash
# View process status
pm2 status

# View logs
pm2 logs

# Monitor resources
pm2 monit
```

### Log Rotation

Create `/etc/logrotate.d/srr-system`:
```
/path/to/project3/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
}
```

## 🔧 Maintenance

### Regular Tasks

#### Daily
- Check system health and logs
- Monitor disk space usage
- Verify API response times

#### Weekly
- Update system packages
- Review error logs
- Check model performance metrics

#### Monthly
- Update Python/Node.js dependencies
- Review and archive old logs
- Performance optimization review

### Backup Strategy

#### Data Backup
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Backup to remote location
rsync -av data/ user@backup-server:/backups/srr-data/
```

#### Configuration Backup
```bash
# Backup configuration files
cp .env .env.backup
cp ecosystem.config.js ecosystem.config.js.backup
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Python Dependencies Error
```bash
# Reinstall dependencies
pip install --upgrade -r config/requirements.txt
```

#### 2. OCR Processing Fails
```bash
# Check EasyOCR installation
python -c "import easyocr; print('EasyOCR working')"

# Reinstall OCR dependencies
pip install --upgrade easyocr
```

#### 3. Frontend Build Fails
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### 4. High Memory Usage
```bash
# Monitor memory usage
htop

# Restart services
pm2 restart all
```

### Performance Optimization

#### Backend Optimization
- Increase worker processes for high load
- Implement Redis caching for AI models
- Use load balancer for multiple instances

#### Frontend Optimization
- Enable gzip compression
- Use CDN for static assets
- Implement service worker for caching

## 📞 Support

### Getting Help
- Check logs in `logs/` directory
- Review error messages in PM2 logs
- Monitor system resources with `htop`
- Check API health endpoint

### Contact Information
For deployment issues or questions, contact the development team with:
- Error logs
- System configuration details
- Steps to reproduce the issue

---

**Last Updated**: 2025-10-19  
**Version**: 1.0

This deployment guide covers the essential steps for getting the SRR Case Processing System running in production. Follow the security and monitoring recommendations for a robust deployment.
