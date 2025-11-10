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
            "status": "Analysis",
            "file_path": "data/evidence/evidence_20250116_143022_342344442.jpg",
            "source": "Handphone",
            "chain_of_custody": {
              "acquisition": {
                "date": "16 Mei 2025, 12:00",
                "investigator": "Solehun",
                "location": "Bandara Soekarno Hatta Terminal 1",
                "description": "Pengambilan bukti handphone dari tersangka",
                "tools_used": []
              },
              "preparation": {
                "date": "16 Mei 2025, 13:30",
                "investigator": "Solehun",
                "location": "Lab Forensik",
                "description": "Persiapan bukti untuk ekstraksi",
                "tools_used": ["Magnet Axiom", "Celebrate"]
              },
              "extraction": {
                "date": "16 Mei 2025, 14:00",
                "investigator": "Solehun",
                "location": "Lab Forensik",
                "description": "Ekstraksi data dari handphone",
                "tools_used": ["Cellebrite UFED"]
              },
              "analysis": {
                "date": "16 Mei 2025, 15:00",
                "investigator": "Solehun",
                "location": "Lab Forensik",
                "description": "Analisis data yang diekstrak",
                "tools_used": ["Oxygen Forensics"]
              }
            }
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
        "id": 5,
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
            "changed_by": "By: Wisnu",
            "change_detail": "Change: Adding person Nathalie"
          }
        ],
        "created_at": "16 Mei 2025, 12:00"
      },
      {
        "id": 3,
        "case_id": 1,
        "action": "Edit",
        "edit": [
          {
            "changed_by": "By: Wisnu",
            "change_detail": "Change: Adding evidence 3234222"
          }
        ],
        "created_at": "16 Mei 2025, 09:00"
      },
      {
        "id": 2,
        "case_id": 1,
        "action": "Closed",
        "notes": "Kasus ini ditutup",
        "status": "Closed",
        "created_at": "12 Mei 2025, 14:00"
      },
      {
        "id": 1,
        "case_id": 1,
        "action": "Open",
        "status": "Open",
        "created_at": "9 Mei 2025, 10:00"
      }
    ],
    "case_notes": "Berdasarkan rekaman CCTV tanggal 10 September 2025, tersangka terlihat memasuki gedung pada pukul 14:30 WIB. Investigasi lebih lanjut diperlukan untuk mengidentifikasi aktivitas tersangka di dalam gedung."
  }
}
```

**Catatan tentang Struktur Case Log dalam Response:**
- **Untuk action "Edit"**: Hanya menampilkan `id`, `case_id`, `action`, `edit` array, dan `created_at` (tidak ada field `notes` dan `status`)
- **Untuk action lainnya** (Open, Closed, Re-Open): Menampilkan `id`, `case_id`, `action`, `status`, `created_at`, dan `notes` (jika ada nilai, tidak kosong)
- **Field `notes` dalam `case_log`:**
  - **Hanya ditampilkan** jika nilai notes tidak kosong (tidak `null` dan tidak string kosong `""`)
  - **Tidak ditampilkan** jika nilai notes adalah string kosong `""` atau `null`
  - Contoh: Jika `notes: ""`, field `notes` tidak akan muncul dalam response
- Action "Edit" hanya muncul ketika user menambahkan person of interest atau evidence ke case
- Format untuk `changed_by` dalam `edit` array: "By: {user_name}" (contoh: "By: Wisnu")
- Format untuk `change_detail` dalam `edit` array: "Change: Adding {type} {name/id}" (contoh: "Change: Adding person Nathalie", "Change: Adding evidence 3234222")
- Field `notes` wajib diisi saat update status via change-log endpoint, dan akan muncul dalam response jika tidak kosong
- **Field `chain_of_custody` dalam `analysis` items:**
  - Berisi tracking Chain of Custody untuk setiap evidence dengan 4 tahap: `acquisition`, `preparation`, `extraction`, `analysis`
  - Setiap tahap berisi: `date` (format Indonesia), `investigator`, `location`, `description`, `tools_used` (array)
  - Jika tahap belum ada data, nilai akan menjadi `null`
  - Data diambil dari `CustodyLog` berdasarkan `event_type` dan diurutkan berdasarkan `event_date`

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
- Tab **Authorization**: 
  - Type: `Bearer Token`
  - Token: `{access_token}`
- Tab **Headers** (optional):
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
      "id": 5,
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
          "changed_by": "By: Wisnu",
          "change_detail": "Change: Adding person Nathalie"
        }
      ],
      "created_at": "16 Mei 2025, 12:00"
    },
    {
      "id": 3,
      "case_id": 1,
      "action": "Edit",
      "edit": [
        {
          "changed_by": "By: Wisnu",
          "change_detail": "Change: Adding evidence 3234222"
        }
      ],
      "created_at": "16 Mei 2025, 09:00"
    },
    {
      "id": 2,
      "case_id": 1,
      "action": "Closed",
      "notes": "Kasus ini ditutup",
      "status": "Closed",
      "created_at": "12 Mei 2025, 14:00"
    },
    {
      "id": 1,
      "case_id": 1,
      "action": "Open",
      "status": "Open",
      "created_at": "9 Mei 2025, 10:00"
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
- `edit`: (Optional) **Hanya muncul untuk action "Edit"** - Array of edit details when person or evidence is added. Each containing:
  - `changed_by`: Format "By: {user_name}" - User who made the change (e.g., "By: Wisnu")
  - `change_detail`: Format "Change: Adding {type} {name/id}" - Detail of the change (e.g., "Change: Adding person Nathalie", "Change: Adding evidence 3234222")
- `notes`: (Optional) **Hanya muncul untuk action selain "Edit"** (Open, Closed, Re-Open) - Additional notes. Field ini **tidak muncul** jika kosong/null untuk initial log (action "Open"), tapi wajib diisi dan selalu muncul saat update status via change-log endpoint.
- `status`: (Optional) **Hanya muncul untuk action selain "Edit"** (Open, Closed, Re-Open) - Case status at the time of log creation
- `created_at`: Date and time formatted in Indonesian: "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")

**Note on Response Structure:**
- **Untuk action "Edit"**: Hanya menampilkan `id`, `case_id`, `action`, `edit` array, dan `created_at` (tidak ada `notes` dan `status`)
- **Untuk action selain "Edit"** (Open, Closed, Re-Open): Menampilkan `id`, `case_id`, `action`, `status`, `notes` (jika ada), dan `created_at` (tidak ada `edit` array)
- Action "Edit" hanya muncul ketika user melakukan adding person of interest atau adding evidence pada case detail
- Field `notes` **tidak muncul** jika kosong/null untuk initial log (action "Open"), tapi wajib diisi dan selalu muncul saat update status via change-log endpoint

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

**Example Request (Postman):**

**Method:** `GET`

**URL:**
```
http://localhost:8000/api/v1/case-logs/case/logs/1
```

**Headers:**
- Tab **Authorization**: 
  - Type: `Bearer Token`
  - Token: `{access_token}`
- Tab **Headers** (optional):
  - `Content-Type: application/json`

**Query Parameters (Tab Params):**
- `skip`: `0` (optional, default: 0)
- `limit`: `10` (optional, default: 10)

**Example Request (cURL):**
```bash
curl -X GET "http://localhost:8000/api/v1/case-logs/case/logs/1?skip=0&limit=10" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"
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

