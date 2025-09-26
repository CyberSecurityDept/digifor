# API - Forensic Analytic Backend

## Base URL
```
http://localhost:8000
```

## Authentication

### Overview
Sistem authentication menggunakan JWT (JSON Web Token) dengan auto refresh token mechanism untuk keamanan dan user experience yang optimal.

### Features
- ✅ **JWT Access Token** - 30 menit expiration
- ✅ **Refresh Token** - 7 hari expiration dengan rotation
- ✅ **Auto Refresh** - Token otomatis di-refresh sebelum expired
- ✅ **Token Rotation** - Security best practice
- ✅ **Session Management** - Multi-device support
- ✅ **Password Security** - Strong password requirements

### 1. Login
**Endpoint:** `POST /api/v1/auth/token`

**Description:** Melakukan login user dan mengembalikan access token.

**Request Headers:**
```
Content-Type: application/json
```

    **Request Body:**
    ```json
    {
        "username": "admin",
        "password": "admin123"
    }
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Login Successfully",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1ODI2NjE2Nn0.sO6Rwm1Xh8oEKz7cvbMDrGvrgzAO4Il13cZKlX2VZt8",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInRvbGUiOiJhZG1pbiIsInR5cGUiOiJyZWZyZXNoIiwiZXhwIjoxNzU5MTMwMDA4fQ.refresh_token_signature",
        "token_type": "bearer",
        "expires_in": 1800
    }
}
```

**Response (401 Unauthorized):**
```json
{
    "status": 401,
    "messages": "Invalid username or password"
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Login failed: Database connection error"
}
```

### 2. Auto Refresh Token
**Endpoint:** `POST /api/v1/auth/auto-refresh`

**Description:** Automatic refresh token endpoint untuk seamless token refresh tanpa user interaction.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Tokens refreshed automatically",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 1800
    }
}
```

**Response (401 Unauthorized):**
```json
{
    "status": 401,
    "message": "Auto refresh failed",
    "error": "Invalid refresh token"
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Token refresh failed: Session service unavailable"
}
```

### 3. Token Status Check
**Endpoint:** `GET /api/v1/auth/token-status`

**Description:** Check status token dan informasi refresh yang diperlukan.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Token status retrieved successfully",
    "data": {
        "valid": true,
        "needs_refresh": false,
        "time_until_expiry": 1200,
        "expires_at": "2024-01-01T12:00:00Z",
        "username": "admin",
        "role": "admin"
    }
}
```

**Response (401 Unauthorized):**
```json
{
    "status": 401,
    "message": "Invalid token"
}
```

### 4. Auto Refresh Headers
Ketika token di-refresh otomatis, server akan menambahkan header berikut ke response:

**Response Headers:**
```
X-New-Access-Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-New-Refresh-Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Token-Expires-In: 1800
X-Token-Refreshed: true
```

**Frontend Implementation:**
```javascript
// Check if token was refreshed
if (response.headers.get('X-Token-Refreshed') === 'true') {
    const newAccessToken = response.headers.get('X-New-Access-Token');
    const newRefreshToken = response.headers.get('X-New-Refresh-Token');
    
    // Update stored tokens
    localStorage.setItem('access_token', newAccessToken);
    localStorage.setItem('refresh_token', newRefreshToken);
}
```

### 5. Get User Profile
**Endpoint:** `GET /api/v1/auth/me`

**Description:** Mendapatkan informasi profil user yang sedang login.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "User profile retrieved successfully",
    "data": {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "username": "admin",
        "email": "admin@forenlytic.com",
        "full_name": "System Administrator",
        "role": "admin",
        "department": "IT",
        "is_active": true,
        "is_superuser": true,
        "last_login": "2025-09-22T06:18:01.135197",
        "created_at": "2025-09-19T04:28:50",
        "updated_at": "2025-09-22T06:18:01"
    }
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Failed to retrieve user profile: Database connection error"
}
```

**Response (401 Unauthorized):**
```json
{
    "detail": "Could not validate credentials"
}
```

### 6. User Registration
**Endpoint:** `POST /api/v1/auth/register`

**Description:** Mendaftarkan user baru dengan validasi password yang kuat.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "username": "newuser",
    "email": "newuser@example.com",
    "full_name": "New User",
    "password": "StrongPass123!",
    "department": "IT",
    "role": "investigator"
}
```

**Response (201 Created):**
```json
{
    "status": 201,
    "message": "User registered successfully",
    "data": {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c8",
        "username": "newuser",
        "email": "newuser@example.com",
        "full_name": "New User",
        "role": "investigator",
        "department": "IT",
        "is_active": true,
        "is_superuser": false,
        "last_login": null,
        "created_at": "2025-09-22T06:45:00",
        "updated_at": null
    }
}
```

**Response (422 Unprocessable Entity) - Password Validation Failed:**
```json
{
    "detail": {
        "status": 422,
        "message": "Password validation failed",
        "errors": [
            "Password must be at least 8 characters long",
            "Password must contain at least one uppercase letter",
            "Password must contain at least one special character"
        ],
        "strength": "weak"
    }
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "User registration failed: Database connection error"
}
```

### 7. Change Password
**Endpoint:** `POST /api/v1/auth/change-password`

**Description:** Mengubah password user dengan validasi password yang kuat.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "current_password": "OldPass123!",
    "new_password": "NewStrongPass456!"
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Password changed successfully",
    "revoked_sessions": 2
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Password change failed: Database connection error"
}
```

### 8. Request Password Reset
**Endpoint:** `POST /api/v1/auth/request-password-reset`

**Description:** Meminta reset password melalui email.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "If the email exists, a password reset link has been sent",
    "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Password reset request failed: Email service unavailable"
}
```

### 9. Reset Password
**Endpoint:** `POST /api/v1/auth/reset-password`

**Description:** Reset password menggunakan token yang valid.

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "new_password": "NewStrongPass789!"
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Password reset successfully",
    "revoked_sessions": 3
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Password reset failed: Database connection error"
}
```

### 10. Get Session Information
**Endpoint:** `GET /api/v1/auth/session`

**Description:** Mendapatkan informasi session saat ini.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Session information retrieved successfully",
    "data": {
        "user_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "username": "testuser",
        "role": "investigator",
        "login_time": "2025-09-22T06:41:18.698214",
        "last_activity": "2025-09-22T06:41:26.261430",
        "expires_at": "2025-09-22T07:11:18.697917",
        "is_active": true
    }
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Failed to retrieve session info: Session service unavailable"
}
```

