# Analytics API Contract Documentation

Dokumentasi lengkap API kontrak untuk Analytics Flow dari upload file hingga contact correlation analysis.

## 📋 Daftar Isi

1. [File Management API](#1-file-management-api)
2. [Device Management API](#2-device-management-api)
3. [Contact Parsing Features](#3-contact-parsing-features)
4. [Analytics Management API](#4-analytics-management-api)
5. [Contact Correlation Analysis API](#5-contact-correlation-analysis-api)
6. [Error Handling](#6-error-handling)
7. [Complete Workflow Example](#7-complete-workflow-example)
8. [Notes](#8-notes)

---

## 1. File Management API

### 1.1 Upload Data File

**Endpoint:** `POST /api/v1/analytics/upload-data`

**Description:** Upload file data untuk analisis forensik

**Request:**
```http
POST /api/v1/analytics/upload-data
Content-Type: multipart/form-data

file: [binary file data]
file_name: "contacts_export.xlsx"
tools: "oxygen"
```

**Request Body (Form Data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | File data (Excel, CSV, etc.) |
| `file_name` | String | Yes | Nama file |
| `tools` | String | Yes | Tools forensik yang digunakan |

**Response 200 - Success:**
```json
{
  "status": 200,
  "message": "File uploaded, encrypted & parsed successfully",
  "data": {
    "file_id": 1,
    "device_id": 1,
    "upload_id": "upload_1760611926_7483e9ec",
    "percentage": 100,
    "progress_size": "217.48 KB",
    "total_size": "217.48 KB",
    "done": true,
    "encrypted_path": "data/uploads/encrypted/Oxygen Forensics - iOS Image CCC.sdp",
    "parsing_result": {
      "tool_used": "Oxygen",
      "contacts_count": 30,
      "messages_count": 143,
      "calls_count": 1,
      "parsing_success": true
    },
    "parsed_data": {
      "contacts": [
        {
          "display_name": "Alifan",
          "phone_number": "+6281218973570",
          "type": "Contact (merged)",
          "last_time_contacted": null
        }
      ],
      "messages": [...],
      "calls": [...]
    }
  }
}
```

**Response 400 - Bad Request:**
```json
{
  "status": 400,
  "message": "Invalid file format or missing required fields",
  "error": {
    "code": "INVALID_FILE_FORMAT",
    "details": "Only Excel (.xlsx) and CSV files are supported"
  }
}
```

**Response 500 - Internal Server Error:**
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

### 1.2 Get All Files

**Endpoint:** `GET /api/v1/analytics/files/all`

**Description:** Mendapatkan daftar semua file yang telah diupload

**Request:**
```http
GET /api/v1/analytics/files/all
```

**Response 200 - Success:**
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
    },
    {
      "id": 2,
      "file_name": "whatsapp_chats.csv",
      "file_size": 512000,
      "tools": "cellebrite",
      "upload_time": "2024-01-15T11:15:00Z",
      "status": "processed"
    }
  ]
}
```

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve files",
  "error": {
    "code": "DATABASE_ERROR",
    "details": "Error connecting to database"
  }
}
```

---

## 2. Device Management API

### 2.1 Add Device

**Endpoint:** `POST /api/v1/analytics/add-device`

**Description:** Menambahkan device baru dengan file yang sudah diupload

**Request:**
```http
POST /api/v1/analytics/add-device
Content-Type: multipart/form-data

owner_name: "John Doe"
phone_number: "081234567890"
file_id: 1
```

**Request Body (Form Data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `owner_name` | String | Yes | Nama pemilik device |
| `phone_number` | String | Yes | Nomor telepon pemilik |
| `file_id` | Integer | Yes | ID file yang sudah diupload |

**Response 200 - Success:**
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

**Response 400 - Bad Request:**
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

**Response 404 - Not Found:**
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

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to create device",
  "error": {
    "code": "DATABASE_ERROR",
    "details": "Error saving device to database"
  }
}
```

### 2.2 Get All Devices

**Endpoint:** `GET /api/v1/analytics/device/get-all-devices`

**Description:** Mendapatkan daftar semua device dengan format grouped structure

**Request:**
```http
GET /api/v1/analytics/device/get-all-devices
```

**Response 200 - Success:**
```json
{
  "status": 200,
  "message": "Retrieved 4 devices successfully",
  "data": [
    {
      "device_label": "Device A",
      "data_device": [
        {
          "device_id": 1,
          "owner_name": "Juki",
          "phone_number": "08112157463",
          "device_name": "Juki Device",
          "file_name": "Magnet Axiom Report - CCC.xlsx",
          "created_at": "2025-10-17 13:12:29.473858",
          "file_info": {
            "file_id": 1,
            "file_name": "Magnet Axiom Report - CCC.xlsx",
            "file_type": "Handphone",
            "notes": "testing upload file Magnet Axiom Report - CCC",
            "tools": "Magnet Axiom",
            "total_size": 97446,
            "total_size_formatted": "95.16 KB"
          }
        }
      ]
    },
    {
      "device_label": "Device B",
      "data_device": [
        {
          "device_id": 2,
          "owner_name": "Bambang",
          "phone_number": "081322392337",
          "device_name": "Bambang Device",
          "file_name": "Oxygen Forensics - iOS Image CCC.xlsx",
          "created_at": "2025-10-17 13:14:49.333768",
          "file_info": {
            "file_id": 2,
            "file_name": "Oxygen Forensics - iOS Image CCC.xlsx",
            "file_type": "Handphone",
            "notes": "testing upload file Oxygen Forensics - iOS Image CCC",
            "tools": "Oxygen",
            "total_size": 222702,
            "total_size_formatted": "217.48 KB"
          }
        }
      ]
    }
  ]
}
```

**Device Label Logic:**
- 1-26 devices: Device A, Device B, ..., Device Z
- 27+ devices: Device AA, Device AB, Device AC, etc.
- Supports unlimited number of devices

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve devices",
  "error": {
    "code": "DATABASE_ERROR",
    "details": "Error connecting to database"
  }
}
```

### 2.3 Get Device by ID

**Endpoint:** `GET /api/v1/analytics/device/{device_id}`

**Description:** Mendapatkan detail device berdasarkan ID

**Request:**
```http
GET /api/v1/analytics/device/1
```

**Response 200 - Success:**
```json
{
  "status": 200,
  "message": "Device retrieved successfully",
  "data": {
    "device_id": 1,
    "owner_name": "Juki",
    "phone_number": "08112157463",
    "device_name": "Juki Device",
    "file_name": "Magnet Axiom Report - CCC.xlsx",
    "created_at": "2025-10-17 13:12:29.473858",
    "updated_at": "2025-10-17 13:12:29.473858",
    "file_info": {
      "file_id": 1,
      "file_name": "Magnet Axiom Report - CCC.xlsx",
      "file_type": "Handphone",
      "notes": "testing upload file Magnet Axiom Report - CCC",
      "tools": "Magnet Axiom",
      "total_size": 97446,
      "total_size_formatted": "95.16 KB"
    }
  }
}
```

**Response 404 - Not Found:**
```json
{
  "status": 404,
  "message": "Device not found",
  "data": []
}
```

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to get device",
  "data": []
}
```

---

## 3. Contact Parsing Features

### 3.1 Enhanced Contact Parsing

**Features:**
- **Smart Duplicate Handling**: Prevents duplicate phone numbers within same device
- **Priority-based Contact Selection**: WhatsApp Contact > Contact > com.whatsapp > com.lge.sync > com.android.contacts.sim > Telegram Contact
- **Indonesian Phone Number Normalization**: Converts 08, 62, +62 formats to +62
- **Generic Name Detection**: Sets display_name to "Unknown" for generic names like "Contact", "Home", etc.
- **Social Media ID Filtering**: Excludes Telegram ID, Instagram ID, WhatsApp ID from phone number parsing
- **Multi-contact Extraction**: Handles multiple contacts in single Excel row

**Contact Model:**
```json
{
  "display_name": "Alifan",
  "phone_number": "+6281218973570",
  "type": "Contact (merged)",
  "last_time_contacted": "2025-10-17T13:16:51.540Z"
}
```

**Duplicate Prevention Logic:**
- Same phone number + device_id = Skip insertion
- Within batch: First occurrence kept, subsequent duplicates skipped
- Priority system determines which contact to keep when duplicates found

**Phone Number Normalization:**
- `081234567890` → `+6281234567890`
- `6281234567890` → `+6281234567890`
- `+6281234567890` → `+6281234567890` (unchanged)
- Service numbers (3-7 digits): Kept as-is

**Performance Optimization:**
- **Smart Response Strategy**: Large datasets (>5000 records) return summary, smaller datasets return full data
- **Duplicate Prevention**: Prevents duplicate phone numbers within same device
- **Batch Processing**: Efficient handling of multiple contacts in single upload
- **Memory Optimization**: Streaming processing for large files

---

## 4. Analytics Management API

### 4.1 Create Analytic with Devices

**Endpoint:** `POST /api/v1/analytics/create-analytic-with-devices`

**Description:** Membuat analytic baru dengan device yang sudah ada

**Request:**
```http
POST /api/v1/analytics/create-analytic-with-devices
Content-Type: application/json

{
  "name": "Contact Correlation Analysis",
  "description": "Analysis of contact correlations across devices",
  "method": "Contact Correlation",
  "device_ids": [1, 2, 3]
}
```

**Request Body (JSON):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Nama analisis |
| `description` | String | No | Deskripsi analisis |
| `method` | String | Yes | Metode analisis |
| `device_ids` | Array[Integer] | Yes | Array ID device yang akan dianalisis |

**Response 200 - Success:**
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
      },
      {
        "device_id": 2,
        "owner_name": "Jane Smith",
        "phone_number": "081234567891"
      },
      {
        "device_id": 3,
        "owner_name": "Bob Johnson",
        "phone_number": "081234567892"
      }
    ]
  }
}
```

**Response 400 - Bad Request:**
```json
{
  "status": 400,
  "message": "Invalid request data",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": "device_ids must be a non-empty array"
  }
}
```

**Response 404 - Not Found:**
```json
{
  "status": 404,
  "message": "One or more devices not found",
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "details": "Device with ID 3 does not exist"
  }
}
```

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to create analytic",
  "error": {
    "code": "DATABASE_ERROR",
    "details": "Error saving analytic to database"
  }
}
```

### 4.2 Get All Analytics

**Endpoint:** `GET /api/v1/analytics/get-all-analytics`

**Description:** Mendapatkan daftar semua analytics

**Request:**
```http
GET /api/v1/analytics/get-all-analytics
```

**Response 200 - Success:**
```json
{
  "status": 200,
  "message": "Analytics retrieved successfully",
  "data": [
    {
      "analytic_id": 1,
      "name": "Contact Correlation Analysis",
      "description": "Analysis of contact correlations across devices",
      "method": "Contact Correlation",
      "status": "created",
      "created_at": "2024-01-15T12:00:00Z",
      "device_count": 3
    }
  ]
}
```

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve analytics",
  "error": {
    "code": "DATABASE_ERROR",
    "details": "Error connecting to database"
  }
}
```

---

## 5. Contact Correlation Analysis API

### 5.1 Get Contact Correlation

**Endpoint:** `POST /api/v1/analytic/{analytic_id}/contact-correlation`

**Description:** Melakukan analisis korelasi kontak antar device

**Request:**
```http
POST /api/v1/analytic/1/contact-correlation
Content-Type: application/json

{
  "analytic_id": 1
}
```

**Request Body (JSON):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `analytic_id` | Integer | Yes | ID analytic yang akan dianalisis |

**Response 200 - Success (With Correlations):**
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
      },
      {
        "device_label": "Device C",
        "device_id": 3,
        "owner_name": "Bob Johnson",
        "phone_number": "081234567892"
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
      },
      {
        "phone_number": "081234567894",
        "contact_name": "Unknown",
        "devices_found_in": [
          {
            "device_label": "Device A",
            "device_id": 1,
            "owner_name": "John Doe"
          },
          {
            "device_label": "Device C",
            "device_id": 3,
            "owner_name": "Bob Johnson"
          }
        ]
      }
    ]
  }
}
```

**Response 200 - Success (No Correlations):**
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

**Response 400 - Bad Request:**
```json
{
  "status": 400,
  "message": "Invalid request data",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": "analytic_id is required"
  }
}
```

**Response 404 - Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "error": {
    "code": "ANALYTIC_NOT_FOUND",
    "details": "Analytic with ID 1 does not exist"
  }
}
```

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to perform contact correlation analysis",
  "error": {
    "code": "ANALYSIS_ERROR",
    "details": "Error occurred during correlation analysis"
  }
}
```

### 5.2 Save Contact Correlation Summary

**Endpoint:** `POST /api/v1/analytic/{analytic_id}/save-summary`

**Description:** Menyimpan ringkasan hasil analisis korelasi kontak

**Request:**
```http
POST /api/v1/analytic/1/save-summary
Content-Type: application/json

