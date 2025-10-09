# Case Management API Documentation

## Overview
This document provides comprehensive API documentation for the Case Management system endpoints. The API is built with FastAPI and follows RESTful conventions.

## Base URL
```
/api/v1
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

**Description:** Create a new case with agency and work unit information. Supports both auto-generated and manual case numbers. **Automatically creates an initial case log entry with status "Open".**

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
- **Auto Case Log Creation**: Ketika case dibuat, sistem otomatis membuat case log entry dengan:
  - `action`: "Open"
  - `changed_by`: ""
  - `change_detail`: ""
  - `notes`: ""
  - `status`: "Open"
- Field `case_number` bersifat opsional:
  - **Jika tidak disertakan**: Akan otomatis di-generate menggunakan format `{INITIALS}-{DATE}-{ID}` 
    - `INITIALS`: Huruf pertama dari setiap kata dalam title (maksimal 3 kata)
    - `DATE`: Tanggal saat ini dalam format DDMMYY
    - `ID`: Case ID dengan padding 4 digit
    - **Contoh**: "Buronan Maroko Interpol" → "BMI-081025-0001"
  - **Jika disertakan**: Akan menggunakan case number yang diberikan (minimum 3 karakter, harus unik)

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Case created successfully",
  "data": {
    "id": 1,
    "case_number": "BMI-081025-0001",
    "title": "Buronan Maroko Interpol",
    "description": "Case description...",
    "status": "Open",
    "main_investigator": "Solehun",
    "agency_name": "Trikora agency",
    "work_unit_name": "Dirjen Imigrasi 1",
    "created_at": "2025-10-08T15:23:10.622831+07:00",
    "updated_at": "2025-10-08T15:23:10.622831+07:00"
  }
}
```

**Response (409 Conflict - Duplicate Case Number):**
```json
{
  "detail": "Case number 'BMI-081025-0001' already exists"
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
      "case_number": "BMI-081025-0001",
      "title": "Buronan Maroko Interpol",
      "description": "Case description...",
      "status": "Open",
      "case_officer": "Solehun",
      "agency": "Trikora agency",
      "work_unit": "Dirjen Imigrasi 1",
      "created_date": "08/10/2025"
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
          }
        ]
      }
    ],
    "case_log": [
      {
        "id": 1,
        "case_id": 1,
        "action": "Open",
        "changed_by": "",
        "change_detail": "",
        "notes": "",
        "status": "Open",
        "created_at": "2025-10-08T15:23:10.622831+07:00"
      }
    ],
    "notes": [
      {
        "timestamp": "08 Oct 2025, 15:23",
        "status": "Active",
        "content": "Initial case note"
      }
    ],
    "summary": {
      "total_persons": 1,
      "total_evidence": 1,
      "total_case_log": 1,
      "total_notes": 1
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
      "case_number": "BMI-081025-0001",
      "title": "Buronan Maroko Interpol",
      "description": "Case description...",
      "status": "Open",
      "main_investigator": "Solehun",
      "agency_name": "Trikora agency",
      "work_unit_name": "Dirjen Imigrasi 1",
      "created_at": "2025-10-08T15:23:10.622831+07:00",
      "updated_at": "2025-10-08T15:23:10.622831+07:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

### 4. Update Case
**Endpoint:** `PUT /api/v1/cases/update-case/{case_id}`

**Description:** Update case information. **Note: Updating case information does NOT create a case log entry.**

**Path Parameters:**
- `case_id` (integer): The ID of the case to update

**Request Body:**
```json
{
  "case_number": "BMI-081025-0001",
  "title": "Updated Case Title",
  "description": "Updated description",
  "main_investigator": "New Investigator",
  "agency_id": 2,
  "work_unit_id": 2,
  "agency_name": "New Agency Name",
  "work_unit_name": "New Work Unit Name"
}
```

**Request Body Fields:**
- `case_number` (string, optional): Case number to update
- `title` (string, optional): Case title to update
- `description` (string, optional): Case description to update
- `main_investigator` (string, optional): Main investigator name to update
- `agency_id` (integer, optional): Agency ID to update
- `work_unit_id` (integer, optional): Work unit ID to update
- `agency_name` (string, optional): Agency name for manual input
- `work_unit_name` (string, optional): Work unit name for manual input

**Note:** All fields are optional. Only provided fields will be updated. You can update any combination of fields.

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case updated successfully",
  "data": {
    "id": 1,
    "case_number": "BMI-081025-0001",
    "title": "Updated Case Title",
    "description": "Updated description",
    "status": "Open",
    "main_investigator": "New Investigator",
    "agency_name": "New Agency",
    "work_unit_name": "New Work Unit",
    "created_at": "2025-10-08T15:23:10.622831+07:00",
    "updated_at": "2025-10-08T17:30:00.000000+07:00"
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

### 1. Update Case Log
**Endpoint:** `PUT /api/v1/case-logs/update-log/{case_id}`

**Description:** Update case status and create a new case log entry. **This is the primary way to change case status.**

**Path Parameters:**
- `case_id` (integer): The ID of the case to update

**Request Body:**
```json
{
  "status": "Closed"
}
```

**Request Body Fields:**
- `status` (string, required): New case status. Valid values: "Open", "Closed", "Re-open" (case-insensitive)

**Behavior:**
- Updates the `status` field in the `cases` table
- Creates a new `CaseLog` entry with:
  - `action`: Same as the provided status ("Open", "Closed", or "Re-open")
  - `changed_by`: "" (empty for now, will be populated from logged-in user later)
  - `change_detail`: "" (empty)
  - `notes`: Retrieved from `case_notes` table if status is "Closed" or "Re-open", otherwise ""
  - `status`: Same as the provided status
  - `created_at`: Current timestamp in WIB timezone

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case log updated successfully",
  "data": {
    "id": 2,
    "case_id": 1,
    "action": "Closed",
    "changed_by": "",
    "change_detail": "",
    "notes": "",
    "status": "Closed",
    "created_at": "08 Oct 25, 16:17"
  }
}
```

