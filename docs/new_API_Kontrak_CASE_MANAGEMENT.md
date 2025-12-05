# API Contract - Case Management, Evidence Management, Suspect Management, Person Management, Auth, and User Management

## Base URLs
```
/api/v1/cases          - Case Management
/api/v1/evidence       - Evidence Management
/api/v1/suspects       - Suspect Management
/api/v1/persons        - Person Management
/api/v1/auth           - Authentication
/api/v1/users          - User Management
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

### 1. Create Case

**Endpoint:** `POST /create-case`

**Description:** Creates a new case. Case number will be auto-generated if not provided.

**Request Body:**
```json
{
  "case_number": "CASE-2025-001",  // Optional - will auto-generate if not provided (min 3 characters)
  "title": "Case Title",
  "description": "Case description",  // Optional
  "main_investigator": "John Doe",
  "agency_id": 1,  // Optional - either agency_id or agency_name
  "work_unit_id": 1,  // Optional - either work_unit_id or work_unit_name
  "agency_name": "Agency Name",  // Optional - manual input
  "work_unit_name": "Work Unit Name"  // Optional - manual input
}
```

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Case created successfully",
  "data": {
    "id": 1,
    "case_number": "CASE-2025-001",
    "title": "Case Title",
    "description": "Case description",
    "status": "Open",
    "main_investigator": "John Doe",
    "agency_name": "Agency Name",
    "work_unit_name": "Work Unit Name",
    "created_at": "05/01/2025",
    "updated_at": "05/01/2025"
  }
}
```

**Error Responses:**

**400 - Invalid Case Number:**
```json
{
  "status": 400,
  "detail": "Case number must be at least 3 characters long"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while creating case. Please try again later."
}
```

---

### 2. Get Case Detail Comprehensive

**Endpoint:** `GET /get-case-detail-comprehensive/{case_id}`

**Description:** Retrieves comprehensive case details including persons, evidence, logs, and summary.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Case detail retrieved successfully",
  "data": {
    "id": 1,
    "case_number": "CASE-2025-001",
    "title": "Case Title",
    "description": "Case description",
    "status": "Open",
    "main_investigator": "John Doe",
    "agency_name": "Agency Name",
    "work_unit_name": "Work Unit Name",
    "created_at": "05/01/2025",
    "updated_at": "05/01/2025",
    "persons": [
      {
        "id": 1,
        "name": "Person Name",
        "person_type": "Suspect",
        "analysis": []
      }
    ],
    "evidence": [],
    "logs": [],
    "summary": {
      "total_persons": 1,
      "total_evidence": 0
    }
  }
}
```

**Error Responses:**

**404 - Case Not Found:**
```json
{
  "status": 404,
  "detail": "Case with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving case details. Please try again later."
}
```

**Note:** If the error message contains "not found", the response will be 404 with detail "Case with ID {case_id} not found".

---

### 3. Get All Cases

**Endpoint:** `GET /get-all-cases`

**Description:** Retrieves a paginated list of cases with optional filtering and search.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Number of records to skip (default: 0, min: 0) |
| `limit` | integer | No | Number of records to return (default: 10, min: 1, max: 100) |
| `search` | string | No | Search term for case number, title, or description (max 255 characters) |
| `status` | string | No | Filter by case status: `Open`, `Closed`, `Re-open` (max 50 characters) |
| `sort_by` | string | No | Field to sort by. Valid values: `created_at`, `id` |
| `sort_order` | string | No | Sort order. Valid values: `asc` (oldest first), `desc` (newest first) |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Cases retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_number": "CASE-2025-001",
      "title": "Case Title",
      "description": "Case description",
      "status": "Open",
      "main_investigator": "John Doe",
      "agency_name": "Agency Name",
      "work_unit_name": "Work Unit Name",
      "created_at": "05/01/2025",
      "updated_at": "05/01/2025"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

**Error Responses:**

**400 - Invalid Search Parameter:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code."
}
```

**400 - Invalid Status Parameter:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in status parameter. Please remove any SQL injection attempts or malicious code."
}
```

**400 - Invalid Sort By:**
```json
{
  "status": 400,
  "detail": "Invalid sort_by value. Valid values are: 'created_at', 'id'"
}
```

**400 - Invalid Sort Order:**
```json
{
  "status": 400,
  "detail": "Invalid sort_order value. Valid values are: 'asc', 'desc'"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "Unexpected server error, please try again later"
}
```

---

### 4. Update Case

**Endpoint:** `PUT /update-case/{case_id}`

**Description:** Updates an existing case. All fields are optional.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID |

**Request Body:**
```json
{
  "case_number": "CASE-2025-001-UPDATED",  // Optional
  "title": "Updated Case Title",  // Optional
  "description": "Updated description",  // Optional
  "main_investigator": "Jane Doe",  // Optional
  "agency_id": 2,  // Optional
  "work_unit_id": 2,  // Optional
  "agency_name": "Updated Agency",  // Optional
  "work_unit_name": "Updated Work Unit",  // Optional
  "notes": "Update notes"  // Optional
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Case updated successfully",
  "data": {
    "id": 1,
    "case_number": "CASE-2025-001-UPDATED",
    "title": "Updated Case Title",
    "description": "Updated description",
    "status": "Open",
    "main_investigator": "Jane Doe",
    "agency_name": "Updated Agency",
    "work_unit_name": "Updated Work Unit",
    "created_at": "05/01/2025",
    "updated_at": "05/01/2025"
  }
}
```

**Error Responses:**

**404 - Case Not Found:**
```json
{
  "status": 404,
  "detail": "Case with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "Unexpected server error, please try again later"
}
```

---

### 5. Get Case Statistics

**Endpoint:** `GET /statistics/summary`

**Description:** Retrieves case statistics summary.

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Statistics retrieved successfully",
  "data": {
    "open_cases": 5,
    "closed_cases": 3,
    "reopened_cases": 1
  },
  "total_cases": 9
}
```

