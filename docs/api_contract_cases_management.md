# API Contract Documentation
## Digital Forensics Analysis Platform - Backend API

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**API Version:** `/api/v1`

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Case Management](#case-management)
3. [Case Log Management](#case-log-management)
4. [Reports Management](#reports-management)
5. [Evidence Management](#evidence-management)
6. [Suspect Management (Person Management)](#suspect-management-person-management)
7. [Error Responses](#error-responses)
8. [Role-Based Access Control](#role-based-access-control)

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

### Get Current User Profile
**Endpoint:** `GET /api/v1/auth/me`

**Description:** Get current authenticated user profile information. Returns user details including id, email, fullname, tag, role, and password.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "User profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "admin@gmail.com",
    "fullname": "Admin Forensic",
    "tag": "Admin",
    "role": "admin",
    "password": "admin.admin"
  }
}
```

**Response Data Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | User ID |
| `email` | string | User email address |
| `fullname` | string | User full name |
| `tag` | string | User tag/category (e.g., "Admin", "Investigator", "Ahli Forensic") |
| `role` | string | User role (e.g., "admin", "user") |
| `password` | string | User password in plain text |

**Security Note:** The `password` field contains the user's password in plain text. Returning plain text passwords in API responses is highly discouraged for security reasons. It is recommended not to use this feature in production environments.

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**401 Unauthorized (Expired Token):**
```json
{
  "status": 401,
  "message": "Expired token",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve user profile",
  "data": null
}
```

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

## 👥 User Management

### Overview

**Access Control:**

**User Management Endpoints:**
- **Admin Role Only**: Only users with `role: "admin"` can access user management endpoints (create, update, delete, and list all users).
- **Regular Users**: Users with `role: "user"` can only view their own profile using `/api/v1/auth/me`.
- **403 Forbidden**: Non-admin users attempting to access user management endpoints will receive a 403 Forbidden error.

**Dashboard Access Control:**
- **Admin Role**: Can view dashboard statistics for **all cases** in the system (via `/api/v1/cases/statistics/summary`).
- **Regular User Role**: Can only view dashboard statistics for **cases where they are the main investigator** (cases where `main_investigator` matches user's fullname or email).

**Available Endpoints:**
- `GET /api/v1/auth/me` - Get current user profile (All authenticated users) - See [Get Current User Profile](#get-current-user-profile) in Authentication section for details
- `GET /api/v1/auth/get-all-users` - List all users (Admin only)
- `POST /api/v1/auth/create-user` - Create new user (Admin only)
- `PUT /api/v1/auth/update-user/{user_id}` - Update user (Admin only)
- `DELETE /api/v1/auth/delete-user/{user_id}` - Delete user (Admin only)

---

**401 Unauthorized (Inactive User):**
```json
{
  "status": 401,
  "message": "Inactive or missing user",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve user profile",
  "data": null
}
```

**500 Internal Server Error (Missing User Data):**
```json
{
  "status": 500,
  "message": "Failed to retrieve user profile - missing user data",
  "data": null
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### Create User (Admin Only)
**Endpoint:** `POST /api/v1/auth/create-user`

**Description:** Create a new user. **Only users with admin role can access this endpoint.** Non-admin users will receive a 403 Forbidden error.

**Headers:** 
- `Authorization: Bearer <admin_access_token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "fullname": "New User",
  "email": "newuser@example.com",
  "password": "password123",
  "confirm_password": "password123",
  "tag": "Investigator"
}
```

**Request Body Fields:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `email` | string | Yes | User email address | Must be valid email format |
| `password` | string | Yes | User password | Minimum 8 characters, maximum 128 characters |
| `confirm_password` | string | Yes | Password confirmation | Must match `password` field exactly |
| `fullname` | string | Yes | User full name | - |
| `tag` | string | Yes | User tag/category | Options: `"Admin"`, `"Investigator"`, `"Ahli Forensic"`, or other tags |

**Note:** 
- `confirm_password` must match `password` exactly. If they don't match, API will return a validation error.
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
    "fullname": "New User",
    "email": "newuser@example.com",
    "role": "user",
    "tag": "Investigator",
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

**400 Bad Request (Password Mismatch):**
```json
{
  "status": 400,
  "message": "Password and confirm password do not match",
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

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to create user",
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
    "confirm_password": "securepass123",
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
     "confirm_password": "securepass123",
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
| **Confirm Password** | `confirm_password` | Yes | Must match `password` exactly |
| **Tag** (dropdown) | `tag` | Yes | Select from: `"Admin"`, `"Investigator"`, `"Ahli Forensic"` |

**Frontend Validation (Before API Call):**
- ✅ `password` and `confirm_password` must match
- ✅ `email` must be valid email format
- ✅ `password` must be at least 8 characters
- ✅ All required fields must be filled

**Backend Validation:**
- ✅ Email format validation
- ✅ Password length: 8-128 characters
- ✅ Password and confirm_password must match
- ✅ Email uniqueness check
- ✅ Admin role check (only admin can create users)

---

### Get All Users (Admin Only)

**Endpoint:** `GET /api/v1/auth/get-all-users`

**Description:** Get paginated list of all users. **Only users with admin role can access this endpoint.** Non-admin users will receive a 403 Forbidden error. **Results are sorted by newest first (descending order by ID or created_at).**

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
      "id": 2,
      "fullname": "Investigator",
      "email": "investigator@gmail.com",
      "role": "user",
      "tag": "Investigator",
      "is_active": true,
      "created_at": "2025-11-13T17:24:58.612660"
    },
    {
      "id": 1,
      "fullname": "Admin Forensic",
      "email": "admin@gmail.com",
      "role": "admin",
      "tag": "Admin",
      "is_active": true,
      "created_at": "2025-11-12T02:33:42.246135"
    }
  ],
  "total": 2,
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

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to retrieve users",
  "data": null
}
```

---

### Update User (Admin Only)

**Endpoint:** `PUT /api/v1/auth/update-user/{user_id}`

**Description:** Update user information. **Only users with admin role can access this endpoint.** Non-admin users will receive a 403 Forbidden error. **All fields are required.**

**Headers:** 
- `Authorization: Bearer <admin_access_token>`
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to update |

**Request Body:**
```json
{
  "fullname": "Updated User Name",
  "email": "updated@example.com",
  "password": "newpassword123",
  "confirm_password": "newpassword123",
  "tag": "Investigator"
}
```

**Request Body Fields:**
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `fullname` | string | Yes | User full name | - |
| `email` | string | Yes | User email address | Must be valid email format |
| `password` | string | Yes | User password | Minimum 8 characters, maximum 128 characters |
| `confirm_password` | string | Yes | Password confirmation | Must match `password` field exactly |
| `tag` | string | Yes | User tag/category | Options: `"Admin"`, `"Investigator"`, `"Ahli Forensic"`, or other tags |

**Note:** 
- **All fields are required** - you must provide all fields when updating a user.
- `is_active` field is **NOT** included in the request body. User's active status cannot be changed via this endpoint.
- `confirm_password` must match `password` exactly. If they don't match, API will return a validation error.
- The `role` is automatically mapped from the `tag` field (see mapping below).
- Password will be hashed automatically.

**Tag to Role Mapping:**
- `"Admin"` → `role: "admin"`
- `"Investigator"` → `role: "user"`
- `"Ahli Forensic"` → `role: "user"`
- Other tags → `role: "user"` (default)

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "User updated successfully",
  "data": {
    "id": 4,
    "fullname": "Updated User Name",
    "email": "updated@example.com",
    "role": "user",
    "tag": "Investigator",
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

**400 Bad Request (Password Mismatch):**
```json
{
  "status": 400,
  "message": "Password and confirm password do not match",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "User with ID {user_id} not found",
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

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to update user",
  "data": null
}
```

**Example Request (cURL):**
```bash
curl -X PUT "http://localhost:8000/api/v1/auth/update-user/4" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "fullname": "Updated User Name",
    "email": "updated@example.com",
    "password": "newpassword123",
    "confirm_password": "newpassword123",
    "tag": "Investigator"
  }'
```

---

### Delete User (Admin Only)

**Endpoint:** `DELETE /api/v1/auth/delete-user/{user_id}`

**Description:** Delete a user. **Only users with admin role can access this endpoint.** Non-admin users will receive a 403 Forbidden error. This will also delete all associated refresh tokens (cascade delete).

**Headers:** `Authorization: Bearer <admin_access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | integer | Yes | User ID to delete |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "User deleted successfully",
  "data": null
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "User with ID {user_id} not found",
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

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to delete user",
  "data": null
}
```

**Example Request (cURL):**
```bash
curl -X DELETE "http://localhost:8000/api/v1/auth/delete-user/4" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Note:**
- Deleting a user will automatically delete all associated refresh tokens (cascade delete).
- This action cannot be undone.

---

## 📁 Case Management

### Base Path
`/api/v1/cases`

### 1. Get Case Summary (Dashboard Statistics)

**Endpoint:** `GET /api/v1/cases/statistics/summary`

**Description:** Get summary statistics of cases by status (Open, Closed, Reopen, Investigating). **Full Access**: All roles can see statistics for all cases. No filtering or access restrictions.

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
- **Admin:** Sees all cases in the database
- **User:** Only sees cases where `main_investigator` matches their `fullname` or `email` (case-insensitive matching)

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

**Description:** Get comprehensive details of a specific case including persons of interest and case logs. **Full Access**: All roles can access details of all cases. No filtering or access restrictions.

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
- Konsisten dengan endpoint lain: `/update-case/{case_id}`, dll.

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
        "suspect_id": 1,
        "name": "Unknown",
        "person_type": null,
        "evidence": [
          {
            "id": 1,
            "evidence_number": "98459845459",
            "evidence_summary": "Evidence dari unknown person 1",
            "file_path": "data/evidence/evidence_20251112_094100_98459845459.png",
            "source": "Handphone"
          }
        ]
      },
      {
        "suspect_id": 2,
        "name": "Unknown",
        "person_type": null,
        "evidence": [
      {
        "id": 2,
            "evidence_number": "4380458334",
            "evidence_summary": "Evidence dari unknown person 2",
            "file_path": "data/evidence/evidence_20251112_094223_4380458334.jpeg",
            "source": "Handphone"
          }
        ]
      }
    ],
    "person_count": 2,
    "case_notes": null
  }
}
```

**Catatan tentang Response:**
- **Urutan `persons_of_interest`:**
  - Data diurutkan dari **terlama ke terbaru** berdasarkan `suspect_id` (suspect_id terkecil = terlama, suspect_id terbesar = terbaru)
  - Person dengan `suspect_id: 1` adalah yang terlama (muncul pertama)
  - Person dengan `suspect_id: 2` adalah yang terbaru (muncul terakhir)
  - Field `suspect_id` menunjukkan ID dari table `suspects` yang terkait dengan person tersebut
- **Urutan `evidence` dalam setiap person:**
  - Data diurutkan dari **terlama ke terbaru** berdasarkan ID evidence (ID terkecil = terlama, ID terbesar = terbaru)
  - Evidence dengan `id: 5` muncul sebelum evidence dengan `id: 7` (karena 5 < 7)
- **Field `person_type` dalam `persons_of_interest`:**
  - Menunjukkan status suspect: `"Witness"`, `"Reported"`, `"Suspected"`, `"Suspect"`, `"Defendant"`, atau `null`
  - **`person_type` akan `null` jika:**
    - Suspect dibuat dari form "Add Evidence" dengan `person_name` yang belum ada (auto-created suspect dengan `status = null`)
    - Suspect dibuat tanpa memilih status dari UI
    - Evidence ter-link ke suspect "Unknown" (setiap suspect "Unknown" muncul sebagai person terpisah dengan `id` yang valid)
  - **`person_type` akan memiliki nilai jika:**
    - Suspect dibuat dengan status yang dipilih dari UI (via `create-person` atau `create-suspect` dengan `suspect_status`)
    - Suspect di-update dengan status (via `update-person` dengan `suspect_status`)
- **Field `person_count` dalam response:**
  - Menunjukkan total jumlah person dalam `persons_of_interest`
  - Nilai ini dihitung dari panjang array `persons_of_interest`
  - Membantu frontend untuk menampilkan jumlah person tanpa perlu menghitung array secara manual
  - Contoh: Jika ada 4 person dalam `persons_of_interest`, maka `person_count: 4`

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

**Description:** Update an existing case. **Full Access**: All roles can update all cases. No filtering or access restrictions. All fields in request body are optional (partial update). Only fields provided in the request body will be updated.

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

**Endpoint:** `GET /api/v1/cases/export-case-details-pdf/{case_id}`

**Description:** Export detail kasus secara lengkap sebagai dokumen PDF. PDF mencakup informasi kasus, person of interest beserta evidence mereka, dan catatan kasus. Dokumen memiliki format profesional dengan header dan footer di setiap halaman, pagination yang benar, dan layout yang terorganisir. **Full Access**: All roles can export PDF for all cases. No filtering or access restrictions.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | Unique case identifier |

**Response (200 OK):**
- **Content-Type:** `application/pdf`
- **Content-Disposition:** `attachment; filename="case_detail_{case_number}_{timestamp}.pdf"`

Response berupa file PDF yang dapat diunduh langsung.

**Struktur Dokumen PDF:**

1. **Header (muncul di setiap halaman):**
   - **Halaman 1:** 
     - Kiri: Logo CYBER SENTINEL (atau teks jika logo tidak tersedia)
     - Kanan: Waktu export dalam format "Exported: DD/MM/YYYY HH:MM WIB"
   - **Halaman 2+ (Header Kustom):**
     - Kiri: Logo CYBER SENTINEL
     - Kanan: Waktu export
     - Informasi Case: Judul kasus, Case ID, Status (dalam box), Investigator, Date Created
     - Header ini tidak muncul di halaman terakhir kecuali ada Notes atau Person of Interest

2. **Footer (muncul di setiap halaman):**
   - Kiri: Judul kasus dan ID kasus (format: "{Judul Kasus} - {ID Kasus}")
   - Kanan: Nomor halaman (format: "Page X of Y" dengan total halaman yang akurat)

3. **Bagian Konten:**
   - **Judul Kasus:** Judul besar dengan format tebal di bagian atas
   - **Informasi Kasus:** ID Kasus, Investigator, Tanggal Dibuat
   - **Deskripsi Kasus:** Teks deskripsi kasus lengkap
   - **Bagian Person of Interest:** Untuk setiap person:
     - Header person: Nama, Status, Jumlah Total Evidence
     - Tabel evidence dengan kolom:
       - **Picture:** Gambar thumbnail (80x80px) atau placeholder "No image"
       - **Evidence Number:** Nomor evidence (string)
       - **Summary:** Ringkasan/deskripsi evidence
   - **Bagian Notes:** Catatan kasus (jika tersedia)

**Fitur PDF:**
- Formatting profesional dengan styling yang konsisten
- Pagination otomatis dengan penomoran halaman yang akurat (format "Page X of Y")
- Header kustom untuk halaman 2+ dengan informasi case lengkap (judul, case ID, status, investigator, date created)
- Header tabel diulang di setiap halaman ketika tabel evidence memanjang ke beberapa halaman
- Gambar otomatis di-resize agar sesuai (thumbnail 80x80px)
- Bagian person dijaga agar tetap bersama untuk mencegah pemisahan halaman yang tidak rapi
- Smart page break handling: menggunakan CondPageBreak untuk mencegah page break yang tidak perlu ketika subtitle (Person of Interest, Notes) sudah muncul di halaman sebelumnya
- Alignment kolom tabel evidence: semua kolom (Picture, Evidence ID, Summary) rata kiri
- Penanganan data yang hilang dengan baik (menampilkan placeholder ketika data tidak tersedia)
- Template PDF langsung mengambil data dari case detail comprehensive (termasuk semua persons of interest dengan evidence mereka)

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
  "message": "Failed to export case detail PDF: {error_message}",
  "data": null
}
```

**Example Request:**
```
GET /api/v1/cases/export-case-details-pdf/1
Authorization: Bearer {access_token}
```

**Example Response:**
The response is a binary PDF file. When saved, it will be named like:
- `case_detail_34124325_20251231_090000.pdf`

**Notes:**
- The PDF is generated using the same data structure as `get-case-detail-comprehensive` endpoint
- Large cases with many persons of interest and evidence will automatically span multiple pages
- Images from evidence files are included as thumbnails if available
- The document maintains professional appearance suitable for official reports

---

### 7. Save Case Notes

**Endpoint:** `POST /api/v1/cases/save-notes`

**Description:** Save or update notes for a specific case. **Full Access**: All roles can save notes for all cases. No filtering or access restrictions.

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

**Description:** Edit existing notes for a specific case. **Full Access**: All roles can edit notes for all cases. No filtering or access restrictions.

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

**Description:** Retrieve all log entries for a specific case with pagination support. **Full Access**: All roles can access logs for all cases. No filtering or access restrictions.

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

**Description:** Get detail of a specific case log entry including notes. This endpoint is specifically designed to retrieve case log details when the "Notes" button is clicked in the case log UI, displaying the notes content in a modal dialog. **Full Access**: All roles can access log details for all cases. No filtering or access restrictions.

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

**403 Forbidden (Access Denied):**
```json
{
  "status": 403,
  "detail": "You do not have permission to access this log"
}
```

**404 Not Found (Case log not found):**
```json
{
  "status": 404,
  "detail": "Case log not found"
}
```

**404 Not Found (Case not found):**
```json
{
  "status": 404,
  "detail": "Case with ID {case_id} not found"
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

**Description:** Update case status and automatically create a new case log entry with required notes/alasan. This endpoint updates the case status in the `cases` table and creates a log entry to track the status change. **Notes/alasan is required** when changing the case status - users must provide a reason for the status change. The notes will be saved in the case log entry and will appear in the case detail's case_log array. **Full Access**: All roles can update case status and create logs for all cases. No filtering or access restrictions.

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

**403 Forbidden (Access Denied):**
```json
{
  "status": 403,
  "detail": "You do not have permission to update log for this case"
}
```

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
  "message": "Notes/reason is required when changing case status",
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

**Description:** Get paginated list of evidences with search, filter, and sorting support. **Full Access**: All roles can see all evidence in the database. No filtering or access restrictions.

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
      "evidence_number": "EVID-1-20251110-0001",
      "title": "Buronan Maroko Interpol",
      "investigator": "Solehun",
      "agency": "Trikora",
      "created_at": "10/11/2025"
    },
    {
      "id": 2,
      "case_id": 1,
      "evidence_number": "EVID-1-20251110-0002",
      "title": "Buronan Maroko Interpol",
      "investigator": "Solehun",
      "agency": "Trikora",
      "created_at": "10/11/2025"
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

### 2. Get Evidence Summary

**Endpoint:** `GET /api/v1/evidence/get-evidence-summary`

**Description:** Get evidence management summary statistics. Returns total case count and total evidence count. **Endpoint ini digunakan untuk menampilkan summary di dashboard Evidence Management**. **Full Access**: All roles can see statistics for all cases and evidence. No filtering or access restrictions.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence summary retrieved successfully",
  "data": {
    "total_case": 21,
    "total_evidence": 21
  }
}
```

**Example Request:**
```
GET /api/v1/evidence/get-evidence-summary
Authorization: Bearer <access_token>
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

### 3. Create Evidence

**Endpoint:** `POST /api/v1/evidence/create-evidence`

**Description:** Create a new evidence item and associate it with a case. Supports file upload and can be associated with a person of interest. **Endpoint ini digunakan dari form "Add Evidence" di Case Details**. **Full Access**: All roles can create evidence for all cases. No filtering or access restrictions. 

**Logika Linking Evidence ke Person:**
- Jika `person_name` disediakan dan `is_unknown_person = false`:
  - Sistem akan cek apakah `person_name` sudah ada berdasarkan `case_id`
  - **Jika person_name dan case_id sudah ada:** Evidence baru akan ditambahkan ke person yang sudah ada (tidak membuat person baru). Person_count tidak akan bertambah.
  - **Jika person_name dan case_id belum ada:** Sistem akan otomatis membuat suspect baru dengan nama tersebut (dengan `status = null`, sehingga `person_type` akan `null` di case detail). Case log akan dibuat untuk mencatat penambahan person baru.
- Jika `is_unknown_person = true`: Sistem akan cek apakah sudah ada suspect "Unknown" dengan `case_id` yang sama. Jika ada, evidence akan ter-link ke suspect "Unknown" yang sudah ada (yang paling baru). Jika belum ada, sistem akan membuat suspect "Unknown" baru dan evidence akan ter-link ke suspect tersebut.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data` (untuk upload file) atau `application/x-www-form-urlencoded`

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID where evidence will be added |
| `evidence_number` | string | No | Evidence number (optional - can be generated automatically or manually input). **If provided manually, cannot be empty**. **Nilai ini akan digunakan sebagai `evidence_number` di database untuk linking dengan Person.evidence_id** |
| `type` | string | No | Evidence type name (text input dari form UI). **Jika disediakan, sistem akan mencari atau membuat EvidenceType baru secara otomatis** |
| `source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| `evidence_file` | file | No | Evidence file upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). File akan disimpan ke `data/evidence/` directory dengan SHA256 hash |
| `evidence_summary` | string | No | Evidence summary/description (disimpan ke field `description` di database) |
| `investigator` | string | **Yes** | Investigator name (who collected/analyzed the evidence, used as `investigator`). **WAJIB diisi** |
| `person_name` | string | Conditional | Person of interest name. **WAJIB diisi jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI). Tidak perlu diisi jika `is_unknown_person = true` (radio button "Unknown Person" dipilih)** - field ini tidak akan ditampilkan di UI jika "Unknown Person" dipilih. **Jika `suspect_id` disediakan, `person_name` dapat digunakan untuk update name suspect tersebut**. Jika disediakan dan `is_unknown_person = false` dan `suspect_id` tidak disediakan, sistem akan mencari existing suspect dengan nama tersebut. Jika tidak ditemukan, sistem akan otomatis membuat suspect baru dengan nama tersebut dan link evidence_number ke suspect tersebut |
| `suspect_status` | string | Conditional | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be selected from UI, no default). **WAJIB diisi jika `is_unknown_person = false` (radio button "Person Name" dipilih). Jika `is_unknown_person = true`, field ini tidak akan ditampilkan di UI dan akan di-set ke `null`**. **Jika `suspect_id` disediakan, `suspect_status` dapat digunakan untuk update status suspect tersebut** |
| `is_unknown_person` | boolean | No | Flag yang menandakan apakah person tersebut unknown/tidak diketahui. **Jika `true` (radio button "Unknown Person" dipilih di UI):** `person_name` dan `suspect_status` tidak akan ditampilkan di UI (tidak perlu diisi). Sistem akan cek apakah sudah ada suspect "Unknown" dengan `case_id` yang sama. Jika `suspect_id` disediakan, evidence akan ter-link ke suspect "Unknown" dengan `suspect_id` tersebut. Jika `suspect_id` tidak disediakan, evidence akan ter-link ke suspect "Unknown" yang sudah ada (yang paling baru) atau membuat suspect "Unknown" baru jika belum ada |
| `suspect_id` | integer | No | Suspect ID untuk memilih suspect tertentu. **Jika `suspect_id` disediakan, evidence akan ter-link ke suspect dengan `suspect_id` tersebut (harus merupakan suspect dengan `case_id` yang sama). Jika `person_name` dan/atau `suspect_status` juga disediakan, suspect tersebut akan di-update dengan nilai baru (tidak membuat suspect baru)**. Jika tidak disediakan, akan menggunakan logika berdasarkan `is_unknown_person` atau `person_name` |

**Catatan:** Field `file_path`, `file_size`, `file_hash`, `file_type`, dan `file_extension` akan otomatis dibuat setelah file di-upload dan tidak perlu dikirim dalam request.

**Format Auto-Generate Evidence Number:**
Jika `evidence_number` tidak disediakan, sistem akan otomatis membuat evidence number dengan format:
- **Format:** `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
- **Contoh:** `EVID-1-20251110-0001`, `EVID-1-20251110-0002`, dst.
- **Sequence:** Nomor urut berdasarkan jumlah Evidence untuk case tersebut (4 digit dengan leading zeros)

**Example Request (form-data) - Manual Evidence Number:**
```
case_id: 1
evidence_number: 32342223
title: Handphone A
type: Dokumen
source: Handphone
evidence_summary: GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.
investigator: Solehun
person_name: Mandeep Singh
is_unknown_person: false
evidence_file: [file]
```

**Example Request (form-data) - Auto-Generate Evidence Number:**
```
case_id: 1
type: Dokumen
source: Handphone
evidence_summary: Smartphone dari tersangka
investigator: Solehun
evidence_file: [file]
```

**Example Request (form-data) - Unknown Person dengan suspect_id:**
```
case_id: 1
evidence_number: 32342223
type: Dokumen
source: Handphone
evidence_summary: Evidence untuk unknown person yang sudah ada
investigator: Solehun
is_unknown_person: true
suspect_id: 2
evidence_file: [file]
```
**Catatan:** 
- **Jika `suspect_id` disediakan:** Evidence akan ter-link ke suspect dengan `suspect_id` tersebut. Jika `person_name` dan/atau `suspect_status` juga disediakan, suspect tersebut akan di-update (tidak membuat suspect baru)
- **Jika `suspect_id` tidak disediakan:** Evidence akan ter-link berdasarkan `is_unknown_person` atau `person_name` sesuai logika yang ada

**Workflow Create Evidence:**
1. **Create Evidence baru** (selalu membuat record Evidence baru)
2. **Link ke Suspect (prioritas dari tertinggi ke terendah):**
   - **Jika `suspect_id` disediakan (prioritas tertinggi):**
     - Evidence akan ter-link ke suspect dengan `suspect_id` tersebut (harus merupakan suspect dengan `case_id` yang sama)
     - Jika `person_name` disediakan, suspect tersebut akan di-update: `name = person_name`, `is_unknown = False`
     - Jika `suspect_status` disediakan, suspect tersebut akan di-update: `status = suspect_status`
     - **Tidak membuat suspect baru** - hanya update suspect yang sudah ada
   - **Jika `is_unknown_person = true` dan `suspect_id` tidak disediakan:**
     - Sistem akan cek apakah sudah ada suspect "Unknown" dengan `case_id` yang sama dan `is_unknown = true`
     - **Jika sudah ada:** Evidence akan ter-link ke suspect "Unknown" yang sudah ada (yang paling baru berdasarkan `id` descending)
     - **Jika belum ada:** Sistem akan membuat suspect "Unknown" baru dengan `name = "Unknown"`, `status = null`, dan `is_unknown = true`. Evidence akan ter-link ke suspect tersebut. Case log akan dibuat untuk mencatat penambahan person "Unknown" baru
   - **Jika `person_name` disediakan dan `is_unknown_person = false` dan `suspect_id` tidak disediakan:**
     - **Cek person_name berdasarkan case_id:**
       - Cek apakah sudah ada suspect dengan `case_id` dan `name` yang sama
     - **Jika person_name dan case_id sudah ada:**
       - Evidence akan ter-link ke suspect yang sudah ada
       - Jika `suspect_status` disediakan, suspect tersebut akan di-update: `status = suspect_status`
       - **Person_count tidak akan bertambah** karena semua suspect records dengan `name` dan `case_id` yang sama dikumpulkan menjadi satu person
     - **Jika person_name dan case_id belum ada:**
       - Buat suspect baru dengan `name = person_name`, `status = suspect_status` (jika disediakan) atau `null`
       - Case log akan dibuat untuk mencatat penambahan person baru
   - Di case-detail, setiap suspect akan muncul sebagai person terpisah (menggunakan `suspect_id` sebagai key)

**Catatan:** 
- Field `evidence_file` bersifat opsional dan digunakan untuk upload file. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). Jika file type tidak didukung, akan mengembalikan error 400.
- Jika disediakan, file akan disimpan ke direktori `data/evidence/` dengan format `evidence_{timestamp}_{evidence_number}.{extension}` dan perhitungan hash SHA256.
- Field `evidence_number` bersifat **opsional**:
  - **Jika TIDAK disediakan:** Sistem akan otomatis membuat evidence number dengan format `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
  - **Jika disediakan secara manual:** Tidak boleh kosong (akan mengembalikan error 400 jika string kosong)
  - **Validasi:** Jika `evidence_number` disediakan tapi kosong, akan mengembalikan error: `"evidence_number cannot be empty when provided manually"`
- Field `evidence_number` akan digunakan untuk linking dengan Suspect.evidence_id
- Field `title` diambil dari `case.title` (tidak perlu diinput, otomatis dari case)
- Field `evidence_summary` akan disimpan ke field `description` di database
- Field `investigator` **WAJIB diisi** dan digunakan sebagai field `investigator` dalam record evidence
- Field `person_name` dan `is_unknown_person` digunakan untuk linking evidence ke suspect:
  - **Jika `person_name` disediakan dan `is_unknown_person = false`:** 
    - Sistem akan cek apakah `person_name` sudah ada berdasarkan `case_id`
    - **Jika person_name dan case_id sudah ada:**
      - Jika `evidence_number` sudah ada, tidak perlu membuat suspect baru
      - Jika `evidence_number` berbeda, buat suspect record baru untuk evidence ini
      - `status` akan diambil dari suspect yang sudah ada (jika ada)
      - **Person_count tidak akan bertambah** karena semua suspect records dengan `name` dan `case_id` yang sama dikumpulkan menjadi satu person di case-detail
    - **Jika person_name dan case_id belum ada:**
      - Buat suspect baru dengan `status = null`
      - Case log akan dibuat untuk mencatat penambahan person baru
    - **Satu person dapat memiliki multiple evidence dengan evidence_number berbeda** - semua evidence akan dikumpulkan di case-detail response
  - **Jika `is_unknown_person = true`:** 
    - Field `person_name` dan `suspect_status` tidak akan ditampilkan di UI (tidak perlu diisi)
    - **Jika `suspect_id` disediakan:**
      - Evidence akan ter-link ke suspect dengan `suspect_id` tersebut (harus merupakan suspect "Unknown" dengan `case_id` yang sama)
      - Jika suspect tidak ditemukan atau bukan "Unknown", akan error 404
    - **Jika `suspect_id` tidak disediakan:**
      - Sistem akan cek apakah sudah ada suspect "Unknown" dengan `case_id` yang sama dan `is_unknown = true`
      - **Jika sudah ada:** Evidence akan ter-link ke suspect "Unknown" yang sudah ada (yang paling baru)
      - **Jika belum ada:** Sistem akan membuat suspect "Unknown" baru dan evidence akan ter-link ke suspect tersebut
    - Di case-detail, setiap suspect "Unknown" akan muncul sebagai person terpisah dengan `suspect_id` yang valid (bukan `null`)
- Endpoint ini selalu membuat record Evidence baru
- **Catatan tentang Auto-Create Suspect:** Ketika suspect baru dibuat secara otomatis dari `create-evidence`:
  - **Jika person_name dan case_id sudah ada:**
    - Suspect record baru dibuat untuk `evidence_number` yang berbeda
    - `status`: Diambil dari suspect yang sudah ada
    - `name`: `person_name` yang diinput
    - `case_id`: Case ID yang sama
    - `case_name`: dari `case.title`
    - `evidence_id`: `evidence_number` dari evidence yang baru dibuat
    - `investigator`: dari `case.main_investigator` (fallback ke `current_user`)
    - `is_unknown`: `False`
    - **Case log tidak dibuat** karena person sudah ada sebelumnya
  - **Jika person_name dan case_id belum ada:**
    - Suspect baru dibuat dengan `status = null`
    - `name`: `person_name` yang diinput
    - `case_id`: Case ID
    - `case_name`: dari `case.title`
    - `evidence_id`: `evidence_number` dari evidence yang baru dibuat
    - `investigator`: dari `case.main_investigator` (fallback ke `current_user`)
    - `is_unknown`: `False`
    - **Case log dibuat** untuk mencatat penambahan person baru
  - Di case detail, semua suspect records dengan `name` dan `case_id` yang sama akan dikumpulkan menjadi satu person dengan multiple evidence items
  - **Person_count tidak akan bertambah** jika person sudah ada, karena semua suspect records dengan `name` dan `case_id` yang sama dikumpulkan menjadi satu person

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Evidence created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "EVID-1-20251110-0001",
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
- Field `evidence_number` bersifat opsional:
  - **Auto-generate:** Jika tidak disediakan, sistem akan membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
  - **Input manual:** Jika disediakan, tidak boleh kosong (mengembalikan error 400 jika kosong)
- Field `evidence_number` akan digunakan untuk mencocokkan dengan Person.evidence_id
- Field `title` diambil dari `case.title` (tidak perlu diinput, otomatis dari case).

**Frontend Validation & Error Handling:**

Sebelum mengirim request ke API, frontend akan melakukan validasi required fields. Jika ada required fields yang belum diisi, akan muncul dialog error:

**1. Dialog "Incomplete Form" (Saat Submit):**
- **Trigger:** User mengklik tombol submit/confirm, tetapi ada required fields yang belum diisi
- **Message:** "Please complete required fields before submitting"
- **Actions:**
  - **Continue Editing:** Menutup dialog dan kembali ke form untuk melengkapi required fields

**Required Fields untuk Create Evidence:**
- `case_id` (selalu required)
- `investigator` (selalu required)
- `person_name` (required jika `is_unknown_person = false`)
- `suspect_status` (required jika `is_unknown_person = false`)

**2. Dialog "Unsaved Changes" (Saat Cancel/Close):**
- **Trigger:** User mengklik tombol cancel/close atau menutup form, tetapi ada perubahan yang belum disimpan
- **Message:** "If you leave this form, your data will not be saved"
- **Actions:**
  - **Leave Anyway:** Menutup form tanpa menyimpan perubahan
  - **Continue Editing:** Kembali ke form untuk melanjutkan editing

**Error Responses:**
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
     - `evidence_number`: `32342223` (Text) - Optional (if provided, cannot be empty)
     - `title`: `Handphone A` (Text) - Optional
     - `type`: `Dokumen` (Text) - Optional (nama evidence type, akan auto-create jika belum ada)
     - `source`: `Handphone` (Text) - Optional
     - `evidence_file`: Select `File` type and choose file - Optional
     - `evidence_summary`: `GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.` (Text) - Optional
     - `investigator`: `Solehun` (Text) - **Required**
     - `person_name`: `Mandeep Singh` (Text) - Optional
     - `is_unknown_person`: `false` (Text) - Optional
5. **Click Send**

**Catatan:** 
- Untuk upload file, ubah tipe `evidence_file` dari "Text" ke "File" di Postman
- Field `evidence_number` bersifat **opsional**:
  - **Jika TIDAK disediakan:** Sistem akan otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
  - **Jika disediakan secara manual:** Tidak boleh kosong (mengembalikan error 400: "evidence_number cannot be empty when provided manually")
- Field `person_name` dan `is_unknown_person` digunakan untuk linking evidence ke suspect:
  - **Jika `person_name` disediakan dan `is_unknown_person = false`:** Sistem akan mencari existing suspect dengan nama tersebut. Jika ditemukan, evidence di-link ke suspect. Jika tidak ditemukan, auto-create suspect baru.
  - **Jika `is_unknown_person = true`:** Field `person_name` dan `suspect_status` tidak akan ditampilkan di UI (tidak perlu diisi). Evidence akan ter-link ke suspect "Unknown" (yang sudah ada atau dibuat baru). Jika `suspect_id` disediakan, evidence akan ter-link ke suspect "Unknown" dengan `suspect_id` tersebut
- Field `file_path` dan `hash_value` biasanya otomatis dibuat setelah file di-upload

---



### 4. Update Evidence

**Endpoint:** `PUT /api/v1/evidence/update-evidence/{evidence_id}`

**Description:** Update evidence information. All fields are optional (partial update). Supports file upload for evidence files. **Endpoint ini digunakan dari form "Edit Evidence"**. **Full Access**: All roles can update all evidence. No filtering or access restrictions.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data` (untuk upload file) atau `application/x-www-form-urlencoded`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | **Yes** | Evidence ID yang akan di-update |

**Request Body (form-data, all fields optional):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | No | Case ID (jika ingin mengubah case yang terkait) |
| `evidence_number` | string | No | Evidence number (jika disediakan, tidak boleh kosong) |
| `type` | string | No | Evidence type name (text input dari form UI). **Jika disediakan, sistem akan mencari atau membuat EvidenceType baru secara otomatis** |
| `source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| `evidence_file` | file | No | Evidence file upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). File akan disimpan ke `data/evidence/` directory dengan SHA256 hash |
| `evidence_summary` | string | No | Evidence summary/description (disimpan ke field `description` di database) |
| `investigator` | string | No | Investigator name (who collected/analyzed the evidence) |
| `person_name` | string | Conditional | Person of interest name. **Hanya digunakan jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI)**. Jika disediakan dan `suspect_id` tidak disediakan, sistem akan mencari existing suspect dengan nama tersebut. Jika tidak ditemukan, sistem akan otomatis membuat suspect baru dengan nama tersebut dan link evidence_number ke suspect tersebut |
| `suspect_status` | string | Conditional | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be selected from UI, no default). **Hanya digunakan jika `is_unknown_person = false` (radio button "Person Name" dipilih)** |
| `is_unknown_person` | boolean | No | Flag yang menandakan apakah person tersebut unknown/tidak diketahui. **Jika `true` (radio button "Unknown Person" dipilih di UI):** Sistem akan cek apakah sudah ada suspect "Unknown" dengan `case_id` yang sama. Jika `suspect_id` disediakan, evidence akan ter-link ke suspect "Unknown" dengan `suspect_id` tersebut. Jika `suspect_id` tidak disediakan, evidence akan ter-link ke suspect "Unknown" yang sudah ada (yang paling baru) atau membuat suspect "Unknown" baru jika belum ada |
| `suspect_id` | integer | No | Suspect ID untuk memilih suspect tertentu. **Jika `suspect_id` disediakan, evidence akan ter-link ke suspect dengan `suspect_id` tersebut (harus merupakan suspect dengan `case_id` yang sama). Jika `person_name` dan/atau `suspect_status` juga disediakan, suspect tersebut akan di-update dengan nilai baru (tidak membuat suspect baru)** |