### 11. Logout All Sessions
**Endpoint:** `POST /api/v1/auth/logout-all`

**Description:** Logout dari semua session user.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Logged out from 3 sessions and 2 refresh tokens"
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Failed to logout all sessions: Session revocation service unavailable"
}
```

### 12. Cleanup Expired Sessions
**Endpoint:** `GET /api/v1/auth/sessions/cleanup`

**Description:** Membersihkan session yang sudah expired (admin only).

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Cleaned up 5 expired sessions and 3 expired refresh tokens",
    "active_sessions": 12,
    "active_refresh_tokens": 8
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Session cleanup failed: Database connection error"
}
```

## Dashboard

### 13. Get Main Dashboard
**Endpoint:** `GET /api/v1/dashboard/`

**Description:** Mendapatkan halaman utama dashboard dengan menu Analytics dan Case.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Main dashboard retrieved successfully",
    "data": {
        "user": {
            "id": "db236fde-41fe-423c-af6a-f5d5a97cacf2",
            "username": "admin",
            "full_name": "System Administrator",
            "role": "admin"
        },
        "menu_options": [
            {
                "id": "analytics",
                "name": "Analytics",
                "description": "Digital forensics analytics and analysis tools",
                "icon": "analytics",
                "route": "/analytics"
            },
            {
                "id": "case",
                "name": "Case",
                "description": "Case management and investigation tools",
                "icon": "case",
                "route": "/case"
            }
        ]
    }
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Failed to retrieve main dashboard: Database connection error"
}
```

### 14. Get Analytics Dashboard
**Endpoint:** `GET /api/v1/dashboard/analytics`

**Description:** Mendapatkan dashboard analytics dengan statistik analisis dan evidence.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Analytics dashboard retrieved successfully",
    "data": {
        "statistics": {
            "total_analyses": 0,
            "completed_analyses": 0,
            "in_progress_analyses": 0,
            "pending_analyses": 0,
            "total_evidence": 0,
            "processed_evidence": 0
        },
        "analysis_types": [],
        "recent_analyses": []
    }
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Failed to retrieve analytics dashboard: Database connection error"
}
```

## Case Management

### 14. Get Case Management Overview
**Endpoint:** `GET /api/v1/cases/overview`

**Description:** Mendapatkan overview case management dengan statistik cards saja.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case management overview retrieved successfully",
    "data": {
        "dashboard_cards": {
            "case_open": 7,
            "case_closed": 1,
            "case_reopen": 0
        }
    }
}
```

### 15. Search Cases
**Endpoint:** `GET /api/v1/cases/search`

**Description:** Mencari kasus dengan query dan filter untuk dashboard case management.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `q` (required): Search query string
- `status` (optional): Filter by case status (open, closed, reopened)
- `priority` (optional): Filter by priority (low, medium, high, critical)
- `case_type` (optional): Filter by case type (criminal, civil, corporate)
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 50, max: 100)

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case search completed successfully",
    "data": {
        "cases": [
            {
                "id": "eca36d41-1385-47a0-984b-706900336f5b",
                "case_name": "Test Case 3",
                "case_number": "TEST-003",
                "investigator": "Unassigned",
                "agency": "N/A",
                "date_created": "09/23/25",
                "status": "Closed",
                "priority": "low",
                "case_type": "corporate",
                "evidence_count": 0,
                "analysis_progress": 0,
                "created_at": "2025-09-23T03:12:53",
                "updated_at": null
            }
        ],
        "total": 3,
        "pagination": {
            "page": 1,
            "per_page": 50,
            "pages": 1,
            "has_next": false,
            "has_prev": false
        },
        "filters_applied": {
            "search_query": "test",
            "status": null,
            "priority": null,
            "case_type": null
        }
    }
}
```

### 16. Get Filter Options
**Endpoint:** `GET /api/v1/cases/filter-options`

**Description:** Mendapatkan opsi filter yang tersedia untuk dashboard case management.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Filter options retrieved successfully",
    "data": {
        "statuses": ["open", "closed", "reopened"],
        "priorities": ["high", "medium", "low", "critical"],
        "case_types": ["criminal", "civil", "corporate"],
        "jurisdictions": ["Jakarta"],
        "case_officers": ["Detective Smith"]
    }
}
```

### 17. Get Case Management Overview
**Endpoint:** `GET /api/v1/cases/overview`

**Description:** Mendapatkan overview case management dengan statistik cards saja.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case management overview retrieved successfully",
    "data": {
        "dashboard_cards": {
            "case_open": 7,
            "case_closed": 1,
            "case_reopen": 0
        }
    }
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Failed to retrieve case management overview: Database connection error"
}
```

### 18. Get All Cases
**Endpoint:** `GET /api/v1/cases/get-all-cases/`