{
  "summary": "Analisis korelasi kontak menunjukkan bahwa terdapat 3 kontak yang sama antara Device A dan Device B. Kontak utama yang teridentifikasi adalah Alice Wilson (081234567893) yang muncul di kedua device. Hal ini menunjukkan kemungkinan komunikasi antara kedua pemilik device."
}
```

**Request Body (JSON):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `summary` | String | Yes | Ringkasan hasil analisis korelasi kontak |

**Response 200 - Success:**
```json
{
  "status": 200,
  "message": "Summary saved successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Contact Correlation Analysis",
    "summary": "Analisis korelasi kontak menunjukkan bahwa terdapat 3 kontak yang sama antara Device A dan Device B. Kontak utama yang teridentifikasi adalah Alice Wilson (081234567893) yang muncul di kedua device. Hal ini menunjukkan kemungkinan komunikasi antara kedua pemilik device.",
    "updated_at": "2024-01-15T12:30:00Z"
  }
}
```

**Response 400 - Bad Request:**
```json
{
  "status": 400,
  "message": "Summary cannot be empty",
  "data": null
}
```

**Response 404 - Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to save summary",
  "data": null
}
```

### 5.3 Export Contact Correlation PDF

**Endpoint:** `GET /api/v1/analytic/{analytic_id}/export-pdf`