**Description:** Get detail of a specific case log entry including notes. This endpoint is specifically designed to retrieve case log details when the "Notes" button is clicked in the case log UI, displaying the notes content in a modal dialog.

**Important:** Endpoint ini **HANYA** untuk action yang memiliki notes (Open, Closed, Re-Open). **TIDAK digunakan** untuk action "Edit" karena action "Edit" tidak memiliki notes field.

**Use Case:**
- Ketika user melihat list case logs dari endpoint `GET /api/v1/case-logs/case/logs/{case_id}`, mereka akan melihat semua log entries untuk case tersebut
- Setiap log entry yang memiliki field `notes` (terlihat di response) akan menampilkan button "Notes"
- **Button "Notes" hanya muncul untuk log entries dengan action: Open, Closed, atau Re-Open (yang memiliki notes)**
- **Button "Notes" TIDAK muncul untuk action "Edit"** (karena tidak memiliki notes field)
- Ketika user klik button "Notes" pada log entry tertentu, frontend akan memanggil endpoint ini dengan `log_id` dari log entry tersebut
- Endpoint ini akan mengembalikan detail notes lengkap untuk ditampilkan di modal pop-up
- Modal akan menampilkan: title "Notes", content notes, dan informasi tambahan (status, created_at)

**Important:** 
- **Endpoint ini HANYA untuk action yang memiliki notes** (Open, Closed, Re-Open)
- **Endpoint ini TIDAK digunakan untuk action "Edit"** karena action "Edit" tidak memiliki notes field
- **Button "Notes" hanya muncul di frontend** jika log entry memiliki field `notes` di response `get case logs`
- Jika field `notes` **tidak ada** di response `get case logs`, maka button "Notes" **TIDAK ditampilkan** di frontend
- "Notes" button **TIDAK** ditampilkan untuk action "Edit" (karena tidak memiliki notes field, dan endpoint ini tidak digunakan untuk action "Edit")
- "Notes" button **TIDAK** ditampilkan untuk initial log "Open" jika notes kosong/null (field notes tidak muncul di response)
- Endpoint ini mengembalikan notes lengkap berdasarkan `log_id` dalam `case_id` yang sama
- **Frontend Logic:** Hanya tampilkan button "Notes" jika `log.hasOwnProperty('notes') && log.notes !== null && log.notes !== undefined && log.action !== "Edit"`

**Headers:** 
- Tab **Authorization**: 
  - Type: `Bearer Token`
  - Token: `{access_token}`
- Tab **Headers** (optional, biasanya otomatis):
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `log_id` | integer | Yes | Unique case log identifier |

**Response (200 OK) - For action with notes (Open, Closed, Re-Open):**
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

**Response (200 OK) - For initial log (Open without notes - notes field not included):**
```json
{
  "status": 200,
  "message": "Case log detail retrieved successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "action": "Open",
    "status": "Open",
    "created_at": "9 Mei 2025, 10:00"
  }
}
```
*Note: Field `notes` tidak muncul karena kosong/null. Frontend tidak akan menampilkan button "Notes" untuk log entry ini.*

**Note:** Endpoint ini **TIDAK digunakan** untuk action "Edit". Action "Edit" tidak memiliki notes field, sehingga button "Notes" tidak akan muncul di frontend untuk log entries dengan action "Edit". Frontend seharusnya tidak memanggil endpoint ini untuk action "Edit" karena button "Notes" tidak ditampilkan.

**Response Fields:**
- `id`: Log entry unique identifier
- `case_id`: Case identifier
- `action`: Action performed (e.g., "Open", "Closed", "Re-open")
- `notes`: Notes for the case log entry. Field ini **tidak muncul** jika kosong/null untuk initial log (action "Open"), tapi wajib diisi dan selalu muncul saat update status via change-log endpoint.
- `status`: Case status at the time of log creation (Open, Closed, Re-Open)
- `created_at`: Date and time formatted in Indonesian: "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")

**Note on Response Structure:**
- **Endpoint ini HANYA untuk action yang memiliki notes** (Open, Closed, Re-Open)
- **Response selalu menampilkan:** `id`, `case_id`, `action`, `status`, `notes` (jika ada), dan `created_at`
- **Field `edit` TIDAK muncul** karena endpoint ini tidak digunakan untuk action "Edit"
- **Action "Edit" tidak menggunakan endpoint ini** karena tidak memiliki notes field, sehingga button "Notes" tidak muncul di frontend untuk action "Edit"
- Button "Notes" hanya muncul untuk action yang memiliki notes (Open, Closed, Re-Open) dan akan memanggil endpoint ini untuk menampilkan notes di modal pop-up ketika diklik

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

**Example Request (Postman):**

**Method:** `GET`

**URL:**
```
http://localhost:8000/api/v1/case-logs/log/5
```
*Note: Ganti `5` dengan `log_id` yang ingin dilihat detail notes-nya (ambil dari field `id` pada log entry di list case logs)*

**Headers:**
- Tab **Authorization**: 
  - Type: `Bearer Token`
  - Token: `{access_token}`
- Tab **Headers** (optional, biasanya otomatis):
  - `Content-Type: application/json`

**Important Notes:**
- `log_id` adalah **path parameter** di URL, bukan query parameter
- **JANGAN** tambahkan Authorization atau Content-Type sebagai query parameter di tab "Params"
- Gunakan tab "Authorization" untuk set Bearer Token
- Contoh URL yang benar: `http://localhost:8000/api/v1/case-logs/log/5`
- Contoh URL yang salah: `http://localhost:8000/api/v1/case-logs/log/5?Authorization=Bearer&Content-Type=application/json`

**Example Request (cURL):**
```bash
curl -X GET "http://localhost:8000/api/v1/case-logs/log/5" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"
```

**Additional Information:**
- **Endpoint ini HANYA untuk action yang memiliki notes** (Open, Closed, Re-Open)
- **Endpoint ini TIDAK digunakan untuk action "Edit"** karena action "Edit" tidak memiliki notes field
- **Response structure:** Returns `id`, `case_id`, `action`, `status`, `notes` (jika ada), dan `created_at`
- The `notes` field **tidak muncul** jika kosong/null untuk initial log (action "Open"), tapi wajib diisi dan selalu muncul saat update status via change-log endpoint
- **Field `edit` TIDAK muncul** dalam response endpoint ini karena endpoint ini tidak digunakan untuk action "Edit"
- Date format: Indonesian format "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")

