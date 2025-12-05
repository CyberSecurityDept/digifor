# API Contract - Analytics Management

## Base URL
```
/api/v1
```

## Authentication
All endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Request Headers

### Required Headers

All authenticated endpoints require the following header:

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | Bearer token for authentication. Format: `Bearer <access_token>` |

**Example:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Content-Type Headers

Different endpoints require different Content-Type headers:

| Endpoint Type | Content-Type | Description |
|---------------|--------------|-------------|
| JSON Request Body | `application/json` | For endpoints that accept JSON in request body |
| Form Data Upload | `multipart/form-data` | For endpoints that accept file uploads or form data |
| Query Parameters | Not required | For GET endpoints with query parameters |

**Examples:**

**JSON Request:**
```
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Form Data Upload:**
```
Content-Type: multipart/form-data
Authorization: Bearer <access_token>
```

**Query Parameters (GET):**
```
Authorization: Bearer <access_token>
```

### Optional Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Accept` | string | No | Expected response format. Default: `application/json` |
| `Content-Length` | integer | No | Automatically set by HTTP client for POST/PUT requests |

---

## Endpoints

### 1. Create Analytic with Devices

**Endpoint:** `POST /analytics/start-analyzing`

**Description:** Creates a new analytic with specified method.

**Request:**
- **Content-Type:** `multipart/form-data` or `application/x-www-form-urlencoded`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_name` | string | Yes | Name of the analytic (max 255 characters) |
| `method` | string | Yes | Analytic method. Must be one of: `Deep Communication Analytics`, `Social Media Correlation`, `Contact Correlation`, `APK Analytics`, `Hashfile Analytics` |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Analytics created successfully",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "My Analytic",
      "method": "Hashfile Analytics",
      "summary": null,
      "created_at": "2025-01-05 10:30:00"
    }
  }
}
```

**Error Responses:**

**400 - Empty Analytic Name:**
```json
{
  "status": 400,
  "message": "analytic_name wajib diisi",
  "data": null
}
```

**400 - SQL Injection Detected in Analytic Name:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in analytic_name. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**400 - SQL Injection Detected in Method:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in method. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**400 - Invalid Method:**
```json
{
  "status": 400,
  "message": "Invalid method. Must be one of: ['Deep Communication Analytics', 'Social Media Correlation', 'Contact Correlation', 'APK Analytics', 'Hashfile Analytics']",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to create analytic. Please try again later.",
  "data": null
}
```

---

### 2. Get Hashfile Analytics

**Endpoint:** `GET /analytics/hashfile-analytics`

**Description:** Retrieves hashfile correlation analytics for a specific analytic ID. Requires minimum 2 devices.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | ID of the analytic |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Hashfile correlation completed successfully",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "owner_name": "John Doe",
        "phone_number": "+1234567890"
      },
      {
        "device_label": "Device B",
        "owner_name": "Jane Smith",
        "phone_number": "+0987654321"
      }
    ],
    "correlations": [
      {
        "hash_value": "abc123def456...",
        "file_name": "document.pdf",
        "file_type": "PDF",
        "devices": ["Device A", "Device B"]
      }
    ],
    "summary": "Analytic summary text",
    "total_correlations": 1
  }
}
```

**Error Responses:**

**400 - Wrong Method:**
```json
{
  "status": 400,
  "message": "This endpoint is only for Hashfile Analytics. Current method: 'Contact Correlation'",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "My Analytic",
      "current_method": "Contact Correlation"
    },
    "next_action": "create_analytic",
    "redirect_to": "/analytics/start-analyzing",
    "instruction": "Please create a new analytic with method 'Hashfile Analytics'"
  }
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 - Analytic Not Found:**
```json
{
  "status": 404,
  "message": "Analytic with ID 1 not found",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Unknown"
    },
    "next_action": "create_analytic",
    "redirect_to": "/analytics/start-analyzing",
    "instruction": "Please create a new analytic with method 'Hashfile Analytics'"
  }
}
```

**404 - No Devices:**
```json
{
  "status": 404,
  "message": "No devices linked to this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "My Analytic"
    },
    "device_count": 0,
    "required_minimum": 2,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "Please add at least 2 devices to continue with Hashfile Analytics"
  }
}
```

**404 - Insufficient Devices:**
```json
{
  "status": 404,
  "message": "Hashfile Analytics requires minimum 2 devices. Current analytic has 1 device(s).",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "My Analytic"
    },
    "device_count": 1,
    "required_minimum": 2,
    "next_action": "add_device",
    "redirect_to": "/analytics/devices",
    "instruction": "Please add at least 2 devices to continue with Hashfile Analytics"
  }
}
```

