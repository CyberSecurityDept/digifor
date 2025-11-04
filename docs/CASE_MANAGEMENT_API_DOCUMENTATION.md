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
  "description": "Investigasi kasus buronan internasional",
  "agency": "POLDA Metro Jaya",
  "work_unit": "Direktorat Reserse Kriminal Umum",
  "case_type": "Criminal",
  "priority": "High",
  "auto_generate_case_number": true
}
```

#### Option 2: Manual Case Number

**Request Body:**

```json
{
  "title": "Buronan Maroko Interpol",
  "description": "Investigasi kasus buronan internasional",
  "agency": "POLDA Metro Jaya",
  "work_unit": "Direktorat Reserse Kriminal Umum",
  "case_type": "Criminal",
  "priority": "High",
  "case_number": "REG/123/2024/DRKUM"
}
```

**Response (201 Created):**

```json
{
  "status": 201,
  "message": "Case created successfully",
  "data": {
    "case_id": 1,
    "case_number": "REG/001/2024/DRKUM",
    "title": "Buronan Maroko Interpol",
    "description": "Investigasi kasus buronan internasional",
    "agency": "POLDA Metro Jaya",
    "work_unit": "Direktorat Reserse Kriminal Umum",
    "case_type": "Criminal",
    "priority": "High",
    "status": "Open",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses:**

- **400 Bad Request:** Invalid input data
- **409 Conflict:** Case number already exists (for manual case numbers)
- **500 Internal Server Error:** Database error

---

### 2. Get All Cases

**Endpoint:** `GET /api/v1/cases/`

**Description:** Retrieve all cases with optional filtering and pagination.

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100)
- `status` (optional): Filter by case status
- `case_type` (optional): Filter by case type
- `priority` (optional): Filter by priority
- `agency` (optional): Filter by agency

**Example Request:**

```
GET /api/v1/cases/?skip=0&limit=10&status=Open&priority=High
```

**Response (200 OK):**

```json
{
  "status": 200,
  "message": "Cases retrieved successfully",
  "data": {
    "cases": [
      {
        "case_id": 1,
        "case_number": "REG/001/2024/DRKUM",
        "title": "Buronan Maroko Interpol",
        "description": "Investigasi kasus buronan internasional",
        "agency": "POLDA Metro Jaya",
        "work_unit": "Direktorat Reserse Kriminal Umum",
        "case_type": "Criminal",
        "priority": "High",
        "status": "Open",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 10
  }
}
```

---

### 3. Get Case by ID

**Endpoint:** `GET /api/v1/cases/{case_id}`

**Description:** Retrieve a specific case by its ID.

**Path Parameters:**

- `case_id` (required): The unique identifier of the case

**Response (200 OK):**

```json
{
  "status": 200,
  "message": "Case retrieved successfully",
  "data": {
    "case_id": 1,
    "case_number": "REG/001/2024/DRKUM",
    "title": "Buronan Maroko Interpol",
    "description": "Investigasi kasus buronan internasional",
    "agency": "POLDA Metro Jaya",
    "work_unit": "Direktorat Reserse Kriminal Umum",
    "case_type": "Criminal",
    "priority": "High",
    "status": "Open",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses:**

- **404 Not Found:** Case not found
- **500 Internal Server Error:** Database error

---

### 4. Update Case

**Endpoint:** `PUT /api/v1/cases/{case_id}`

**Description:** Update an existing case. Only provided fields will be updated.

**Path Parameters:**

- `case_id` (required): The unique identifier of the case

**Request Body:**

```json
{
  "title": "Buronan Maroko Interpol - Updated",
  "description": "Investigasi kasus buronan internasional - Updated description",
  "status": "In Progress",
  "priority": "Critical"
}
```

**Response (200 OK):**

```json
{
  "status": 200,
  "message": "Case updated successfully",
  "data": {
    "case_id": 1,
    "case_number": "REG/001/2024/DRKUM",
    "title": "Buronan Maroko Interpol - Updated",
    "description": "Investigasi kasus buronan internasional - Updated description",
    "agency": "POLDA Metro Jaya",
    "work_unit": "Direktorat Reserse Kriminal Umum",
    "case_type": "Criminal",
    "priority": "Critical",
    "status": "In Progress",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:45:00Z"
  }
}
```

**Error Responses:**

- **404 Not Found:** Case not found
- **400 Bad Request:** Invalid input data
- **500 Internal Server Error:** Database error

---

### 5. Delete Case

**Endpoint:** `DELETE /api/v1/cases/{case_id}`

**Description:** Delete a case by its ID. This will also delete all associated case logs and notes.

**Path Parameters:**

- `case_id` (required): The unique identifier of the case

**Response (200 OK):**

```json
{
  "status": 200,
  "message": "Case deleted successfully"
}
```

**Error Responses:**

- **404 Not Found:** Case not found
- **500 Internal Server Error:** Database error

---

## Case Log Endpoints

### 6. Create Case Log

**Endpoint:** `POST /api/v1/cases/{case_id}/logs`

**Description:** Create a new log entry for a specific case.

**Path Parameters:**

- `case_id` (required): The unique identifier of the case

**Request Body:**

```json
{
  "status": "In Progress",
  "notes": "Mulai investigasi forensik digital",
  "log_type": "Status Update"
}
```

**Response (201 Created):**

```json
{
  "status": 201,
  "message": "Case log created successfully",
  "data": {
    "log_id": 1,
    "case_id": 1,
    "status": "In Progress",
    "notes": "Mulai investigasi forensik digital",
    "log_type": "Status Update",
    "created_at": "2024-01-15T11:00:00Z"
  }
}
```

---

### 7. Get Case Logs

**Endpoint:** `GET /api/v1/cases/{case_id}/logs`

**Description:** Retrieve all log entries for a specific case.

**Path Parameters:**

- `case_id` (required): The unique identifier of the case

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100)

**Response (200 OK):**

```json
{
  "status": 200,
  "message": "Case logs retrieved successfully",
  "data": {
    "logs": [
      {
        "log_id": 1,
        "case_id": 1,
        "status": "Open",
        "notes": "Case created",
        "log_type": "System",
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "log_id": 2,
        "case_id": 1,
        "status": "In Progress",
        "notes": "Mulai investigasi forensik digital",
        "log_type": "Status Update",
        "created_at": "2024-01-15T11:00:00Z"
      }
    ],
    "total": 2,
    "skip": 0,
    "limit": 100
  }
}
```

---

## Case Note Endpoints

### 8. Create Case Note

**Endpoint:** `POST /api/v1/cases/{case_id}/notes`

**Description:** Create a new note for a specific case.

**Path Parameters:**

- `case_id` (required): The unique identifier of the case

**Request Body:**

```json
{
  "title": "Temuan Forensik Digital",
  "content": "Ditemukan bukti komunikasi melalui WhatsApp dengan tersangka utama",
  "note_type": "Evidence"
}
```

**Response (201 Created):**

```json
{
  "status": 201,
  "message": "Case note created successfully",
  "data": {
    "note_id": 1,
    "case_id": 1,
    "title": "Temuan Forensik Digital",
    "content": "Ditemukan bukti komunikasi melalui WhatsApp dengan tersangka utama",
    "note_type": "Evidence",
    "created_at": "2024-01-15T12:00:00Z"
  }
}
```

---

### 9. Get Case Notes

**Endpoint:** `GET /api/v1/cases/{case_id}/notes`

**Description:** Retrieve all notes for a specific case.

**Path Parameters:**

- `case_id` (required): The unique identifier of the case

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100)
- `note_type` (optional): Filter by note type

**Response (200 OK):**

```json
{
  "status": 200,
  "message": "Case notes retrieved successfully",
  "data": {
    "notes": [
      {
        "note_id": 1,
        "case_id": 1,
        "title": "Temuan Forensik Digital",
        "content": "Ditemukan bukti komunikasi melalui WhatsApp dengan tersangka utama",
        "note_type": "Evidence",
        "created_at": "2024-01-15T12:00:00Z"
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 100
  }
}
```

---

## Data Models

### Case Model

```json
{
  "case_id": "integer",
  "case_number": "string",
  "title": "string",
  "description": "string",
  "agency": "string",
  "work_unit": "string",
  "case_type": "string",
  "priority": "string",
  "status": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Case Log Model

```json
{
  "log_id": "integer",
  "case_id": "integer",
  "status": "string",
  "notes": "string",
  "log_type": "string",
  "created_at": "datetime"
}
```

### Case Note Model

```json
{
  "note_id": "integer",
  "case_id": "integer",
  "title": "string",
  "content": "string",
  "note_type": "string",
  "created_at": "datetime"
}
```

---

## Enums

### Case Status

- `Open` - Case baru dibuat
- `In Progress` - Case sedang dalam investigasi
- `Under Review` - Case sedang direview
- `Closed` - Case telah ditutup
- `Archived` - Case telah diarsipkan

### Case Type

- `Criminal` - Kasus kriminal
- `Civil` - Kasus perdata
- `Administrative` - Kasus administratif
- `Intelligence` - Kasus intelijen

### Priority

- `Low` - Prioritas rendah
- `Medium` - Prioritas sedang
- `High` - Prioritas tinggi
- `Critical` - Prioritas kritis

### Log Type

- `System` - Log sistem otomatis
- `Status Update` - Update status
- `Note` - Catatan manual
- `Evidence` - Bukti

### Note Type

- `Evidence` - Bukti
- `Observation` - Observasi
- `Analysis` - Analisis
- `Conclusion` - Kesimpulan

---

## Error Handling

### Standard Error Response Format

```json
{
  "status": "integer",
  "message": "string",
  "error": {
    "code": "string",
    "details": "string"
  }
}
```

### Common Error Codes

- `CASE_NOT_FOUND` - Case tidak ditemukan
- `INVALID_CASE_NUMBER` - Nomor kasus tidak valid
- `CASE_NUMBER_EXISTS` - Nomor kasus sudah ada
- `INVALID_STATUS` - Status tidak valid
- `INVALID_PRIORITY` - Prioritas tidak valid
- `DATABASE_ERROR` - Error database
- `VALIDATION_ERROR` - Error validasi input

---

## Examples

### Complete Case Workflow

#### 1. Create Case

```bash
curl -X POST "http://localhost:8000/api/v1/cases/create-case" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Buronan Maroko Interpol",
       "description": "Investigasi kasus buronan internasional",
       "agency": "POLDA Metro Jaya",
       "work_unit": "Direktorat Reserse Kriminal Umum",
       "case_type": "Criminal",
       "priority": "High",
       "auto_generate_case_number": true
     }'
```

#### 2. Add Case Log

```bash
curl -X POST "http://localhost:8000/api/v1/cases/1/logs" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "In Progress",
       "notes": "Mulai investigasi forensik digital",
       "log_type": "Status Update"
     }'
```

#### 3. Add Case Note

```bash
curl -X POST "http://localhost:8000/api/v1/cases/1/notes" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Temuan Forensik Digital",
       "content": "Ditemukan bukti komunikasi melalui WhatsApp dengan tersangka utama",
       "note_type": "Evidence"
     }'
```

#### 4. Update Case Status

```bash
curl -X PUT "http://localhost:8000/api/v1/cases/1" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "status": "Under Review",
       "priority": "Critical"
     }'
```

#### 5. Get Case with Logs and Notes

```bash
curl -X GET "http://localhost:8000/api/v1/cases/1" \
     -H "Authorization: Bearer <token>"

curl -X GET "http://localhost:8000/api/v1/cases/1/logs" \
     -H "Authorization: Bearer <token>"

curl -X GET "http://localhost:8000/api/v1/cases/1/notes" \
     -H "Authorization: Bearer <token>"
```

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Case numbers are auto-generated in format: `REG/{sequence}/{year}/{work_unit_code}`
- Case logs are automatically created when case status changes
- All endpoints require authentication
- Pagination is available for list endpoints
- Filtering is available for most list endpoints
- Soft delete is implemented for cases (archived instead of deleted)

---

**📚 Case Management API Documentation siap digunakan!**