**Frontend Integration Guide:**

**1. When to Show "Notes" Button:**
- **Show "Notes" button** HANYA jika case log entry memiliki field `notes` di response `get case logs`
  - Contoh: Log dengan action "Closed" yang memiliki `"notes": "kasus sudah di tutup"` → **Tampilkan button**
  - Contoh: Log dengan action "Re-open" yang memiliki `"notes": "Kasus dibuka kembali..."` → **Tampilkan button**
- **Do NOT show "Notes" button** untuk:
  - Case log entries yang **tidak memiliki field `notes`** di response (field tidak muncul sama sekali) → **TIDAK tampilkan button**
  - Case log entries dengan action "Edit" (tidak memiliki notes field) → **TIDAK tampilkan button**
  - Case log entries dengan action "Open" yang tidak memiliki field `notes` di response (notes kosong/null) → **TIDAK tampilkan button**

**Frontend Implementation Logic:**
```javascript
// Check if notes field exists in response from get case logs
const hasNotes = log.hasOwnProperty('notes') && log.notes !== null && log.notes !== undefined;
const isEditAction = log.action === "Edit";

// Only show Notes button if notes field exists AND not Edit action
const showNotesButton = hasNotes && !isEditAction;

// In your render function:
{showNotesButton && (
  <button onClick={() => handleNotesClick(log.id)}>
    Notes
  </button>
)}
```

**2. Error Handling:**
- **404 Not Found**: Show message "Case log not found"
- **401 Unauthorized**: Prompt user to re-login
- **500 Server Error**: Show generic error message
- **Network Error**: Show connection error message

---


### 11. Change Case Log (Update Case Status with Notes)

**Endpoint:** `PUT /api/v1/case-logs/change-log/{case_id}`

**Description:** Update case status and automatically create a new case log entry with required notes/alasan. This endpoint updates the case status in the `cases` table and creates a log entry to track the status change. **Notes/alasan is required** when changing the case status - users must provide a reason for the status change. The notes will be saved in the case log entry and will appear in the case detail's case_log array.

**Headers:** 
- Tab **Authorization**: 
  - Type: `Bearer Token`
  - Token: `{access_token}`
- Tab **Headers**:
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
- `action`: Action performed (same as status value - Open, Closed, or Re-Open)
- `status`: New case status (always included since this is a status change)
- `notes`: Notes/alasan yang wajib diisi ketika mengubah status (always included in change-log response since it's required)
- `created_at`: Date and time formatted in Indonesian: "D Bulan YYYY, HH:MM" (e.g., "16 Mei 2025, 12:00")

**Important Notes:**
- Change-log endpoint does not create "Edit" action logs, so `edit` array is **never included** in the response
- Change-log endpoint always creates a log entry with action matching the new status (Open, Closed, or Re-Open)
- Response always includes `status` and `notes` fields (no `edit` array since this is not an "Edit" action)
- Notes is required and cannot be empty when changing case status
- Field `edit` tidak muncul karena endpoint ini hanya untuk mengubah status, bukan untuk action "Edit"

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

**Example Request (Postman):**

**Method:** `PUT`

**URL:**
```
http://localhost:8000/api/v1/case-logs/change-log/1
```

**Headers:**
- Tab **Authorization**: 
  - Type: `Bearer Token`
  - Token: `{access_token}`
- Tab **Headers**:
  - `Content-Type: application/json`

**Body (Tab Body → raw → JSON):**
```json
{
  "status": "Closed",
  "notes": "kasus sudah di tutup"
}
```

**Example Request (Re-open with Notes):**

**Method:** `PUT`

**URL:**
```
http://localhost:8000/api/v1/case-logs/change-log/1
```

**Body (Tab Body → raw → JSON):**
```json
{
  "status": "Re-open",
  "notes": "Kasus dibuka kembali untuk investigasi lebih lanjut."
}
```

**Example Request (cURL):**
```bash
curl -X PUT "http://localhost:8000/api/v1/case-logs/change-log/1" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Closed",
    "notes": "kasus sudah di tutup"
  }'
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

**Description:** Get paginated list of evidences with search, filter, and sorting support.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip (pagination) |
| `limit` | integer | No | 10 | Number of records per page (max: 100) |
| `search` | string | No | - | Search keyword (searches in evidence_number, title, description) |
| `sort_by` | string | No | - | Field to sort by. Valid values: `'created_at'`, `'id'` |
| `sort_order` | string | No | `'desc'` | Sort order. Valid values: `'asc'` (oldest first), `'desc'` (newest first) |

**Sorting:**
- **Default sorting:** Results are sorted by **ID descending** (newest first, oldest last) if `sort_by` is not provided
- **Sort by `created_at`:** 
  - `sort_order='asc'`: Oldest first (terlama ke terbaru)
  - `sort_order='desc'`: Newest first (terbaru ke terlama)
- **Sort by `id`:** 
  - `sort_order='asc'`: Lowest ID first
  - `sort_order='desc'`: Highest ID first (default)

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence list retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_id": 1,
      "evidence_id": "EVID-1-20251110-0001",
      "title": "Illegal Drone Flight",
      "description": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
      "file_path": "data/evidence/evidence_20251110_154315_EVID-1-20251110-0001.jpg",
      "created_at": "2025-11-10T15:43:15.553339+07:00"
    },
    {
      "id": 2,
      "case_id": 1,
      "evidence_id": "EVID-1-20251110-0002",
      "title": "Handphone A",
      "description": "Smartphone dari tersangka",
      "file_path": "data/evidence/evidence_20251110_160000_EVID-1-20251110-0002.jpg",
      "created_at": "2025-11-10T16:00:00.123456+07:00"
    }
  ],
  "total": 2,
  "page": 1,
  "size": 10
}
```

**Catatan:** 
- **Default sorting:** Data diurutkan dari **terbaru ke terlama** berdasarkan ID (ID terbesar = terbaru, ID terkecil = terlama) jika `sort_by` tidak disediakan
- **Custom sorting:** Gunakan parameter `sort_by` dan `sort_order` untuk mengatur urutan data
  - `sort_by=created_at&sort_order=asc`: Urutkan dari terlama ke terbaru berdasarkan tanggal dibuat
  - `sort_by=created_at&sort_order=desc`: Urutkan dari terbaru ke terlama berdasarkan tanggal dibuat
  - `sort_by=id&sort_order=asc`: Urutkan dari ID terkecil ke terbesar
  - `sort_by=id&sort_order=desc`: Urutkan dari ID terbesar ke terkecil (default)

**Example Requests:**
```
GET /api/v1/evidence/get-evidence-list?skip=0&limit=10
GET /api/v1/evidence/get-evidence-list?search=Data%20Leak
GET /api/v1/evidence/get-evidence-list?skip=10&limit=5&search=Agus
GET /api/v1/evidence/get-evidence-list?sort_by=created_at&sort_order=asc
GET /api/v1/evidence/get-evidence-list?sort_by=created_at&sort_order=desc
GET /api/v1/evidence/get-evidence-list?search=Evidence&sort_by=created_at&sort_order=asc
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

**Description:** Create a new evidence item and associate it with a case. Supports file upload and can be associated with a person of interest.

**Headers:** 
- Tab **Authorization**: 
  - Type: `Bearer Token`
  - Token: `{access_token}`
- Tab **Body**: 
  - Select: `form-data`

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID where evidence will be added |
| `evidence_id` | string | No | Evidence ID (optional - can be generated automatically or manually input). **If provided manually, cannot be empty**. **Nilai ini akan digunakan sebagai `evidence_number` di database untuk linking dengan Person.evidence_id** |
| `title` | string | No | Evidence title/name |
| `type` | string | No | Evidence type name (text input dari form UI). **Jika disediakan, sistem akan mencari atau membuat EvidenceType baru secara otomatis** |
| `source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| `evidence_file` | file | No | Evidence file upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). File akan disimpan ke `data/evidence/` directory dengan SHA256 hash |
| `evidence_summary` | string | No | Evidence summary/description (disimpan ke field `description` di database) |
| `investigator` | string | No | Investigator name (who collected/analyzed the evidence, used as `collected_by`) |
| `person_name` | string | No | Person of interest name (for reference only, not stored in database) |
| `is_unknown_person` | boolean | No | Whether the person is unknown (for reference only, not stored in database) |