**Error Responses:**

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "Unexpected server error, please try again later"
}
```

---

### 6. Save Case Notes

**Endpoint:** `POST /save-notes`

**Description:** Saves notes for a case.

**Request Body:**
```json
{
  "case_id": 1,
  "notes": "Case notes text"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Case notes saved successfully",
  "data": {
    "case_id": 1,
    "notes": "Case notes text"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Invalid input data. Please check your request and try again.",
  "data": null
}
```

**404 - Case Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to save case notes. Please try again later.",
  "data": null
}
```

---

### 7. Edit Case Notes

**Endpoint:** `PUT /edit-notes`

**Description:** Updates existing case notes.

**Request Body:**
```json
{
  "case_id": 1,
  "notes": "Updated case notes text"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Case notes updated successfully",
  "data": {
    "case_id": 1,
    "notes": "Updated case notes text"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Invalid input data. Please check your request and try again.",
  "data": null
}
```

**404 - Case Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to edit case notes. Please try again later.",
  "data": null
}
```

---

### 8. Export Case Details PDF

**Endpoint:** `GET /export-case-details-pdf/{case_id}`

**Description:** Exports case details as a PDF file.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID |

**Success Response (200):**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename=case_details_{case_id}.pdf`
- Returns PDF file as binary data

**Error Responses:**

**404 - Case Not Found:**
```json
{
  "status": 404,
  "detail": "Case with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "Failed to export case detail PDF. Please try again later."
}
```

---

## Evidence Management Endpoints

### 9. Get Evidence List

**Endpoint:** `GET /evidence/get-evidence-list`

**Description:** Retrieves a paginated list of evidence with optional filtering and search.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Number of records to skip (default: 0, min: 0) |
| `limit` | integer | No | Number of records to return (default: 10, min: 1, max: 100) |
| `search` | string | No | Search term for evidence number, title, or description (max 255 characters) |
| `sort_by` | string | No | Field to sort by. Valid values: `created_at`, `id` |
| `sort_order` | string | No | Sort order. Valid values: `asc` (oldest first), `desc` (newest first) |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Evidence list retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_id": 1,
      "evidence_number": "EVID-001",
      "title": "Case Title",
      "investigator": "John Doe",
      "agency": "Agency Name",
      "created_at": "05/01/2025"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code."
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving evidence list. Please try again later."
}
```

---

### 10. Get Evidence Summary

**Endpoint:** `GET /evidence/get-evidence-summary`

**Description:** Retrieves evidence statistics summary.

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Evidence summary retrieved successfully",
  "data": {
    "total_evidence": 10,
    "total_cases": 5
  }
}
```

**Error Responses:**

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving evidence summary. Please try again later."
}
```

---

### 11. Create Evidence

**Endpoint:** `POST /evidence/create-evidence`

**Description:** Creates a new evidence record. Can optionally create a linked suspect/person.

**Request:**
- **Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID |
| `evidence_number` | string | No | Evidence number (auto-generated if not provided) |
| `title` | string | No | Evidence title |
| `source` | string | No | Evidence source (max 100 characters) |
| `evidence_file` | file | No | Evidence file (PDF or image formats) |
| `evidence_summary` | string | No | Evidence summary/description (max 1000 characters) |
| `investigator` | string | Yes | Investigator name (max 100 characters) |
| `person_name` | string | No | Person name if creating linked person (max 255 characters) |
| `suspect_status` | string | No | Suspect status if creating linked person. Valid values: `Witness`, `Reported`, `Suspected`, `Suspect`, `Defendant` |
| `is_unknown_person` | boolean | No | Whether person is unknown (default: false) |
| `suspect_id` | integer | No | Existing suspect ID to link |

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Evidence created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "EVID-001",
    "source": "Handphone",
    "file_path": "/path/to/file",
    "description": "Evidence description",
    "title": "Case Title",
    "investigator": "John Doe",
    "agency": "Agency Name",
    "person_name": "John Doe",
    "created_at": "05/01/2025"
  }
}
```

**Error Responses:**

**400 - Invalid File Name:**
```json
{
  "status": 400,
  "detail": "Invalid file name. File name contains dangerous characters."
}
```

