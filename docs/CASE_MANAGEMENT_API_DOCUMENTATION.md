# Case Management API Documentation

## Overview
This document provides comprehensive API documentation for the Case Management system endpoints. The API is built with FastAPI and follows RESTful conventions.

## Base URL
```
/api/v1/cases
```

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <access_token>
```

---

## Available Endpoints

### 1. Create Case
**Endpoint:** `POST /api/v1/cases/create-case`

**Description:** Create a new case with agency and work unit information. Supports both auto-generated and manual case numbers.

#### Option 1: Auto-Generate Case Number (Recommended)
**Request Body:**
```json
{
  "title": "Buronan Maroko Interpol",
  "description": "Case description...",
  "main_investigator": "Solehun",
  "agency_id": 1,
  "work_unit_id": 1,
  "agency_name": "Trikora agency",
  "work_unit_name": "Dirjen Imigrasi 1"
}
```

#### Option 2: Manual Case Number
**Request Body:**
```json
{
  "case_number": "CASE-2024-001",
  "title": "Buronan Maroko Interpol",
  "description": "Case description...",
  "main_investigator": "Solehun",
  "agency_id": 1,
  "work_unit_id": 1,
  "agency_name": "Trikora agency",
  "work_unit_name": "Dirjen Imigrasi 1"
}
```

**Notes:** 
- Field `status` tidak perlu disertakan dalam request body karena akan otomatis diset ke "Open" saat case pertama kali dibuat.
- Field `case_number` bersifat opsional:
  - **Jika tidak disertakan**: Akan otomatis di-generate menggunakan format `{INITIALS}-{DATE}-{ID}` 
    - `INITIALS`: Huruf pertama dari setiap kata dalam title (maksimal 3 kata)
    - `DATE`: Tanggal saat ini dalam format DDMMYY
    - `ID`: Case ID dengan padding 4 digit
    - **Contoh**: "Buronan Maroko Interpol" → "BMI-061025-0001"
  - **Jika disertakan**: Akan menggunakan case number yang diberikan (minimum 3 karakter, harus unik)

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Case created successfully",
  "data": {
    "id": 1,
    "case_number": "BMI-061025-0001",
    "title": "Buronan Maroko Interpol",
    "description": "Case description...",
    "status": "Open",
    "main_investigator": "Solehun",
    "agency_name": "Trikora agency",
    "work_unit_name": "Dirjen Imigrasi 1",
    "created_at": "2024-12-02T00:00:00Z",
    "updated_at": "2024-12-02T00:00:00Z"
  }
}
```

**Response (409 Conflict - Duplicate Case Number):**
```json
{
  "detail": "Case number 'BMI-061025-0001' already exists"
}
```

**Response (400 Bad Request - Invalid Case Number):**
```json
{
  "detail": [
    {
      "loc": ["body", "case_number"],
      "msg": "Case number must be at least 3 characters long",
      "type": "value_error"
    }
  ]
}
```

### 2. Get Case Detail Comprehensive
**Endpoint:** `GET /api/v1/cases/get-case-detail-comprehensive/{case_id}`

**Description:** Get comprehensive case details including persons, evidence, logs, and notes.