**Catatan:** 
- Semua field bersifat opsional (partial update)
- Jika `evidence_file` disediakan, file lama akan diganti dengan file baru
- Field `file_path`, `file_size`, `file_hash`, `file_type`, dan `file_extension` akan otomatis di-update setelah file di-upload
- Jika `evidence_number` disediakan secara manual, tidak boleh kosong (mengembalikan error 400: "evidence_number cannot be empty when provided manually")
- Jika `evidence_number` yang ingin diupdate sudah digunakan oleh evidence lain (bukan evidence yang sedang diupdate), akan mengembalikan error 400 dengan pesan yang menampilkan ID evidence yang sudah menggunakan `evidence_number` tersebut
- Jika `evidence_number` yang ingin diupdate sama dengan `evidence_number` yang sudah ada di evidence yang sedang diupdate, tidak akan ada error (tidak perlu update)
- `case_id` harus dipilih dari dropdown cases (gunakan `GET /api/v1/cases/get-all-cases` untuk mendapatkan cases yang tersedia)
- `evidence_source` harus dipilih dari sumber evidence: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR"
- `suspect_status` harus dipilih dari: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (tidak ada default, bisa null)

**Example Request (form-data):**
```
case_id: 1
evidence_number: 32342223
type: Dokumen
source: Handphone
evidence_summary: Updated GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.
investigator: Solehun
person_name: Dwiky
suspect_status: Witness
evidence_file: [file]
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence updated successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "32342223",
    "source": "Handphone",
    "file_path": "data/evidence/evidence_20251111_163602_32342223.png",
    "description": "Updated GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
    "title": "Buronan Maroko Interpol",
    "investigator": "Solehun",
    "agency": "Trikora",
    "person_name": "Dwiky",
    "updated_at": "11/11/2025"
  }
}
```

