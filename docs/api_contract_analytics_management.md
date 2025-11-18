# API Contract Documentation - Analytics Management
## Digital Forensics Analysis Platform - Backend API

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**API Version:** `/api/v1`

---

## 📋 Daftar Isi

1. [Authentication](#authentication)
2. [Overview](#overview)
3. [File Management](#file-management)
4. [Analytics Management](#analytics-management)
5. [Device Management](#device-management)
6. [Analytics Endpoints](#analytics-endpoints)
7. [Analytics Report Management](#analytics-report-management)
8. [Role-Based Access Control](#role-based-access-control)
9. [Error Responses](#error-responses)

---

## 🔐 Authentication

### Overview
Semua endpoint yang dilindungi memerlukan Bearer Token authentication. Token diperoleh dari endpoint login:
- **Access Token**: Valid selama 24 jam (1440 menit). Digunakan untuk autentikasi API.
- **Refresh Token**: Valid selama 7 hari. Digunakan untuk mendapatkan access token baru ketika expired.

**Alur Token:**
1. User login → menerima `access_token` dan `refresh_token`
2. Gunakan `access_token` untuk request API (expires setelah 24 jam)
3. Ketika `access_token` expired → gunakan `refresh_token` untuk mendapatkan token baru
4. Setelah 7 hari → user harus login lagi

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

### 1. Login

**Endpoint:** `POST /api/v1/auth/login`

**Deskripsi:** Autentikasi user dan mendapatkan access token.

**Headers:** `Content-Type: application/json`

**Request Body:**
```json
{
  "email": "admin@gmail.com",
  "password": "admin.admin"
}
```

**Request Body Fields:**
| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `email` | string | Yes | Email user |
| `password` | string | Yes | Password user |

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

**Informasi Token:**
- `access_token`: JWT token valid selama **24 jam**. Gunakan ini untuk autentikasi API.
- `refresh_token`: Token valid selama **7 hari**. Gunakan ini untuk refresh access token ketika expired.

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

### 2. Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

**Deskripsi:** Refresh access token menggunakan refresh token. Mengimplementasikan refresh token rotation untuk keamanan - refresh token lama akan di-revoke dan token baru akan dikeluarkan.

**Headers:** `Content-Type: application/json`

**Catatan:** Endpoint ini TIDAK memerlukan Authorization header (public endpoint).

**Request Body:**
```json
{
  "refresh_token": "d8IL20i8CR4UqcbtydMQ_c7u-mvEHffed9IIS-DYDBelBH3411929NaWEEi1D6p2"
}
```

**Request Body Fields:**
| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `refresh_token` | string | Yes | Refresh token yang valid |

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

**Catatan Penting:**
- Refresh token lama akan di-**revoke** (tidak bisa digunakan lagi)
- Selalu gunakan **refresh_token baru** untuk refresh berikutnya
- Access_token baru valid selama **24 jam**
- Refresh_token baru valid selama **7 hari** dari sekarang

**Error Responses:**

**401 Unauthorized (Invalid or Expired Refresh Token):**
```json
{
  "status": 401,
  "message": "Invalid or expired refresh token",
  "data": null
}
```

**Penyebab:**
- Refresh token tidak valid
- Refresh token sudah expired (lebih dari 7 hari)
- Refresh token sudah di-revoke (sudah digunakan atau user logout)

---

### 3. Get Current User Profile

**Endpoint:** `GET /api/v1/auth/me`

**Deskripsi:** Mendapatkan profil user yang sedang login.

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

**Response Fields:**
| Field | Type | Deskripsi |
|-------|------|-----------|
| `id` | integer | ID user |
| `email` | string | Email user |
| `fullname` | string | Nama lengkap user |
| `tag` | string | Tag user |
| `role` | string | Role user (admin/user) |
| `password` | string | Password asli user (plain text) |

**Catatan Keamanan:** Field `password` berisi password asli dalam bentuk plain text. Mengembalikan password plain text dalam response API sangat tidak disarankan untuk keamanan. Disarankan untuk tidak menggunakan fitur ini di production environment.

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
  "message": "Failed to retrieve user profile",
  "data": null
}
```

---

### 4. Logout

**Endpoint:** `POST /api/v1/auth/logout`

**Deskripsi:** Logout user dan revoke semua token (access token dan semua refresh token). Setelah logout, user harus login lagi untuk mendapatkan token baru.

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
  "message": "Failed to logout user",
  "data": null
}
```

---

## Overview

### Kontrol Akses

**Kontrol Akses Analytics Management:**
- **Admin Role**: Dapat mengakses, melihat, membuat, dan mengelola semua analytics, files, dan devices di sistem.
- **Regular User Role**: Hanya dapat mengakses analytics, files, dan devices yang terkait dengan mereka (berdasarkan `analytic_name`, `summary`, `created_by`, `file_name`, atau `notes` yang mengandung fullname atau email user). Mencoba mengakses analytics lain akan mengembalikan 403 Forbidden.

**Kepemilikan Data:**
- Analytics dan files difilter berdasarkan `fullname` atau `email` user yang cocok dengan:
  - `Analytic.analytic_name`
  - `Analytic.summary`
  - `Analytic.created_by` (field khusus untuk informasi creator)
  - `File.notes`
  - `File.file_name`

**Catatan:** 
- Field `created_by` otomatis diisi saat membuat analytic baru dengan format `"Created by: {fullname} ({email})"` dan digunakan untuk filtering akses.
- Field `summary` tetap terpisah dan digunakan untuk menyimpan ringkasan analisis yang sebenarnya.
- Filtering dilakukan berdasarkan text matching di field name/summary/created_by untuk analytics.

---

## 📁 File Management

### Base Path
`/api/v1/analytics`

### 1. Get Files

**Endpoint:** `GET /api/v1/analytics/get-files`

**Deskripsi:** Mendapatkan daftar file yang sudah di-upload dengan dukungan pencarian dan filter. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Melihat semua file di database.
- **Regular User Role**: Hanya melihat file dimana `created_by`, `notes`, atau `file_name` mengandung `fullname` atau `email` mereka (case-insensitive matching).

**Catatan Penting:**
- Untuk file yang di-upload melalui endpoint `POST /api/v1/analytics/upload-data`, field `created_by` otomatis diisi dengan informasi user dalam format `"Created by: {fullname} ({email})"`.
- Sistem melakukan filtering berdasarkan pencarian substring di field `created_by`, `notes`, dan `file_name`, sehingga user non-admin hanya akan melihat file yang mereka upload sendiri.
- File yang di-upload sebelum implementasi fitur ini (tidak memiliki informasi user di `created_by`) tidak akan muncul untuk user non-admin karena tidak memiliki informasi ownership.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Default | Deskripsi |
|-----------|------|----------|---------|-----------|
| `search` | string | No | - | Kata kunci pencarian (mencari di file_name, notes, tools, method) |
| `filter` | string | No | "All" | Filter method: `"Deep Communication Analytics"`, `"Social Media Correlation"`, `"Contact Correlation"`, `"Hashfile Analytics"`, `"APK Analytics"`, `"All"` |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Retrieved 5 files successfully",
  "data": [
    {
      "id": 1,
      "file_name": "device_data.xlsx",
      "file_path": "data/uploads/device_data.xlsx",
      "notes": "Exported magnet axiom iphone",
      "type": "Handphone",
      "tools": "Magnet Axiom",
      "method": "Deep Communication Analytics",
      "total_size": 1048576,
      "total_size_formatted": "1.00 MB",
      "amount_of_data": 1500,
      "created_at": "2025-12-12T10:30:00Z",
      "date": "12/12/2025"
    }
  ]
}
```

**Response Fields:**
| Field | Type | Deskripsi |
|-------|------|-----------|
| `id` | integer | ID file |
| `file_name` | string | Nama file |
| `file_path` | string | Path file di server |
| `notes` | string | Catatan tambahan yang diinput user (tanpa modifikasi) |
| `type` | string | Tipe device |
| `tools` | string | Tools yang digunakan |
| `method` | string | Method analisis |
| `total_size` | integer | Ukuran file dalam bytes |
| `total_size_formatted` | string | Ukuran file yang sudah diformat (contoh: "1.00 MB") |
| `amount_of_data` | integer | Jumlah data yang berhasil diparsing |
| `created_at` | string | Timestamp kapan file dibuat |
| `date` | string | Tanggal file dibuat dalam format "DD/MM/YYYY" |

**Catatan Response:**
- Field `notes` berisi notes yang diinput user tanpa modifikasi.
- Field `created_by` digunakan secara internal oleh sistem untuk filtering akses file berdasarkan user, tetapi tidak ditampilkan dalam response.

**Error Responses:**

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**403 Forbidden (Access Denied):**
```json
{
  "status": 403,
  "message": "You do not have permission to access this resource",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to get files: <error_message>",
  "data": null
}
```

---

### 2. Upload Data

**Endpoint:** `POST /api/v1/analytics/upload-data`

**Deskripsi:** Upload file data untuk dianalisis. Endpoint ini menginisialisasi proses upload file yang sudah dienkripsi dalam format `.sdp` dan mengembalikan `upload_id` yang dapat digunakan untuk memantau progress upload. File akan diproses secara asynchronous di background.

**Catatan Penting:**
- Informasi user (fullname dan email) **otomatis disimpan** ke field `created_by` yang terpisah dalam format `"Created by: {fullname} ({email})"` untuk keperluan access control.
- Field `notes` tetap berisi notes yang diinput user tanpa modifikasi.
- Field `created_by` digunakan oleh sistem untuk filtering akses file berdasarkan user (lihat endpoint `GET /api/v1/analytics/get-files`).

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request Body (form-data):**
| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `file` | file | Yes | File yang akan di-upload (harus dalam format `.sdp` - file yang sudah dienkripsi) |
| `file_name` | string | Yes | Nama file (wajib diisi, tidak boleh kosong) |
| `notes` | string | No | Catatan tambahan terkait file (opsional) |
| `type` | string | Yes | Tipe device: `Handphone`, `SSD`, `Harddisk`, `PC`, `Laptop`, `DVR` |
| `tools` | string | Yes | Tools yang digunakan: `Magnet Axiom`, `Cellebrite`, `Oxygen`, `Encase` |
| `method` | string | Yes | Method analisis: `Deep Communication Analytics`, `Social Media Correlation`, `Contact Correlation`, `Hashfile Analytics` |

**Validation Rules:**
- Hanya file dengan ekstensi `.sdp` yang diterima (file yang sudah dienkripsi)
- Ukuran file maksimum: **100 MB**
- Semua field wajib (`file_name`, `type`, `tools`, `method`) harus diisi dan tidak boleh kosong
- Field `notes` bersifat opsional

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "File uploaded, encrypted & parsed successfully",
  "data": {
    "upload_id": "upload_1730558981_8df7b3a1",
    "status_upload": "Pending",
    "upload_type": "data"
  }
}
```

**Response Fields:**
| Field | Type | Deskripsi |
|-------|------|-----------|
| `upload_id` | string | ID unik untuk tracking progress upload |
| `status_upload` | string | Status upload: `"Pending"` (sedang menunggu proses) |
| `upload_type` | string | Tipe upload: `"data"` |

**Error Responses:**

**400 Bad Request (Invalid file extension):**
```json
{
  "status": 400,
  "message": "Only .sdp files are accepted. Please upload encrypted .sdp first",
  "data": null
}
```

**400 Bad Request (Invalid type):**
```json
{
  "status": 400,
  "message": "Invalid type. Allowed types: ['Handphone', 'SSD', 'Harddisk', 'PC', 'Laptop', 'DVR']",
  "data": null
}
```

**400 Bad Request (Invalid method):**
```json
{
  "status": 400,
  "message": "Invalid method. Must be one of: ['Deep Communication Analytics', 'Social Media Correlation', 'Contact Correlation', 'Hashfile Analytics']",
  "data": null
}
```

**400 Bad Request (Invalid tools):**
```json
{
  "status": 400,
  "message": "Invalid tools. Must be one of: ['Magnet Axiom', 'Cellebrite', 'Oxygen', 'Encase']",
  "data": null
}
```

**400 Bad Request (File size exceeds limit):**
```json
{
  "status": 400,
  "message": "File size exceeds 100MB limit",
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

**422 Unprocessable Entity (Missing required field):**
```json
{
  "status": 422,
  "message": "Field 'file_name' is required and cannot be empty",
  "error_field": "file_name",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Upload error: <error_message>",
  "data": null
}
```

---

### 3. Get Upload Progress

**Endpoint:** `GET /api/v1/analytics/upload-progress`

**Deskripsi:** Mendapatkan status progress dari proses upload file. Endpoint ini dapat digunakan untuk memantau progress upload baik untuk file data maupun file APK. Jika upload belum dimulai, endpoint ini akan secara otomatis memulai proses upload di background.

**Catatan Penting:**
- **Error Handling & Cleanup:** Jika proses upload gagal setelah file record di-insert ke database (misalnya error saat parsing, decryption timeout, atau error lainnya), sistem akan secara otomatis melakukan cleanup dengan menghapus:
  - File record dari database
  - Data terkait (social media, contacts, calls, hashfiles, chat messages) yang terkait dengan file tersebut
  - File fisik dari storage
- Hal ini memastikan tidak ada orphaned records yang tersisa di database ketika upload gagal.
- Status `"Failed"` mengindikasikan bahwa proses upload telah gagal dan tidak ada data yang tersimpan di database.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Default | Deskripsi |
|-----------|------|----------|---------|-----------|
| `upload_id` | string | Yes | - | ID upload yang ingin dicek progress-nya |
| `type` | string | No | `"data"` | Jenis upload: `"data"` atau `"apk"` |

**Response (200 OK - Progress):**
```json
{
  "status": "Progress",
  "message": "Upload Progress",
  "upload_id": "upload_1762102934_d45ac90f",
  "file_name": "Testing",
  "size": "0.000/1.716 MB",
  "percentage": 0,
  "upload_status": "Progress",
  "data": []
}
```

**Response (200 OK - Success):**
```json
{
  "status": "Success",
  "message": "Upload successful",
  "upload_id": "upload_1762102550_16bf143b",
  "file_name": "Testing",
  "size": "1.72 MB",
  "percentage": 100,
  "upload_status": "Success",
  "data": [
    {
      "file_id": 1,
      "file_path": "data/uploads/data/Exported_results_realme_hikari.xlsx",
      "notes": "testing",
      "type": "Handphone",
      "tools": "Oxygen",
      "method": "Contact Correlation",
      "total_size": "1.716 MB",
      "amount_of_data": "0",
      "create_at": "2025-11-02 23:56:36",
      "update_at": "2025-11-02 23:56:36"
    }
  ]
}
```

**Response (200 OK - Failed):**
```json
{
  "status": "Failed",
  "message": "Upload Failed! Please try again",
  "upload_id": "upload_1730558981_xxxx",
  "file_name": "Testing",
  "size": "Upload Failed! Please try again",
  "percentage": "Error",
  "upload_status": "Failed",
  "data": []
}
```

**Response Fields:**
| Field | Type | Deskripsi |
|-------|------|-----------|
| `status` | string | Status upload: `"Progress"`, `"Success"`, atau `"Failed"` |
| `message` | string | Pesan status |
| `upload_id` | string | ID upload |
| `file_name` | string | Nama file yang di-upload |
| `size` | string | Ukuran file (format: "uploaded/total MB" untuk progress, "total MB" untuk success) |
| `percentage` | integer/string | Persentase upload (0-100 untuk progress, "Error" untuk failed) |
| `upload_status` | string | Status upload: `"Progress"`, `"Success"`, atau `"Failed"` |
| `data` | array | Array kosong untuk progress/failed, atau array berisi detail file untuk success |

**Error Responses:**

**404 Not Found (Upload ID not found):**
```json
{
  "status": "Failed",
  "message": "Upload ID not found",
  "upload_id": "upload_1730558981_xxxx",
  "file_name": null,
  "size": "Upload Failed! Please try again",
  "percentage": "Error",
  "upload_status": "Failed",
  "data": []
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
  "status": "Failed",
  "message": "Internal server error: <error_message>",
  "upload_id": "upload_1730558981_xxxx",
  "file_name": null,
  "size": "Upload Failed! Please try again",
  "percentage": "Error",
  "upload_status": "Failed",
  "data": []
}
```

**Catatan Error Handling:**
- Jika error terjadi setelah file record di-insert ke database, sistem akan otomatis melakukan cleanup (menghapus file record, data terkait, dan file fisik).
- Response dengan status `"Failed"` berarti proses upload telah gagal dan tidak ada data yang tersimpan di database.
- Untuk error yang terjadi sebelum file record di-insert (misalnya error saat upload file atau decryption), tidak ada cleanup yang diperlukan karena belum ada data di database.

---

## 🔬 Analytics Management

### Base Path
`/api/v1/analytics`

### 1. Get All Analytics

**Endpoint:** `GET /api/v1/analytics/get-all-analytic`

**Deskripsi:** Mendapatkan daftar semua analytics dengan dukungan pencarian dan filter. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Melihat semua analytics di database.
- **Regular User Role**: Hanya melihat analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka (case-insensitive matching).

**Catatan:** Field `created_by` pada analytic baru otomatis berisi informasi user yang membuat analytic dalam format `"Created by: {fullname} ({email})"`, sehingga filtering berdasarkan `created_by` akan bekerja dengan baik untuk analytics yang dibuat setelah update ini.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Default | Deskripsi |
|-----------|------|----------|---------|-----------|
| `search` | string | No | - | Kata kunci pencarian (mencari di analytic_name, method, summary) |
| `method` | string | No | - | Filter berdasarkan method: `"Deep Communication Analytics"`, `"Social Media Correlation"`, `"Contact Correlation"`, `"APK Analytics"`, `"Hashfile Analytics"` |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Retrieved 3 analytics successfully",
  "data": [
    {
      "id": 1,
      "analytic_name": "Analysis by Investigator A",
      "method": "Deep Communication Analytics",
      "summary": "Communication analysis for case XYZ",
      "date": "14/11/2025"
    }
  ]
}
```

**Response Fields:**
| Field | Type | Deskripsi |
|-------|------|-----------|
| `id` | integer | ID analytic |
| `analytic_name` | string | Nama analytic |
| `method` | string | Method analisis |
| `summary` | string | Ringkasan analisis (dapat null) |
| `date` | string | Tanggal dibuat (format: DD/MM/YYYY) |

**Catatan Response:**
- Field `created_by` digunakan secara internal oleh sistem untuk filtering akses analytics berdasarkan user, tetapi tidak ditampilkan dalam response.

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
  "message": "Gagal mengambil data: <error_message>",
  "data": null
}
```

---

### 2. Create Analytic

**Endpoint:** `POST /api/v1/analytics/start-analyzing`

**Deskripsi:** Membuat session analytic baru. **Semua user yang terautentikasi dapat membuat analytics**, tetapi mereka hanya akan melihat analytics mereka sendiri di daftar (berdasarkan filtering). 

**Catatan Penting:** 
- Informasi user (fullname dan email) yang membuat analytic akan **otomatis disimpan** ke field `created_by` dalam format: `"Created by: {fullname} ({email})"`.
- Field `created_by` digunakan untuk filtering akses, sehingga user non-admin hanya dapat melihat analytics yang mereka buat sendiri.
- Field `summary` tetap terpisah dan dapat digunakan untuk menyimpan ringkasan analisis. Field `summary` dapat diupdate kemudian melalui endpoint edit summary.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request Body (form-data):**
| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `analytic_name` | string | Yes | Nama session analytic |
| `method` | string | Yes | Method analisis: `"Deep Communication Analytics"`, `"Social Media Correlation"`, `"Contact Correlation"`, `"APK Analytics"`, `"Hashfile Analytics"` |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Analytics created successfully",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "Analysis by Investigator A",
      "method": "Deep Communication Analytics",
      "summary": null,
      "created_at": "2025-12-12T10:30:00Z"
    }
  }
}
```

**Response Fields:**
| Field | Type | Deskripsi |
|-------|------|-----------|
| `id` | integer | ID analytic yang baru dibuat |
| `analytic_name` | string | Nama analytic |
| `method` | string | Method analisis yang dipilih |
| `summary` | string | Ringkasan analisis (dapat diisi kemudian melalui endpoint edit summary) |
| `created_at` | string | Timestamp kapan analytic dibuat |

**Catatan Response:**
- Field `created_by` otomatis disimpan ke database untuk filtering akses, tetapi tidak ditampilkan dalam response.

**Error Responses:**

**400 Bad Request (Empty analytic_name):**
```json
{
  "status": 400,
  "message": "analytic_name wajib diisi",
  "data": []
}
```

**400 Bad Request (Invalid method):**
```json
{
  "status": 400,
  "message": "Invalid method. Must be one of: ['Deep Communication Analytics', 'Social Media Correlation', 'Contact Correlation', 'APK Analytics', 'Hashfile Analytics']",
  "data": []
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
  "message": "Gagal membuat analytic: <error_message>",
  "data": null
}
```

---

### 3. Start Data Extraction

**Endpoint:** `POST /api/v1/analytics/start-extraction`

**Deskripsi:** Memulai ekstraksi data untuk sebuah analytic. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat memulai ekstraksi untuk semua analytics.
- **Regular User Role**: Hanya dapat memulai ekstraksi untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba memulai ekstraksi untuk analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic untuk memulai ekstraksi |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Data extraction completed Deep Communication Analytics",
  "data": {
    "analytic_id": 1,
    "method": "Deep Communication Analytics",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytic/deep-communication-analytics?analytic_id=1"
  }
}
```

**Error Responses:**

**400 Bad Request (Insufficient devices):**
```json
{
  "status": 400,
  "message": "Minimum 2 devices required. Currently have 1 device(s)",
  "data": {
    "device_count": 1,
    "required": 2
  }
}
```

**400 Bad Request (Unsupported method):**
```json
{
  "status": 400,
  "message": "Unsupported method: APK Analytics. Supported methods: Contact Correlation, Hashfile Analytics, Deep Communication Analytics, Social Media Correlation",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": []
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": []
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to start data extraction: <error_message>",
  "data": null
}
```

---

## 📱 Device Management

### Base Path
`/api/v1/analytics`

### 1. Get Devices

**Endpoint:** `GET /api/v1/analytics/get-devices`

**Deskripsi:** Mendapatkan daftar devices yang terhubung dengan sebuah analytic. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses devices untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses devices untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses devices untuk analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic untuk mendapatkan devices |

**Response (200 OK - With Devices):**
```json
{
  "status": 200,
  "message": "Retrieved 2 devices for Deep Communication Analytics",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "Analysis by Investigator A",
      "method": "Deep Communication Analytics"
    },
    "devices": [
      {
        "label": "Device A",
        "device_id": "1",
        "name": "John Doe",
        "phone_number": "+628123456789",
        "file_name": "device_data.xlsx",
        "file_size": "1.00 MB"
      }
    ],
    "device_count": 2
  }
}
```

**Response (200 OK - No Devices):**
```json
{
  "status": 200,
  "message": "No devices linked to this analytic yet",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "Analysis by Investigator A",
      "method": "Deep Communication Analytics"
    },
    "devices": [],
    "device_count": 0
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": []
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": []
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to get devices: <error_message>",
  "data": []
}
```

---

### 2. Add Device

**Endpoint:** `POST /api/v1/analytics/add-device`

**Deskripsi:** Menambahkan device baru ke analytic terbaru yang dibuat. Device akan otomatis ditambahkan ke analytic yang paling baru dibuat (berdasarkan `created_at`). Device akan diberi label otomatis (A, B, C, dst.) berdasarkan urutan penambahan. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat menambahkan device ke semua analytics.
- **Regular User Role**: Hanya dapat menambahkan device ke analytic dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba menambahkan device ke analytic lain akan mengembalikan 403 Forbidden.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request Body (form-data):**
| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `file_id` | integer | Yes | ID file yang sudah di-upload sebelumnya |
| `name` | string | Yes | Nama pemilik device |
| `phone_number` | string | Yes | Nomor telepon pemilik device |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Device added successfully",
  "data": {
    "analytics": [
      {
        "analytic_id": 1,
        "analytic_name": "Analysis by Investigator A",
        "method": "Deep Communication Analytics",
        "summary": null,
        "date": "12/12/2025",
        "device": [
          {
            "device_label": "A",
            "device_id": 1,
            "owner_name": "John Doe",
            "phone_number": "+628123456789"
          }
        ],
        "file_info": {
          "file_id": 1,
          "file_name": "device_data.xlsx",
          "file_type": "Handphone",
          "notes": "Uploaded by Investigator A",
          "tools": "Magnet Axiom",
          "method": "Deep Communication Analytics",
          "total_size": 1048576,
          "total_size_formatted": "1.00 MB"
        }
      }
    ]
  }
}
```

**Response Fields:**
| Field | Type | Deskripsi |
|-------|------|-----------|
| `analytics` | array | Array berisi informasi analytic dan device yang ditambahkan |
| `analytics[].analytic_id` | integer | ID analytic |
| `analytics[].analytic_name` | string | Nama analytic |
| `analytics[].method` | string | Method analisis |
| `analytics[].summary` | string/null | Summary analytic (dapat null) |
| `analytics[].date` | string | Tanggal dibuat (format: DD/MM/YYYY) |
| `analytics[].device` | array | Array berisi device yang ditambahkan |
| `analytics[].device[].device_label` | string | Label device (A, B, C, dst.) |
| `analytics[].device[].device_id` | integer | ID device |
| `analytics[].device[].owner_name` | string | Nama pemilik device |
| `analytics[].device[].phone_number` | string | Nomor telepon pemilik device |
| `analytics[].file_info` | object | Informasi file yang digunakan |
| `analytics[].file_info.file_id` | integer | ID file |
| `analytics[].file_info.file_name` | string | Nama file |
| `analytics[].file_info.file_type` | string | Tipe device (Handphone, SSD, dll.) |
| `analytics[].file_info.notes` | string | Catatan file |
| `analytics[].file_info.tools` | string | Tools yang digunakan |
| `analytics[].file_info.method` | string | Method analisis |
| `analytics[].file_info.total_size` | integer | Ukuran file dalam bytes |
| `analytics[].file_info.total_size_formatted` | string | Ukuran file yang sudah diformat (MB) |

**Error Responses:**

**400 Bad Request (Method mismatch):**
```json
{
  "status": 400,
  "message": "File method 'Contact Correlation' does not match analytic method 'Deep Communication Analytics'",
  "data": []
}
```

**400 Bad Request (File already used):**
```json
{
  "status": 400,
  "message": "This file is already used by another device in this analytic",
  "data": {
    "device_id": 1,
    "owner_name": "John Doe",
    "phone_number": "+628123456789"
  }
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": []
}
```

**404 Not Found (No analytic found):**
```json
{
  "status": 404,
  "message": "No analytic found. Please create an analytic first.",
  "data": []
}
```

**404 Not Found (File not found):**
```json
{
  "status": 404,
  "message": "File not found",
  "data": []
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to add device: <error_message>",
  "data": []
}
```

**Catatan Penting:**
- Device akan otomatis ditambahkan ke analytic yang paling baru dibuat (berdasarkan `created_at` terbaru)
- Method file harus sama dengan method analytic, jika tidak akan mengembalikan error 400
- Satu file tidak dapat digunakan oleh lebih dari satu device dalam analytic yang sama
- Device label (A, B, C, dst.) otomatis di-generate berdasarkan urutan penambahan

---

## 📊 Analytics Endpoints

### Base Path
`/api/v1/analytics` or `/api/v1/analytic`

### 1. Deep Communication Analytics

**Endpoint:** `GET /api/v1/analytic/deep-communication-analytics`

**Deskripsi:** Mendapatkan data deep communication analytics untuk sebuah analytic. Endpoint ini hanya dapat digunakan untuk analytic dengan method **"Deep Communication Analytics"**. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses analytics untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic (harus memiliki method "Deep Communication Analytics") |
| `device_id` | integer | No | Filter berdasarkan device ID. Jika tidak disediakan, akan mengambil data dari semua device yang terhubung dengan analytic |

**Logika Penentuan Person Name:**
- Jika `chat_type` adalah **"Group"** atau **"Broadcast"**: `person` value diambil dari field `group_name` pada table `chat_messages`
- Jika `chat_type` adalah **"One On One"**: `person` value diambil dari field `from_name` pada table `chat_messages`
- Jika `chat_type` adalah `null`: menggunakan logika default yang sudah ada (berdasarkan direction dan field lainnya)

**Response (200 OK - With Data):**
```json
{
  "status": 200,
  "message": "Deep Communication Analytics retrieved successfully",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Analysis by Investigator A"
    },
    "devices": [
      {
        "device_id": 1,
        "device_name": "John Doe",
        "phone_number": "+628123456789",
        "platform_cards": [
          {
            "platform": "Instagram",
            "platform_key": "instagram",
            "has_data": true,
            "message_count": 150,
            "intensity_list": [
              {
                "person": "Jane Smith",
                "intensity": 75
              },
              {
                "person": "Youth Bandung Reborn",
                "intensity": 42
              }
            ]
          }
        ]
      }
    ],
    "summary": "Lorem Ipsum is simply dummy text..."
  }
}
```

**Catatan:**
- `intensity_list` berisi daftar orang/grup yang berkomunikasi dengan device owner, diurutkan berdasarkan intensity (frekuensi komunikasi) tertinggi
- Untuk chat type "Group" atau "Broadcast", `person` akan menampilkan nama grup dari `group_name`
- Untuk chat type "One On One", `person` akan menampilkan nama kontak dari `from_name`
- Device owner tidak akan muncul dalam `intensity_list`

**Response (200 OK - No Devices Linked):**
```json
{
  "status": 200,
  "message": "No devices linked to this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Analysis by Investigator A"
    },
    "devices": [],
    "summary": null
  }
}
```

**Error Responses:**

**400 Bad Request (Wrong Analytic Method):**
```json
{
  "status": 400,
  "message": "This endpoint is only for Deep Communication Analytics. Current analytic method is 'Social Media Correlation'",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found (Analytic not found):**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**404 Not Found (Device not found in this analytic):**
```json
{
  "status": 404,
  "message": "Device not found in this analytic",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Internal server error: Failed to retrieve deep communication analytics",
  "data": null
}
```

---

### 2. Platform Cards Intensity

**Endpoint:** `GET /api/v1/analytic/platform-cards/intensity`

**Deskripsi:** Mendapatkan data intensity (frekuensi komunikasi) untuk platform tertentu dalam sebuah analytic. Endpoint ini hanya dapat digunakan untuk analytic dengan method **"Deep Communication Analytics"**. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses analytics untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic (harus memiliki method "Deep Communication Analytics") |
| `platform` | string | Yes | Platform name: `"Instagram"`, `"Telegram"`, `"WhatsApp"`, `"Facebook"`, `"X"`, `"TikTok"` (case-insensitive) |
| `device_id` | integer | No | Filter berdasarkan device ID. Jika tidak disediakan, akan mengambil data dari semua device yang terhubung dengan analytic |

**Response (200 OK - With Data):**
```json
{
  "status": 200,
  "message": "Platform cards intensity retrieved successfully",
  "data": {
    "analytic_id": 1,
    "platform": "Instagram",
    "device_id": null,
    "intensity_list": [
      {
        "person": "Jane Smith",
        "person_id": "+628987654321",
        "intensity": 75
      },
      {
        "person": "John Doe",
        "person_id": null,
        "intensity": 42
      }
    ],
    "summary": "Lorem Ipsum is simply dummy text..."
  }
}
```

**Response (200 OK - No Devices/No Data):**
```json
{
  "status": 200,
  "message": "Platform cards intensity retrieved successfully",
  "data": {
    "analytic_id": 1,
    "platform": "Instagram",
    "device_id": null,
    "intensity_list": [],
    "summary": "Lorem Ipsum is simply dummy text..."
  }
}
```

**Catatan:**
- `intensity_list` berisi daftar orang yang berkomunikasi dengan device owner, diurutkan berdasarkan intensity (frekuensi komunikasi) tertinggi
- `person_id` bisa berupa `null` jika tidak tersedia (hanya nama yang tersedia)
- `intensity` menunjukkan jumlah total pesan yang dipertukarkan dengan orang tersebut
- Device owner tidak akan muncul dalam `intensity_list`

**Error Responses:**

**400 Bad Request (Platform parameter is required):**
```json
{
  "status": 400,
  "message": "Platform parameter is required",
  "data": null
}
```

**400 Bad Request (Invalid platform):**
```json
{
  "status": 400,
  "message": "Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok",
  "data": null
}
```

**400 Bad Request (Wrong Analytic Method):**
```json
{
  "status": 400,
  "message": "This endpoint is only for Deep Communication Analytics. Current analytic method is 'Social Media Correlation'",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found (Analytic not found):**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**404 Not Found (Device not found in this analytic):**
```json
{
  "status": 404,
  "message": "Device not found in this analytic",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Internal server error: Failed to retrieve platform cards intensity",
  "data": null
}
```

---

### 3. Chat Detail

**Endpoint:** `GET /api/v1/analytic/chat-detail`

**Deskripsi:** Mendapatkan detail chat messages untuk person tertentu atau berdasarkan search text dalam sebuah analytic. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses analytics untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |
| `person_name` | string | No* | Nama person untuk filter chat (required jika `search` tidak disediakan) |
| `platform` | string | No | Platform name: `"Instagram"`, `"Telegram"`, `"WhatsApp"`, `"Facebook"`, `"X"`, `"TikTok"` |
| `device_id` | integer | No | Filter berdasarkan device ID |
| `search` | string | No* | Search text dalam messages (required jika `person_name` tidak disediakan) |

*Catatan: Minimal salah satu dari `person_name` atau `search` harus disediakan.

**Response (200 OK - With Messages):**
```json
{
  "status": 200,
  "message": "Chat detail retrieved successfully",
  "data": {
    "person_name": "Jane Smith",
    "person_id": "+628987654321",
    "platform": "Instagram",
    "intensity": 25,
    "chat_messages": [
      {
        "message_id": 1,
        "timestamp": "2025-12-12T10:30:00Z",
        "times": "10:30",
        "direction": "Incoming",
        "sender": "Jane Smith",
        "recipient": "John Doe",
        "sender_id": "+628987654321",
        "recipient_id": "+628123456789",
        "message_text": "Hello, how are you?",
        "message_type": "text",
        "platform": "Instagram",
        "thread_id": "thread_123",
        "chat_id": "chat_123"
      }
    ],
    "summary": null
  }
}
```

**Response (200 OK - No Devices Linked):**
```json
{
  "status": 200,
  "message": "No devices linked",
  "data": {
    "person_name": "Jane Smith",
    "platform": "Instagram",
    "chat_messages": []
  }
}
```

**Error Responses:**

**400 Bad Request (Missing person_name or search):**
```json
{
  "status": 400,
  "message": "Either person_name or search parameter must be provided",
  "data": null
}
```

**400 Bad Request (Platform parameter cannot be empty):**
```json
{
  "status": 400,
  "message": "Platform parameter cannot be empty",
  "data": null
}
```

**400 Bad Request (Invalid platform):**
```json
{
  "status": 400,
  "message": "Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found (Analytic not found):**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**404 Not Found (Device not found in this analytic):**
```json
{
  "status": 404,
  "message": "Device not found in this analytic",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Internal server error: Failed to retrieve chat detail",
  "data": null
}
```

---

### 2. Social Media Correlation

**Endpoint:** `GET /api/v1/analytics/social-media-correlation`

**Deskripsi:** Mendapatkan data social media correlation untuk sebuah analytic. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses analytics untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |
| `platform` | string | No | Filter platform: `"Instagram"`, `"Facebook"`, `"WhatsApp"`, `"TikTok"`, `"Telegram"`, `"X"` (default: `"Instagram"`) |

**Response (200 OK - With Data):**
```json
{
  "status": 200,
  "message": "Success analyzing social media correlation for 'Analysis by Investigator A'",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Analysis by Investigator A",
    "total_devices": 2,
    "devices": [
      {
        "device_id": 1,
        "owner_name": "John Doe",
        "phone_number": "+628123456789",
        "device_name": "John Doe Device",
        "created_at": "2025-12-12T10:30:00Z"
      }
    ],
    "correlations": {
      "Instagram": {
        "buckets": [
          {
            "label": "2 koneksi",
            "devices": [
              ["John Doe", "Jane Smith"]
            ]
          }
        ]
      }
    },
    "summary": null
  }
}
```

**Response (200 OK - No Data):**
```json
{
  "status": 200,
  "message": "No social media data found for platform 'instagram'",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Analysis by Investigator A",
    "total_devices": 2,
    "devices": [
      {
        "device_id": 1,
        "owner_name": "John Doe",
        "phone_number": "+628123456789",
        "device_name": "John Doe Device",
        "created_at": "2025-12-12T10:30:00Z"
      }
    ],
    "correlations": {
      "Instagram": {
        "buckets": []
      }
    },
    "summary": null
  }
}
```

**Error Responses:**

**400 Bad Request (Wrong method):**
```json
{
  "status": 400,
  "message": "This endpoint is only for Social Media Correlation. Current analytic method is '{method}'",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": {}
}
```

**404 Not Found (Analytic not found):**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": {}
}
```

**404 Not Found (No linked devices):**
```json
{
  "status": 404,
  "message": "No linked devices",
  "data": {}
}
```

**404 Not Found (Devices not found):**
```json
{
  "status": 404,
  "message": "Devices not found",
  "data": {}
}
```

**Catatan Format Error Response:**
- **400 Bad Request**: `"data": null`
- **401 Unauthorized**: `"data": null`
- **403 Forbidden**: `"data": {}` (empty object)
- **404 Not Found**: `"data": {}` (empty object) atau `"data": []` (empty array untuk beberapa endpoint yang mengembalikan list)
- **422 Unprocessable Entity**: `"data": null`
- **500 Internal Server Error**: `"data": null`

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to get social media correlation: <error_message>",
  "data": null
}
```

---

### 3. Hashfile Analytics

**Endpoint:** `GET /api/v1/analytics/hashfile-analytics`

**Deskripsi:** Mendapatkan data hashfile analytics untuk sebuah analytic. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses analytics untuk semua analytic.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |

**Response (200 OK - With Data):**
```json
{
  "status": 200,
  "message": "Hashfile correlation completed successfully",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "owner_name": "John Doe",
        "phone_number": "+628123456789"
      }
    ],
    "correlations": [
      {
        "hash_value": "abc123def456...",
        "file_name": "document.pdf",
        "file_type": "PDF",
        "devices": ["Device A", "Device B"]
      }
    ],
    "summary": null,
    "total_correlations": 1
  }
}
```

**Response (200 OK - No Hashfile Data):**
```json
{
  "status": 200,
  "message": "No hashfile data found",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "owner_name": "John Doe",
        "phone_number": "+628123456789"
      }
    ],
    "correlations": [],
    "summary": null,
    "total_correlations": 0
  }
}
```

**Error Responses:**

**400 Bad Request (Invalid analytic_id or wrong method):**
```json
{
  "status": 400,
  "message": "This endpoint is only for Hashfile Analytics. Current method: '{method}'",
  "data": null
}
```

**400 Bad Request (No devices linked):**
```json
{
  "status": 400,
  "message": "No devices linked to this analytic",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found (Analytic not found):**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**404 Not Found (No valid devices found):**
```json
{
  "status": 404,
  "message": "No valid devices found",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to get hashfile analytics: <error_message>",
  "data": null
}
```

---

### 4. APK Analytics

## Upload Apk
**Endpoint:** `POST /api/v1/analytics/upload-apk`

**Deskripsi:** Upload file APK atau IPA untuk dianalisis. Endpoint ini menginisialisasi proses upload dan mengembalikan `upload_id` yang dapat digunakan untuk memantau progress upload.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Request Body (form-data):**
| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `file` | file | Yes | File APK atau IPA yang akan di-upload |
| `file_name` | string | Yes | Nama file (wajib diisi, tidak boleh kosong) |

**Format File yang Diizinkan:**
- `apk` - Android Application Package
- `ipa` - iOS Application Package

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Upload initialized successfully",
  "data": {
    "file_id": null,
    "upload_id": "upload_1234567890_abc12345",
    "status_upload": "Pending",
    "upload_type": "apk"
  }
}
```

**Error Responses:**

**400 Bad Request (Invalid file type):**
```json
{
  "status": 400,
  "message": "Invalid file type. Only ['apk', 'ipa'] allowed.",
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

**422 Unprocessable Entity (Missing file_name):**
```json
{
  "status": 422,
  "message": "Field 'file_name' is required",
  "error_field": "file_name",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Upload error: <error_message>",
  "data": null
}
```

---


## Analyze Apk
**Endpoint:** `POST /api/v1/analytics/analyze-apk`

**Deskripsi:** Menganalisis file APK yang sudah di-upload. Endpoint ini melakukan analisis keamanan APK termasuk permission analysis dan malware scoring. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat menganalisis APK untuk semua analytic.
- **Regular User Role**: Hanya dapat menganalisis APK untuk analytic dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba menganalisis APK untuk analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `file_id` | integer | Yes | ID File APK yang sudah di-upload |
| `analytic_id` | integer | Yes | ID Analytic untuk menyimpan hasil analisis |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "analytic_name": "Analisis APK Aplikasi X",
    "method": "APK Analytics",
    "malware_scoring": "75",
    "permissions": [
      {
        "id": 1,
        "item": "android.permission.INTERNET",
        "status": "normal",
        "description": "Allows app to access the internet"
      },
      {
        "id": 2,
        "item": "android.permission.ACCESS_FINE_LOCATION",
        "status": "dangerous",
        "description": "Allows app to access precise location"
      }
    ]
  }
}
```

**Error Responses:**

**400 Bad Request (Invalid analysis result or file not supported):**
```json
{
  "status": 400,
  "message": "Invalid analysis result or file not supported",
  "data": null
}
```

**400 Bad Request (No permissions found):**
```json
{
  "status": 400,
  "message": "No permissions found in analysis result",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found (Analytic not found):**
```json
{
  "status": 404,
  "message": "Analytics Not Found",
  "data": null
}
```

**404 Not Found (File not found):**
```json
{
  "status": 404,
  "message": "File Not Found",
  "data": null
}
```

**404 Not Found (File not found with details):**
```json
{
  "status": 404,
  "message": "File not found: <error_details>",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Something went wrong, please try again later!",
  "data": null
}
```

---


## Apk Analytic
**Endpoint:** `GET /api/v1/analytics/apk-analytic`

**Deskripsi:** Mendapatkan hasil analisis APK untuk sebuah analytic. Endpoint ini mengembalikan data analisis APK termasuk malware scoring dan daftar permissions. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses hasil analisis APK untuk semua analytic.
- **Regular User Role**: Hanya dapat mengakses hasil analisis APK untuk analytic dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "analytic_name": "Analisis APK Aplikasi X",
    "method": "APK Analytics",
    "malware_scoring": "75",
    "permissions": [
      {
        "id": 1,
        "item": "android.permission.INTERNET",
        "status": "normal",
        "description": "Allows app to access the internet"
      }
    ]
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": {}
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "No APK analysis found for analytic_id={analytic_id}",
  "data": {}
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to get APK analysis: <error_message>",
  "data": null
}
```

---

### 5. Contact Correlation

**Endpoint:** `GET /api/v1/analytic/contact-correlation`

**Deskripsi:** Mendapatkan data contact correlation untuk sebuah analytic. Endpoint ini menganalisis kontak yang sama antara beberapa devices. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses contact correlation untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses contact correlation untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |

**Response (200 OK - With Correlations):**
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "devices": [
      {
        "device_id": 1,
        "device_label": "Device A",
        "owner_name": "John Doe",
        "phone_number": "+628123456789"
      }
    ],
    "correlations": [
      {
        "phone": "+628123456789",
        "devices": [1, 2],
        "device_labels": ["Device A", "Device B"]
      }
    ],
    "total_correlations": 1
  }
}
```