**Description:** Mendapatkan daftar semua kasus forensik.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100, max: 1000)
- `status` (optional): Filter by case status (open, closed, reopened)
- `priority` (optional): Filter by priority (low, medium, high, critical)
- `case_type` (optional): Filter by case type (criminal, civil, administrative)
- `search` (optional): Search in title, case_number, or description

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Cases retrieved successfully",
    "data": [
        {
            "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "case_number": "CASE-001",
            "title": "Digital Forensics Investigation",
            "description": "Investigation of cybercrime incident",
            "case_type": "criminal",
            "status": "open",
            "priority": "high",
            "incident_date": "2025-09-20T10:00:00",
            "reported_date": "2025-09-20T11:00:00",
            "jurisdiction": "Jakarta",
            "case_officer": "Detective Smith",
            "evidence_count": 5,
            "analysis_progress": 75,
            "created_by": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "assigned_to": "135df21b-c0ab-4bcc-b438-95874333f1c7",
            "created_at": "2025-09-20T12:00:00",
            "updated_at": "2025-09-22T08:00:00",
            "closed_at": null,
            "tags": {
                "category": "cybercrime",
                "type": "malware"
            },
            "notes": "High priority case",
            "is_confidential": true
        }
    ],
    "pagination": {
        "total": 1,
        "page": 1,
        "per_page": 100,
        "pages": 1
    }
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Failed to retrieve cases: Database connection error"
}
```

### 19. Create New Case
**Endpoint:** `POST /api/v1/cases/create-cases/`

**Description:** Membuat kasus forensik baru dengan form-based approach yang mendukung auto-generated case ID.

**Features:**
- ✅ **Auto-generated Case Numbers**: Format `CASE-YYYY-NNNN` (e.g., `CASE-2025-0001`)
- ✅ **Manual Case Numbers**: Custom case number support
- ✅ **Form-based Validation**: User-friendly form approach
- ✅ **Activity Logging**: Automatic case creation tracking
- ✅ **Duplicate Prevention**: Prevents duplicate case numbers

**UI Form Fields:**
- **Case name** (required) → `title`
- **Case Description** (optional) → `description`
- **Case ID** (Auto/Manual) → `use_auto_generated_id` + `case_number`
- **Main Investigator** (optional) → `case_officer`
- **Agency** (optional) → `jurisdiction`
- **Work Unit** (optional) → `work_unit`

**System Defaults:**
- **Status**: `"open"` (default)
- **Priority**: `"medium"` (default)
- **Case Type**: `null` (default)
- **Confidentiality**: `false` (default)

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body (Auto-generated Case ID):**
```json
{
    "title": "Digital Forensics Investigation",
    "description": "Investigation of cybercrime case",
    "use_auto_generated_id": true,
    "case_officer": "Detective Smith",
    "jurisdiction": "Jakarta Police",
    "work_unit": "Cyber Crime Unit"
}
```

**Request Body (Manual Case ID):**
```json
{
    "title": "Digital Forensics Investigation",
    "description": "Investigation of cybercrime case",
    "use_auto_generated_id": false,
    "case_number": "MANUAL-2024-001",
    "case_officer": "Detective Smith",
    "jurisdiction": "Jakarta Police",
    "work_unit": "Cyber Crime Unit"
}
```

**Response (201 Created):**
```json
{
    "status": 201,
    "message": "Case created successfully",
    "data": {
        "id": "6b3b5cb2-42c6-4764-84a5-855e2686b1c1",
        "case_number": "CASE-2025-0001",
        "title": "Digital Forensics Investigation",
        "description": "Investigation of cybercrime case",
        "case_type": null,
        "status": "open",
        "priority": "medium",
        "incident_date": null,
        "reported_date": null,
        "jurisdiction": "Jakarta Police",
        "case_officer": "Detective Smith",
        "work_unit": "Cyber Crime Unit",
        "evidence_count": 0,
        "analysis_progress": 0,
        "created_by": "db236fde-41fe-423c-af6a-f5d5a97cacf2",
        "assigned_to": null,
        "created_at": "2024-01-16T10:00:00Z",
        "updated_at": null,
        "closed_at": null,
        "reopened_count": 0,
        "last_status_change": null,
        "status_change_reason": null,
        "tags": null,
        "notes": null,
        "is_confidential": false,
        "persons": []
    }
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Case creation failed: Database connection error"
}
```

### 20. Get Form Options
**Endpoint:** `GET /api/v1/cases/form-options`

**Description:** Mendapatkan opsi untuk form create case (investigators, agencies, work units, dll).

**Request Headers:**
```
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
                "id": "db236fde-41fe-423c-af6a-f5d5a97cacf2",
                "name": "System Administrator",
                "username": "admin",
                "role": "admin"
            },
            {
                "id": "35198401-f70f-4867-98d9-575017f9b43f",
                "name": "Test User",
                "username": "testuser",
                "role": "investigator"
            }
        ],
        "agencies": ["Jakarta"],
        "work_units": [],
        "case_types": ["criminal", "civil", "corporate", "cybercrime", "fraud", "other"],
        "priorities": ["low", "medium", "high", "critical"]
    }
}
```

### 21. Get Case by ID
**Endpoint:** `GET /api/v1/cases/case-by-id`

**Description:** Mendapatkan detail kasus berdasarkan ID.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `case_id` (required): UUID kasus yang akan diambil (format: UUID string)

**Example URL:**
```
GET /api/v1/cases/case-by-id?case_id=719e0a0a-4e54-48c6-b2e2-10fe42cadc9e
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case retrieved successfully",
    "data": {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "case_number": "CASE-001",
        "title": "Digital Forensics Investigation",
        "description": "Investigation of cybercrime incident",
        "case_type": "criminal",
        "status": "open",
        "priority": "high",
        "incident_date": "2025-09-20T10:00:00",
        "reported_date": "2025-09-20T11:00:00",
        "jurisdiction": "Jakarta",
        "case_officer": "Detective Smith",
        "evidence_count": 5,
        "analysis_progress": 75,
        "created_by": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "assigned_to": "135df21b-c0ab-4bcc-b438-95874333f1c7",
        "created_at": "2025-09-20T12:00:00",
        "updated_at": "2025-09-22T08:00:00",
        "closed_at": null,
        "tags": {
            "category": "cybercrime",
            "type": "malware"
        },
        "notes": "High priority case",
        "is_confidential": true
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

### 22. Update Case
**Endpoint:** `PUT /api/v1/cases/update-case/{case_id}`

**Description:** Mengupdate informasi kasus forensik.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `case_id`: UUID kasus yang akan diupdate (format: UUID string)

**Example URL:**
```
PUT /api/v1/cases/update-case/719e0a0a-4e54-48c6-b2e2-10fe42cadc9e
```

**Request Body:**
```json
{
    "title": "Updated Financial Fraud Investigation",
    "description": "Updated investigation of suspected online banking fraud targeting multiple victims.",
    "case_type": "financial",
    "status": "open",
    "priority": "high",
    "jurisdiction": "Updated OJK Cybersecurity Division",
    "case_officer": "Detective Johnson",
    "work_unit": "Updated Financial Crime Unit",
    "is_confidential": true
}
```

**Request Schema:**
- `title` (string, optional): Updated case title
- `description` (string, optional): Updated case description
- `case_type` (string, optional): Updated case type (criminal, civil, financial, etc.)
- `status` (string, optional): Updated case status (open, closed, reopened)
- `priority` (string, optional): Updated priority level (low, medium, high, critical)
- `jurisdiction` (string, optional): Updated jurisdiction/agency
- `case_officer` (string, optional): Updated main investigator
- `work_unit` (string, optional): Updated work unit
- `is_confidential` (boolean, optional): Updated confidentiality status

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case updated successfully",
    "data": {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "case_number": "CASE-001",
        "title": "Updated Case Title",
        "description": "Updated case description",
        "case_type": "civil",
        "status": "open",
        "priority": "high",
        "incident_date": "2025-09-22T10:00:00",
        "reported_date": "2025-09-22T11:00:00",
        "jurisdiction": "Bandung",
        "case_officer": "Detective Brown",
        "evidence_count": 5,
        "analysis_progress": 75,
        "created_by": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "assigned_to": "135df21b-c0ab-4bcc-b438-95874333f1c7",
        "created_at": "2025-09-20T12:00:00",
        "updated_at": "2025-09-22T14:00:00",
        "closed_at": null,
        "reopened_count": 0,
        "last_status_change": null,
        "status_change_reason": null,
        "tags": {
            "category": "updated",
            "type": "digital"
        },
        "notes": "Updated case notes",
        "is_confidential": true
    }
}
```

### 23. Close Case
**Endpoint:** `POST /api/v1/cases/{case_id}/close`

**Description:** Menutup kasus forensik dengan alasan dan tracking aktivitas.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `case_id`: UUID kasus yang akan ditutup (format: UUID string)

**Request Body:**
```json
{
    "reason": "Investigation completed successfully",
    "notes": "All evidence analyzed and report generated"
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case closed successfully",
    "data": {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "case_number": "CASE-001",
        "title": "Digital Forensics Investigation",
        "status": "closed",
        "priority": "high",
        "closed_at": "2025-09-22T15:00:00",
        "last_status_change": "2025-09-22T15:00:00",
        "status_change_reason": "Investigation completed successfully",
        "reopened_count": 0
    }
}
```

**Response (400 Bad Request):**
```json
{
    "status": 400,
    "message": "Case is already closed"
}
```

### 24. Reopen Case
**Endpoint:** `POST /api/v1/cases/{case_id}/reopen`

**Description:** Membuka kembali kasus yang sudah ditutup dengan alasan dan tracking aktivitas.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `case_id`: UUID kasus yang akan dibuka kembali (format: UUID string)

**Request Body:**
```json
{
    "reason": "New evidence found",
    "notes": "Additional witness testimony received"
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case reopened successfully",
    "data": {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "case_number": "CASE-001",
        "title": "Digital Forensics Investigation",
        "status": "reopened",
        "priority": "high",
        "closed_at": null,
        "last_status_change": "2025-09-22T16:00:00",
        "status_change_reason": "New evidence found",
        "reopened_count": 1
    }
}
```

**Response (400 Bad Request):**
```json
{
    "status": 400,
    "message": "Only closed cases can be reopened"
}
```

### 25. Change Case Status
**Endpoint:** `POST /api/v1/cases/{case_id}/change-status`

**Description:** Mengubah status kasus dengan alasan dan tracking aktivitas.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `case_id`: UUID kasus yang statusnya akan diubah (format: UUID string)

**Request Body:**
```json
{
    "status": "open",
    "reason": "Investigation started",
    "notes": "Assigned to senior investigator"
}
```

**Valid Status Values:**
- `open` - Case baru dibuka
- `closed` - Case ditutup
- `reopened` - Case dibuka kembali

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case status changed successfully",
    "data": {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "case_number": "CASE-001",
        "title": "Digital Forensics Investigation",
        "status": "open",
        "last_status_change": "2025-09-22T17:00:00",
        "status_change_reason": "Investigation started",
        "reopened_count": 0
    }
}
```

