# API Contract Documentation
## Digital Forensics Analysis Platform - Backend API

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**API Version:** `/api/v1`

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Case Management](#case-management)
3. [Evidence Management](#evidence-management)
4. [Suspect Management (Person Management)](#suspect-management-person-management)
5. [Error Responses](#error-responses)
6. [Role-Based Access Control](#role-based-access-control)

---

## 🔐 Authentication

### Overview
All protected endpoints require Bearer Token authentication. Tokens are obtained from the login endpoint:
- **Access Token**: Valid for 24 hours (1440 minutes). Used for API authentication.
- **Refresh Token**: Valid for 7 days. Used to get new access token when expired.

**Token Flow:**
1. User logs in → receives `access_token` and `refresh_token`
2. Use `access_token` for API requests (expires after 24 hours)
3. When `access_token` expires → use `refresh_token` to get new tokens
4. After 7 days → user must login again

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Login
**Endpoint:** `POST /api/v1/auth/login`

**Description:** Authenticate user and get access token.

**Request Body:**
```json
{
  "email": "admin@gmail.com",
  "password": "admin.admin"
}
```

**Response (200 OK):**
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
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "d8IL20i8CR4UqcbtydMQ_c7u-mvEHffed9IIS-DYDBelBH3411929NaWEEi1D6p2"
  }
}
```

**Token Information:**
- `access_token`: JWT token valid for **24 hours**. Use this for API authentication.
- `refresh_token`: Token valid for **7 days**. Use this to refresh access token when expired.

**Error Responses:**

**401 Unauthorized (Invalid Credentials):**
```json
{
  "status": 401,
  "message": "Invalid credentials",
  "data": null
}
```

**400 Bad Request (Validation Error):**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### Refresh Token
**Endpoint:** `POST /api/v1/auth/refresh`

**Description:** Refresh access token using refresh token. Implements refresh token rotation for security - old refresh token will be revoked and new tokens will be issued.

**Headers:**
```
Content-Type: application/json
```

**Note:** This endpoint does NOT require Authorization header (public endpoint).

**Request Body:**
```json
{
  "refresh_token": "d8IL20i8CR4UqcbtydMQ_c7u-mvEHffed9IIS-DYDBelBH3411929NaWEEi1D6p2"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "new_refresh_token_xyz789..."
  }
}
```

**Important Notes:**
- Old refresh token will be **revoked** (cannot be used again)
- Always use the **new refresh_token** for next refresh
- New access_token is valid for **24 hours**
- New refresh_token is valid for **7 days** from now

**Error Responses:**

**401 Unauthorized (Invalid or Expired Refresh Token):**
```json
{
  "status": 401,
  "message": "Invalid or expired refresh token",
  "data": null
}
```

**Causes:**
- Refresh token is invalid
- Refresh token has expired (more than 7 days)
- Refresh token has been revoked (already used or user logged out)

**422 Validation Error (Missing Field):**
```json
{
  "detail": [
    {
      "loc": ["body", "refresh_token"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "d8IL20i8CR4UqcbtydMQ_c7u-mvEHffed9IIS-DYDBelBH3411929NaWEEi1D6p2"
  }'
```

**Example Response:**
```json
{
  "status": 200,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNzYyNTczNDU2LCJleHAiOjE3NjI1NzUyNTYsInR5cGUiOiJhY2Nlc3MifQ...",
    "refresh_token": "new_refresh_token_xyz789abc123..."
  }
}
```

**Token Rotation Flow:**
1. User calls `/refresh` with old refresh_token
2. System validates refresh_token
3. System revokes old refresh_token
4. System generates new access_token (24 hours)
5. System generates new refresh_token (7 days)
6. User receives both new tokens
7. For next refresh, use the new refresh_token (old one is revoked)

---

### Logout
**Endpoint:** `POST /api/v1/auth/logout`

**Description:** Logout user and revoke all tokens (access token and all refresh tokens). After logout, user must login again to get new tokens.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Logout successful. Access token revoked.",
  "data": null
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### Create User (Admin Only)
**Endpoint:** `POST /api/v1/auth/create-user`

**Description:** Create a new user. Only admin can access this endpoint.

**Headers:** 
- `Authorization: Bearer <admin_access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "password123",
  "fullname": "New User",
  "tag": "Investigator"
}
```

**Request Body Fields:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `email` | string | Yes | User email address | Must be valid email format |
| `password` | string | Yes | User password | Minimum 8 characters, maximum 128 characters |
| `fullname` | string | Yes | User full name | - |
| `tag` | string | Yes | User tag/category | Options: `"Admin"`, `"Investigator"`, `"Ahli Forensic"`, or other tags |

**Note:** 
- `confirm_password` field is **NOT** sent to the API. It's only used for frontend validation to ensure password matches.
- The `role` is automatically mapped from the `tag` field (see mapping below).

**Tag to Role Mapping:**
- `"Admin"` → `role: "admin"`
- `"Investigator"` → `role: "user"`
- `"Ahli Forensic"` → `role: "user"`
- Other tags → `role: "user"` (default)

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "User created successfully",
  "data": {
    "id": 4,
    "email": "newuser@example.com",
    "fullname": "New User",
    "tag": "Investigator",
    "role": "user",
    "is_active": true,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request (Invalid Input):**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**409 Conflict (Email Already Exists):**
```json
{
  "status": 409,
  "message": "User with this email already exists",
  "data": null
}
```

**403 Forbidden (Not Admin):**
```json
{
  "status": 403,
  "message": "Access denied. Admin role required.",
  "data": null
}
```

**Example Request (cURL):**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/create-user" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "email": "investigator@example.com",
    "password": "securepass123",
    "fullname": "John Investigator",
    "tag": "Investigator"
  }'
```

**Example Request (Postman):**
1. Method: `POST`
2. URL: `http://localhost:8000/api/v1/auth/create-user`
3. Headers:
   - `Authorization`: `Bearer {admin_token}`
   - `Content-Type`: `application/json`
4. Body (raw JSON):
   ```json
   {
     "email": "investigator@example.com",
     "password": "securepass123",
     "fullname": "John Investigator",
     "tag": "Investigator"
   }
   ```

**Form Fields Mapping (UI to API):**

The "Add User" form in the UI contains the following fields:

| UI Field | API Field | Required | Notes |
|----------|-----------|----------|-------|
| **Name** | `fullname` | Yes | User's full name |
| **Email** | `email` | Yes | Must be valid email format |
| **Password** | `password` | Yes | Min 8 chars, max 128 chars |
| **Confirm Password** | - | No | Frontend validation only, **NOT sent to API** |
| **Tag** (dropdown) | `tag` | Yes | Select from: `"Admin"`, `"Investigator"`, `"Ahli Forensic"` |

**Frontend Validation (Before API Call):**
- ✅ `password` and `confirm_password` must match
- ✅ `email` must be valid email format
- ✅ `password` must be at least 8 characters
- ✅ All required fields must be filled

**Backend Validation:**
- ✅ Email format validation
- ✅ Password length: 8-128 characters
- ✅ Email uniqueness check
- ✅ Admin role check (only admin can create users)

---

### Get All Users (Admin Only)

**Endpoint:** `GET /api/v1/auth/get-all-users`

**Description:** Get paginated list of all users. Only admin can access this endpoint. **Results are sorted by newest first (descending order by ID or created_at).**

**Headers:** `Authorization: Bearer <admin_access_token>`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip (pagination) |
| `limit` | integer | No | 10 | Number of records per page (max: 100) |
| `search` | string | No | - | Search keyword (searches in name, email) |
| `tag` | string | No | - | Filter by tag: `"Admin"`, `"Investigator"`, `"Ahli Forensic"` |

**Sorting:**
- Results are sorted by **ID descending** (newest first, oldest last)
- First item in the array is the most recently created user
- Last item in the array is the oldest user

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Users retrieved successfully",
  "data": [
    {
      "id": 3,
      "email": "ahliforensic@gmail.com",
      "fullname": "Ahli Forensic",
      "tag": "Ahli Forensic",
      "role": "user",
      "is_active": true,
      "created_at": "2025-11-06T18:50:13.382112Z"
    },
    {
      "id": 2,
      "email": "investigator@gmail.com",
      "fullname": "Investigator",
      "tag": "Investigator",
      "role": "user",
      "is_active": true,
      "created_at": "2025-11-06T18:50:13.382105Z"
    },
    {
      "id": 1,
      "email": "admin@gmail.com",
      "fullname": "Admin Forensic",
      "tag": "Admin",
      "role": "admin",
      "is_active": true,
      "created_at": "2025-11-06T18:50:13.38197Z"
    }
  ],
  "total": 3,
  "page": 1,
  "size": 10
}
```

**Note:** Data diurutkan dari **terbaru ke terlama** berdasarkan ID (ID terbesar = terbaru, ID terkecil = terlama).

**Error Responses:**

**403 Forbidden (Not Admin):**
```json
{
  "status": 403,
  "message": "Access denied. Admin role required.",
  "data": null
}
```

**Example Requests:**
```
GET /api/v1/auth/get-all-users?skip=0&limit=10
GET /api/v1/auth/get-all-users?search=investigator
GET /api/v1/auth/get-all-users?tag=Admin&limit=20
GET /api/v1/auth/get-all-users?skip=10&limit=5&search=admin
```

---

## 📁 Case Management

### Base Path
`/api/v1/cases`

### 1. Get Case Summary (Dashboard Statistics)

**Endpoint:** `GET /api/v1/cases/statistics/summary`

**Description:** Get summary statistics of cases by status (Open, Closed, Reopen, Investigating).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Statistics retrieved successfully",
    "data": {
        "open_cases": 2,
        "closed_cases": 0,
        "reopened_cases": 0
    },
    "total_cases": 2
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 2. Get All Cases

**Endpoint:** `GET /api/v1/cases/get-all-cases`

**Description:** Get paginated list of cases with search and filter support. Results are filtered based on user role (RBAC). **Results are sorted by newest first (descending order by ID).**

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip (pagination) |
| `limit` | integer | No | 10 | Number of records per page (max: 100) |
| `search` | string | No | - | Search keyword (searches in title, investigator, agency) |
| `status` | string | No | - | Filter by case status. Valid values: `"Open"`, `"Closed"`, `"Re-open"` atau `"Reopen"` |
| `sort_by` | string | No | - | Field to sort by. Valid values: `"created_at"`, `"id"` |
| `sort_order` | string | No | - | Sort order. Valid values: `"asc"` (oldest first), `"desc"` (newest first) |

**Status Filter Values:**
- `"Open"` - Filter cases with status "Open"
- `"Closed"` - Filter cases with status "Closed"
- `"Re-open"` atau `"Reopen"` - Filter cases with status "Re-open" (case yang dibuka kembali)

**Note:** Filter status tidak case-sensitive dan mendukung berbagai format:
- Untuk "Re-open": bisa menggunakan `"Re-open"`, `"Reopen"`, `"reopen"`, `"REOPEN"`, dll.
- Semua format akan dinormalisasi ke `"Re-open"` di database

**Sorting:**
- Default: Results are sorted by **ID descending** (newest first, oldest last)
- Jika `sort_by="created_at"` dan `sort_order="asc"`: Sort by **created_at ascending** (oldest first, newest last)
- Jika `sort_by="created_at"` dan `sort_order="desc"`: Sort by **created_at descending** (newest first, oldest last)
- Jika `sort_by` tidak disediakan: Default sort by **ID descending**

**RBAC Behavior:**
- **Admin:** Sees all cases
- **User:** Only sees cases where `main_investigator` matches their `fullname`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Cases retrieved successfully",
  "data": [
    {
      "id": 3,
      "case_number": "LC-081125-0003",
      "title": "Latest Case",
      "description": "Most recently created case",
      "status": "Open",
      "main_investigator": "Solehun",
      "agency_name": "Trikora",
      "work_unit_name": "Direktorat Reserse Kriminal Umum",
      "created_at": "15/01/2026",
      "updated_at": "08/11/2025"
    },
    {
      "id": 2,
      "case_number": "BMI-081125-0002",
      "title": "Buronan Maroko Interpol Amerika Serikat",
      "description": "Investigasi kasus buronan internasional",
      "status": "Open",
      "main_investigator": "Solehun",
      "agency_name": "Trikora",
      "work_unit_name": "Direktorat Reserse Kriminal Umum",
      "created_at": "08/11/2025",
      "updated_at": "08/11/2025"
    },
    {
      "id": 1,
      "case_number": "BMI-081125-0001",
      "title": "Buronan Maroko Interpol",
      "description": "Investigasi kasus buronan internasional",
      "status": "Open",
      "main_investigator": "Solehun",
      "agency_name": "Trikora",
      "work_unit_name": "Direktorat Reserse Kriminal Umum",
      "created_at": "12/12/2025",
      "updated_at": "08/11/2025"
    }
  ],
  "total": 53,
  "page": 1,
  "size": 10
}
```

**Note:** 
- Data diurutkan dari **terbaru ke terlama** berdasarkan ID (ID terbesar = terbaru, ID terkecil = terlama)
- Case dengan `id: 3` adalah yang terbaru (muncul pertama)
- Case dengan `id: 1` adalah yang terlama (muncul terakhir)

**Example Requests:**

**1. Get all cases (no filter):**
```
GET /api/v1/cases/get-all-cases?skip=0&limit=5
```

**2. Search cases:**
```
GET /api/v1/cases/get-all-cases?search=Buronan
```

**3. Filter by status "Open":**
```
GET /api/v1/cases/get-all-cases?status=Open&limit=20
```

**4. Filter by status "Closed":**
```
GET /api/v1/cases/get-all-cases?status=Closed
```

**5. Filter by status "Re-open" atau "Reopen":**
```
GET /api/v1/cases/get-all-cases?status=Re-open
GET /api/v1/cases/get-all-cases?status=Reopen
```

**6. Combine search and status filter:**
```
GET /api/v1/cases/get-all-cases?skip=10&limit=5&search=Maroko&status=Open
```

**7. Pagination with status filter:**
```
GET /api/v1/cases/get-all-cases?status=Open&skip=0&limit=10
GET /api/v1/cases/get-all-cases?status=Closed&skip=10&limit=10
GET /api/v1/cases/get-all-cases?status=Re-open&skip=20&limit=10
GET /api/v1/cases/get-all-cases?status=Reopen&skip=20&limit=10
```

**8. Sort by Date Created (oldest first):**
```
GET /api/v1/cases/get-all-cases?sort_by=created_at&sort_order=asc
```

**9. Sort by Date Created (newest first):**
```
GET /api/v1/cases/get-all-cases?sort_by=created_at&sort_order=desc
```

**10. Combine sorting with filter:**
```
GET /api/v1/cases/get-all-cases?status=Open&sort_by=created_at&sort_order=asc
GET /api/v1/cases/get-all-cases?search=Buronan&sort_by=created_at&sort_order=desc
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 3. Get Case Detail Comprehensive

**Endpoint:** `GET /api/v1/cases/get-case-detail-comprehensive/{case_id}`

**Description:** Get comprehensive details of a specific case including persons of interest and case logs.

**Note:** Field `case_notes` dalam response akan berisi nilai notes jika sudah disimpan melalui endpoint `/api/v1/cases/save-notes` atau `/api/v1/cases/edit-notes`, atau `null` jika belum ada notes.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Unique case identifier (in URL path) |

**Note:** 
- `case_id` adalah **path parameter** (di URL path), bukan query parameter
- URL format: `/api/v1/cases/get-case-detail-comprehensive/{case_id}`
- Contoh: `/api/v1/cases/get-case-detail-comprehensive/1`
- Konsisten dengan endpoint lain: `/get-person/{person_id}`, `/update-case/{case_id}`, dll.

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case detail retrieved successfully",
  "data": {
    "case": {
      "id": 1,
      "case_number": "BMI-081125-0001",
      "title": "Buronan Maroko Interpol",
      "description": "Tersangka diduga terlibat dalam kasus perdagangan narkotika lintas negara...",
      "status": "Open",
      "case_officer": "Solehun",
      "agency": "Trikora",
      "work_unit": "Dirjen Imigrasi IV",
      "created_date": "20/12/2025"
    },
    "persons_of_interest": [
      {
        "id": 1,
        "name": "Mandeep Singh",
        "person_type": "Suspect",
        "analysis": [
          {
            "evidence_id": "342344442",
            "notes": "Berdasarkan rekaman CCTV tanggal 10 September 2025...",
            "status": "Analysis"
          }
        ]
      },
      {
        "id": 2,
        "name": "Nathalie",
        "person_type": "Witness",
        "analysis": []
      }
    ],
    "case_log": [
      {
        "id": 1,
        "case_id": 1,
        "action": "Open",
        "status": "Open",
        "created_at": "9 Mei 2025, 18:00"
      },
      {
        "id": 2,
        "case_id": 1,
        "action": "Edit",
        "edit": [
          {
            "changed_by": "Wisnu",
            "change_detail": "Adding person Nathalie"
          }
        ],
        "status": "Open",
        "created_at": "16 Mei 2025, 12:00"
      }
    ],
    "case_notes": "Berdasarkan rekaman CCTV tanggal 10 September 2025, tersangka terlihat memasuki gedung pada pukul 14:30 WIB. Investigasi lebih lanjut diperlukan untuk mengidentifikasi aktivitas tersangka di dalam gedung."
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

**Example Requests:**

**1. Get case detail dengan ID 1:**
```
GET http://localhost:8000/api/v1/cases/get-case-detail-comprehensive/1
Authorization: Bearer <access_token>
```

**2. Get case detail dengan ID 2:**
```
GET http://localhost:8000/api/v1/cases/get-case-detail-comprehensive/2
Authorization: Bearer <access_token>
```

**Note:** 
- `case_id` adalah **path parameter**, jadi langsung di URL path
- Format URL: `/get-case-detail-comprehensive/{case_id}`
- **JANGAN** gunakan query parameter seperti `?case_id=1` (akan error "Not Found")
- Konsisten dengan endpoint lain yang menggunakan path parameter untuk resource identification

---

### 4. Create Case

**Endpoint:** `POST /api/v1/cases/create-case`

**Description:** Create a new case. Case number can be auto-generated or manually provided.

**Auto-Generated Case Number Format:**
Jika `auto_generate_case_number: true` atau `case_number` tidak disediakan, sistem akan otomatis generate case number dengan format:
- **Format:** `{PREFIX}-{DATE}-{UNIQUE_NUMBER}`
- **PREFIX:** Diambil dari 2 atau 3 huruf pertama dari 2 atau 3 kata pertama pada `title` (huruf kapital)
  - Contoh: "Buronan Maroko Interpol" → "BMI" (B dari "Buronan", M dari "Maroko", I dari "Interpol")
  - Jika title lebih dari 3 kata, hanya 3 kata pertama yang digunakan
  - Contoh: "Buronan Maroko Interpol Amerika Serikat" → "BMI" (tetap hanya 3 kata pertama)
- **DATE:** Format tanggal `DDMMYY` (hari-bulan-tahun 2 digit)
  - Contoh: 12 Desember 2025 → "121225"
- **UNIQUE_NUMBER:** Nomor urut 4 digit dengan leading zeros
  - Contoh: "0001", "0002", "0003", dst.

**Contoh Auto-Generated Case Number:**
- Title: "Buronan Maroko Interpol" → `BMI-121225-0001`
- Title: "Buronan Maroko Interpol Amerika Serikat" → `BMI-121225-0001` (hanya ambil 3 kata pertama)
- Title: "Kasus Penipuan Online" → `KPO-121225-0002`

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body (Auto-Generate Case Number):**
```json
{
  "title": "Buronan Maroko Interpol",
  "description": "Investigasi kasus buronan internasional",
  "main_investigator": "Solehun",
  "agency_name": "Trikora",
  "work_unit_name": "Direktorat Reserse Kriminal Umum"
}
```

**Note:** Jika `case_number` tidak disediakan, sistem akan otomatis generate case number berdasarkan format di atas.

**OR (Manual Case Number):**
```json
{
  "title": "Buronan Maroko Interpol",
  "description": "Investigasi kasus buronan internasional",
  "main_investigator": "Solehun",
  "agency_name": "Trikora",
  "work_unit_name": "Direktorat Reserse Kriminal Umum",
  "case_number": "BMI-121225-0001"
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Case created successfully",
  "data": {
    "id": 1,
    "case_number": "BMI-121225-0001",
    "title": "Buronan Maroko Interpol",
    "description": "Investigasi kasus buronan internasional",
    "status": "Open",
    "main_investigator": "Solehun",
    "agency_name": "Trikora",
    "work_unit_name": "Direktorat Reserse Kriminal Umum",
    "created_at": "2025-12-12T10:30:00Z",
    "updated_at": "2025-12-12T10:30:00Z"
  }
}
```

**Contoh: Title dengan lebih dari 3 kata**

Jika title memiliki lebih dari 3 kata, case_number tetap hanya menggunakan 3 kata pertama:

**Request:**
```json
{
  "title": "Buronan Maroko Interpol Amerika Serikat",
  "description": "Investigasi kasus buronan internasional",
  "main_investigator": "Solehun",
  "agency_name": "Trikora",
  "work_unit_name": "Direktorat Reserse Kriminal Umum"
}
```

**Response:**
```json
{
  "status": 201,
  "message": "Case created successfully",
  "data": {
    "id": 2,
    "case_number": "BMI-121225-0002",
    "title": "Buronan Maroko Interpol Amerika Serikat",
    ...
  }
}
```

**Note:** Case number tetap `BMI-121225-0002` karena hanya mengambil 3 kata pertama: "Buronan", "Maroko", "Interpol" → "BMI".

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**409 Conflict (Case Number Already Exists):**
```json
{
  "status": 409,
  "message": "Case number 'REG/123/2024/DRKUM' already exists",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 5. Update Case

**Endpoint:** `PUT /api/v1/cases/update-case/{case_id}`

**Description:** Update an existing case. All fields in request body are optional (partial update). Only fields provided in the request body will be updated.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Unique case identifier (in URL path) |

**Request Body (all fields optional - partial update):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Case title |
| `description` | string | No | Case description |
| `main_investigator` | string | No | Main investigator name |
| `case_number` | string | No | Case number (manual) |
| `agency_id` | integer | No | Agency ID |
| `work_unit_id` | integer | No | Work unit ID |
| `agency_name` | string | No | Agency name (free text, auto-create if not exists) |
| `work_unit_name` | string | No | Work unit name (free text, auto-create if not exists) |

**Note:**
- `case_id` adalah **path parameter** (di URL path), bukan di request body
- Semua field di request body adalah **optional** (partial update)
- Hanya field yang diisi yang akan di-update
- Field yang tidak diisi akan tetap seperti semula
- URL format: `/api/v1/cases/update-case/{case_id}`
- Contoh: `/api/v1/cases/update-case/1`

**Request Body Examples:**

**Example 1: Update title saja**
```json
{
  "title": "Updated Case Title"
}
```

**Example 2: Update multiple fields**
```json
{
  "title": "Updated Case Title",
  "description": "Updated description",
  "main_investigator": "New Investigator"
}
```

**Example 3: Update agency dan work unit**
```json
{
  "agency_name": "New Agency",
  "work_unit_name": "New Work Unit"
}
```

**Example 4: Update semua field**
```json
{
  "title": "Updated Case Title",
  "description": "Updated description",
  "main_investigator": "New Investigator",
  "agency_name": "New Agency",
  "work_unit_name": "New Work Unit"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case updated successfully",
  "data": {
    "id": 1,
    "case_number": "BMI-081125-0001",
    "title": "Updated Case Title",
    "description": "Updated description",
    "status": "Open",
    "main_investigator": "New Investigator",
    "agency_name": "New Agency",
    "work_unit_name": "New Work Unit",
    "created_at": "08/11/2025",
    "updated_at": "08/11/2025"
  }
}
```

**Note:**
- `created_at` dan `updated_at` menggunakan format "DD/MM/YYYY" (string)
- Format konsisten dengan response `get-all-cases`

**Example Requests:**

**1. Update case dengan ID 1 (update title saja):**
```
PUT http://localhost:8000/api/v1/cases/update-case/1
Authorization: Bearer <access_token>
Content-Type: application/json

Body (raw JSON):
{
  "title": "Updated Case Title"
}
```

**2. Update case dengan ID 2 (update multiple fields):**
```
PUT http://localhost:8000/api/v1/cases/update-case/2
Authorization: Bearer <access_token>
Content-Type: application/json

Body (raw JSON):
{
  "title": "Updated Case Title",
  "description": "Updated description",
  "main_investigator": "New Investigator"
}
```

**3. Update case dengan ID 3 (update agency dan work unit):**
```
PUT http://localhost:8000/api/v1/cases/update-case/3
Authorization: Bearer <access_token>
Content-Type: application/json

Body (raw JSON):
{
  "agency_name": "New Agency",
  "work_unit_name": "New Work Unit"
}
```

**Note:**
- `case_id` adalah **path parameter**, jadi langsung di URL path
- Format URL: `/update-case/{case_id}`
- **JANGAN** gunakan query parameter seperti `?case_id=1` (akan error "Not Found")
- Request body menggunakan **raw JSON** (bukan form-data)
- Semua field di body adalah optional (partial update)

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 6. Export Case Details PDF

**Endpoint:** `GET /api/v1/cases/export-case-details-pdf`

**Description:** Export comprehensive case details as PDF document. Includes case information, persons of interest, case logs, and notes.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Unique case identifier |

**Response (200 OK):**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="case_details_{case_id}_{timestamp}.pdf"`

The response is a PDF file that can be downloaded directly.

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

**Example Request:**
```
GET /api/v1/cases/export-case-details-pdf?case_id=1
Authorization: Bearer {access_token}
```

---

### 7. Save Case Notes

**Endpoint:** `POST /api/v1/cases/save-notes`

**Description:** Save or update notes for a specific case.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "case_id": 1,
  "notes": "Berdasarkan rekaman CCTV tanggal 10 September 2025, tersangka terlihat memasuki gedung pada pukul 14:30 WIB. Investigasi lebih lanjut diperlukan untuk mengidentifikasi aktivitas tersangka di dalam gedung."
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case notes saved successfully",
    "data": {
        "case_id": 1,
        "case_number": "BM-081125-0001",
        "case_title": "Buronan Maroko",
        "notes": "Berdasarkan rekaman CCTV tanggal 10 September 2025, tersangka terlihat memasuki gedung pada pukul 14:30 WIB. Investigasi lebih lanjut diperlukan untuk mengidentifikasi aktivitas tersangka di dalam gedung.",
        "updated_at": "2025-11-08T19:25:34.990264+07:00"
    }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Notes cannot be empty",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to save case notes: {error_message}",
  "data": null
}
```

---

### 8. Edit Case Notes

**Endpoint:** `PUT /api/v1/cases/edit-notes`

**Description:** Update notes for a specific case.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "case_id": 1,
  "notes": "Updated notes: Berdasarkan rekaman CCTV tanggal 10 September 2025, tersangka terlihat memasuki gedung pada pukul 14:30 WIB. Investigasi lebih lanjut menunjukkan bahwa tersangka melakukan aktivitas mencurigakan di lantai 3."
}
```

**Response (200 OK):**
```json
{
    "status": 200,
    "message": "Case notes updated successfully",
    "data": {
        "case_id": 1,
        "case_number": "BM-081125-0001",
        "case_title": "Buronan Maroko",
        "notes": "Updated summary: Berdasarkan rekaman CCTV tanggal 10 September 2025, tersangka terlihat memasuki gedung pada pukul 14:30 WIB. Investigasi lebih lanjut menunjukkan bahwa tersangka melakukan aktivitas mencurigakan di lantai 3.",
        "updated_at": "2025-11-08T19:27:00.576546+07:00"
    }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Notes cannot be empty",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to edit case notes: {error_message}",
  "data": null
}
```

**Note:**
- Endpoint `save-notes` dan `edit-notes` memiliki fungsi yang sama (save atau update notes)
- Gunakan `save-notes` untuk membuat notes baru atau mengupdate notes yang sudah ada
- Gunakan `edit-notes` untuk mengupdate notes yang sudah ada (lebih eksplisit untuk operasi update)

**Example Request:**
```
POST http://localhost:8000/api/v1/cases/save-notes
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "case_id": 1,
  "notes": "Berdasarkan rekaman CCTV tanggal 10 September 2025, tersangka terlihat memasuki gedung pada pukul 14:30 WIB. Investigasi lebih lanjut diperlukan untuk mengidentifikasi aktivitas tersangka di dalam gedung."
}
```

**Example Request (Edit Notes):**
```
PUT http://localhost:8000/api/v1/cases/edit-notes
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "case_id": 1,
  "notes": "Updated notes: Berdasarkan rekaman CCTV tanggal 10 September 2025, tersangka terlihat memasuki gedung pada pukul 14:30 WIB. Investigasi lebih lanjut menunjukkan bahwa tersangka melakukan aktivitas mencurigakan di lantai 3."
}
```

---

## 📝 Case Log Management

### Base Path
`/api/v1/case-logs`

### 9. Get Case Logs

**Endpoint:** `GET /api/v1/case-logs/case/logs/{case_id}`

**Description:** Retrieve all log entries for a specific case with pagination support.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Unique case identifier |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip (for pagination) |
| `limit` | integer | No | 10 | Number of records to return (max: 100) |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case logs retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_id": 1,
      "action": "Open",
      "notes": "Kasus sudah ditutup",
      "status": "Open",
      "created_at": "9 Mei 2025, 10:00"
    },
    {
      "id": 2,
      "case_id": 1,
      "action": "Closed",
      "status": "Closed",
      "created_at": "12 Mei 2025, 14:00"
    },
    {
      "id": 3,
      "case_id": 1,
      "action": "Re-Open",
      "notes": "Kasus dibuka kembali",
      "status": "Re-Open",
      "created_at": "16 Mei 2025, 12:00"
    },
    {
      "id": 4,
      "case_id": 1,
      "action": "Edit",
      "edit": [
        {
          "changed_by": "Admin Forensic",
          "change_detail": "Adding person Nathalie"
        }
      ],
      "status": "Edit",
      "created_at": "16 Mei 2025, 12:00"
    },
    {
      "id": 5,
      "case_id": 1,
      "action": "Edit",
      "edit": [
        {
          "changed_by": "Admin Forensic",
          "change_detail": "Adding evidence 3234222"
        }
      ],
      "status": "Edit",
      "created_at": "16 Mei 2025, 09:00"
    }
  ],
  "total": 5,
  "page": 1,
  "size": 10
}
```

