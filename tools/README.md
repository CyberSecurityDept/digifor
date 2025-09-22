# Forenlytic Backend Tools

Folder ini berisi semua tools dan utility Python untuk mengelola aplikasi Forenlytic Backend.

## 🛠️ Daftar Tools

### **Database Management**
- **[init_db.py](init_db.py)** - Initialize database dan create tables
- **[create_admin.py](create_admin.py)** - Create admin user default

### **Development Tools**
- **[run.py](run.py)** - Production runner script
- **[run_dev.py](run_dev.py)** - Development runner script dengan auto-reload

## 🚀 Cara Menggunakan

### **1. Initialize Database**
```bash
# Dari root directory backend/
python tools/init_db.py

# Atau dari folder tools
cd tools
python init_db.py
```

### **2. Create Admin User**
```bash
# Dari root directory backend/
python tools/create_admin.py

# Atau dari folder tools
cd tools
python create_admin.py
```

### **3. Run Application**
```bash
# Development mode (dengan auto-reload)
python tools/run_dev.py

# Production mode
python tools/run.py
```

## 📋 Deskripsi Tools

### **init_db.py**
- Membuat database SQLite3
- Create semua tables berdasarkan models
- Setup database schema
- Menampilkan status initialization

### **create_admin.py**
- Membuat admin user default
- Username: admin
- Password: admin123
- Role: admin
- Cek jika user sudah ada

### **run.py**
- Production runner script
- Menggunakan uvicorn
- Konfigurasi production
- Logging ke file

### **run_dev.py**
- Development runner script
- Auto-reload enabled
- Debug mode
- Console logging

## 🔧 Konfigurasi

Tools menggunakan konfigurasi dari:
- `app/config.py` - Konfigurasi aplikasi
- `app/database.py` - Database connection
- `app/models/` - Database models

## 🐛 Troubleshooting

### **Database Error**
```bash
# Recreate database
rm data/forenlytic.db
python tools/init_db.py
```

### **Admin User Error**
```bash
# Recreate admin user
python tools/create_admin.py
```

### **Permission Error**
```bash
# Make scripts executable
chmod +x tools/*.py
```

## 📝 Notes

- Semua tools menggunakan Python 3.11
- Database menggunakan SQLite3 untuk development
- Default admin: admin / admin123
- Pastikan virtual environment aktif sebelum menjalankan tools

---

**🎯 Tools siap digunakan untuk mengelola Forenlytic Backend!**
