# Analytics API Contract

## Overview
This document describes the Analytics API endpoints for the Forenlytic system, including File Management, Device Management, Analytics Management, Contact Correlation, Deep Communication, Hashfile Analytics, APK Analytics, and Social Media Analytics.

## Base URL
```
/api/v1
```

## 0. Authentication
All endpoints require authentication (implementation depends on your auth system).

### 0.1 Login 
**Endpoint**: `POST /api/v1/auth/login`

**Request Body**
```json
{
  "email": "admin@gmail.com",
  "password": "password"
}
```

**Response 200**
```json
{
  "status": 200,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "admin@gmail.com",
      "fullname": "Admin Forensic",
      "tag": "Admin",
      "role": "admin"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNzYxNjM0MjE4LCJleHAiOjE3NjE2MzYwMTgsInR5cGUiOiJhY2Nlc3MifQ.lJqwyyXYKM32VvM9VYWhRQl_14OYvJrjIjvKFJVepqo",
      "refresh_token": "ekBwqeBq8HhPbgUQYV02-VFyRLAzHqr6vbfNowZ-nq9mxs6gexIkhwwDesAEIQ0v"
    }
  }
}
```


**Notes** 
When a user logs in, the system issues two tokens:
- access_token — used to access protected resources or endpoints.
- refresh_token — used to request a new access_token without having to log in again.
When the access_token expires, send the refresh_token to the /refresh endpoint to obtain a new one.


### 0.2 Refresh Token 
**Endpoint**: `POST /api/v1/auth/refresh`

**Request Body**
```json
{
  "refresh_token": "ekBwqeBq8HhPbgUQYV02-VFyRLAzHqr6vbfNowZ-nq9mxs6gexIkhwwDesAEIQ0v"
}
```

**Response 200**
```json
{
  "status": 200,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNzYxNjM0NDY4LCJleHAiOjE3NjE2MzYyNjgsInR5cGUiOiJhY2Nlc3MifQ.hWUhf5vXhJUuCjXnzGc-sppqBhlklFTkVnkoTzfHk0I",
    "refresh_token": "vifCle8QxzFVGPj0SyHGwiAjzE5_7xuaH8ley-36EH2ZeFXvXoxhpUrqHTY9KcyS",
    "token_type": "bearer"
  }
}
```
### 0.3 Logout 
**Endpoint**: `POST /api/v1/auth/logout`

**Headers**: `Authorization : Bearer {{token}}`

**Response 200**
```json
{
    "status": 200,
    "message": "Logout successful. All refresh tokens revoked.",
    "data": null
}
```

**ERROR RESPONSE AUTH**
**Response 401**
```json
{
  "status": 401,
  "message": "Invalid or expired refresh token"
}
```

```json
{
  "status": 401,
  "message": "Invalid credentials",
}
```

```json
{
  "status": 401,
  "message": "Invalid token type",
}
```

```json
{
  "status": 401,
  "message": "Expired token",
}
```