**Error Responses:**

**400 Bad Request (Empty evidence_number):**
```json
{
  "status": 400,
  "detail": "evidence_number cannot be empty when provided manually"
}
```

**400 Bad Request (Duplicate evidence_number):**
```json
{
  "status": 400,
  "detail": "Evidence number '454950045' already exists for another evidence (ID: 1)"
}
```

**Catatan:** Error ini terjadi ketika `evidence_number` yang ingin diupdate sudah digunakan oleh evidence lain (bukan evidence yang sedang diupdate). Pesan error akan menampilkan ID evidence yang sudah menggunakan `evidence_number` tersebut untuk membantu troubleshooting.

**400 Bad Request (Invalid file type):**
```json
{
  "status": 400,
  "detail": "File type tidak didukung. Hanya file PDF dan Image yang diperbolehkan (extensions: pdf, jpg, jpeg, png, gif, bmp, webp)"
}
```

**404 Not Found (Evidence not found):**
```json
{
  "status": 404,
  "detail": "Evidence with ID {evidence_id} not found"
}
```

**404 Not Found (Case not found):**
```json
{
  "status": 404,
  "detail": "Case with ID {case_id} not found"
}
```

**404 Not Found (Suspect not found):**
```json
{
  "status": 404,
  "detail": "Suspect with ID {suspect_id} not found for this case"
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
  "detail": "Unexpected server error: {error_message}"
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
- **Default sorting:** Results are sorted by **ID descending** (newest first, oldest last)

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspects retrieved successfully",
  "data": [
    {
      "id": 2,
      "case_id": 1,
      "person_name": "Mandeep Singh",
      "case_name": "Kasus kriminal pembunuhan di terminal pasar minggu",
      "investigator": "Solehun",
      "agency": "Trikora",
      "status": "Suspected",
      "created_at": "2025-11-11T14:16:16.306085+07:00",
      "updated_at": "2025-11-11T14:20:25.732980+07:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

**Note:** 
- **Default sorting:** Data diurutkan dari **terbaru ke terlama** berdasarkan ID (ID terbesar = terbaru, ID terkecil = terlama)
- Status values: `"Witness"` (blue tag), `"Reported"` (yellow tag), `"Suspected"` (orange tag), `"Suspect"` (red tag), `"Defendant"` (dark red tag)
- Field `agency` didapatkan dari table `cases` berdasarkan `case_id` dan `investigator`
- Field `person_name` adalah alias untuk `name` dari suspect

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

### 2. Get Suspect Summary

**Endpoint:** `GET /api/v1/suspects/get-suspect-summary`

**Description:** Get suspect management summary statistics. Returns total person count and total evidence count. **Endpoint ini digunakan untuk menampilkan summary di dashboard Suspect Management**. **Full Access**: All roles can see statistics for all suspects and evidence. No filtering or access restrictions.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect summary retrieved successfully",
  "data": {
    "total_person": 21,
    "total_evidence": 21
  }
}
```