**200 - No Hashfile Data:**
```json
{
  "status": 200,
  "message": "No hashfile data found",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "owner_name": "John Doe",
        "phone_number": "+1234567890"
      }
    ],
    "correlations": [],
    "summary": null,
    "total_correlations": 0
  }
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve hashfile analytics. Please try again later.",
  "data": null
}
```

---

### 3. Start Data Extraction

**Endpoint:** `POST /analytics/start-extraction`

**Description:** Starts data extraction process for an analytic. Requires minimum 2 devices.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | ID of the analytic |

**Success Response (200):**

**For Contact Correlation:**
```json
{
  "status": 200,
  "message": "Data extraction completed Contact Correlation",
  "data": {
    "analytic_id": 1,
    "method": "Contact Correlation",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytic/1/contact-correlation"
  }
}
```

**For Hashfile Analytics:**
```json
{
  "status": 200,
  "message": "Data extraction completed Hashfile Analytics",
  "data": {
    "analytic_id": 1,
    "method": "Hashfile Analytics",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytic/1/hashfile-analytics"
  }
}
```

**For Deep Communication Analytics:**
```json
{
  "status": 200,
  "message": "Data extraction completed Deep Communication Analytics",
  "data": {
    "analytic_id": 1,
    "method": "Deep Communication Analytics",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytic/deep-communication-analytics?analytic_id=1"
  }
}
```

**For Social Media Correlation:**
```json
{
  "status": 200,
  "message": "Data extraction completed Social Media Correlation",
  "data": {
    "analytic_id": 1,
    "method": "Social Media Correlation",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytics/social-media-correlation?analytic_id=1"
  }
}
```

**Error Responses:**

**400 - Insufficient Devices:**
```json
{
  "status": 400,
  "message": "Minimum 2 devices required. Currently have 1 device(s)",
  "data": {
    "device_count": 1,
    "required": 2
  }
}
```

**400 - Unsupported Method:**
```json
{
  "status": 400,
  "message": "Unsupported method: APK Analytics. Supported methods: Contact Correlation, Hashfile Analytics, Deep Communication Analytics, Social Media Correlation",
  "data": null
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 - Analytic Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to start data extraction. Please try again later.",
  "data": null
}
```

---

### 4. Get All Analytics

**Endpoint:** `GET /analytics/get-all-analytic`

**Description:** Retrieves all analytics with optional filtering and search. Non-admin users can only see analytics they created or are associated with.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | string | No | Search by analytics name, method, or notes (summary) (max 255 characters) |
| `method` | string[] | No | Filter by one or more methods. Can be comma-separated or multiple query params |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Retrieved 2 analytics successfully",
  "data": [
    {
      "id": 1,
      "analytic_name": "My Analytic",
      "method": "Hashfile Analytics",
      "summary": "Analytic summary",
      "date": "05/01/2025"
    },
    {
      "id": 2,
      "analytic_name": "Another Analytic",
      "method": "Contact Correlation",
      "summary": null,
      "date": "04/01/2025"
    }
  ]
}
```

**Error Responses:**

**400 - SQL Injection Detected in Search:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**400 - SQL Injection Detected in Method:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in method parameter. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve data. Please try again later.",
  "data": null
}
```

---

### 5. Upload Data File

**Endpoint:** `POST /analytics/upload-data`

**Description:** Uploads a data file for analytics processing. Supports various forensic tool formats (Cellebrite, Oxygen, Magnet Axiom, Encase) and methods (Deep Communication Analytics, Social Media Correlation, Contact Correlation, Hashfile Analytics).

**Request:**
- **Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | The file to upload (Excel, CSV, TXT, SDP formats) |
| `file_name` | string | Yes | Name of the file (max 255 characters, validated for path traversal) |
| `notes` | string | No | Optional notes about the file (max 1000 characters) |
| `type` | string | Yes | Device type. Must be one of: `Handphone`, `SSD`, `Harddisk`, `PC`, `Laptop`, `DVR` |
| `tools` | string | Yes | Forensic tool. Must be one of: `Cellebrite`, `Oxygen`, `Magnet Axiom`, `Encase` |
| `method` | string | Yes | Analytic method. Must be one of: `Deep Communication Analytics`, `Social Media Correlation`, `Contact Correlation`, `Hashfile Analytics` |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Upload initialized successfully",
  "data": {
    "file_id": null,
    "upload_id": "upload_1764743980_61e7001a",
    "status_upload": "Pending",
    "upload_type": "data"
  }
}
```

**Error Responses:**

**400 - Invalid File Name:**
```json
{
  "status": 400,
  "message": "Invalid file name. File name contains dangerous characters.",
  "data": null
}
```

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in file_name. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Upload error occurred. Please try again later.",
  "data": null
}
```