**Path Parameters:**
- `case_id` (integer): The ID of the case to retrieve

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case detail retrieved successfully",
  "data": {
    "case": {
      "id": 1,
      "case_number": "CASE-2024-0001",
      "title": "Buronan Maroko Interpol",
      "status": "Closed",
      "case_officer": "Solehun",
      "created_date": "12/02/2025",
      "agency": "Trikora agency",
      "work_unit": "Dirjen Imigrasi 1",
      "description": "Emily Johnson, the plaintiff, filed a lawsuit against Acme Corporation for negligence and breach of warranty related to a defective blender. The malfunction caused severe lacerations to her hand during use."
    },
    "persons_of_interest": [
      {
        "id": 1,
        "name": "Rafi ahmad",
        "person_type": "Suspect",
        "analysis": [
          {
            "evidence_id": "32342223",
            "summary": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian",
            "status": "Analysis"
          },
          {
            "evidence_id": "32342223",
            "summary": "Terdapat dialog seputar pembakaran dengan suspect lain",
            "status": "Analysis"
          }
        ]
      },
      {
        "id": 2,
        "name": "Nathalie",
        "person_type": "Suspect",
        "analysis": [
          {
            "evidence_id": "32342223",
            "summary": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian",
            "status": "Analysis"
          },
          {
            "evidence_id": "32342223",
            "summary": "Terdapat dialog seputar pembakaran dengan suspect lain",
            "status": "Analysis"
          }
        ]
      }
    ],
    "case_log": [
      {
        "status": "Re-Open",
        "timestamp": "16 Mei 2024, 08:12",
        "description": "Re-open",
        "notes": "tersangka kemungkinan kerabat dari pelaku utama"
      },
      {
        "status": "Edit",
        "timestamp": "16 Mei 2024, 08:12",
        "description": "Adding Person: Nathalie"
      },
      {
        "status": "Edit",
        "timestamp": "16 Mei 2024, 08:12",
        "description": "Adding Evidence: 32342223, Description change"
      },
      {
        "status": "Closed",
        "timestamp": "12 Mei 2024, 15:23",
        "description": "Kasus ini memiliki indikasi adanya tersangka tambahan"
      },
      {
        "status": "Open",
        "timestamp": "17 Feb 2024, 09:12",
        "description": "Initial case created"
      }
    ],
    "notes": [
      {
        "timestamp": "12 Mei 2024, 15:23",
        "status": "Closed",
        "content": "Kasus ini memiliki indikasi adanya tersangka tambahan"
      },
      {
        "timestamp": "16 Mei 2024, 08:12",
        "status": "Re-Open",
        "content": "tersangka kemungkinan kerabat dari pelaku utama"
      }
    ],
    "summary": {
      "total_persons": 2,
      "total_evidence": 4
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Case with ID 1 not found"
}
```

### 3. Get All Cases
**Endpoint:** `GET /api/v1/cases/get-all-cases`

**Description:** Retrieve paginated list of cases with filtering options.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0, minimum: 0)
- `limit` (integer, optional): Number of records to return (default: 10, minimum: 1, maximum: 100)
- `search` (string, optional): Search in title, case number, or description
- `status` (string, optional): Filter by case status (Open, Closed, Re-open)

**Request:**
```http
GET /api/v1/cases/get-all-cases?skip=0&limit=10&search=maroko&status=Open
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Cases retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_number": "BMI-061025-0001",
      "title": "Buronan Maroko Interpol",
      "description": "Case description...",
      "status": "Open",
      "main_investigator": "Solehun",
      "agency_name": "Trikora agency",
      "work_unit_name": "Dirjen Imigrasi 1",
      "created_at": "2024-12-02T00:00:00Z",
      "updated_at": "2024-12-02T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

### 4. Update Case
**Endpoint:** `PUT /api/v1/cases/update-case/{case_id}`

**Description:** Update case information.

**Path Parameters:**
- `case_id` (integer): The ID of the case to update

**Request Body:**
```json
{
  "title": "Updated Case Title",
  "description": "Updated description",
  "main_investigator": "New Investigator",
  "agency_id": 2,
  "work_unit_id": 2
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case updated successfully",
  "data": {
    "id": 1,
    "case_number": "BMI-061025-0001",
    "title": "Updated Case Title",
    "description": "Updated description",
    "status": "Open",
    "main_investigator": "New Investigator",
    "agency_name": "New Agency",
    "work_unit_name": "New Work Unit",
    "created_at": "2024-12-02T00:00:00Z",
    "updated_at": "2024-12-02T10:30:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Case with ID 1 not found"
}
```

### 5. Delete Case
**Endpoint:** `DELETE /api/v1/cases/delete-case/{case_id}`

**Description:** Delete a case and all related data (cascade delete).

**Path Parameters:**
- `case_id` (integer): The ID of the case to delete

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case deleted successfully"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Case with ID 1 not found"
}
```

### 6. Get Case Statistics
**Endpoint:** `GET /api/v1/cases/statistics/summary`

**Description:** Get case statistics for dashboard.

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Statistics retrieved successfully",
  "data": {
    "open_cases": 12,
    "closed_cases": 3,
    "reopened_cases": 2
  },
  "total_cases": 17
}
```

