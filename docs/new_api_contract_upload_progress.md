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

**b. Tools mismatch atau parsing error (dengan tool name)**

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

**c. Upload gagal (tool name dari parameter tools)**

```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools Cellebrite",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "Upload Failed! Please upload this file using Tools 'Cellebrite'",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

**d. Upload gagal (fallback ke parameter tools atau generic message)**

```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools the correct tools",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "Upload Failed! Please upload this file using Tools 'the correct tools'",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

**e. Unknown status**

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
- Size: `"Upload Failed! Please try again"` atau `"Upload Failed! Please upload this file using Tools '{tool_name}'"` jika tool name tersedia dari upload service

**Catatan:** Sistem akan mencoba mengambil `detected_tool` dari upload service jika tersedia. Tool name yang valid adalah: `"Cellebrite"`, `"Oxygen"`, `"Magnet Axiom"`, atau `"Encase"`.

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
- Message: `"File upload failed. Please upload this file using Tools {tool_name}"`
- Size: `"Upload Failed! Please upload this file using Tools '{tool_name}'"`

**Tool Detection Priority:**
1. **Deteksi dari Sheet Names**: Sistem akan mencoba mendeteksi tool dari sheet names di file Excel berdasarkan method yang dipilih
2. **Normalisasi dari Parameter Tools**: Jika deteksi dari sheet gagal, sistem akan menormalisasi parameter `tools` yang diberikan user
3. **Fallback ke Parameter Tools**: Jika normalisasi gagal, sistem akan menggunakan parameter `tools` langsung atau `"the correct tools"`

**Tool Names yang Valid:**
- `"Cellebrite"` - Untuk file dengan sheet "Chats" atau "Social Media" (Deep Communication, Contact Correlation, Social Media Correlation)
- `"Oxygen"` - Untuk file iOS dengan sheet seperti "Telegram Messages - iOS", "Instagram Direct Messages", dll
- `"Magnet Axiom"` - Untuk file Android dengan sheet seperti "Android WhatsApp Messages", "Telegram Messages - Android", dll
- `"Encase"` - Untuk file dengan format Encase (Hashfile Analytics)

**Catatan:** Sistem tidak akan menggunakan `"Unknown"` sebagai tool name. Jika tool tidak bisa dideteksi, sistem akan menggunakan normalisasi dari parameter `tools` atau fallback ke parameter `tools` langsung.

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
- Message: `"File upload failed. Please upload this file using Tools {tool_name}"` (selalu menggunakan tool name yang valid)
- Size: `"Upload Failed! Please upload this file using Tools '{tool_name}'"`

**Tool Name Source:**
1. Dari `parsing_result["detected_tool"]` jika tersedia
2. Deteksi dari sheet names menggunakan `_detect_tool_from_sheets()`
3. Normalisasi dari parameter `tools` menggunakan `_normalize_tool_name()`
4. Fallback ke parameter `tools` langsung atau `"the correct tools"`

**Catatan:** Sistem akan selalu mencoba menampilkan tool name yang valid dalam error message. Tidak akan ada error message tanpa tool name kecuali dalam kasus yang sangat spesifik.

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

2. **Tool Detection & Normalization**: Ketika upload gagal karena tools mismatch atau parsing error, sistem akan mencoba mendapatkan tool name yang valid dengan urutan prioritas:
   - **Deteksi dari Sheet Names**: Berdasarkan method yang dipilih (Deep Communication Analytics, Contact Correlation, Social Media Correlation, Hashfile Analytics) dan sheet names yang ada di file Excel
   - **Normalisasi dari Parameter Tools**: Jika deteksi gagal, sistem akan menormalisasi parameter `tools` yang diberikan user menjadi format standar:
     - `"cellebrite"` atau `"celebrate"` → `"Cellebrite"`
     - `"oxygen"` → `"Oxygen"`
     - `"magnet axiom"` atau `"magnet"` + `"axiom"` → `"Magnet Axiom"`
     - `"encase"` → `"Encase"`
   - **Fallback**: Jika normalisasi juga gagal, sistem akan menggunakan parameter `tools` langsung atau `"the correct tools"`
   
   **Catatan Penting:** Sistem tidak akan menggunakan `"Unknown"` sebagai tool name. Semua error message akan selalu mencoba menampilkan tool name yang valid.

3. **Size Field**: 
   - Format normal: `"{uploaded_size} MB/{total_size} MB"` (contoh: `"2.345 MB/5.234 MB"`)
   - Format success: `"{total_size} MB"` (contoh: `"5.234 MB"`)
   - Format error dengan tool name: `"Upload Failed! Please upload this file using Tools '{tool_name}'"` (tool_name: Cellebrite, Oxygen, Magnet Axiom, Encase, atau parameter tools)
   - Format error fallback: `"Upload Failed! Please upload this file using Tools 'the correct tools'"` (hanya jika semua deteksi dan normalisasi gagal)

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

**Catatan:** Jika `detected_tool` tersedia dari upload service, `size` akan berisi `"Upload Failed! Please upload this file using Tools '{tool_name}'"` dengan tool name yang valid.

### Error Response (Parsing Error dengan Tool Name)
```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools Magnet Axiom",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "Upload Failed! Please upload this file using Tools 'Magnet Axiom'",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

### Error Response (No Data Parsed dengan Tool Name)
```json
{
    "status": "Failed",
    "message": "File upload failed. Please upload this file using Tools Encase",
    "upload_id": "upload_1234567890_abc123",
    "file_name": "example_file.xlsx",
    "size": "Upload Failed! Please upload this file using Tools 'Encase'",
    "percentage": "Error",
    "upload_status": "Failed",
    "data": []
}
```