**Example Request:**
```
GET /api/v1/suspects/get-suspect-summary
Authorization: Bearer <access_token>
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

### 3. Get Suspect Detail

**Endpoint:** `GET /api/v1/suspects/get-suspect-detail/{suspect_id}`

**Description:** Get detailed information of a specific suspect by ID. **Endpoint ini digunakan untuk menampilkan detail suspect di halaman detail suspect**. Returns suspect details including name, case information, investigator, status, evidence information, and timestamps. **Full Access**: All roles can view details of all suspects. No filtering or access restrictions.

**Headers:** 
- `Authorization: Bearer <access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | **Yes** | Suspect ID |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect detail retrieved successfully",
  "data": {
    "id": 1,
    "person_name": "Bombom",
    "suspect_status": "Reported",
    "investigator": "Solehun",
    "case_name": "Kasus kriminal pembunuhan di terminal pasar minggu",
    "created_at_case": "20/12/2025",
    "evidence": [
      {
        "evidence_count": "2",
        "list_evidence": [
          {
            "id": 1,
            "evidence_number": "EVID-1-20251116-0001",
            "evidence_summary": "Handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.",
            "file_path": "data/evidence/evidence_20251116_211231_EVID-1-20251116-0001.png",
            "created_at": "2025-11-16T21:12:31.214904+07:00",
            "updated_at": "2025-11-16T21:27:35.722355+07:00"
          },
          {
            "id": 2,
            "evidence_number": "33242352",
            "evidence_summary": "Terdapat dialog seputar pembakaran dengan suspect lain.",
            "file_path": "data/evidence/evidence_20251116_211231_EVID-1-20251116-0002.png",
            "created_at": "2025-11-16T21:12:31.214904+07:00",
            "updated_at": "2025-11-16T21:27:35.722355+07:00"
          }
        ]
      }
    ],
    "suspect_notes": "Dokumentasi detail, isolasi jaringan, serta pencatatan chain of custody sangat penting untuk memastikan integritas bukti GPS handphone dan dapat dipertanggungjawabkan di pengadilan."
  }
}
```

**Example Request:**
```
GET /api/v1/suspects/get-suspect-detail/7
Authorization: Bearer <access_token>
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found"
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
  "message": "Unexpected server error: {error_message}"
}
```

**Note:**
- Field `person_name` adalah nama suspect (bisa "Unknown" jika `is_unknown = true`)
- Field `suspect_status` bisa `null` jika suspect adalah unknown person
- Field `created_at_case` adalah tanggal pembuatan case dalam format DD/MM/YYYY
- Field `evidence` berisi array dengan:
  - `evidence_count`: Jumlah total evidence yang terhubung dengan suspect (dalam format string)
  - `list_evidence`: Array dari evidence records yang terhubung dengan suspect, berisi:
    - `id`: Evidence ID
    - `evidence_number`: Nomor evidence
    - `evidence_summary`: Ringkasan/deskripsi evidence (dari field `description` di Evidence)
    - `file_path`: Path file evidence
    - `created_at`: Timestamp pembuatan evidence dalam format ISO 8601 dengan timezone
    - `updated_at`: Timestamp update evidence dalam format ISO 8601 dengan timezone
- Field `suspect_notes`: Catatan tentang suspect (dari field `notes` di Suspect atau Evidence, jika tersedia)

---

### 4. Create Suspect

**Endpoint:** `POST /api/v1/suspects/create-suspect`

**Description:** Create a new suspect record. Supports file upload for evidence files. **Endpoint ini digunakan dari form "Add Suspect"**. Jika `evidence_number` disediakan, sistem akan mencari existing evidence dengan `evidence_number` tersebut. Jika ditemukan, suspect akan di-link ke evidence tersebut. Jika tidak ditemukan dan ada `evidence_file`, sistem akan membuat evidence baru. **Full Access**: All roles can create suspect for all cases. No filtering or access restrictions.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data` (untuk upload file) atau `application/x-www-form-urlencoded`

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | **Yes** | Case ID where suspect will be added |
| `person_name` | string | Conditional | Person name. **WAJIB diisi jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI). Tidak perlu diisi jika `is_unknown_person = true` (radio button "Unknown Person" dipilih)** - field ini tidak akan ditampilkan di UI jika "Unknown Person" dipilih |
| `suspect_status` | string | Conditional | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be selected from UI, no default). **WAJIB diisi jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI). Jika `is_unknown_person = true`, field ini tidak akan ditampilkan di UI dan akan di-set ke `null`** |
| `is_unknown_person` | boolean | No | Flag yang menandakan apakah person tersebut unknown/tidak diketahui. **Jika `true` (radio button "Unknown Person" dipilih di UI):** `person_name` dan `suspect_status` tidak perlu diisi (tidak akan ditampilkan di UI), suspect akan dibuat dengan nama "Unknown", dan `suspect_status` akan di-set ke `null`. **Jika `false` (radio button "Person Name" dipilih):** `person_name` dan `suspect_status` wajib diisi |
| `evidence_number` | string | **Conditional** | Evidence number (can be generated automatically or manually input). **WAJIB disediakan jika `evidence_file` tidak ada**. **If provided manually, cannot be empty** |
| `evidence_file` | file | **Conditional** | Evidence file upload. **WAJIB disediakan jika `evidence_number` tidak ada**. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). File akan disimpan ke `data/evidence/` directory dengan SHA256 hash |
| `evidence_source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| `evidence_summary` | string | No | Evidence summary/description |

**Catatan Field Required:**
- **Required (Wajib):** `case_id`
- **Conditional Required (Wajib jika `is_unknown_person = false`):** `person_name` wajib diisi jika `is_unknown_person = false`. Jika `is_unknown_person = false` dan `person_name` tidak diisi, akan mengembalikan error 400: "person_name is required when is_unknown_person is false"
- **Conditional Required (Wajib jika `is_unknown_person = false`):** `suspect_status` wajib diisi jika `is_unknown_person = false`. Jika `is_unknown_person = false` dan `suspect_status` tidak diisi, akan mengembalikan error 400: "suspect_status is required when is_unknown_person is false"
- **Conditional Required (Wajib minimal salah satu):** `evidence_file` **ATAU** `evidence_number` harus disediakan. Jika keduanya tidak disediakan, akan mengembalikan error 400: "evidence_file atau evidence_number harus disediakan untuk create suspect"
- **Optional (Opsional):** `evidence_source`, `evidence_summary`, `is_unknown_person`

**Catatan tentang `is_unknown_person` dan Validasi:**
- **Jika `is_unknown_person = true` (radio button "Unknown Person" dipilih di UI):** 
  - Di UI **TIDAK menampilkan** kolom `person_name` dan `suspect_status` (field ini tidak perlu diisi)
  - `person_name` tidak perlu diisi (akan diabaikan dan di-set menjadi "Unknown")
  - `suspect_status` tidak perlu diisi (akan diabaikan dan di-set ke `null`)
  - `name` di database = "Unknown"
  - `status` di database = `null`
- **Jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI):**
  - Di UI menampilkan kolom `person_name` dan `suspect_status`
  - `person_name` **WAJIB diisi** (jika tidak diisi, akan error 400: "person_name is required when is_unknown_person is false")
  - `suspect_status` **WAJIB diisi** (jika tidak diisi, akan error 400: "suspect_status is required when is_unknown_person is false")
  - `name` di database = `person_name` (wajib)
  - `status` di database = `suspect_status` (wajib)

**Format Auto-Generate Evidence Number:**
Jika radio "Generating" dipilih atau `evidence_number` tidak disediakan dan `evidence_file` ada:
- **Format:** `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
- **Contoh:** `EVID-1-20251110-0001`, `EVID-1-20251110-0002`, dst.