---

## Case Log Management Endpoints

### 1. Create Case Log
**Endpoint:** `POST /api/v1/case-logs/create-log`

**Description:** Create a new case log entry to track case activities.

**Request Body:**
```json
{
  "case_id": 1,
  "action": "Status Change",
  "changed_by": "investigator@example.com",
  "change_detail": "Case status changed from Open to Closed",
  "notes": "Additional notes about this change"
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Case log created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "action": "Status Change",
    "changed_by": "investigator@example.com",
    "change_detail": "Case status changed from Open to Closed",
    "notes": "Additional notes about this change",
    "created_at": "2024-12-02T10:30:00Z"
  }
}
```

### 2. Get Case Logs
**Endpoint:** `GET /api/v1/case-logs/case/{case_id}/logs`

**Description:** Retrieve paginated list of logs for a specific case.

**Path Parameters:**
- `case_id` (integer): The ID of the case to retrieve logs for

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0, minimum: 0)
- `limit` (integer, optional): Number of records to return (default: 10, minimum: 1, maximum: 100)

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case logs retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_id": 1,
      "action": "Status Change",
      "changed_by": "investigator@example.com",
      "change_detail": "Case status changed from Open to Closed",
      "notes": "Additional notes about this change",
      "created_at": "2024-12-02T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

---

## Case Note Management Endpoints

### 1. Create Case Note
**Endpoint:** `POST /api/v1/case-notes/create-note`

**Description:** Create a new case note with optional status.

**Request Body:**
```json
{
  "case_id": 1,
  "note": "Initial investigation findings suggest multiple suspects involved",
  "status": "Investigation",
  "created_by": "investigator@example.com"
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Case note created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "note": "Initial investigation findings suggest multiple suspects involved",
    "status": "Investigation",
    "created_by": "investigator@example.com",
    "created_at": "2024-12-02T10:30:00Z"
  }
}
```

### 2. Get Case Notes
**Endpoint:** `GET /api/v1/case-notes/case/{case_id}/notes`

**Description:** Retrieve paginated list of notes for a specific case.

**Path Parameters:**
- `case_id` (integer): The ID of the case to retrieve notes for

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0, minimum: 0)
- `limit` (integer, optional): Number of records to return (default: 10, minimum: 1, maximum: 100)

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case notes retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_id": 1,
      "note": "Initial investigation findings suggest multiple suspects involved",
      "status": "Investigation",
      "created_by": "investigator@example.com",
      "created_at": "2024-12-02T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

### 3. Update Case Note
**Endpoint:** `PUT /api/v1/case-notes/update-note/{note_id}`

**Description:** Update an existing case note.

**Path Parameters:**
- `note_id` (integer): The ID of the note to update

**Request Body:**
```json
{
  "note": "Updated investigation findings with new evidence",
  "status": "Analysis"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case note updated successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "note": "Updated investigation findings with new evidence",
    "status": "Analysis",
    "created_by": "investigator@example.com",
    "created_at": "2024-12-02T10:30:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Note with ID 1 not found"
}
```

### 4. Delete Case Note
**Endpoint:** `DELETE /api/v1/case-notes/delete-note/{note_id}`

**Description:** Delete a case note.

