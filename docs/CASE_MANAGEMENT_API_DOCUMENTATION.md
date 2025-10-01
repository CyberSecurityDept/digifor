# Case Management API Documentation

## Overview
This document provides comprehensive API documentation for the Case Management system endpoints. The endpoints are organized by UI sections to match the Case Management interface functionality.

## Base URL
```
/api/v1/cases
```

## Frontend API Endpoints Summary

### **Endpoints yang akan digunakan Frontend:**

#### **1. Case List Management (Essential untuk Frontend)**
- ✅ `GET /overview` - Get dashboard statistics for case management cards
- ✅ `GET /get-all-cases/` - Retrieve paginated list of cases with filtering options
- ✅ `GET /search` - Search cases with advanced filters
- ✅ `GET /filter-options` - Get available filter options for case list
- ✅ `GET /form-options` - Get dropdown options for case creation form

#### **2. Case Detail Management (Essential untuk Frontend)**
- ✅ `POST /create-cases/` - Create new case
- ✅ `GET /case-by-id` - Get case by ID
- ✅ `GET /{case_id}/detail` - Get comprehensive case details
- ✅ `PUT /update-case/{case_id}` - Update case information
- ✅ `DELETE /delete-case/` - Delete case
- ✅ `GET /{case_id}/stats` - Get case statistics
- ✅ `GET /{case_id}/export/pdf` - Export case to PDF

#### **3. Case Person of Interest Management (Essential untuk Frontend)**
- ✅ `POST /{case_id}/persons` - Add person of interest to case
- ✅ `GET /{case_id}/persons` - Get all persons of interest for a case
- ✅ `PUT /{case_id}/persons/{person_id}` - Update person of interest
- ✅ `DELETE /{case_id}/persons/{person_id}` - Remove person of interest

#### **4. Case Evidence Management (Essential untuk Frontend)**
- ✅ `POST /{case_id}/persons/{person_id}/evidence/{evidence_id}` - Associate evidence with person

#### **5. Case Log & Notes Management (Essential untuk Frontend)**
- ✅ `GET /{case_id}/activities` - Get case activities/log
- ✅ `GET /{case_id}/activities/recent` - Get recent case activities
- ✅ `GET /{case_id}/status-history` - Get case status history
- ✅ `POST /{case_id}/notes` - Add note to case
- ✅ `GET /{case_id}/notes` - Get case notes
- ✅ `DELETE /{case_id}/notes/{note_index}` - Delete case note
- ✅ `POST /{case_id}/close` - Close case
- ✅ `POST /{case_id}/reopen` - Reopen case
- ✅ `POST /{case_id}/change-status` - Change case status