---

### 6. Get Upload Progress

**Endpoint:** `GET /analytics/upload-progress`

**Description:** Retrieves the progress status of an ongoing file upload.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `upload_id` | string | Yes | Upload ID returned from upload endpoint |
| `type` | string | No | Upload type: `data` (default) or `apk` |

**Success Response (200):**

**For In Progress:**
```json
{
  "status": "Progress",
  "message": "Upload Progress",
  "upload_id": "upload_1764743980_61e7001a",
  "file_name": "example.xlsx",
  "size": "10.5 MB",
  "percentage": 45,
  "upload_status": "Progress",
  "data": null
}
```

**For Completed:**
```json
{
  "status": "Completed",
  "message": "Upload completed successfully",
  "upload_id": "upload_1764743980_61e7001a",
  "file_name": "example.xlsx",
  "size": "10.5 MB",
  "percentage": 100,
  "upload_status": "Completed",
  "data": {
    "file_id": 123,
    "file_name": "example.xlsx",
    "method": "Hashfile Analytics",
    "tools": "Cellebrite"
  }
}
```

**For Failed (Tool/Method Mismatch):**
```json
{
  "status": "Failed",
  "message": "File upload failed. Please upload this file using Tools Cellebrite with method Hashfile Analytics",
  "upload_id": "upload_1764743980_61e7001a",
  "file_name": "example.xlsx",
  "size": "File upload failed. Please upload this file using Tools Cellebrite with method Hashfile Analytics",
  "percentage": "Error",
  "upload_status": "Failed",
  "data": null
}
```

**For Failed (No Data Found):**
```json
{
  "status": "Failed",
  "message": "Hashfile Analytics data not found in file. The file format is correct (Cellebrite with Hashfile Analytics method), but no hash data exists in this file.",
  "upload_id": "upload_1764743980_61e7001a",
  "file_name": "example.xlsx",
  "size": "Hashfile Analytics data not found in file. The file format is correct (Cellebrite with Hashfile Analytics method), but no hash data exists in this file.",
  "percentage": "Error",
  "upload_status": "Failed",
  "data": null
}
```

**Error Responses:**

**404 - Upload Not Found:**
```json
{
  "status": 404,
  "message": "Upload not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while checking upload progress. Please try again later.",
  "data": null
}
```

---

### 7. Get Files

**Endpoint:** `GET /analytics/get-files`

**Description:** Retrieves a list of uploaded files with optional filtering and search. Non-admin users can only see files they uploaded.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | string | No | Search by file_name, notes, tools, or method (max 255 characters) |
| `filter` | string | No | Filter by method. Valid values: `Deep Communication Analytics`, `Social Media Correlation`, `Contact Correlation`, `Hashfile Analytics`, `All` (default) |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Files retrieved successfully",
  "data": [
    {
      "id": 1,
      "file_name": "example.xlsx",
      "notes": "File notes",
      "tools": "Cellebrite",
      "method": "Hashfile Analytics",
      "type": "Handphone",
      "created_at": "2025-01-05 10:30:00",
      "created_by": "user@example.com"
    }
  ],
  "total": 1
}
```

**Error Responses:**

**400 - SQL Injection Detected in Search:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**400 - SQL Injection Detected in Filter:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in filter parameter. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve files. Please try again later.",
  "data": null
}
```

---

### 8. Add Device

**Endpoint:** `POST /analytics/add-device`

**Description:** Links a file to an analytic as a device. The file method must match the analytic method.