**Path Parameters:**
- `note_id` (integer): The ID of the note to delete

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case note deleted successfully"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Note with ID 1 not found"
}
```

---

## Person Management Endpoints

### 1. Create Person
**Endpoint:** `POST /api/v1/persons/create-person`

**Description:** Create a new person record associated with a case.

**Request Body:**
```json
{
  "case_id": 1,
  "name": "John Doe",
  "is_unknown": false,
  "custody_stage": "Arrested",
  "evidence_id": "EVID-001",
  "evidence_source": "Digital Forensics",
  "evidence_summary": "Phone analysis reveals suspicious communications",
  "investigator": "Detective Smith",
  "created_by": "investigator@example.com"
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Person created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "name": "John Doe",
    "is_unknown": false,
    "custody_stage": "Arrested",
    "evidence_id": "EVID-001",
    "evidence_source": "Digital Forensics",
    "evidence_summary": "Phone analysis reveals suspicious communications",
    "investigator": "Detective Smith",
    "created_by": "investigator@example.com",
    "created_at": "2024-12-02T10:30:00Z",
    "updated_at": "2024-12-02T10:30:00Z"
  }
}
```

### 2. Get Person
**Endpoint:** `GET /api/v1/persons/get-person/{person_id}`

**Description:** Retrieve a specific person by ID.

**Path Parameters:**
- `person_id` (integer): The ID of the person to retrieve

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Person retrieved successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "name": "John Doe",
    "is_unknown": false,
    "custody_stage": "Arrested",
    "evidence_id": "EVID-001",
    "evidence_source": "Digital Forensics",
    "evidence_summary": "Phone analysis reveals suspicious communications",
    "investigator": "Detective Smith",
    "created_by": "investigator@example.com",
    "created_at": "2024-12-02T10:30:00Z",
    "updated_at": "2024-12-02T10:30:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Person with ID 1 not found"
}
```

### 3. Get Persons by Case
**Endpoint:** `GET /api/v1/persons/get-persons-by-case/{case_id}`

**Description:** Retrieve paginated list of persons associated with a specific case.

**Path Parameters:**
- `case_id` (integer): The ID of the case to retrieve persons for

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0, minimum: 0)
- `limit` (integer, optional): Number of records to return (default: 10, minimum: 1, maximum: 100)

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Persons retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_id": 1,
      "name": "John Doe",
      "is_unknown": false,
      "custody_stage": "Arrested",
      "evidence_id": "EVID-001",
      "evidence_source": "Digital Forensics",
      "evidence_summary": "Phone analysis reveals suspicious communications",
      "investigator": "Detective Smith",
      "created_by": "investigator@example.com",
      "created_at": "2024-12-02T10:30:00Z",
      "updated_at": "2024-12-02T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

### 4. Update Person
**Endpoint:** `PUT /api/v1/persons/update-person/{person_id}`

**Description:** Update an existing person record.

**Path Parameters:**
- `person_id` (integer): The ID of the person to update

**Request Body:**
```json
{
  "name": "John Smith",
  "custody_stage": "Released",
  "evidence_summary": "Updated analysis shows no criminal activity"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Person updated successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "name": "John Smith",
    "is_unknown": false,
    "custody_stage": "Released",
    "evidence_id": "EVID-001",
    "evidence_source": "Digital Forensics",
    "evidence_summary": "Updated analysis shows no criminal activity",
    "investigator": "Detective Smith",
    "created_by": "investigator@example.com",
    "created_at": "2024-12-02T10:30:00Z",
    "updated_at": "2024-12-02T11:00:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Person with ID 1 not found"
}
```

### 5. Delete Person
**Endpoint:** `DELETE /api/v1/persons/delete-person/{person_id}`

**Description:** Delete a person record.

