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

## 🚀 Quick Start

```bash
# Cara termudah - auto setup dan run
./run.sh

# Atau manual step by step
./scripts/setup.sh
./scripts/start.sh

# Atau script lengkap
./scripts/start_backend.sh
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