### 26. Get Case Activities
**Endpoint:** `GET /api/v1/cases/{case_id}/activities`

**Description:** Mendapatkan log aktivitas kasus dengan pagination.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)

**Query Parameters:**
- `limit` (optional): Maximum number of records to return (default: 50, max: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case activities retrieved successfully",
    "data": [
        {
            "id": "activity-uuid-1",
            "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "user_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "activity_type": "created",
            "description": "Case 'CASE-001' created",
            "old_value": null,
            "new_value": {
                "case_number": "CASE-001",
                "title": "Digital Forensics Investigation",
                "status": "open"
            },
            "changed_fields": null,
            "status_change_reason": null,
            "previous_status": null,
            "new_status": null,
            "timestamp": "2025-09-20T12:00:00",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0..."
        },
        {
            "id": "activity-uuid-2",
            "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "user_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "activity_type": "status_change",
            "description": "Case 'CASE-001' status changed from 'open' to 'closed' - Reason: Investigation completed",
            "old_value": {"status": "open"},
            "new_value": {"status": "closed"},
            "changed_fields": ["status"],
            "status_change_reason": "Investigation completed",
            "previous_status": "open",
            "new_status": "closed",
            "timestamp": "2025-09-22T15:00:00",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0..."
        }
    ]
}
```

### 27. Get Recent Case Activities
**Endpoint:** `GET /api/v1/cases/{case_id}/activities/recent`

**Description:** Mendapatkan aktivitas terbaru kasus dengan informasi user.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)

**Query Parameters:**
- `limit` (optional): Maximum number of records to return (default: 10, max: 50)

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Recent case activities retrieved successfully",
    "data": [
        {
            "id": "activity-uuid-2",
            "activity_type": "status_change",
            "description": "Case 'CASE-001' status changed from 'open' to 'closed' - Reason: Investigation completed",
            "timestamp": "2025-09-22T15:00:00",
            "user_name": "John Investigator",
            "user_role": "investigator"
        },
        {
            "id": "activity-uuid-1",
            "activity_type": "created",
            "description": "Case 'CASE-001' created",
            "timestamp": "2025-09-20T12:00:00",
            "user_name": "Admin User",
            "user_role": "admin"
        }
    ]
}
```

### 28. Get Case Status History
**Endpoint:** `GET /api/v1/cases/{case_id}/status-history`

**Description:** Mendapatkan history perubahan status kasus.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)

