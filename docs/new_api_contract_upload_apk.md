# API Contract: APK Analytics

## Endpoint
`GET /api/v1/analytics/apk-analytic`

## Description
Mendapatkan hasil analisis APK untuk sebuah analytic. Endpoint ini mengembalikan data analisis APK termasuk malware scoring dan daftar permissions. **Kontrol akses berdasarkan role user:**
- **Admin Role**: Dapat mengakses hasil analisis APK untuk semua analytic.
- **Regular User Role**: Hanya dapat mengakses hasil analisis APK untuk analytic dimana `analytic_name`, `summary`, atau `created_by` mengandung `fullname` atau `email` mereka. Mencoba mengakses analytic lain akan mengembalikan 403 Forbidden.

## Authentication
Required - Bearer Token

## Headers
```
Authorization: Bearer <access_token>
```

## Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | integer | Yes | ID Analytic yang ingin diambil hasil analisis APK-nya |

## Response Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success - Data analisis APK berhasil diambil |
| 400 | Bad Request - Analytic method bukan APK Analytics |
| 403 | Forbidden - User tidak memiliki permission untuk mengakses analytic ini |
| 404 | Not Found - Analytic tidak ditemukan atau tidak ada APK analysis |

## Response Body Structure

### Success Response (200 OK)

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
                "item": "android.permission.READ_EXTERNAL_STORAGE",
                "status": "dangerous",
                "description": "Allows app to read from external storage"
            }
        ],
        "summary": "Summary of the APK analysis"
    }
}
```

## Error Handling

### 1. Analytic Not Found (404)

**Kondisi:** Analytic dengan ID yang diberikan tidak ditemukan dalam database.

**Response:**
- Status Code: `404`
- Message: `"Analytic not found"`
- Data: `{}`

**Contoh:**
```json
{
    "status": 404,
    "message": "Analytic not found",
    "data": {}
}
```

### 2. Permission Denied (403)

**Kondisi:** User tidak memiliki permission untuk mengakses analytic ini. Hanya admin atau user yang memiliki analytic (berdasarkan `analytic_name`, `summary`, atau `created_by`) yang dapat mengakses.

**Response:**
- Status Code: `403`
- Message: `"You do not have permission to access this analytic"`
- Data: `{}`

**Contoh:**
```json
{
    "status": 403,
    "message": "You do not have permission to access this analytic",
    "data": {}
}
```

### 3. Wrong Analytic Method (400)

**Kondisi:** Analytic yang diberikan bukan untuk APK Analytics. Method analytic tidak sesuai dengan endpoint ini.

**Response:**
- Status Code: `400`
- Message: `"This endpoint is only for APK Analytics. Current analytic method is '{method_value}'"`
- Data: `{}`

**Contoh:**
```json
{
    "status": 400,
    "message": "This endpoint is only for APK Analytics. Current analytic method is 'Deep Communication Analytics'",
    "data": {}
}
```

### 4. No APK Analysis Found - No Files Uploaded (404)

**Kondisi:** Tidak ada APK analysis untuk analytic_id yang diberikan, dan tidak ada file yang sudah di-upload untuk analytic ini. User perlu mengupload APK file terlebih dahulu.

**Response:**
- Status Code: `404`
- Message: `"No APK analysis found for analytic_id={analytic_id}. Please upload an APK file first."`
- Data:
  - `analytic_info`: Informasi tentang analytic
  - `next_action`: `"upload_apk"`
  - `redirect_to`: `"/analytics/upload-apk"`
  - `instruction`: Instruksi untuk user

**Contoh:**
```json
{
    "status": 404,
    "message": "No APK analysis found for analytic_id=44. Please upload an APK file first.",
    "data": {
        "analytic_info": {
            "analytic_id": 44,
            "analytic_name": "APK Analysis Test",
            "method": "APK Analytics"
        },
        "next_action": "upload_apk",
        "redirect_to": "/analytics/upload-apk",
        "instruction": "Please upload an APK file to analyze. After uploading, you can analyze the APK file."
    }
}
```

**Frontend Handling:**
- Frontend harus mengecek `next_action` dan `redirect_to` dalam response
- Jika `next_action` adalah `"upload_apk"`, redirect user ke halaman upload APK (`/analytics/upload-apk`)
- Tampilkan `instruction` sebagai pesan informatif kepada user

### 5. No APK Analysis Found - Files Exist But Not Analyzed (404)

**Kondisi:** Tidak ada APK analysis untuk analytic_id yang diberikan, tetapi sudah ada file yang di-upload untuk analytic ini. User perlu menganalisis file APK yang sudah di-upload.

**Response:**
- Status Code: `404`
- Message: `"No APK analysis found for analytic_id={analytic_id}. Please analyze the uploaded APK file."`
- Data:
  - `analytic_info`: Informasi tentang analytic
  - `file_info`: Informasi tentang file yang sudah di-upload
  - `next_action`: `"analyze_apk"`
  - `redirect_to`: `"/analytics/analyze-apk"`
  - `instruction`: Instruksi untuk user

**Contoh:**
```json
{
    "status": 404,
    "message": "No APK analysis found for analytic_id=44. Please analyze the uploaded APK file.",
    "data": {
        "analytic_info": {
            "analytic_id": 44,
            "analytic_name": "APK Analysis Test",
            "method": "APK Analytics"
        },
        "file_info": {
            "file_count": 2,
            "file_ids": [101, 102]
        },
        "next_action": "analyze_apk",
        "redirect_to": "/analytics/analyze-apk",
        "instruction": "Please analyze the uploaded APK file to view the analysis results."
    }
}
```

**Frontend Handling:**
- Frontend harus mengecek `next_action` dan `redirect_to` dalam response
- Jika `next_action` adalah `"analyze_apk"`, redirect user ke halaman analyze APK (`/analytics/analyze-apk`)
- Gunakan `file_info.file_ids` untuk menampilkan daftar file yang tersedia untuk dianalisis
- Tampilkan `instruction` sebagai pesan informatif kepada user

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | integer | HTTP status code |
| `message` | string | Pesan status atau error message |
| `data` | object | Data response atau error details |

### Success Response Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `analytic_name` | string | Nama dari analytic |
| `method` | string | Method analytic (selalu "APK Analytics" untuk endpoint ini) |
| `malware_scoring` | string | Skor malware dari analisis APK (0-100) |
| `permissions` | array | Daftar permissions yang ditemukan dalam APK |
| `permissions[].id` | integer | ID dari permission record |
| `permissions[].item` | string | Nama permission (contoh: "android.permission.INTERNET") |
| `permissions[].status` | string | Status permission ("normal", "dangerous", "signature", dll) |
| `permissions[].description` | string | Deskripsi dari permission |
| `summary` | string \| null | Summary dari analytic (jika ada) |

### Error Response Data Fields (No APK Analysis)

| Field | Type | Description |
|-------|------|-------------|
| `analytic_info` | object | Informasi tentang analytic |
| `analytic_info.analytic_id` | integer | ID dari analytic |
| `analytic_info.analytic_name` | string | Nama dari analytic |
| `analytic_info.method` | string | Method dari analytic |
| `file_info` | object \| null | Informasi tentang file yang sudah di-upload (hanya ada jika files exist) |
| `file_info.file_count` | integer | Jumlah file yang sudah di-upload |
| `file_info.file_ids` | array | Array of file IDs yang sudah di-upload |
| `next_action` | string | Action yang harus dilakukan selanjutnya: `"upload_apk"` atau `"analyze_apk"` |
| `redirect_to` | string | Path untuk redirect user: `"/analytics/upload-apk"` atau `"/analytics/analyze-apk"` |
| `instruction` | string | Instruksi yang jelas untuk user tentang apa yang harus dilakukan |

## Example Requests

### Request 1: Get APK Analysis
```http
GET /api/v1/analytics/apk-analytic?analytic_id=44
Authorization: Bearer <access_token>
```

### Request 2: Get APK Analysis (Different Analytic)
```http
GET /api/v1/analytics/apk-analytic?analytic_id=50
Authorization: Bearer <access_token>
```

## Example Responses

### Success Response
```json
{
    "status": 200,
    "message": "Success",
    "data": {
        "analytic_name": "APK Analysis - WhatsApp",
        "method": "APK Analytics",
        "malware_scoring": "85",
        "permissions": [
            {
                "id": 1,
                "item": "android.permission.INTERNET",
                "status": "normal",
                "description": "Allows app to access the internet"
            },
            {
                "id": 2,
                "item": "android.permission.READ_CONTACTS",
                "status": "dangerous",
                "description": "Allows app to read contacts"
            },
            {
                "id": 3,
                "item": "android.permission.CAMERA",
                "status": "dangerous",
                "description": "Allows app to take pictures"
            }
        ],
        "summary": "WhatsApp APK analysis completed successfully"
    }
}
```

### Error Response - No Files Uploaded
```json
{
    "status": 404,
    "message": "No APK analysis found for analytic_id=44. Please upload an APK file first.",
    "data": {
        "analytic_info": {
            "analytic_id": 44,
            "analytic_name": "APK Analysis Test",
            "method": "APK Analytics"
        },
        "next_action": "upload_apk",
        "redirect_to": "/analytics/upload-apk",
        "instruction": "Please upload an APK file to analyze. After uploading, you can analyze the APK file."
    }
}
```

### Error Response - Files Exist But Not Analyzed
```json
{
    "status": 404,
    "message": "No APK analysis found for analytic_id=44. Please analyze the uploaded APK file.",
    "data": {
        "analytic_info": {
            "analytic_id": 44,
            "analytic_name": "APK Analysis Test",
            "method": "APK Analytics"
        },
        "file_info": {
            "file_count": 1,
            "file_ids": [101]
        },
        "next_action": "analyze_apk",
        "redirect_to": "/analytics/analyze-apk",
        "instruction": "Please analyze the uploaded APK file to view the analysis results."
    }
}
```

### Error Response - Wrong Method
```json
{
    "status": 400,
    "message": "This endpoint is only for APK Analytics. Current analytic method is 'Deep Communication Analytics'",
    "data": {}
}
```

### Error Response - Permission Denied
```json
{
    "status": 403,
    "message": "You do not have permission to access this analytic",
    "data": {}
}
```

## Notes

1. **Error Handling Flow:**
   - Endpoint akan mengecek apakah analytic ada
   - Kemudian mengecek permission user
   - Kemudian mengecek apakah method adalah "APK Analytics"
   - Kemudian mengecek apakah ada APK analysis
   - Jika tidak ada APK analysis, akan mengecek apakah ada file yang sudah di-upload
   - Berdasarkan hasil pengecekan, akan memberikan instruksi yang sesuai

2. **Frontend Integration:**
   - Frontend harus selalu mengecek field `next_action` dan `redirect_to` dalam error response
   - Gunakan `redirect_to` untuk redirect user ke halaman yang sesuai
   - Tampilkan `instruction` sebagai pesan informatif kepada user
   - Jika `file_info` ada, gunakan `file_ids` untuk menampilkan daftar file yang tersedia

3. **Permission Check:**
   - Admin dapat mengakses semua analytic
   - Regular user hanya dapat mengakses analytic yang mereka miliki (berdasarkan text matching di `analytic_name`, `summary`, atau `created_by`)

4. **APK Analysis Workflow:**
   - **Step 1:** Upload APK file menggunakan endpoint `/api/v1/analytics/upload-apk`
   - **Step 2:** Analyze APK file menggunakan endpoint `/api/v1/analytics/analyze-apk` dengan `file_id` dan `analytic_id`
   - **Step 3:** Get APK analysis results menggunakan endpoint ini (`/api/v1/analytics/apk-analytic`)

5. **Data Ordering:**
   - APK records diurutkan berdasarkan `created_at` descending (terbaru pertama)
   - `malware_scoring` diambil dari record pertama (terbaru)

