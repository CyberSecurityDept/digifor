# Forenlytic Backend (digifor)

Sistem backend untuk analisis forensik digital yang komprehensif.

Platform analisis forensik digital dengan kemampuan big data analytics, case management, dan report generation.

## 📋 Requirements

**Python Version:** 3.11+  
**Main Dependencies:**
- FastAPI 0.104.1
- Uvicorn 0.24.0
- SQLAlchemy 2.0.23
- Pydantic 2.5.0

Lihat [requirements.txt](requirements.txt) untuk daftar lengkap dependencies.

## 🚀 Installation & Setup

### 📥 Clone Repository

```bash
# Clone repository
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend
```

### 🖥️ Platform-Specific Installation

#### **Linux (Ubuntu/Debian)**

```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and pip
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Install system dependencies
sudo apt install build-essential libssl-dev libffi-dev -y

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env file if needed
nano .env

# Initialize database
python tools/init_db.py

# Run application
python tools/run_dev.py
```

#### **macOS**

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env file if needed
nano .env

# Initialize database
python tools/init_db.py

# Run application
python tools/run_dev.py
```

#### **Windows (PowerShell)**

```powershell
# Install Python 3.11+ from python.org
# Then open PowerShell as Administrator

# Create virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Setup environment
copy .env.example .env
# Edit .env file if needed
notepad .env

# Initialize database
python tools/init_db.py

# Run application
python tools/run_dev.py
```

#### **Windows (Command Prompt)**

```cmd
# Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Setup environment
copy .env.example .env
# Edit .env file if needed
notepad .env

# Initialize database
python tools/init_db.py

# Run application
python tools/run_dev.py
```

### 🚀 Quick Start (All Platforms)

```bash
# Cara termudah - auto setup dan run
./run.sh

# Atau manual step by step
./scripts/setup.sh
./scripts/start.sh

# Atau script lengkap
./scripts/start_backend.sh
```

### 🔧 Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional)
nano .env  # Linux/macOS
notepad .env  # Windows
```

**Environment Variables:**
```env
# Database
DATABASE_URL=sqlite:///./data/forenlytic.db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API
API_V1_STR=/api/v1
PROJECT_NAME=Forenlytic Backend

# Development
DEBUG=True
LOG_LEVEL=INFO
```

### 🛠️ Troubleshooting

#### **Common Issues & Solutions**

**1. Python Version Issues**
```bash
# Check Python version
python --version
python3 --version

# If Python 3.11+ not found, install it:
# Ubuntu/Debian:
sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS:
brew install python@3.11

# Windows: Download from python.org
```

**2. Virtual Environment Issues**
```bash
# Linux/macOS - Permission denied
chmod +x venv/bin/activate
source venv/bin/activate

# Windows - Execution Policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**3. Dependencies Installation Issues**
```bash
# Update pip first
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Install specific problematic package
pip install --no-cache-dir package-name
```

**4. Database Issues**
```bash
# Remove existing database and recreate
rm -f data/forenlytic.db
python tools/init_db.py

# Check database file permissions
ls -la data/
```

**5. Port Already in Use**
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process using port 8000
kill -9 $(lsof -t -i:8000)  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### 📋 Verification Steps

After installation, verify everything works:

```bash
# 1. Check Python version
python --version

# 2. Check virtual environment
which python  # Should point to venv/bin/python

# 3. Check dependencies
pip list

# 4. Test database connection
python -c "from app.database import engine; print('Database OK')"

# 5. Run health check
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

### 🎯 First Run Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment file copied (`cp .env.example .env`)
- [ ] Database initialized (`python tools/init_db.py`)
- [ ] Application started (`python tools/run_dev.py`)
- [ ] API accessible at `http://localhost:8000`
- [ ] Health check passes (`http://localhost:8000/health`)

### 🐳 Docker Installation (Alternative)

If you prefer Docker, you can use the following commands:

