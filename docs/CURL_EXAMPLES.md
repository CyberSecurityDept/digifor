# Forenlytic Backend - cURL Examples

Kumpulan contoh cURL commands untuk testing API Forenlytic Backend.

## 🚀 Quick Start

### **1. Start Server**
```bash
./run.sh
```

### **2. Set Base URL**
```bash
export BASE_URL="http://localhost:8000"
```

## 🔐 Authentication

### **Login**
```bash
curl -X POST "$BASE_URL/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### **Get Token (for other requests)**
```bash
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

echo "Token: $TOKEN"
```

### **Get User Info**
```bash
curl -X GET "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```


## 📁 Case Management

### **Create Case**
```bash
curl -X POST "$BASE_URL/api/v1/cases/" \
  -H "Authorization: Bearer $TOKEN" \
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

### **Get All Cases**
```bash
curl -X GET "$BASE_URL/api/v1/cases/" \
  -H "Authorization: Bearer $TOKEN"
```

### **Get Case by ID**
```bash
curl -X GET "$BASE_URL/api/v1/cases/1" \
  -H "Authorization: Bearer $TOKEN"
```

### **Update Case**
```bash
curl -X PUT "$BASE_URL/api/v1/cases/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "notes": "Investigation in progress",
    "priority": "critical"
  }'
```

### **Archive Case**
```bash
curl -X DELETE "$BASE_URL/api/v1/cases/1" \
  -H "Authorization: Bearer $TOKEN"
```

## 👤 Case Persons

### **Add Person to Case**
```bash
curl -X POST "$BASE_URL/api/v1/cases/1/persons" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_type": "suspect",
    "full_name": "John Doe",
    "alias": "Johnny",
    "phone": "08123456789",
    "email": "john.doe@example.com",
    "social_media_accounts": {
      "facebook": "john.doe",
      "instagram": "@johndoe"
    },
    "description": "Primary suspect in cybercrime case",
    "is_primary": true
  }'
```

### **Get Case Persons**
```bash
curl -X GET "$BASE_URL/api/v1/cases/1/persons" \
  -H "Authorization: Bearer $TOKEN"
```

### **Update Case Person**
```bash
curl -X PUT "$BASE_URL/api/v1/cases/1/persons/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "08123456788",
    "description": "Updated suspect information"
  }'
```

### **Delete Case Person**
```bash
curl -X DELETE "$BASE_URL/api/v1/cases/1/persons/1" \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Case Statistics

### **Get Case Statistics**
```bash
curl -X GET "$BASE_URL/api/v1/cases/1/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## 📄 Report Generation

### **Generate Comprehensive Report**
```bash
curl -X POST "$BASE_URL/api/v1/reports/cases/1/generate?report_type=comprehensive" \
  -H "Authorization: Bearer $TOKEN"
```

### **Generate Summary Report**
```bash
curl -X POST "$BASE_URL/api/v1/reports/cases/1/generate?report_type=summary" \
  -H "Authorization: Bearer $TOKEN"
```

### **Generate Evidence Report**
```bash
curl -X POST "$BASE_URL/api/v1/reports/cases/1/generate?report_type=evidence" \
  -H "Authorization: Bearer $TOKEN"
```

### **Generate Analysis Report**
```bash
curl -X POST "$BASE_URL/api/v1/reports/cases/1/generate?report_type=analysis" \
  -H "Authorization: Bearer $TOKEN"
```

### **List Case Reports**
```bash
curl -X GET "$BASE_URL/api/v1/reports/cases/1/reports" \
  -H "Authorization: Bearer $TOKEN"
```

### **Get Specific Report**
```bash
curl -X GET "$BASE_URL/api/v1/reports/cases/1/reports/case_1_comprehensive_CASE-2024-001.json" \
  -H "Authorization: Bearer $TOKEN"
```

### **Delete Report**
```bash
curl -X DELETE "$BASE_URL/api/v1/reports/cases/1/reports/case_1_comprehensive_CASE-2024-001.json" \
  -H "Authorization: Bearer $TOKEN"
```

### **Get Report Statistics**
```bash
curl -X GET "$BASE_URL/api/v1/reports/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔍 Filtering & Search

### **Filter by Status**
```bash
curl -X GET "$BASE_URL/api/v1/cases/?status=open" \
  -H "Authorization: Bearer $TOKEN"
```

### **Filter by Priority**
```bash
curl -X GET "$BASE_URL/api/v1/cases/?priority=high" \
  -H "Authorization: Bearer $TOKEN"
```

### **Filter by Case Type**
```bash
curl -X GET "$BASE_URL/api/v1/cases/?case_type=criminal" \
  -H "Authorization: Bearer $TOKEN"
```

### **Search by Title**
```bash
curl -X GET "$BASE_URL/api/v1/cases/?search=cybercrime" \
  -H "Authorization: Bearer $TOKEN"
```

### **Pagination**
```bash
curl -X GET "$BASE_URL/api/v1/cases/?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### **Combined Filters**
```bash
curl -X GET "$BASE_URL/api/v1/cases/?status=open&priority=high&search=cybercrime&skip=0&limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

## 🧪 Complete Testing Workflow

### **Step 1: Setup**
```bash
# Set base URL
export BASE_URL="http://localhost:8000"

# Get authentication token
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

echo "Token: $TOKEN"
```

### **Step 2: Create Test Case**
```bash
CASE_ID=$(curl -s -X POST "$BASE_URL/api/v1/cases/" \
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

### **Step 3: Add Person**
```bash
curl -X POST "$BASE_URL/api/v1/cases/$CASE_ID/persons" \
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

### **Step 4: Generate Report**
```bash
curl -X POST "$BASE_URL/api/v1/reports/cases/$CASE_ID/generate?report_type=comprehensive" \
  -H "Authorization: Bearer $TOKEN"
```

### **Step 5: Get Statistics**
```bash
curl -X GET "$BASE_URL/api/v1/cases/$CASE_ID/stats" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔧 Utility Commands

### **Health Check**
```bash
curl -X GET "$BASE_URL/health"
```

### **API Root**
```bash
curl -X GET "$BASE_URL/"
```

### **Pretty Print JSON Response**
```bash
curl -X GET "$BASE_URL/api/v1/cases/" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### **Save Response to File**
```bash
curl -X GET "$BASE_URL/api/v1/cases/" \
  -H "Authorization: Bearer $TOKEN" > cases.json
```

### **Verbose Output**
```bash
curl -v -X GET "$BASE_URL/api/v1/cases/" \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Response Examples

### **Successful Case Creation**
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

### **Error Response**
```json
{
  "detail": "Could not validate credentials"
}
```

## 🎯 Tips & Best Practices

1. **Always check response status codes**
2. **Use jq for pretty printing JSON**
3. **Store tokens in variables for reuse**
4. **Test error scenarios**
5. **Use verbose mode for debugging**
6. **Save important responses to files**

---

**🎯 cURL Examples siap untuk testing API!**