**Query Parameters:**
- `limit` (optional): Maximum number of records to return (default: 50, max: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case status history retrieved successfully",
    "data": [
        {
            "id": "history-uuid-1",
            "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "user_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "previous_status": "open",
            "new_status": "closed",
            "reason": "Investigation completed successfully",
            "notes": "All evidence analyzed and report generated",
            "changed_at": "2025-09-22T15:00:00",
            "ip_address": "192.168.1.100"
        },
        {
            "id": "history-uuid-2",
            "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "user_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "previous_status": "closed",
            "new_status": "reopened",
            "reason": "New evidence found",
            "notes": "Additional witness testimony received",
            "changed_at": "2025-09-22T16:00:00",
            "ip_address": "192.168.1.100"
        }
    ]
}
```

### 29. Add Person to Case
**Endpoint:** `POST /api/v1/cases/{case_id}/persons`

**Description:** Menambahkan orang (suspect, victim, witness) ke dalam kasus.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)

**Request Body:**
```json
{
    "person_type": "suspect",
    "full_name": "John Doe",
    "alias": "JD",
    "date_of_birth": "1990-01-15T00:00:00",
    "nationality": "Indonesian",
    "address": "Jl. Merdeka No. 123, Jakarta",
    "phone": "+6281234567890",
    "email": "john.doe@email.com",
    "social_media_accounts": {
        "facebook": "john.doe.fb",
        "instagram": "@johndoe",
        "twitter": "@johndoe_tw"
    },
    "device_identifiers": {
        "imei": "123456789012345",
        "mac_address": "00:11:22:33:44:55"
    },
    "description": "Primary suspect in the case",
    "is_primary": true
}
```

**Valid Person Types:**
- `suspect` - Tersangka
- `victim` - Korban
- `witness` - Saksi
- `other` - Lainnya

**Response (201 Created):**
```json
{
    "status": 201,
    "message": "Person added to case successfully",
    "data": {
        "id": "person-uuid-1",
        "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "person_type": "suspect",
        "full_name": "John Doe",
        "alias": "JD",
        "date_of_birth": "1990-01-15T00:00:00",
        "nationality": "Indonesian",
        "address": "Jl. Merdeka No. 123, Jakarta",
        "phone": "+6281234567890",
        "email": "john.doe@email.com",
        "social_media_accounts": {
            "facebook": "john.doe.fb",
            "instagram": "@johndoe",
            "twitter": "@johndoe_tw"
        },
        "device_identifiers": {
            "imei": "123456789012345",
            "mac_address": "00:11:22:33:44:55"
        },
        "description": "Primary suspect in the case",
        "is_primary": true,
        "created_at": "2025-09-22T18:00:00",
        "updated_at": "2025-09-22T18:00:00"
    }
}
```

### 30. Get Case Persons
**Endpoint:** `GET /api/v1/cases/{case_id}/persons`

**Description:** Mendapatkan daftar semua orang yang terlibat dalam kasus.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case persons retrieved successfully",
    "data": [
        {
            "id": "person-uuid-1",
            "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "person_type": "suspect",
            "full_name": "John Doe",
            "alias": "JD",
            "date_of_birth": "1990-01-15T00:00:00",
            "nationality": "Indonesian",
            "address": "Jl. Merdeka No. 123, Jakarta",
            "phone": "+6281234567890",
            "email": "john.doe@email.com",
            "social_media_accounts": {
                "facebook": "john.doe.fb",
                "instagram": "@johndoe",
                "twitter": "@johndoe_tw"
            },
            "device_identifiers": {
                "imei": "123456789012345",
                "mac_address": "00:11:22:33:44:55"
            },
            "description": "Primary suspect in the case",
            "is_primary": true,
            "created_at": "2025-09-22T18:00:00",
            "updated_at": "2025-09-22T18:00:00"
        }
    ]
}
```

### 31. Update Case Person
**Endpoint:** `PUT /api/v1/cases/{case_id}/persons/{person_id}`

**Description:** Mengupdate informasi orang dalam kasus.

**Request Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)
- `person_id`: ID orang yang akan diupdate

**Request Body:**
```json
{
    "full_name": "John Doe Updated",
    "phone": "+6281234567891",
    "email": "john.doe.updated@email.com",
    "description": "Updated suspect information"
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case person updated successfully",
    "data": {
        "id": "person-uuid-1",
        "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "person_type": "suspect",
        "full_name": "John Doe Updated",
        "alias": "JD",
        "date_of_birth": "1990-01-15T00:00:00",
        "nationality": "Indonesian",
        "address": "Jl. Merdeka No. 123, Jakarta",
        "phone": "+6281234567891",
        "email": "john.doe.updated@email.com",
        "social_media_accounts": {
            "facebook": "john.doe.fb",
            "instagram": "@johndoe",
            "twitter": "@johndoe_tw"
        },
        "device_identifiers": {
            "imei": "123456789012345",
            "mac_address": "00:11:22:33:44:55"
        },
        "description": "Updated suspect information",
        "is_primary": true,
        "created_at": "2025-09-22T18:00:00",
        "updated_at": "2025-09-22T19:00:00"
    }
}
```

### 32. Delete Case Person
**Endpoint:** `DELETE /api/v1/cases/{case_id}/persons/{person_id}`

**Description:** Menghapus orang dari kasus.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)
- `person_id`: ID orang yang akan dihapus

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Person deleted successfully"
}
```

### 33. Get Case Statistics
**Endpoint:** `GET /api/v1/cases/{case_id}/stats`

**Description:** Mendapatkan statistik kasus.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case statistics retrieved successfully",
    "data": {
        "case_id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "evidence_count": 5,
        "analysis_count": 3,
        "completed_analysis": 2,
        "analysis_progress": 75,
        "status": "open",
        "priority": "high",
        "reopened_count": 0,
        "last_status_change": "2025-09-22T17:00:00"
    }
}
```

### 34. Delete Case
**Endpoint:** `DELETE /api/v1/cases/delete-case/?case_id={case_id}`

**Description:** Menghapus kasus forensik (soft delete/archive) menggunakan query parameter.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `case_id` (required): UUID kasus yang akan dihapus (format: UUID string)

**Response (200 OK):**
```json
{
    "message": "Case archived successfully"
}
```

**Response (404 Not Found):**
```json
{
    "status": 404,
    "message": "Case not found"
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Case deletion failed: Database connection error"
}
```

## Report Generation

### 34. Generate Case Report
**Endpoint:** `POST /api/v1/reports/cases/{case_id}/generate`

**Description:** Membuat laporan forensik untuk kasus tertentu.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: ID kasus yang akan dibuat laporannya (integer)

**Query Parameters:**
- `report_type` (optional): Jenis laporan (default: "comprehensive")
  - `comprehensive` - Laporan lengkap
  - `summary` - Ringkasan kasus
  - `evidence` - Laporan evidence
  - `analysis` - Laporan analisis

**Example URL:**
```
POST /api/v1/reports/cases/1/generate?report_type=summary
```

**Response (200 OK):**
```json
{
    "message": "Report generated successfully",
    "case_id": 1,
    "report_type": "summary",
    "file_path": "/data/reports/case_1_summary_CASE-2025-0001.json",
    "generated_at": "2025-09-22T12:00:00",
    "file_size": 2048
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
    "message": "Invalid report type. Must be one of: comprehensive, summary, evidence, analysis"
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Report generation failed: Report service unavailable"
}
```

### 35. List Case Reports
**Endpoint:** `GET /api/v1/reports/cases/{case_id}/reports`