**Response Fields:**
- `id`: Log entry unique identifier
- `case_id`: Case identifier
- `action`: Action performed (e.g., "Open", "Closed", "Re-open", "Edit")
- `edit`: (Optional) Array of edit details, only included if `changed_by` or `change_detail` has value. Each containing:
  - `changed_by`: User who made the change (only populated if action is "Edit" and status matches current case status)
  - `change_detail`: Detail of the change (e.g., "Adding person Nathalie", "Adding evidence 3234222", only populated if action is "Edit" and status matches current case status)
- `notes`: (Optional) Additional notes, only included if notes has value (not empty)
- `status`: Case status at the time of log creation
- `created_at`: Date and time formatted in Indonesian: "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")

**Note on Conditional Fields:**
- Field `edit` **tidak akan muncul** jika `changed_by` dan `change_detail` keduanya kosong
- Field `notes` **tidak akan muncul** jika notes kosong atau tidak ada
- Ini membuat response lebih clean dan hanya menampilkan field yang relevan

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

**Example Request:**
```
GET http://localhost:8000/api/v1/case-logs/case/logs/1?skip=0&limit=10
Authorization: Bearer {access_token}
```

**Note:**
- Logs are ordered by `created_at` in descending order (newest first)
- Date format: Indonesian format "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")
- Case logs are automatically created when:
  - Case is created (initial "Open" log)
  - Case status is updated (via update-log endpoint)
  - Evidence is added to a case
  - Person is added to a case

