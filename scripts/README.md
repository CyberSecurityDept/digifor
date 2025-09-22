# Forenlytic Backend Scripts

Folder ini berisi semua script shell (.sh) untuk menjalankan dan mengelola aplikasi Forenlytic Backend.

## 📜 Daftar Scripts

### **Setup & Installation**
- **[setup.sh](setup.sh)** - Script setup lengkap untuk pertama kali
- **[start_backend.sh](start_backend.sh)** - Script lengkap untuk menjalankan aplikasi

### **Development & Testing**
- **[start.sh](start.sh)** - Script untuk menjalankan aplikasi (setelah setup)

## 🚀 Cara Menggunakan

### **1. Setup Aplikasi (Pertama Kali)**
```bash
# Dari root directory backend/
./scripts/setup.sh
```

### **2. Menjalankan Aplikasi**
```bash
# Script lengkap (setup + run)
./scripts/start_backend.sh

# Atau script simple (setelah setup)
./scripts/start.sh
```

### **3. Menjalankan dari Folder Scripts**
```bash
cd scripts
./setup.sh
./start_backend.sh
```

## 📋 Deskripsi Scripts

### **setup.sh**
- Membuat virtual environment Python 3.11
- Install dependencies dari requirements.txt
- Membuat direktori yang diperlukan
- Initialize database SQLite3
- Membuat admin user default
- Menampilkan informasi setup

### **start_backend.sh**
- Script lengkap untuk menjalankan aplikasi
- Cek virtual environment
- Install/update dependencies
- Cek dan initialize database jika perlu
- Menjalankan aplikasi dengan auto-reload
- Menampilkan informasi akses

### **start.sh**
- Script simple untuk menjalankan aplikasi
- Asumsi virtual environment sudah ada
- Asumsi database sudah diinitialize
- Menjalankan aplikasi dengan uvicorn

## 🔧 Konfigurasi

Scripts menggunakan konfigurasi dari:
- `app/config.py` - Konfigurasi aplikasi
- `requirements.txt` - Dependencies Python
- `env.example` - Template environment variables

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
- Database menggunakan SQLite3 untuk development
- Default admin: admin / admin123
- API Documentation: http://localhost:8000/docs

---

**🎯 Scripts siap digunakan untuk mengelola Forenlytic Backend!**