**Response (400 Bad Request - Invalid Status):**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "status"],
      "msg": "Value error, Invalid status 'invalid'. Only ['Open', 'Closed', 'Re-open'] are allowed.",
      "input": "invalid"
    }
  ]
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
      "id": 2,
      "case_id": 1,
      "action": "Closed",
      "changed_by": "",
      "change_detail": "",
      "notes": "",
      "status": "Closed",
      "created_at": "08 Oct 25, 16:17"
    },
    {
      "id": 1,
      "case_id": 1,
      "action": "Open",
      "changed_by": "",
      "change_detail": "",
      "notes": "",
      "status": "Open",
      "created_at": "08 Oct 25, 15:23"
    }
  ],
  "total": 2,
  "page": 1,
  "size": 10
}
```

**Note:** The `created_at` field is formatted as "DD MMM YY, HH:MM" (e.g., "08 Oct 25, 16:17").

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
    "created_at": "2025-10-08T15:23:10.622831+07:00"
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
      "created_at": "2025-10-08T15:23:10.622831+07:00"
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
    "created_at": "2025-10-08T15:23:10.622831+07:00"
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

**Description:** Create a new person record associated with a case. **Automatically creates a case log entry with action "Edit".**

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

**Auto Case Log Creation:**
When a person is created, the system automatically creates a case log entry with:
- `action`: "Edit"
- `changed_by`: "Wisnu" (default value, will be replaced with logged-in user later)
- `change_detail`: "Adding Person: {person_name}"
- `notes`: ""
- `status`: Current case status (maintains last known status)

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
    "created_at": "2025-10-08T15:23:10.622831+07:00",
    "updated_at": "2025-10-08T15:23:10.622831+07:00"
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
    "created_at": "2025-10-08T15:23:10.622831+07:00",
    "updated_at": "2025-10-08T15:23:10.622831+07:00"
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
      "created_at": "2025-10-08T15:23:10.622831+07:00",
      "updated_at": "2025-10-08T15:23:10.622831+07:00"
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
    "created_at": "2025-10-08T15:23:10.622831+07:00",
    "updated_at": "2025-10-08T17:00:00.000000+07:00"
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

## Evidence Management Endpoints

### 1. Create Evidence
**Endpoint:** `POST /api/v1/evidence/create-evidence`

**Description:** Create a new evidence record. **Automatically creates a case log entry with action "Edit".**

**Request Body:**
```json
{
  "case_id": 1,
  "evidence_id": "EVID-001",
  "evidence_type": "Digital",
  "description": "Mobile phone evidence",
  "custody_officer": "Detective Smith",
  "created_by": "investigator@example.com"
}
```

**Auto Case Log Creation:**
When evidence is created, the system automatically creates a case log entry with:
- `action`: "Edit"
- `changed_by`: "Wisnu" (default value, will be replaced with logged-in user later)
- `change_detail`: "Adding Evidence: {evidence_id}"
- `notes`: ""
- `status`: Current case status (maintains last known status)

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Evidence created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_id": "EVID-001",
    "evidence_type": "Digital",
    "description": "Mobile phone evidence",
    "custody_officer": "Detective Smith",
    "created_by": "investigator@example.com",
    "created_at": "2025-10-08T15:23:10.622831+07:00"
  }
}
```