```bash
# Build Docker image
docker build -t forenlytic-backend .

# Run with Docker Compose (if available)
docker-compose up -d

# Or run directly
docker run -p 8000:8000 -v $(pwd)/data:/app/data forenlytic-backend
```

**Docker Requirements:**
- Docker 20.10+
- Docker Compose 2.0+ (optional)

### 👨‍💻 Development Setup

For developers who want to contribute or customize:

```bash
# 1. Clone and setup
git clone https://github.com/your-username/forenlytic-backend.git
cd forenlytic-backend

# 2. Create development environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. Install development dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available

# 4. Setup pre-commit hooks (optional)
pre-commit install

# 5. Configure environment
cp .env.example .env
# Edit .env for development settings

# 6. Initialize development database
python tools/init_db.py
python tools/create_admin.py  # Create admin user

# 7. Run in development mode
python tools/run_dev.py
# Or use uvicorn directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Development Environment Variables:**
```env
# Development settings
DEBUG=True
LOG_LEVEL=DEBUG
RELOAD=True

# Database (development)
DATABASE_URL=sqlite:///./data/forenlytic_dev.db

# Security (development - use different keys in production)
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
```

### 🔧 Advanced Configuration

**Custom Database Setup:**
```bash
# PostgreSQL (production)
pip install psycopg2-binary
# Update DATABASE_URL in .env:
# DATABASE_URL=postgresql://user:password@localhost/forenlytic

# MySQL (production)
pip install PyMySQL
# Update DATABASE_URL in .env:
# DATABASE_URL=mysql+pymysql://user:password@localhost/forenlytic
```

**Production Deployment:**
```bash
# Use production environment
cp env.production .env

# Install production dependencies
pip install -r requirements.txt

# Run with production settings
python tools/run.py
```

## 📖 Documentation

Semua dokumentasi tersedia di folder `docs/`:

- **[Quick Start Guide](docs/QUICK_START.md)** - Panduan cepat untuk memulai
- **[Usage Guide](docs/USAGE.md)** - Panduan penggunaan lengkap
- **[Implementation Details](docs/IMPLEMENTATION.md)** - Detail implementasi
- **[Final Summary](docs/FINAL_SUMMARY.md)** - Ringkasan lengkap fitur

## 🏗️ System Architecture

Arsitektur sistem Forenlytic Backend menggunakan FastAPI dengan SQLite database untuk analisis forensik digital.

## 🔧 API Endpoints

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 📋 Complete API Documentation
Lihat **[API Documentation](docs/api-forensix-analytics.md)** untuk dokumentasi lengkap semua endpoints.

### 🧪 Postman Testing

**Base URL:** `http://localhost:8000`

**Authentication Endpoints:**
- `POST /api/v1/auth/token` - Login
- `GET /api/v1/auth/me` - Get user profile
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

**Case Management Endpoints:**
- `GET /api/v1/cases/` - Get all cases
- `POST /api/v1/cases/` - Create new case
- `GET /api/v1/cases/{case_id}` - Get case by ID

**Report Generation Endpoints:**
- `POST /api/v1/reports/generate` - Generate case report
- `GET /api/v1/reports/{report_id}` - Get report by ID

**Default Test Credentials:**
```
Username: test
Password: test123
```

## 🛡️ Security & Technology Stack

**Teknologi yang digunakan:**
- **Backend**: Python 3.11+, FastAPI 0.104.1, Uvicorn 0.24.0
- **Database**: SQLite dengan SQLAlchemy 2.0.23
- **Authentication**: JWT (JSON Web Tokens) dengan python-jose 3.3.0
- **Security**: Data encryption, secure API endpoints
- **HTTP Client**: httpx 0.25.2, requests 2.31.0
- **Testing**: pytest 7.4.3, pytest-asyncio 0.21.1
- **Logging**: loguru 0.7.2


## ⚙️ Environment Configuration

