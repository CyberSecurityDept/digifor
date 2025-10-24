# Analytics API Contract

## Overview
This document describes the Analytics API endpoints for the Forenlytic system, including File Management, Device Management, Analytics Management, Contact Correlation, Deep Communication, Hashfile Analytics, APK Analytics, and Social Media Analytics.

## Base URL
```
/api/v1
```

## Authentication
All endpoints require authentication (implementation depends on your auth system).

---

## 1. File Management

### 1.1 Get All Files
**Endpoint**: `GET /api/v1/analytics/files/all`

**Description**: Retrieves all uploaded files in the system.

**Parameters**: None

**Response 200**:
```json
{
  "status": 200,
  "message": "Files retrieved successfully",
  "data": [
    {
      "id": 1,
      "file_name": "device_data.xlsx",
      "original_name": "device_data.xlsx",
      "file_path": "/uploads/data/device_data_123456.xlsx",
      "file_size": 1024000,
      "file_type": "xlsx",
      "notes": "Device data from iPhone",
      "created_at": "2025-10-22T15:08:14"
    }
  ]
}
```

**Response 500**:
```json
{
  "status": 500,
  "message": "Database error",
  "data": null
}
```

### 1.2 Upload Data
**Endpoint**: `POST /api/v1/analytics/upload-data`

**Description**: Uploads and processes forensic data files.

**Parameters**:
- `file` (form-data): File to upload (required)
- `file_name` (form-data): Name for the file (required)
- `notes` (form-data): Additional notes (required)
- `type` (form-data): Device type - "Handphone" | "SSD" | "Harddisk" | "PC" | "Laptop" | "DVR" (required)
- `tools` (form-data): Forensic tool used - "Oxygen" | "Cellebrite" | "Axiom" | "Encase" (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "File uploaded and processed successfully",
  "data": {
    "upload_id": "upload_1698064894_abc12345",
    "file_id": 1,
    "file_name": "device_data.xlsx",
    "file_size": 1024000,
    "processing_status": "completed",
    "parsing_result": {
      "tool_used": "Oxygen",
      "contacts_count": 150,
      "messages_count": 500,
      "calls_count": 200,
      "hashfiles_count": 0,
      "parsing_success": true
    }
  }
}
```

**Response 400**:
```json
{
  "status": 400,
  "message": "Invalid file extension for type 'Handphone'. Allowed: ['xlsx', 'xls', 'csv', 'apk', 'ipa']",
  "data": null
}
```

**Response 500**:
```json
{
  "status": 500,
  "message": "Upload error: File processing failed",
  "data": null
}
```

---

## 2. Device Management

### 2.1 Add Device
**Endpoint**: `POST /api/v1/analytics/add-device`

**Description**: Creates a new device record linked to uploaded files.

**Parameters**:
- `owner_name` (form-data): Device owner name (required)
- `phone_number` (form-data): Phone number (required)
- `file_id` (form-data): ID of uploaded file (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Device created successfully",
  "data": {
    "device_id": 1,
    "owner_name": "John Doe",
    "phone_number": "+6281234567890",
    "device_name": "John Doe Device",
    "file_id": 1,
    "created_at": "2025-10-22T15:08:14"
  }
}
```

**Response 400**:
```json
{
  "status": 400,
  "message": "File not found",
  "data": null
}
```

### 2.2 Get All Devices
**Endpoint**: `GET /api/v1/analytics/device/get-all-devices`

**Description**: Retrieves all devices in the system.

**Parameters**: None

**Response 200**:
```json
{
  "status": 200,
  "message": "Devices retrieved successfully",
  "data": [
    {
      "id": 1,
      "owner_name": "John Doe",
      "phone_number": "+6281234567890",
      "device_name": "John Doe Device",
      "created_at": "2025-10-22T15:08:14"
    }
  ]
}
```

### 2.3 Get Device by ID
**Endpoint**: `GET /api/v1/analytics/device/{device_id}`

**Description**: Retrieves specific device information.