**Workflow Create Suspect:**
1. **Create Suspect baru** (selalu membuat suspect baru)
2. **Link ke Evidence (jika `evidence_number` disediakan):**
   - Cari existing evidence dengan `evidence_number` yang sama di case tersebut
   - **Jika ditemukan:** Link suspect ke evidence (update `suspect.evidence_id` dengan `evidence_number` dari evidence yang ditemukan)
   - **Jika tidak ditemukan dan ada `evidence_file`:** Create evidence baru dengan `evidence_number` yang diberikan
   - **Jika tidak ditemukan dan tidak ada `evidence_file`:** Gunakan `evidence_number` yang diberikan (suspect.evidence_id = evidence_number, tapi evidence record tidak dibuat)

**Perilaku Evidence Number:**
- **Jika "Generating" dipilih atau `evidence_number` TIDAK disediakan:**
  - **Jika `evidence_file` ada:** Otomatis membuat `evidence_number` dengan format `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence baru
  - **Jika `evidence_file` TIDAK ada:** `evidence_number = null` (opsional, tidak membuat record Evidence)
- **Jika "Manual Input" dipilih dan `evidence_number` disediakan:**
  - Tidak boleh kosong (mengembalikan error 400: "evidence_number cannot be empty when provided manually")
  - Sistem memeriksa apakah record Evidence sudah ada dengan `evidence_number` yang sama
  - **Jika Evidence sudah ada:** Link suspect ke evidence yang sudah ada (update file jika `evidence_file` disediakan)
  - **Jika Evidence TIDAK ada dan ada `evidence_file`:** Membuat record Evidence baru dengan `evidence_number` yang diberikan
  - **Jika Evidence TIDAK ada dan tidak ada `evidence_file`:** Gunakan `evidence_number` yang diberikan (suspect.evidence_id = evidence_number, tapi evidence record tidak dibuat)

**Example Request (form-data) - Manual Evidence Number (Person Name):**
```
case_id: 1
person_name: John Doe
suspect_status: Suspect
is_unknown_person: false
evidence_number: 32342223
evidence_source: Handphone
evidence_summary: Smartphone dari tersangka
evidence_file: [file]
```

**Example Request (form-data) - Auto-Generate Evidence Number (Person Name):**
```
case_id: 1
person_name: John Doe
suspect_status: Witness
is_unknown_person: false
evidence_source: Handphone
evidence_summary: Test evidence summary
evidence_file: [file]
```

**Example Request (form-data) - Unknown Person:**
```
case_id: 1
is_unknown_person: true
evidence_number: 32342223
evidence_source: Handphone
evidence_summary: Evidence for unknown person
evidence_file: [file]
```

**Example Request (form-data) - Link to Existing Evidence (Person Name):**
```
case_id: 1
person_name: Nathalie
suspect_status: Witness
is_unknown_person: false
evidence_number: 32342223
evidence_source: Handphone
evidence_summary: Link to existing evidence
```


**Catatan:**
- **Selalu create suspect baru** (tidak mengecek existing suspect dengan nama yang sama)
- Field `evidence_file` atau `evidence_number` **WAJIB** disediakan (minimal salah satu)
- Field `suspect_status` bersifat opsional dan disimpan di database. **Jika tidak disediakan, akan menjadi `null` (tidak ada nilai default)**. Di case detail, `person_type` akan `null` jika `suspect_status = null`. **PENTING: Jika `is_unknown_person = true`, `suspect_status` akan di-set ke `null` (override jika ada value)**.
- Field `is_unknown_person`: 
  - **Jika `true` (radio button "Unknown" dipilih di UI):** `person_name` akan diabaikan, suspect akan dibuat dengan nama "Unknown", dan `suspect_status` akan di-set ke `null` (override jika ada value)
  - **Jika `false` (radio button "Person Name" dipilih di UI):** `person_name` dan `suspect_status` dapat diisi sesuai input user
- Upload file: File disimpan dengan format `evidence_{timestamp}_{evidence_number}.{extension}` di direktori `data/evidence/` dengan perhitungan hash SHA256.
- Field `evidence_number` bersifat **opsional**:
  - **Jika TIDAK disediakan + file ada:** Otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence
  - **Jika TIDAK disediakan + tidak ada file:** Mengembalikan error 400: "evidence_file atau evidence_number harus disediakan untuk create suspect"
  - **Jika disediakan secara manual:** Tidak boleh kosong (mengembalikan error 400 jika kosong)
  - **Linking:** Suspect dan Evidence ter-link via `evidence_id` (suspect.evidence_id = evidence.evidence_number)
- **Auto-fill:**
  - `investigator`: **TIDAK ada di form**. Otomatis diambil dari `case.main_investigator` berdasarkan `case_id`. Jika `case.main_investigator` tidak ada, fallback ke `current_user` (fullname atau email)
- **Case Log:**
  - Endpoint ini secara otomatis membuat case log entry ketika suspect ditambahkan
  - Jika `evidence_number` disediakan dan Evidence record dibuat/dihubungkan, case log entry untuk evidence juga akan dibuat

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Suspect created successfully",
  "data": {
    "id": 6,
    "name": "John Doe",
    "case_id": 1,
    "case_name": "Data Breach",
    "investigator": "Solehun",
    "status": "Suspect",
    "is_unknown": false,
    "evidence_number": "32342223",
    "evidence_source": "Handphone",
    "evidence_summary": "Smartphone dari tersangka",
    "created_by": "admin@example.com",
    "created_at": "2025-12-16T10:00:00Z",
    "updated_at": "2025-12-16T10:00:00Z"
  }
}
```

**Frontend Validation & Error Handling:**

Sebelum mengirim request ke API, frontend akan melakukan validasi required fields. Jika ada required fields yang belum diisi, akan muncul dialog error:

**1. Dialog "Incomplete Form" (Saat Submit):**
- **Trigger:** User mengklik tombol submit/confirm, tetapi ada required fields yang belum diisi
- **Message:** "Please complete required fields before submitting"
- **Actions:**
  - **Continue Editing:** Menutup dialog dan kembali ke form untuk melengkapi required fields

**Required Fields untuk Create Suspect:**
- `case_id` (selalu required)
- `person_name` (required jika `is_unknown_person = false`)
- `suspect_status` (required jika `is_unknown_person = false`)
- `evidence_file` atau `evidence_number` (minimal salah satu harus disediakan)

**2. Dialog "Unsaved Changes" (Saat Cancel/Close):**
- **Trigger:** User mengklik tombol cancel/close atau menutup form, tetapi ada perubahan yang belum disimpan
- **Message:** "If you leave this form, your data will not be saved"
- **Actions:**
  - **Leave Anyway:** Menutup form tanpa menyimpan perubahan
  - **Continue Editing:** Kembali ke form untuk melanjutkan editing

**Error Responses:**

**400 Bad Request (Empty evidence_number when provided manually):**
```json
{
  "status": 400,
  "detail": "evidence_number cannot be empty when provided manually"
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

### 5. Update Suspect

**Endpoint:** `PUT /api/v1/suspects/update-suspect/{suspect_id}`

**Description:** Update suspect information. **Endpoint ini digunakan dari form "Edit Suspect"**. Endpoint ini hanya menerima field: `case_id`, `person_name` (dan `suspect_status`), atau `is_unknown_person`. Field evidence tidak dapat diupdate melalui endpoint ini. **Full Access**: All roles can update all suspects. No filtering or access restrictions.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/x-www-form-urlencoded` atau `multipart/form-data`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | **Yes** | Suspect ID yang akan di-update |

**Request Body (form-data, all fields optional):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | No | Case ID (jika ingin mengubah case yang terkait). Jika diubah, `case_name` dan `investigator` akan diupdate otomatis dari case |
| `person_name` | string | Conditional | Person name. **WAJIB diisi jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI). Tidak perlu diisi jika `is_unknown_person = true` (radio button "Unknown Person" dipilih)** |
| `is_unknown_person` | boolean | No | Flag yang menandakan apakah person tersebut unknown/tidak diketahui. **Jika `true` (radio button "Unknown Person" dipilih di UI):** `person_name` dan `suspect_status` tidak perlu diisi (tidak akan ditampilkan di UI), suspect akan diubah menjadi "Unknown", dan `suspect_status` akan di-set ke `null`. **Jika `false` (radio button "Person Name" dipilih):** `person_name` wajib diisi, `suspect_status` wajib diisi |
| `suspect_status` | string | Conditional | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be selected from UI, no default). **WAJIB diisi jika `is_unknown_person = false` (radio button "Person Name" dipilih). Jika `is_unknown_person = true`, field ini tidak akan ditampilkan di UI dan akan di-set ke `null`** |

**Catatan Field Required:**
- **Required (Wajib):** `suspect_id` (di path parameter)
- **Conditional Required (Wajib jika `is_unknown_person = false`):** `person_name` wajib diisi jika `is_unknown_person = false`. Jika `is_unknown_person = false` dan `person_name` tidak diisi, akan mengembalikan error 400: "person_name is required when is_unknown_person is false"
- **Conditional Required (Wajib jika `is_unknown_person = false`):** `suspect_status` wajib diisi jika `is_unknown_person = false`. Jika `is_unknown_person = false` dan `suspect_status` tidak diisi, akan mengembalikan error 400: "suspect_status is required when is_unknown_person is false"
- **Optional (Opsional):** `case_id`, `is_unknown_person`

**Catatan Penting:**
- Field evidence (`evidence_number`, `evidence_source`, `evidence_file`, `evidence_summary`) **TIDAK dapat diupdate** melalui endpoint ini
- Jika `case_id` diubah, `case_name` dan `investigator` akan diupdate otomatis dari case yang dipilih

**Catatan tentang `is_unknown_person` dan `suspect_status`:**
- **Jika `is_unknown_person = true` (radio button "Unknown Person" dipilih di UI):** 
  - Di UI **TIDAK menampilkan** kolom `person_name` dan `suspect_status` (field ini tidak perlu diisi)
  - `person_name` tidak perlu diisi (akan diabaikan dan di-set menjadi "Unknown")
  - `suspect_status` tidak perlu diisi (akan diabaikan dan di-set ke `null`)
  - `name` di database = "Unknown"
  - `status` di database = `null`
- **Jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI):**
  - Di UI menampilkan kolom `person_name` dan `suspect_status`
  - `person_name` **WAJIB diisi** (jika tidak diisi, akan error 400: "person_name is required when is_unknown_person is false")
  - `suspect_status` **WAJIB diisi** (jika tidak diisi, akan error 400: "suspect_status is required when is_unknown_person is false")
  - `name` di database = `person_name` (wajib)
  - `status` di database = `suspect_status` (wajib)

**Example Request (form-data) - Person Name:**
```
case_id: 1
person_name: John Doe
suspect_status: Defendant
is_unknown_person: false
```

**Example Request (form-data) - Unknown Person:**
```
case_id: 1
is_unknown_person: true
```

**Example Request (form-data) - Update case_id only:**
```
case_id: 2
```

**Example Request (form-data) - Update person_name and suspect_status only:**
```
person_name: Jane Smith
suspect_status: Suspect
```