---

### 10. Get Case Log Detail (Get Notes for Modal)

**Endpoint:** `GET /api/v1/case-logs/log/{log_id}`

**Description:** Get detail of a specific case log entry including notes. This endpoint is specifically designed to retrieve case log details when the "Notes" button is clicked in the case log UI, displaying the notes content in a modal dialog. Returns all case log information including the notes field which can be empty or contain text.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `log_id` | integer | Yes | Unique case log identifier |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case log detail retrieved successfully",
  "data": {
    "id": 3,
    "case_id": 1,
    "action": "Closed",
    "notes": "kasus sudah di tutup",
    "status": "Closed",
    "created_at": "16 Mei 2025, 12:00"
  }
}
```

**Response Fields:**
- `id`: Log entry unique identifier
- `case_id`: Case identifier
- `action`: Action performed (e.g., "Open", "Closed", "Re-open", "Edit")
- `edit`: (Optional) Array of edit details, only included if `changed_by` or `change_detail` has value. Each containing:
  - `changed_by`: User who made the change (only populated if action is "Edit" and status matches current case status)
  - `change_detail`: Detail of the change (only populated if action is "Edit" and status matches current case status)
- `notes`: (Optional) Notes for the case log entry, only included if notes has value (not empty)
- `status`: Case status at the time of log creation
- `created_at`: Date and time formatted in Indonesian: "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")

**Note on Conditional Fields:**
- Field `edit` **tidak akan muncul** jika `changed_by` dan `change_detail` keduanya kosong
- Field `notes` **tidak akan muncul** jika notes kosong atau tidak ada

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case log not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

**Example Request:**
```
GET http://localhost:8000/api/v1/case-logs/log/3
Authorization: Bearer {access_token}
```

**Note:**
- **Primary Use Case:** This endpoint is used to display notes in a modal dialog when the "Notes" button is clicked on a case log entry in the UI
- Returns a single case log entry with all its details including the `notes` field
- The `notes` field can be empty string `""` if no notes have been added, or contain text if notes exist
- The `changed_by` and `change_detail` fields in the `edit` array will only contain values if:
  - `action` is "Edit" AND
  - `status` matches the current case status (status terakhir)
- Date format: Indonesian format "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")
- **UI Integration:** Frontend should call this endpoint when user clicks the "Notes" button on a case log entry to populate the modal with the notes content

---

### 11. Change Case Log (Update Case Status with Notes)

**Endpoint:** `PUT /api/v1/case-logs/change-log/{case_id}`

**Description:** Update case status and automatically create a new case log entry with required notes/alasan. This endpoint updates the case status in the `cases` table and creates a log entry to track the status change. **Notes/alasan is required** when changing the case status - users must provide a reason for the status change. The notes will be saved in the case log entry and will appear in the case detail's case_log array.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Unique case identifier |

**Request Body:**
```json
{
  "status": "Closed",
  "notes": "kasus sudah di tutup"
}
```

**Request Body Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | Case status (Open, Closed, Re-open) |
| `notes` | string | Yes | **Wajib** - Alasan/notes untuk perubahan status case log entry |

**Valid Status Values:**
- `"Open"`: Case is open and active
- `"Closed"`: Case is closed
- `"Re-open"`: Case is reopened (case-insensitive, accepts "Re-open", "Reopen", "re-open", "reopen")

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Case log updated successfully",
  "data": {
    "id": 6,
    "case_id": 1,
    "action": "Closed",
    "notes": "kasus sudah di tutup",
    "status": "Closed",
    "created_at": "16 Mei 2025, 15:30"
  }
}
```