**Request:**
- **Content-Type:** `multipart/form-data` or `application/x-www-form-urlencoded`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | integer | Yes | ID of the uploaded file |
| `analytic_id` | integer | Yes | ID of the analytic |
| `name` | string | Yes | Device owner name (max 255 characters) |
| `phone_number` | string | Yes | Device phone number (max 50 characters) |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Device added successfully",
  "data": {
    "device_id": 1,
    "file_id": 123,
    "analytic_id": 1,
    "owner_name": "John Doe",
    "phone_number": "+1234567890"
  }
}
```

**Error Responses:**

**400 - Method Mismatch:**
```json
{
  "status": 400,
  "message": "File method 'Contact Correlation' does not match analytic method 'Hashfile Analytics'",
  "data": null
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 - Analytic Not Found:**
```json
{
  "status": 404,
  "message": "Analytic with ID 1 not found",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Unknown"
    },
    "next_action": "create_analytic",
    "redirect_to": "/analytics/start-analyzing",
    "instruction": "The specified analytic was not found. Please create a new analytic."
  }
}
```

**404 - File Not Found:**
```json
{
  "status": 404,
  "message": "File not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to add device. Please try again later.",
  "data": null
}
```

---

### 9. Get Devices

**Endpoint:** `GET /analytics/get-devices`

**Description:** Retrieves all devices linked to a specific analytic.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | ID of the analytic |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Devices retrieved successfully",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "My Analytic",
      "method": "Hashfile Analytics"
    },
    "devices": [
      {
        "id": 1,
        "owner_name": "John Doe",
        "phone_number": "+1234567890",
        "file_id": 123,
        "file_name": "example.xlsx"
      }
    ],
    "total_devices": 1
  }
}
```

**Success Response (200) - No Devices:**
```json
{
  "status": 200,
  "message": "No devices linked to this analytic yet",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "My Analytic",
      "method": "Hashfile Analytics"
    },
    "devices": [],
    "total_devices": 0
  }
}
```

**Error Responses:**

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 - Analytic Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve devices. Please try again later.",
  "data": null
}
```

---

### 10. Upload APK File

**Endpoint:** `POST /analytics/upload-apk`

**Description:** Uploads an APK or IPA file for analysis.

**Request:**
- **Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | APK or IPA file to upload |
| `file_name` | string | Yes | Name of the file |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Upload initialized successfully",
  "data": {
    "file_id": null,
    "upload_id": "upload_1764743980_61e7001a",
    "status_upload": "Pending",
    "upload_type": "apk"
  }
}
```

**Error Responses:**

**400 - Invalid File Type:**
```json
{
  "status": 400,
  "message": "Invalid file type. Only ['apk', 'ipa'] allowed.",
  "data": null
}
```

**422 - Missing File Name:**
```json
{
  "status": 422,
  "message": "Field 'file_name' is required",
  "error_field": "file_name",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Upload error occurred. Please try again later.",
  "data": null
}
```

---

### 11. Analyze APK

**Endpoint:** `POST /analytics/analyze-apk`

**Description:** Analyzes an uploaded APK file for security permissions and malware scoring.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | integer | Yes | ID of the uploaded APK file |
| `analytic_id` | integer | Yes | ID of the analytic (must have method "APK Analytics") |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "analytic_name": "My APK Analytic",
    "method": "APK Analytics",
    "status": "scanned",
    "malware_scoring": "75",
    "file_size": "5.2 MB",
    "permissions": [
      {
        "id": 1,
        "item": "android.permission.INTERNET",
        "status": "normal",
        "description": "Allows app to access internet"
      }
    ],
    "summary": "Analytic summary"
  }
}
```

**Error Responses:**

**400 - Wrong Analytic Method:**
```json
{
  "status": 400,
  "message": "Wrong Analytic Method",
  "data": null
}
```

**400 - Invalid Analysis Result:**
```json
{
  "status": 400,
  "message": "Invalid analysis result",
  "data": null
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "Forbidden",
  "data": null
}
```

**404 - Analytics Not Found:**
```json
{
  "status": 404,
  "message": "Analytics Not Found",
  "data": null
}
```

**404 - File Not Found:**
```json
{
  "status": 404,
  "message": "File Not Found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while retrieving APK analysis. Please try again later.",
  "data": null
}
```

---

### 12. Get APK Analysis

**Endpoint:** `GET /analytics/apk-analytic`