**Catatan:** Field `file_path`, `file_size`, `file_hash`, `file_type`, dan `file_extension` akan otomatis dibuat setelah file di-upload dan tidak perlu dikirim dalam request.

**Format Auto-Generate Evidence ID:**
Jika `evidence_id` tidak disediakan, sistem akan otomatis membuat evidence ID dengan format:
- **Format:** `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
- **Contoh:** `EVID-1-20251110-0001`, `EVID-1-20251110-0002`, dst.
- **Sequence:** Nomor urut berdasarkan jumlah Evidence untuk case tersebut (4 digit dengan leading zeros)

**Example Request (form-data) - Manual Evidence ID:**
```
case_id: 1
evidence_id: 32342223
title: Handphone A
type: Dokumen
source: Handphone
evidence_summary: GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.
investigator: Solehun
person_name: Mandeep Singh
is_unknown_person: false
evidence_file: [file]
```

**Example Request (form-data) - Auto-Generate Evidence ID:**
```
case_id: 1
title: Handphone A
type: Dokumen
source: Handphone
evidence_summary: Smartphone dari tersangka
evidence_file: [file]
```

**Catatan:** 
- Field `evidence_file` bersifat opsional dan digunakan untuk upload file. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). Jika file type tidak didukung, akan mengembalikan error 400.
- Jika disediakan, file akan disimpan ke direktori `data/evidence/` dengan format `evidence_{timestamp}_{evidence_id}.{extension}` dan perhitungan hash SHA256.
- Field `evidence_id` bersifat **opsional**:
  - **Jika TIDAK disediakan:** Sistem akan otomatis membuat evidence ID dengan format `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
  - **Jika disediakan secara manual:** Tidak boleh kosong (akan mengembalikan error 400 jika string kosong)
  - **Validasi:** Jika `evidence_id` disediakan tapi kosong, akan mengembalikan error: `"evidence_id cannot be empty when provided manually"`
