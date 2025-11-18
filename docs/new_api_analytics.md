# API Contract Documentation - Analytics Endpoints
## Digital Forensics Analysis Platform - Backend API

**Version:** 2.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**API Version:** `/api/v1`  
**Last Updated:** December 2024

---

## 📋 Daftar Isi

1. [Authentication](#authentication)
2. [Overview](#overview)
3. [Method Validation](#method-validation)
4. [Analytics Endpoints](#analytics-endpoints)
   - [Deep Communication Analytics](#1-deep-communication-analytics)
   - [Social Media Correlation](#2-social-media-correlation)
   - [Hashfile Analytics](#3-hashfile-analytics)
   - [APK Analytics](#4-apk-analytics)
   - [Contact Correlation](#5-contact-correlation)
5. [Role-Based Access Control](#role-based-access-control)
6. [Error Responses](#error-responses)

---

## 🔐 Authentication

### Overview
Semua endpoint yang dilindungi memerlukan Bearer Token authentication. Token diperoleh dari endpoint login:
- **Access Token**: Valid selama 24 jam (1440 menit). Digunakan untuk autentikasi API.
- **Refresh Token**: Valid selama 7 hari. Digunakan untuk mendapatkan access token baru ketika expired.

### Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

### Login
**Endpoint:** `POST /api/v1/auth/login`

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

---

## 📊 Overview

Dokumentasi ini mencakup semua endpoint analytics dengan **validasi method yang ketat**. Setiap endpoint hanya dapat diakses jika method analytics sesuai dengan endpoint yang dipanggil.

### Supported Methods
1. **Deep Communication Analytics** - Analisis komunikasi mendalam dari berbagai platform
2. **Social Media Correlation** - Korelasi data media sosial antar device
3. **Hashfile Analytics** - Analisis hash file untuk menemukan file duplikat
4. **APK Analytics** - Analisis keamanan aplikasi Android/iOS
5. **Contact Correlation** - Korelasi kontak antar device

---

## ⚠️ Method Validation

### Penting: Validasi Method
**Semua endpoint analytics sekarang memiliki validasi method yang ketat.** Endpoint hanya akan mengembalikan data jika method analytics sesuai dengan endpoint yang dipanggil.

### Alur Validasi
1. ✅ **Cek Analytic Exists** - Memastikan analytic dengan ID yang diberikan ada
2. ✅ **Cek User Access** - Memastikan user memiliki akses ke analytic tersebut
3. ✅ **Cek Method Match** - **Memastikan method analytics sesuai dengan endpoint**

### Error Response untuk Method Mismatch
Jika method analytics tidak sesuai dengan endpoint, akan mengembalikan error **400 Bad Request**:

```json
{
  "status": 400,
  "message": "This endpoint is only for [Method Name]. Current analytic method is '[actual_method]'",
  "data": null
}
```

### Contoh Skenario
- ❌ **SALAH**: Memanggil `/api/v1/analytic/deep-communication-analytics?analytic_id=1` untuk analytic dengan method `"Social Media Correlation"`
- ✅ **BENAR**: Memanggil `/api/v1/analytics/social-media-correlation?analytic_id=1` untuk analytic dengan method `"Social Media Correlation"`

---

## 📊 Analytics Endpoints

### Base Path
`/api/v1/analytics` or `/api/v1/analytic`

---

### 1. Deep Communication Analytics

**Endpoint:** `GET /api/v1/analytic/deep-communication-analytics`

**Deskripsi:** Mendapatkan data deep communication analytics untuk sebuah analytic. Endpoint ini menganalisis komunikasi dari berbagai platform (Instagram, Telegram, WhatsApp, Facebook, X, TikTok) dan menghitung intensity komunikasi dengan setiap kontak.

**⚠️ Method Validation:** Endpoint ini **hanya** dapat diakses untuk analytic dengan method `"Deep Communication Analytics"`.

**Kontrol Akses:**
- **Admin Role**: Dapat mengakses analytics untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka.

**Headers:** `Authorization: Bearer <access_token>`

**Query Parameters:**
| Parameter | Type | Required | Deskripsi |
|-----------|------|----------|-----------|
| `analytic_id` | integer | Yes | ID Analytic |
| `device_id` | integer | No | Filter berdasarkan device ID |

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
              }
            ]
          },
          {
            "platform": "Telegram",
            "platform_key": "telegram",
            "has_data": false,
            "message_count": 0,
            "person": null,
            "intensity": 0
          }
        ]
      }
    ],
    "summary": "Lorem Ipsum is simply dummy text..."
  }
}
```

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

**400 Bad Request (Method Mismatch):**
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

### 2. Social Media Correlation

**Endpoint:** `GET /api/v1/analytics/social-media-correlation`

**Deskripsi:** Mendapatkan data social media correlation untuk sebuah analytic. Endpoint ini menganalisis korelasi akun media sosial antar device dan mengelompokkan device berdasarkan jumlah koneksi.

**⚠️ Method Validation:** Endpoint ini **hanya** dapat diakses untuk analytic dengan method `"Social Media Correlation"`.

**Kontrol Akses:**
- **Admin Role**: Dapat mengakses analytics untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka.

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
    "devices": [],
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

**400 Bad Request (Method Mismatch):**
```json
{
  "status": 400,
  "message": "This endpoint is only for Social Media Correlation. Current analytic method is 'Deep Communication Analytics'",
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

**Deskripsi:** Mendapatkan data hashfile analytics untuk sebuah analytic. Endpoint ini menganalisis hash file untuk menemukan file duplikat atau file yang sama di berbagai device.

**⚠️ Method Validation:** Endpoint ini **hanya** dapat diakses untuk analytic dengan method `"Hashfile Analytics"`.

**Kontrol Akses:**
- **Admin Role**: Dapat mengakses analytics untuk semua analytic.
- **Regular User Role**: Hanya dapat mengakses analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka.

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

**400 Bad Request (Method Mismatch):**
```json
{
  "status": 400,
  "message": "This endpoint is only for Hashfile Analytics. Current method: 'Contact Correlation'",
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

#### 4.1. Upload APK

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

**422 Unprocessable Entity (Missing file_name):**
```json
{
  "status": 422,
  "message": "Field 'file_name' is required",
  "error_field": "file_name",
  "data": null
}
```

---

#### 4.2. Analyze APK

**Endpoint:** `POST /api/v1/analytics/analyze-apk`

**Deskripsi:** Menganalisis file APK yang sudah di-upload. Endpoint ini melakukan analisis keamanan APK termasuk permission analysis dan malware scoring.

**⚠️ Method Validation:** Endpoint ini **hanya** dapat diakses untuk analytic dengan method `"APK Analytics"`.

**Kontrol Akses:**
- **Admin Role**: Dapat menganalisis APK untuk semua analytic.
- **Regular User Role**: Hanya dapat menganalisis APK untuk analytic dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka.

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

**400 Bad Request (Method Mismatch):**
```json
{
  "status": 400,
  "message": "This endpoint is only for APK Analytics. Current analytic method is 'Social Media Correlation'",
  "data": null
}
```

**400 Bad Request (Invalid analysis result):**
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

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Something went wrong, please try again later!",
  "data": null
}
```

---

#### 4.3. Get APK Analysis

**Endpoint:** `GET /api/v1/analytics/apk-analytic`

**Deskripsi:** Mendapatkan hasil analisis APK untuk sebuah analytic. Endpoint ini mengembalikan data analisis APK termasuk malware scoring dan daftar permissions.

**⚠️ Method Validation:** Endpoint ini **hanya** dapat diakses untuk analytic dengan method `"APK Analytics"`.

**Kontrol Akses:**
- **Admin Role**: Dapat mengakses hasil analisis APK untuk semua analytic.
- **Regular User Role**: Hanya dapat mengakses hasil analisis APK untuk analytic dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka.

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

**Response (404 Not Found - No APK analysis):**
```json
{
  "status": 404,
  "message": "No APK analysis found for analytic_id=1",
  "data": {}
}
```

**Error Responses:**

**400 Bad Request (Method Mismatch):**
```json
{
  "status": 400,
  "message": "This endpoint is only for APK Analytics. Current analytic method is 'Hashfile Analytics'",
  "data": {}
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

---

### 5. Contact Correlation

**Endpoint:** `GET /api/v1/analytic/contact-correlation`

**Deskripsi:** Mendapatkan data contact correlation untuk sebuah analytic. Endpoint ini menganalisis kontak yang sama antara beberapa devices.

**⚠️ Method Validation:** Endpoint ini **hanya** dapat diakses untuk analytic dengan method `"Contact Correlation"`.

**Kontrol Akses:**
- **Admin Role**: Dapat mengakses contact correlation untuk semua analytics.
- **Regular User Role**: Hanya dapat mengakses contact correlation untuk analytics dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka.

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

**400 Bad Request (Method Mismatch):**
```json
{
  "status": 400,
  "message": "This endpoint is only for Contact Correlation. Current analytic method is 'Deep Communication Analytics'",
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

## 🔒 Role-Based Access Control

### Admin Role
- ✅ Dapat mengakses semua analytics
- ✅ Dapat membuat, mengedit, dan menghapus analytics
- ✅ Tidak ada batasan akses

### Regular User Role
- ✅ Hanya dapat mengakses analytics dimana:
  - `analytic_name` mengandung `fullname` atau `email` mereka, ATAU
  - `summary` mengandung `fullname` atau `email` mereka, ATAU
  - `created_by` mengandung `fullname` atau `email` mereka
- ❌ Mencoba mengakses analytic lain akan mengembalikan **403 Forbidden**

### Contoh Pengecekan Akses
```python
# User: "John Doe" (john.doe@example.com)
# Analytic 1: analytic_name = "Analysis by John Doe" → ✅ BISA AKSES
# Analytic 2: created_by = "Created by: John Doe (john.doe@example.com)" → ✅ BISA AKSES
# Analytic 3: analytic_name = "Analysis by Jane Smith" → ❌ TIDAK BISA AKSES (403 Forbidden)
```

---

## ❌ Error Responses

### Standard Error Response Format

Semua error response mengikuti format standar:

```json
{
  "status": <http_status_code>,
  "message": "<error_message>",
  "data": <null | {} | []>
}
```

### HTTP Status Codes

| Status Code | Deskripsi | Data Format |
|-------------|-----------|-------------|
| **400** | Bad Request (Method mismatch, invalid parameters) | `null` |
| **401** | Unauthorized (Invalid or missing token) | `null` |
| **403** | Forbidden (No permission to access) | `null` atau `{}` |
| **404** | Not Found (Resource not found) | `null` atau `{}` |
| **422** | Unprocessable Entity (Validation error) | `null` |
| **500** | Internal Server Error | `null` |

### Common Error Messages

#### 400 Bad Request - Method Mismatch
```json
{
  "status": 400,
  "message": "This endpoint is only for [Method Name]. Current analytic method is '[actual_method]'",
  "data": null
}
```

#### 401 Unauthorized
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

#### 403 Forbidden
```json
{
  "status": 403,
  "message": "You do not have permission to access this analytic",
  "data": null
}
```

#### 404 Not Found
```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

#### 500 Internal Server Error
```json
{
  "status": 500,
  "message": "Internal server error: <error_details>",
  "data": null
}
```

---

## 📝 Catatan Penting

### Method Validation
1. **Setiap endpoint hanya menerima method yang sesuai**
2. **Validasi dilakukan setelah pengecekan akses user**
3. **Error 400 akan dikembalikan jika method tidak sesuai**

### Best Practices
1. ✅ **Selalu cek method analytic sebelum memanggil endpoint**
2. ✅ **Gunakan endpoint yang sesuai dengan method analytic**
3. ✅ **Handle error 400 dengan pesan yang jelas ke user**
4. ✅ **Pastikan token valid sebelum memanggil endpoint**

### Testing
Saat testing, pastikan untuk:
1. Test dengan method yang sesuai → harus return 200 OK
2. Test dengan method yang tidak sesuai → harus return 400 Bad Request
3. Test dengan analytic yang tidak ada → harus return 404 Not Found
4. Test dengan user yang tidak memiliki akses → harus return 403 Forbidden

---

## 📚 Referensi

- **Base Documentation**: `docs/api_contract_analytics_management.md`
- **Cases Management API**: `docs/api_contract_cases_management.md`
- **API Version**: v1.0.0
- **Last Updated**: December 2024

---

**End of Documentation**