**Description:** Mendapatkan daftar laporan yang sudah dibuat untuk kasus tertentu.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)

**Response (200 OK):**
```json
{
    "case_id": 1,
    "total_reports": 2,
    "reports": [
        {
            "filename": "case_1_summary_CASE-2025-0001.json",
            "filepath": "/data/reports/case_1_summary_CASE-2025-0001.json",
            "size": 2048,
            "created_at": 1695379200.0,
            "modified_at": 1695379200.0
        }
    ]
}
```

**Response (404 Not Found):**
```json
{
    "status": 404,
    "message": "Case not found"
}
```

### 36. Get Case Report
**Endpoint:** `GET /api/v1/reports/cases/{case_id}/reports/{filename}`

**Description:** Mengambil konten laporan JSON untuk kasus tertentu.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: UUID kasus (format: UUID string)
- `filename`: Nama file laporan

**Response (200 OK):**
```json
{
    "case_id": 1,
    "case_number": "CASE-2025-0001",
    "report_type": "summary",
    "generated_at": "2025-09-22T12:00:00",
    "case_info": {
        "title": "Digital Forensics Investigation",
        "status": "open",
        "priority": "high"
    },
    "summary": "Case investigation summary..."
}
```

**Response (404 Not Found):**
```json
{
    "status": 404,
    "message": "Case not found"
}
```

**Response (404 Not Found - Report):**
```json
{
    "status": 404,
    "message": "Report not found"
}
```

**Response (400 Bad Request):**
```json
{
    "status": 400,
    "message": "Report does not belong to this case"
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Failed to read report: File service unavailable"
}
```

### 37. Delete Case Report
**Endpoint:** `DELETE /api/v1/reports/cases/{case_id}/reports/{filename}`

**Description:** Menghapus laporan kasus tertentu.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `case_id`: ID kasus (integer)
- `filename`: Nama file laporan

**Response (200 OK):**
```json
{
    "message": "Report deleted successfully"
}
```

**Response (404 Not Found):**
```json
{
    "status": 404,
    "message": "Case not found"
}
```

**Response (404 Not Found - Report):**
```json
{
    "status": 404,
    "message": "Report not found"
}
```

### 38. Generate Custody Report
**Endpoint:** `POST /api/v1/reports/evidence/{evidence_id}/custody-report`

**Description:** Membuat laporan chain of custody untuk evidence tertentu.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
- `evidence_id`: ID evidence (integer)

**Response (200 OK):**
```json
{
    "message": "Custody report generated successfully",
    "evidence_id": 1,
    "file_path": "/data/reports/custody_evidence_1_2025-09-22.json",
    "generated_at": "2025-09-22T12:00:00"
}
```

### 39. Get Report Statistics
**Endpoint:** `GET /api/v1/reports/reports/stats`

**Description:** Mendapatkan statistik laporan yang telah dibuat.

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Report statistics retrieved successfully",
    "data": {
        "total_reports": 15,
        "reports_by_type": {
            "comprehensive": 5,
            "summary": 8,
            "evidence": 2,
            "analysis": 0
        },
        "reports_by_case": {
            "case_1": 3,
            "case_2": 2,
            "case_3": 1
        },
        "total_size": 2048000,
        "average_size": 136533
    }
}
```

## System Endpoints

### 40. Health Check
**Endpoint:** `GET /health`

**Description:** Memeriksa status kesehatan sistem.

**Response (200 OK):**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "database": "connected"
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Health check failed: System service unavailable"
}
```

### 41. Root Endpoint
**Endpoint:** `GET /`

**Description:** Informasi dasar API.

**Response (200 OK):**
```json
{
    "message": "Welcome to Forenlytic Backend",
    "version": "1.0.0",
    "docs": "/docs",
    "redoc": "/redoc"
}
```

**Response (500 Internal Server Error):**
```json
{
    "status": 500,
    "message": "Root endpoint failed: Application service unavailable"
}
```

## Response Status Codes

### 200 OK - Success Responses

**Login Success:**
```json
{
    "status": 200,
    "messages": "Login Successfully",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
    }
}
```

**Get User Profile Success:**
```json
{
    "status": 200,
    "message": "User profile retrieved successfully",
    "data": {
        "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
        "username": "admin",
        "email": "admin@forenlytic.com",
        "full_name": "System Administrator",
        "role": "admin",
        "department": "IT",
        "is_active": true,
        "is_superuser": true,
        "last_login": "2025-09-22T06:18:01.135197",
        "created_at": "2025-09-19T04:28:50",
        "updated_at": "2025-09-22T06:18:01"
    }
}
```

**Get Cases Success:**
```json
{
    "status": 200,
    "message": "Cases retrieved successfully",
    "data": [
        {
            "id": "135df21b-c0ab-4bcc-b438-95874333f1c6",
            "case_number": "CASE-001",
            "title": "Digital Forensics Investigation",
            "status": "open",
            "priority": "high"
        }
    ],
    "pagination": {
        "total": 1,
        "page": 1,
        "per_page": 100,
        "pages": 1
    }
}
```

**Health Check Success:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "database": "connected"
}
```

### 401 Unauthorized - Authentication Errors

**Invalid Credentials:**
```json
{
    "status": 401,
    "messages": "Invalid username or password"
}
```

**Missing Token:**
```json
{
    "detail": "Not authenticated"
}
```

**Invalid Token:**
```json
{
    "detail": "Could not validate credentials"
}
```

**Expired Token:**
```json
{
    "detail": "Token has expired"
}
```

**Inactive User:**
```json
{
    "detail": "Inactive user"
}
```

**Session Expired:**
```json
{
    "detail": "Session has expired"
}
```

**Session Not Found:**
```json
{
    "status": 401,
    "message": "Session not found"
}
```

**Invalid Session:**
```json
{
    "detail": "Could not validate credentials"
}
```

**Token Not Provided:**
```json
{
    "status": 401,
    "message": "Token not provided"
}
```

**User Not Found:**
```json
{
    "status": 401,
    "message": "User not found"
}
```

**Session Inactive:**
```json
{
    "status": 401,
    "message": "Session is inactive"
}
```

### 500 Internal Server Error - Server Errors

**Database Connection Error:**
```json
{
    "status": 500,
    "message": "Database connection failed",
    "error_id": "DB_CONN_001"
}
```

**File Processing Error:**
```json
{
    "status": 500,
    "message": "Failed to process uploaded file",
    "error_id": "FILE_PROC_001"
}
```

**Report Generation Error:**
```json
{
    "status": 500,
    "message": "Failed to generate report",
    "error_id": "REPORT_GEN_001"
}
```

**Generic Server Error:**
```json
{
    "status": 500,
    "message": "An unexpected error occurred. Please try again later.",
    "error_id": "ERR_500_20250922_001"
}
```

**Critical System Error:**
```json
{
    "detail": "Internal server error"
}
```

### Other Common Error Formats

**400 Bad Request:**
```json
{
    "detail": "Validation error message"
}
```

**403 Forbidden:**
```json
{
    "detail": "Not enough permissions"
}
```

**404 Not Found:**
```json
{
    "status": 404,
    "message": "Resource not found"
}
```

**422 Unprocessable Entity:**
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "field_name"],
            "msg": "Field required",
            "input": null
        }
    ]
}
```