**Response Fields:**
- `id`: New log entry unique identifier
- `case_id`: Case identifier
- `action`: Action performed (same as status value)
- `edit`: (Optional) Array of edit details, only included if `changed_by` or `change_detail` has value. Each containing:
  - `changed_by`: User who made the change (only populated if action is "Edit" and status matches current case status)
  - `change_detail`: Detail of the change (only populated if action is "Edit" and status matches current case status)
- `notes`: Notes/alasan yang wajib diisi ketika mengubah status (always included in change-log response since it's required)
- `status`: New case status
- `created_at`: Date and time formatted in Indonesian: "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")

**Error Responses:**

**400 Bad Request (Invalid Status):**
```json
{
  "status": 400,
  "message": "Invalid status 'InvalidStatus'. Valid values are: ['Open', 'Closed', 'Re-open'] (case-sensitive)",
  "data": null
}
```

**400 Bad Request (Notes Required):**
```json
{
  "status": 400,
  "message": "Notes/alasan wajib diisi ketika mengubah status case",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

**Example Request (With Notes):**
```
PUT http://localhost:8000/api/v1/case-logs/change-log/1
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "status": "Closed",
  "notes": "kasus sudah di tutup"
}
```

**Example Request (Re-open with Notes):**
```
PUT http://localhost:8000/api/v1/case-logs/change-log/1
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "status": "Re-open",
  "notes": "Kasus dibuka kembali untuk investigasi lanjutan"
}
```

**Note:**
- **Important:** Field `notes` adalah **WAJIB** ketika mengubah status case. User harus memberikan alasan untuk perubahan status.
- This endpoint updates the case status in the `cases` table and creates a new log entry
- The `action` field in the log entry will match the new status value (e.g., "Closed", "Open", "Re-open")
- The `notes` field is **required** and cannot be empty. It must contain a reason/alasan for the status change
- The notes will appear in the `case_log` array when retrieving case detail via `get-case-detail-comprehensive`
- The `changed_by` and `change_detail` fields in the `edit` array will only contain values if:
  - `action` is "Edit" AND
  - `status` matches the current case status (status terakhir)
- For status change actions (Open, Closed, Re-open), `changed_by` and `change_detail` will be empty strings
- Status validation is case-insensitive for common variations (e.g., "reopen", "Re-open", "Re-open" all map to "Re-open")
- Date format: Indonesian format "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")
- **UI Flow:** When user changes case status, the UI must require them to input notes/alasan before submitting

---

## 🔍 Evidence Management

### Base Path
`/api/v1/evidence`

### 1. Get Evidence List

**Endpoint:** `GET /api/v1/evidence/get-evidence-list`

**Description:** Get paginated list of evidences with search and filter support. **Results are sorted by newest first (descending order by ID).**

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip (pagination) |
| `limit` | integer | No | 10 | Number of records per page (max: 100) |
| `search` | string | No | - | Search keyword (searches in evidence ID, case name, investigator, agency) |
| `status` | string | No | - | Filter by status |
| `evidence_type_id` | integer | No | - | Filter by evidence type ID |

**Sorting:**
- Results are sorted by **ID descending** (newest first, oldest last)
- First item in the array is the most recently created evidence
- Last item in the array is the oldest evidence

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence list retrieved successfully",
  "data": [
    {
      "id": 5,
      "evidence_id": "34569809",
      "evidence_number": "EVID-005",
      "case_name": "Data Leak",
      "investigator": "Solehun",
      "agency": "Trikora",
      "title": "Evidence Title",
      "status": "Collected",
      "date_created": "12/12/2025",
      "created_at": "2025-12-12T10:30:00Z"
    },
    {
      "id": 4,
      "evidence_id": "34569809",
      "evidence_number": "EVID-004",
      "case_name": "Data Leak",
      "investigator": "Solehun",
      "agency": "Trikora",
      "title": "Evidence Title",
      "status": "Collected",
      "date_created": "12/12/2025",
      "created_at": "2025-12-12T09:30:00Z"
    },
    {
      "id": 2,
      "evidence_id": "12339813",
      "evidence_number": "EVID-002",
      "case_name": "Illegal Drone Flight",
      "investigator": "Agus Smith",
      "agency": "Police HQ",
      "title": "Evidence Title",
      "status": "Collected",
      "date_created": "12/12/2025",
      "created_at": "2025-12-12T08:30:00Z"
    },
    {
      "id": 1,
      "evidence_id": "12336728",
      "evidence_number": "EVID-001",
      "case_name": "Illegal Drone Flight",
      "investigator": "Agus Smith",
      "agency": "Police HQ",
      "title": "Evidence Title",
      "status": "Collected",
      "date_created": "12/12/2025",
      "created_at": "2025-12-12T07:30:00Z"
    }
  ],
  "total": 21,
  "page": 1,
  "size": 10
}
```

**Note:** 
- Data diurutkan dari **terbaru ke terlama** berdasarkan ID (ID terbesar = terbaru, ID terkecil = terlama)
- Evidence dengan `id: 5` adalah yang terbaru (muncul pertama)
- Evidence dengan `id: 1` adalah yang terlama (muncul terakhir)
- Field `date_created` menggunakan format `DD/MM/YYYY` untuk tampilan UI

**Example Requests:**
```
GET /api/v1/evidence/get-evidence-list?skip=0&limit=10
GET /api/v1/evidence/get-evidence-list?search=Data%20Leak
GET /api/v1/evidence/get-evidence-list?status=Collected&limit=20
GET /api/v1/evidence/get-evidence-list?skip=10&limit=5&search=Agus
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 2. Create Evidence

**Endpoint:** `POST /api/v1/evidence/create-evidence`

**Description:** Create a new evidence item and associate it with a case.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "case_id": 1,
  "evidence_id": "32342223",
  "evidence_number": "EVID-001",
  "title": "Handphone A",
  "description": "Smartphone dari tersangka",
  "evidence_type_id": 1,
  "status": "Collected",
  "source": "Handphone",
  "hash_value": "sha256:abcdef12345...",
  "file_path": "/data/evidence/evidence_001.zip"
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Evidence created successfully",
  "data": {
    "case_id": 1,
    "evidence_id": "32342223",
    "evidence_number": "EVID-001",
    "title": "Handphone A",
    "description": "Smartphone dari tersangka",
    "status": "Collected",
    "source": "Handphone"
  }
}
```

**Note:** This endpoint automatically creates a case log entry when evidence is added.

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**404 Not Found (Case not found):**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 3. Get Evidence Details by ID

**Endpoint:** `GET /api/v1/evidence/get-evidence-by-id`