**Path Parameters:**
- `person_id` (integer): The ID of the person to delete

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Person deleted successfully"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Person with ID 1 not found"
}
```

---

## Case Number Handling

### Auto-Generated Case Numbers
When `case_number` is not provided in the request, the system automatically generates a unique case number using the following format:
```
{INITIALS}-{DATE}-{ID}
```

**Examples:**
- Title: "Digital Forensics Investigation" → "DFI-061025-0001"
- Title: "Buronan Maroko Interpol" → "BMI-061025-0002"
- Title: "Kasus Buronan Internasional Maroko Interpol" → "KBI-061025-0003"

**Format Breakdown:**
- `INITIALS`: First letter of each word in the title (max 3 words)
  - If title has 3 words or less: Use all words
  - If title has more than 3 words: Use first 3 words only
- `DATE`: Current date in DDMMYY format (e.g., 061025 for June 10, 2025)
- `ID`: Case ID with 4-digit padding (e.g., 0001, 0002, 0003)

### Manual Case Numbers
When `case_number` is provided in the request, the system validates and uses the provided value.

**Validation Rules:**
- Minimum 3 characters long
- Must be unique (no duplicates allowed)
- Case-sensitive
- Cannot be empty or null

**Best Practices:**
- Use consistent naming conventions (e.g., "CASE-YYYY-NNNN")
- Include year for easy identification
- Use sequential numbers for better organization
- Avoid special characters that might cause issues

### Error Handling
- **409 Conflict**: Case number already exists
- **400 Bad Request**: Case number too short or invalid format
- **422 Unprocessable Entity**: Validation errors in request body
- **500 Internal Server Error**: Database constraint violations or unexpected errors

### Case Number Generation Examples

**Title with 3 words or less:**
- "Digital Forensics" → "DF-061025-0001"
- "Buronan Maroko Interpol" → "BMI-061025-0002"
- "Cyber Crime" → "CC-061025-0003"

**Title with more than 3 words:**
- "Kasus Buronan Internasional Maroko Interpol" → "KBI-061025-0004"
- "Digital Forensics Investigation Cyber Crime" → "DFI-061025-0005"
- "Penyelidikan Kasus Kejahatan Cyber Internasional" → "PKK-061025-0006"

**Special Characters Handling:**
- "Case #123 - Special Investigation" → "CSI-061025-0007"
- "Digital Forensics (Phase 1)" → "DFP-061025-0008"

---

## Data Models

### Case Model
```json
{
  "id": "integer",
  "case_number": "string (unique)",
  "title": "string",
  "description": "string (optional)",
  "status": "enum (Open, Closed, Re-open)",
  "main_investigator": "string",
  "agency_id": "integer (optional)",
  "work_unit_id": "integer (optional)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Person Model
```json
{
  "id": "integer",
  "name": "string",
  "is_unknown": "boolean",
  "custody_stage": "string (optional)",
  "evidence_id": "string (optional)",
  "evidence_source": "string (optional)",
  "evidence_summary": "string (optional)",
  "investigator": "string (optional)",
  "case_id": "integer",
  "created_by": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### CaseLog Model
```json
{
  "id": "integer",
  "case_id": "integer",
  "action": "string",
  "changed_by": "string",
  "change_detail": "string (optional)",
  "notes": "string (optional)",
  "created_at": "datetime"
}
```

### CaseNote Model
```json
{
  "id": "integer",
  "case_id": "integer",
  "note": "string",
  "status": "string (optional)",
  "created_by": "string",
  "created_at": "datetime"
}
```

### Agency Model
```json
{
  "id": "integer",
  "name": "string"
}
```

### WorkUnit Model
```json
{
  "id": "integer",
  "name": "string",
  "agency_id": "integer"
}
```

### AnalysisItem Model
```json
{
  "evidence_id": "string",
  "summary": "string",
  "status": "string"
}
```

### PersonWithAnalysis Model
```json
{
  "id": "integer",
  "name": "string",
  "person_type": "string",
  "analysis": "array of AnalysisItem"
}
```

### CaseLogDetail Model
```json
{
  "status": "string",
  "timestamp": "string",
  "description": "string",
  "notes": "string (optional)"
}
```

### CaseNoteDetail Model
```json
{
  "timestamp": "string",
  "status": "string",
  "content": "string"
}
```

### CaseSummary Model
```json
{
  "total_persons": "integer",
  "total_evidence": "integer"
}
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Validation error message"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**404 Not Found:**
```json
{
  "detail": "Case with ID 1 not found"
}
```

**409 Conflict:**
```json
{
  "detail": "Case number 'CASE-2024-0001' already exists"
}
```

**422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Unexpected server error, please try again later"
}
```

---

## Database Relationships

### Case Relationships (with Cascade Delete)
- **Case → CaseLog**: `cascade="all, delete-orphan"`
- **Case → CaseNote**: `cascade="all, delete-orphan"`
- **Case → Person**: `cascade="all, delete-orphan"`
- **Case → Evidence**: `cascade="all, delete-orphan"`
- **Case → Suspect**: `cascade="all, delete-orphan"`

### Evidence Relationships
- **Evidence → CustodyLog**: `cascade="all, delete-orphan"`
- **Evidence → CustodyReport**: `cascade="all, delete-orphan"`

---

## Frontend Integration Examples

### Get Case List
```javascript
async function getCases(page = 0, limit = 10, filters = {}) {
  const token = localStorage.getItem('access_token');
  const params = new URLSearchParams({
    skip: page * limit,
    limit: limit,
    ...filters
  });
  
  const response = await fetch(`/api/v1/cases/get-all-cases?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Create New Case

#### Auto-Generate Case Number
```javascript
async function createCaseWithAutoNumber(caseData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/cases/create-case', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: caseData.title,
      description: caseData.description,
      main_investigator: caseData.main_investigator,
      agency_id: caseData.agency_id,
      work_unit_id: caseData.work_unit_id,
      agency_name: caseData.agency_name,
      work_unit_name: caseData.work_unit_name
      // case_number will be auto-generated as {INITIALS}-{DATE}-{ID}
    })
  });
  
  return await response.json();
}