**Description:** Export hasil analisis korelasi kontak ke PDF

**Request:**
```http
GET /api/v1/analytic/1/export-pdf
```

**Response 200 - Success:**
```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename=contact_correlation_report_1_20240115_120000.pdf

[PDF Binary Data]
```

**Response 404 - Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "error": {
    "code": "ANALYTIC_NOT_FOUND",
    "details": "Analytic with ID 1 does not exist"
  }
}
```

**Response 500 - Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to generate PDF report",
  "error": {
    "code": "PDF_GENERATION_ERROR",
    "details": "Error occurred during PDF generation"
  }
}
```

---

## 6. Error Handling

### 6.1 Standard Error Response Format

Semua error response mengikuti format standar:

```json
{
  "status": [HTTP_STATUS_CODE],
  "message": "[Human readable error message]",
  "error": {
    "code": "[ERROR_CODE]",
    "details": "[Detailed error information]"
  }
}
```

### 6.2 Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request data tidak valid |
| `FILE_NOT_FOUND` | File tidak ditemukan |
| `DEVICE_NOT_FOUND` | Device tidak ditemukan |
| `ANALYTIC_NOT_FOUND` | Analytic tidak ditemukan |
| `INVALID_FILE_FORMAT` | Format file tidak didukung |
| `PROCESSING_ERROR` | Error saat memproses file |
| `DATABASE_ERROR` | Error database |
| `ANALYSIS_ERROR` | Error saat analisis |
| `PDF_GENERATION_ERROR` | Error saat generate PDF |

