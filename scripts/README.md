# Digital Forensics Backend Scripts

Folder ini berisi semua script Python untuk menjalankan dan mengelola aplikasi Digital Forensics Backend.

## 📜 Daftar Scripts

### **Setup & Development**

- **[start.sh](start.sh)** - Start development server
- **[restart.py](restart.py)** - Restart development server
- **[status.py](status.py)** - Check server status

### **Analysis Workflows**

- **[run_complete_workflow.py](run_complete_workflow.py)** - Run complete workflow (upload, device, analytic, correlation)
- **[run_complete_analysis.py](run_complete_analysis.py)** - Run complete analysis (for hash files)
- **[run_complete_analysis.sh](run_complete_analysis.sh)** - Bash script for complete analysis
- **[run_analytics_workflow.py](run_analytics_workflow.py)** - Python script for analytics workflow with API contract
- **[run_analytics_workflow.sh](run_analytics_workflow.sh)** - Bash script for analytics workflow with API contract

### **Database Management**

- **[check-db-connection.py](check-db-connection.py)** - Test koneksi database
- **[verify-db-connection.py](verify-db-connection.py)** - Verifikasi lengkap koneksi dan tabel
- **[list-tables.py](list-tables.py)** - List semua tabel dengan detail
- **[init-database.py](init-database.py)** - Initialize database (membuat tabel jika belum ada)

### **Utilities**

- **[clean.py](clean.py)** - Clean temporary files and directories

## Cara Menggunakan

### **1. Quick Start (Recommended)**

```bash
# Start the server
./scripts/start.sh
```

### **2. Development Workflow**

```bash
# Restart development server
python scripts/restart.py

# Check server status
python scripts/status.py
```

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

### **4. Database Management**

```bash
# Test database connection
python3 scripts/check-db-connection.py

# Verify database connection and tables
python3 scripts/verify-db-connection.py

# List all tables
python3 scripts/list-tables.py

# Initialize database (create tables)
python3 scripts/init-database.py
```

### **5. Utilities**

```bash
# Clean files
python scripts/clean.py
```

## Deskripsi Scripts

### **Setup & Development Scripts**

- **`start.sh`**: Script untuk memulai server pengembangan menggunakan `uvicorn`.
- **`restart.py`**: Script Python untuk menghentikan dan memulai ulang server pengembangan.
- **`status.py`**: Script Python untuk memeriksa status server pengembangan.

### **Analysis Workflow Scripts**

- **`run_complete_workflow.py`**: Script Python yang mengotomatiskan seluruh alur kerja dari unggah file, pembuatan perangkat, pembuatan analitik, hingga analisis korelasi kontak.
- **`run_complete_analysis.py`**: Script Python untuk menjalankan analisis lengkap, termasuk hash file.
- **`run_complete_analysis.sh`**: Script Bash yang mengotomatiskan seluruh alur kerja analisis, termasuk hash file.
- **`run_analytics_workflow.py`**: Script Python untuk workflow analytics dengan API contract yang lengkap, termasuk error handling dan logging.
- **`run_analytics_workflow.sh`**: Script Bash untuk workflow analytics dengan API contract yang lengkap, termasuk error handling dan logging.

### **Database Management Scripts**

- **`check-db-connection.py`**: Script untuk test koneksi database sebelum service start. Digunakan oleh systemd service.
- **`verify-db-connection.py`**: Script untuk verifikasi lengkap koneksi database, menampilkan semua tabel, permissions, dan informasi server.
- **`list-tables.py`**: Script untuk menampilkan semua tabel di database beserta jumlah kolom dan baris.
- **`init-database.py`**: Script untuk initialize database - membuat semua tabel jika belum ada. Digunakan oleh systemd service.

### **Utility Scripts**

- **`clean.py`**: Script Python untuk membersihkan file dan direktori sementara yang dihasilkan selama pengembangan dan pengujian.

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
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Dependencies Error**

```bash
# Install dependencies
pip install -r requirements.txt
```

### **Database Error**

```bash
# Check database connection
python -c "from app.database import engine; print('Database connected')"
```

## 📝 Notes

- Semua scripts menggunakan Python 3.11
- Database menggunakan PostgreSQL untuk production
- Analytics dependencies: pandas, numpy, python-magic
- System dependencies: libmagic, PostgreSQL
- API Documentation: http://172.15.2.105/docs
- Swagger UI: http://172.15.2.105/docs
- ReDoc: http://172.15.2.105/redoc
- Health Check: http://172.15.2.105/health

---

**🎯 Python Scripts siap digunakan untuk mengelola Digital Forensics Backend!**
