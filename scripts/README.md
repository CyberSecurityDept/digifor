# Digital Forensics Backend Scripts

Folder ini berisi semua script shell (.sh) untuk menjalankan dan mengelola aplikasi Digital Forensics Backend.

## 📜 Daftar Scripts

### **Quick Run Scripts**
- **[run.sh](run.sh)** - Full setup script (auto setup + run)
- **[run_dev.sh](run_dev.sh)** - Development mode (quick start)
- **[run_prod.sh](run_prod.sh)** - Production mode (full validation)

### **System Dependencies**
- **[install_system_deps.sh](install_system_deps.sh)** - Install system dependencies (libmagic)

### **Setup & Installation**
- **[setup.sh](setup.sh)** - Script setup lengkap untuk pertama kali
- **[start_backend.sh](start_backend.sh)** - Script lengkap untuk menjalankan aplikasi

### **Development & Testing**
- **[start.sh](start.sh)** - Script untuk menjalankan aplikasi (setelah setup)

## 🚀 Cara Menggunakan

### **1. Quick Start (Recommended)**
```bash
# Full setup (first time)
./scripts/run.sh

# Development mode (quick start)
./scripts/run_dev.sh

# Production mode (full validation)
./scripts/run_prod.sh
```

### **2. System Dependencies**
```bash
# Install system dependencies (required for analytics)
./scripts/install_system_deps.sh
```

### **3. Manual Setup (Legacy)**
```bash
# Setup aplikasi (pertama kali)
./scripts/setup.sh

# Script lengkap (setup + run)
./scripts/start_backend.sh

# Script simple (setelah setup)
./scripts/start.sh
```

### **4. Menjalankan dari Folder Scripts**
```bash
cd scripts
./run.sh
./run_dev.sh
./run_prod.sh
```

## 📋 Deskripsi Scripts

### **Quick Run Scripts**

#### **run.sh**
- Full setup script dengan PostgreSQL support
- Install system dependencies (libmagic)
- Setup environment variables
- Initialize PostgreSQL database
- Run application dengan comprehensive checks

#### **run_dev.sh**
- Development mode untuk quick start
- Minimal checks untuk development
- Fast startup untuk development workflow

#### **run_prod.sh**
- Production mode dengan full validation
- Security checks untuk production
- Comprehensive environment validation
- Database connection testing

#### **install_system_deps.sh**
- Install system dependencies (libmagic, PostgreSQL)
- Platform detection (Linux, macOS, Windows)
- Automatic dependency installation

### **Legacy Scripts**

#### **setup.sh**
- Membuat virtual environment Python 3.11
- Install dependencies dari requirements.txt
- Membuat direktori yang diperlukan
- Initialize database SQLite3 (legacy)
- Membuat admin user default
- Menampilkan informasi setup

#### **start_backend.sh**
- Script lengkap untuk menjalankan aplikasi
- Cek virtual environment
- Install/update dependencies
- Cek dan initialize database jika perlu
- Menjalankan aplikasi dengan auto-reload
- Menampilkan informasi akses

#### **start.sh**
- Script simple untuk menjalankan aplikasi
- Asumsi virtual environment sudah ada
- Asumsi database sudah diinitialize
- Menjalankan aplikasi dengan uvicorn

## 🔧 Konfigurasi

Scripts menggunakan konfigurasi dari:
- `app/config.py` - Konfigurasi aplikasi
- `requirements.txt` - Dependencies Python
- `env.example` - Template environment variables
- `.env` - Environment variables (PostgreSQL, Analytics)

## 🐛 Troubleshooting

### **Permission Denied**
```bash
chmod +x scripts/*.sh
```

### **Script Not Found**
```bash
# Pastikan berada di root directory backend/
ls scripts/
```

### **Virtual Environment Error**
```bash
# Recreate virtual environment
rm -rf venv
./scripts/setup.sh
```

## 📝 Notes

- Semua scripts menggunakan Python 3.11
- Database menggunakan PostgreSQL untuk production
- Analytics dependencies: pandas, numpy, python-magic
- System dependencies: libmagic, PostgreSQL
- Default admin: admin / admin123
- API Documentation: http://localhost:8000/docs

---

**🎯 Scripts siap digunakan untuk mengelola Digital Forensics Backend!**
