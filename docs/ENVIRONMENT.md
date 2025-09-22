# Environment Configuration

Dokumentasi konfigurasi environment untuk Forenlytic Backend.

## 📁 Environment Files

### **Development Environment**
- **[.env](.env)** - Konfigurasi development (default)
- **[env.example](env.example)** - Template environment variables

### **Production Environment**
- **[env.production](env.production)** - Konfigurasi production

### **Testing Environment**
- **[env.test](env.test)** - Konfigurasi testing

## 🔧 Environment Variables

### **Database Configuration**
```env
DATABASE_URL=sqlite:///./data/forenlytic.db
DATABASE_ECHO=False
```

**Development**: SQLite3 untuk kemudahan development
**Production**: PostgreSQL untuk performa dan skalabilitas

### **Security**
```env
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**⚠️ PENTING**: Ganti `SECRET_KEY` dan `ENCRYPTION_KEY` untuk production!

### **File Storage**
```env
UPLOAD_DIR=./data/uploads
ANALYSIS_DIR=./data/analysis
REPORTS_DIR=./data/reports
MAX_FILE_SIZE=104857600  # 100MB
```

### **Encryption**
```env
ENCRYPTION_KEY=your-encryption-key-here-32-chars
ENCRYPTION_ALGORITHM=AES-256-GCM
```

### **Logging**
```env
LOG_LEVEL=INFO
LOG_FILE=./logs/forenlytic.log
```

**Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### **API Configuration**
```env
API_V1_STR=/api/v1
PROJECT_NAME=Forenlytic
VERSION=1.0.0
```

### **Development Settings**
```env
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"]
```

### **Big Data Analytics**
```env
ANALYTICS_BATCH_SIZE=1000
HASH_ALGORITHMS=["md5", "sha1", "sha256"]
MAX_ANALYSIS_THREADS=4
```

## 🚀 Cara Menggunakan

### **1. Development (Default)**
```bash
# File .env sudah dikonfigurasi untuk development
./run.sh
```

### **2. Production**
```bash
# Copy production environment
cp env.production .env

# Edit sesuai kebutuhan
nano .env

# Jalankan aplikasi
./run.sh
```

### **3. Testing**
```bash
# Copy test environment
cp env.test .env

# Jalankan tests
python tests/run_tests.py
```

## 🔒 Security Best Practices

### **1. Secret Keys**
- Gunakan key yang kuat dan unik
- Minimal 32 karakter
- Kombinasi huruf, angka, dan simbol
- Simpan di environment variables, bukan di code

### **2. Database**
- Gunakan connection string yang aman
- Enable SSL untuk production
- Gunakan user database yang terbatas

### **3. File Storage**
- Set permission yang tepat
- Gunakan path yang aman
- Enable file validation

### **4. CORS**
- Batasi origins untuk production
- Jangan gunakan wildcard (*)
- Gunakan HTTPS untuk production

## 📊 Environment Comparison

| Setting | Development | Production | Testing |
|---------|-------------|------------|---------|
| Database | SQLite3 | PostgreSQL | SQLite3 |
| Debug | True | False | True |
| Log Level | INFO | WARNING | DEBUG |
| File Size | 100MB | 500MB | 10MB |
| Token Expiry | 30 min | 60 min | 5 min |
| CORS | Localhost | Domain | Localhost |

## 🐛 Troubleshooting

### **Environment Not Loaded**
```bash
# Check if .env exists
ls -la .env

# Check file permissions
chmod 600 .env
```

### **Database Connection Error**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test database connection
python tools/init_db.py
```

### **Permission Denied**
```bash
# Check file permissions
ls -la .env

# Fix permissions
chmod 600 .env
```

## 📝 Notes

- File `.env` tidak di-commit ke git (ada di .gitignore)
- Gunakan `env.example` sebagai template
- Selalu backup environment configuration
- Test konfigurasi sebelum deploy ke production

---

**🎯 Environment configuration siap untuk development, testing, dan production!**
