# Case Management API Documentation

This document describes the enhanced case management API endpoints that support the comprehensive case management interface.

## Overview

The case management system provides endpoints for:
- Case details with persons of interest, evidence, and activities
- Case notes management
- Evidence-person associations
- Case log and activity tracking
- PDF export functionality

## Base URL
```
/api/cases
```

## Authentication
All endpoints require authentication via Bearer token in the Authorization header.

## Endpoints

### 1. Get Case Detail
**GET** `/api/cases/{case_id}/detail`

Returns comprehensive case information including persons of interest, evidence, case log, and notes.

**Parameters:**
- `case_id` (path): UUID of the case

**Response:**
```json
{
  "status": 200,
  "message": "Case detail retrieved successfully",
  "data": {
    "case": {
      "id": "uuid",
      "case_number": "CASE-2024-0001",
      "title": "Buronan Maroko Interpol",
      "description": "Case description...",
      "status": "closed",
      "priority": "high",
      "case_type": "criminal",
      "jurisdiction": "Trikora agency",
      "work_unit": "Dirjen Imigrasi 1",
      "case_officer": "John Doe",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "closed_at": "2024-01-15T10:30:00Z",
      "evidence_count": 5,
      "analysis_progress": 80
    },
    "persons_of_interest": [
      {
        "id": "uuid",
        "full_name": "Rafi ahmad",
        "person_type": "suspect",
        "alias": "Rafi",
        "description": "Primary suspect",
        "evidence": [
          {
            "id": "uuid",
            "evidence_number": "E001",
            "description": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian",
            "item_type": "phone",
            "analysis_status": "completed",
            "created_at": "2024-01-02T09:00:00Z",
            "association_type": "primary",
            "confidence_level": "high",
            "association_notes": "Direct evidence from suspect's phone"
          }
        ]
      }
    ],
    "case_log": [
      {
        "id": "uuid",
        "activity_type": "reopened",
        "description": "Case reopened",
        "timestamp": "2024-01-16T08:12:00Z",
        "user_name": "Wianu",
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

### 2. Add Case Note
**POST** `/api/cases/{case_id}/notes`

Add a note to a case.

**Parameters:**
- `case_id` (path): UUID of the case
- `note_content` (query): Content of the note

**Response:**
```json
{
  "status": 200,
  "message": "Note added successfully",
  "data": {
    "note": {
      "content": "New note content",
      "timestamp": "2024-01-16T10:30:00Z",
      "status": "active",
      "added_by": "John Doe"
    },
    "total_notes": 3
  }
}
```

### 3. Get Case Notes
**GET** `/api/cases/{case_id}/notes`

Get all notes for a case.

**Response:**
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
      }
    ],
    "total_notes": 1
  }
}
```

### 4. Delete Case Note
**DELETE** `/api/cases/{case_id}/notes/{note_index}`

Delete a specific note from a case.

**Parameters:**
- `case_id` (path): UUID of the case
- `note_index` (query): Index of the note to delete (0-based)

**Response:**
```json
{
  "status": 200,
  "message": "Note deleted successfully",
  "data": {
    "deleted_note": {
      "content": "Deleted note content",
      "timestamp": "2024-01-12T15:23:00Z",
      "status": "active"
    },
    "total_notes": 2
  }
}
```

### 5. Associate Evidence with Person
**POST** `/api/cases/{case_id}/persons/{person_id}/evidence/{evidence_id}`

Associate evidence with a person of interest.

**Parameters:**
- `case_id` (path): UUID of the case
- `person_id` (path): UUID of the person
- `evidence_id` (path): UUID of the evidence

**Response:**
```json
{
  "status": 200,
  "message": "Evidence associated with person successfully",
  "data": {
    "evidence": {
      "id": "uuid",
      "evidence_number": "E001",
      "description": "Evidence description"
    },
    "person": {
      "id": "uuid",
      "full_name": "Rafi ahmad",
      "person_type": "suspect"
    }
  }
}
```

### 6. Export Case PDF
**GET** `/api/cases/{case_id}/export/pdf`

Export case details as PDF (placeholder implementation).

**Response:**
```json
{
  "status": 200,
  "message": "PDF export functionality is not yet implemented",
  "data": {
    "case_id": "uuid",
    "case_number": "CASE-2024-0001",
    "title": "Buronan Maroko Interpol",
    "note": "PDF generation will be implemented in a future version"
  }
}
```

## Database Schema Updates

### New Fields in Cases Table
- `agency`: Agency name (e.g., "Trikora agency")
- `jurisdiction_level`: Local, State, Federal, International
- `case_classification`: Public, Confidential, Secret, Top Secret

### New Table: evidence_person_associations
```sql
CREATE TABLE evidence_person_associations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id UUID NOT NULL REFERENCES evidence_items(id),
    person_id UUID NOT NULL REFERENCES case_persons(id),
    association_type VARCHAR(50) DEFAULT 'related',
    association_notes TEXT,
    confidence_level VARCHAR(20) DEFAULT 'medium',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(evidence_id, person_id)
);
```

## Migration Script

Run the migration script to update the database:

```bash
python tools/update_case_management.py
```

This script will:
1. Add new fields to the cases table
2. Create the evidence_person_associations table
3. Migrate existing evidence-person associations from descriptions

## Error Responses

All endpoints return appropriate HTTP status codes and error messages:

```json
{
  "status": 404,
  "message": "Case not found"
}
```

```json
{
  "status": 400,
  "message": "Invalid case ID format",
  "error": "Invalid UUID format"
}
```

```json
{
  "status": 500,
  "message": "Failed to retrieve case detail",
  "error": "Database connection error"
}
```

## Usage Examples

### Get Case Detail
```bash
curl -X GET "http://localhost:8000/api/cases/123e4567-e89b-12d3-a456-426614174000/detail" \
  -H "Authorization: Bearer your_token_here"
```

### Add Note
```bash
curl -X POST "http://localhost:8000/api/cases/123e4567-e89b-12d3-a456-426614174000/notes?note_content=New%20investigation%20lead" \
  -H "Authorization: Bearer your_token_here"
```

### Associate Evidence with Person
```bash
curl -X POST "http://localhost:8000/api/cases/123e4567-e89b-12d3-a456-426614174000/persons/456e7890-e89b-12d3-a456-426614174000/evidence/789e0123-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer your_token_here"
```

## Future Enhancements

1. **PDF Export**: Implement actual PDF generation using libraries like reportlab or weasyprint
2. **Advanced Search**: Add full-text search capabilities for cases, persons, and evidence
3. **Bulk Operations**: Support for bulk adding/updating of persons and evidence
4. **Timeline View**: Enhanced case timeline with visual representation
5. **Notifications**: Real-time notifications for case updates
6. **Audit Trail**: Comprehensive audit logging for compliance
