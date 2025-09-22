# Forenlytic Backend (digifor)

<div align="center">
  <img src="https://img.shields.io/badge/Forensic-Digital%20Analytics-blue?style=for-the-badge&logo=shield" alt="Forensic Digital Analytics">
  <img src="https://img.shields.io/badge/Python-FastAPI-green?style=for-the-badge&logo=python" alt="Python FastAPI">
  <img src="https://img.shields.io/badge/Database-SQLite-orange?style=for-the-badge&logo=sqlite" alt="SQLite Database">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
</div>

<div align="center">
  <h3>🔍 Sistem backend untuk analisis forensik digital yang komprehensif</h3>
  <p>Platform analisis forensik digital dengan kemampuan big data analytics, case management, dan report generation</p>
</div>

---

<div align="center">
  <img src="https://via.placeholder.com/800x400/1e3a8a/ffffff?text=Forensic+Digital+Analytics+Platform" alt="Forensic Analytics Platform" width="800" height="400">
  <p><em>Platform analisis forensik digital untuk investigasi cybercrime</em></p>
</div>

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

<div align="center">
  <img src="https://via.placeholder.com/800x500/1e40af/ffffff?text=Forensic+Analytics+Architecture" alt="System Architecture" width="800" height="500">
  <p><em>Arsitektur sistem Forenlytic Backend</em></p>
</div>

## 🔧 API Endpoints

<div align="center">
  <img src="https://via.placeholder.com/600x200/0891b2/ffffff?text=API+Documentation+%7C+ReDoc+%7C+Health+Check" alt="API Endpoints" width="600" height="200">
</div>

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🛡️ Security & Technology Stack

<div align="center">
  <img src="https://via.placeholder.com/800x300/dc2626/ffffff?text=JWT+Authentication+%7C+Data+Encryption+%7C+Secure+API" alt="Security Features" width="800" height="300">
</div>

<div align="center">
  <img src="https://via.placeholder.com/900x200/1f2937/ffffff?text=Python+%7C+FastAPI+%7C+SQLite+%7C+JWT+%7C+Uvicorn" alt="Technology Stack" width="900" height="200">
</div>

## 🔐 Default Credentials

- **Username**: admin
- **Password**: admin123

## ⚙️ Environment Configuration

File `.env` sudah dikonfigurasi untuk development. Lihat **[docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)** untuk detail konfigurasi.

### **Environment Files**
- **.env** - Development (default)
- **env.production** - Production template
- **env.test** - Testing template
- **env.example** - Template untuk custom configuration

## 🔬 Digital Forensics Process

<div align="center">
  <img src="https://via.placeholder.com/900x300/be123c/ffffff?text=Evidence+Acquisition+%7C+Analysis+%7C+Correlation+%7C+Reporting" alt="Digital Forensics Process" width="900" height="300">
</div>

<div align="center">
  <img src="https://via.placeholder.com/800x400/0f766e/ffffff?text=Hash+Analysis+%7C+Contact+Correlation+%7C+Timeline+Analysis" alt="Forensic Analytics" width="800" height="400">
</div>

## 🧪 Testing

<div align="center">
  <img src="https://via.placeholder.com/600x150/7c2d12/ffffff?text=Automated+Testing+%7C+Manual+Testing+%7C+API+Testing" alt="Testing Framework" width="600" height="150">
</div>

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

<div align="center">
  <img src="https://via.placeholder.com/600x300/059669/ffffff?text=Digital+Forensics+Workflow" alt="Digital Forensics Workflow" width="600" height="300">
</div>

- ✅ **Case Management** - Manajemen kasus forensik
- ✅ **Evidence Management** - Manajemen bukti digital  
- ✅ **Big Data Analytics** - Analisis data forensik
- ✅ **Report Generation** - Generasi laporan
- ✅ **Authentication** - Sistem autentikasi JWT
- ✅ **API Documentation** - Dokumentasi API lengkap

<div align="center">
  <img src="https://via.placeholder.com/700x200/7c3aed/ffffff?text=Evidence+Collection+%7C+Analysis+%7C+Reporting" alt="Forensic Process" width="700" height="200">
</div>

## 🚀 Deployment & Monitoring

<div align="center">
  <img src="https://via.placeholder.com/800x300/059669/ffffff?text=Production+Deployment+%7C+Health+Monitoring+%7C+Log+Analysis" alt="Deployment & Monitoring" width="800" height="300">
</div>

<div align="center">
  <img src="https://via.placeholder.com/700x200/7c3aed/ffffff?text=Forensic+Data+Pipeline+%7C+Real-time+Analytics+%7C+Automated+Reporting" alt="Data Pipeline" width="700" height="200">
</div>

---

<div align="center">
  <img src="https://via.placeholder.com/600x100/1e40af/ffffff?text=🎉+Forenlytic+Backend+Digital+Forensics+Analytics+Platform+🎉" alt="Forenlytic Platform" width="600" height="100">
</div>

**🎉 Forenlytic Backend analisis forensik digital!**