**Description:** Get comprehensive details of a specific evidence item including notes, chain of custody, investigation hypothesis, tools used, and analysis results.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Unique evidence identifier |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence retrieved successfully",
  "data": {
    "id": 1,
    "evidence_id": "32342223",
    "evidence_number": "EVID-001",
    "title": "Handphone A",
    "description": "Smartphone dari tersangka",
    "status": "Collected",
    "source": "Handphone",
    "investigator": "Solehun",
    "date_created": "20/12/2025",
    "person_related": "Dwiky",
    "case_related": "Buronan Maroko Interpol",
    "case_id": 1,
    "evidence_type": "File",
    "evidence_detail": "081902938201",
    "created_at": "2025-12-20T10:00:00Z",
    "updated_at": "2025-12-20T10:00:00Z",
    "notes": {
      "id": "33242352",
      "thumbnail": "/data/thumbnails/evidence_1_map.png",
      "text": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian."
    },
    "chain_of_custody": {
      "acquisition": {
        "date": "16 Mei 2025, 12:00",
        "investigator": "Solehun",
        "location": "Bandara Soekarno Hatta Terminal 1",
        "status": "Recorded"
      },
      "preparation": {
        "date": "16 Mei 2025, 14:00",
        "investigator": "Solehun",
        "location": "Forensic Lab",
        "status": "Recorded"
      },
      "extraction": {
        "date": "17 Mei 2025, 10:00",
        "investigator": "Solehun",
        "location": "Forensic Lab",
        "status": "Recorded"
      },
      "analysis": {
        "date": "18 Mei 2025, 15:00",
        "investigator": "Solehun",
        "location": "Forensic Lab",
        "status": "Recorded"
      }
    },
    "current_stage": {
      "stage": "Preparation",
      "location": "Bandara Soekarno Hatta Terminal 1",
      "investigation_hypothesis": [
        "1. Perangkat seluler tersangka kemungkinan besar menyimpan data GPS yang menunjukkan lokasi pada saat kejadian",
        "2. Data GPS dapat digunakan untuk membuktikan keberadaan tersangka di TKP",
        "3. Perangkat seluler mungkin terhubung dengan perangkat lain yang relevan dengan kasus"
      ],
      "tools_used": [
        "Google Earth",
        "Axiom Magnet Forensics",
        "Power BI"
      ],
      "extraction_results": {
        "file_name": "Handphone A",
        "file_size": "67 Gb",
        "file_path": "/data/extractions/evidence_1_extraction.zip"
      },
      "analysis_results": {
        "hypothesis": "Menemukan hubungan tersangka dengan temannya.",
        "result": "Tersangka terkait dengan suspect A, B, dan C.",
        "report_file": {
          "file_name": "PDF Report",
          "file_size": "14 Mb",
          "file_path": "/data/reports/evidence_1_analysis.pdf"
        }
      },
      "notes": "Penting untuk memastikan dokumentasi lengkap dan chain of custody yang jelas untuk menjaga integritas bukti digital."
    },
    "gallery": [
      {
        "id": 1,
        "url": "/data/gallery/evidence_1_photo1.jpg",
        "thumbnail": "/data/gallery/thumbnails/evidence_1_photo1_thumb.jpg",
        "description": "Evidence bag sealed"
      },
      {
        "id": 2,
        "url": "/data/gallery/evidence_1_photo2.jpg",
        "thumbnail": "/data/gallery/thumbnails/evidence_1_photo2_thumb.jpg",
        "description": "Device in evidence bag"
      }
    ]
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 4. Log Custody Event

**Endpoint:** `POST /api/v1/evidence/custody-events`

**Description:** Log a chain of custody event for an evidence item.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body (all fields required, including `evidence_id`):**
```json
{
  "evidence_id": 1,
  "event_type": "Acquisition",
  "event_date": "2025-05-16T12:00:00Z",
  "person_name": "Solehan",
  "person_title": "Investigator",
  "person_id": 1,
  "location": "Bandara Soekarno Hatta Terminal 1",
  "location_type": "Airport",
  "action_description": "Seizure of evidence",
  "tools_used": "Evidence bag, Camera",
  "conditions": "Perangkat seluler tidak tersambung ke internet",
  "duration": "2 hours",
  "transferred_to": "Forensic Lab",
  "transferred_from": "Crime Scene",
  "transfer_reason": "For analysis",
  "witness_name": "John Doe",
  "witness_signature": "signature_hash",
  "verification_method": "Digital signature",
  "created_by": "admin@gmail.com",
  "notes": "Evidence properly sealed and documented"
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Custody event logged successfully",
  "data": {
    "evidence_id": 1,
    "event_type": "Acquisition",
    "event_date": "2025-05-16T12:00:00Z",
    "person_name": "Solehan",
    "location": "Bandara Soekarno Hatta Terminal 1",
    "action_description": "Seizure of evidence",
    "is_immutable": true,
    "is_verified": false,
    "log_hash": "sha256_hash_here",
    "created_at": "2025-05-16T12:00:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 5. Get Custody Chain

**Endpoint:** `GET /api/v1/evidence/custody-chain`

**Description:** Get complete chain of custody for an evidence item.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Unique evidence identifier |

**Response (200 OK):**
```json
{
  "evidence_id": 1,
  "evidence_number": "EVID-001",
  "evidence_title": "Handphone A",
  "custody_chain": [
    {
      "id": 1,
      "evidence_id": 1,
      "event_type": "Acquisition",
      "event_date": "2025-05-16T12:00:00Z",
      "person_name": "Solehan",
      "location": "Bandara Soekarno Hatta Terminal 1",
      "action_description": "Seizure of evidence",
      "tools_used": "Evidence bag, Camera",
      "is_verified": false,
      "created_at": "2025-05-16T12:00:00Z"
    },
    {
      "id": 2,
      "evidence_id": 1,
      "event_type": "Preparation",
      "event_date": "2025-05-16T14:00:00Z",
      "person_name": "Solehan",
      "location": "Forensic Lab",
      "action_description": "Evidence preparation",
      "tools_used": "Write blocker",
      "is_verified": true,
      "created_at": "2025-05-16T14:00:00Z"
    }
  ],
  "chain_integrity": true,
  "total_events": 2,
  "first_event": { /* first event object */ },
  "last_event": { /* last event object */ }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 6. Get Custody Events

**Endpoint:** `GET /api/v1/evidence/custody-events`

**Description:** Get paginated list of custody events for an evidence item.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Unique evidence identifier |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip |
| `limit` | integer | No | 50 | Number of records per page (max: 100) |
| `event_type` | string | No | - | Filter by event type |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Custody events retrieved successfully",
  "data": [
    {
      "id": 1,
      "evidence_id": 1,
      "event_type": "Acquisition",
      "event_date": "2025-05-16T12:00:00Z",
      "person_name": "Solehan",
      "location": "Bandara Soekarno Hatta Terminal 1",
      "action_description": "Seizure of evidence",
      "tools_used": "Evidence bag, Camera",
      "is_verified": false,
      "created_at": "2025-05-16T12:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "size": 50
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 7. Update Custody Event

**Endpoint:** `PUT /api/v1/evidence/custody-events`

**Description:** Update a custody event (limited fields, maintains immutability).

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body (all fields optional, but `evidence_id` and `custody_id` are required):**
```json
{
  "evidence_id": 1,
  "custody_id": 1,
  "is_verified": true,
  "notes": "Updated notes"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Custody event updated successfully",
  "data": {
    "id": 1,
    "evidence_id": 1,
    "updated_fields": {
      "is_verified": true,
      "notes": "Updated notes"
    }
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found or Custody event with ID {custody_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 8. Generate Custody Report

**Endpoint:** `POST /api/v1/evidence/custody-report`

**Description:** Generate a custody report (PDF) for an evidence item.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body (all fields required, including `evidence_id`):**
```json
{
  "evidence_id": 1,
  "report_type": "Full Chain of Custody",
  "report_title": "Evidence Custody Report - EVID-001",
  "report_description": "Complete chain of custody documentation",
  "compliance_standard": "ISO 27037",
  "generated_by": "admin@gmail.com"
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Custody report generated successfully",
  "data": {
    "evidence_id": 1,
    "report_type": "Full Chain of Custody",
    "report_title": "Evidence Custody Report - EVID-001",
    "report_file_path": "/data/reports/custody_evidence_1_20250115_143022.pdf",
    "is_verified": false,
    "generated_date": "2025-01-15T14:30:22Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 10. Get Evidence Types

**Endpoint:** `GET /api/v1/evidence/types`

**Description:** Get list of available evidence types (for dropdown selection in forms).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence types retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "File"
    },
    {
      "id": 2,
      "name": "Device"
    },
    {
      "id": 3,
      "name": "Document"
    },
    {
      "id": 4,
      "name": "Image"
    },
    {
      "id": 5,
      "name": "Video"
    }
  ]
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 11. Get Evidence Sources

**Endpoint:** `GET /api/v1/evidence/sources`

**Description:** Get list of available evidence sources (for dropdown selection in forms).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence sources retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Handphone"
    },
    {
      "id": 2,
      "name": "CCTV"
    },
    {
      "id": 3,
      "name": "Computer"
    },
    {
      "id": 4,
      "name": "Server"
    },
    {
      "id": 5,
      "name": "Network Device"
    }
  ]
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 12. Export Evidence Details PDF

**Endpoint:** `GET /api/v1/evidence/export-evidence-details-pdf`

**Description:** Export comprehensive evidence details as PDF document. Includes evidence information, notes, chain of custody, investigation hypothesis, tools used, analysis results, and gallery.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Unique evidence identifier |

**Response (200 OK):**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="evidence_details_{evidence_id}_{timestamp}.pdf"`

The response is a PDF file that can be downloaded directly.

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

**Example Request:**
```
GET /api/v1/evidence/export-evidence-details-pdf/1
Authorization: Bearer {access_token}
```

**Note:** This endpoint generates a comprehensive PDF report including all evidence details, chain of custody stages (Acquisition, Preparation, Extraction, Analysis), investigation hypothesis, tools used, and analysis results.

---

### 13. Save Evidence Notes

**Endpoint:** `POST /api/v1/evidence/save-notes`

**Description:** Save or update notes for a specific evidence item.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "evidence_id": 1,
  "notes": {
    "id": "33242352",
    "thumbnail": "/data/thumbnails/evidence_1_map.png",
    "text": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian."
  }
}
```

**Response (200 OK):**
```json
{
  "status": 200,
    "message": "Evidence notes saved successfully",
  "data": {
    "evidence_id": 1,
    "evidence_number": "EVID-001",
    "evidence_title": "Handphone A",
    "notes": {
      "id": "33242352",
      "thumbnail": "/data/thumbnails/evidence_1_map.png",
      "text": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian."
    },
    "updated_at": "2025-12-20T14:30:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Notes cannot be empty",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to save evidence notes: {error_message}",
  "data": null
}
```

---

### 14. Edit Evidence Notes

**Endpoint:** `PUT /api/v1/evidence/edit-notes`

**Description:** Update notes for a specific evidence item.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "evidence_id": 1,
  "notes": {
    "id": "33242352",
    "thumbnail": "/data/thumbnails/evidence_1_map_updated.png",
    "text": "Updated: GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian. Analisis lebih lanjut menunjukkan pergerakan mencurigakan."
  }
}
```

**Response (200 OK):**
```json
{
  "status": 200,
    "message": "Evidence notes updated successfully",
  "data": {
    "evidence_id": 1,
    "evidence_number": "EVID-001",
    "evidence_title": "Handphone A",
    "notes": {
      "id": "33242352",
      "thumbnail": "/data/thumbnails/evidence_1_map_updated.png",
      "text": "Updated: GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian. Analisis lebih lanjut menunjukkan pergerakan mencurigakan."
    },
    "updated_at": "2025-12-20T15:45:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Notes cannot be empty and must be a JSON object",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to edit evidence notes: {error_message}",
  "data": null
}
```

**Note:**
- Endpoint `save-notes` dan `edit-notes` memiliki fungsi yang sama (save atau update notes)
- Gunakan `save-notes` untuk membuat notes baru atau mengupdate notes yang sudah ada
- Gunakan `edit-notes` untuk mengupdate notes yang sudah ada (lebih eksplisit untuk operasi update)
- **Evidence notes berbentuk JSON object** dengan struktur: `{"id": "...", "thumbnail": "...", "text": "..."}`

**Example Request:**
```
POST http://localhost:8000/api/v1/evidence/save-notes
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "evidence_id": 1,
  "notes": {
    "id": "33242352",
    "thumbnail": "/data/thumbnails/evidence_1_map.png",
    "text": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian."
  }
}
```

**Example Request (Edit Notes):**
```
PUT http://localhost:8000/api/v1/evidence/edit-notes
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "evidence_id": 1,
  "notes": {
    "id": "33242352",
    "thumbnail": "/data/thumbnails/evidence_1_map_updated.png",
    "text": "Updated: GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian. Analisis lebih lanjut menunjukkan pergerakan mencurigakan."
  }
}
```

---

## 👤 Suspect Management (Person Management)

### Base Path
`/api/v1/suspects` (for Suspect Management endpoints)  
`/api/v1/persons` (for Person Management endpoints)

---

### 1. Get All Suspects

**Endpoint:** `GET /api/v1/suspects/`

**Description:** Get paginated list of suspects with search and filter support. **Results are sorted by newest first (descending order by ID).**

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip (pagination) |
| `limit` | integer | No | 10 | Number of records per page (max: 100) |
| `search` | string | No | - | Search keyword (searches in name, case name, investigator) |
| `status` | string | No | - | Filter by status: `"Witness"`, `"Reported"`, `"Suspected"`, `"Suspect"`, `"Defendant"` |

**Sorting:**
- Results are sorted by **ID descending** (newest first, oldest last)
- First item in the array is the most recently created suspect
- Last item in the array is the oldest suspect

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspects retrieved successfully",
  "data": [
    {
      "id": 5,
      "name": "Kyle Reese",
      "case_name": "Ransomware",
      "investigator": "Solehun",
      "agency": "Trikora",
      "status": "Suspect",
      "date_of_birth": "1990-05-15",
      "place_of_birth": "Jakarta",
      "nationality": "Indonesian",
      "phone_number": "+628123456789",
      "email": "kyle@example.com",
      "address": "Jakarta, Indonesia",
      "height": 175,
      "weight": 70,
      "eye_color": "Brown",
      "hair_color": "Black",
      "distinguishing_marks": "Tattoo on left arm",
      "has_criminal_record": false,
      "risk_level": "high",
      "is_confidential": false,
      "created_at": "2025-12-15T10:30:00Z",
      "updated_at": "2025-12-15T10:30:00Z"
    },
    {
      "id": 4,
      "name": "Sarah Connor",
      "case_name": "Malware Outbreak",
      "investigator": "Solehun",
      "agency": "Trikora",
      "status": "Defendant",
      "date_of_birth": "1985-08-20",
      "place_of_birth": "Bandung",
      "nationality": "Indonesian",
      "phone_number": "+628123456788",
      "email": "sarah@example.com",
      "address": "Bandung, Indonesia",
      "height": 165,
      "weight": 55,
      "eye_color": "Brown",
      "hair_color": "Brown",
      "distinguishing_marks": null,
      "has_criminal_record": true,
      "risk_level": "medium",
      "is_confidential": false,
      "created_at": "2025-12-14T09:20:00Z",
      "updated_at": "2025-12-14T09:20:00Z"
    },
    {
      "id": 3,
      "name": "Mike Ross",
      "case_name": "Phishing Attack",
      "investigator": "Solehun",
      "agency": "Trikora",
      "status": "Suspected",
      "date_of_birth": "1992-03-10",
      "place_of_birth": "Surabaya",
      "nationality": "Indonesian",
      "phone_number": "+628123456787",
      "email": "mike@example.com",
      "address": "Surabaya, Indonesia",
      "height": 180,
      "weight": 75,
      "eye_color": "Black",
      "hair_color": "Black",
      "distinguishing_marks": null,
      "has_criminal_record": false,
      "risk_level": "low",
      "is_confidential": false,
      "created_at": "2025-12-13T14:15:00Z",
      "updated_at": "2025-12-13T14:15:00Z"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "case_name": "Insider Threat",
      "investigator": "Solehun",
      "agency": "Trikora",
      "status": "Reported",
      "date_of_birth": "1988-11-25",
      "place_of_birth": "Yogyakarta",
      "nationality": "Indonesian",
      "phone_number": "+628123456786",
      "email": "jane@example.com",
      "address": "Yogyakarta, Indonesia",
      "height": 160,
      "weight": 50,
      "eye_color": "Brown",
      "hair_color": "Black",
      "distinguishing_marks": null,
      "has_criminal_record": false,
      "risk_level": "medium",
      "is_confidential": false,
      "created_at": "2025-12-12T11:00:00Z",
      "updated_at": "2025-12-12T11:00:00Z"
    },
    {
      "id": 1,
      "name": "John Doe",
      "case_name": "Data Breach",
      "investigator": "Solehun",
      "agency": "Trikora",
      "status": "Witness",
      "date_of_birth": "1995-01-01",
      "place_of_birth": "Medan",
      "nationality": "Indonesian",
      "phone_number": "+628123456785",
      "email": "john@example.com",
      "address": "Medan, Indonesia",
      "height": 170,
      "weight": 65,
      "eye_color": "Brown",
      "hair_color": "Black",
      "distinguishing_marks": null,
      "has_criminal_record": false,
      "risk_level": "low",
      "is_confidential": false,
      "created_at": "2025-12-11T08:00:00Z",
      "updated_at": "2025-12-11T08:00:00Z"
    }
  ],
  "total": 21,
  "page": 1,
  "size": 10
}
```