**400 - Invalid File Type:**
```json
{
  "status": 400,
  "detail": "File type tidak didukung. Hanya file PDF dan Image yang diperbolehkan (extensions: pdf, jpg, jpeg, png, gif, bmp, webp)"
}
```

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code."
}
```

**404 - Case Not Found:**
```json
{
  "status": 404,
  "detail": "Case with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while creating evidence. Please try again later."
}
```

---

### 12. Get Evidence Detail

**Endpoint:** `GET /evidence/{evidence_id}/detail`

**Description:** Retrieves detailed information about a specific evidence.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Evidence detail retrieved successfully",
  "data": {
    "id": 1,
    "evidence_number": "EVID-001",
    "title": "Evidence Title",
    "description": "Evidence description",
    "source": "Handphone",
    "case_id": 1,
    "suspect_id": 1,
    "file_path": "/path/to/file",
    "file_size": 1024,
    "investigator": "John Doe",
    "created_at": "2025-01-05T10:30:00",
    "updated_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "detail": "Evidence with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving evidence detail. Please try again later."
}
```

---

### 13. Export Evidence Detail PDF

**Endpoint:** `GET /evidence/export-evidence-detail-pdf/{evidence_id}`

**Description:** Exports evidence details as a PDF file.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Success Response (200):**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename=evidence_detail_{evidence_id}.pdf`
- Returns PDF file as binary data

**Error Responses:**

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "detail": "Evidence with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "Failed to export evidence detail PDF. Please try again later."
}
```

---

### 14. Update Evidence

**Endpoint:** `PUT /evidence/update-evidence/{evidence_id}`

**Description:** Updates an existing evidence record. All fields are optional.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Request:**
- **Content-Type:** `multipart/form-data`

**Parameters:** (All optional)
| Parameter | Type | Description |
|-----------|------|-------------|
| `case_id` | integer | Case ID |
| `evidence_number` | string | Evidence number |
| `title` | string | Evidence title |
| `type` | string | Evidence type |
| `source` | string | Evidence source (max 100 characters) |
| `evidence_file` | file | Evidence file (PDF or image formats) |
| `evidence_summary` | string | Evidence summary/description (max 1000 characters) |
| `investigator` | string | Investigator name (max 100 characters) |
| `person_name` | string | Person name if creating linked person (max 255 characters) |
| `suspect_status` | string | Suspect status if creating linked person |
| `is_unknown_person` | boolean | Whether person is unknown |
| `suspect_id` | integer | Existing suspect ID to link |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Evidence updated successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "EVID-001",
    "source": "Handphone",
    "description": "Updated description",
    "title": "Updated Title",
    "investigator": "Jane Doe",
    "created_at": "05/01/2025"
  }
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code."
}
```

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "detail": "Evidence with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while updating evidence. Please try again later."
}
```

---

### 15. Save Evidence Notes

**Endpoint:** `POST /evidence/save-notes`

**Description:** Saves notes for an evidence.

**Request Body:**
```json
{
  "evidence_id": 1,
  "notes": {
    "text": "Evidence notes text",
    "additional_info": "Additional information"
  }
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Evidence notes saved successfully",
  "data": {
    "evidence_id": 1,
    "evidence_number": "EVID-001",
    "evidence_title": "Evidence Title",
    "notes": {
      "text": "Evidence notes text",
      "additional_info": "Additional information"
    },
    "updated_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Notes cannot be empty and must be a JSON object",
  "data": null
}
```

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while saving evidence notes. Please try again later.",
  "data": null
}
```

---

### 16. Edit Evidence Notes

**Endpoint:** `PUT /evidence/edit-notes`

**Description:** Updates existing evidence notes.

**Request Body:**
```json
{
  "evidence_id": 1,
  "notes": {
    "text": "Updated evidence notes text",
    "additional_info": "Updated additional information"
  }
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Evidence notes updated successfully",
  "data": {
    "evidence_id": 1,
    "evidence_number": "EVID-001",
    "evidence_title": "Evidence Title",
    "notes": {
      "text": "Updated evidence notes text",
      "additional_info": "Updated additional information"
    },
    "updated_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Notes cannot be empty and must be a JSON object",
  "data": null
}
```

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while editing evidence notes. Please try again later.",
  "data": null
}
```

---

### 17. Download Custody File

**Endpoint:** `GET /evidence/custody/download-file`

**Description:** Downloads a custody-related file.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Path to the file to download |

**Success Response (200):**
- **Content-Type:** Based on file type
- **Content-Disposition:** `attachment; filename={filename}`
- Returns file as binary data

**Error Responses:**

**404 - File Not Found:**
```json
{
  "status": 404,
  "detail": "File not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while downloading file. Please try again later."
}
```

---

### 18. Get Custody Logs

**Endpoint:** `GET /evidence/{evidence_id}/custody-logs`

**Description:** Retrieves custody logs for a specific evidence.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Custody logs retrieved successfully",
  "data": [
    {
      "id": 1,
      "custody_type": "Acquisition",
      "notes": "Custody log notes",
      "created_at": "2025-01-05T10:30:00",
      "created_by": "John Doe"
    }
  ]
}
```

**Error Responses:**

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "detail": "Evidence with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving custody logs. Please try again later."
}
```

---

### 19. Get Custody Chain

**Endpoint:** `GET /evidence/{evidence_id}/custody`