**Response (200 OK - No Devices Linked):**
```json
{
  "status": 200,
  "message": "No devices linked",
  "data": {
    "devices": [],
    "correlations": [],
    "total_correlations": 0
  }
}
```

**Error Responses:**

**400 Bad Request (Wrong method):**
```json
{
  "status": 400,
  "message": "This endpoint is only for Contact Correlation. Current analytic method is '{method}'",
  "data": null
}
```

**400 Bad Request (No devices linked):**
```json
{
  "status": 400,
  "message": "No devices linked to this analytic",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to get contact correlation: <error_message>",
  "data": null
}
```

---

## 📄 Analytics Report Management

### Base Path
`/api/v1/analytic`

### 1. Export Analytics Report to PDF

**Endpoint:** `GET /api/v1/analytic/export-pdf`

**Deskripsi:** Mengekspor laporan analytics ke format PDF. Endpoint ini dioptimalkan untuk dataset besar (jutaan record) dan menggunakan streaming/chunking untuk menghindari timeout dan masalah memori. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengekspor PDF untuk semua analytics.
- **Regular User Role**: Hanya dapat mengekspor PDF untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengekspor PDF untuk analytic lain akan mengembalikan 403 Forbidden.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |
| `person_name` | string | No | Nama person (jika method = Deep Communication Analytics) |
| `device_id` | integer | No | ID Device (jika method = Deep Communication Analytics) |
| `source` | string | No | Source/platform (jika method = Social Media Correlation atau Deep Communication Analytics) |

