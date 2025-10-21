# 📚 FORENLYTIC ANALYTICS - DOCUMENTATION INDEX

## 🎯 **OVERVIEW**

Sistem Forenlytic Analytics adalah platform analisis forensik digital yang memungkinkan analisis komprehensif data perangkat, hashfile, kontak, media sosial, dan komunikasi untuk keperluan investigasi forensik.

---

## 📋 **DOCUMENTATION FILES**

### **📊 API Documentation**
- **[ANALYTICS_API_CONTRACT.md](ANALYTICS_API_CONTRACT.md)** - Kontrak API dan schema lengkap
- **[ANALYTICS_API_EXAMPLES.md](ANALYTICS_API_EXAMPLES.md)** - Contoh penggunaan API
- **[COMPLETE_API_WORKFLOW_GUIDE.md](COMPLETE_API_WORKFLOW_GUIDE.md)** - Panduan lengkap workflow API
- **[CASE_MANAGEMENT_API_DOCUMENTATION.md](CASE_MANAGEMENT_API_DOCUMENTATION.md)** - Dokumentasi API case management

### **🛠️ Tools & Scripts**
- **[scripts/run_complete_analysis.sh](../scripts/run_complete_analysis.sh)** - Script bash untuk analisis otomatis
- **[scripts/run_complete_analysis.py](../scripts/run_complete_analysis.py)** - Script Python untuk analisis otomatis
- **[scripts/run_analytics_workflow.py](../scripts/run_analytics_workflow.py)** - Script Python untuk workflow analytics
- **[scripts/run_analytics_workflow.sh](../scripts/run_analytics_workflow.sh)** - Script bash untuk workflow analytics

### **📱 Postman Collections**
- **[Forenlytic_Analytics_API.postman_collection.json](Forenlytic_Analytics_API.postman_collection.json)** - Collection Postman untuk Analytics API
- **[Forenlytic_Analytics_Environment.postman_environment.json](Forenlytic_Analytics_Environment.postman_environment.json)** - Environment Postman

---

## 🚀 **QUICK START**

### **1. Setup Environment**
```bash
# Clone repository
git clone <repository-url>
cd backend

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Start Server**
```bash
# Start development server
./scripts/start.sh

# Or manually
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **3. Run Analytics Workflow**
```bash
# Method 1: Python Script (Recommended)
python scripts/run_analytics_workflow.py

# Method 2: Bash Script
./scripts/run_analytics_workflow.sh

# Method 3: Complete Analysis
python scripts/run_complete_analysis.py
```

---

## 📊 **ANALYTICS WORKFLOW**

### **Step-by-Step Process:**

1. **📤 Upload File** - Upload forensic reports (Excel/CSV)
2. **📱 Add Device** - Buat device dengan single file (1 device = 1 file)
3. **📊 Create Analytic** - Buat analytic dengan linked devices
4. **🔗 Contact Correlation** - Jalankan analisis korelasi kontak
5. **📄 Export PDF** - Export hasil ke PDF

### **File Types Supported:**
- **Excel**: .xlsx, .xls
- **CSV**: .csv
- **Tools**: Oxygen, Magnet Axiom, Cellebrite

---

## 🔍 **ANALYSIS TYPES**

### **1. Contact Correlation**
- **Tujuan**: Menemukan kontak yang sama di beberapa perangkat
- **Output**: Daftar kontak dengan korelasi antar perangkat
- **Kegunaan**: Investigasi jaringan komunikasi

### **2. Hashfile Analysis**
- **Tujuan**: Analisis file berdasarkan hash untuk deteksi duplikasi
- **Output**: File duplikat, mencurigakan, dan malware
- **Kegunaan**: Deteksi file yang sama di beberapa perangkat

---

## 📄 **REPORTS GENERATED**

### **PDF Reports:**
1. **Contact Correlation Report** - Laporan korelasi kontak
2. **Hashfile Correlation Report** - Laporan korelasi hashfile

### **Lokasi Laporan:**
- Semua laporan PDF disimpan di folder `data/reports/{analytic_id}/`
- Format: Professional forensic report
- Content: Executive summary, detailed analysis, conclusions

---

## 🛠️ **TROUBLESHOOTING**

### **Common Issues:**

#### **Server Issues:**
```bash
# Restart server
python scripts/restart.py

# Check server status
python scripts/status.py
```

#### **Database Issues:**
```bash
# Check database connection
python -c "from app.database import engine; print('Database connected')"
```

#### **File Upload Issues:**
- Pastikan file ada di direktori yang benar
- Periksa ekstensi file sesuai dengan tipe yang dipilih
- Pastikan ukuran file tidak melebihi 100MB

---

## 📱 **POSTMAN TESTING**

### **Import Collections:**
1. Import `Forenlytic_Analytics_API.postman_collection.json`
2. Import `Forenlytic_Analytics_Environment.postman_environment.json`
3. Set environment variables
4. Run collection in sequence

### **Environment Variables:**
- `base_url`: http://localhost:8000/api/v1
- `analytic_id`: 1
- `device_id`: 1
- `file_id`: 1

---

## 🎯 **USE CASES**

### **1. Multi-Device Investigation**
- Analisis data dari beberapa perangkat tersangka
- Korelasi kontak dan komunikasi antar perangkat
- Deteksi file yang sama di beberapa perangkat

### **2. Contact Correlation Analysis**
- Analisis kontak yang sama di beberapa perangkat
- Identifikasi jaringan komunikasi
- Export laporan PDF untuk keperluan hukum

---

## 📊 **STATISTICS**

### **System Capabilities:**
- ✅ **Analytics API Endpoints** untuk analisis lengkap
- ✅ **Multi-Platform Support** - iPhone, Android, PC, Laptop, SSD, Harddisk
- ✅ **Multiple Tools Support** - Cellebrite, Oxygen, Magnet Axiom
- ✅ **Professional Reports** - PDF dengan format forensik
- ✅ **Automated Workflow** - Script otomatis untuk efisiensi

### **File Processing:**
- ✅ **Multiple Formats** - Excel, CSV
- ✅ **Large File Support** - Hingga 100MB per file
- ✅ **Encryption Support** - SDP format untuk keamanan

---

## 🎉 **CONCLUSION**

Sistem Forenlytic Analytics memberikan kemampuan analisis forensik digital yang komprehensif dengan:

1. **Multi-Platform Support** - Mendukung berbagai perangkat dan tools
2. **Advanced Analytics** - Analisis korelasi dan deteksi anomali
3. **Professional Reports** - Laporan PDF untuk keperluan hukum
4. **Automated Workflow** - Script otomatis untuk efisiensi
5. **Comprehensive Coverage** - Analisis dari kontak hingga media sosial

**Selamat menggunakan sistem Forenlytic Analytics untuk investigasi forensik digital Anda!** 🚀

---

## 📞 **SUPPORT**

Untuk bantuan dan dukungan:
- Dokumentasi lengkap tersedia di folder `docs/`
- Script otomatis tersedia di folder `scripts/`
- Postman collections tersedia untuk testing
- Contoh file tersedia di `sample_dataset/`