**Description:** Retrieves the complete custody chain for a specific evidence.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Custody chain retrieved successfully",
  "data": {
    "evidence_id": 1,
    "evidence_number": "EVID-001",
    "custody_chain": [
      {
        "stage": "Acquisition",
        "timestamp": "2025-01-05T10:30:00",
        "handler": "John Doe",
        "notes": "Acquisition notes"
      }
    ]
  }
}
```

**Error Responses:**

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "detail": "Evidence with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving custody chain. Please try again later."
}
```

---

### 20. Create Custody Acquisition

**Endpoint:** `POST /evidence/{evidence_id}/custody/acquisition`

**Description:** Creates a custody acquisition record.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Request Body:**
```json
{
  "handler_name": "John Doe",
  "handler_signature": "base64_encoded_signature",
  "location": "Location",
  "notes": "Acquisition notes"
}
```

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Custody acquisition created successfully",
  "data": {
    "id": 1,
    "custody_type": "Acquisition",
    "handler_name": "John Doe",
    "location": "Location",
    "notes": "Acquisition notes",
    "created_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Invalid input data. Please check your request and try again.",
  "data": null
}
```

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while creating custody acquisition. Please try again later.",
  "data": null
}
```

---

### 21. Create Custody Preparation

**Endpoint:** `POST /evidence/{evidence_id}/custody/preparation`

**Description:** Creates a custody preparation record.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Request Body:**
```json
{
  "handler_name": "John Doe",
  "handler_signature": "base64_encoded_signature",
  "location": "Location",
  "notes": "Preparation notes"
}
```

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Custody preparation created successfully",
  "data": {
    "id": 1,
    "custody_type": "Preparation",
    "handler_name": "John Doe",
    "location": "Location",
    "notes": "Preparation notes",
    "created_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Invalid input data. Please check your request and try again.",
  "data": null
}
```

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while creating custody preparation. Please try again later.",
  "data": null
}
```

---

### 22. Create Custody Extraction

**Endpoint:** `POST /evidence/{evidence_id}/custody/extraction`

**Description:** Creates a custody extraction record.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Request Body:**
```json
{
  "handler_name": "John Doe",
  "handler_signature": "base64_encoded_signature",
  "location": "Location",
  "notes": "Extraction notes"
}
```

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Custody extraction created successfully",
  "data": {
    "id": 1,
    "custody_type": "Extraction",
    "handler_name": "John Doe",
    "location": "Location",
    "notes": "Extraction notes",
    "created_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Invalid input data. Please check your request and try again.",
  "data": null
}
```

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while creating custody extraction. Please try again later.",
  "data": null
}
```

---

### 23. Create Custody Analysis

**Endpoint:** `POST /evidence/{evidence_id}/custody/analysis`

**Description:** Creates a custody analysis record.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |

**Request Body:**
```json
{
  "handler_name": "John Doe",
  "handler_signature": "base64_encoded_signature",
  "location": "Location",
  "notes": "Analysis notes"
}
```

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Custody analysis created successfully",
  "data": {
    "id": 1,
    "custody_type": "Analysis",
    "handler_name": "John Doe",
    "location": "Location",
    "notes": "Analysis notes",
    "created_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Invalid input data. Please check your request and try again.",
  "data": null
}
```

**404 - Evidence Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while creating custody analysis. Please try again later.",
  "data": null
}
```

---

### 24. Update Custody Report Notes

**Endpoint:** `PUT /evidence/{evidence_id}/custody/{report_id}/notes`

**Description:** Updates notes for a specific custody report.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Evidence ID |
| `report_id` | integer | Yes | Custody report ID |

**Request Body:**
```json
{
  "notes": "Updated custody report notes"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Custody report notes updated successfully",
  "data": {
    "id": 1,
    "custody_type": "Acquisition",
    "notes": "Updated custody report notes",
    "updated_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - Validation Error:**
```json
{
  "status": 400,
  "message": "Invalid input data. Please check your request and try again.",
  "data": null
}
```

**404 - Evidence or Report Not Found:**
```json
{
  "status": 404,
  "message": "Evidence or custody report not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred while updating custody report notes. Please try again later.",
  "data": null
}
```

---

## Suspect Management Endpoints

### 25. Get Suspects List

**Endpoint:** `GET /suspects/`

**Description:** Retrieves a paginated list of suspects with optional filtering and search.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Number of records to skip (default: 0, min: 0) |
| `limit` | integer | No | Number of records to return (default: 10, min: 1, max: 100) |
| `search` | string | No | Search term for suspect name (max 255 characters) |
| `status` | string[] | No | Filter by suspect status. Can be multiple values: `Witness`, `Reported`, `Suspected`, `Suspect`, `Defendant` |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Suspects retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "status": "Suspect",
      "case_id": 1,
      "case_name": "Case Title",
      "evidence_number": "EVID-001",
      "evidence_source": "Handphone",
      "investigator": "Jane Doe",
      "created_at": "2025-01-05T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code."
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving suspects. Please try again later."
}
```

---

### 26. Get Suspect Summary

**Endpoint:** `GET /suspects/get-suspect-summary`

**Description:** Retrieves suspect statistics summary.

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Suspect summary retrieved successfully",
  "data": {
    "total_person": 10,
    "total_evidence": 20
  }
}
```

**Error Responses:**

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving suspects. Please try again later."
}
```

---

### 27. Create Suspect

