# Analytics API Examples

Contoh penggunaan lengkap untuk Analytics API dari upload file hingga contact correlation analysis.

## 📋 Daftar Isi

1. [Quick Start](#1-quick-start)
2. [File Management Examples](#2-file-management-examples)
3. [Device Management Examples](#3-device-management-examples)
4. [Analytics Management Examples](#4-analytics-management-examples)
5. [Contact Correlation Examples](#5-contact-correlation-examples)
6. [Complete Workflow Examples](#6-complete-workflow-examples)
7. [Error Handling Examples](#7-error-handling-examples)

---

## 1. Quick Start

### 1.1 Start Server
```bash
# Start the development server
./scripts/start.sh

# Check server status
python scripts/status.py
```

### 1.2 Run Complete Workflow
```bash
# Python script
python scripts/run_analytics_workflow.py

# Bash script
./scripts/run_analytics_workflow.sh
```

### 1.3 Import Postman Collection
1. Import `docs/Forenlytic_Analytics_API.postman_collection.json`
2. Import `docs/Forenlytic_Analytics_Environment.postman_environment.json`
3. Set environment variables as needed

---

## 2. File Management Examples

### 2.1 Upload File with cURL
```bash
# Upload Excel file
curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
     -F "file=@contacts_export.xlsx" \
     -F "file_name=contacts_export.xlsx" \
     -F "tools=oxygen"

# Upload CSV file
curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
     -F "file=@whatsapp_chats.csv" \
     -F "file_name=whatsapp_chats.csv" \
     -F "tools=cellebrite"
```

### 2.2 Upload File with Python
```python
import requests

def upload_file(file_path, file_name, tools):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'file_name': file_name,
            'tools': tools
        }
        response = requests.post(
            "http://localhost:8000/api/v1/analytics/upload-data",
            files=files,
            data=data
        )
    return response.json()

# Example usage
result = upload_file("contacts_export.xlsx", "contacts_export.xlsx", "oxygen")
print(f"File ID: {result['data']['file_id']}")
```

### 2.3 Get All Files
```bash
# Get all uploaded files
curl -X GET "http://localhost:8000/api/v1/analytics/files/all"
```

### 2.4 Expected Response
```json
{
  "status": 200,
  "message": "Files retrieved successfully",
  "data": [
    {
      "id": 1,
      "file_name": "contacts_export.xlsx",
      "file_size": 245760,
      "tools": "oxygen",
      "upload_time": "2024-01-15T10:30:00Z",
      "status": "processed"
    }
  ]
}
```

---

## 3. Device Management Examples

### 3.1 Add Device with cURL
```bash
# Add device with file ID 1
curl -X POST "http://localhost:8000/api/v1/analytics/device/add-device" \
     -F "owner_name=John Doe" \
     -F "phone_number=081234567890" \
     -F "file_id=1"
```

### 3.2 Add Device with Python
```python
import requests

def add_device(owner_name, phone_number, file_id):
    data = {
        'owner_name': owner_name,
        'phone_number': phone_number,
        'file_id': file_id
    }
    response = requests.post(
        "http://localhost:8000/api/v1/analytics/device/add-device",
        data=data
    )
    return response.json()

# Example usage
result = add_device("John Doe", "081234567890", 1)
print(f"Device ID: {result['data']['device_id']}")
```

### 3.3 Get All Devices
```bash
# Get all devices
curl -X GET "http://localhost:8000/api/v1/analytics/device/get-all-devices"
```

### 3.4 Get Device by ID
```bash
# Get device with ID 1
curl -X GET "http://localhost:8000/api/v1/analytics/device/1"
```

### 3.5 Get Device by ID with Python
```python
import requests

def get_device_by_id(device_id):
    response = requests.get(f"http://localhost:8000/api/v1/analytics/device/{device_id}")
    return response.json()

# Example usage
result = get_device_by_id(1)
print(f"Device: {result['data']['owner_name']}")
print(f"Phone: {result['data']['phone_number']}")
print(f"Device Type: {result['data']['device_type']}")
print(f"Extraction Status: {result['data']['data_extraction_status']['is_extracted']}")
```

### 3.6 Expected Response
```json
{
  "status": 200,
  "message": "Device created successfully",
  "data": {
        "device_id": 1,
    "owner_name": "John Doe",
    "phone_number": "081234567890",
    "file_id": 1,
    "created_at": "2024-01-15T10:35:00Z"
  }
}
```

---

## 4. Analytics Management Examples

### 4.1 Create Analytic with cURL
```bash
# Create analytic with multiple devices
curl -X POST "http://localhost:8000/api/v1/analytics/create-analytic-with-devices" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Contact Correlation Analysis",
       "description": "Analysis of contact correlations across devices",
       "method": "Contact Correlation",
       "device_ids": [1, 2, 3]
     }'
```

### 4.2 Create Analytic with Python
```python
import requests

def create_analytic(name, description, method, device_ids):
    data = {
        'name': name,
        'description': description,
        'method': method,
        'device_ids': device_ids
    }
    response = requests.post(
        "http://localhost:8000/api/v1/analytics/create-analytic-with-devices",
        json=data
    )
    return response.json()

# Example usage
result = create_analytic(
    "Contact Correlation Analysis",
    "Analysis of contact correlations across devices",
    "Contact Correlation",
    [1, 2, 3]
)
print(f"Analytic ID: {result['data']['analytic_id']}")
```

### 4.3 Get All Analytics
```bash
# Get all analytics
curl -X GET "http://localhost:8000/api/v1/analytics/get-all-analytics"
```

### 4.4 Expected Response
```json
{
  "status": 200,
  "message": "Analytic created successfully",
  "data": {
      "analytic_id": 1,
    "name": "Contact Correlation Analysis",
    "description": "Analysis of contact correlations across devices",
    "method": "Contact Correlation",
    "status": "created",
    "created_at": "2024-01-15T12:00:00Z",
    "devices": [
      {
        "device_id": 1,
        "owner_name": "John Doe",
        "phone_number": "081234567890"
      }
    ]
  }
}
```

---

## 5. Contact Correlation Examples

### 5.1 Run Contact Correlation with cURL
```bash
# Run contact correlation analysis
curl -X POST "http://localhost:8000/api/v1/analytic/1/contact-correlation" \
     -H "Content-Type: application/json" \
     -d '{"analytic_id": 1}'
```

### 5.2 Run Contact Correlation with Python
```python
import requests

def run_contact_correlation(analytic_id):
    data = {'analytic_id': analytic_id}
    response = requests.post(
        f"http://localhost:8000/api/v1/analytic/{analytic_id}/contact-correlation",
        json=data
    )
    return response.json()

# Example usage
result = run_contact_correlation(1)
print(f"Correlations found: {len(result['data']['correlations'])}")
```

### 5.3 Export PDF with cURL
```bash
# Export correlation results to PDF
curl -X GET "http://localhost:8000/api/v1/analytic/1/export-pdf" \
     --output "contact_correlation_report.pdf"
```

### 5.4 Save Contact Correlation Summary with cURL
```bash
# Save summary for analytic
curl -X POST "http://localhost:8000/api/v1/analytic/1/save-summary" \
     -H "Content-Type: application/json" \
     -d '{
       "summary": "Analisis korelasi kontak menunjukkan bahwa terdapat 3 kontak yang sama antara Device A dan Device B. Kontak utama yang teridentifikasi adalah Alice Wilson (081234567893) yang muncul di kedua device. Hal ini menunjukkan kemungkinan komunikasi antara kedua pemilik device."
     }'
```

### 5.5 Save Contact Correlation Summary with Python
```python
import requests

def save_summary(analytic_id, summary):
    data = {"summary": summary}
    response = requests.post(
        f"http://localhost:8000/api/v1/analytic/{analytic_id}/save-summary",
        json=data
    )
    return response.json()

# Example usage
summary_text = """
Analisis korelasi kontak menunjukkan bahwa terdapat 3 kontak yang sama antara Device A dan Device B. 
Kontak utama yang teridentifikasi adalah Alice Wilson (081234567893) yang muncul di kedua device. 
Hal ini menunjukkan kemungkinan komunikasi antara kedua pemilik device.
"""
result = save_summary(1, summary_text)
print(f"Summary saved: {result['message']}")
```

### 5.6 Export PDF with cURL
```bash
# Export correlation results to PDF
curl -X GET "http://localhost:8000/api/v1/analytic/1/export-pdf" \
     --output "contact_correlation_report.pdf"
```

### 5.7 Export PDF with Python
```python
import requests

def export_pdf(analytic_id, output_path):
    response = requests.get(
        f"http://localhost:8000/api/v1/analytic/{analytic_id}/export-pdf"
    )
    with open(output_path, "wb") as f:
        f.write(response.content)

# Example usage
export_pdf(1, "contact_correlation_report.pdf")
```

### 5.8 Expected Response (With Correlations)
```json
{
  "status": 200,
  "message": "Contact correlation analysis completed",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "device_id": 1,
        "owner_name": "John Doe",
        "phone_number": "081234567890"
      },
      {
        "device_label": "Device B",
        "device_id": 2,
        "owner_name": "Jane Smith",
        "phone_number": "081234567891"
      }
    ],
    "correlations": [
      {
        "phone_number": "081234567893",
        "contact_name": "Alice Wilson",
        "devices_found_in": [
          {
            "device_label": "Device A",
            "device_id": 1,
            "owner_name": "John Doe"
          },
          {
            "device_label": "Device B",
            "device_id": 2,
            "owner_name": "Jane Smith"
          }
        ]
      }
    ]
  }
}
```

### 5.9 Expected Response (No Correlations)
```json
{
  "status": 200,
  "message": "Contact correlation analysis completed",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "device_id": 1,
        "owner_name": "John Doe",
        "phone_number": "081234567890"
      },
      {
        "device_label": "Device B",
        "device_id": 2,
        "owner_name": "Jane Smith",
        "phone_number": "081234567891"
      }
    ],
    "correlations": []
  }
}
```

---

## 6. Complete Workflow Examples

### 6.1 Complete Workflow with cURL
```bash
#!/bin/bash

# 1. Upload file
echo "Uploading file..."
FILE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
     -F "file=@contacts_export.xlsx" \
     -F "file_name=contacts_export.xlsx" \
     -F "tools=oxygen")
FILE_ID=$(echo $FILE_RESPONSE | jq -r '.data.file_id')
echo "File ID: $FILE_ID"

# 2. Add device
echo "Adding device..."
DEVICE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/analytics/device/add-device" \
     -F "owner_name=John Doe" \
     -F "phone_number=081234567890" \
     -F "file_id=$FILE_ID")
DEVICE_ID=$(echo $DEVICE_RESPONSE | jq -r '.data.device_id')
echo "Device ID: $DEVICE_ID"

# 3. Create analytic
echo "Creating analytic..."
ANALYTIC_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/analytics/create-analytic-with-devices" \
     -H "Content-Type: application/json" \
     -d "{\"name\": \"Contact Correlation Analysis\", \"description\": \"Analysis of contact correlations\", \"method\": \"Contact Correlation\", \"device_ids\": [$DEVICE_ID]}")
ANALYTIC_ID=$(echo $ANALYTIC_RESPONSE | jq -r '.data.analytic_id')
echo "Analytic ID: $ANALYTIC_ID"

# 4. Run correlation
echo "Running contact correlation..."
CORRELATION_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/analytic/$ANALYTIC_ID/contact-correlation" \
  -H "Content-Type: application/json" \
     -d "{\"analytic_id\": $ANALYTIC_ID}")
echo "Correlation results:"
echo $CORRELATION_RESPONSE | jq '.data.correlations | length'

# 5. Export PDF
echo "Exporting PDF..."
curl -X GET "http://localhost:8000/api/v1/analytic/$ANALYTIC_ID/export-pdf" \
     --output "contact_correlation_report_$ANALYTIC_ID.pdf"
echo "PDF exported: contact_correlation_report_$ANALYTIC_ID.pdf"
```

### 6.2 Complete Workflow with Python
```python
import requests
import json

class AnalyticsWorkflow:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def upload_file(self, file_path, file_name, tools):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'file_name': file_name, 'tools': tools}
            response = self.session.post(f"{self.base_url}/analytics/upload-data", files=files, data=data)
        return response.json()
    
    def add_device(self, owner_name, phone_number, file_id):
        data = {'owner_name': owner_name, 'phone_number': phone_number, 'file_id': file_id}
        response = self.session.post(f"{self.base_url}/analytics/device/add-device", data=data)
        return response.json()
    
    def create_analytic(self, name, description, method, device_ids):
        data = {'name': name, 'description': description, 'method': method, 'device_ids': device_ids}
        response = self.session.post(f"{self.base_url}/analytics/create-analytic-with-devices", json=data)
        return response.json()
    
    def run_contact_correlation(self, analytic_id):
        data = {'analytic_id': analytic_id}
        response = self.session.post(f"{self.base_url}/analytic/{analytic_id}/contact-correlation", json=data)
        return response.json()
    
    def export_pdf(self, analytic_id, output_path):
        response = self.session.get(f"{self.base_url}/analytic/{analytic_id}/export-pdf")
        with open(output_path, "wb") as f:
            f.write(response.content)

# Example usage
workflow = AnalyticsWorkflow()

# 1. Upload file
upload_result = workflow.upload_file("contacts_export.xlsx", "contacts_export.xlsx", "oxygen")
file_id = upload_result['data']['file_id']

# 2. Add device
device_result = workflow.add_device("John Doe", "081234567890", file_id)
device_id = device_result['data']['device_id']

# 3. Create analytic
analytic_result = workflow.create_analytic(
    "Contact Correlation Analysis",
    "Analysis of contact correlations",
    "Contact Correlation",
    [device_id]
)
analytic_id = analytic_result['data']['analytic_id']

# 4. Run correlation
correlation_result = workflow.run_contact_correlation(analytic_id)
print(f"Correlations found: {len(correlation_result['data']['correlations'])}")

# 5. Export PDF
workflow.export_pdf(analytic_id, f"contact_correlation_report_{analytic_id}.pdf")
```

---

## 7. Error Handling Examples

### 7.1 Common Error Responses

#### 400 Bad Request
```json
{
  "status": 400,
  "message": "Invalid request data",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": "phone_number is required and must be valid"
  }
}
```

#### 404 Not Found
```json
{
  "status": 404,
  "message": "File not found",
  "error": {
    "code": "FILE_NOT_FOUND",
    "details": "File with ID 1 does not exist"
  }
}
```

#### 500 Internal Server Error
```json
{
  "status": 500,
  "message": "Failed to process uploaded file",
  "error": {
    "code": "PROCESSING_ERROR",
    "details": "Error occurred during file parsing"
  }
}
```

### 7.2 Error Handling in Python
```python
import requests

def safe_api_call(func, *args, **kwargs):
    try:
        response = func(*args, **kwargs)
        if response.status_code == 200:
            return response.json()
        else:
            error_data = response.json()
            print(f"API Error: {error_data['message']}")
            print(f"Details: {error_data['error']['details']}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return None
        except Exception as e:
        print(f"Unexpected Error: {e}")
        return None

# Example usage
def upload_file_safe(file_path, file_name, tools):
    def upload():
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'file_name': file_name, 'tools': tools}
            return requests.post("http://localhost:8000/api/v1/analytics/upload-data", files=files, data=data)
    
    return safe_api_call(upload)
```

### 7.3 Error Handling in Bash
```bash
#!/bin/bash

# Function to handle API calls with error checking
api_call() {
    local url="$1"
    local method="$2"
    local data="$3"
    
    response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" $data)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        echo "$body"
        return 0
    else
        echo "Error: HTTP $http_code" >&2
        echo "$body" | jq -r '.message // "Unknown error"' >&2
        return 1
    fi
}

# Example usage
upload_file_safe() {
    local file_path="$1"
    local file_name="$2"
    local tools="$3"
    
    api_call "http://localhost:8000/api/v1/analytics/upload-data" "POST" \
        "-F file=@$file_path -F file_name=$file_name -F tools=$tools"
}
```

---

## 8. Testing Examples

### 8.1 Test with Sample Data
```bash
# Create sample Excel file with overlapping contacts
python scripts/create_correlation_test_data.py

# Run workflow with sample data
python scripts/run_analytics_workflow.py
```

### 8.2 Test with Real Data
```bash
# Upload your own files
curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
     -F "file=@your_contacts.xlsx" \
     -F "file_name=your_contacts.xlsx" \
     -F "tools=oxygen"

# Continue with workflow...
```

### 8.3 Validate Results
```python
import requests

def validate_correlation_results(analytic_id):
    response = requests.post(
        f"http://localhost:8000/api/v1/analytic/{analytic_id}/contact-correlation",
        json={"analytic_id": analytic_id}
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        devices = data['devices']
        correlations = data['correlations']
        
        print(f"Devices analyzed: {len(devices)}")
        print(f"Correlations found: {len(correlations)}")
        
        for correlation in correlations:
            print(f"Contact: {correlation['contact_name']} ({correlation['phone_number']})")
            print(f"Found in {len(correlation['devices_found_in'])} devices:")
            for device in correlation['devices_found_in']:
                print(f"  - {device['device_label']}: {device['owner_name']}")
        
        return True
    else:
        print(f"Validation failed: {response.status_code}")
        return False
```

---

## 9. Best Practices

### 9.1 File Upload
- Use supported formats: Excel (.xlsx) and CSV
- Ensure file contains contact data with phone numbers
- Use appropriate tools parameter: "oxygen", "cellebrite", "magnet_axiom"

### 9.2 Device Management
- Use valid phone numbers (Indonesian format: 08xxxxxxxxx)
- Provide meaningful owner names
- Ensure file_id exists before creating device

### 9.3 Analytics
- Use descriptive names for analytics
- Include multiple devices for meaningful correlation
- Use "Contact Correlation" as method for contact analysis

### 9.4 Error Handling
- Always check HTTP status codes
- Handle network timeouts
- Validate response data structure
- Log errors for debugging

### 9.5 Performance
- Use session objects for multiple requests
- Implement retry logic for failed requests
- Cache results when appropriate
- Monitor API response times

---

**📚 Analytics API Examples siap digunakan!**