# Digital Forensics Backend Scripts

Folder ini berisi semua script Python untuk menjalankan dan mengelola aplikasi Digital Forensics Backend.

## 📜 Daftar Scripts

### **Setup & Development**
<<<<<<< HEAD
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
=======
- **[start.sh](start.sh)** - Start development server
- **[restart.py](restart.py)** - Restart development server
- **[status.py](status.py)** - Check server status

### **Analysis Workflows**
- **[run_complete_workflow.py](run_complete_workflow.py)** - Run complete workflow (upload, device, analytic, correlation)
- **[run_complete_analysis.py](run_complete_analysis.py)** - Run complete analysis (for hash files)
- **[run_complete_analysis.sh](run_complete_analysis.sh)** - Bash script for complete analysis
- **[run_analytics_workflow.py](run_analytics_workflow.py)** - Python script for analytics workflow with API contract
- **[run_analytics_workflow.sh](run_analytics_workflow.sh)** - Bash script for analytics workflow with API contract

### **Utilities**
- **[clean.py](clean.py)** - Clean temporary files and directories
>>>>>>> analytics-fix

## 🚀 Cara Menggunakan

### **1. Quick Start (Recommended)**
```bash
<<<<<<< HEAD
# Setup project untuk pertama kali
python scripts/setup.py

# Development mode (quick start)
python scripts/dev.py

# Production mode (full validation)
python scripts/prod.py
=======
# Start the server
./scripts/start.sh
>>>>>>> analytics-fix
```

### **2. Development Workflow**
```bash
<<<<<<< HEAD
# Start development server
python scripts/start.py

# Stop development server
python scripts/stop.py

=======
>>>>>>> analytics-fix
# Restart development server
python scripts/restart.py

# Check server status
python scripts/status.py
```

<<<<<<< HEAD
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
=======
### **3. Analysis Workflows**
```bash
# Run complete workflow (Python)
python scripts/run_complete_workflow.py

# Run complete analysis (Python)
python scripts/run_complete_analysis.py

# Run complete analysis (Bash)
./scripts/run_complete_analysis.sh

# Run analytics workflow with API contract (Python)
python scripts/run_analytics_workflow.py

# Run analytics workflow with API contract (Bash)
./scripts/run_analytics_workflow.sh
```

### **4. Utilities**
```bash
# Clean files
python scripts/clean.py
>>>>>>> analytics-fix
```

## 📋 Deskripsi Scripts

### **Setup & Development Scripts**
<<<<<<< HEAD

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
=======
- **`start.sh`**: Script untuk memulai server pengembangan menggunakan `uvicorn`.
- **`restart.py`**: Script Python untuk menghentikan dan memulai ulang server pengembangan.
- **`status.py`**: Script Python untuk memeriksa status server pengembangan.

### **Analysis Workflow Scripts**
- **`run_complete_workflow.py`**: Script Python yang mengotomatiskan seluruh alur kerja dari unggah file, pembuatan perangkat, pembuatan analitik, hingga analisis korelasi kontak.
- **`run_complete_analysis.py`**: Script Python untuk menjalankan analisis lengkap, termasuk hash file.
- **`run_complete_analysis.sh`**: Script Bash yang mengotomatiskan seluruh alur kerja analisis, termasuk hash file.
- **`run_analytics_workflow.py`**: Script Python untuk workflow analytics dengan API contract yang lengkap, termasuk error handling dan logging.
- **`run_analytics_workflow.sh`**: Script Bash untuk workflow analytics dengan API contract yang lengkap, termasuk error handling dan logging.

### **Utility Scripts**
- **`clean.py`**: Script Python untuk membersihkan file dan direktori sementara yang dihasilkan selama pengembangan dan pengujian.
>>>>>>> analytics-fix

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
<<<<<<< HEAD
python scripts/setup.py
=======
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
>>>>>>> analytics-fix
```

### **Dependencies Error**
```bash
# Install dependencies
<<<<<<< HEAD
python scripts/install.py
=======
pip install -r requirements.txt
>>>>>>> analytics-fix
```

### **Database Error**
```bash
<<<<<<< HEAD
# Setup database
python scripts/setup_db.py
=======
# Check database connection
python -c "from app.database import engine; print('Database connected')"
>>>>>>> analytics-fix
```

## 📝 Notes

- Semua scripts menggunakan Python 3.11
- Database menggunakan PostgreSQL untuk production
- Analytics dependencies: pandas, numpy, python-magic
- System dependencies: libmagic, PostgreSQL
<<<<<<< HEAD
- Default admin: admin / admin123
=======
>>>>>>> analytics-fix
- API Documentation: http://localhost:8000/docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

---

<<<<<<< HEAD
**🎯 Python Scripts siap digunakan untuk mengelola Digital Forensics Backend!**
=======
**🎯 Python Scripts siap digunakan untuk mengelola Digital Forensics Backend!**
>>>>>>> analytics-fix