**Endpoint:** `POST /suspects/create-suspect`

**Description:** Creates a new suspect record. Can optionally create a linked evidence.

**Request:**
- **Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID |
| `person_name` | string | No | Person name (required if `is_unknown_person` is false, max 255 characters) |
| `is_unknown_person` | string | No | Whether person is unknown ("true" or "false") |
| `suspect_status` | string | No | Suspect status. Valid values: `Witness`, `Reported`, `Suspected`, `Suspect`, `Defendant` (required if `is_unknown_person` is false) |
| `evidence_number` | string | No | Evidence number (auto-generated if not provided) |
| `evidence_source` | string | No | Evidence source (max 100 characters) |
| `evidence_file` | file | No | Evidence file (PDF or image formats) |
| `evidence_summary` | string | No | Evidence summary/description (max 1000 characters) |
| `case_name` | string | No | Case name |

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Suspect created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "name": "John Doe",
    "status": "Suspect",
    "evidence_number": "EVID-001",
    "evidence_source": "Handphone",
    "investigator": "Jane Doe",
    "created_by": "Admin",
    "created_at": "2025-01-05T10:30:00",
    "updated_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code."
}
```

**400 - Invalid Suspect Status:**
```json
{
  "status": 400,
  "detail": "Invalid suspect_status value: 'Invalid'. Valid values are: Witness, Reported, Suspected, Suspect, Defendant"
}
```

**404 - Case Not Found:**
```json
{
  "status": 404,
  "detail": "Case with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while creating suspect. Please try again later."
}
```

---

### 28. Get Suspect Detail

**Endpoint:** `GET /suspects/get-suspect-detail/{suspect_id}`

**Description:** Retrieves detailed information about a specific suspect.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Suspect ID |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Suspect detail retrieved successfully",
  "data": {
    "id": 1,
    "name": "John Doe",
    "status": "Suspect",
    "case_id": 1,
    "case_name": "Case Title",
    "evidence_number": "EVID-001",
    "evidence_source": "Handphone",
    "investigator": "Jane Doe",
    "notes": "Suspect notes",
    "created_at": "2025-01-05T10:30:00",
    "updated_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**404 - Suspect Not Found:**
```json
{
  "status": 404,
  "detail": "Suspect with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while retrieving suspect detail. Please try again later."
}
```

---

### 29. Export Suspect Detail PDF

**Endpoint:** `GET /suspects/export-suspect-detail-pdf/{suspect_id}`

**Description:** Exports suspect details as a PDF file.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Suspect ID |

**Success Response (200):**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename=suspect_detail_{suspect_id}.pdf`
- Returns PDF file as binary data

**Error Responses:**

**404 - Suspect Not Found:**
```json
{
  "status": 404,
  "detail": "Suspect with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "Failed to export suspect detail PDF. Please try again later."
}
```

---

### 30. Update Suspect

**Endpoint:** `PUT /suspects/update-suspect/{suspect_id}`

**Description:** Updates an existing suspect record. All fields are optional.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Suspect ID |

**Request:**
- **Content-Type:** `multipart/form-data`

**Parameters:** (All optional)
| Parameter | Type | Description |
|-----------|------|-------------|
| `person_name` | string | Person name (max 255 characters) |
| `suspect_status` | string | Suspect status. Valid values: `Witness`, `Reported`, `Suspected`, `Suspect`, `Defendant` |
| `is_unknown_person` | boolean | Whether person is unknown |
| `notes` | string | Suspect notes |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Suspect updated successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "name": "John Doe",
    "status": "Suspect",
    "evidence_number": "EVID-001",
    "evidence_source": "Handphone",
    "investigator": "Jane Doe",
    "created_by": "Admin",
    "created_at": "2025-01-05T10:30:00",
    "updated_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code."
}
```

**404 - Suspect Not Found:**
```json
{
  "status": 404,
  "detail": "Suspect with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while updating suspect. Please try again later."
}
```

---

### 31. Save Suspect Notes

**Endpoint:** `POST /suspects/save-suspect-notes/{suspect_id}`

**Description:** Saves notes for a suspect.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Suspect ID |

**Request Body:**
```json
{
  "notes": "Suspect notes text"
}
```

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Suspect notes saved successfully",
  "data": {
    "suspect_id": 1,
    "notes": "Suspect notes text"
  }
}
```

**Error Responses:**

**400 - Notes Already Exist:**
```json
{
  "status": 400,
  "message": "Notes already exist for this suspect. Use PUT /edit-suspect-notes/{suspect_id} to update.",
  "data": null
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this case",
  "data": null
}
```

**404 - Suspect Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

---

### 32. Edit Suspect Notes

**Endpoint:** `PUT /suspects/edit-suspect-notes/{suspect_id}`

**Description:** Updates existing suspect notes.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Suspect ID |

**Request Body:**
```json
{
  "notes": "Updated suspect notes text"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Suspect notes updated successfully",
  "data": {
    "suspect_id": 1,
    "notes": "Updated suspect notes text"
  }
}
```

**Error Responses:**

**400 - No Notes Found:**
```json
{
  "status": 400,
  "message": "No notes found for this suspect. Use POST /save-suspect-notes/{suspect_id} to create notes.",
  "data": null
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this case",
  "data": null
}
```