---

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <access_token>
```

---

## 1. Case List Management

### 1.1 Get Case Management Overview
**Endpoint:** `GET /api/v1/cases/overview`

**Description:** Get dashboard statistics for case management cards.

**Request:**
```http
GET /api/v1/cases/overview
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case management overview retrieved successfully",
  "data": {
    "dashboard_cards": {
      "case_open": 12,
      "case_closed": 3,
      "case_reopen": 12
    }
  }
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": 500,
  "message": "Failed to retrieve case management overview"
}
```

### 1.2 Get All Cases
**Endpoint:** `GET /api/v1/cases/get-all-cases/`

**Description:** Retrieve paginated list of cases with filtering options.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100, max: 1000)
- `status` (optional): Filter by case status (open, closed, reopened)
- `priority` (optional): Filter by priority (low, medium, high, critical)
- `case_type` (optional): Filter by case type (criminal, civil, corporate, etc.)
- `search` (optional): Search in title, case number, or description

**Request:**
```http
GET /api/v1/cases/get-all-cases/?skip=0&limit=20&status=open&search=maroko
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Cases retrieved successfully",
  "data": [
    {
      "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
      "case_number": "CASE-2024-0001",
      "title": "Buronan Maroko Interpol",
      "description": "Case description...",
      "status": "open",
      "priority": "high",
      "case_type": "criminal",
      "jurisdiction": "Interpol",
      "work_unit": "Dirjen Imigrasi 1",
      "case_officer": "Robert",
      "created_at": "2024-12-12T00:00:00Z",
      "updated_at": "2024-12-12T00:00:00Z",
      "evidence_count": 5,
      "analysis_progress": 75
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "per_page": 20,
    "pages": 2
  }
}
```

**Response (400 Bad Request):**
```json
{
  "status": 400,
  "message": "Invalid query parameters"
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": 500,
  "message": "Failed to retrieve cases"
}
```

### 1.3 Search Cases
**Endpoint:** `GET /api/v1/cases/search`

**Description:** Search cases with advanced filtering.

**Query Parameters:**
- `q` (required): Search query string
- `status` (optional): Filter by status
- `priority` (optional): Filter by priority
- `case_type` (optional): Filter by case type
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 50, max: 100)

**Request:**
```http
GET /api/v1/cases/search?q=maroko&status=open&limit=10
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case search completed successfully",
  "data": {
    "cases": [
      {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "case_name": "Buronan Maroko Interpol",
        "case_number": "CASE-2024-0001",
        "investigator": "Robert",
        "agency": "Interpol",
        "date_created": "12/12/25",
        "status": "Open",
        "priority": "high",
        "case_type": "criminal",
        "evidence_count": 5,
        "analysis_progress": 75
      }
    ],
    "total": 1,
    "pagination": {
      "page": 1,
      "per_page": 10,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    },
    "filters_applied": {
      "search_query": "maroko",
      "status": "open",
      "priority": null,
      "case_type": null
    }
  }
}
```

### 1.4 Get Filter Options
**Endpoint:** `GET /api/v1/cases/filter-options`

**Description:** Get available filter options for case management dashboard.

**Request:**
```http
GET /api/v1/cases/filter-options
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Filter options retrieved successfully",
  "data": {
    "statuses": ["open", "closed", "reopened"],
    "priorities": ["low", "medium", "high", "critical"],
    "case_types": ["criminal", "civil", "corporate", "cybercrime"],
    "jurisdictions": ["Interpol", "Imigrasi", "Polri"],
    "case_officers": ["Robert", "Solebun", "Wisnu"]
  }
}
```

### 1.5 Get Form Options
**Endpoint:** `GET /api/v1/cases/form-options`

**Description:** Get dropdown options for case creation form.

**Request:**
```http
GET /api/v1/cases/form-options
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Form options retrieved successfully",
  "data": {
    "investigators": [
      {
        "id": "user-uuid-1",
        "name": "Robert",
        "username": "robert",
        "role": "investigator"
      }
    ],
    "agencies": ["Interpol", "Imigrasi", "Polri"],
    "work_units": ["Dirjen Imigrasi 1", "Unit Cybercrime"],
    "case_types": ["criminal", "civil", "corporate", "cybercrime", "fraud", "other"],
    "priorities": ["low", "medium", "high", "critical"]
  }
}
```

---

## 2. Case Detail Management

### 2.1 Get Case by ID
**Endpoint:** `GET /api/v1/cases/case-by-id`

**Description:** Get basic case information by case ID.

**Query Parameters:**
- `case_id` (required): UUID of the case

**Request:**
```http
GET /api/v1/cases/case-by-id?case_id=135df21b-c0ab-4bcc-b438-95874333f1c6
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case retrieved successfully",
  "data": {
    "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "case_number": "CASE-2024-0001",
    "title": "Buronan Maroko Interpol",
    "description": "Case description...",
    "status": "open",
    "priority": "high",
    "case_type": "criminal",
    "jurisdiction": "Interpol",
    "work_unit": "Dirjen Imigrasi 1",
    "case_officer": "Robert",
    "created_at": "2024-12-12T00:00:00Z",
    "updated_at": "2024-12-12T00:00:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Case not found"
}
```

**Response (400 Bad Request):**
```json
{
  "status": 400,
  "message": "Invalid case ID format"
}
```

### 2.2 Get Case Detail (Comprehensive)
**Endpoint:** `GET /api/v1/cases/{case_id}/detail`

**Description:** Get comprehensive case details including persons, evidence, activities, and notes.

**Path Parameters:**
- `case_id`: UUID of the case

**Request:**
```http
GET /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/detail
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case detail retrieved successfully",
  "data": {
    "case": {
      "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
      "case_number": "CASE-2024-0001",
      "title": "Buronan Maroko Interpol",
      "description": "Case description...",
      "status": "closed",
      "priority": "high",
      "case_type": "criminal",
      "jurisdiction": "Interpol",
      "work_unit": "Dirjen Imigrasi 1",
      "case_officer": "Solehun",
      "created_at": "2024-12-02T00:00:00Z",
      "updated_at": "2024-12-02T00:00:00Z",
      "closed_at": "2024-12-02T15:23:00Z",
      "evidence_count": 5,
      "analysis_progress": 75
    },
    "persons_of_interest": [
      {
        "id": "person-uuid-1",
        "full_name": "Rafi ahmad",
        "person_type": "suspect",
        "alias": "Rafi",
        "description": "Primary suspect",
        "evidence": [
          {
            "id": "evidence-uuid-1",
            "evidence_number": "32342223",
            "description": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian",
            "item_type": "phone",
            "analysis_status": "completed",
            "created_at": "2024-12-02T00:00:00Z",
            "association_type": "primary",
            "confidence_level": "high",
            "association_notes": "GPS data analysis"
          }
        ]
      }
    ],
    "case_log": [
      {
        "id": "activity-uuid-1",
        "activity_type": "reopened",
        "description": "Re-open 16 mei 2024, 08:12",
        "timestamp": "2024-05-16T08:12:00Z",
        "user_name": "Wisnu",
        "user_role": "investigator",
        "old_value": {"status": "closed"},
        "new_value": {"status": "reopened"}
      }
    ],
    "notes": [
      {
        "content": "Kasus ini memiliki indikasi adanya tersangka tambahan",
        "timestamp": "2024-01-12T15:23:00Z",
        "status": "active"
      }
    ],
    "total_persons": 3,
    "total_evidence": 5
  }
}
```

### 2.3 Create Case
**Endpoint:** `POST /api/v1/cases/create-cases/`

**Description:** Create a new case with auto-generated or manual case number.

**Request Body:**
```json
{
  "title": "New Case Title",
  "description": "Case description",
  "case_type": "criminal",
  "status": "open",
  "priority": "high",
  "jurisdiction": "Interpol",
  "case_officer": "Robert",
  "work_unit": "Dirjen Imigrasi 1",
  "is_confidential": false,
  "use_auto_generated_id": true,
  "case_number": "MANUAL-001"
}
```

**Request:**
```http
POST /api/v1/cases/create-cases/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Buronan Maroko Interpol",
  "description": "Case description...",
  "case_type": "criminal",
  "status": "open",
  "priority": "high",
  "jurisdiction": "Interpol",
  "case_officer": "Robert",
  "work_unit": "Dirjen Imigrasi 1",
  "is_confidential": false,
  "use_auto_generated_id": true
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Case created successfully",
  "data": {
    "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "case_number": "CASE-2024-0001",
    "title": "Buronan Maroko Interpol",
    "description": "Case description...",
    "status": "open",
    "priority": "high",
    "case_type": "criminal",
    "jurisdiction": "Interpol",
    "work_unit": "Dirjen Imigrasi 1",
    "case_officer": "Robert",
    "created_at": "2024-12-12T00:00:00Z"
  }
}
```

**Response (400 Bad Request):**
```json
{
  "status": 400,
  "message": "Case number already exists"
}
```

**Response (500 Internal Server Error):**
```json
{
  "status": 500,
  "message": "Case creation failed: Database error"
}
```

### 2.4 Update Case
**Endpoint:** `PUT /api/v1/cases/update-case/{case_id}`

**Description:** Update case information.

**Path Parameters:**
- `case_id`: UUID of the case

**Request Body:**
```json
{
  "title": "Updated Case Title",
  "description": "Updated description",
  "status": "closed",
  "priority": "medium"
}
```

**Request:**
```http
PUT /api/v1/cases/update-case/135df21b-c0ab-4bcc-b438-95874333f1c6
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Updated Case Title",
  "description": "Updated description",
  "status": "closed"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case updated successfully",
  "data": {
    "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "case_number": "CASE-2024-0001",
    "title": "Updated Case Title",
    "description": "Updated description",
    "status": "closed",
    "updated_at": "2024-12-12T10:30:00Z"
  }
}
```

### 2.5 Delete Case
**Endpoint:** `DELETE /api/v1/cases/delete-case/`

**Description:** Soft delete (archive) a case.

**Query Parameters:**
- `case_id` (required): UUID of the case to delete

**Request:**
```http
DELETE /api/v1/cases/delete-case/?case_id=135df21b-c0ab-4bcc-b438-95874333f1c6
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Case archived successfully"
}
```

### 2.6 Export Case PDF
**Endpoint:** `GET /api/v1/cases/{case_id}/export/pdf`

**Description:** Export case details as PDF (placeholder implementation).

**Path Parameters:**
- `case_id`: UUID of the case

**Request:**
```http
GET /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/export/pdf
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "PDF export functionality is not yet implemented",
  "data": {
    "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "case_number": "CASE-2024-0001",
    "title": "Buronan Maroko Interpol",
    "note": "PDF generation will be implemented in a future version"
  }
}
```

---

## 3. Case Person of Interest Management

### 3.1 Add Person of Interest
**Endpoint:** `POST /api/v1/cases/{case_id}/persons`

**Description:** Add a new person of interest to a case.

**Path Parameters:**
- `case_id`: UUID of the case

**Request Body:**
```json
{
  "person_type": "suspect",
  "full_name": "Rafi ahmad",
  "alias": "Rafi",
  "date_of_birth": "1990-01-01",
  "nationality": "Indonesian",
  "address": "Jakarta, Indonesia",
  "phone": "+628123456789",
  "email": "rafi@example.com",
  "social_media_accounts": ["@rafi_ahmad"],
  "device_identifiers": ["IMEI:123456789"],
  "description": "Primary suspect in the case",
  "is_primary": true
}
```

**Request:**
```http
POST /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/persons
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "person_type": "suspect",
  "full_name": "Rafi ahmad",
  "alias": "Rafi",
  "description": "Primary suspect in the case",
  "is_primary": true
}
```

**Response (201 Created):**
```json
{
  "id": "person-uuid-1",
  "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
  "person_type": "suspect",
  "full_name": "Rafi ahmad",
  "alias": "Rafi",
  "description": "Primary suspect in the case",
  "is_primary": true,
  "created_at": "2024-12-12T00:00:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Case not found"
}
```

### 3.2 Get Case Persons
**Endpoint:** `GET /api/v1/cases/{case_id}/persons`

**Description:** Get all persons of interest for a case.

**Path Parameters:**
- `case_id`: UUID of the case

**Request:**
```http
GET /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/persons
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
[
  {
    "id": "person-uuid-1",
    "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "person_type": "suspect",
    "full_name": "Rafi ahmad",
    "alias": "Rafi",
    "description": "Primary suspect in the case",
    "is_primary": true,
    "created_at": "2024-12-12T00:00:00Z"
  },
  {
    "id": "person-uuid-2",
    "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "person_type": "witness",
    "full_name": "Nathalie",
    "alias": null,
    "description": "Witness to the incident",
    "is_primary": false,
    "created_at": "2024-12-12T01:00:00Z"
  }
]
```

### 3.3 Update Person of Interest
**Endpoint:** `PUT /api/v1/cases/{case_id}/persons/{person_id}`

**Description:** Update person of interest information.

**Path Parameters:**
- `case_id`: UUID of the case
- `person_id`: UUID of the person

**Request Body:**
```json
{
  "full_name": "Updated Name",
  "description": "Updated description",
  "is_primary": false
}
```

**Request:**
```http
PUT /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/persons/person-uuid-1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "Rafi Ahmad Updated",
  "description": "Updated suspect description"
}
```

**Response (200 OK):**
```json
{
  "id": "person-uuid-1",
  "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
  "person_type": "suspect",
  "full_name": "Rafi Ahmad Updated",
  "alias": "Rafi",
  "description": "Updated suspect description",
  "is_primary": true,
  "updated_at": "2024-12-12T10:30:00Z"
}
```

### 3.4 Delete Person of Interest
**Endpoint:** `DELETE /api/v1/cases/{case_id}/persons/{person_id}`

**Description:** Delete a person of interest from a case.

**Path Parameters:**
- `case_id`: UUID of the case
- `person_id`: UUID of the person

**Request:**
```http
DELETE /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/persons/person-uuid-1
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Person deleted successfully"
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Person not found"
}
```

---

## 4. Case Evidence Management

### 4.1 Associate Evidence with Person
**Endpoint:** `POST /api/v1/cases/{case_id}/persons/{person_id}/evidence/{evidence_id}`

**Description:** Associate evidence with a person of interest.

**Path Parameters:**
- `case_id`: UUID of the case
- `person_id`: UUID of the person
- `evidence_id`: UUID of the evidence

**Request:**
```http
POST /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/persons/person-uuid-1/evidence/evidence-uuid-1
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence associated with person successfully",
  "data": {
    "evidence": {
      "id": "evidence-uuid-1",
      "evidence_number": "32342223",
      "description": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian"
    },
    "person": {
      "id": "person-uuid-1",
      "full_name": "Rafi ahmad",
      "person_type": "suspect"
    }
  }
}
```

**Response (404 Not Found):**
```json
{
  "status": 404,
  "message": "Case not found"
}
```

**Response (400 Bad Request):**
```json
{
  "status": 400,
  "message": "Evidence is already associated with this person"
}
```

---

## 5. Case Log & Notes Management

### 5.1 Get Case Activities
**Endpoint:** `GET /api/v1/cases/{case_id}/activities`

**Description:** Get case activity log (case log).

**Path Parameters:**
- `case_id`: UUID of the case

**Query Parameters:**
- `limit` (optional): Number of activities to return (default: 50, max: 100)
- `offset` (optional): Number of activities to skip (default: 0)

**Request:**
```http
GET /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/activities?limit=20
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
[
  {
    "id": "activity-uuid-1",
    "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "activity_type": "reopened",
    "description": "Re-open 16 mei 2024, 08:12",
    "timestamp": "2024-05-16T08:12:00Z",
    "user_id": "user-uuid-1",
    "old_value": {"status": "closed"},
    "new_value": {"status": "reopened"}
  },
  {
    "id": "activity-uuid-2",
    "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "activity_type": "updated",
    "description": "Edit By: Wisnu 16 mai 2024, 08:12 Change: Adding Person: Nathalie",
    "timestamp": "2024-05-16T08:12:00Z",
    "user_id": "user-uuid-2",
    "old_value": {"persons_count": 1},
    "new_value": {"persons_count": 2}
  }
]
```

### 5.2 Get Recent Case Activities
**Endpoint:** `GET /api/v1/cases/{case_id}/activities/recent`

**Description:** Get recent case activities with user information.

**Path Parameters:**
- `case_id`: UUID of the case

**Query Parameters:**
- `limit` (optional): Number of activities to return (default: 10, max: 50)

**Request:**
```http
GET /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/activities/recent?limit=5
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
[
  {
    "id": "activity-uuid-1",
    "activity_type": "reopened",
    "description": "Re-open 16 mei 2024, 08:12",
    "timestamp": "2024-05-16T08:12:00Z",
    "user_name": "Wisnu",
    "user_role": "investigator"
  },
  {
    "id": "activity-uuid-2",
    "activity_type": "updated",
    "description": "Edit By: Wisnu 16 mai 2024, 08:12 Change: Adding Person: Nathalie",
    "timestamp": "2024-05-16T08:12:00Z",
    "user_name": "Wisnu",
    "user_role": "investigator"
  }
]
```

### 5.3 Get Case Status History
**Endpoint:** `GET /api/v1/cases/{case_id}/status-history`

**Description:** Get case status change history.

**Path Parameters:**
- `case_id`: UUID of the case

**Query Parameters:**
- `limit` (optional): Number of history records to return (default: 50, max: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Request:**
```http
GET /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/status-history
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
[
  {
    "id": "history-uuid-1",
    "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "old_status": "open",
    "new_status": "closed",
    "changed_by": "user-uuid-1",
    "reason": "Case completed",
    "notes": "All evidence analyzed",
    "timestamp": "2024-12-02T15:23:00Z"
  }
]
```

### 5.4 Add Case Note
**Endpoint:** `POST /api/v1/cases/{case_id}/notes`

**Description:** Add a note to a case.

**Path Parameters:**
- `case_id`: UUID of the case

**Query Parameters:**
- `note_content` (required): Content of the note

**Request:**
```http
POST /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/notes?note_content=New note content
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Note added successfully",
  "data": {
    "note": {
      "content": "New note content",
      "timestamp": "2024-12-12T10:30:00Z",
      "status": "active",
      "added_by": "John Doe"
    },
    "total_notes": 3
  }
}
```

### 5.5 Get Case Notes
**Endpoint:** `GET /api/v1/cases/{case_id}/notes`

**Description:** Get all notes for a case.

**Path Parameters:**
- `case_id`: UUID of the case

**Request:**
```http
GET /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/notes
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case notes retrieved successfully",
  "data": {
    "notes": [
      {
        "content": "Kasus ini memiliki indikasi adanya tersangka tambahan",
        "timestamp": "2024-01-12T15:23:00Z",
        "status": "active"
      },
      {
        "content": "Additional suspect identified",
        "timestamp": "2024-01-13T09:00:00Z",
        "status": "active"
      }
    ],
    "total_notes": 2
  }
}
```

### 5.6 Delete Case Note
**Endpoint:** `DELETE /api/v1/cases/{case_id}/notes/{note_index}`

**Description:** Delete a specific note from a case.

**Path Parameters:**
- `case_id`: UUID of the case
- `note_index`: Index of the note to delete (0-based)

**Request:**
```http
DELETE /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/notes/0
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Note deleted successfully",
  "data": {
    "deleted_note": {
      "content": "Kasus ini memiliki indikasi adanya tersangka tambahan",
      "timestamp": "2024-01-12T15:23:00Z",
      "status": "active"
    },
    "total_notes": 1
  }
}
```

### 5.7 Close Case
**Endpoint:** `POST /api/v1/cases/{case_id}/close`

**Description:** Close a case with reason and notes.

**Path Parameters:**
- `case_id`: UUID of the case

**Request Body:**
```json
{
  "reason": "Case completed successfully",
  "notes": "All evidence analyzed and case resolved"
}
```

**Request:**
```http
POST /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/close
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "Case completed successfully",
  "notes": "All evidence analyzed and case resolved"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case closed successfully",
  "data": {
    "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "case_number": "CASE-2024-0001",
    "title": "Buronan Maroko Interpol",
    "status": "closed",
    "closed_at": "2024-12-12T15:23:00Z"
  }
}
```

### 5.8 Reopen Case
**Endpoint:** `POST /api/v1/cases/{case_id}/reopen`

**Description:** Reopen a closed case.

**Path Parameters:**
- `case_id`: UUID of the case

**Request Body:**
```json
{
  "reason": "New evidence found",
  "notes": "Additional evidence requires further investigation"
}
```

**Request:**
```http
POST /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/reopen
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "New evidence found",
  "notes": "Additional evidence requires further investigation"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case reopened successfully",
  "data": {
    "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "case_number": "CASE-2024-0001",
    "title": "Buronan Maroko Interpol",
    "status": "reopened",
    "reopened_at": "2024-12-12T16:00:00Z"
  }
}
```

### 5.9 Change Case Status
**Endpoint:** `POST /api/v1/cases/{case_id}/change-status`

**Description:** Change case status with reason and notes.

**Path Parameters:**
- `case_id`: UUID of the case

**Request Body:**
```json
{
  "status": "reopened",
  "reason": "Status change reason",
  "notes": "Additional notes for status change"
}
```

**Request:**
```http
POST /api/v1/cases/135df21b-c0ab-4bcc-b438-95874333f1c6/change-status
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "status": "reopened",
  "reason": "New evidence requires investigation",
  "notes": "Additional evidence found"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case status changed successfully",
  "data": {
    "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
    "case_number": "CASE-2024-0001",
    "title": "Buronan Maroko Interpol",
    "status": "reopened",
    "updated_at": "2024-12-12T16:00:00Z"
  }
}
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Invalid request parameters",
  "error": "Detailed error description"
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "Insufficient permissions"
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Internal server error",
  "error": "Detailed error description"
}
```

---

## Data Models

### Case Status Values
- `open`: Case is active and being investigated
- `closed`: Case is completed and closed
- `reopened`: Case was closed but reopened for further investigation
- `archived`: Case is archived (soft deleted)

### Priority Levels
- `low`: Low priority case
- `medium`: Medium priority case
- `high`: High priority case
- `critical`: Critical priority case

### Person Types
- `suspect`: Person suspected of involvement
- `witness`: Person who witnessed the incident
- `victim`: Person who was victimized
- `related`: Person related to the case

### Activity Types
- `created`: Case created
- `updated`: Case updated
- `closed`: Case closed
- `reopened`: Case reopened
- `note_added`: Note added to case
- `note_deleted`: Note deleted from case
- `evidence_associated`: Evidence associated with person
- `person_added`: Person added to case
- `person_updated`: Person information updated
- `person_deleted`: Person removed from case

---

## Rate Limiting

API requests are rate limited to prevent abuse:
- **Standard endpoints**: 100 requests per minute per user
- **Search endpoints**: 50 requests per minute per user
- **Export endpoints**: 10 requests per minute per user

---

## Versioning

This API follows semantic versioning:
- Current version: v1
- Version is specified in the URL path: `/api/v1/cases`
- Breaking changes will result in a new major version

---

## Frontend Integration Guide

### **Essential Frontend Endpoints**

#### **Case List Flow**
```javascript
// 1. Get Dashboard Overview
GET /api/v1/cases/overview
// 2. Get All Cases with Pagination
GET /api/v1/cases/get-all-cases/?skip=0&limit=10
// 3. Search Cases
GET /api/v1/cases/search?q=search_term
// 4. Get Filter Options
GET /api/v1/cases/filter-options
// 5. Get Form Options
GET /api/v1/cases/form-options
```

#### **Case Detail Flow**
```javascript
// 1. Create New Case
POST /api/v1/cases/create-cases/
// 2. Get Case by ID
GET /api/v1/cases/case-by-id?case_id=uuid
// 3. Get Case Detail
GET /api/v1/cases/{case_id}/detail
// 4. Update Case
PUT /api/v1/cases/update-case/{case_id}
// 5. Get Case Stats
GET /api/v1/cases/{case_id}/stats
// 6. Export Case PDF
GET /api/v1/cases/{case_id}/export/pdf
// 7. Delete Case
DELETE /api/v1/cases/delete-case/?case_id=uuid
```

#### **Person of Interest Flow**
```javascript
// 1. Add Person to Case
POST /api/v1/cases/{case_id}/persons
// 2. Get Case Persons
GET /api/v1/cases/{case_id}/persons
// 3. Update Person
PUT /api/v1/cases/{case_id}/persons/{person_id}
// 4. Remove Person
DELETE /api/v1/cases/{case_id}/persons/{person_id}
```

#### **Case Log & Notes Flow**
```javascript
// 1. Get Case Activities
GET /api/v1/cases/{case_id}/activities
// 2. Get Recent Activities
GET /api/v1/cases/{case_id}/activities/recent
// 3. Get Status History
GET /api/v1/cases/{case_id}/status-history
// 4. Add Note
POST /api/v1/cases/{case_id}/notes?note_content=note_text
// 5. Get Notes
GET /api/v1/cases/{case_id}/notes
// 6. Delete Note
DELETE /api/v1/cases/{case_id}/notes/{note_index}
// 7. Close Case
POST /api/v1/cases/{case_id}/close
// 8. Reopen Case
POST /api/v1/cases/{case_id}/reopen
// 9. Change Status
POST /api/v1/cases/{case_id}/change-status
```

### **Frontend Implementation Examples**

#### **Get Case List**
```javascript
async function getCases(page = 0, limit = 10, filters = {}) {
  const token = localStorage.getItem('access_token');
  const params = new URLSearchParams({
    skip: page * limit,
    limit: limit,
    ...filters
  });
  
  const response = await fetch(`/api/v1/cases/get-all-cases/?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

#### **Create New Case**
```javascript
async function createCase(caseData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/v1/cases/create-cases/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(caseData)
  });
  
  return await response.json();
}
```

#### **Get Case Detail**
```javascript
async function getCaseDetail(caseId) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/cases/${caseId}/detail`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

#### **Search Cases**
```javascript
async function searchCases(query, filters = {}) {
  const token = localStorage.getItem('access_token');
  const params = new URLSearchParams({
    q: query,
    ...filters
  });
  
  const response = await fetch(`/api/v1/cases/search?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

#### **Add Person of Interest**
```javascript
async function addPersonToCase(caseId, personData) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/cases/${caseId}/persons`, {
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

#### **Add Case Note**
```javascript
async function addCaseNote(caseId, noteContent) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/cases/${caseId}/notes?note_content=${encodeURIComponent(noteContent)}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

#### **Close Case**
```javascript
async function closeCase(caseId, reason, notes) {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/v1/cases/${caseId}/close`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      reason: reason,
      notes: notes
    })
  });
  
  return await response.json();
}
```

### **Frontend Error Handling**

#### **Common Error Responses**
```javascript
// Handle case management errors
function handleCaseError(error) {
  switch (error.status) {
    case 401:
      // Unauthorized - redirect to login
      window.location.href = '/login';
      break;
    case 404:
      // Case not found
      showError('Case not found');
      break;
    case 400:
      // Bad request (validation errors)
      showError(error.message);
      break;
    case 422:
      // Validation failed
      showValidationErrors(error.errors);
      break;
    case 500:
      // Server error
      showError('Server error occurred');
      break;
    default:
      showError('An unexpected error occurred');
  }
}
```

### **Frontend State Management**

#### **Case State Management**
```javascript
// Case state management
const CaseManager = {
  cases: [],
  currentCase: null,
  loading: false,
  error: null,
  
  async loadCases(filters = {}) {
    this.loading = true;
    try {
      const response = await getCases(0, 10, filters);
      this.cases = response.data;
      this.error = null;
    } catch (error) {
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  },
  
  async loadCaseDetail(caseId) {
    this.loading = true;
    try {
      const response = await getCaseDetail(caseId);
      this.currentCase = response.data;
      this.error = null;
    } catch (error) {
      this.error = error.message;
    } finally {
      this.loading = false;
    }
  }
};
```

## Support

For API support and questions:
- Documentation: `/docs` (Swagger UI)
- Contact: [Support Team Email]
- Issue Tracker: [GitHub Issues URL]
