# Backend (digifor)

Forensik digital memainkan peran penting dalam penyelidikan di berbagai konteks seperti penegakan hukum, pemerintahan, keamanan korporasi, dan ranah hukum. Platform ini hadir untuk menjawab tantangan tersebut dengan menyediakan solusi yang komprehensif, aman, dan terintegrasi untuk mengelola kasus forensik digital, barang bukti, rantai penguasaan (chain of custody), analitik lanjutan, serta pelaporan.

## 📋 Requirements

**Python Version:** 3.11+  
**Main Dependencies:**
- FastAPI 0.104.1
- Uvicorn 0.24.0
- SQLAlchemy 2.0.23
- PostgreSQL (psycopg2-binary 2.9.9)
- Analytics (pandas 2.1.4, numpy 1.24.3, python-magic 0.4.27)

## 🚀 Quick Start

### **All Platforms (Recommended)**
```bash
# Cara termudah - auto setup dan run
./scripts/run.sh

# Development mode (quick start)
./scripts/run_dev.sh

# Production mode
./scripts/run_prod.sh
```

### **Manual Setup**
```bash
# 1. Clone repository
git clone https://github.com/CyberSecurityDept/digifor.git
cd digifor

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env file with your PostgreSQL credentials

# 5. Initialize database
python tools/setup_postgres.py

# 6. Run application
python tools/run_dev.py
```

### **System Dependencies (Required)**
```bash
# Linux (Ubuntu/Debian)
sudo apt install libmagic1-dev postgresql postgresql-contrib

# macOS
brew install libmagic postgresql

# Windows
# Download PostgreSQL from postgresql.org
# Install libmagic via conda: conda install libmagic
```

## 🔧 Environment Configuration

```env
# Database (PostgreSQL)
DATABASE_URL=postgresql://Digital Forensics:password@localhost:5432/Digital Forensics_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=Digital Forensics
POSTGRES_PASSWORD=password
POSTGRES_DB=Digital Forensics_db

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_V1_STR=/api/v1
PROJECT_NAME=Digital Forensics Backend
DEBUG=True
```

## 🔧 API Endpoints

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### **Authentication Endpoints:**
- `POST /api/v1/auth/oauth2/token` - Login
- `GET /api/v1/auth/me` - Get user profile
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout-all` - Logout

### **Case Management Endpoints:**
- `GET /api/v1/cases/overview` - Dashboard statistics
- `GET /api/v1/cases/get-all-cases/` - Get all cases
- `POST /api/v1/cases/create-cases/` - Create new case
- `GET /api/v1/cases/{case_id}/detail` - Get case details
- `PUT /api/v1/cases/update-case/{case_id}` - Update case

### **Default Test Credentials:**
```
Username: username
Password: password
```

## 🛡️ Security & Technology Stack

### **Core Technologies**
- **Backend Framework**: Python 3.11+, FastAPI 0.104.1, Uvicorn 0.24.0
- **Database**: PostgreSQL dengan SQLAlchemy 2.0.23
- **Authentication**: JWT (JSON Web Tokens) dengan python-jose 3.3.0
- **Analytics**: pandas 2.1.4, numpy 1.24.3, python-magic 0.4.27

### **Forensic Security Features**
- **Data Encryption**: AES-256 encryption untuk data sensitif
- **Chain of Custody**: Pelacakan lengkap dengan cryptographic signatures
- **Audit Logging**: Log komprehensif semua aktivitas dan akses
- **Role-based Access Control**: Kontrol akses granular berdasarkan peran
- **Hash Verification**: MD5, SHA-1, SHA-256 untuk integritas data

## 🎯 Features

### **Core Forensic Capabilities**
- ✅ **Case Management** - Manajemen kasus forensik dengan tracking lengkap
- ✅ **Evidence Management** - Manajemen bukti digital dengan chain of custody
- ✅ **Chain of Custody** - Pelacakan perpindahan dan akses barang bukti
- ✅ **Digital Evidence Analysis** - Analisis mendalam bukti digital
- ✅ **Hash Verification** - Verifikasi integritas file dan data

### **Analytics & Intelligence**
- ✅ **Advanced Analytics** - Analisis data forensik dengan AI/ML
- ✅ **Pattern Recognition** - Deteksi pola dan anomali
- ✅ **Data Correlation** - Korelasi data dari berbagai sumber
- ✅ **Contact Analysis** - Analisis komunikasi dan kontak

### **Reporting & Compliance**
- ✅ **Standardized Reports** - Laporan sesuai standar hukum
- ✅ **Audit Trail** - Log lengkap semua aktivitas
- ✅ **Legal Documentation** - Dokumentasi yang dapat diterima di pengadilan
- ✅ **Export Capabilities** - Ekspor data dalam berbagai format

## 🧪 Testing

```bash
# Run all tests
python tests/run_tests.py