**404 - Suspect Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

---

## Person Management Endpoints

### 33. Create Person

**Endpoint:** `POST /persons/create-person`

**Description:** Creates a new person record. Can optionally create a linked evidence.

**Request:**
- **Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID |
| `person_name` | string | No | Person name (required if `is_unknown_person` is false, max 255 characters) |
| `suspect_status` | string | No | Suspect status. Valid values: `Witness`, `Reported`, `Suspected`, `Suspect`, `Defendant` (required if `is_unknown_person` is false) |
| `evidence_number` | string | No | Evidence number (auto-generated if not provided) |
| `evidence_source` | string | No | Evidence source (max 100 characters) |
| `evidence_file` | file | No | Evidence file (PDF or image formats) |
| `evidence_summary` | string | No | Evidence summary/description (max 1000 characters) |
| `is_unknown_person` | boolean | No | Whether person is unknown (default: false) |

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Person created successfully",
  "data": {
    "id": 3,
    "case_id": 1,
    "name": "John Doe",
    "suspect_status": "Reported",
    "evidence_number": "438343040304",
    "evidence_source": "Handphone",
    "evidence_summary": "Evidence summary text",
    "investigator": "Jojo Sikumbang",
    "created_by": "Admin Forensic",
    "created_at": "2025-12-05T21:02:16.542064+07:00",
    "updated_at": "2025-12-05T21:02:16.542510+07:00"
  }
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code."
}
```

**400 - Invalid File Name:**
```json
{
  "status": 400,
  "detail": "Invalid file name. File name contains dangerous characters."
}
```

**400 - Invalid File Type:**
```json
{
  "status": 400,
  "detail": "File type tidak didukung. Hanya file PDF dan Image yang diperbolehkan (extensions: pdf, jpg, jpeg, png, gif, bmp, webp)"
}
```

**404 - Case Not Found:**
```json
{
  "status": 404,
  "detail": "Case with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while creating person. Please try again later."
}
```

---

### 34. Update Person

**Endpoint:** `PUT /persons/update-person/{person_id}`

**Description:** Updates an existing person record. All fields are optional.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | integer | Yes | Person ID |

**Request:**
- **Content-Type:** `multipart/form-data`

**Parameters:** (All optional)
| Parameter | Type | Description |
|-----------|------|-------------|
| `person_name` | string | Person name (max 255 characters) |
| `suspect_status` | string | Suspect status. Valid values: `Witness`, `Reported`, `Suspected`, `Suspect`, `Defendant` |
| `is_unknown_person` | boolean | Whether person is unknown |
| `notes` | string | Person notes |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Person updated successfully",
  "data": {
    "id": 3,
    "case_id": 1,
    "name": "John Doe",
    "suspect_status": "Reported",
    "evidence_number": "438343040304",
    "evidence_source": "Handphone",
    "investigator": "Jojo Sikumbang",
    "created_by": "Admin Forensic",
    "created_at": "2025-12-05T21:02:16.542064+07:00",
    "updated_at": "2025-12-05T21:02:16.542510+07:00"
  }
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "detail": "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code."
}
```

**404 - Person Not Found:**
```json
{
  "status": 404,
  "detail": "Person with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while creating person. Please try again later."
}
```

---

### 35. Delete Person

**Endpoint:** `DELETE /persons/delete-person/{person_id}`

**Description:** Deletes a person record.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | integer | Yes | Person ID |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Person deleted successfully"
}
```

**Error Responses:**

**404 - Person Not Found:**
```json
{
  "status": 404,
  "detail": "Person with ID 1 not found"
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "detail": "An unexpected error occurred while creating person. Please try again later."
}
```

---

### 36. Save Suspect Notes (Person)

**Endpoint:** `POST /persons/save-suspect-notes/{suspect_id}`

**Description:** Saves notes for a suspect (via person management).

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Suspect ID |

**Request Body:**
```json
{
  "notes": "Suspect notes text"
}
```

**Success Response (201):**
```json
{
  "status": 201,
  "message": "Suspect notes saved successfully",
  "data": {
    "suspect_id": 1,
    "notes": "Suspect notes text"
  }
}
```

**Error Responses:**

**400 - Notes Already Exist:**
```json
{
  "status": 400,
  "message": "Notes already exist for this suspect. Use PUT /edit-suspect-notes/{suspect_id} to update.",
  "data": null
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this case",
  "data": null
}
```

**404 - Suspect Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

---

### 37. Edit Suspect Notes (Person)

**Endpoint:** `PUT /persons/edit-suspect-notes/{suspect_id}`

**Description:** Updates existing suspect notes (via person management).

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Suspect ID |

**Request Body:**
```json
{
  "notes": "Updated suspect notes text"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Suspect notes updated successfully",
  "data": {
    "suspect_id": 1,
    "notes": "Updated suspect notes text"
  }
}
```

**Error Responses:**

**400 - No Notes Found:**
```json
{
  "status": 400,
  "message": "No notes found for this suspect. Use POST /save-suspect-notes/{suspect_id} to create notes.",
  "data": null
}
```

**403 - Access Denied:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this case",
  "data": null
}
```

**404 - Suspect Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID 1 not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