## Dashboard Flow

1. **Login:** POST `/api/v1/auth/token` untuk mendapatkan access token
2. **Main Dashboard:** GET `/api/v1/dashboard/` untuk menampilkan halaman utama dengan menu Analytics dan Case
3. **Case Dashboard:** GET `/api/v1/dashboard/case` untuk statistik case dengan chart dan trend
4. **Case Management:** GET `/api/v1/dashboard/case/management` untuk dashboard case management dengan tabel case
5. **Analytics Dashboard:** GET `/api/v1/dashboard/analytics` untuk dashboard analytics dengan statistik analisis
6. **Search Cases:** GET `/api/v1/cases/search?q=query` untuk mencari case di dashboard
7. **Filter Options:** GET `/api/v1/cases/filter-options` untuk mendapatkan opsi filter

## Authentication Flow

### Basic Flow
1. **Register:** POST `/api/v1/auth/register` untuk membuat akun baru
2. **Login:** POST `/api/v1/auth/token` dengan username dan password
3. **Get Tokens:** Response berisi access_token dan refresh_token
4. **Use Access Token:** Tambahkan header `Authorization: Bearer <access_token>` ke semua request yang memerlukan autentikasi
5. **Auto Refresh:** Middleware otomatis refresh token 5 menit sebelum expired
6. **Token Rotation:** Refresh token lama di-revoke, token baru diberikan
7. **Seamless UX:** User tidak perlu login ulang, token otomatis di-refresh

### Auto Refresh Flow
1. **Request dengan Token:** Frontend mengirim request dengan access_token + refresh_token
2. **Middleware Detection:** Server mendeteksi token yang akan expired
3. **Auto Refresh:** Server otomatis refresh menggunakan refresh_token
4. **Token Rotation:** Refresh token lama di-revoke, token baru dibuat
5. **Response Headers:** Server mengirim token baru via response headers
6. **Frontend Update:** Frontend otomatis update token dari headers
7. **Seamless Experience:** User tidak merasakan interupsi

### Manual Refresh Flow
1. **Token Expired:** Access token expired, request gagal dengan 401
2. **Manual Refresh:** Frontend panggil POST `/api/v1/auth/auto-refresh` dengan refresh_token
3. **New Tokens:** Server memberikan access_token dan refresh_token baru
4. **Retry Request:** Frontend retry request dengan token baru
5. **Continue:** Request berhasil dengan token baru

### Logout Flow
1. **Logout:** POST `/api/v1/auth/logout` untuk revoke session
2. **Logout All:** POST `/api/v1/auth/logout-all` untuk revoke semua session
3. **Clear Tokens:** Frontend clear access_token dan refresh_token
4. **Redirect:** Redirect ke halaman login

## Dashboard Features

### Main Dashboard
- **User Information:** Menampilkan informasi user yang sedang login
- **Menu Navigation:** Pilihan menu Analytics dan Case dengan deskripsi
- **Role-based Access:** Menu disesuaikan dengan role user

### Case Dashboard
- **Statistics Cards:** Total cases, open, closed, reopened
- **Priority Distribution:** Chart distribusi berdasarkan priority
- **Type Distribution:** Chart distribusi berdasarkan case type
- **Monthly Trend:** Trend pembuatan case per bulan
- **Recent Cases:** Daftar case terbaru dengan informasi lengkap

### Case Management Dashboard
- **Dashboard Cards:** Statistik case dalam format card
- **Case List Table:** Tabel case dengan informasi investigator, agency, tanggal
- **Search Functionality:** Pencarian case dengan query
- **Filter Options:** Filter berdasarkan status, priority, type, dll
- **Pagination:** Navigasi halaman untuk data banyak

### Analytics Dashboard
- **Analysis Statistics:** Total analisis, completed, in progress, pending
- **Evidence Statistics:** Total evidence dan yang sudah diproses
- **Analysis Types:** Distribusi berdasarkan jenis analisis
- **Recent Analyses:** Daftar analisis terbaru

## Security Features

### UUID Primary Keys
- **Enhanced Security:** Semua table menggunakan UUID sebagai primary key
- **Non-sequential:** Tidak dapat ditebak seperti auto-increment integer
- **Globally Unique:** Memastikan keunikan di seluruh sistem
- **Format:** UUID v4 (random) - contoh: `135df21b-c0ab-4bcc-b438-95874333f1c6`

### ID Security Benefits
- ✅ **No Enumeration Attacks** - Tidak dapat menebak ID berikutnya
- ✅ **Distributed Systems** - Aman untuk sistem terdistribusi
- ✅ **Data Privacy** - ID tidak mengungkapkan informasi internal
- ✅ **Collision Resistant** - Probabilitas duplikasi sangat rendah

## Auto Refresh Token System

### How It Works
1. **Login** - User login dan mendapat access_token + refresh_token
2. **Auto Detection** - Middleware mendeteksi token yang akan expired (5 menit sebelum)
3. **Auto Refresh** - Server otomatis refresh token menggunakan refresh_token
4. **Token Rotation** - Refresh token lama di-revoke, token baru diberikan
5. **Header Response** - Server mengirim token baru via response headers
6. **Frontend Update** - Frontend otomatis update token dari headers

### Frontend Implementation Examples

