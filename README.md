# Forenlytic Backend (digifor)

Sistem backend untuk analisis forensik digital yang komprehensif.

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

## 🔧 API Endpoints

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

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

---

**🎉 Forenlytic Backend analisis forensik digital!**
