# Digital Forensics Backend Scripts

Folder ini berisi semua script Python untuk menjalankan dan mengelola aplikasi Digital Forensics Backend.

## 📜 Daftar Scripts

### **Setup & Development**
- **[setup_new.py](setup_new.py)** - Setup project untuk development
- **[dev_new.py](dev_new.py)** - Run development server
- **[prod_new.py](prod_new.py)** - Run production server
- **[start_new.py](start_new.py)** - Start development server
- **[stop_new.py](stop_new.py)** - Stop development server
- **[restart_new.py](restart_new.py)** - Restart development server
- **[status_new.py](status_new.py)** - Check server status

### **Testing & Quality**
- **[run_tests_new.py](run_tests_new.py)** - Run all tests
- **[lint_new.py](lint_new.py)** - Run code linting
- **[format_new.py](format_new.py)** - Format code
- **[run_all_new.py](run_all_new.py)** - Run all development tasks

### **Database & Utilities**
- **[setup_db_new.py](setup_db_new.py)** - Setup database
- **[install_new.py](install_new.py)** - Install dependencies
- **[clean_new.py](clean_new.py)** - Clean files
- **[help_new.py](help_new.py)** - Show help information

## 🚀 Cara Menggunakan

### **1. Quick Start (Recommended)**
```bash
# Setup project untuk pertama kali
python scripts/setup.py

# Development mode (quick start)
python scripts/dev.py

# Production mode (full validation)
python scripts/prod.py
```

### **2. Development Workflow**
```bash
# Start development server
python scripts/start.py

# Stop development server
python scripts/stop.py

# Restart development server
python scripts/restart.py

# Check server status
python scripts/status.py
```

### **3. Testing & Quality**
```bash
# Run all tests
python scripts/run_tests.py

# Run code linting
python scripts/lint.py

# Format code
python scripts/format.py

# Run all development tasks
python scripts/run_all.py
```

### **4. Database & Utilities**
```bash
# Setup database
python scripts/setup_db.py

# Install dependencies
python scripts/install.py

# Clean files
python scripts/clean.py

# Show help
python scripts/help.py
```

## 📋 Deskripsi Scripts

### **Setup & Development Scripts**

#### **setup_new.py**
- Setup project untuk development
- Membuat virtual environment Python 3.11
- Install dependencies dari requirements.txt
- Setup environment variables
- Initialize database
- Membuat admin user default

#### **dev_new.py**
- Development mode untuk quick start
- Minimal checks untuk development
- Fast startup untuk development workflow
- Auto-reload untuk development

#### **prod_new.py**
- Production mode dengan full validation
- Security checks untuk production
- Comprehensive environment validation
- Database connection testing

#### **start_new.py**
- Start development server
- Cek virtual environment
- Install/update dependencies
- Menjalankan aplikasi dengan uvicorn

#### **stop_new.py**
- Stop development server
- Graceful shutdown
- Cleanup processes

#### **restart_new.py**
- Restart development server
- Stop dan start ulang server
- Refresh configuration

#### **status_new.py**
- Check server status
- Health check endpoint
- Process monitoring

### **Testing & Quality Scripts**

#### **run_tests_new.py**
- Run all tests
- Unit tests dan integration tests
- Test coverage reporting
- Test result summary

#### **lint_new.py**
- Run code linting
- Code quality checks
- Style validation
- Error detection

#### **format_new.py**
- Format code
- Auto-format Python code
- Consistent code style
- Black formatter integration

#### **run_all_new.py**
- Run all development tasks
- Format, lint, dan test
- Complete development workflow
- Quality assurance pipeline

### **Database & Utility Scripts**

#### **setup_db_new.py**
- Setup database
- Initialize database schema
- Create tables
- Setup database connection

#### **install_new.py**
- Install dependencies
- Update requirements
- Virtual environment management
- Dependency resolution

#### **clean_new.py**
- Clean files
- Remove temporary files
- Cache cleanup
- Log file management

#### **help_new.py**
- Show help information
- Script documentation
- Usage examples
- Command reference

## 🔧 Konfigurasi

Scripts menggunakan konfigurasi dari:
- `app/config.py` - Konfigurasi aplikasi
- `requirements.txt` - Dependencies Python
- `env.example` - Template environment variables
- `.env` - Environment variables (PostgreSQL, Analytics)

## 🐛 Troubleshooting

### **Script Not Found**
```bash
# Pastikan berada di root directory backend/
ls scripts/
```

### **Python Path Error**
```bash
# Pastikan menggunakan Python 3.11
python --version
python3.11 --version
```

### **Virtual Environment Error**
```bash
# Recreate virtual environment
rm -rf venv
python scripts/setup.py
```

### **Dependencies Error**
```bash
# Install dependencies
python scripts/install.py
```

### **Database Error**
```bash
# Setup database
python scripts/setup_db.py
```

## 📝 Notes

- Semua scripts menggunakan Python 3.11
- Database menggunakan PostgreSQL untuk production
- Analytics dependencies: pandas, numpy, python-magic
- System dependencies: libmagic, PostgreSQL
- Default admin: admin / admin123
- API Documentation: http://localhost:8000/docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

---

**🎯 Python Scripts siap digunakan untuk mengelola Digital Forensics Backend!**
