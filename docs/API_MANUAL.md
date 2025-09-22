# Forenlytic Backend API Manual

Manual lengkap untuk testing dan menggunakan API Forenlytic Backend.

## 🚀 Quick Start

### **1. Start Server**
```bash
# Cara termudah
./run.sh

# Atau manual
./scripts/start_backend.sh
```

### **2. Access API Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### **3. Default Credentials**
- **Username**: admin
- **Password**: admin123

## 🔐 Authentication

### **Login untuk mendapatkan token**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```


### **Get User Info**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📁 Case Management

### **1. Create Case**
```bash
curl -X POST "http://localhost:8000/api/v1/cases/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "case_number": "CASE-2024-001",
    "title": "Digital Forensics Investigation",
    "description": "Investigation of suspected cybercrime activity",
    "case_type": "criminal",
    "priority": "high",
    "jurisdiction": "Jakarta",
    "case_officer": "Detective Smith",
    "tags": {
      "category": "cybercrime",
      "status": "active"
    }
  }'
```

**Response:**
```json
{
  "id": 1,
  "case_number": "CASE-2024-001",
  "title": "Digital Forensics Investigation",
  "description": "Investigation of suspected cybercrime activity",
  "case_type": "criminal",
  "priority": "high",
  "status": "open",
  "jurisdiction": "Jakarta",
  "case_officer": "Detective Smith",
  "evidence_count": 0,
  "analysis_progress": 0,
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z",
  "tags": {
    "category": "cybercrime",
    "status": "active"
  }
}
```

### **2. Get All Cases**
```bash
curl -X GET "http://localhost:8000/api/v1/cases/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**With Filters:**
```bash
# Filter by status
curl -X GET "http://localhost:8000/api/v1/cases/?status=open" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Filter by priority
curl -X GET "http://localhost:8000/api/v1/cases/?priority=high" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Search by title
curl -X GET "http://localhost:8000/api/v1/cases/?search=cybercrime" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Pagination
curl -X GET "http://localhost:8000/api/v1/cases/?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **3. Get Case by ID**
```bash
curl -X GET "http://localhost:8000/api/v1/cases/1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **4. Update Case**
```bash
curl -X PUT "http://localhost:8000/api/v1/cases/1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "notes": "Investigation in progress",
    "priority": "critical"
  }'
```

### **5. Archive Case**
```bash
curl -X DELETE "http://localhost:8000/api/v1/cases/1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 👤 Case Persons Management

### **1. Add Person to Case**
```bash
curl -X POST "http://localhost:8000/api/v1/cases/1/persons" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "person_type": "suspect",
    "full_name": "John Doe",
    "alias": "Johnny",
    "date_of_birth": "1990-01-01",
    "nationality": "Indonesian",
    "address": "Jakarta, Indonesia",
    "phone": "08123456789",
    "email": "john.doe@example.com",
    "social_media_accounts": {
      "facebook": "john.doe",
      "instagram": "@johndoe",
      "twitter": "@johndoe"
    },
    "device_identifiers": {
      "imei": "123456789012345",
      "mac_address": "00:11:22:33:44:55"
    },
    "description": "Primary suspect in cybercrime case",
    "is_primary": true
  }'
```

### **2. Get Case Persons**
```bash
curl -X GET "http://localhost:8000/api/v1/cases/1/persons" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **3. Update Case Person**
```bash
curl -X PUT "http://localhost:8000/api/v1/cases/1/persons/1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "08123456788",
    "description": "Updated suspect information"
  }'
```

### **4. Delete Case Person**
```bash
curl -X DELETE "http://localhost:8000/api/v1/cases/1/persons/1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📊 Case Statistics

### **Get Case Statistics**
```bash
curl -X GET "http://localhost:8000/api/v1/cases/1/stats" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "case_id": 1,
  "evidence_count": 5,
  "analysis_count": 3,
  "completed_analysis": 2,
  "analysis_progress": 67,
  "status": "in_progress",
  "priority": "high"
}
```

## 📄 Report Generation

### **1. Generate Comprehensive Report**
```bash
curl -X POST "http://localhost:8000/api/v1/reports/cases/1/generate?report_type=comprehensive" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **2. Generate Summary Report**
```bash
curl -X POST "http://localhost:8000/api/v1/reports/cases/1/generate?report_type=summary" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **3. Generate Evidence Report**
```bash
curl -X POST "http://localhost:8000/api/v1/reports/cases/1/generate?report_type=evidence" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **4. Generate Analysis Report**
```bash
curl -X POST "http://localhost:8000/api/v1/reports/cases/1/generate?report_type=analysis" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **5. List Case Reports**
```bash
curl -X GET "http://localhost:8000/api/v1/reports/cases/1/reports" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **6. Get Specific Report**
```bash
curl -X GET "http://localhost:8000/api/v1/reports/cases/1/reports/case_1_comprehensive_CASE-2024-001.json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **7. Delete Report**
```bash
curl -X DELETE "http://localhost:8000/api/v1/reports/cases/1/reports/case_1_comprehensive_CASE-2024-001.json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **8. Get Report Statistics**
```bash
curl -X GET "http://localhost:8000/api/v1/reports/stats" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🧪 Testing Scripts

### **1. Run All Tests**
```bash
python tests/run_tests.py
```

### **2. Run Specific Tests**
```bash
# Authentication tests
python tests/test_auth.py

# Case management tests
python tests/test_cases.py

# Report generation tests
python tests/test_reports.py
```

## 📋 Complete Testing Workflow

### **Step 1: Start Server**
```bash
./run.sh
```

### **Step 2: Test Authentication**
```bash
# Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

echo "Token: $TOKEN"
```

### **Step 3: Create Test Case**
```bash
CASE_ID=$(curl -s -X POST "http://localhost:8000/api/v1/cases/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_number": "TEST-API-001",
    "title": "API Testing Case",
    "description": "Case created for API testing",
    "case_type": "criminal",
    "priority": "high"
  }' | jq -r '.id')

echo "Case ID: $CASE_ID"
```

### **Step 4: Add Person to Case**
```bash
curl -X POST "http://localhost:8000/api/v1/cases/$CASE_ID/persons" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_type": "suspect",
    "full_name": "Test Suspect",
    "phone": "08123456789",
    "email": "suspect@test.com",
    "is_primary": true
  }'
```

### **Step 5: Generate Report**
```bash
curl -X POST "http://localhost:8000/api/v1/reports/cases/$CASE_ID/generate?report_type=comprehensive" \
  -H "Authorization: Bearer $TOKEN"
```

### **Step 6: Get Case Statistics**
```bash
curl -X GET "http://localhost:8000/api/v1/cases/$CASE_ID/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Error Handling

### **Common Error Responses**

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**404 Not Found:**
```json
{
  "detail": "Case not found"
}
```

**400 Bad Request:**
```json
{
  "detail": "Invalid input data"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "case_number"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## 📊 Response Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Access denied |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |

## 🎯 Best Practices

### **1. Authentication**
- Always include Authorization header
- Store token securely
- Refresh token when expired

### **2. Error Handling**
- Check response status codes
- Handle validation errors
- Implement retry logic

### **3. Data Validation**
- Validate input data before sending
- Use appropriate data types
- Check required fields

### **4. Performance**
- Use pagination for large datasets
- Implement caching where appropriate
- Monitor response times

## 📚 Additional Resources

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Environment Config**: [docs/ENVIRONMENT.md](ENVIRONMENT.md)
- **Implementation Details**: [docs/IMPLEMENTATION.md](IMPLEMENTATION.md)

---

**🎯 API Manual siap untuk testing dan development!**