- Field `evidence_number` akan menggunakan nilai `evidence_id` jika tidak disediakan (untuk mencocokkan dengan Person.evidence_id)
- Field `title` default menjadi `"Evidence {evidence_id}"` jika tidak disediakan
- Field `evidence_summary` akan disimpan ke field `description` di database
- Field `person_name` dan `is_unknown_person` bersifat opsional dan hanya digunakan untuk referensi (tidak disimpan di database)
- Field `investigator` bersifat opsional dan digunakan sebagai field `collected_by` dalam record evidence
- Record evidence disimpan ke database dengan semua informasi yang disediakan
- Endpoint ini selalu membuat record Evidence baru

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Evidence created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_id": "EVID-1-20251110-0001",
    "source": "Handphone",
    "file_path": "data/evidence/evidence_20251110_154315_EVID-1-20251110-0001.jpg",
    "description": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
    "title": "Illegal Drone Flight",
    "investigator": "Solehun",
    "agency": "Trikora",
    "person_name": "Mandeep Singh",
    "created_at": "10/11/2025"
  }
}
```

**Catatan:**
- Field `title` berisi title dari case (bukan title evidence)
- Field `investigator` berisi investigator yang diinput, atau `main_investigator` dari case jika tidak diinput
- Field `agency` berisi nama agency dari `case.agency_id` (jika ada)
- Field `person_name` berisi person_name yang diinput (jika ada)
- Field `created_at` menggunakan format Indonesia (DD/MM/YYYY)

**Catatan:** 
- Endpoint ini secara otomatis membuat entry case log ketika evidence ditambahkan.
- Record evidence disimpan ke database dengan semua informasi yang disediakan.
- Upload file bersifat opsional - jika `evidence_file` disediakan, akan disimpan ke direktori `data/evidence/` dengan perhitungan hash SHA256.
- Field `evidence_id` bersifat opsional:
  - **Auto-generate:** Jika tidak disediakan, sistem akan membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
  - **Input manual:** Jika disediakan, tidak boleh kosong (mengembalikan error 400 jika kosong)
- Field `evidence_number` akan menggunakan nilai `evidence_id` jika tidak disediakan (untuk mencocokkan dengan Person.evidence_id)
- Field `title` default menjadi `"Evidence {evidence_id}"` jika tidak disediakan.

**Error Responses:**

**400 Bad Request (File Type Not Supported):**
```json
{
  "status": 400,
  "detail": "File type tidak didukung. Hanya file PDF dan Image yang diperbolehkan (extensions: pdf, jpg, jpeg, png, gif, bmp, webp)"
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

**Postman Testing Guide:**

1. **Set Request Method:** `POST`
2. **Set URL:** `http://localhost:8000/api/v1/evidence/create-evidence`
3. **Tab Authorization:**
   - Type: `Bearer Token`
   - Token: `{{access_token}}` (or paste your access token)
4. **Tab Body:**
   - Select: `form-data`
   - Add the following key-value pairs:
     - `case_id`: `1` (Text) - Required
     - `evidence_id`: `32342223` (Text) - Optional (if provided, cannot be empty)
     - `title`: `Handphone A` (Text) - Optional
     - `type`: `Dokumen` (Text) - Optional (nama evidence type, akan auto-create jika belum ada)
     - `source`: `Handphone` (Text) - Optional
     - `evidence_file`: Select `File` type and choose file - Optional
     - `evidence_summary`: `GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.` (Text) - Optional
     - `investigator`: `Solehun` (Text) - Optional
     - `person_name`: `Mandeep Singh` (Text) - Optional
     - `is_unknown_person`: `false` (Text) - Optional
5. **Click Send**

**Catatan:** 
- Untuk upload file, ubah tipe `evidence_file` dari "Text" ke "File" di Postman
- Field `evidence_id` bersifat **opsional**:
  - **Jika TIDAK disediakan:** Sistem akan otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
  - **Jika disediakan secara manual:** Tidak boleh kosong (mengembalikan error 400: "evidence_id cannot be empty when provided manually")
- Field `person_name` dan `is_unknown_person` digunakan untuk mengasosiasikan evidence dengan person of interest
- Field `file_path` dan `hash_value` biasanya otomatis dibuat setelah file di-upload

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

**Catatan:**
- Field `chain_of_custody` berisi tracking Chain of Custody dengan 4 tahap: `acquisition`, `preparation`, `extraction`, `analysis`
- Setiap tahap berisi: `date` (format Indonesia), `investigator`, `location`, `status` ("Recorded" jika ada data, `null` jika belum ada)
- Data diambil dari `CustodyLog` berdasarkan `event_type` dan diurutkan berdasarkan `event_date`
- Field `current_stage` berisi informasi tahap saat ini (Preparation, Extraction, Analysis) beserta investigation hypothesis, tools used, extraction results, analysis results, dan notes
- Field `gallery` berisi array gambar evidence dengan thumbnail dan description
- Field `notes` berisi object dengan `id`, `thumbnail`, dan `text` untuk menampilkan peta atau visualisasi

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

**Endpoint:** `POST /api/v1/evidence/{evidence_id}/custody-report`

**Description:** Generate custody report untuk evidence item. Report akan menyimpan chain of custody lengkap dari evidence tersebut ke dalam database.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Unique evidence identifier (di URL path) |

**Request Body:**
```json
{
  "report_type": "standard",
  "report_title": "Evidence Custody Report - EVID-001",
  "report_description": "Complete chain of custody documentation",
  "compliance_standard": "ISO 27037",
  "generated_by": "admin@gmail.com"
}
```

**Request Body Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_type` | string | No | Tipe report (default: "standard"). Opsi: "standard", "iso_27037", "nist" |
| `report_title` | string | Yes | Judul report |
| `report_description` | string | No | Deskripsi report |
| `compliance_standard` | string | No | Standar compliance (contoh: "ISO 27037", "NIST", "custom") |
| `generated_by` | string | Yes | User yang membuat report (jika tidak disediakan, akan menggunakan current_user) |

**Catatan:**
- Field `evidence_id` diambil dari path parameter, tidak perlu dikirim di request body
- Field `generated_by` bersifat opsional - jika tidak disediakan, akan menggunakan `current_user.fullname` atau `current_user.email`
- Report akan otomatis menyimpan chain of custody data dari evidence ke field `report_data`
- Report disimpan ke database dengan status `is_verified: false` dan `is_active: true`

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Custody report generated successfully",
  "data": {
    "id": 1,
    "evidence_id": 1,
    "report_type": "standard",
    "report_title": "Evidence Custody Report - EVID-001",
    "report_description": "Complete chain of custody documentation",
    "generated_by": "admin@gmail.com",
    "generated_date": "2025-01-15T14:30:22Z",
    "report_file_path": null,
    "is_verified": false,
    "created_at": "2025-01-15T14:30:22Z"
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

### 9. Get Custody Reports

**Endpoint:** `GET /api/v1/evidence/{evidence_id}/custody-reports`

**Description:** Get list of custody reports untuk evidence item dengan pagination dan filter.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Unique evidence identifier (di URL path) |

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Number of records to skip |
| `limit` | integer | No | 10 | Number of records per page (max: 50) |
| `report_type` | string | No | - | Filter by report type (opsional) |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Custody reports retrieved successfully",
  "data": [
    {
      "id": 1,
      "evidence_id": 1,
      "report_type": "standard",
      "report_title": "Evidence Custody Report - EVID-001",
      "report_description": "Complete chain of custody documentation",
      "generated_by": "admin@gmail.com",
      "generated_date": "2025-01-15T14:30:22Z",
      "report_file_path": null,
      "is_verified": false,
      "created_at": "2025-01-15T14:30:22Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
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

### 10. Get Custody Report by ID

**Endpoint:** `GET /api/v1/evidence/{evidence_id}/custody-report/{report_id}`

**Description:** Get detail custody report berdasarkan ID.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | Unique evidence identifier (di URL path) |
| `report_id` | integer | Yes | Unique custody report identifier (di URL path) |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Custody report retrieved successfully",
  "data": {
    "id": 1,
    "evidence_id": 1,
    "report_type": "standard",
    "report_title": "Evidence Custody Report - EVID-001",
    "report_description": "Complete chain of custody documentation",
    "generated_by": "admin@gmail.com",
    "generated_date": "2025-01-15T14:30:22Z",
    "report_file_path": null,
    "report_file_hash": null,
    "report_data": {
      "custody_chain": [...],
      "chain_integrity": true
    },
    "compliance_standard": "ISO 27037",
    "is_verified": false,
    "verified_by": null,
    "verification_date": null,
    "created_at": "2025-01-15T14:30:22Z",
    "is_active": true
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

**404 Not Found (Report):**
```json
{
  "status": 404,
  "message": "Custody report with ID {report_id} not found for evidence {evidence_id}",
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

### 11. Get Evidence Types

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
- `Content-Type: multipart/form-data` (untuk upload file) atau `application/x-www-form-urlencoded`

**Request Body (form-data):**

**Form Fields Mapping (sesuai dengan UI Form "Add Suspect"):**

**Field Utama (Visible di Form):**
| UI Field | API Field | Type | Required | Description |
|----------|-----------|------|----------|-------------|
| Case Name (dropdown) | `case_id` | integer | Yes | Case ID yang dipilih dari dropdown |
| Person of Interest (radio) | `is_unknown` | boolean | No | `true` untuk "Unknown Person", `false` untuk "Person Name" (default: `false`) |
| Person Name (text input) | `name` | string | Yes | Nama lengkap suspect (wajib jika `is_unknown = false`) |
| Status (dropdown) | `status` | string | No | Status suspect: `"Witness"`, `"Reported"`, `"Suspected"`, `"Suspect"`, `"Defendant"` (default: `"Suspect"` jika tidak disediakan) |
| Evidence ID (radio: Generating) | - | - | No | Jika dipilih, `evidence_id` TIDAK perlu disediakan (akan auto-generate) |
| Evidence ID (radio: Manual Input) | - | - | No | Jika dipilih, `evidence_id` HARUS disediakan dan tidak boleh kosong |
| Evidence ID (text input) | `evidence_id` | string | No | Evidence ID manual (wajib jika Manual Input dipilih, tidak boleh kosong) |
| Evidence Source (dropdown) | `evidence_source` | string | No | Sumber evidence: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| Evidence (Upload button) | `evidence_file` | file | No | File evidence untuk di-upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`) |

**Field Tambahan (Opsional, untuk detail lengkap suspect):**
| UI Field | API Field | Type | Required | Description |
|----------|-----------|------|----------|-------------|
| Evidence Summary | `evidence_summary` | string | No | Ringkasan/deskripsi evidence |
| Investigator | `investigator` | string | No | Nama investigator (jika tidak disediakan, akan menggunakan current user) |
| Case Name | `case_name` | string | No | Nama case (jika tidak disediakan, akan menggunakan case.title) |
| Date of Birth | `date_of_birth` | string | No | Tanggal lahir (format: YYYY-MM-DD) |
| Place of Birth | `place_of_birth` | string | No | Tempat lahir |
| Nationality | `nationality` | string | No | Kewarganegaraan |
| Phone Number | `phone_number` | string | No | Nomor telepon |
| Email | `email` | string | No | Alamat email |
| Address | `address` | string | No | Alamat lengkap |
| Height | `height` | integer | No | Tinggi badan (cm) |
| Weight | `weight` | integer | No | Berat badan (kg) |
| Eye Color | `eye_color` | string | No | Warna mata |
| Hair Color | `hair_color` | string | No | Warna rambut |
| Distinguishing Marks | `distinguishing_marks` | string | No | Tanda khusus/ciri fisik |
| Has Criminal Record | `has_criminal_record` | boolean | No | Memiliki catatan kriminal (default: `false`) |
| Criminal Record Details | `criminal_record_details` | string | No | Detail catatan kriminal |
| Risk Level | `risk_level` | string | No | Level risiko: "low", "medium", "high" (default: `"medium"`) |
| Risk Assessment Notes | `risk_assessment_notes` | string | No | Catatan penilaian risiko |
| Is Confidential | `is_confidential` | boolean | No | Apakah bersifat rahasia (default: `false`) |
| Notes | `notes` | string | No | Catatan tambahan |

**Format Auto-Generate Evidence ID:**
Jika radio "Generating" dipilih atau `evidence_id` tidak disediakan dan `evidence_file` ada:
- **Format:** `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
- **Contoh:** `EVID-1-20251110-0001`, `EVID-1-20251110-0002`, dst.

**Perilaku Evidence ID:**
- **Jika "Generating" dipilih atau `evidence_id` TIDAK disediakan:**
  - **Jika `evidence_file` ada:** Otomatis membuat `evidence_id` dan membuat record Evidence
  - **Jika `evidence_file` TIDAK ada:** `evidence_id = null` (opsional, tidak membuat record Evidence)
- **Jika "Manual Input" dipilih dan `evidence_id` disediakan:**
  - Tidak boleh kosong (mengembalikan error 400: "evidence_id cannot be empty when provided manually")
  - Sistem memeriksa apakah record Evidence sudah ada dengan `evidence_number = evidence_id`
  - **Jika Evidence sudah ada:** Menghubungkan person ke record Evidence yang sudah ada (memperbarui file jika `evidence_file` disediakan)
  - **Jika Evidence TIDAK ada:** Membuat record Evidence baru dengan `evidence_number = evidence_id` (dengan file jika disediakan, atau tanpa file)

**Contoh Request (form-data) - Auto-Generate Evidence ID (sesuai dengan form UI):**
```
case_id: 1
is_unknown: false
name: "John Doe"
status: "Suspect"
evidence_source: "Handphone"
evidence_file: [file]
```

**Catatan:** 
- Radio "Generating" dipilih → `evidence_id` TIDAK perlu dikirim
- Sistem akan otomatis membuat `evidence_id` dengan format `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
- File evidence di-upload melalui field `evidence_file`

**Contoh Request (form-data) - Manual Evidence ID (sesuai dengan form UI):**
```
case_id: 1
is_unknown: false
name: "John Doe"
status: "Suspect"
evidence_id: "32342223"
evidence_source: "Handphone"
evidence_file: [file]
```

**Catatan:**
- Radio "Manual Input" dipilih → `evidence_id` HARUS dikirim dan tidak boleh kosong
- Field `evidence_id` muncul di form ketika "Manual Input" dipilih
- File evidence di-upload melalui field `evidence_file`

**Contoh Request (form-data) - Manual Evidence ID dengan Field Tambahan:**
```
case_id: 1
is_unknown: false
name: "John Doe"
status: "Suspect"
evidence_id: "32342223"
evidence_source: "Handphone"
evidence_file: [file]
evidence_summary: "Smartphone dari tersangka"
investigator: "Solehun"
date_of_birth: "1995-01-01"
place_of_birth: "Medan"
nationality: "Indonesian"
phone_number: "+628123456785"
email: "john@example.com"
address: "Medan, Indonesia"
height: 170
weight: 65
eye_color: "Brown"
hair_color: "Black"
risk_level: "high"
```

**Contoh Request (form-data) - Link to Existing Evidence (tanpa upload file baru):**
```
case_id: 1
is_unknown: false
name: "John Doe"
status: "Witness"
evidence_id: "32342223"
evidence_source: "Handphone"
```

**Catatan:**
- Radio "Manual Input" dipilih dan `evidence_id` mengacu ke Evidence yang sudah ada
- Tidak ada `evidence_file` → hanya menghubungkan suspect ke Evidence yang sudah ada
- Jika `evidence_file` disediakan, file akan memperbarui Evidence yang sudah ada

**Catatan (sesuai dengan form UI "Add Suspect"):** 
- Endpoint ini menggunakan `multipart/form-data` untuk mendukung upload file
- **Field yang terlihat di form UI:**
  - `case_id` (wajib): Dipilih dari dropdown "Case Name"
  - `is_unknown` (opsional): Radio button "Person of Interest" - `false` untuk "Person Name", `true` untuk "Unknown Person"
  - `name` (wajib jika `is_unknown = false`): Input text "Person Name"
  - `status` (opsional): Dropdown "Status" - pilihan: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (default: "Suspect")
  - `evidence_id` (opsional): 
    - Jika radio "Generating" dipilih → TIDAK perlu dikirim (akan auto-generate)
    - Jika radio "Manual Input" dipilih → HARUS dikirim dan tidak boleh kosong
  - `evidence_source` (opsional): Dropdown "Evidence Source" - pilihan: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR"
  - `evidence_file` (opsional): File upload melalui button "Upload" di section "Evidence"
- **Perilaku Evidence ID:**
  - **Radio "Generating" dipilih (atau `evidence_id` TIDAK disediakan):**
    - **Jika `evidence_file` ada:** Otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence baru
    - **Jika `evidence_file` TIDAK ada:** `evidence_id = null` (opsional, tidak membuat record Evidence)
  - **Radio "Manual Input" dipilih dan `evidence_id` disediakan:**
    - Tidak boleh kosong (mengembalikan error 400: "evidence_id cannot be empty when provided manually")
    - Sistem memeriksa apakah record Evidence sudah ada dengan `evidence_number = evidence_id`
    - **Jika Evidence sudah ada:** Menghubungkan suspect ke Evidence yang sudah ada (memperbarui file jika `evidence_file` disediakan)
    - **Jika Evidence TIDAK ada:** Membuat record Evidence baru dengan `evidence_number = evidence_id` (dengan file jika disediakan, atau tanpa file)
- **Field tambahan (opsional, untuk detail lengkap):**
  - `evidence_summary`, `investigator`, `case_name`, `date_of_birth`, `place_of_birth`, `nationality`, `phone_number`, `email`, `address`, `height`, `weight`, `eye_color`, `hair_color`, `distinguishing_marks`, `has_criminal_record`, `criminal_record_details`, `risk_level`, `risk_assessment_notes`, `is_confidential`, `notes`
- **Default values:**
  - `is_unknown`: `false` (Person Name)
  - `status`: `"Suspect"` jika tidak disediakan
  - `risk_level`: `"medium"` jika tidak disediakan
  - `has_criminal_record`: `false` jika tidak disediakan
  - `is_confidential`: `false` jika tidak disediakan
- **Auto-fill:**
  - `investigator`: Jika tidak disediakan, akan menggunakan current user (fullname atau email)
  - `case_name`: Jika tidak disediakan, akan menggunakan `case.title` dari case yang dipilih
- **Format:**
  - `date_of_birth`: Format `YYYY-MM-DD` (contoh: "1995-01-01")
- **Case Log:**
  - Endpoint ini secara otomatis membuat case log entry ketika suspect ditambahkan
  - Jika `evidence_id` disediakan dan Evidence record dibuat/dihubungkan, case log entry untuk evidence juga akan dibuat
- **File Upload:**
  - File disimpan ke direktori `data/evidence/` dengan format `evidence_{timestamp}_{evidence_id}.{extension}`
  - Perhitungan hash SHA256 otomatis dilakukan

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
    "criminal_record_details": null,
    "risk_level": "high",
    "risk_assessment_notes": null,
    "is_confidential": false,
    "notes": null,
    "created_at": "2025-12-16T10:00:00Z",
    "updated_at": "2025-12-16T10:00:00Z",
    "last_seen": null
  }
}
```

**Error Responses:**

**400 Bad Request (Empty evidence_id when provided manually):**
```json
{
  "status": 400,
  "message": "evidence_id cannot be empty when provided manually",
  "data": null
}
```

**400 Bad Request (Other validation errors):**
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

### 3. Get Suspect by ID

**Endpoint:** `GET /api/v1/suspects/get-suspect-by-id/{suspect_id}`

**Description:** Get comprehensive details of a specific suspect including personal information, case association, risk assessment, dan evidence-related fields.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | Unique suspect identifier (di URL path) |

**Contoh Request:**
```
GET http://localhost:8000/api/v1/suspects/get-suspect-by-id/1
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect retrieved successfully",
  "data": {
    "id": 1,
    "name": "John Doe",
    "case_name": "Data Breach",
    "case_id": 1,
    "investigator": "Solehun",
    "status": "Witness",
    "is_unknown": false,
    "custody_stage": null,
    "evidence_id": "32342223",
    "evidence_source": "Handphone",
    "evidence_summary": "GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
    "created_by": "admin@gmail.com",
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
    "criminal_record_details": null,
    "risk_level": "low",
    "risk_assessment_notes": null,
    "is_confidential": false,
    "notes": null,
    "created_at": "2025-12-11T08:00:00Z",
    "updated_at": "2025-12-11T08:00:00Z",
    "last_seen": null
  }
}
```

**Catatan:**
- Field `status` tidak memiliki default value - harus dipilih dari UI (Witness, Reported, Suspected, Suspect, Defendant)
- Field `evidence_id`, `evidence_source`, `evidence_summary` berasal dari Person model yang sudah digabung ke Suspect
- Field `is_unknown` menunjukkan apakah suspect adalah "Unknown Person" atau memiliki nama
- Field `custody_stage` menunjukkan tahap penahanan suspect
- Field `created_by` menunjukkan user yang membuat record suspect

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
| Evidence ID (radio: Generating) | - | - | No | If selected, `evidence_id` should NOT be provided (will auto-generate) |
| Evidence ID (radio: Manual Input) | - | - | No | If selected, `evidence_id` MUST be provided and cannot be empty |
| Evidence ID (text input) | `evidence_id` | string | No | Manual Evidence ID (required if Manual Input selected, cannot be empty) |
| Evidence Source (dropdown) | `evidence_source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| Evidence (file upload) | `evidence_file` | file | No | Evidence file to upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`) |
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

**Catatan:** 
- Jika `evidence_file` disediakan, gunakan content type `multipart/form-data`
- Semua field bersifat opsional (partial update)
- Field `evidence_id` bersifat **opsional**:
  - **Jika TIDAK disediakan + file ada:** Otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence
  - **Jika TIDAK disediakan + tidak ada file:** `evidence_id = null` (opsional, tidak membuat record Evidence)
  - **Jika disediakan secara manual:** Tidak boleh kosong (mengembalikan error 400: "evidence_id cannot be empty when provided manually")
  - **Linking:** Jika record Evidence sudah ada dengan `evidence_number` yang sama, person akan dihubungkan ke Evidence yang sudah ada
- `case_id` harus dipilih dari dropdown cases (gunakan `GET /api/v1/cases/get-all-cases` untuk mendapatkan cases yang tersedia)
- `evidence_source` harus dipilih dari sumber evidence: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR"
- `suspect_status` harus dipilih dari: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (tidak ada default, bisa null)

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
| `evidence_file` | file | Yes | Evidence file to upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`) |
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
- Tab **Authorization**: 
  - Type: `Bearer Token`
  - Token: `{access_token}`
- Tab **Body**: 
  - Select: `form-data`

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID where person will be added |
| `name` | string | Yes | Person name (required if `is_unknown` is false) |
| `is_unknown` | boolean | No | Whether person is unknown (default: false). Use "Person Name" = false, "Unknown Person" = true |
| `suspect_status` | string | No | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be selected from UI, no default) |
| `custody_stage` | string | No | Custody stage (e.g., "In Custody", "Released", etc.) |
| `evidence_id` | string | No | Evidence ID (optional - can be generated automatically or manually input). **If provided manually, cannot be empty** |
| `evidence_source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| `evidence_file` | file | No | Evidence file upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). File akan disimpan ke `data/evidence/` directory dengan SHA256 hash |
| `evidence_summary` | string | No | Evidence summary/description |
| `investigator` | string | No | Investigator name |
| `created_by` | string | No | User email who created the person (auto-filled from current user if not provided) |

