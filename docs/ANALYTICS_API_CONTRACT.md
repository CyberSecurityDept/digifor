# Analytics API Contract

## Overview
This document describes the API endpoints for the Analytics system, including Contact Correlation, Deep Communication, Hashfile Analytics, and APK Analytics.

## Base URL
```
/api/v1
```

## Authentication
All endpoints require authentication (implementation depends on your auth system).

---

## 1. Universal Analytics Management

### 1.1 Create Analytics with Devices
**Endpoint**: `POST /api/v1/analytics/create-analytic-with-devices`

**Description**: Creates analytics for any supported method with device linking.

**Request Body**:

**For Hashfile Analytics** (no description field):
```json
{
  "analytic_name": "Malware Analysis 2024",
  "method": "Hashfile Analytics",
  "device_ids": [1, 2, 3],
  "min_device_threshold": 2,
  "include_suspicious_only": true,
  "hash_algorithm": "MD5"
}
```

**For Other Analytics (Contact Correlation, Deep Communication, APK Analytics)**:
```json
{
  "analytic_name": "Contact Analysis 2024",
  "method": "Contact Correlation",
  "device_ids": [1, 2, 3]
}
```

**Field Descriptions**:
- `analytic_name`: Name for the analytics session (required)
- `method`: Analytics type - "Contact Correlation" | "Deep Communication" | "Hashfile Analytics" | "APK Analytics" (required)
- `device_ids`: Array of device IDs to analyze (required)
- `description`: Description for hashfile analytics only (optional, only for Hashfile Analytics)
- `min_device_threshold`: Minimum devices to show hashfile (optional, default: 2, only for Hashfile Analytics)
- `include_suspicious_only`: Include only suspicious files (optional, default: false, only for Hashfile Analytics)
- `hash_algorithm`: Hash algorithm to use (optional, default: "MD5", only for Hashfile Analytics)

**Response**:
```json
{
  "status": 200,
  "message": "Analytics created and 3 devices linked successfully",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "Malware Analysis 2024",
      "type": "Hashfile Analytics",
      "method": "Hashfile Analytics",
      "summary": null,
      "created_at": "2025-10-22T15:08:14"
    },
    "hashfile_analytics": {
      "id": 1,
      "analytic_name": "Malware Analysis 2024",
      "total_hashfiles": 150,
      "total_devices": 3,
      "common_hashfiles_count": 25,
      "min_device_threshold": 2,
      "include_suspicious_only": true,
      "created_at": "2025-10-22T15:08:14"
    },
    "statistics": {
      "total_devices": 3,
      "total_hashfiles": 150,
      "common_hashfiles": 25,
      "unique_hashfiles": 120,
      "average_files_per_device": 50.0
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

### 1.2 Get All Analytics
**Endpoint**: `GET /api/v1/analytics/get-all-analytic`

**Response**:
```json
{
  "status": 200,
  "message": "Retrieved 5 analytics successfully",
  "data": [
    {
      "id": 1,
      "analytic_name": "Contact Analysis",
      "method": "Contact Correlation",
      "summary": "Found 15 common contacts",
      "created_at": "2025-10-22T15:08:14"
    }
  ]
}
```

---

## 2. Universal Summary & Export

### 2.1 Save Analytics Summary
**Endpoint**: `POST /api/v1/analytic/{analytic_id}/save-summary`

**Request Body**:
```json
{
  "summary": "Ditemukan 25 file mencurigakan yang sama di 3 device. File paling berbahaya: suspicious.exe (High Risk) dan keylogger.dll (Critical Risk)."
}
```

**Response**:
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

### 2.2 Export Analytics PDF
**Endpoint**: `GET /api/v1/analytic/{analytic_id}/export-pdf`

**Description**: Exports analytics report as PDF. Automatically detects analytics type and generates appropriate report.

**Response**: PDF file download

---

---

## 4. Contact Correlation Analytics

### 4.1 Get Contact Correlation Matrix
**Endpoint**: `GET /api/v1/analytics/contact-correlation/{analytic_id}`

**Description**: Returns contact correlation matrix showing which contacts are present on which devices.

**Response**:
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

---

## 5. Deep Communication Analytics

### 5.1 Get Communication Matrix
**Endpoint**: `GET /api/v1/analytics/communication/{analytic_id}`

**Description**: Returns communication analysis matrix.

**Response**:
```json
{
  "status": 200,
  "message": "Communication analysis retrieved successfully",
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
        "message_id": 1,
        "sender": "John Doe",
        "receiver": "Jane Smith",
        "message_text": "Hello, how are you?",
        "timestamp": "2025-10-22T15:08:14",
        "device_id": 1
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

---

## 6. APK Analytics

### 6.1 Get APK Analysis
**Endpoint**: `GET /api/v1/analytics/apk/{analytic_id}`

**Description**: Returns APK analysis results.

**Response**:
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

---

## 7. Error Responses

### 7.1 Common Error Responses

**404 Not Found**:
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**400 Bad Request**:
```json
{
  "status": 400,
  "message": "Invalid method. Must be one of: Contact Correlation, Deep Communication, Hashfile Analytics, APK Analytics",
  "data": []
}
```

**500 Internal Server Error**:
```json
{
  "status": 500,
  "message": "Failed to create analytics: Database connection error",
  "data": null
}
```

---

## 8. Workflow Examples

### 8.1 Complete Hashfile Analytics Workflow

1. **Create Analytics** (Hashfile Analytics without description):
   ```bash
   POST /api/v1/analytics/create-analytic-with-devices
   {
     "analytic_name": "Malware Analysis 2024",
     "method": "Hashfile Analytics",
     "device_ids": [1, 2, 3],
     "min_device_threshold": 2,
     "include_suspicious_only": true,
     "hash_algorithm": "MD5"
   }
   ```

2. **Save Summary**:
   ```bash
   POST /api/v1/analytic/1/save-summary
   {
     "summary": "Ditemukan 25 file mencurigakan yang sama di 3 device..."
   }
   ```

4. **Export PDF**:
   ```bash
   GET /api/v1/analytic/1/export-pdf
   ```

### 8.2 Contact Correlation Workflow

1. **Create Analytics**:
   ```bash
   POST /api/v1/analytics/create-analytic-with-devices
   {
     "analytic_name": "Contact Analysis 2024",
          "method": "Contact Correlation",
          "device_ids": [1, 2, 3]
   }
   ```

2. **Get Contact Matrix**:
   ```bash
   GET /api/v1/analytics/contact-correlation/1
   ```

3. **Save Summary**:
   ```bash
   POST /api/v1/analytic/1/save-summary
   {
     "summary": "Ditemukan 15 kontak yang sama di 3 device..."
   }
   ```

4. **Export PDF**:
   ```bash
   GET /api/v1/analytic/1/export-pdf
```

---

## 9. Notes

- All timestamps are in ISO 8601 format
- Device IDs must exist in the database
- Hashfile analytics only shows files that appear on at least 2 devices
- PDF exports are generated with timestamp in filename
- Summary can be saved multiple times (updates existing)
- All analytics support universal summary and PDF export

---

## 10. Deprecated Endpoints

- `POST /api/v1/hashfile-analytics/create` → Use `POST /api/v1/analytics/create-analytic-with-devices`
- `GET /api/v1/hashfile-analytics/` → Use `GET /api/v1/analytics/get-all-analytic`
- `PUT /api/v1/hashfile-analytics/{id}` → Use universal summary endpoint
- `DELETE /api/v1/hashfile-analytics/{id}` → Use universal analytics management

---

*Last updated: 2025-10-22*