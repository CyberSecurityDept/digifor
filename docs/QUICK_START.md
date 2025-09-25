# Forenlytic Backend - Quick Start Guide

## 🚀 Quick Start (5 Menit)

### 1. **Setup Aplikasi**
```bash
cd backend
./setup.sh
```

### 2. **Menjalankan Aplikasi**
```bash
./start.sh
```

### 3. **Akses API**
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 4. **Login Default**
- **Username**: admin
- **Password**: admin123

## 🔧 Manual Setup

### **1. Install Dependencies**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **2. Initialize Database**
```bash
python init_db.py
python create_admin.py
```

### **3. Run Application**
```bash
python run.py
# atau
python run_dev.py  # untuk development dengan auto-reload
```

## 🧪 Testing

### **Test API**
```bash
python test_api.py
```

### **Manual Test dengan curl**
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Create case (ganti YOUR_TOKEN dengan token dari login)
curl -X POST "http://localhost:8000/api/v1/cases/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_number": "TEST-001",
    "title": "Test Case",
    "description": "Test case description",
    "case_type": "criminal",
    "priority": "high"
  }'
```

## 📊 API Endpoints

### **Authentication**
- `POST /api/v1/auth/token` - Login
- `GET /api/v1/auth/me` - Get user info

### **Case Management**
- `POST /api/v1/cases/` - Create case
- `GET /api/v1/cases/` - List cases
- `GET /api/v1/cases/{id}` - Get case detail
- `PUT /api/v1/cases/{id}` - Update case
- `POST /api/v1/cases/{id}/persons` - Add person to case

### **Report Generation**
- `POST /api/v1/reports/cases/{id}/generate` - Generate report
- `GET /api/v1/reports/cases/{id}/reports` - List reports

## 🔍 Troubleshooting

### **Port sudah digunakan**
```bash
# Kill process di port 8000
lsof -ti:8000 | xargs kill
```

### **Database error**
```bash
# Recreate database
rm data/your_database.db
python init_db.py
python create_admin.py
```

### **Permission denied**
```bash
# Make scripts executable
chmod +x setup.sh start.sh run_dev.py test_api.py
```

### **Module not found**
```bash
# Activate virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

## 📁 Struktur File

```
backend/
├── app/                    # Aplikasi utama
├── data/                  # Data storage
├── logs/                  # Log files
├── requirements.txt       # Dependencies
├── setup.sh              # Setup script
├── start.sh              # Start script
├── run_dev.py            # Development runner
├── test_api.py           # API testing
└── README.md             # Documentation
```

## 🎯 Next Steps

1. **Test API** dengan `python test_api.py`
2. **Explore Documentation** di http://localhost:8000/docs
3. **Create test cases** melalui API
4. **Generate reports** untuk testing
5. **Integrate dengan frontend** (jika ada)

## Support

Jika ada masalah:
1. Check logs di `logs/forenlytic.log`
2. Check health endpoint: http://localhost:8000/health
3. Restart aplikasi: `./start.sh`
4. Recreate database: `python init_db.py`

---

**🎉 Selamat! Backend Forenlytic siap digunakan!**