**Response (200 OK):**
Endpoint ini mengembalikan file PDF sebagai binary response dengan HTTP status code `200 OK` dan Content-Type `application/pdf`. File PDF akan di-download sebagai attachment dengan nama file sesuai dengan method analytics.

**Status Code:** `200 OK`

**Response Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="{filename}.pdf"
```

**Nama File (berdasarkan method analytics):**
- Contact Correlation: `contact_correlation_report_{analytic_id}_{timestamp}.pdf`
- APK Analytics: `apk_analytics_report_{analytic_id}_{timestamp}.pdf`
- Deep Communication Analytics: `communication_analytics_report_{analytic_id}_{timestamp}.pdf`
- Social Media Correlation: `social_media_analytics_report_{analytic_id}_{timestamp}.pdf`
- Hashfile Analytics: `hashfile_analytics_report_{analytic_id}_{timestamp}.pdf`

**Response Body:**
Response body berisi binary data PDF (bukan JSON). File akan otomatis di-download oleh browser/client.

**Format Timestamp:** `YYYYMMDD_HHMMSS` (contoh: `20251212_103000`)

**Contoh Response (200 OK):**
```
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="contact_correlation_report_1_20251212_103000.pdf"
Content-Length: 245678

[Binary PDF Data]
```

**Catatan Penting:**
- Status code: `200 OK` (success)
- Response body: Binary PDF file (bukan JSON)
- Content-Type: `application/pdf`
- File akan otomatis di-download dengan nama sesuai format di atas
- Untuk error cases (400, 401, 403, 404, 500), endpoint mengembalikan JSON response dengan format standar

**Struktur PDF untuk Social Media Correlation:**

PDF untuk Social Media Correlation memiliki struktur berikut:

1. **Header (Halaman 1):**
   - Logo CYBER SENTINEL di kiri atas
   - Waktu export di kanan atas: "Exported: DD/MM/YYYY HH:MM WIB"
   - Judul analytic (Arial Bold, 20px, warna #0d0d0d)
   - Method: "Method: Social Media Correlation" (kiri)
   - File Uploaded: "File Uploaded: DD/MM/YYYY" (kanan)
   - Informasi: Source, Total Device, Total Social Media Account

2. **Device Identification Summary:**
   - Subtitle dengan background #cccccc
   - Tabel dengan kolom: Device ID, Registered Owner, Phone Number
   - Format Device ID: "Device 1", "Device 2", dst.
   - Header tabel: background #466087, teks putih, align left dan middle
   - Data rows: align left dan top, font size 12px
   - Border: top dan bottom saja, warna #000408, tebal 1px

3. **Device Account Correlation:**
   - Subtitle dengan background #cccccc
   - Tabel dengan kolom: Connections, Involved Device, Correlated Account
   - **Format "Involved Device":** 
     - Format: "Device 1, 2, 3" (tanpa "Device" di setiap angka)
     - Device IDs diurutkan secara ascending
     - Contoh: "Device 2, 5" untuk 2 devices, "Device 1, 2, 3, 4, 5" untuk 5 devices
   - **Format "Correlated Account":**
     - Accounts ditampilkan dalam **single column** (lurus ke bawah)
     - Setiap account dengan bullet point: "• @account_name"
     - Nilai `null` ditampilkan sebagai "• unknown" (tanpa @ symbol)
     - Accounts diurutkan secara alphabetical
     - Multiple accounts untuk kombinasi device yang sama dikelompokkan dalam satu row
   - **Grouping Logic:**
     - Data dikelompokkan berdasarkan kombinasi unique dari (Connections count, Involved Device IDs)
     - Setiap kombinasi unique menjadi satu row
     - Semua accounts untuk kombinasi yang sama ditampilkan dalam satu cell "Correlated Account"
   - Header tabel: background #466087, teks putih, align left dan middle
   - Data rows: align left dan top, font size 12px
   - Border: top dan bottom saja, warna #000408, tebal 1px
   - Header tabel diulang di setiap halaman (repeatRows=1)

4. **Summary Section:**
   - Background #F5F5F5, border 1px hitam
   - Judul "Summary" bold, 12px, hitam, left-aligned
   - Konten sebagai bullet points (•), 11px, normal Helvetica, hitam, justified

5. **Footer:**
   - Garis horizontal warna #466086, tebal 1.5px, lebar 545px
   - Teks "Page X of Y" dengan font size 10px, warna #333333

6. **Header Halaman 2+:**
   - Logo dan waktu export dalam satu grid
   - Judul analytic, Method, dan File Uploaded
   - Header tidak overlap dengan konten (topMargin disesuaikan)

**Error Responses:**

**400 Bad Request (No devices linked):**
```json
{
  "status": 400,
  "message": "No devices linked to this analytic",
  "data": null
}
```

**400 Bad Request (Invalid method):**
```json
{
  "status": 400,
  "message": "Unsupported method for PDF export: '{method}'",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to generate PDF: <error_message>",
  "data": null
}
```

---

### 2. Save Analytic Summary

**Endpoint:** `POST /api/v1/analytic/save-summary`

**Deskripsi:** Menyimpan summary untuk sebuah analytic. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat menyimpan summary untuk semua analytics.
- **Regular User Role**: Hanya dapat menyimpan summary untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba menyimpan summary untuk analytic lain akan mengembalikan 403 Forbidden.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |

**Request Body:**
```json
{
  "summary": "Analisis menunjukkan adanya korelasi antara beberapa devices melalui kontak yang sama."
}
```

**Request Body Fields:**
| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `summary` | string | Yes | Teks summary untuk analytic (tidak boleh kosong) |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Summary saved successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Analisis Kontak",
    "summary": "Analisis menunjukkan adanya korelasi antara beberapa devices melalui kontak yang sama.",
    "updated_at": "2025-12-12T10:30:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request (Empty summary):**
```json
{
  "status": 400,
  "message": "Summary cannot be empty",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to save summary: <error_message>",
  "data": null
}
```

---

### 3. Edit Analytic Summary

**Endpoint:** `PUT /api/v1/analytic/edit-summary`

**Deskripsi:** Mengedit summary untuk sebuah analytic. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengedit summary untuk semua analytics.
- **Regular User Role**: Hanya dapat mengedit summary untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengedit summary untuk analytic lain akan mengembalikan 403 Forbidden.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |

**Request Body:**
```json
{
  "summary": "Summary yang telah diupdate dengan informasi tambahan."
}
```

**Request Body Fields:**
| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `summary` | string | Yes | Teks summary yang telah diupdate (tidak boleh kosong) |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Summary updated successfully",
  "data": {
    "analytic_id": 1,
    "analytic_name": "Analisis Kontak",
    "summary": "Summary yang telah diupdate dengan informasi tambahan.",
    "updated_at": "2025-12-12T10:35:00Z"
  }
}
```