// Example usage:
const caseData = {
  title: "Buronan Maroko Interpol",
  description: "Investigation of international fugitive",
  main_investigator: "Detective Smith",
  agency_name: "Trikora Agency",
  work_unit_name: "International Division"
};
// Will generate case number like: "BMI-061025-0001"
```

#### Manual Case Number
```javascript
async function createCaseWithManualNumber(caseData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/cases/create-case', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      case_number: caseData.case_number, // Manual case number
      title: caseData.title,
      description: caseData.description,
      main_investigator: caseData.main_investigator,
      agency_id: caseData.agency_id,
      work_unit_id: caseData.work_unit_id
    })
  });
  
  return await response.json();
}
```

### Get Case Detail
```javascript
async function getCaseDetail(caseId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/cases/get-case-detail-comprehensive/${caseId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Update Case
```javascript
async function updateCase(caseId, caseData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/cases/update-case/${caseId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(caseData)
  });
  
  return await response.json();
}
```

### Delete Case
```javascript
async function deleteCase(caseId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/cases/delete-case/${caseId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Get Case Statistics
```javascript
async function getCaseStatistics() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/cases/statistics/summary', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Create Case Log
```javascript
async function createCaseLog(logData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/case-logs/create-log', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(logData)
  });
  
  return await response.json();
}
```

### Get Case Logs
```javascript
async function getCaseLogs(caseId, page = 0, limit = 10) {
  const token = localStorage.getItem('access_token');
  const params = new URLSearchParams({
    skip: page * limit,
    limit: limit
  });
  
  const response = await fetch(`/api/v1/case-logs/case/${caseId}/logs?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Create Case Note
```javascript
async function createCaseNote(noteData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/case-notes/create-note', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(noteData)
  });
  
  return await response.json();
}
```

### Get Case Notes
```javascript
async function getCaseNotes(caseId, page = 0, limit = 10) {
  const token = localStorage.getItem('access_token');
  const params = new URLSearchParams({
    skip: page * limit,
    limit: limit
  });
  
  const response = await fetch(`/api/v1/case-notes/case/${caseId}/notes?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Update Case Note
```javascript
async function updateCaseNote(noteId, noteData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/case-notes/update-note/${noteId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(noteData)
  });
  
  return await response.json();
}
```

### Delete Case Note
```javascript
async function deleteCaseNote(noteId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/case-notes/delete-note/${noteId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Create Person
```javascript
async function createPerson(personData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/persons/create-person', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(personData)
  });
  
  return await response.json();
}
```

### Get Person
```javascript
async function getPerson(personId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/persons/get-person/${personId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Get Persons by Case
```javascript
async function getPersonsByCase(caseId, page = 0, limit = 10) {
  const token = localStorage.getItem('access_token');
  const params = new URLSearchParams({
    skip: page * limit,
    limit: limit
  });
  
  const response = await fetch(`/api/v1/persons/get-persons-by-case/${caseId}?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### Update Person
```javascript
async function updatePerson(personId, personData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/persons/update-person/${personId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(personData)
  });
  
  return await response.json();
}
```

### Delete Person
```javascript
async function deletePerson(personId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/persons/delete-person/${personId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

---

## Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request parameters |
| 401 | Unauthorized - Authentication required |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |

---

## Rate Limiting

API requests are rate limited to prevent abuse:
- **Standard endpoints**: 100 requests per minute per user
- **Search endpoints**: 50 requests per minute per user

---

## Support

For API support and questions:
- Documentation: `/docs` (Swagger UI)
- Contact: [Support Team Email]
- Issue Tracker: [GitHub Issues URL]

---

## API Summary

This comprehensive API documentation covers all Case Management system endpoints:

### Case Management
- **Create Case**: `POST /api/v1/cases/create-case`
- **Get Case Detail**: `GET /api/v1/cases/get-case-detail-comprehensive/{case_id}`
- **Get All Cases**: `GET /api/v1/cases/get-all-cases`
- **Update Case**: `PUT /api/v1/cases/update-case/{case_id}`
- **Delete Case**: `DELETE /api/v1/cases/delete-case/{case_id}`
- **Get Statistics**: `GET /api/v1/cases/statistics/summary`

### Case Log Management
- **Create Log**: `POST /api/v1/case-logs/create-log`
- **Get Case Logs**: `GET /api/v1/case-logs/case/{case_id}/logs`

### Case Note Management
- **Create Note**: `POST /api/v1/case-notes/create-note`
- **Get Case Notes**: `GET /api/v1/case-notes/case/{case_id}/notes`
- **Update Note**: `PUT /api/v1/case-notes/update-note/{note_id}`
- **Delete Note**: `DELETE /api/v1/case-notes/delete-note/{note_id}`

### Person Management
- **Create Person**: `POST /api/v1/persons/create-person`
- **Get Person**: `GET /api/v1/persons/get-person/{person_id}`
- **Get Persons by Case**: `GET /api/v1/persons/get-persons-by-case/{case_id}`
- **Update Person**: `PUT /api/v1/persons/update-person/{person_id}`
- **Delete Person**: `DELETE /api/v1/persons/delete-person/{person_id}`

### Key Features
- **Flexible Case Number Handling**: Support for both auto-generated and manual case numbers
- **Comprehensive Case Tracking**: Full lifecycle management from creation to closure
- **Audit Trail**: Complete logging of all case activities and changes
- **Person Management**: Detailed tracking of suspects, witnesses, and other persons of interest
- **Note System**: Flexible note-taking with status tracking
- **Pagination**: All list endpoints support pagination for large datasets
- **Search & Filter**: Advanced filtering capabilities for case discovery
- **Cascade Operations**: Automatic cleanup of related data when cases are deleted
- **Validation & Error Handling**: Comprehensive input validation with clear error messages

### Data Relationships
- Cases have one-to-many relationships with logs, notes, and persons
- All related data is automatically cleaned up when a case is deleted
- Comprehensive case details include all related entities in a single response

This API provides a complete digital forensics case management solution with full CRUD operations, audit trails, and comprehensive data relationships.