---

## Authentication Endpoints

### 38. Login

**Endpoint:** `POST /auth/login`

**Description:** Authenticates a user and returns access and refresh tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "fullname": "John Doe",
      "tag": "Investigator",
      "role": "user"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_string"
  }
}
```

**Error Responses:**

**400 - Email Required:**
```json
{
  "status": 400,
  "message": "Email is required",
  "data": null
}
```

**400 - Password Required:**
```json
{
  "status": 400,
  "message": "Password is required",
  "data": null
}
```

**400 - Invalid Email Format:**
```json
{
  "status": 400,
  "message": "Invalid email format",
  "data": null
}
```

**400 - Password Too Short:**
```json
{
  "status": 400,
  "message": "Password must be at least 8 characters long",
  "data": null
}
```

**400 - Password Too Long:**
```json
{
  "status": 400,
  "message": "Password must not exceed 128 characters",
  "data": null
}
```

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in email. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**401 - Invalid Credentials:**
```json
{
  "status": 401,
  "message": "Invalid credentials",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

---

### 39. Refresh Token

**Endpoint:** `POST /auth/refresh`

**Description:** Refreshes an access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "refresh_token_string"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "new_refresh_token_string"
  }
}
```

**Error Responses:**

**400 - Refresh Token Required:**
```json
{
  "status": 400,
  "message": "Refresh token is required",
  "data": null
}
```

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in refresh_token. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**401 - Invalid Refresh Token:**
```json
{
  "status": 401,
  "message": "Invalid or expired refresh token",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

---

### 40. Get Current User Profile

**Endpoint:** `GET /auth/me`

**Description:** Retrieves the current authenticated user's profile.

**Success Response (200):**
```json
{
  "status": 200,
  "message": "User profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "fullname": "John Doe",
    "tag": "Investigator",
    "role": "user",
    "password": ""
  }
}
```

**Error Responses:**

**401 - Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid credentials",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve user profile",
  "data": null
}
```

---

### 41. Logout

**Endpoint:** `POST /auth/logout`

**Description:** Logs out the current user by blacklisting the refresh token.

**Request Body:**
```json
{
  "refresh_token": "refresh_token_string"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Logout successful",
  "data": null
}
```

**Error Responses:**

**400 - Refresh Token Required:**
```json
{
  "status": 400,
  "message": "Refresh token is required",
  "data": null
}
```

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in refresh_token. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "An unexpected error occurred. Please try again later.",
  "data": null
}
```

---

## User Management Endpoints

### 42. Get All Users

**Endpoint:** `GET /users/get-all-users`