**Format Auto-Generate Evidence ID:**
Jika `evidence_id` tidak disediakan dan `evidence_file` ada, sistem akan otomatis membuat evidence ID dengan format:
- **Format:** `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
- **Contoh:** `EVID-1-20251110-0001`, `EVID-1-20251110-0002`, dst.
- **Sequence:** Nomor urut berdasarkan jumlah Evidence untuk case tersebut (4 digit dengan leading zeros)

**Perilaku Evidence ID:**
- **Jika `evidence_id` disediakan (input manual):**
  - Tidak boleh kosong (mengembalikan error 400: "evidence_id cannot be empty when provided manually")
  - Sistem memeriksa apakah record Evidence sudah ada dengan `evidence_number = evidence_id`
  - **Jika Evidence sudah ada:** Menghubungkan person ke record Evidence yang sudah ada (memperbarui file jika `evidence_file` disediakan)
  - **Jika Evidence TIDAK ada:** Membuat record Evidence baru dengan `evidence_number = evidence_id` (dengan file jika disediakan, atau tanpa file)
- **Jika `evidence_id` TIDAK disediakan:**
  - **Jika `evidence_file` ada:** Otomatis membuat `evidence_id` dan membuat record Evidence baru
  - **Jika `evidence_file` TIDAK ada:** `evidence_id = null` (opsional, tidak membuat record Evidence)

**Example Request (form-data) - Manual Evidence ID:**
```
case_id: 1
name: Mandeep Singh
is_unknown: false
suspect_status: Suspect
custody_stage: In Custody
evidence_id: 342344442
evidence_source: Handphone
evidence_summary: GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.
investigator: Solehun
evidence_file: [file]
created_by: admin@gmail.com
```

**Example Request (form-data) - Auto-Generate Evidence ID:**
```
case_id: 1
name: Mandeep Singh
is_unknown: false
suspect_status: Witness
evidence_source: Handphone
evidence_summary: Test evidence summary
evidence_file: [file]
```

**Example Request (form-data) - Link to Existing Evidence:**
```
case_id: 1
name: Nathalie
is_unknown: false
suspect_status: Witness
evidence_id: 342344442
evidence_source: Handphone
evidence_summary: Link to existing evidence
```

**Catatan:** 
- Field `evidence_file` bersifat opsional dan digunakan untuk upload file jika file evidence disediakan. Jika disediakan, file akan disimpan ke direktori `data/evidence/` dengan perhitungan hash SHA256.
- Field `suspect_status` bersifat opsional dan disimpan di database. Jika tidak disediakan, akan menjadi `null` (tidak ada nilai default).
- Field `created_by` bersifat opsional dan otomatis diisi dari user yang sedang terautentikasi (email atau fullname) jika tidak disediakan.
- Upload file: File disimpan dengan format `evidence_{timestamp}_{evidence_id}.{extension}` di direktori `data/evidence/`.
- Field `evidence_id` bersifat **opsional**:
  - **Jika TIDAK disediakan + file ada:** Otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence
  - **Jika TIDAK disediakan + tidak ada file:** `evidence_id = null` (opsional, tidak membuat record Evidence)
  - **Jika disediakan secara manual:** Tidak boleh kosong (mengembalikan error 400 jika kosong)
  - **Linking:** Jika record Evidence sudah ada dengan `evidence_number` yang sama, person akan dihubungkan ke Evidence yang sudah ada

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

**Catatan:** Endpoint ini secara otomatis membuat entry case log ketika person ditambahkan.

**Error Responses:**

**400 Bad Request (Empty evidence_id when provided manually):**
```json
{
  "status": 400,
  "message": "evidence_id cannot be empty when provided manually",
  "data": null
}
```

**400 Bad Request (Other validation errors):**
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

**Postman Testing Guide:**

1. **Set Request Method:** `POST`
2. **Set URL:** `http://localhost:8000/api/v1/persons/create-person`
3. **Tab Authorization:**
   - Type: `Bearer Token`
   - Token: `{{access_token}}` (or paste your access token)