File `.env` sudah dikonfigurasi untuk development. Lihat **[docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)** untuk detail konfigurasi.

### **Environment Files**
- **.env** - Development (default)
- **env.production** - Production template
- **env.test** - Testing template
- **env.example** - Template untuk custom configuration

## 🔬 Digital Forensics Process

Platform ini mendukung proses forensik digital yang lengkap:

1. **Evidence Acquisition** - Pengumpulan bukti digital
2. **Analysis** - Analisis data forensik
3. **Correlation** - Korelasi data dan kontak
4. **Reporting** - Generasi laporan forensik

**Fitur Analisis:**
- Hash Analysis - Analisis hash file
- Contact Correlation - Korelasi kontak dan komunikasi
- Timeline Analysis - Analisis timeline kejadian

## 🧪 Testing

### **Automated Testing**
```bash
# Run all tests
python tests/run_tests.py

# Run specific test
python tests/test_api.py
python tests/test_auth.py
python tests/test_cases.py
python tests/test_reports.py
```

### **Manual Testing**
```bash
# Quick API test
./quick_test.sh

# Detailed manual test
./test_api_manual.sh
```

### **API Documentation**
- **[API Manual](docs/API_MANUAL.md)** - Complete API testing guide
- **[cURL Examples](docs/CURL_EXAMPLES.md)** - Ready-to-use cURL commands
- **[Complete API Reference](docs/api-forensix-analytics.md)** - Detailed API documentation

### **Postman Collection Setup**

1. **Import Collection:**
   - Download atau copy API endpoints dari dokumentasi
   - Import ke Postman dengan Base URL: `http://localhost:8000`

2. **Environment Variables:**
   ```
   base_url: http://localhost:8000
   access_token: {{access_token}}
   refresh_token: {{refresh_token}}
   ```

3. **Testing Workflow:**
   ```
   1. POST /api/v1/auth/token (Login)
   2. Set access_token dari response
   3. Test protected endpoints dengan Bearer token
   ```

4. **Sample Request Body (Login):**
   ```json
   {
     "username": "test",
     "password": "TesPassword123"
   }
   ```

## 📜 Scripts

### **Quick Run**
- **[run.sh](run.sh)** - Script termudah (auto setup + run)

### **Manual Scripts**
Semua script shell tersedia di folder `scripts/`:

- **[scripts/README.md](scripts/README.md)** - Dokumentasi scripts
- **[scripts/setup.sh](scripts/setup.sh)** - Setup aplikasi
- **[scripts/start_backend.sh](scripts/start_backend.sh)** - Jalankan aplikasi lengkap
- **[scripts/start.sh](scripts/start.sh)** - Jalankan aplikasi simple

## 🛠️ Tools

Python tools dan utilities tersedia di folder `tools/`:

- **[tools/README.md](tools/README.md)** - Dokumentasi tools
- **[tools/init_db.py](tools/init_db.py)** - Initialize database
- **[tools/create_admin.py](tools/create_admin.py)** - Create admin user
- **[tools/run.py](tools/run.py)** - Production runner
- **[tools/run_dev.py](tools/run_dev.py)** - Development runner

## 🎯 Features

- ✅ **Case Management** - Manajemen kasus forensik
- ✅ **Evidence Management** - Manajemen bukti digital  
- ✅ **Big Data Analytics** - Analisis data forensik
- ✅ **Report Generation** - Generasi laporan
- ✅ **Authentication** - Sistem autentikasi JWT
- ✅ **API Documentation** - Dokumentasi API lengkap

**Workflow Forensik:**
- Evidence Collection → Analysis → Reporting

## 🚀 Deployment & Monitoring

**Production Deployment:**
- Health monitoring
- Log analysis
- Real-time analytics
- Automated reporting

**Data Pipeline:**
- Forensic data processing
- Real-time analytics
- Automated report generation

---

**🎉 Forenlytic Backend analisis forensik digital!**