**Parameters**:
- `device_id` (path): Device ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Device retrieved successfully",
  "data": {
    "id": 1,
    "owner_name": "John Doe",
    "phone_number": "+6281234567890",
    "device_name": "John Doe Device",
    "created_at": "2025-10-22T15:08:14"
  }
}
```

**Response 404**:
```json
{
  "status": 404,
  "message": "Device not found",
  "data": null
}
```

---

## 3. Analytics Management

### 3.1 Get All Analytics
**Endpoint**: `GET /api/v1/analytics/get-all-analytic`

**Description**: Retrieves all analytics sessions.

**Parameters**: None

**Response 200**:
```json
{
  "status": 200,
  "message": "Retrieved 5 analytics successfully",
  "data": [
    {
      "id": 1,
      "analytic_name": "Contact Analysis 2024",
      "method": "Contact Correlation",
      "summary": "Found 15 common contacts",
      "created_at": "2025-10-22T15:08:14"
    }
  ]
}
```

### 3.2 Create Analytics with Devices
**Endpoint**: `POST /api/v1/analytics/create-analytic-with-devices`

**Description**: Creates analytics for any supported method with device linking.

**Request Body**:

**For Hashfile Analytics**:
```json
{
  "analytic_name": "Malware Analysis 2024",
  "method": "Hashfile Analytics",
  "device_ids": [1, 2, 3]
}
```

**For Other Analytics**:
```json
{
  "analytic_name": "Contact Analysis 2024",
  "method": "Contact Correlation",
  "device_ids": [1, 2, 3]
}
```

**Field Descriptions**:
- `analytic_name`: Name for the analytics session (required)
- `method`: Analytics type - "Contact Correlation" | "Deep Communication" | "Hashfile Analytics" | "APK Analytics" | "Social Media Analytics" (required)
- `device_ids`: Array of device IDs to analyze (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Analytics created and 3 devices linked successfully",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "Contact Analysis 2024",
      "method": "Contact Correlation",
      "summary": null,
      "created_at": "2025-10-22T15:08:14"
    },
    "linked_devices": {
      "total_devices": 3,
      "linked_count": 3,
      "already_linked": 0,
      "devices": [
        {
          "device_id": 1,
          "owner_name": "John Doe",
          "phone_number": "+6281234567890",
          "device_name": "iPhone 13"
        }
      ]
    }
  }
}
```

**Response 400**:
```json
{
  "status": 400,
  "message": "Invalid method. Must be one of: Contact Correlation, Deep Communication, Hashfile Analytics, APK Analytics, Social Media Analytics",
  "data": []
}
```

**Response 500**:
```json
{
  "status": 500,
  "message": "Failed to create analytics: Database connection error",
  "data": null
}
```

### 3.3 Save Analytics Summary
**Endpoint**: `POST /api/v1/analytic/{analytic_id}/save-summary`

**Description**: Saves or updates analytics summary.

**Parameters**:
- `analytic_id` (path): Analytics ID (required)

**Request Body**:
```json
{
  "summary": "Ditemukan 25 file mencurigakan yang sama di 3 device. File paling berbahaya: suspicious.exe (High Risk) dan keylogger.dll (Critical Risk)."
}
```

**Response 200**:
```json
{
  "status": 200,
  "message": "Summary saved successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Malware Analysis 2024",
    "summary": "Ditemukan 25 file mencurigakan yang sama di 3 device...",
    "updated_at": "2025-10-22T15:15:30"
  }
}
```

**Response 404**:
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

### 3.4 Export Analytics PDF
**Endpoint**: `GET /api/v1/analytic/{analytic_id}/export-pdf`

**Description**: Exports analytics report as PDF. Automatically detects analytics type and generates appropriate report.

**Parameters**:
- `analytic_id` (path): Analytics ID (required)

**Response**: PDF file download

**Response 404**:
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

---

## 4. Contact Correlation Analysis

### 4.1 Get Contact Correlation
**Endpoint**: `GET /api/v1/analytic/{analytic_id}/contact-correlation`

**Description**: Returns contact correlation matrix showing which contacts are present on which devices.