**Error Responses:**

**400 Bad Request (Empty summary):**
```json
{
  "status": 400,
  "message": "Summary cannot be empty",
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

**403 Forbidden:**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to edit summary: <error_message>",
  "data": null
}
```

---

## 🔒 Role-Based Access Control (RBAC)

### Overview
API Analytics Management mengimplementasikan Role-Based Access Control (RBAC) untuk membatasi akses data berdasarkan role user. Sistem ini dirancang untuk memastikan bahwa setiap user hanya dapat mengakses data yang relevan dengan mereka.

### Bagaimana Access Control Bekerja?

**1. Role vs Tag - Perbedaan Penting:**

| Konsep | Fungsi | Penggunaan |
|--------|--------|------------|
| **Role** | Menentukan level akses data | Digunakan untuk **access control** - menentukan apakah user dapat melihat semua data atau hanya data sendiri |
| **Tag** | Kategori/jabatan user | Digunakan untuk **display** dan **mapping ke role** saat create user, **TIDAK digunakan untuk filtering data** |

**2. Mapping Tag ke Role:**

Saat membuat user baru, tag otomatis di-mapping ke role:

| Tag User | Role yang Dihasilkan | Akses Data |
|----------|----------------------|------------|
| `"Admin"` | `admin` | ✅ Akses semua data di sistem |
| `"Investigator"` | `user` | ⚠️ Hanya data sendiri |
| `"Ahli Forensic"` | `user` | ⚠️ Hanya data sendiri |
| Tag lainnya | `user` (default) | ⚠️ Hanya data sendiri |