**Catatan:** 
- Semua field bersifat opsional (partial update), tetapi ada conditional requirements berdasarkan `is_unknown_person`
- Jika `case_id` diubah, `case_name` dan `investigator` akan diupdate otomatis dari case yang dipilih
- `case_id` harus dipilih dari dropdown cases (gunakan `GET /api/v1/cases/get-all-cases` untuk mendapatkan cases yang tersedia)
- `suspect_status` harus dipilih dari: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (tidak ada default, bisa null)
- Field evidence (`evidence_number`, `evidence_source`, `evidence_file`, `evidence_summary`) **TIDAK dapat diupdate** melalui endpoint ini. Gunakan endpoint evidence management untuk update evidence

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect updated successfully",
  "data": {
    "id": 7,
    "name": "Doyo Wati Jo Sa Li",
    "case_name": "Kasus kriminal pembunuhan di terminal pasar minggu",
    "investigator": "Solehun",
    "status": "Reported",
    "evidence_number": "45495004534839",
    "evidence_source": "SSD",
    "created_at": "2025-11-16T22:20:01.709015+07:00",
    "updated_at": "2025-11-17T15:44:34.479614+07:00"
  }
}
```

**Error Responses:**

**400 Bad Request (person_name required):**
```json
{
  "status": 400,
  "message": "person_name is required when is_unknown_person is false"
}
```

**400 Bad Request (suspect_status required):**
```json
{
  "status": 400,
  "message": "suspect_status is required when is_unknown_person is false"
}
```

**400 Bad Request (person_name cannot be empty):**
```json
{
  "status": 400,
  "message": "person_name cannot be empty"
}
```

**400 Bad Request (suspect_status cannot be empty):**
```json
{
  "status": 400,
  "message": "suspect_status cannot be empty"
}
```

**400 Bad Request (Invalid suspect_status):**
```json
{
  "status": 400,
  "message": "Invalid suspect_status value: 'InvalidStatus'. Valid values are: Witness, Reported, Suspected, Suspect, Defendant"
}
```

**404 Not Found (Suspect not found):**
```json
{
  "status": 404,
  "message": "Suspect with ID {suspect_id} not found"
}
```

**404 Not Found (Case not found):**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found"
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

**500 Internal Server Error (Database error):**
```json
{
  "status": 500,
  "message": "Database error: {error_str}"
}
```

**500 Internal Server Error (Unexpected error):**
```json
{
  "status": 500,
  "message": "Unexpected server error: {error_message}"
}
```

---

**Endpoint:** `POST /api/v1/suspects/evidence`

**Description:** Add new evidence to an existing suspect. Supports file upload for evidence files.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request Body (multipart/form-data - all fields required, including `suspect_id`):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `suspect_id` | integer | Yes | Unique suspect identifier |
| `evidence_number` | string | No | Evidence Number (if manual input) |
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


## 👤 Person Management (Legacy)

### Base Path
`/api/v1/persons`

### 1. Create Person

**Endpoint:** `POST /api/v1/persons/create-person`

**Description:** Add a person of interest (suspect/witness) to a case. **Endpoint ini HARUS membuat suspect + evidence bersamaan (1 person, 1 evidence)**. Endpoint ini digunakan dari form "Add Person" di Case Details. Endpoint ini selalu membuat suspect baru (tidak mengecek existing suspect dengan nama yang sama). **Full Access**: All roles can create person for all cases. No filtering or access restrictions.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data` (untuk upload file) atau `application/x-www-form-urlencoded`

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | **Yes** | Case ID where person will be added |
| `person_name` | string | **Conditional** | Person name. **WAJIB diisi jika `is_unknown_person = false`**. **Tidak perlu diisi jika `is_unknown_person = true`** (akan diabaikan) |
| `suspect_status` | string | No | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be selected from UI, no default). **Hanya digunakan jika `is_unknown_person = false`**. **Jika `is_unknown_person = true`, akan di-set ke `null`**. **Jika tidak disediakan, akan menjadi `null` (tidak ada nilai default)** |
| `evidence_number` | string | **Conditional** | Evidence number (can be generated automatically or manually input). **WAJIB disediakan jika `evidence_file` tidak ada**. **If provided manually, cannot be empty** |
| `evidence_file` | file | **Conditional** | Evidence file upload. **WAJIB disediakan jika `evidence_number` tidak ada**. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). File akan disimpan ke `data/evidence/` directory dengan SHA256 hash |
| `evidence_source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| `evidence_summary` | string | No | Evidence summary/description |
| `is_unknown_person` | boolean | No | Flag yang menandakan apakah person tersebut unknown/tidak diketahui. **Jika `true` (radio button "Unknown" dipilih di UI), `person_name` dan `suspect_status` tidak perlu diisi. Sistem akan membuat suspect "Unknown" baru dengan `name = "Unknown"`, `status = null`, dan `is_unknown = true`. Evidence akan ter-link ke suspect tersebut**. **Jika `false` (radio button "Person Name" dipilih), `person_name` wajib diisi dan `suspect_status` dapat diisi** (default: `false`) |

**Catatan Field Required:**
- **Required (Wajib):** `case_id`
- **Conditional Required (Wajib jika `is_unknown_person = false`):** `person_name` wajib diisi jika `is_unknown_person = false`. Jika `is_unknown_person = false` dan `person_name` tidak diisi, akan mengembalikan error 400: "person_name is required when is_unknown_person is false"
- **Conditional Required (Wajib jika `is_unknown_person = false`):** `suspect_status` wajib diisi jika `is_unknown_person = false`. Jika `is_unknown_person = false` dan `suspect_status` tidak diisi, akan mengembalikan error 400: "suspect_status is required when is_unknown_person is false"
- **Conditional Required (Wajib minimal salah satu):** `evidence_file` **ATAU** `evidence_number` harus disediakan. Jika keduanya tidak disediakan, akan mengembalikan error 400: "evidence_file atau evidence_number harus disediakan untuk create person"
- **Optional (Opsional):** `evidence_source`, `evidence_summary`, `is_unknown_person`

**Catatan tentang `is_unknown_person` dan `suspect_status`:**
- **Jika `is_unknown_person = true` (radio button "Unknown" dipilih di UI):** 
  - Di UI hanya menampilkan kolom untuk evidence (tidak ada kolom `person_name` dan `suspect_status`)
  - `person_name` tidak perlu diisi (akan diabaikan jika dikirim)
  - `suspect_status` tidak perlu diisi (akan di-set ke `null`)
  - **Suspect "Unknown" akan dibuat:**
    - Sistem akan membuat suspect baru dengan `name = "Unknown"`, `status = null`, dan `is_unknown = true`
    - Evidence akan ter-link ke suspect tersebut (`suspect_id` di-set)
  - Di case-detail, setiap suspect "Unknown" akan muncul sebagai person terpisah dengan `id` yang valid (menggunakan `suspect_id` sebagai key, bukan `name`)
- **Jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI):**
  - Di UI menampilkan kolom `person_name` dan `suspect_status`
  - `person_name` **WAJIB diisi** (jika tidak diisi, akan error 400: "person_name is required when is_unknown_person is false")
  - `suspect_status` **WAJIB diisi** (jika tidak diisi, akan error 400: "suspect_status is required when is_unknown_person is false")
  - Suspect dibuat dengan `name = person_name` dan `status = suspect_status`
  - Evidence dibuat dengan `suspect_id` yang link ke suspect tersebut

**Format Auto-Generate Evidence Number:**
Jika `evidence_number` tidak disediakan dan `evidence_file` ada, sistem akan otomatis membuat evidence number dengan format:
- **Format:** `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
- **Contoh:** `EVID-1-20251110-0001`, `EVID-1-20251110-0002`, dst.
- **Sequence:** Nomor urut berdasarkan jumlah Evidence untuk case tersebut (4 digit dengan leading zeros)

**Workflow Create Person:**
1. **Validasi input:**
   - Jika `is_unknown_person = false` dan `person_name` tidak diisi, akan mengembalikan error 400: "person_name is required when is_unknown_person is false"
   - Jika `is_unknown_person = false` dan `suspect_status` tidak diisi, akan mengembalikan error 400: "suspect_status is required when is_unknown_person is false"
2. **Generate evidence_number jika belum ada:**
   - Jika `evidence_number` tidak disediakan dan `evidence_file` ada, sistem akan otomatis membuat evidence number dengan format `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}`
   - Jika `evidence_number` tidak disediakan dan `evidence_file` tidak ada, akan mengembalikan error 400: "evidence_file atau evidence_number harus disediakan untuk create person"
3. **Create atau Update Evidence (wajib - selalu dilakukan):**
   - Jika evidence dengan `evidence_number` yang sama sudah ada, update evidence dengan file jika `evidence_file` disediakan
   - Jika evidence belum ada, create evidence baru dengan `evidence_number` yang diberikan
   - Evidence selalu dibuat/updated meskipun `is_unknown_person = true`
4. **Create Suspect (selalu dilakukan):**
   - **Jika `is_unknown_person = false`:**
     - Membuat suspect baru dengan `name = person_name` dan `status = suspect_status`
     - Set `suspect_id` di Evidence yang baru dibuat/diupdate
     - Case log dibuat untuk mencatat penambahan person baru
   - **Jika `is_unknown_person = true`:**
     - Membuat suspect baru dengan `name = "Unknown"`, `status = null`, dan `is_unknown = true`
     - Set `suspect_id` di Evidence yang baru dibuat/diupdate
     - Case log dibuat untuk mencatat penambahan person "Unknown" baru
     - Di case-detail, setiap suspect "Unknown" akan muncul sebagai person terpisah dengan `id` yang valid (menggunakan `suspect_id` sebagai key, bukan `name`)

**Perilaku Evidence Number:**
- **Jika `evidence_number` disediakan (input manual):**
  - Tidak boleh kosong (mengembalikan error 400: "evidence_number cannot be empty when provided manually")
  - Sistem memeriksa apakah record Evidence sudah ada dengan `evidence_number` yang sama
  - **Jika Evidence sudah ada:** Update evidence dengan file jika `evidence_file` disediakan
  - **Jika Evidence TIDAK ada:** Membuat record Evidence baru dengan `evidence_number` yang diberikan