```json
{
  "status": 401,
  "message": "Invalid token",
}
```

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
  "message": "File uploaded successfully.",
  "data": [
    {
      "id": 2,
      "file_name": "TESTING CELLEBRITE",
      "file_path": "data/uploads/data/iPhone 7_2025-10-22_Report.xlsx",
      "notes": "TESTING",
      "type": "Handphone",
      "tools": "cellebrite",
      "total_size": 105118,
      "total_size_formatted": "102.65 KB",
      "amount_of_data": 0,
      "created_at": "2025-10-27T15:48:44.034286"
    },
    {
      "id": 1,
      "file_name": "TESTING CELLEBRITE",
      "file_path": "data/uploads/data/iPhone 7_2025-10-22_Report.xlsx",
      "notes": "TESTING",
      "type": "Handphone",
      "tools": "cellebrite",
      "total_size": 105118,
      "total_size_formatted": "102.65 KB",
      "amount_of_data": 0,
      "created_at": "2025-10-27T15:43:56.571714"
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
}
```
**Response 400**:
```json
{
  "status": 400,
  "message": "Invalid type. Must be one of: ['Handphone', 'SSD', 'Harddisk', 'PC', 'Laptop', 'DVR']"
}
```
**Response 400**:
```json
{
  "status": 400,
  "message": "File name is required"
}
```
**Response 400**:
```json
{
  "status": 400,
  "message": "File size exceeds 100MB limit"
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
  "message": "Retrieved 1 analytics successfully",
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
  "message": "Contact correlation analysis completed",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "owner_name": "testing 1",
        "phone_number": "085827384234"
      },
      {
        "device_label": "Device B",
        "owner_name": "testing 2",
        "phone_number": "085827384234"
      }
    ],
    "correlations": [
      {
        "contact_number": "628123456789",
        "devices_found_in": [
          {
            "device_label": "Device A",
            "contact_name": "Zagoto"
          },
          {
            "device_label": "Device B",
            "contact_name": "Bang Goto Intek"
          }
        ]
      },
      {
        "contact_number": "628987654321",
        "devices_found_in": [
          {
            "device_label": "Device A",
            "contact_name": "Doyo"
          },
          {
            "device_label": "Device B",
            "contact_name": "Bang Purwo Intek"
          }
        ]
      }
    ]
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
  "message": "Retrieved deep communication data for analytic 'testing' successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "testing",
    "total_devices": 2,
    "devices": [
      {
        "device_id": 1,
        "device_name": "testing 1 Device",
        "owner_name": "testing 1",
        "phone_number": "085827384234"
      },
      {
        "device_id": 2,
        "device_name": "testing 2 Device",
        "owner_name": "testing 2",
        "phone_number": "085827384234"
      }
    ],
    "correlations": [
      {
        "device_id": 1,
        "platforms": {
          "facebook_messenger": [
            {
              "peer": "Ifa <100051336874335>",
              "thread_id": "acb0b0ccb8fb9d92922e1a08143f7aee",
              "intensity": 2,
              "first_timestamp": "2020-05-15 08:58:47",
              "last_timestamp": "2020-05-15 08:59:02",
              "platform": "facebook_messenger"
            },
          ],
          "telegram": [
            {
              "peer": "Unknown",
              "thread_id": "1d368997e3e44ee43f4092ed76902d5d",
              "intensity": 5,
              "first_timestamp": "2020-10-22 11:41:58",
              "last_timestamp": "2021-01-18 16:22:17",
              "platform": "telegram"
            }
          ],
          "whatsapp_messenger": [
            {
              "peer": "Fahrul Rohman <6289652052405>",
              "thread_id": "71ad16fbfdd52f47c404e39461cf9fb9",
              "intensity": 2135,
              "first_timestamp": "2020-08-09 09:13:44",
              "last_timestamp": "2021-02-04 05:51:25",
              "platform": "whatsapp_messenger"
            },
          ],
          "x_(twitter)": [
            {
              "peer": "myXLCare <480224156>",
              "thread_id": "2f653f9fac77434964444ab2468af3eb",
              "intensity": 10,
              "first_timestamp": "2019-10-28 06:57:38",
              "last_timestamp": "2020-05-12 05:32:48",
              "platform": "x_(twitter)"
            }
          ],
          "instagram": [],
          "tiktok": []
        }
      },
      {
        "device_id": 2,
        "platforms": {
          "facebook_messenger": [
            {
              "peer": "Ifa <100051336874335>",
              "thread_id": "acb0b0ccb8fb9d92922e1a08143f7aee",
              "intensity": 2,
              "first_timestamp": "2020-05-15 08:58:47",
              "last_timestamp": "2020-05-15 08:59:02",
              "platform": "facebook_messenger"
            },
          ],
          "telegram": [
            {
              "peer": "Unknown",
              "thread_id": "1d368997e3e44ee43f4092ed76902d5d",
              "intensity": 5,
              "first_timestamp": "2020-10-22 11:41:58",
              "last_timestamp": "2021-01-18 16:22:17",
              "platform": "telegram"
            }
          ],
          "whatsapp_messenger": [
            {
              "peer": "Fahrul Rohman <6289652052405>",
              "thread_id": "71ad16fbfdd52f47c404e39461cf9fb9",
              "intensity": 2135,
              "first_timestamp": "2020-08-09 09:13:44",
              "last_timestamp": "2021-02-04 05:51:25",
              "platform": "whatsapp_messenger"
            },
          ],
          "x_(twitter)": [
            {
              "peer": "myXLCare <480224156>",
              "thread_id": "2f653f9fac77434964444ab2468af3eb",
              "intensity": 10,
              "first_timestamp": "2019-10-28 06:57:38",
              "last_timestamp": "2020-05-12 05:32:48",
              "platform": "x_(twitter)"
            }
          ],
          "instagram": [],
          "tiktok": []
        }
      }
    ]
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
  "message": "Success",
  "data": [
    {
      "id": 1392,
      "timestamp": "2020-05-12 05:05:16",
      "direction": "Outgoing",
      "sender": "Riko Suloyo <1130597879284883457>",
      "receiver": "myXLCare <480224156>",
      "text": "lokasi tempat tinggal? di bandung",
      "type": "Twitter message",
      "source": "X (Twitter)"
    },
    {
      "id": 1395,
      "timestamp": "2020-05-12 05:32:24",
      "direction": "Incoming",
      "sender": "myXLCare <480224156>",
      "receiver": "Riko Suloyo <1130597879284883457>",
      "text": "Untuk informasinya sudah cukup jelas ya :) Thanks #M31",
      "type": "Twitter message",
      "source": "X (Twitter)"
    },
  ]
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
        "device_label": "Device A",
        "owner_name": "dwi arya",
        "phone_number": "08518731231123"
      },
      {
        "device_label": "Device B",
        "owner_name": "dwi arya 2",
        "phone_number": "08518731231123"
      },
      {
        "device_label": "Device C",
        "owner_name": "dwi ",
        "phone_number": "08518731231123"
      }
    ],
    "hashfiles": [
      
      {
        "hash_value": "4352d88a78aa39750bf70cd6f27bcaa5",
        "file_name": "Oxygen iPhone - Hashfile MD5.xls",
        "file_type": "Other files",
        "file_size": "167.5 KB",
        "file_path": "/Macintosh HD/Users/macbookair/Workdir/Projects/digifor-clean/data/uploads/data/Oxygen iPhone - Hashfile MD5.xls",
        "created_at": "2025-10-28T11:17:16",
        "modified_at": "2025-10-28T11:17:16",
        "devices": [
          "Device A",
          "Device B",
          "Device C"
        ],
        "general_info": {
          "kind": "Microsoft Excel 97-2004 Workbook (.xls)",
          "size": "171.520 (167.5 KB on disk)",
          "where": "/Macintosh HD/Users/macbookair/Workdir/Projects/digifor-clean/data/uploads/data/Oxygen iPhone - Hashfile MD5.xls",
          "created": "2025 10 28 11:17:16",
          "modified": "2025 10 28 11:17:16",
          "stationery_pad": false,
          "locked": false
        }
      },
      {
        "hash_value": "295de6aae44d7a8c4b8e3f50c8b6941a",
        "file_name": "Oxygen iPhone - Hashfile MD5.xls",
        "file_type": "Images (WEBP)",
        "file_size": "167.5 KB",
        "file_path": "/Macintosh HD/Users/macbookair/Workdir/Projects/digifor-clean/data/uploads/data/Oxygen iPhone - Hashfile MD5.xls",
        "created_at": "2025-10-28T11:17:16",
        "modified_at": "2025-10-28T11:17:16",
        "devices": [
          "Device A",
          "Device C"
        ],
        "general_info": {
          "kind": "Microsoft Excel 97-2004 Workbook (.xls)",
          "size": "171.520 (167.5 KB on disk)",
          "where": "/Macintosh HD/Users/macbookair/Workdir/Projects/digifor-clean/data/uploads/data/Oxygen iPhone - Hashfile MD5.xls",
          "created": "2025 10 28 11:17:16",
          "modified": "2025 10 28 11:17:16",
          "stationery_pad": false,
          "locked": false
        }
      },
    ],
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