#### JavaScript/TypeScript
```javascript
class AutoRefreshTokenManager {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    }

    async request(url, options = {}) {
        const headers = {
            'Authorization': `Bearer ${this.accessToken}`,
            'X-Refresh-Token': this.refreshToken,
            ...options.headers
        };

        const response = await fetch(url, { ...options, headers });

        // Check if token was refreshed automatically
        if (response.headers.get('X-Token-Refreshed') === 'true') {
            const newAccessToken = response.headers.get('X-New-Access-Token');
            const newRefreshToken = response.headers.get('X-New-Refresh-Token');
            
            if (newAccessToken && newRefreshToken) {
                this.accessToken = newAccessToken;
                this.refreshToken = newRefreshToken;
                
                localStorage.setItem('access_token', this.accessToken);
                localStorage.setItem('refresh_token', this.refreshToken);
                
                console.log('🔄 Tokens refreshed automatically');
            }
        }

        return response;
    }
}
```

#### React Hook
```javascript
import { useState, useEffect, useCallback } from 'react';

const useAutoRefreshToken = (baseURL = 'http://localhost:8000') => {
    const [accessToken, setAccessToken] = useState(null);
    const [refreshToken, setRefreshToken] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const request = useCallback(async (url, options = {}) => {
        const headers = {
            'Authorization': `Bearer ${accessToken}`,
            'X-Refresh-Token': refreshToken,
            ...options.headers
        };

        const response = await fetch(url, { ...options, headers });

        // Handle auto refresh
        if (response.headers.get('X-Token-Refreshed') === 'true') {
            const newAccessToken = response.headers.get('X-New-Access-Token');
            const newRefreshToken = response.headers.get('X-New-Refresh-Token');
            
            if (newAccessToken && newRefreshToken) {
                setAccessToken(newAccessToken);
                setRefreshToken(newRefreshToken);
                localStorage.setItem('access_token', newAccessToken);
                localStorage.setItem('refresh_token', newRefreshToken);
            }
        }

        return response;
    }, [accessToken, refreshToken]);

    return { accessToken, refreshToken, isAuthenticated, request };
};
```

#### Axios Interceptor
```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
});

// Request interceptor
api.interceptors.request.use((config) => {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
    }
    
    if (refreshToken) {
        config.headers['X-Refresh-Token'] = refreshToken;
    }
    
    return config;
});

// Response interceptor
api.interceptors.response.use(
    (response) => {
        // Check if token was refreshed
        if (response.headers['x-token-refreshed'] === 'true') {
            const newAccessToken = response.headers['x-new-access-token'];
            const newRefreshToken = response.headers['x-new-refresh-token'];
            
            if (newAccessToken && newRefreshToken) {
                localStorage.setItem('access_token', newAccessToken);
                localStorage.setItem('refresh_token', newRefreshToken);
                console.log('🔄 Tokens refreshed automatically');
            }
        }
        
        return response;
    },
    async (error) => {
        if (error.response?.status === 401) {
            // Handle token refresh failure
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
        }
        
        return Promise.reject(error);
    }
);
```

## Token Management

### Access Token
- **Expiration:** 30 menit (dapat dikonfigurasi)
- **Usage:** Untuk autentikasi API requests
- **Storage:** Memory (session tracking)
- **Rotation:** Tidak ada (digunakan sampai expired)

### Refresh Token
- **Expiration:** 7 hari
- **Usage:** Untuk mendapatkan access token baru
- **Storage:** Memory (refresh token tracking)
- **Rotation:** Ya (token baru dibuat setiap refresh)

### Token Security Features
- **JWT ID (JTI):** Unique identifier untuk setiap token
- **Token Rotation:** Refresh token di-rotate setiap kali digunakan
- **Session Tracking:** Access token terikat dengan session
- **Automatic Cleanup:** Expired tokens otomatis dibersihkan
- **Auto Refresh:** Token otomatis di-refresh 5 menit sebelum expired
- **Seamless UX:** User tidak perlu login ulang

## Password Requirements

Password harus memenuhi kriteria berikut:
- **Minimum 8 karakter**
- **Setidaknya 1 huruf besar (A-Z)**
- **Setidaknya 1 huruf kecil (a-z)**
- **Setidaknya 1 angka (0-9)**
- **Setidaknya 1 karakter khusus (!@#$%^&*(),.?\":{}|<>])**
- **Tidak boleh menggunakan password umum**

## Session Management

- **Session Timeout:** 30 menit (dapat dikonfigurasi)
- **Session Tracking:** Setiap login membuat session unik dengan JWT ID
- **Auto Logout:** Session otomatis expired setelah timeout
- **Multi-Session:** User dapat login dari multiple device
- **Session Revoke:** Admin dapat revoke semua session user
- **Activity Tracking:** Last activity diupdate setiap request

## Error Codes Reference

| Error Type | Status Code | Message | Description |
|------------|-------------|---------|-------------|
| `invalid_token` | 401 | "Invalid token" | Token format tidak valid atau corrupt |
| `session_not_found` | 401 | "Session not found" | Session tidak ditemukan di server |
| `session_expired` | 401 | "Session has expired" | Session sudah melewati waktu expired |
| `session_inactive` | 401 | "Session is inactive" | Session sudah di-revoke atau dinonaktifkan |
| `token_not_provided` | 401 | "Token not provided" | Header Authorization tidak ada |
| `user_not_found` | 401 | "User not found" | User tidak ditemukan di database |
| `invalid_credentials` | 401 | "Invalid username or password" | Username/password salah |
| `inactive_user` | 400 | "Inactive user" | User account tidak aktif |
| `invalid_refresh_token` | 401 | "Invalid refresh token" | Refresh token tidak valid |
| `refresh_token_not_found` | 401 | "Refresh token not found" | Refresh token tidak ditemukan |
| `refresh_token_expired` | 401 | "Refresh token has expired" | Refresh token sudah expired |
| `refresh_token_inactive` | 401 | "Refresh token is inactive" | Refresh token sudah di-revoke |
| `invalid_token_type` | 401 | "Invalid token type" | Token type bukan refresh |

## Rate Limiting

- **Login attempts:** 5 attempts per minute per IP
- **API calls:** 1000 requests per hour per user
- **File uploads:** 10 files per hour per user

## CORS Configuration

API mendukung CORS untuk domain berikut:
- `http://localhost:3000`
- `http://localhost:8080`

## File Upload Limits

- **Maximum file size:** 100MB
- **Allowed formats:** All forensic file types
- **Storage location:** `/data/uploads/`

## Database

- **Type:** SQLite (development) / PostgreSQL (production)
- **Location:** `./data/your_database.db`
- **Backup:** Automatic daily backups

## Logging

- **Log level:** INFO
- **Log file:** `./logs/forenlytic.log`
- **Rotation:** Daily
- **Retention:** 30 days