---

## Case Log Behavior Summary

### Automatic Case Log Creation

1. **Case Creation**: 
   - Action: "Open"
   - Status: "Open"
   - Changed by: "" (empty)
   - Change detail: "" (empty)
   - Notes: "" (empty)

2. **Person Creation**:
   - Action: "Edit"
   - Status: Current case status (maintains last known status)
   - Changed by: "Wisnu" (default, will be replaced with logged-in user)
   - Change detail: "Adding Person: {person_name}"
   - Notes: "" (empty)

3. **Evidence Creation**:
   - Action: "Edit"
   - Status: Current case status (maintains last known status)
   - Changed by: "Wisnu" (default, will be replaced with logged-in user)
   - Change detail: "Adding Evidence: {evidence_id}"
   - Notes: "" (empty)

4. **Case Status Update** (via Update Case Log):
   - Action: Same as status ("Open", "Closed", "Re-open")
   - Status: New status
   - Changed by: "" (empty, will be replaced with logged-in user)
   - Change detail: "" (empty)
   - Notes: Retrieved from case_notes table if status is "Closed" or "Re-open"

### Case Status Values
- **"Open"**: Case is active and being investigated
- **"Closed"**: Case investigation is complete
- **"Re-open"**: Previously closed case is reopened for further investigation
- **Note**: "In Progress" status is not used

### Timestamp Format
All case log timestamps are formatted as: **"DD MMM YY, HH:MM"** (e.g., "08 Oct 25, 16:17")

---

## Case Number Handling

### Auto-Generated Case Numbers
When `case_number` is not provided in the request, the system automatically generates a unique case number using the following format:
```
{INITIALS}-{DATE}-{ID}
```

**Examples:**
- Title: "Digital Forensics Investigation" → "DFI-081025-0001"
- Title: "Buronan Maroko Interpol" → "BMI-081025-0002"
- Title: "Kasus Buronan Internasional Maroko Interpol" → "KBI-081025-0003"

**Format Breakdown:**
- `INITIALS`: First letter of each word in the title (max 3 words)
  - If title has 3 words or less: Use all words
  - If title has more than 3 words: Use first 3 words only
- `DATE`: Current date in DDMMYY format (e.g., 081025 for October 8, 2025)
- `ID`: Case ID with 4-digit padding (e.g., 0001, 0002, 0003)

### Manual Case Numbers
When `case_number` is provided in the request, the system validates and uses the provided value.