**Parameters**:
- `analytic_id` (path): Analytics ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Contact correlation retrieved successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Contact Analysis 2024",
    "devices": [
      {
        "id": 1,
        "owner_name": "John Doe",
        "phone_number": "+6281234567890",
        "device_name": "iPhone 13"
      }
    ],
    "contacts": [
      {
        "contact_name": "John Doe",
        "phone_number": "+6281234567890",
        "device_count": 3,
        "devices": {
          "1": {
            "device_id": 1,
            "device_name": "iPhone 13",
            "is_present": true,
            "contact_name": "John Doe"
          }
        }
      }
    ],
    "statistics": {
      "total_devices": 3,
      "total_contacts": 150,
      "cross_device_contacts": 25
    }
  }
}
```

**Response 404**:
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

---

## 5. Deep Communication Analysis

### 5.1 Get Deep Communication by Analytic
**Endpoint**: `GET /api/v1/analytics/{analytic_id}/deep-communication`

**Description**: Returns deep communication analysis for specific analytics.

**Parameters**:
- `analytic_id` (path): Analytics ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Deep communication analysis retrieved successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Communication Analysis 2024",
    "devices": [
      {
        "id": 1,
        "owner_name": "John Doe",
        "phone_number": "+6281234567890",
        "device_name": "iPhone 13"
      }
    ],
    "communications": [
      {
        "id": 1,
        "sender": "John Doe",
        "receiver": "Jane Smith",
        "message_text": "Hello, how are you?",
        "timestamp": "2025-10-22T15:08:14",
        "device_id": 1,
        "thread_id": "thread_123"
      }
    ],
    "statistics": {
      "total_devices": 3,
      "total_messages": 500,
      "unique_contacts": 25
    }
  }
}
```

### 5.2 Get Thread Messages
**Endpoint**: `GET /api/v1/analytics/deep-communication/{device_id}/chat/{thread_id}`

**Description**: Retrieves specific thread messages for a device.

**Parameters**:
- `device_id` (path): Device ID (required)
- `thread_id` (path): Thread ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Thread messages retrieved successfully",
  "data": {
    "device_id": 1,
    "thread_id": "thread_123",
    "messages": [
      {
        "id": 1,
        "sender": "John Doe",
        "receiver": "Jane Smith",
        "message_text": "Hello, how are you?",
        "timestamp": "2025-10-22T15:08:14"
      }
    ]
  }
}
```

---

## 6. Hashfile Analytics

### 6.1 Get Hashfile Analytics
**Endpoint**: `GET /api/v1/analytic/{analytic_id}/hashfile-analytics`

**Description**: Returns hashfile correlation analysis showing which files are present on which devices.

**Parameters**:
- `analytic_id` (path): Analytics ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Hashfile correlation retrieved successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Hashfile Analysis 2024",
    "devices": [
      {
        "id": 1,
        "owner_name": "John Doe",
        "phone_number": "+6281234567890",
        "device_name": "iPhone 13"
      }
    ],
    "hashfiles": [
      {
        "hash_value": "d41d8cd98f00b204e9800998ecf8427e",
        "file_name": "suspicious.exe",
        "file_path": "/system/bin/suspicious.exe",
        "file_size": 1024000,
        "file_type": "Executable",
        "file_extension": "exe",
        "is_suspicious": true,
        "risk_level": "High",
        "source_type": "File System",
        "source_tool": "Cellebrite",
        "device_count": 2,
        "devices": {
          "1": {
            "device_id": 1,
            "device_name": "iPhone 13",
            "is_present": true
          }
        }
      }
    ],
    "statistics": {
      "total_devices": 3,
      "total_hashfiles": 1500,
      "common_hashfiles": 25,
      "unique_hashfiles": 1475,
      "min_devices_threshold": 2
    },
    "description": {
      "endpoints": {
        "save_summary": "/api/v1/analytic/1/save-summary",
        "export_pdf": "/api/v1/analytic/1/export-pdf"
      }
    }
  }
}
```

**Response 404**:
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

---

## 7. APK Analysis

### 7.1 Get APK Analysis
**Endpoint**: `GET /api/v1/analytics/{analytic_id}/apk-analytic`

**Description**: Returns APK analysis results for specific analytics.