- **Jika `evidence_number` TIDAK disediakan:**
  - **Jika `evidence_file` ada:** Otomatis membuat `evidence_number` dengan format `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence baru
  - **Jika `evidence_file` TIDAK ada:** Mengembalikan error 400: "evidence_file atau evidence_number harus disediakan untuk create person"

**Example Request (form-data) - Manual Evidence Number:**
```
case_id: 1
person_name: Mandeep Singh
suspect_status: Suspect
evidence_number: 342344442
evidence_source: Handphone
evidence_summary: GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.
evidence_file: [file]
```

**Example Request (form-data) - Auto-Generate Evidence Number:**
```
case_id: 1
person_name: Mandeep Singh
suspect_status: Witness
evidence_source: Handphone
evidence_summary: Test evidence summary
evidence_file: [file]
```

**Example Request (form-data) - Link to Existing Evidence:**
```
case_id: 1
person_name: Nathalie
suspect_status: Witness
evidence_number: 342344442
evidence_source: Handphone
evidence_summary: Link to existing evidence
```

**Example Request (form-data) - Unknown:**
```
case_id: 1
is_unknown_person: true
evidence_number: 342344442
evidence_source: Handphone
evidence_summary: Evidence dari unknown person
evidence_file: [file]
```

**Catatan:** 
- **Endpoint ini HARUS membuat evidence (selalu dilakukan)**
- **Suspect selalu dibuat (baik untuk `is_unknown_person = true` maupun `false`)**
- **Jika `is_unknown_person = true`:** Suspect "Unknown" akan dibuat dengan `name = "Unknown"`, `status = null`, dan `is_unknown = true`. Evidence akan ter-link ke suspect tersebut.
- Field `evidence_file` atau `evidence_number` **WAJIB** disediakan (minimal salah satu)
- Field `person_name` **WAJIB diisi jika `is_unknown_person = false`**. Jika `is_unknown_person = false` dan `person_name` tidak diisi, akan mengembalikan error 400: "person_name is required when is_unknown_person is false"
- Field `suspect_status` **WAJIB diisi jika `is_unknown_person = false`**. Jika `is_unknown_person = false` dan `suspect_status` tidak diisi, akan mengembalikan error 400: "suspect_status is required when is_unknown_person is false". **PENTING: Jika `is_unknown_person = true`, `suspect_status` akan di-set ke `null` (suspect "Unknown" akan dibuat dengan `status = null`)**.
- Field `is_unknown_person`: 
  - **Jika `true` (radio button "Unknown" dipilih di UI):** 
    - `person_name` tidak perlu diisi (akan diabaikan jika dikirim)
    - `suspect_status` tidak perlu diisi (akan di-set ke `null`)
    - Suspect "Unknown" akan dibuat dengan `name = "Unknown"`, `status = null`, dan `is_unknown = true`
    - Evidence dibuat dengan `suspect_id` yang link ke suspect "Unknown"
    - Di case-detail, setiap suspect "Unknown" akan muncul sebagai person terpisah dengan `id` yang valid (menggunakan `suspect_id` sebagai key, bukan `name`)
  - **Jika `false` (radio button "Person Name" dipilih di UI):** 
    - `person_name` **WAJIB diisi** (jika tidak diisi, akan error 400: "person_name is required when is_unknown_person is false")
    - `suspect_status` **WAJIB diisi** (jika tidak diisi, akan error 400: "suspect_status is required when is_unknown_person is false")
    - Suspect dibuat dengan `name = person_name` dan `status = suspect_status`
    - Evidence dibuat dengan `suspect_id` yang link ke suspect tersebut
- Upload file: File disimpan dengan format `evidence_{timestamp}_{evidence_number}.{extension}` di direktori `data/evidence/` dengan perhitungan hash SHA256.
- Field `evidence_number` bersifat **opsional**:
  - **Jika TIDAK disediakan + file ada:** Otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence
  - **Jika TIDAK disediakan + tidak ada file:** Mengembalikan error 400: "evidence_file atau evidence_number harus disediakan untuk create person"
  - **Jika disediakan secara manual:** Tidak boleh kosong (mengembalikan error 400 jika kosong)
  - **Linking:** Jika `is_unknown_person = false`, Suspect dan Evidence ter-link via `suspect_id` di Evidence (evidence.suspect_id = suspect.id)

**Response (201 Created) - Jika `is_unknown_person = false` (Person dengan nama):**
```json
{
  "status": 201,
  "message": "Person created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "name": "Mandeep Singh",
    "suspect_status": "Suspected",
    "evidence_number": "342344442",
    "evidence_source": "Handphone",
    "investigator": "Solehun",
    "created_by": "Admin Forensic",
    "created_at": "2025-12-20T10:00:00+07:00",
    "updated_at": "2025-12-20T10:00:00+07:00"
  }
}
```

**Response (201 Created) - Jika `is_unknown_person = true` (Unknown):**
```json
{
  "status": 201,
  "message": "Evidence created successfully (Unknown)",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "342344442",
    "source": "Handphone",
    "file_path": "data/evidence/evidence_20251111_163602_342344442.png",
    "description": "Evidence dari unknown person",
    "title": "Kasus kriminal pembunuhan di terminal pasar minggu",
    "investigator": "Solehun",
    "person_name": null,
    "suspect_status": null,
    "is_unknown_person": true,
    "created_at": "11/11/2025"
  }
}
```

**Catatan:** 
- Endpoint ini secara otomatis membuat entry case log ketika person ditambahkan (hanya jika `is_unknown_person = false`)
- Jika `is_unknown_person = true`, tidak ada case log untuk penambahan person (karena tidak ada suspect yang dibuat)
- Evidence selalu dibuat/updated meskipun `is_unknown_person = true`

**Frontend Validation & Error Handling:**

Sebelum mengirim request ke API, frontend akan melakukan validasi required fields. Jika ada required fields yang belum diisi, akan muncul dialog error:

**1. Dialog "Incomplete Form" (Saat Submit):**
- **Trigger:** User mengklik tombol submit/confirm, tetapi ada required fields yang belum diisi
- **Message:** "Please complete required fields before submitting"
- **Actions:**
  - **Continue Editing:** Menutup dialog dan kembali ke form untuk melengkapi required fields

**Required Fields untuk Create Person:**
- `case_id` (selalu required)
- `person_name` (required jika `is_unknown_person = false`)
- `suspect_status` (required jika `is_unknown_person = false`)
- `evidence_file` atau `evidence_number` (minimal salah satu harus disediakan)

**2. Dialog "Unsaved Changes" (Saat Cancel/Close):**
- **Trigger:** User mengklik tombol cancel/close atau menutup form, tetapi ada perubahan yang belum disimpan
- **Message:** "If you leave this form, your data will not be saved"
- **Actions:**
  - **Leave Anyway:** Menutup form tanpa menyimpan perubahan
  - **Continue Editing:** Kembali ke form untuk melanjutkan editing

**Error Responses:**

**400 Bad Request (person_name required):**
```json
{
  "status": 400,
  "detail": "person_name is required when is_unknown_person is false"
}
```

**400 Bad Request (suspect_status required):**
```json
{
  "status": 400,
  "detail": "suspect_status is required when is_unknown_person is false"
}
```

**400 Bad Request (Empty evidence_number when provided manually):**
```json
{
  "status": 400,
  "detail": "evidence_number cannot be empty when provided manually"
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

**403 Forbidden (Access Denied):**
```json
{
  "status": 403,
  "detail": "You do not have permission to create person for this case"
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
     - `person_name`: `Mandeep Singh` (Text) - Conditional (Required if `is_unknown_person = false`, Optional if `is_unknown_person = true`)
     - `suspect_status`: `Suspect` (Text) - Optional (only used if `is_unknown_person = false`)
     - `evidence_number`: `342344442` (Text) - Optional (if provided, cannot be empty)
     - `evidence_source`: `Handphone` (Text) - Optional
     - `evidence_file`: Select `File` type and choose file - Optional (if provided, file will be saved to `data/evidence/` directory)
     - `evidence_summary`: `GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian.` (Text) - Optional
     - `is_unknown_person`: `false` (Text) - Optional (default: `false`. If `true`, `person_name` and `suspect_status` are not required)
5. **Click Send**

**Catatan:** 
- Untuk upload file, ubah tipe `evidence_file` dari "Text" ke "File" di Postman
- Field `case_id` wajib diisi
- Field `person_name` wajib diisi jika `is_unknown_person = false` (conditional required)
- Field `person_name` dan `suspect_status` tidak akan ditampilkan di UI jika `is_unknown_person = true` (tidak perlu diisi)
- Field `evidence_file` atau `evidence_number` harus disediakan minimal salah satu (conditional required)
- Upload file: File disimpan dengan format `evidence_{timestamp}_{evidence_number}.{extension}` di direktori `data/evidence/` dengan perhitungan hash SHA256
- Field `suspect_status` bersifat opsional dan disimpan di database. Jika tidak disediakan, akan menjadi `null` (tidak ada nilai default)
- Field `evidence_number` bersifat **opsional**:
  - **Jika TIDAK disediakan + file ada:** Otomatis membuat `EVID-{case_id}-{YYYYMMDD}-{sequence:04d}` dan membuat record Evidence
  - **Jika TIDAK disediakan + tidak ada file:** Mengembalikan error 400: "evidence_file atau evidence_number harus disediakan untuk create person"
  - **Jika disediakan secara manual:** Tidak boleh kosong (mengembalikan error 400: "evidence_number cannot be empty when provided manually")
  - **Linking:** Suspect dan Evidence ter-link via `evidence_id` (suspect.evidence_id = evidence.evidence_number)

---

**Catatan:** 
- Endpoint `get-person` dan `get-persons-by-case` sudah tidak digunakan karena data person/suspect sudah ditampilkan di endpoint `get-case-detail-comprehensive`.
- Untuk mendapatkan detail person/suspect, gunakan endpoint `GET /api/v1/cases/get-case-detail-comprehensive/{case_id}` yang akan menampilkan semua persons of interest dalam response `persons_of_interest`.
- Untuk mendapatkan detail suspect lengkap, gunakan endpoint `GET /api/v1/suspects/get-suspect-by-id/{suspect_id}`.

---

### 2. Update Person

**Endpoint:** `PUT /api/v1/persons/update-person/{person_id}`

**Description:** Update person information. All fields are optional (partial update). **Endpoint ini digunakan dari form "Edit Person of Interest"**. **Full Access**: All roles can update all persons. No filtering or access restrictions.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data` atau `application/x-www-form-urlencoded`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | integer | **Yes** | Person ID yang akan di-update |

**Request Body (form-data, all fields optional):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_name` | string | Conditional | Person name. **Wajib jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI). Tidak perlu diisi jika `is_unknown_person = true` (radio button "Unknown Person" dipilih)** - field ini akan diabaikan dan suspect akan diubah menjadi "Unknown" |
| `suspect_status` | string | Conditional | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be selected from UI, no default). **Hanya digunakan jika `is_unknown_person = false` (radio button "Person Name" dipilih). Jika `is_unknown_person = true`, field ini akan diabaikan dan `suspect_status` akan di-set ke `null`** |
| `is_unknown_person` | boolean | No | Flag yang menandakan apakah person tersebut unknown/tidak diketahui. **Jika `true` (radio button "Unknown Person" dipilih di UI):** `person_name` dan `suspect_status` tidak perlu diisi (akan diabaikan), suspect akan diubah menjadi "Unknown", dan `suspect_status` akan di-set ke `null`. **Jika `false` (radio button "Person Name" dipilih):** `person_name` wajib diisi, `suspect_status` optional (default: `false`) |

**Example Request (form-data):**
```
person_name: Updated Name
suspect_status: Witness
is_unknown_person: false
```

**Example Request (form-data) - Unknown Person:**
```
is_unknown_person: true
```
**Catatan:** Ketika `is_unknown_person = true`, `person_name` dan `suspect_status` tidak perlu diisi (akan diabaikan). Suspect akan diubah menjadi "Unknown" dan `suspect_status` akan di-set ke `null`.

**Catatan:**
- Semua field bersifat opsional (partial update), tetapi ada conditional requirements berdasarkan `is_unknown_person`
- **Jika `is_unknown_person = true` (radio button "Unknown Person" dipilih di UI):** 
  - Di UI **TIDAK menampilkan** kolom `person_name` dan `suspect_status` (field ini tidak perlu diisi)
  - `person_name` tidak perlu diisi (akan diabaikan dan di-set menjadi "Unknown")
  - `suspect_status` tidak perlu diisi (akan diabaikan dan di-set ke `null`)
  - `name` di database = "Unknown"
  - `suspect_status` di database = `null`
- **Jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI):**
  - Di UI menampilkan kolom `person_name` dan `suspect_status`
  - `person_name` **WAJIB diisi** (jika tidak diisi, akan error 400: "person_name is required when is_unknown_person is false")
  - `suspect_status` **WAJIB diisi** (jika tidak diisi, akan error 400: "suspect_status is required when is_unknown_person is false")
  - `name` di database = `person_name` (wajib)
  - `status` di database = `suspect_status` (wajib)
- `suspect_status` dapat diubah ke status lain: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (hanya jika `is_unknown_person = false`)
- Endpoint ini secara otomatis membuat case log entry ketika person di-update

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Person updated successfully",
  "data": {
    "id": 1,
    "name": "Mangdepp Singh",
    "suspect_status": "Witness",
    "evidence_number": "EVID-1-20251111-0001",
    "evidence_source": "Handphone",
    "evidence_summary": "Berdasarkan rekaman CCTV",
    "investigator": "Solehun",
    "case_id": 1,
    "created_by": "admin@gmail.com",
    "created_at": "2025-11-10T23:53:56.323353+07:00",
    "updated_at": "2025-11-11T10:30:00.000000+07:00"
  }
}
```

**Error Responses:**

**400 Bad Request (person_name required):**
```json
{
  "status": 400,
  "detail": "person_name is required when is_unknown_person is false"
}
```

**400 Bad Request (suspect_status required):**
```json
{
  "status": 400,
  "detail": "suspect_status is required when is_unknown_person is false"
}
```

**400 Bad Request (person_name cannot be empty):**
```json
{
  "status": 400,
  "detail": "person_name cannot be empty"
}
```

**400 Bad Request (suspect_status cannot be empty):**
```json
{
  "status": 400,
  "detail": "suspect_status cannot be empty"
}
```

**403 Forbidden (Access Denied):**
```json
{
  "status": 403,
  "detail": "You do not have permission to update this person"
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "detail": "Person with ID {person_id} not found"
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

### 3. Delete Person

**Endpoint:** `DELETE /api/v1/persons/delete-person/{person_id}`

**Description:** Delete a person of interest. **Endpoint ini digunakan dari dialog "Delete Person"**. Evidence yang terhubung dengan person ini TIDAK akan dihapus, hanya link ke person yang dihapus. Evidence akan muncul sebagai "Unknown" di case detail. **Full Access**: All roles can delete all persons. No filtering or access restrictions.

**Headers:** `Authorization: Bearer <access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | integer | **Yes** | Person ID yang akan dihapus |

**Catatan:**
- **Evidence TIDAK dihapus:** Evidence yang terhubung dengan person ini tetap ada di database
- **Evidence menjadi "orphaned":** Evidence akan kehilangan link ke person dan muncul sebagai "Unknown" di case detail
- **Case log dibuat:** Endpoint ini secara otomatis membuat case log entry dengan pesan "Change: Deleting suspect {name}"

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Person deleted successfully"
}
```

**Postman Testing Guide:**

1. **Set Request Method:** `DELETE`
2. **Set URL:** `http://localhost:8000/api/v1/persons/delete-person/{person_id}` (ganti `{person_id}` dengan ID person yang akan dihapus, contoh: `1`)
3. **Tab Authorization:**
   - Type: `Bearer Token`
   - Token: `{{access_token}}` (or paste your access token)