**Validation Rules:**
- Minimum 3 characters long
- Must be unique (no duplicates allowed)
- Case-sensitive
- Cannot be empty or null

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
  "created_at": "datetime (WIB timezone)",
  "updated_at": "datetime (WIB timezone)"
}
```

### CaseLog Model
```json
{
  "id": "integer",
  "case_id": "integer",
  "action": "string (Open, Closed, Re-open, Edit)",
  "changed_by": "string",
  "change_detail": "string (optional)",
  "notes": "string (optional)",
  "status": "string (Open, Closed, Re-open)",
  "created_at": "string (formatted as 'DD MMM YY, HH:MM')"
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
  "created_at": "datetime (WIB timezone)",
  "updated_at": "datetime (WIB timezone)"
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
  "created_at": "datetime (WIB timezone)"
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
  "detail": "Case number 'BMI-081025-0001' already exists"
}
```

**422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "loc": ["body", "status"],
      "msg": "Value error, Invalid status 'invalid'. Only ['Open', 'Closed', 'Re-open'] are allowed.",
      "type": "value_error"
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

### Evidence Relationships
- **Evidence → CustodyLog**: `cascade="all, delete-orphan"`
- **Evidence → CustodyReport**: `cascade="all, delete-orphan"`

---

## Frontend Integration Examples

### Create New Case
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
```

### Update Case Status
```javascript
async function updateCaseStatus(caseId, newStatus) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/case-logs/update-log/${caseId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      status: newStatus // "Open", "Closed", or "Re-open"
    })
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

### Create Person (Auto-generates Edit log)
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

## API Summary

This comprehensive API documentation covers all Case Management system endpoints:

### Case Management
- **Create Case**: `POST /api/v1/cases/create-case` (auto-creates initial log)
- **Get Case Detail**: `GET /api/v1/cases/get-case-detail-comprehensive/{case_id}`
- **Get All Cases**: `GET /api/v1/cases/get-all-cases`
- **Update Case**: `PUT /api/v1/cases/update-case/{case_id}`
- **Delete Case**: `DELETE /api/v1/cases/delete-case/{case_id}`
- **Get Statistics**: `GET /api/v1/cases/statistics/summary`

### Case Log Management
- **Update Case Log**: `PUT /api/v1/case-logs/update-log/{case_id}` (primary way to change status)
- **Get Case Logs**: `GET /api/v1/case-logs/case/{case_id}/logs`

### Case Note Management
- **Create Note**: `POST /api/v1/case-notes/create-note`
- **Get Case Notes**: `GET /api/v1/case-notes/case/{case_id}/notes`
- **Update Note**: `PUT /api/v1/case-notes/update-note/{note_id}`
- **Delete Note**: `DELETE /api/v1/case-notes/delete-note/{note_id}`

### Person Management
- **Create Person**: `POST /api/v1/persons/create-person` (auto-creates Edit log)
- **Get Person**: `GET /api/v1/persons/get-person/{person_id}`
- **Get Persons by Case**: `GET /api/v1/persons/get-persons-by-case/{case_id}`
- **Update Person**: `PUT /api/v1/persons/update-person/{person_id}`
- **Delete Person**: `DELETE /api/v1/persons/delete-person/{person_id}`

### Evidence Management
- **Create Evidence**: `POST /api/v1/evidence/create-evidence` (auto-creates Edit log)

### Key Features
- **Automatic Case Logging**: All case activities are automatically logged
- **Status Management**: Centralized status updates through case log endpoint
- **Flexible Case Number Handling**: Support for both auto-generated and manual case numbers
- **Comprehensive Case Tracking**: Full lifecycle management from creation to closure
- **Audit Trail**: Complete logging of all case activities and changes
- **Person Management**: Detailed tracking of suspects, witnesses, and other persons of interest
- **Evidence Management**: Digital evidence tracking with automatic logging
- **Note System**: Flexible note-taking with status tracking
- **Pagination**: All list endpoints support pagination for large datasets
- **Search & Filter**: Advanced filtering capabilities for case discovery
- **Cascade Operations**: Automatic cleanup of related data when cases are deleted
- **Validation & Error Handling**: Comprehensive input validation with clear error messages
- **Timezone Support**: All timestamps in WIB (UTC+7) timezone
- **Formatted Timestamps**: User-friendly timestamp format in case logs

### Data Relationships
- Cases have one-to-many relationships with logs, notes, persons, and evidence
- All related data is automatically cleaned up when a case is deleted
- Comprehensive case details include all related entities in a single response
- Automatic case log creation for all case activities

This API provides a complete digital forensics case management solution with full CRUD operations, automatic audit trails, and comprehensive data relationships.