**Note:** 
- Data diurutkan dari **terbaru ke terlama** berdasarkan ID (ID terbesar = terbaru, ID terkecil = terlama)
- Suspect dengan `id: 5` adalah yang terbaru (muncul pertama)
- Suspect dengan `id: 1` adalah yang terlama (muncul terakhir)
- Status values: `"Witness"` (blue tag), `"Reported"` (yellow tag), `"Suspected"` (orange tag), `"Suspect"` (red tag), `"Defendant"` (dark red tag)

**Example Requests:**
```
GET /api/v1/suspects/?skip=0&limit=10
GET /api/v1/suspects/?search=John
GET /api/v1/suspects/?status=Suspect&limit=20
GET /api/v1/suspects/?skip=10&limit=5&search=Data%20Breach
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 2. Create Suspect

**Endpoint:** `POST /api/v1/suspects/create-suspect`

**Description:** Create a new suspect record. Supports file upload for evidence files.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data` (when evidence file is included) or `application/json`

**Request Body (multipart/form-data or JSON):**

**Form Fields Mapping:**
| UI Field | API Field | Type | Required | Description |
|----------|-----------|------|----------|-------------|
| Case Name (dropdown) | `case_id` | integer | Yes | Case ID selected from dropdown |
| Person of Interest (radio) | `is_unknown` | boolean | No | `true` for "Unknown Person", `false` for "Person Name" (default: `false`) |
| Person Name | `name` | string | Yes | Full name of the suspect |
| Status (dropdown) | `status` | string | Yes | Suspect status: `"Witness"`, `"Reported"`, `"Suspected"`, `"Suspect"`, `"Defendant"` |
| Evidence ID (radio: Generating) | `evidence_id_generating` | boolean | No | `true` if Evidence ID is auto-generated |
| Evidence ID (radio: Manual Input) | `evidence_id_manual` | boolean | No | `true` if Evidence ID is manually input |
| Evidence ID (text input) | `evidence_id` | string | No | Manual Evidence ID (required if `evidence_id_manual` is `true`) |
| Evidence Source (dropdown) | `evidence_source` | string | Yes | Evidence source (e.g., "Handphone", "CCTV") |
| Evidence (file upload) | `evidence_file` | file | No | Evidence file to upload |

**Example Request (multipart/form-data):**
```
case_id: 1
is_unknown: false
name: "John Doe"
status: "Suspect"
evidence_id_generating: true
evidence_source: "Handphone"
evidence_file: [file]
```

**Example Request (JSON - without file upload):**
```json
{
  "case_id": 1,
  "is_unknown": false,
  "name": "John Doe",
  "case_name": "Data Breach",
  "investigator": "Solehun",
  "status": "Suspect",
  "evidence_id": "32342223",
  "evidence_source": "Handphone",
  "date_of_birth": "1995-01-01",
  "place_of_birth": "Medan",
  "nationality": "Indonesian",
  "phone_number": "+628123456785",
  "email": "john@example.com",
  "address": "Medan, Indonesia",
  "height": 170,
  "weight": 65,
  "eye_color": "Brown",
  "hair_color": "Black",
  "has_criminal_record": false,
  "risk_level": "low"
}
```