**Description:** Retrieves APK analysis results for a specific analytic.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | ID of the analytic (must have method "APK Analytics") |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "analytic_name": "My APK Analytic",
    "method": "APK Analytics",
    "status": "scanned",
    "malware_scoring": "75",
    "file_size": "5.2 MB",
    "file_id": 123,
    "permissions": [
      {
        "id": 1,
        "item": "android.permission.INTERNET",
        "status": "normal",
        "description": "Allows app to access internet"
      }
    ],
    "summary": "Analytic summary"
  }
}
```

**Error Responses:**

**400 - Wrong Method:**
```json
{
  "status": 400,
  "message": "Wrong Method",
  "data": null
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "Forbidden",
  "data": null
}
```

**404 - Analytic Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**404 - No APK Analysis Found:**
```json
{
  "status": 404,
  "message": "No APK analysis found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while retrieving APK analysis. Please try again later.",
  "data": null
}
```

---

### 13. Store Analytic File

**Endpoint:** `POST /analytics/store-analytic-file`

**Description:** Links an uploaded file to an analytic for APK Analytics.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | ID of the analytic |
| `file_id` | integer | Yes | ID of the uploaded file |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "File linked successfully",
  "data": {
    "id": 1,
    "analytic_id": 1,
    "file_id": 123,
    "status": "pending",
    "file_size": "5.2 MB"
  }
}
```

**Success Response (200) - Already Exists:**
```json
{
  "status": 200,
  "message": "Already exists",
  "data": {
    "id": 1,
    "analytic_id": 1,
    "file_id": 123,
    "status": "pending",
    "file_size": "5.2 MB"
  }
}
```

**Error Responses:**

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "Forbidden",
  "data": null
}
```

**404 - Analytic Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**404 - File Not Found:**
```json
{
  "status": 404,
  "message": "File not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while storing analytic file. Please try again later.",
  "data": null
}
```

---

## Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input or validation error |
| 401 | Unauthorized - Missing or invalid authentication token |
| 403 | Forbidden - User does not have permission to access the resource |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error (e.g., missing required field) |
| 500 | Internal Server Error - Unexpected server error |

---

## Notes

1. **Authentication:** All endpoints require a valid Bearer token in the Authorization header.

2. **Access Control:** 
   - Admin users can access all analytics and files
   - Non-admin users can only access analytics/files where their name or email appears in `analytic_name`, `summary`, `created_by`, `notes`, or `file_name` fields

3. **Method Validation:** The `method` parameter must be exactly one of the valid methods (case-sensitive):
   - `Deep Communication Analytics`
   - `Social Media Correlation`
   - `Contact Correlation`
   - `APK Analytics`
   - `Hashfile Analytics`

4. **Tool Validation:** The `tools` parameter must be exactly one of the valid tools (case-sensitive):
   - `Cellebrite`
   - `Oxygen`
   - `Magnet Axiom`
   - `Encase`

5. **Device Type Validation:** The `type` parameter must be exactly one of the valid types (case-sensitive):
   - `Handphone`
   - `SSD`
   - `Harddisk`
   - `PC`
   - `Laptop`
   - `DVR`

6. **Device Requirements:** Hashfile Analytics and data extraction require minimum 2 devices to be linked to the analytic.

7. **File Format Detection:** The system automatically detects the correct tool and method based on file structure. If the user's selection doesn't match, the error message will redirect to the correct tool and method.

8. **Upload Progress:** Use the `upload_id` returned from upload endpoints to check progress via `/analytics/upload-progress`.

9. **Data Format:** All responses use `"data": null` for error cases or when no data is available (not empty arrays).

10. **Error Messages:** All error messages are in English and do not expose technical details to prevent information leakage.

11. **Security Validation:**
    - **SQL Injection Protection:** All string inputs (Form fields, Query parameters, Request body) are validated using `validate_sql_injection_patterns()` to detect and prevent SQL injection attempts.
    - **Input Sanitization:** All validated inputs are sanitized using `sanitize_input()` with appropriate `max_length` constraints based on database schema.
    - **File Name Validation:** All file uploads are validated using `validate_file_name()` to prevent path traversal attacks.
    - **List Input Sanitization:** Array/list inputs are sanitized using `sanitize_list_input()`.
    - **Nested Data Validation:** For complex data structures (e.g., JSON objects in notes), all string values are validated recursively.
    - **Error Messages:** When SQL injection patterns are detected, the API returns a 400 status with message: "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code."
    
    **Protected Input Types:**
    - All Form fields (multipart/form-data)
    - All Query parameters
    - All Request body fields (JSON)
    - All file names in uploads
    - All nested string values in complex objects
    
    **Validation Coverage:**
    - Analytics Management: 5 validations
    - Analytics File: 8 validations
    - Analytics Device: 3 validations
    - **Total: 16 SQL injection validations across analytics endpoints**

11. **SQL Injection Protection:** All input parameters are validated and sanitized to prevent SQL injection attacks.

12. **Path Traversal Protection:** All file names are validated to prevent path traversal attacks.