### 6.3 HTTP Status Codes

| Status | Description |
|--------|-------------|
| `200` | Success |
| `400` | Bad Request - Data tidak valid |
| `404` | Not Found - Resource tidak ditemukan |
| `500` | Internal Server Error - Error server |

---

## 7. Complete Workflow Example

### 7.1 Step-by-Step Workflow

1. **Upload File**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
        -F "file=@contacts_export.xlsx" \
        -F "file_name=contacts_export.xlsx" \
        -F "tools=oxygen"
   ```

2. **Add Device**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/analytics/add-device" \
        -F "owner_name=John Doe" \
        -F "phone_number=081234567890" \
        -F "file_id=1"
   ```

3. **Create Analytic**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/analytics/create-analytic-with-devices" \
        -H "Content-Type: application/json" \
        -d '{
          "name": "Contact Correlation Analysis",
          "description": "Analysis of contact correlations across devices",
          "method": "Contact Correlation",
          "device_ids": [1, 2, 3]
        }'
   ```

4. **Run Contact Correlation**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/analytic/1/contact-correlation" \
        -H "Content-Type: application/json" \
        -d '{"analytic_id": 1}'
   ```

5. **Export PDF**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/analytic/1/export-pdf" \
        --output "contact_correlation_report.pdf"
   ```

### 7.2 Python Script Example

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def upload_file(file_path, file_name, tools):
    """Upload file untuk analisis"""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'file_name': file_name,
            'tools': tools
        }
        response = requests.post(f"{BASE_URL}/analytics/upload-data", files=files, data=data)
    return response.json()

def add_device(owner_name, phone_number, file_id):
    """Tambah device baru"""
    data = {
        'owner_name': owner_name,
        'phone_number': phone_number,
        'file_id': file_id
    }
    response = requests.post(f"{BASE_URL}/analytics/add-device", data=data)
    return response.json()

def create_analytic(name, description, method, device_ids):
    """Buat analytic baru"""
    data = {
        'name': name,
        'description': description,
        'method': method,
        'device_ids': device_ids
    }
    response = requests.post(f"{BASE_URL}/analytics/create-analytic-with-devices", json=data)
    return response.json()

def run_contact_correlation(analytic_id):
    """Jalankan analisis korelasi kontak"""
    data = {'analytic_id': analytic_id}
    response = requests.post(f"{BASE_URL}/analytic/{analytic_id}/contact-correlation", json=data)
    return response.json()

def export_pdf(analytic_id):
    """Export hasil ke PDF"""
    response = requests.get(f"{BASE_URL}/analytic/{analytic_id}/export-pdf")
    return response

# Contoh penggunaan
if __name__ == "__main__":
    # 1. Upload file
    upload_result = upload_file("contacts_export.xlsx", "contacts_export.xlsx", "oxygen")
    file_id = upload_result['data']['file_id']
    
    # 2. Add device
    device_result = add_device("John Doe", "081234567890", file_id)
    device_id = device_result['data']['device_id']
    
    # 3. Create analytic
    analytic_result = create_analytic(
        "Contact Correlation Analysis",
        "Analysis of contact correlations across devices",
        "Contact Correlation",
        [device_id]
    )
    analytic_id = analytic_result['data']['analytic_id']
    
    # 4. Run correlation
    correlation_result = run_contact_correlation(analytic_id)
    print("Correlation Results:", json.dumps(correlation_result, indent=2))
    
    # 5. Export PDF
    pdf_response = export_pdf(analytic_id)
    with open("contact_correlation_report.pdf", "wb") as f:
        f.write(pdf_response.content)
```

---

## 8. Notes

- Semua endpoint menggunakan prefix `/api/v1`
- File upload mendukung format Excel (.xlsx) dan CSV
- **Enhanced Contact Parsing**: Smart duplicate handling, priority-based selection, Indonesian phone normalization
- **Device Response Format**: Grouped structure with device labels (Device A, Device B, etc.)
- **Performance Optimized**: Smart response strategy for large datasets
- **Clean Response**: Removed null fields and unnecessary data extraction status
- PDF export disimpan di `data/reports/{analytic_id}/`
- Uploaded files disimpan di `data/uploads/` dan `data/uploads/encrypted/`
- Database menggunakan PostgreSQL
- API Documentation tersedia di `http://localhost:8000/docs`
- **Contact Model**: Simplified to display_name, phone_number, type, last_time_contacted
- **Duplicate Prevention**: Same phone_number + device_id combinations are prevented

---