**Note:** 
- If `evidence_file` is provided, use `multipart/form-data` content type
- If `evidence_id_generating` is `true`, the system will auto-generate the Evidence ID
- If `evidence_id_manual` is `true`, the `evidence_id` field must be provided
- `case_id` is required and should be selected from the cases dropdown (use `GET /api/v1/cases/get-all-cases` to get available cases)
- `evidence_source` should be selected from evidence sources dropdown (use `GET /api/v1/evidence/sources` to get available sources)
- `status` should be selected from statuses dropdown (use `GET /api/v1/suspects/statuses` to get available statuses)

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Suspect created successfully",
  "data": {
    "id": 6,
    "name": "John Doe",
    "case_name": "Data Breach",
    "investigator": "Solehun",
    "status": "Suspect",
    "created_at": "2025-12-16T10:00:00Z",
    "updated_at": "2025-12-16T10:00:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 3. Get Suspect by ID

**Endpoint:** `GET /api/v1/suspects/get-suspect-by-id`

**Description:** Get details of a specific suspect.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Unique suspect identifier |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect retrieved successfully",
  "data": {
    "id": 1,
    "name": "John Doe",
    "case_name": "Data Breach",
    "investigator": "Solehun",
    "status": "Witness",
    "date_of_birth": "1995-01-01",
    "place_of_birth": "Medan",
    "nationality": "Indonesian",
    "phone_number": "+628123456785",
    "email": "john@example.com",
    "address": "Medan, Indonesia",
    "height": 170,
    "weight": 65,
    "eye_color": "Brown",
    "hair_color": "Black",
    "distinguishing_marks": null,
    "has_criminal_record": false,
    "risk_level": "low",
    "is_confidential": false,
    "created_at": "2025-12-11T08:00:00Z",
    "updated_at": "2025-12-11T08:00:00Z"
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 4. Update Suspect

**Endpoint:** `PUT /api/v1/suspects/update-suspect`

**Description:** Update suspect information. Uses the same form as Create Suspect. All fields are optional (partial update). Supports file upload for evidence files.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data` (when evidence file is included) or `application/json`

**Request Body (multipart/form-data or JSON - all fields optional, but `suspect_id` is required):**

**Form Fields Mapping (same as Create Suspect):**
| UI Field | API Field | Type | Required | Description |
|----------|-----------|------|----------|-------------|
| Case Name (dropdown) | `case_id` | integer | No | Case ID selected from dropdown |
| Person of Interest (radio) | `is_unknown` | boolean | No | `true` for "Unknown Person", `false` for "Person Name" |
| Person Name | `name` | string | No | Full name of the suspect |
| Status (dropdown) | `status` | string | No | Suspect status: `"Witness"`, `"Reported"`, `"Suspected"`, `"Suspect"`, `"Defendant"` |
| Evidence ID (radio: Generating) | `evidence_id_generating` | boolean | No | `true` if Evidence ID is auto-generated |
| Evidence ID (radio: Manual Input) | `evidence_id_manual` | boolean | No | `true` if Evidence ID is manually input |
| Evidence ID (text input) | `evidence_id` | string | No | Manual Evidence ID (required if `evidence_id_manual` is `true`) |
| Evidence Source (dropdown) | `evidence_source` | string | No | Evidence source (e.g., "Handphone", "CCTV") |
| Evidence (file upload) | `evidence_file` | file | No | Evidence file to upload |
| Investigator | `investigator` | string | No | Investigator name |
| Date of Birth | `date_of_birth` | date | No | Date of birth (YYYY-MM-DD) |
| Place of Birth | `place_of_birth` | string | No | Place of birth |
| Nationality | `nationality` | string | No | Nationality |
| Phone Number | `phone_number` | string | No | Phone number |
| Email | `email` | string | No | Email address |
| Address | `address` | string | No | Address |
| Height | `height` | integer | No | Height in cm |
| Weight | `weight` | integer | No | Weight in kg |
| Eye Color | `eye_color` | string | No | Eye color |
| Hair Color | `hair_color` | string | No | Hair color |
| Distinguishing Marks | `distinguishing_marks` | string | No | Distinguishing marks |
| Has Criminal Record | `has_criminal_record` | boolean | No | Has criminal record |
| Criminal Record Details | `criminal_record_details` | string | No | Criminal record details |
| Risk Level | `risk_level` | string | No | Risk level: `"low"`, `"medium"`, `"high"` |
| Risk Assessment Notes | `risk_assessment_notes` | string | No | Risk assessment notes |
| Is Confidential | `is_confidential` | boolean | No | Is confidential |
| Notes | `notes` | string | No | Additional notes |

**Example Request (multipart/form-data):**
```
case_id: 1
is_unknown: false
name: "Updated Name"
status: "Defendant"
evidence_id_generating: true
evidence_source: "Handphone"
evidence_file: [file]
risk_level: "high"
notes: "Updated notes"
```

**Example Request (JSON - without file upload):**
```json
{
  "suspect_id": 1,
  "case_id": 1,
  "is_unknown": false,
  "name": "Updated Name",
  "case_name": "Data Breach",
  "investigator": "Solehun",
  "status": "Defendant",
  "evidence_id": "32342223",
  "evidence_source": "Handphone",
  "date_of_birth": "1995-01-01",
  "place_of_birth": "Medan",
  "nationality": "Indonesian",
  "phone_number": "+628123456785",
  "email": "updated@example.com",
  "address": "Medan, Indonesia",
  "height": 170,
  "weight": 65,
  "eye_color": "Brown",
  "hair_color": "Black",
  "has_criminal_record": false,
  "risk_level": "high",
  "notes": "Updated notes"
}
```

**Note:** 
- If `evidence_file` is provided, use `multipart/form-data` content type
- All fields are optional (partial update)
- If `evidence_id_generating` is `true`, the system will auto-generate the Evidence ID
- If `evidence_id_manual` is `true`, the `evidence_id` field must be provided
- `case_id` should be selected from the cases dropdown (use `GET /api/v1/cases/get-all-cases` to get available cases)
- `evidence_source` should be selected from evidence sources dropdown (use `GET /api/v1/evidence/sources` to get available sources)
- `status` should be selected from statuses dropdown (use `GET /api/v1/suspects/statuses` to get available statuses)

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect updated successfully",
  "data": {
    "id": 1,
    "name": "Updated Name",
    "status": "Defendant",
    "risk_level": "high",
    "updated_at": "2025-12-16T15:00:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 5. Delete Suspect

**Endpoint:** `DELETE /api/v1/suspects/delete-suspect`

**Description:** Delete a suspect record.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Unique suspect identifier |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect deleted successfully"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 6. Get Suspect Statuses

**Endpoint:** `GET /api/v1/suspects/statuses`

**Description:** Get list of available suspect statuses (for dropdown selection in forms).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect statuses retrieved successfully",
  "data": [
    {
      "value": "Witness",
      "label": "Witness",
      "color": "green"
    },
    {
      "value": "Suspected",
      "label": "Suspected",
      "color": "orange"
    },
    {
      "value": "Reported",
      "label": "Reported",
      "color": "yellow"
    },
    {
      "value": "Suspect",
      "label": "Suspect",
      "color": "red"
    },
    {
      "value": "Defendant",
      "label": "Defendant",
      "color": "dark-red"
    }
  ]
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 7. Export Suspect Details PDF

**Endpoint:** `GET /api/v1/suspects/export-suspect-details-pdf`

**Description:** Export comprehensive suspect details as PDF document. Includes suspect information, personal details, case information, risk assessment, and related data.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Unique suspect identifier |

**Response (200 OK):**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="suspect_details_{suspect_id}_{timestamp}.pdf"`

The response is a PDF file that can be downloaded directly.

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

**Example Request:**
```
GET /api/v1/suspects/export-suspect-details-pdf?suspect_id=1
Authorization: Bearer {access_token}
```

**Note:** This endpoint generates a comprehensive PDF report including all suspect information, personal details, case association, risk level assessment, and related evidence.

---

### 7. Get Suspect Statistics

**Endpoint:** `GET /api/v1/suspects/statistics`

**Description:** Get summary statistics for Suspect Management dashboard (Total Person, Total Evidence).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_persons": 21,
    "total_evidence": 21
  }
}
```

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 8. Get Evidence by Suspect ID

**Endpoint:** `GET /api/v1/suspects/evidence`

**Description:** Get all evidence associated with a specific suspect.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Unique suspect identifier |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence retrieved successfully",
  "data": [
    {
      "id": 1,
      "evidence_id": "32342223",
      "evidence_number": "EVID-001",
      "title": "Handphone A",
      "thumbnail": "/data/thumbnails/evidence_1_map.png",
      "notes": "Notes 33242352",
      "description": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
      "status": "Collected",
      "created_at": "2025-12-20T10:00:00Z"
    },
    {
      "id": 2,
      "evidence_id": "32342224",
      "evidence_number": "EVID-002",
      "title": "Phone Screen",
      "thumbnail": "/data/thumbnails/evidence_2_phone.png",
      "notes": "Notes 33242352",
      "description": "Terdapat dialog seputar pembakaran dengan suspect lain.",
      "status": "Collected",
      "created_at": "2025-12-20T11:00:00Z"
    }
  ],
  "total": 12
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 9. Add Evidence to Suspect

**Endpoint:** `POST /api/v1/suspects/evidence`

**Description:** Add new evidence to an existing suspect. Supports file upload for evidence files.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request Body (multipart/form-data - all fields required, including `suspect_id`):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `suspect_id` | integer | Yes | Unique suspect identifier |
| `evidence_id` | string | No | Evidence ID (if manual input) |
| `evidence_source` | string | Yes | Evidence source (e.g., "Handphone", "CCTV") |
| `evidence_file` | file | Yes | Evidence file to upload |
| `notes` | string | No | Evidence notes |
| `description` | string | No | Evidence description |

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Evidence added to suspect successfully",
  "data": {
    "id": 13,
    "evidence_id": "32342225",
    "evidence_number": "EVID-013",
    "title": "New Evidence",
      "notes": "Notes 33242353",
    "description": "New evidence description",
    "suspect_id": 1,
    "created_at": "2025-12-20T12:00:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error: {error_details}",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 10. Update Suspect Notes

**Endpoint:** `PUT /api/v1/suspects/notes`

**Description:** Update notes for a specific suspect.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body (all fields required, including `suspect_id`):**
```json
{
  "suspect_id": 1,
  "notes": "Dokumentasi detail, isolasi jaringan, serta pencatatan chain of custody sangat penting untuk memastikan integritas bukti GPS handphone dan dapat dipertanggungjawabkan di pengadilan."
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect notes updated successfully",
  "data": {
    "id": 1,
    "notes": "Dokumentasi detail, isolasi jaringan, serta pencatatan chain of custody sangat penting untuk memastikan integritas bukti GPS handphone dan dapat dipertanggungjawabkan di pengadilan.",
    "updated_at": "2025-12-20T13:00:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 11. Save Suspect Notes

**Endpoint:** `POST /api/v1/suspects/save-notes`

**Description:** Save or update notes for a specific suspect.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "suspect_id": 1,
  "notes": "Suspect teridentifikasi melalui analisis GPS handphone yang menunjukkan posisi di TKP pada saat kejadian. Terdapat bukti komunikasi dengan tersangka lain terkait pembakaran."
}
```

**Response (200 OK):**
```json
{
  "status": 200,
    "message": "Suspect notes saved successfully",
  "data": {
    "suspect_id": 1,
    "suspect_name": "John Doe",
    "notes": "Suspect teridentifikasi melalui analisis GPS handphone yang menunjukkan posisi di TKP pada saat kejadian. Terdapat bukti komunikasi dengan tersangka lain terkait pembakaran.",
    "updated_at": "2025-12-20T14:30:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Notes cannot be empty",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to save suspect notes: {error_message}",
  "data": null
}
```

---

### 12. Edit Suspect Notes

**Endpoint:** `PUT /api/v1/suspects/edit-notes`

**Description:** Update notes for a specific suspect.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "suspect_id": 1,
  "notes": "Updated: Suspect teridentifikasi melalui analisis GPS handphone yang menunjukkan posisi di TKP pada saat kejadian. Terdapat bukti komunikasi dengan tersangka lain terkait pembakaran. Investigasi lebih lanjut menunjukkan pola pergerakan mencurigakan."
}
```

**Response (200 OK):**
```json
{
  "status": 200,
    "message": "Suspect notes updated successfully",
  "data": {
    "suspect_id": 1,
    "suspect_name": "John Doe",
    "notes": "Updated: Suspect teridentifikasi melalui analisis GPS handphone yang menunjukkan posisi di TKP pada saat kejadian. Terdapat bukti komunikasi dengan tersangka lain terkait pembakaran. Investigasi lebih lanjut menunjukkan pola pergerakan mencurigakan.",
    "updated_at": "2025-12-20T15:45:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Notes cannot be empty",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to edit suspect notes: {error_message}",
  "data": null
}
```

**Note:**
- Endpoint `save-notes` dan `edit-notes` memiliki fungsi yang sama (save atau update notes)
- Gunakan `save-notes` untuk membuat notes baru atau mengupdate notes yang sudah ada
- Gunakan `edit-notes` untuk mengupdate notes yang sudah ada (lebih eksplisit untuk operasi update)
- **Suspect notes berbentuk string** (plain text)

**Example Request:**
```
POST http://localhost:8000/api/v1/suspects/save-notes
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "suspect_id": 1,
  "notes": "Suspect teridentifikasi melalui analisis GPS handphone yang menunjukkan posisi di TKP pada saat kejadian. Terdapat bukti komunikasi dengan tersangka lain terkait pembakaran."
}
```

**Example Request (Edit Notes):**
```
PUT http://localhost:8000/api/v1/suspects/edit-notes
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "suspect_id": 1,
  "notes": "Updated: Suspect teridentifikasi melalui analisis GPS handphone yang menunjukkan posisi di TKP pada saat kejadian. Terdapat bukti komunikasi dengan tersangka lain terkait pembakaran. Investigasi lebih lanjut menunjukkan pola pergerakan mencurigakan."
}
```

---

## 👤 Person Management (Legacy)

### Base Path
`/api/v1/persons`

### 1. Create Person

**Endpoint:** `POST /api/v1/persons/create-person`

**Description:** Add a person of interest (suspect/witness) to a case. Can include initial evidence.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "case_id": 1,
  "name": "Mandeep Singh",
  "is_unknown": false,
  "custody_stage": "In Custody",
  "evidence_id": "342344442",
  "evidence_source": "Handphone",
  "evidence_summary": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
  "investigator": "Solehun",
  "created_by": "admin@gmail.com"
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Person created successfully",
  "data": {
    "id": 1,
    "name": "Mandeep Singh",
    "is_unknown": false,
    "custody_stage": "In Custody",
    "evidence_id": "342344442",
    "evidence_source": "Handphone",
    "evidence_summary": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
    "investigator": "Solehun",
    "case_id": 1,
    "created_by": "admin@gmail.com",
    "created_at": "2025-12-20T10:00:00Z",
    "updated_at": "2025-12-20T10:00:00Z"
  }
}
```

**Note:** This endpoint automatically creates a case log entry when a person is added.

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**404 Not Found (Case not found):**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 2. Get Person by ID

**Endpoint:** `GET /api/v1/persons/get-person`

**Description:** Get details of a specific person of interest.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | integer | Yes | Unique person identifier |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Person retrieved successfully",
  "data": {
    "id": 1,
    "name": "Mandeep Singh",
    "is_unknown": false,
    "custody_stage": "In Custody",
    "evidence_id": "342344442",
    "evidence_source": "Handphone",
    "evidence_summary": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
    "investigator": "Solehun",
    "case_id": 1,
    "created_by": "admin@gmail.com",
    "created_at": "2025-12-20T10:00:00Z",
    "updated_at": "2025-12-20T10:00:00Z"
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Person with ID {person_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 3. Get Persons by Case

**Endpoint:** `GET /api/v1/persons/get-persons-by-case`

**Description:** Get all persons of interest associated with a specific case.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Unique case identifier |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip |
| `limit` | integer | No | 10 | Number of records per page (max: 100) |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Persons retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Mandeep Singh",
      "is_unknown": false,
      "custody_stage": "In Custody",
      "evidence_id": "342344442",
      "evidence_source": "Handphone",
      "evidence_summary": "GPS handphone suspect menyatakan posisi...",
      "investigator": "Solehun",
      "case_id": 1,
      "created_at": "2025-12-20T10:00:00Z",
      "updated_at": "2025-12-20T10:00:00Z"
    },
    {
      "id": 2,
      "name": "Nathalie",
      "is_unknown": false,
      "custody_stage": "Released",
      "evidence_id": "342344444",
      "evidence_source": "CCTV",
      "evidence_summary": "Berdasarkan rekaman CCTV tanggal 10 September 2025...",
      "investigator": "Solehun",
      "case_id": 1,
      "created_at": "2025-12-20T11:00:00Z",
      "updated_at": "2025-12-20T11:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "size": 10
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 4. Update Person

**Endpoint:** `PUT /api/v1/persons/update-person`

**Description:** Update person information. All fields are optional (partial update).

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Request Body (all fields optional, but `person_id` is required):**
```json
{
  "person_id": 1,
  "name": "Updated Name",
  "custody_stage": "Released",
  "evidence_summary": "Updated evidence summary",
  "investigator": "New Investigator"
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Person updated successfully",
  "data": {
    "id": 1,
    "name": "Updated Name",
    "custody_stage": "Released",
    "evidence_summary": "Updated evidence summary",
    "investigator": "New Investigator",
    "updated_at": "2025-12-20T15:00:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "message": "Validation error",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Person with ID {person_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

### 5. Delete Person

**Endpoint:** `DELETE /api/v1/persons/delete-person`

**Description:** Delete a person of interest and all associated data.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | integer | Yes | Unique person identifier |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Person deleted successfully"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Person with ID {person_id} not found",
  "data": null
}
```

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

## 🚨 Error Responses

### Standard Error Format
All error responses follow this structure:

```json
{
  "status": <http_status_code>,
  "message": "<error_message>",
  "data": null
}
```

### Common HTTP Status Codes

| Status Code | Description | Example |
|-------------|-------------|---------|
| `200` | Success | Request completed successfully |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Missing or invalid authentication token |
| `403` | Forbidden | Insufficient permissions (RBAC) |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource already exists (e.g., duplicate case number) |
| `500` | Internal Server Error | Unexpected server error |

### Error Response Examples

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Unauthorized",
  "data": null
}
```

**403 Forbidden (Admin Only):**
```json
{
  "status": 403,
  "message": "Access denied. Admin role required.",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID 999 not found",
  "data": null
}
```

**409 Conflict:**
```json
{
  "status": 409,
  "message": "Case number 'REG/123/2024/DRKUM' already exists",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Unexpected server error, please try again later",
  "data": null
}
```

---

## 🔒 Role-Based Access Control (RBAC)

### Overview
The API implements Role-Based Access Control (RBAC) to restrict data access based on user roles.

### Roles

| Role | Description | Access Level |
|------|-------------|--------------|
| `admin` | Administrator | Full access to all data |
| `user` | Regular user | Limited access (own data only) |

### Role Mapping from Tags

When creating a user, the role is automatically mapped from the tag:

| Tag | Role |
|-----|------|
| `"Admin"` | `admin` |
| `"Investigator"` | `user` |
| `"Ahli Forensic"` | `user` |
| Other tags | `user` (default) |

### Access Rules

#### Case Management

**Get All Cases (`GET /api/v1/cases/get-all-cases`):**
- **Admin:** Sees all cases in the database
- **User:** Only sees cases where `main_investigator` matches their `fullname`

**Example:**
- User with `fullname = "Investigator"` only sees cases with `main_investigator = "Investigator"`
- User with `fullname = "Ahli Forensic"` only sees cases with `main_investigator = "Ahli Forensic"`

#### User Management

**Create User (`POST /api/v1/auth/create-user`):**
- **Admin:** ✅ Can create users
- **User:** ❌ Cannot create users (403 Forbidden)

### Important Notes

1. **Matching Criteria:** User role filtering uses exact match: `Case.main_investigator == User.fullname`
   - Case-sensitive
   - Must match exactly (including spaces and special characters)

2. **Admin Bypass:** Admin users bypass all filters and see all data

3. **Token Validation:** All protected endpoints validate:
   - Token signature
   - Token expiration
   - User active status
   - App identifier (for multi-app scenarios)

---

## 📝 Additional Notes

### Date Formats
- **API Response:** `created_at` in case list uses format `"DD/MM/YYYY"` (e.g., `"12/12/2025"`)
- **API Request/Response (ISO):** Other datetime fields use ISO 8601 format (e.g., `"2025-12-12T10:30:00Z"`)

### Pagination
- Default `limit`: 10
- Maximum `limit`: 100
- `page` is calculated as: `skip // limit + 1`
- `total` represents total records matching the filter (before pagination)

### Search Functionality
- Search is case-insensitive
- Searches across multiple fields (title, investigator, agency, etc.)
- Uses `ILIKE` pattern matching (SQL)

### Case Number Generation
- Auto-generated format: `{INITIALS}-{DDMMYY}-{SEQUENCE}`
  - Example: `"BUR-121225-0001"`
  - INITIALS: First 3 words of title
  - DDMMYY: Date in format DDMMYY
  - SEQUENCE: 4-digit sequence number

---

## 🔗 Related Documentation

- [Multi-App Authentication Guide](./MULTI_APP_AUTHENTICATION.md)
- [Role-Based Access Control Guide](./ROLE_BASED_ACCESS_CONTROL.md)
- [Postman Testing Guide](./POSTMAN_TESTING_GUIDE.md)

---