4. **Click Send**

**Catatan:**
- Tidak perlu request body untuk DELETE request
- Person ID dikirim sebagai path parameter

**Error Responses:**

**403 Forbidden (Access Denied):**
```json
{
  "status": 403,
  "detail": "You do not have permission to delete this person"
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
The API implements Role-Based Access Control (RBAC) for different modules:
- **Case Management Modules (Case, Evidence, Suspect, Person, Case Log, Reports)**: **Full Access** - All roles can access all data
- **User Management**: **Admin Only** - Only admin role can access user management endpoints
- **Analytics Management**: **Role-Based** - Access control based on user roles (see Analytics Management documentation)

### How Access Control Works?

**1. Role vs Tag - Important Difference:**

| Concept | Function | Usage |
|---------|----------|-------|
| **Role** | Determines data access level | Used for **access control** - determines if user can see all data or only their own data |
| **Tag** | User category/position | Used for **display** and **mapping to role** when creating user, **NOT used for data filtering** |

**2. Tag to Role Mapping:**

When creating a new user, tag is automatically mapped to role:

| User Tag | Resulting Role | Case Management Access | User Management Access |
|----------|----------------|------------------------|------------------------|
| `"Admin"` | `admin` | ✅ Full Access (all data) | ✅ Full Access (can manage users) |
| `"Investigator"` | `user` | ✅ Full Access (all data) | ❌ No Access (403 Forbidden) |
| `"Ahli Forensic"` | `user` | ✅ Full Access (all data) | ❌ No Access (403 Forbidden) |
| Other tags | `user` (default) | ✅ Full Access (all data) | ❌ No Access (403 Forbidden) |

**3. Access Control by Module:**

**Case Management Modules (Full Access):**
- **All Roles**: Can access, view, create, update, delete all cases, evidence, suspects, persons, case logs, and reports
- **No Filtering**: No restrictions based on `main_investigator` or user information
- **No 403 Errors**: All roles can access all data without permission errors

**User Management (Admin Only):**
- **Admin Role**: Can access, view, create, update, delete all users
- **Regular User Role**: Cannot access user management endpoints (403 Forbidden)

**Analytics Management (Role-Based):**
- See Analytics Management documentation for detailed access control rules
- Uses filtering based on `analytic_name`, `summary`, or `created_by` containing user's `fullname` or `email`

**Note:** The old data filtering mechanism (based on `main_investigator` matching user's `fullname` or `email`) **no longer applies** to Case Management modules. All Case Management modules now have full access for all roles.

### Roles

| Role | Description | Case Management Access | User Management Access |
|------|-------------|------------------------|------------------------|
| `admin` | Administrator | Full access to all data | Full access (can manage users) |
| `user` | Regular user | Full access to all data | No access (403 Forbidden) |

### Role Mapping from Tags

When creating a user, the role is automatically mapped from the tag:

| Tag | Role |
|-----|------|
| `"Admin"` | `admin` |
| `"Investigator"` | `user` |
| `"Ahli Forensic"` | `user` |
| Other tags | `user` (default) |

### Practical Examples

**Scenario 1: User with Admin Role**
```
User: {
  fullname: "Admin User",
  email: "admin@example.com",
  tag: "Admin",
  role: "admin"
}

Case Management: ✅ Can access ALL cases, evidence, suspects, persons, case logs, and reports
User Management: ✅ Can access, create, update, delete all users
```

**Scenario 2: User with User Role (Tag: Investigator)**
```
User: {
  fullname: "Investigator A",
  email: "investigator@example.com",
  tag: "Investigator",
  role: "user"
}

Case Management: ✅ Can access ALL cases, evidence, suspects, persons, case logs, and reports
  - Case 1 (main_investigator: "Investigator A"): ✅ CAN ACCESS
  - Case 2 (main_investigator: "Investigator B"): ✅ CAN ACCESS
  - Case 3 (main_investigator: "Ahli Forensic X"): ✅ CAN ACCESS
  - All cases accessible regardless of main_investigator value

User Management: ❌ Cannot access (403 Forbidden)
  - GET /api/v1/auth/get-all-users: ❌ 403 Forbidden
  - POST /api/v1/auth/create-user: ❌ 403 Forbidden
```

**Scenario 3: User with User Role (Tag: Ahli Forensic)**
```
User: {
  fullname: "Ahli Forensic X",
  email: "forensic@example.com",
  tag: "Ahli Forensic",
  role: "user"
}

Case Management: ✅ Can access ALL cases, evidence, suspects, persons, case logs, and reports
  - Case 1 (main_investigator: "Ahli Forensic X"): ✅ CAN ACCESS
  - Case 2 (main_investigator: "Ahli Forensic Y"): ✅ CAN ACCESS
  - Case 3 (main_investigator: "Investigator A"): ✅ CAN ACCESS
  - All cases accessible regardless of main_investigator value

User Management: ❌ Cannot access (403 Forbidden)
```

**Important Points:**
- Tags `"Investigator"` and `"Ahli Forensic"` **both result in role `"user"`**
- Both have **full access** to Case Management modules (all data)
- Both have **no access** to User Management (admin only)
- Tag difference is only for **display/organization purposes**, not for access control
- **No filtering** is applied to Case Management modules - all roles see all data

### Access Control Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER LOGIN                                │
│  { fullname, email, tag, role }                             │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Check Module Type    │
         └───────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ Case Mgmt    │   │ User Mgmt    │
│ Modules      │   │              │
└──────┬───────┘   └──────┬───────┘
       │                  │
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│ Full Access  │   │ Check Role   │
│ All Roles    │   └──────┬───────┘
│              │          │
│ ✅ Admin     │          │
│ ✅ User      │          ▼
│              │   ┌──────────────┐
│ No Filtering │   │ admin?       │
│ No 403       │   └──────┬───────┘
└──────────────┘          │
                          │
                  ┌───────┴───────┐
                  │               │
                  ▼               ▼
            ┌─────────┐     ┌──────────┐
            │  Yes    │     │   No     │
            │ ✅ Allow│     │ ❌ 403   │
            └─────────┘     └──────────┘
```

### Summary

| Aspect | Explanation |
|--------|-------------|
| **Case Management Modules** | **Full Access** - All roles (admin/user) can access all data |
| **User Management** | **Admin Only** - Only admin role can access user management endpoints |
| **Access Control Based On** | **Module Type** - Different modules have different access rules |
| **Tag Used For** | Display and mapping to role when creating user |
| **Case Management Filtering** | **No Filtering** - All roles see all data |
| **User Management Filtering** | **Role-Based** - Only admin can access |
| **Tag "Investigator" vs "Ahli Forensic"** | Both result in role "user" with full access to Case Management, no access to User Management |

### Access Rules

#### Case Management

**All Case Management Endpoints:**
- **Full Access**: All roles (Admin, Investigator, Ahli Forensic) can access, view, create, update, delete, and export all cases. No filtering or access restrictions based on `main_investigator`.

**Affected Endpoints:**
- `GET /api/v1/cases/get-all-cases` - All cases accessible to all roles
- `GET /api/v1/cases/get-case-detail-comprehensive/{case_id}` - All case details accessible to all roles
- `PUT /api/v1/cases/update-case/{case_id}` - All cases can be updated by all roles
- `GET /api/v1/cases/export-case-details-pdf/{case_id}` - All cases can be exported by all roles
- `POST /api/v1/cases/save-notes` - Notes can be saved for all cases by all roles
- `PUT /api/v1/cases/edit-notes` - Notes can be edited for all cases by all roles
- `GET /api/v1/cases/statistics/summary` - All statistics accessible to all roles

**Example:**
- User with any role can access all cases regardless of `main_investigator` value
- No 403 Forbidden errors for accessing cases from other users

#### Evidence Management

**All Evidence Management Endpoints:**
- **Full Access**: All roles (Admin, Investigator, Ahli Forensic) can access, view, and create evidence for all cases. No filtering or access restrictions based on `main_investigator`.

**Affected Endpoints:**
- `GET /api/v1/evidence/get-evidence-list` - All evidence accessible to all roles
- `GET /api/v1/evidence/get-evidence-summary` - All statistics accessible to all roles
- `POST /api/v1/evidence/create-evidence` - Evidence can be created for all cases by all roles
- `GET /api/v1/evidence/get-evidence-by-id{evidence_id}` - All evidence details accessible to all roles

#### Suspect Management

**All Suspect Management Endpoints:**
- **Full Access**: All roles (Admin, Investigator, Ahli Forensic) can access, view, create, update, and delete all suspects. No filtering or access restrictions based on `main_investigator`.

**Affected Endpoints:**
- `GET /api/v1/suspects/` - All suspects accessible to all roles
- `GET /api/v1/suspects/get-suspect-summary` - All statistics accessible to all roles
- `POST /api/v1/suspects/create-suspect` - Suspects can be created for all cases by all roles
- `GET /api/v1/suspects/get-suspect-by-id/{suspect_id}` - All suspect details accessible to all roles
- `PUT /api/v1/suspects/update-suspect/{suspect_id}` - All suspects can be updated by all roles
- `DELETE /api/v1/suspects/delete-suspect/{suspect_id}` - All suspects can be deleted by all roles

#### Person Management (Legacy)

**All Person Management Endpoints:**
- **Full Access**: All roles (Admin, Investigator, Ahli Forensic) can access, view, create, update, and delete all persons. No filtering or access restrictions based on `main_investigator`.

**Affected Endpoints:**
- `POST /api/v1/persons/create-person` - Persons can be created for all cases by all roles
- `PUT /api/v1/persons/update-person/{person_id}` - All persons can be updated by all roles
- `DELETE /api/v1/persons/delete-person/{person_id}` - All persons can be deleted by all roles

**Note:** Person Management endpoints are legacy endpoints that work similarly to Suspect Management. Both endpoints manage the same underlying data (Suspect model).

#### Case Log Management

**All Case Log Management Endpoints:**
- **Full Access**: All roles (Admin, Investigator, Ahli Forensic) can access, view, and update case logs for all cases. No filtering or access restrictions based on `main_investigator`.

**Affected Endpoints:**
- `GET /api/v1/case-logs/case/logs/{case_id}` - All case logs accessible to all roles
- `GET /api/v1/case-logs/log/{log_id}` - All log details accessible to all roles
- `PUT /api/v1/case-logs/change-log/{case_id}` - Case status can be updated for all cases by all roles

#### Reports Management

**All Reports Management Endpoints:**
- **Full Access**: All roles (Admin, Investigator, Ahli Forensic) can access all case summary and evidence chain reports. No filtering or access restrictions based on `main_investigator`.

**Affected Endpoints:**
- `GET /api/v1/reports/case-summary/{case_id}` - All case summary reports accessible to all roles
- `GET /api/v1/reports/evidence-chain/{evidence_id}` - All evidence chain reports accessible to all roles

#### User Management

**All User Management Endpoints:**
- **Admin Role**: ✅ Can access, view, create, update, and delete all users.
- **Regular User Role**: ❌ Cannot access user management endpoints (403 Forbidden). Only admin can manage users.

**Affected Endpoints:**
- `GET /api/v1/auth/get-all-users` - Admin only
- `POST /api/v1/auth/create-user` - Admin only
- `PUT /api/v1/auth/update-user/{user_id}` - Admin only
- `DELETE /api/v1/auth/delete-user/{user_id}` - Admin only

**Note:** User Management is the only module with restricted access. All other modules (Case, Evidence, Suspect, Person, Case Log, Reports) have full access for all roles.

### Important Notes

1. **Full Access for Case Management Modules:** All Case Management, Evidence Management, Suspect Management, Person Management, Case Log Management, and Reports Management endpoints have **full access** for all roles. No filtering or access restrictions are applied.

2. **User Management Restriction:** Only Admin role can access User Management endpoints. Regular users (Investigator, Ahli Forensic) will receive 403 Forbidden when attempting to access user management endpoints.

3. **No 403 Forbidden Errors:** Regular users will NOT receive 403 Forbidden errors when accessing Case Management, Evidence Management, Suspect Management, Person Management, Case Log Management, or Reports Management endpoints, as all roles have full access to these modules.

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