**3. Mekanisme Filtering Data:**

Filtering data **TIDAK menggunakan tag**, melainkan menggunakan **fullname** dan **email** user:

- **Admin Role**: Tidak ada filtering, melihat semua data
- **User Role**: Filtering berdasarkan matching text:
  - `user.fullname` atau `user.email` harus ada di field tertentu (case-insensitive)
  - Contoh: Jika user memiliki `fullname = "John Doe"` dan `email = "john@example.com"`, maka user hanya melihat data dimana field tertentu mengandung "John Doe" atau "john@example.com"

### Roles

| Role | Deskripsi | Tingkat Akses |
|------|-----------|---------------|
| `admin` | Administrator | Akses penuh ke semua analytics, files, dan devices |
| `user` | User biasa | Akses terbatas (hanya analytics sendiri) |

### Contoh Praktis

**Scenario 1: User dengan Role Admin**
```
User: {
  fullname: "Admin User",
  email: "admin@example.com",
  tag: "Admin",
  role: "admin"
}

Hasil: ✅ Melihat SEMUA analytics, files, dan devices di sistem
```

**Scenario 2: User dengan Role User (Tag: Investigator)**
```
User: {
  fullname: "Investigator A",
  email: "investigator@example.com",
  tag: "Investigator",
  role: "user"
}

Analytic 1: {
  analytic_name: "Analysis by Investigator A",
  summary: "Communication analysis for case XYZ",
  created_by: "Created by: Investigator A (investigator@example.com)"
}
→ ✅ DAPAT DILIHAT (karena fullname/email match di created_by)

Analytic 2: {
  analytic_name: "Analysis by Investigator B",
  summary: "Communication analysis for case ABC",
  created_by: "Created by: Investigator B (investigator2@example.com)"
}
→ ❌ TIDAK DAPAT DILIHAT (karena tidak match dengan fullname/email user)
```