## 7. APK Analytics

### 7.1 Get APK Analytics
**Endpoint**: `GET /api/v1/analytics/{analytic_id}/apk-analytic`

**Parameters**:
- `analytic_id` (path): Analytics ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "analytic_name": "testing 3",
    "method": "APK Analytics",
    "malware_scoring": "47",
    "permissions": [
      {
        "id": 2,
        "item": "android.permission.SCHEDULE_EXACT_ALARM",
        "status": "normal",
        "description": "Allows an app to use exact alarm scheduling APIs to perform timing sensitive background work."
      },
      {
        "id": 1,
        "item": "easy.sudoku.puzzle.solver.free.permission.C2D_MESSAGE",
        "status": "unknown",
        "description": "Unknown permission from android reference"
      }
    ]
  }
}
```

### 7.2 Analyze APK 
**Endpoint**: `POST /api/v1/analytics/analyze-apk`

**Parameters**:
- `analytic_id` (path): Analytics ID (required)
- `file_id` (path): File ID (required)

**Response 200**:
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "analytic_name": "Analytic 1",
    "method": "APK Analytics",
    "malware_scoring": "47",
    "permissions": [
      {
        "id": 1,
        "item": "easy.sudoku.puzzle.solver.free.permission.C2D_MESSAGE",
        "status": "unknown",
        "description": "Unknown permission from android reference"
      },
      {
        "id": 2,
        "item": "android.permission.SCHEDULE_EXACT_ALARM",
        "status": "normal",
        "description": "Allows an app to use exact alarm scheduling APIs to perform timing sensitive background work."
      },
    ]
  }
}
```

---
## 8. Error Responses

### 8.1 Common Error Responses

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

## 9. Workflow Examples

### 9.1 Complete Analytics Workflow

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

## 10. Notes

- All timestamps are in ISO 8601 format
- Device IDs must exist in the database
- Hashfile analytics only shows files that appear on at least 2 devices
- PDF exports are generated with timestamp in filename
- Summary can be saved multiple times (updates existing)
- All analytics support universal summary and PDF export
- File uploads support various forensic tool formats

---

*Last updated: 2025-10-23*