4. **Tab Body:**
   - Select: `form-data`
   - Add the following key-value pairs:
     - `case_id`: `1` (Text) - Required
     - `name`: `Mandeep Singh` (Text) - Required
     - `is_unknown`: `false` (Text) - Optional
     - `suspect_status`: `Suspect` (Text) - Optional
     - `custody_stage`: `In Custody` (Text) - Optional
     - `evidence_id`: `342344442` (Text) - Optional (if provided, cannot be empty)
     - `evidence_source`: `Handphone` (Text) - Optional
     - `evidence_file`: Select `File` type and choose file - Optional (if provided, file will be saved to `data/evidence/` directory)
     - `evidence_summary`: `GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.` (Text) - Optional
     - `investigator`: `Solehun` (Text) - Optional
     - `created_by`: `admin@gmail.com` (Text) - Optional (auto-filled from current user if not provided)
5. **Click Send**

**Catatan:** 
- Untuk upload file, ubah tipe `evidence_file` dari "Text" ke "File" di Postman
- Field `created_by` bersifat opsional dan otomatis diisi dari user yang sedang terautentikasi (email atau fullname) jika tidak disediakan
- Semua field kecuali `case_id` dan `name` bersifat opsional
- Upload file: File disimpan dengan format `evidence_{timestamp}_{evidence_id}.{extension}` di direktori `data/evidence/` dengan perhitungan hash SHA256
- Field `suspect_status` bersifat opsional dan disimpan di database. Jika tidak disediakan, akan menjadi `null` (tidak ada nilai default)
- Field `evidence_id` bersifat **opsional**:
  - **Jika TIDAK disediakan + file ada:** Otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence
  - **Jika TIDAK disediakan + tidak ada file:** `evidence_id = null` (opsional, tidak membuat record Evidence)
  - **Jika disediakan secara manual:** Tidak boleh kosong (mengembalikan error 400: "evidence_id cannot be empty when provided manually")
  - **Linking:** Jika record Evidence sudah ada dengan `evidence_number` yang sama, person akan dihubungkan ke Evidence yang sudah ada (memperbarui file jika disediakan)

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