**Scenario 3: User dengan Role User (Tag: Ahli Forensic)**
```
User: {
  fullname: "Ahli Forensic X",
  email: "forensic@example.com",
  tag: "Ahli Forensic",
  role: "user"
}

File 1: {
  file_name: "data_forensic_x.xlsx",
  notes: "Uploaded by Ahli Forensic X"
}
→ ✅ DAPAT DILIHAT (karena fullname/email match di notes)

File 2: {
  file_name: "data_forensic_y.xlsx",
  notes: "Uploaded by Ahli Forensic Y"
}
→ ❌ TIDAK DAPAT DILIHAT (karena tidak match)
```

**Poin Penting:**
- Tag `"Investigator"` dan `"Ahli Forensic"` **keduanya menghasilkan role `"user"`**
- Keduanya memiliki **level akses yang sama** (hanya data sendiri)
- Perbedaan tag hanya untuk **tujuan display/organisasi**, bukan untuk access control
- Filtering dilakukan berdasarkan **fullname/email matching**, bukan berdasarkan tag

### Alur Access Control (Flow Diagram)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER LOGIN                               │
│  { fullname, email, tag, role }                            │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Cek Role User        │
         └───────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
   ┌─────────┐      ┌──────────┐
   │ admin   │      │  user    │
   └────┬────┘      └────┬─────┘
        │                │
        │                ▼
        │      ┌─────────────────────┐
        │      │ Filtering Data      │
        │      │ Berdasarkan:        │
        │      │ - fullname          │
        │      │ - email             │
        │      │                     │
        │      │ Matching dengan:   │
        │      │ - analytic_name     │
        │      │ - summary           │
        │      │ - created_by        │
        │      │ - file notes        │
        │      │ - file_name         │
        │      └─────────────────────┘
        │
        ▼
