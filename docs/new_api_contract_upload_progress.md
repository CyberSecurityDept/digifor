# API Contract: Upload Progress

## Endpoint
`GET /api/v1/analytics/upload-progress`

## Description
Mengambil status progress dari proses upload file analytics. Endpoint ini digunakan untuk memantau status upload file, termasuk progress percentage, status upload, dan informasi error jika terjadi kegagalan.

## Authentication
Tidak diperlukan authentication (public endpoint)

## Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `upload_id` | string | Yes | - | ID unik dari upload yang ingin dicek progress-nya |
| `type` | string | No | `"data"` | Tipe upload: `"data"` untuk analytics data atau `"apk"` untuk APK analytics |

## Response Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success - Progress berhasil diambil |
| 404 | Not Found - Upload ID tidak ditemukan |
| 500 | Internal Server Error - Terjadi error pada server |

## Response Body Structure

### Success Response (200 OK)

Response body bervariasi tergantung status upload:

#### 1. Status: `Pending`
Upload sedang menunggu untuk diproses.

```json
{
    "status": "Pending",
    "message": "Preparing...",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "0 MB/5.234 MB",
    "percentage": 0,
    "upload_status": "Pending",
    "data": []
}
```

#### 2. Status: `Progress`
Upload sedang dalam proses.

```json
{
    "status": "Progress",
    "message": "Preparing... (45%)",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "2.345 MB/5.234 MB",
    "percentage": 45,
    "upload_status": "Progress",
    "data": []
}
```

#### 3. Status: `Success`
Upload berhasil diselesaikan.

```json
{
    "status": "Success",
    "message": "Upload successful",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "5.234 MB",
    "percentage": 100,
    "upload_status": "Success",
    "data": [
        {
            "file_id": 123,
            "file_name": "example_file.xlsx",
            "status": "completed"
        }
    ]
}
```

#### 4. Status: `Failed`
Upload gagal dengan berbagai alasan.

**a. Upload ID tidak ditemukan (404)**

```json
{
    "status": "Failed",
    "message": "Upload ID not found",
    "upload_id": "upload_1234567890_abc123",
    "file_name": null,
    "size": "Upload Failed! Please try again",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

**b. Tools mismatch (detected tool tersedia)**

```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools Oxygen",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "Upload Failed! Please upload this file using Tools 'Oxygen'",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

**c. Upload gagal (detected tool tidak tersedia)**

