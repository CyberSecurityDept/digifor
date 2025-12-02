# Digital Forensics Backend Tests

Folder ini berisi semua file test untuk aplikasi Digital Forensics Backend.

## 🧪 Daftar Test Files

### **API Tests**

- **[test_api.py](test_api.py)** - Automated API testing script

## Cara Menjalankan Tests

### **1. API Testing**

```bash
# Dari root directory backend/
python tests/test_api.py

# Atau dari folder tests
cd tests
python test_api.py
```

### **2. Unit Testing (Future)**

```bash
# Install pytest jika belum ada
pip install pytest pytest-asyncio

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest tests/ --cov=app
```

## Test Categories

### **1. API Integration Tests**

- Health check endpoint
- Authentication endpoints
- Case management endpoints
- Report generation endpoints

### **2. Unit Tests (Planned)**

- Model validation tests
- Service layer tests
- Utility function tests
- Analytics engine tests

### **3. End-to-End Tests (Planned)**

- Complete workflow tests
- Database integration tests
- File upload tests
- Report generation tests

## 🔧 Test Configuration

### **Environment Setup**

Tests menggunakan environment yang sama dengan aplikasi:

- Database: SQLite3 test database
- API Base URL: http://172.15.4.26
- Default admin: admin / admin123

### **Test Data**

- Test cases dibuat otomatis
- Test data di-cleanup setelah test
- Isolated test environment

## Test Results

### **API Test Output**

```
Starting Digital Forensics Backend API Tests...
==================================================
Testing health endpoint...
Health check passed
   Response: {'status': 'healthy', 'version': '1.0.0', 'database': 'connected'}

🔐 Testing authentication...
Login successful
   Token type: bearer

📁 Testing case management...
Case created successfully
   Case ID: 1
   Case Number: TEST-001

🔧 Testing case operations...
Get case successful
Update case successful
Add person successful
Get case stats successful

Testing report generation...
Generate comprehensive report successful
   Filename: case_1_comprehensive_TEST-001.json
List reports successful
   Total reports: 1

==================================================
🎯 API Testing completed!
📖 API Documentation: http://172.15.4.26/docs
📚 ReDoc: http://172.15.4.26/redoc
```

## 🐛 Troubleshooting

### **Test Failures**

1. Pastikan aplikasi berjalan di http://172.15.4.26
2. Check database sudah diinitialize
3. Check admin user sudah dibuat
4. Check logs untuk error details

### **Connection Errors**

```bash
# Check if server is running
curl http://172.15.4.26/health

# Restart server if needed
./run.sh
```

### **Database Errors**

```bash
# Recreate database
rm data/digifor.db
python init_db.py
python create_admin.py
```

## 📝 Writing New Tests

### **API Test Template**

```python
def test_endpoint():
    """Test specific endpoint"""
    response = requests.get(f"{BASE_URL}/endpoint")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### **Unit Test Template**

```python
def test_function():
    """Test specific function"""
    result = function_to_test(input_data)
    assert result == expected_output
```

## 🎯 Future Test Plans

### **Phase 1: Basic Tests**

- API integration tests
- 🔄 Authentication tests
- 🔄 Case management tests

### **Phase 2: Advanced Tests**

- Analytics engine tests
- Report generation tests
- File upload tests

### **Phase 3: Performance Tests**

- Load testing
- Stress testing
- Database performance tests

---

**🎯 Test suite siap untuk memastikan kualitas Digital Forensics Backend!**