**Parameters**:
- `analytic_id` (path): Analytics ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "APK analysis retrieved successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "APK Analysis 2024",
    "devices": [
      {
        "id": 1,
        "owner_name": "John Doe",
        "phone_number": "+6281234567890",
        "device_name": "iPhone 13"
      }
    ],
    "apks": [
      {
        "apk_name": "suspicious_app.apk",
        "package_name": "com.suspicious.app",
        "version": "1.0.0",
        "risk_level": "High",
        "is_malware": true,
        "device_count": 2,
        "devices": {
          "1": {
            "device_id": 1,
            "device_name": "iPhone 13",
            "is_present": true
          }
        }
      }
    ],
    "statistics": {
      "total_devices": 3,
      "total_apks": 50,
      "malicious_apks": 5,
      "common_apks": 10
    }
  }
}
```

### 7.2 Analyze APK
**Endpoint**: `POST /api/v1/analytics/analyze-apk`

**Description**: Analyzes a specific APK file.

**Parameters**:
- `file_id` (query): File ID to analyze (required)
- `analytic_id` (query): Analytics ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "APK analysis completed successfully",
  "data": {
    "file_id": 1,
    "analytic_id": 1,
    "apk_analysis": {
      "package_name": "com.suspicious.app",
      "version": "1.0.0",
      "risk_level": "High",
      "is_malware": true,
      "permissions": ["android.permission.INTERNET", "android.permission.CAMERA"],
      "threats_detected": ["Keylogger", "Data Exfiltration"]
    }
  }
}
```

---

## 8. Social Media Analytics

### 8.1 Get Social Media Correlation
**Endpoint**: `GET /api/v1/analytics/{analytic_id}/social-media-correlation`

**Description**: Returns social media correlation analysis.

**Parameters**:
- `analytic_id` (path): Analytics ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Social media correlation retrieved successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Social Media Analysis 2024",
    "devices": [
      {
        "id": 1,
        "owner_name": "John Doe",
        "phone_number": "+6281234567890",
        "device_name": "iPhone 13"
      }
    ],
    "social_media_data": [
      {
        "platform": "WhatsApp",
        "account": "john.doe@example.com",
        "device_count": 2,
        "devices": {
          "1": {
            "device_id": 1,
            "device_name": "iPhone 13",
            "is_present": true
          }
        }
      }
    ],
    "statistics": {
      "total_devices": 3,
      "total_accounts": 25,
      "cross_device_accounts": 5
    }
  }
}
```

---

## 9. Error Responses

### 9.1 Common Error Responses

**400 Bad Request**:
```json
{
  "status": 400,
  "message": "Invalid request parameters",
  "data": null
}
```

**404 Not Found**:
```json
{
  "status": 404,
  "message": "Resource not found",
  "data": null
}
```

**500 Internal Server Error**:
```json
{
  "status": 500,
  "message": "Internal server error",
  "data": null
}
```

---

## 10. Workflow Examples

### 10.1 Complete Analytics Workflow

1. **Upload Data**:
   ```bash
   POST /api/v1/analytics/upload-data
   ```

2. **Add Device**:
   ```bash
   POST /api/v1/analytics/add-device
   ```

3. **Create Analytics**:
   ```bash
   POST /api/v1/analytics/create-analytic-with-devices
   ```

4. **Get Analytics Results**:
   ```bash
   GET /api/v1/analytic/{analytic_id}/contact-correlation
   GET /api/v1/analytic/{analytic_id}/hashfile-analytics
   GET /api/v1/analytics/{analytic_id}/deep-communication
   GET /api/v1/analytics/{analytic_id}/apk-analytic
   GET /api/v1/analytics/{analytic_id}/social-media-correlation
   ```

5. **Save Summary**:
   ```bash
   POST /api/v1/analytic/{analytic_id}/save-summary
   ```

6. **Export PDF**:
   ```bash
   GET /api/v1/analytic/{analytic_id}/export-pdf
   ```

---

## 11. Notes

- All timestamps are in ISO 8601 format
- Device IDs must exist in the database
- Hashfile analytics only shows files that appear on at least 2 devices
- PDF exports are generated with timestamp in filename
- Summary can be saved multiple times (updates existing)
- All analytics support universal summary and PDF export
- File uploads support various forensic tool formats

---

*Last updated: 2025-10-23*