```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools Oxygen",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "Upload Failed! Please try again",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

**d. Unknown status**

```json
{
    "status": "Failed",
    "message": "Unknown upload status: UnknownStatus",
    "upload_id": "upload_1234567890_abc123",
    "upload_status": "Failed",
    "data": []
}
```

### Error Response (500 Internal Server Error)

```json
{
    "status": "Failed",
    "message": "Internal server error: <error_message>",
    "upload_id": "upload_1234567890_abc123"
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Status upload: `"Pending"`, `"Progress"`, `"Success"`, atau `"Failed"` |
| `message` | string | Pesan status atau error message |
| `upload_id` | string | ID unik dari upload |
| `file_name` | string \| null | Nama file yang di-upload |
| `size` | string | Ukuran file yang sudah di-upload / total ukuran file, atau error message jika gagal |
| `percentage` | number \| string | Persentase progress (0-100) atau `"Error"` jika gagal |
| `upload_status` | string | Status upload: `"Pending"`, `"Progress"`, `"Success"`, atau `"Failed"` |
| `data` | array | Array data hasil upload (hanya ada jika status `"Success"`) |

## Error Handling

### 1. Upload ID Not Found (404)

**Kondisi:** Upload ID tidak ditemukan dalam sistem.

**Response:**
- Status Code: `404`
- Status: `"Failed"`
- Message: `"Upload ID not found"`
- Size: `"Upload Failed! Please try again"` atau `"Upload Failed! Please upload this file using Tools '{detected_tool}'"` jika detected tool tersedia

**Contoh:**
```json
{
    "status": "Failed",
    "message": "Upload ID not found",
    "upload_id": "invalid_upload_id",
    "file_name": null,
    "size": "Upload Failed! Please try again",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

### 2. Tools Mismatch Error

**Kondisi:** File yang di-upload tidak sesuai dengan tools yang dipilih. Sistem akan mendeteksi tools yang benar berdasarkan sheet names di file.

**Response:**
- Status Code: `200`
- Status: `"Failed"`
- Message: `"File upload failed. Please upload this file using Tools {detected_tool}"`
- Size: `"Upload Failed! Please upload this file using Tools '{detected_tool}'"`

**Detected Tools yang mungkin:**
- `"Oxygen"` - Untuk file iOS dengan sheet seperti "Telegram Messages - iOS", "Instagram Direct Messages", dll
- `"Cellebrite"` - Untuk file dengan sheet "Chats" atau "Social Media"
- `"Magnet Axiom"` - Untuk file Android dengan sheet seperti "Android WhatsApp Messages", "Telegram Messages - Android", dll

**Contoh:**
```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools Oxygen",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "Exported_results_iphone_hikari.xlsx",
    "size": "Upload Failed! Please upload this file using Tools 'Oxygen'",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

### 3. Parsing Error

**Kondisi:** Terjadi error saat parsing file atau tidak ada data yang berhasil di-parse.

**Response:**
- Status Code: `200`
- Status: `"Failed"`
- Message: Pesan error dari parsing atau `"File upload failed. Please upload this file using Tools {detected_tool}"`
- Size: `"Upload Failed! Please upload this file using Tools '{detected_tool}'"` atau `"Upload Failed! Please try again"`

**Contoh:**
```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools Oxygen",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "Upload Failed! Please upload this file using Tools 'Oxygen'",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

### 4. Internal Server Error (500)

**Kondisi:** Terjadi error internal pada server.

**Response:**
- Status Code: `500`
- Status: `"Failed"`
- Message: `"Internal server error: {error_message}"`

**Contoh:**
```json
{
    "status": "Failed",
    "message": "Internal server error: Database connection failed",
    "upload_id": "upload_1234567890_abc123"
}
```

### 5. Unknown Status

**Kondisi:** Status upload tidak dikenali oleh sistem.

**Response:**
- Status Code: `200`
- Status: `"Failed"`
- Message: `"Unknown upload status: {status}"`

**Contoh:**
```json
{
    "status": "Failed",
    "message": "Unknown upload status: UnknownStatus",
    "upload_id": "upload_1234567890_abc123",
    "upload_status": "Failed",
    "data": []
}
```

## Status Flow

```
Pending → Progress → Success
   ↓         ↓
 Failed   Failed
```

1. **Pending**: Upload baru dibuat, menunggu untuk diproses
2. **Progress**: Upload sedang dalam proses (percentage 0-100)
3. **Success**: Upload berhasil diselesaikan (percentage 100)
4. **Failed**: Upload gagal pada tahap manapun

## Notes

1. **Polling Frequency**: Disarankan untuk melakukan polling setiap 1-2 detik untuk mendapatkan update progress yang real-time.

2. **Detected Tool**: Ketika upload gagal karena tools mismatch, sistem akan mencoba mendeteksi tools yang benar berdasarkan:
   - Method yang dipilih (Deep Communication Analytics, Contact Correlation, Social Media Correlation, Hashfile Analytics)
   - Sheet names yang ada di file Excel
   - Format file yang digunakan

3. **Size Field**: 
   - Format normal: `"{uploaded_size} MB/{total_size} MB"` (contoh: `"2.345 MB/5.234 MB"`)
   - Format success: `"{total_size} MB"` (contoh: `"5.234 MB"`)
   - Format error dengan detected tool: `"Upload Failed! Please upload this file using Tools '{detected_tool}'"`
   - Format error tanpa detected tool: `"Upload Failed! Please try again"`

4. **Percentage Field**:
   - Range: `0` sampai `100` untuk status Progress
   - Value: `100` untuk status Success
   - Value: `"Error"` untuk status Failed

5. **Type Parameter**:
   - `"data"`: Untuk upload analytics data (default)
   - `"apk"`: Untuk upload APK analytics

## Example Requests

### Request 1: Check Progress (Data Upload)
```http
GET /api/v1/analytics/upload-progress?upload_id=upload_1234567890_abc123&type=data
```

### Request 2: Check Progress (APK Upload)
```http
GET /api/v1/analytics/upload-progress?upload_id=upload_1234567890_abc123&type=apk
```

### Request 3: Check Progress (Default Type)
```http
GET /api/v1/analytics/upload-progress?upload_id=upload_1234567890_abc123
```

## Example Responses

### Success Response (Progress)
```json
{
    "status": "Progress",
    "message": "Preparing... (67%)",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "3.456 MB/5.234 MB",
    "percentage": 67,
    "upload_status": "Progress",
    "data": []
}
```

### Success Response (Success)
```json
{
    "status": "Success",
    "message": "Upload successful",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "5.234 MB",
    "percentage": 100,
    "upload_status": "Success",
    "data": [
        {
            "file_id": 123,
            "file_name": "example_file.xlsx",
            "status": "completed"
        }
    ]
}
```

### Error Response (Tools Mismatch)
```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools Oxygen",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "Exported_results_iphone_hikari.xlsx",
    "size": "Upload Failed! Please upload this file using Tools 'Oxygen'",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

### Error Response (Upload ID Not Found)
```json
{
    "status": "Failed",
    "message": "Upload ID not found",
    "upload_id": "invalid_upload_id",
    "file_name": null,
    "size": "Upload Failed! Please try again",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