┌──────────────────┐
│  Akses Semua     │
│  Data (No Filter)│
└──────────────────┘
```

### Ringkasan

| Aspek | Penjelasan |
|-------|------------|
| **Akses Control Berdasarkan** | **Role** (admin/user), bukan Tag |
| **Tag Digunakan Untuk** | Display dan mapping ke role saat create user |
| **Filtering Data Menggunakan** | **Fullname** dan **Email** user (text matching) |
| **Admin Role** | Melihat semua data tanpa filtering |
| **User Role** | Hanya melihat data dimana fullname/email match dengan field tertentu |
| **Tag "Investigator" vs "Ahli Forensic"** | Keduanya menghasilkan role "user" dengan akses yang sama |

### Aturan Akses

#### File Management

**Upload Data (`POST /api/v1/analytics/upload-data`):**
- Informasi user (fullname dan email) **otomatis disimpan** ke field `created_by` yang terpisah dalam format `"Created by: {fullname} ({email})"` untuk keperluan access control.
- Field `notes` tetap berisi notes yang diinput user tanpa modifikasi.
- Field `created_by` digunakan oleh sistem untuk filtering akses file berdasarkan user.

**Get Files (`GET /api/v1/analytics/get-files`):**
- **Admin:** Melihat semua file di database
- **User:** Hanya melihat file dimana `created_by`, `notes`, atau `file_name` mengandung `fullname` atau `email` mereka (case-insensitive matching)
- Sistem melakukan filtering berdasarkan pencarian substring di field `created_by`, `notes`, dan `file_name`
- File yang di-upload sebelum implementasi fitur ini (tidak memiliki informasi user di `created_by`) tidak akan muncul untuk user non-admin karena tidak memiliki informasi ownership

#### Analytics Management

**Semua Endpoint Analytics:**
- **Admin Role**: Dapat mengakses, melihat, membuat, dan mengelola semua analytics.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka (case-insensitive matching). Mencoba mengakses analytics lain akan mengembalikan 403 Forbidden.

**Catatan Penting:**
- Saat membuat analytic baru melalui `POST /api/v1/analytics/start-analyzing`, informasi user (fullname dan email) **otomatis disimpan** ke field `created_by` dalam format `"Created by: {fullname} ({email})"`.
- Field `created_by` digunakan khusus untuk menyimpan informasi creator dan digunakan untuk filtering akses.
- Field `summary` tetap terpisah dan dapat digunakan untuk menyimpan ringkasan analisis yang sebenarnya.
- Informasi ini memastikan bahwa user non-admin dapat melihat analytics yang mereka buat sendiri di daftar.
- Untuk analytics yang dibuat sebelum update ini (dengan `created_by` null), user non-admin tidak akan melihatnya kecuali `analytic_name` atau `summary` mengandung fullname atau email mereka.

**Endpoint yang Terpengaruh:**
- `POST /api/v1/analytics/start-analyzing` - Membuat analytic baru (memerlukan authentication, otomatis menyimpan informasi user ke created_by)
- `GET /api/v1/analytics/get-all-analytic` - Daftar terfilter berdasarkan role
- `POST /api/v1/analytics/start-extraction` - Pengecekan akses sebelum memulai ekstraksi
- `GET /api/v1/analytics/get-devices` - Pengecekan akses sebelum mengembalikan devices
- `GET /api/v1/analytic/deep-communication-analytics` - Pengecekan akses sebelum mengembalikan data
- `GET /api/v1/analytic/platform-cards/intensity` - Pengecekan akses sebelum mengembalikan data
- `GET /api/v1/analytic/chat-detail` - Pengecekan akses sebelum mengembalikan data
- `GET /api/v1/analytics/social-media-correlation` - Pengecekan akses sebelum mengembalikan data
- `GET /api/v1/analytics/hashfile-analytics` - Pengecekan akses sebelum mengembalikan data
- `GET /api/v1/analytic/contact-correlation` - Pengecekan akses sebelum mengembalikan data
- `POST /api/v1/analytics/analyze-apk` - Pengecekan akses sebelum menganalisis APK
- `GET /api/v1/analytics/apk-analytic` - Pengecekan akses sebelum mengembalikan hasil analisis APK

#### APK Analytics

**Semua Endpoint APK Analytics:**
- **Admin Role**: Dapat mengupload, menganalisis, dan melihat hasil analisis APK untuk semua analytics.
- **Regular User Role**: Hanya dapat mengupload, menganalisis, dan melihat hasil analisis APK untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytics lain akan mengembalikan 403 Forbidden.

**Endpoint yang Terpengaruh:**
- `POST /api/v1/analytics/upload-apk` - Upload file APK/IPA (semua user dapat upload, tetapi hanya melihat hasil analisis mereka sendiri)
- `POST /api/v1/analytics/analyze-apk` - Analisis APK (pengecekan akses sebelum menganalisis)
- `GET /api/v1/analytics/apk-analytic` - Mendapatkan hasil analisis APK (pengecekan akses sebelum mengembalikan data)

#### Analytics Report Management

**Semua Endpoint Analytics Report:**
- **Admin Role**: Dapat mengekspor PDF, menyimpan, dan mengedit summary untuk semua analytics.
- **Regular User Role**: Hanya dapat mengekspor PDF, menyimpan, dan mengedit summary untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytics lain akan mengembalikan 403 Forbidden.

**Endpoint yang Terpengaruh:**
- `GET /api/v1/analytic/export-pdf` - Ekspor PDF (pengecekan akses sebelum mengekspor)
- `POST /api/v1/analytic/save-summary` - Simpan summary (pengecekan akses sebelum menyimpan)
- `PUT /api/v1/analytic/edit-summary` - Edit summary (pengecekan akses sebelum mengedit)

### Catatan Penting

1. **Kriteria Matching:** Filtering role user menggunakan case-insensitive matching:
   - Untuk Analytics: `Analytic.analytic_name`, `Analytic.summary`, atau `Analytic.created_by` mengandung `User.fullname` atau `User.email`
   - Untuk Files: `File.notes` atau `File.file_name` mengandung `User.fullname` atau `User.email`
   - Partial matching (contoh: "Investigator A" cocok dengan "investigator.a@example.com")
   - Matching dilakukan menggunakan operator SQL `ILIKE` untuk fleksibilitas

2. **Admin Bypass:** User admin melewati semua filter dan melihat semua data

3. **Error 403 Forbidden:** User biasa yang mencoba mengakses analytics dari user lain akan menerima:
   ```json
   {
     "status": 403,
     "message": "You do not have permission to access this analytic",
     "data": null
   }
   ```

4. **Kepemilikan Data:** 
   - Analytics: Kepemilikan ditentukan oleh text matching di field `analytic_name`, `summary`, atau `created_by`. Field `created_by` otomatis diisi saat membuat analytic baru dengan format `"Created by: {fullname} ({email})"`.
   - Files: Kepemilikan ditentukan oleh text matching di field `file_name` atau `notes`.
   - Untuk filtering yang lebih akurat, field `created_by` sudah ditambahkan ke model `Analytic` dan otomatis diisi saat membuat analytic baru.

---

## 🚨 Error Responses

### Format Error Standar
Semua error response mengikuti struktur ini:

```json
{
  "status": <http_status_code>,
  "message": "<error_message>",
  "data": null
}
```

### HTTP Status Codes Umum

| Status Code | Deskripsi | Contoh |
|-------------|-----------|--------|
| `200` | Success | Request berhasil diselesaikan |
| `400` | Bad Request | Parameter request tidak valid |
| `401` | Unauthorized | Token autentikasi tidak ada atau tidak valid |
| `403` | Forbidden | Tidak memiliki permission (RBAC) |
| `404` | Not Found | Resource tidak ditemukan |
| `500` | Internal Server Error | Error server yang tidak terduga |

### Contoh Error Response

**401 Unauthorized:**
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

**403 Forbidden (Akses Ditolak):**
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Analytic not found",
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

## 📝 Catatan Tambahan

### Filtering Data

Sistem menggunakan text-based filtering untuk menentukan kepemilikan data:
- **Analytics**: Difilter berdasarkan `analytic_name`, `summary`, atau `created_by` yang mengandung fullname atau email user. Field `created_by` otomatis diisi saat membuat analytic baru dengan format `"Created by: {fullname} ({email})"`.
- **Files**: Difilter berdasarkan `file_name` atau `notes` yang mengandung fullname atau email user

**Catatan:** Field `created_by` sudah ditambahkan ke model `Analytic` dan otomatis diisi saat membuat analytic baru, sehingga filtering lebih akurat dan konsisten.

### Best Practices

1. **Field created_by:** Field `created_by` otomatis diisi saat membuat analytic baru, sehingga tidak perlu menambahkan identifier user secara manual di `analytic_name` atau `summary`.
2. **Field summary:** Gunakan field `summary` untuk menyimpan ringkasan analisis yang sebenarnya, bukan untuk informasi creator.
3. **File Notes:** Saat mengupload files, sertakan identifier user di field `notes` untuk filtering yang tepat
4. **Akses Admin:** User admin selalu dapat mengakses semua data terlepas dari kepemilikan