**Description:** Retrieves a paginated list of users. Admin only.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Number of records to skip (default: 0, min: 0) |
| `limit` | integer | No | Number of records to return (default: 10, min: 1, max: 100) |
| `search` | string | No | Search keyword (searches in name, email, max 255 characters) |
| `tag` | string | No | Filter by tag: `Admin`, `Investigator`, `Ahli Forensic` |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "Users retrieved successfully",
  "data": [
    {
      "id": 1,
      "fullname": "John Doe",
      "email": "user@example.com",
      "role": "user",
      "tag": "Investigator",
      "is_active": true,
      "created_at": "2025-01-05T10:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**403 - Forbidden:**
```json
{
  "status": 403,
  "message": "Forbidden - Admin access required",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve users",
  "data": null
}
```

---

### 43. Create User

**Endpoint:** `POST /users/create-user`

**Description:** Creates a new user. Admin only.

**Request Body:**
```json
{
  "fullname": "John Doe",
  "email": "user@example.com",
  "password": "password123",
  "confirm_password": "password123",
  "tag": "Investigator",
  "role": "user"
}
```

**Success Response (201):**
```json
{
  "status": 201,
  "message": "User created successfully",
  "data": {
    "id": 1,
    "fullname": "John Doe",
    "email": "user@example.com",
    "role": "user",
    "tag": "Investigator",
    "is_active": true,
    "created_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**400 - Password Mismatch:**
```json
{
  "status": 400,
  "message": "Password and confirm password do not match",
  "data": null
}
```

**400 - Email Already Exists:**
```json
{
  "status": 400,
  "message": "Email already registered",
  "data": null
}
```

**403 - Forbidden:**
```json
{
  "status": 403,
  "message": "Forbidden - Admin access required",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to create user",
  "data": null
}
```

---

### 44. Update User

**Endpoint:** `PUT /users/update-user/{user_id}`

**Description:** Updates an existing user. Admin only.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

**Request Body:**
```json
{
  "fullname": "John Doe Updated",
  "email": "user@example.com",
  "password": "newpassword123",
  "confirm_password": "newpassword123",
  "tag": "Investigator",
  "role": "user"
}
```

**Success Response (200):**
```json
{
  "status": 200,
  "message": "User updated successfully",
  "data": {
    "id": 1,
    "fullname": "John Doe Updated",
    "email": "user@example.com",
    "role": "user",
    "tag": "Investigator",
    "is_active": true,
    "updated_at": "2025-01-05T10:30:00"
  }
}
```

**Error Responses:**

**400 - SQL Injection Detected:**
```json
{
  "status": 400,
  "message": "Invalid characters detected in [field]. Please remove any SQL injection attempts or malicious code.",
  "data": null
}
```

**400 - Password Mismatch:**
```json
{
  "status": 400,
  "message": "Password and confirm password do not match",
  "data": null
}
```

**403 - Forbidden:**
```json
{
  "status": 403,
  "message": "Forbidden - Admin access required",
  "data": null
}
```

**404 - User Not Found:**
```json
{
  "status": 404,
  "message": "User not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to update user",
  "data": null
}
```

---

### 45. Delete User

**Endpoint:** `DELETE /users/delete-user/{user_id}`

**Description:** Deletes a user. Admin only.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID |

**Success Response (200):**
```json
{
  "status": 200,
  "message": "User deleted successfully",
  "data": null
}
```

**Error Responses:**

**403 - Forbidden:**
```json
{
  "status": 403,
  "message": "Forbidden - Admin access required",
  "data": null
}
```

**404 - User Not Found:**
```json
{
  "status": 404,
  "message": "User not found",
  "data": null
}
```

**500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to delete user",
  "data": null
}
```

---

## Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input or validation error |
| 401 | Unauthorized - Missing or invalid authentication token |
| 403 | Forbidden - User does not have permission to access the resource |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Unexpected server error |

---

## Additional Notes

1. **Authentication:** All endpoints (except `/auth/login` and `/auth/refresh`) require a valid Bearer token in the Authorization header.

2. **Admin Access:** User Management endpoints require admin role.

3. **File Uploads:** Evidence and Person endpoints support file uploads. Allowed file types:
   - PDF files
   - Image files: jpg, jpeg, png, gif, bmp, webp

4. **Suspect Status Values:**
   - `Witness` - Person is a witness
   - `Reported` - Person has been reported
   - `Suspected` - Person is suspected
   - `Suspect` - Person is a suspect
   - `Defendant` - Person is a defendant

5. **Data Format:** All responses use `"data": null` for error cases or when no data is available (not empty arrays).

6. **Error Messages:** All error messages are in English and do not expose technical details to prevent information leakage.

7. **SQL Injection Protection:** All input parameters are validated and sanitized to prevent SQL injection attacks.

8. **Path Traversal Protection:** All file names are validated to prevent path traversal attacks.

9. **Password Requirements:**
   - Minimum 8 characters
   - Maximum 128 characters

10. **Email Validation:** Email addresses are validated for proper format and sanitized.

11. **Pagination:** 
    - Default page size: 10
    - Maximum page size: 100
    - Page number is calculated as `skip // limit + 1`

12. **Date Format:** All dates in responses are formatted as `DD/MM/YYYY` or ISO 8601 format for timestamps.

13. **Security Validation:**
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
    - Case Management: 20 validations
    - Evidence Management: 26 validations
    - Suspect Management: 10 validations
    - Person Management: 9 validations
    - Analytics Device: 3 validations
    - Analytics Management: 5 validations
    - Analytics File: 8 validations
    - **Total: 81 SQL injection validations across all endpoints**


| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input or validation error |
| 401 | Unauthorized - Missing or invalid authentication token |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Unexpected server error |

---

## Data Models

### Case Status Values
- `Open` - Case is currently open
- `Closed` - Case has been closed
- `Re-open` - Case has been reopened

### Case Notes Request
```json
{
  "case_id": integer,  // Required
  "notes": string      // Required
}
```

### Case Create Request
```json
{
  "case_number": string,           // Optional (min 3 characters if provided)
  "title": string,                  // Required
  "description": string,            // Optional
  "main_investigator": string,     // Required
  "agency_id": integer | string,   // Optional
  "work_unit_id": integer | string, // Optional
  "agency_name": string,           // Optional
  "work_unit_name": string         // Optional
}
```

### Case Update Request
All fields are optional:
```json
{
  "case_number": string,
  "title": string,
  "description": string,
  "main_investigator": string,
  "agency_id": integer,
  "work_unit_id": integer,
  "agency_name": string,
  "work_unit_name": string,
  "notes": string
}
```

---

## Notes

1. **Authentication:** All endpoints require a valid Bearer token in the Authorization header.

2. **Case Number:** 
   - If not provided, will be auto-generated
   - If provided, must be at least 3 characters long
   - Must be unique

3. **Agency and Work Unit:**
   - Can be provided either by `agency_id`/`work_unit_id` (from database) or `agency_name`/`work_unit_name` (manual input)
   - If both are provided, ID takes precedence

4. **Date Format:** All dates in responses are formatted as `DD/MM/YYYY`

5. **Pagination:** 
   - Default page size: 10
   - Maximum page size: 100
   - Page number is calculated as `skip // limit + 1`

6. **Search:** Searches across case number, title, and description fields (case-insensitive)

7. **Sorting:** 
   - Default sort: by `created_at` descending (newest first)
   - Valid sort fields: `created_at`, `id`
   - Valid sort orders: `asc`, `desc`

8. **Data Format:** All responses use `"data": null` for error cases or when no data is available (not empty arrays).

9. **Error Messages:** All error messages are in English and do not expose technical details to prevent information leakage.

10. **SQL Injection Protection:** All search, status, sort_by, and sort_order parameters are validated and sanitized to prevent SQL injection attacks.