# Run specific test
python tests/test_api.py
python tests/test_auth.py
python tests/test_cases.py
python tests/test_reports.py
```

## 📖 Documentation

Semua dokumentasi tersedia di folder `docs/`:

- **[Quick Start Guide](docs/QUICK_START.md)** - Panduan cepat untuk memulai
- **[Complete Environment Guide](docs/COMPLETE_ENVIRONMENT_GUIDE.md)** - Panduan lengkap konfigurasi environment
- **[cURL Examples](docs/CURL_EXAMPLES.md)** - Ready-to-use cURL commands
- **[Authentication API](docs/AUTHENTICATION_API_DOCUMENTATION.md)** - Authentication endpoints documentation
- **[Case Management API](docs/CASE_MANAGEMENT_API_DOCUMENTATION.md)** - Case management endpoints documentation
- **[Frontend Endpoints Summary](docs/FRONTEND_ENDPOINTS_SUMMARY.md)** - Quick reference for frontend developers

## 🛠️ Troubleshooting

### **Common Issues & Solutions**

**1. Python Version Issues**
```bash
# Check Python version
python --version

# If Python 3.11+ not found, install it:
# Ubuntu/Debian: sudo apt install python3.11 python3.11-venv python3.11-dev
# macOS: brew install python@3.11
# Windows: Download from python.org
```

**2. Database Issues**
```bash
# Check environment variables
python tools/check_env.py

# For PostgreSQL setup
python tools/setup_postgres.py

# Test PostgreSQL connection
python -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5432, user='Digital Forensics', password='password', database='Digital Forensics_db'); print('PostgreSQL OK')"
```

**3. Port Already in Use**
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process using port 8000
kill -9 $(lsof -t -i:8000)  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

## 📜 Scripts

### **Quick Run Scripts**
- **[scripts/run.sh](scripts/run.sh)** - Full setup script (auto setup + run)
- **[scripts/run_dev.sh](scripts/run_dev.sh)** - Development mode (quick start)
- **[scripts/run_prod.sh](scripts/run_prod.sh)** - Production mode (full validation)

### **System Dependencies**
- **[scripts/install_system_deps.sh](scripts/install_system_deps.sh)** - Install system dependencies (libmagic)

## 🛠️ Tools

Python tools dan utilities tersedia di folder `tools/`:

- **[tools/setup_postgres.py](tools/setup_postgres.py)** - PostgreSQL setup script
- **[tools/check_env.py](tools/check_env.py)** - Environment variables checker
- **[tools/create_admin.py](tools/create_admin.py)** - Create admin user
- **[tools/run_dev.py](tools/run_dev.py)** - Development runner

## 🎯 First Run Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment file copied (`cp .env.example .env`)
- [ ] Database initialized (`python tools/setup_postgres.py`)
- [ ] Application started (`python tools/run_dev.py`)
- [ ] API accessible at `http://localhost:8000`
- [ ] Health check passes (`http://localhost:8000/health`)

---

**🔍 Digifor Backend - Digital Forensik**