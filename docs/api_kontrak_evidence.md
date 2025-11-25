# Evidence Custody API Contract

Dokumentasi ini menjelaskan API endpoints untuk mengelola chain of custody evidence, termasuk acquisition, preparation, extraction, analysis, dan custody logs.

## 📋 Daftar Isi

1. [Base Path](#base-path)
2. [Create Acquisition Report](#1-create-acquisition-report)
3. [Create Preparation Report](#2-create-preparation-report)
4. [Create Extraction Report](#3-create-extraction-report)
5. [Create Analysis Report](#4-create-analysis-report)
6. [Get Custody Logs](#5-get-custody-logs)

---

## Base Path

`/api/v1/evidence`

---

## 1. Create Acquisition Report

**Endpoint:** `POST /api/v1/evidence/{evidence_id}/custody/acquisition`

**Description:** Membuat laporan acquisition (pengambilan) untuk evidence. Endpoint ini digunakan untuk mencatat proses pengambilan evidence di lapangan, termasuk langkah-langkah yang dilakukan dan foto dokumentasi.

**Headers:**
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID Evidence yang akan dibuat laporan acquisition-nya |

**Request Body (Form Data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `investigator` | string | No | Nama investigator. Jika tidak diisi, akan menggunakan fullname dari current user |
| `location` | string | No | Lokasi pengambilan evidence |
| `evidence_source` | string | No | Sumber evidence (jika tidak diisi, akan mengambil dari evidence.source) |
| `evidence_type` | string | No | Tipe evidence |
| `evidence_detail` | string | No | Detail evidence |
| `notes` | string | No | Catatan tambahan |
| `steps` | array[string] | Yes | Daftar langkah-langkah pengambilan evidence |
| `photos` | array[file] | Yes | Foto dokumentasi untuk setiap langkah (harus sesuai jumlah steps) |

**Note:**
- `investigator` akan default ke `fullname` dari current user jika tidak diisi
- `created_by` akan otomatis diisi dengan `email` dari current user
- `evidence_source` akan mengambil nilai dari `evidence.source` jika tidak diisi
- Jumlah `photos` harus sesuai dengan jumlah `steps`

**Request Example:**
```bash
POST /api/v1/evidence/1/custody/acquisition
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

investigator: "John Doe"
location: "Crime Scene A"
evidence_source: "Hp"
evidence_type: "File"
evidence_detail: "Samsung Galaxy S21"
notes: "Evidence diambil dari tersangka"
steps: ["Step 1: Dokumentasi lokasi", "Step 2: Pengambilan device", "Step 3: Packaging"]
photos: [file1.jpg, file2.jpg, file3.jpg]
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Success",
  "data": {
    "id": 1,
    "evidence_id": 1,
    "created_by": "admin@example.com",
    "investigator": "John Doe",
    "custody_type": "acquisition",
    "location": "Crime Scene A",
    "evidence_source": "Hp",
    "evidence_type": "File",
    "evidence_detail": "Samsung Galaxy S21",
    "notes": "Evidence diambil dari tersangka",
    "details": [
      {
        "steps": "Step 1: Dokumentasi lokasi",
        "photo": "uploads/custody/acquisition/abc123.jpg"
      },
      {
        "steps": "Step 2: Pengambilan device",
        "photo": "uploads/custody/acquisition/def456.jpg"
      },
      {
        "steps": "Step 3: Packaging",
        "photo": "uploads/custody/acquisition/ghi789.jpg"
      }
    ],
    "created_at": "2025-11-25T10:30:00+07:00",
    "updated_at": null
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence not found",
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

---

## 2. Create Preparation Report

**Endpoint:** `POST /api/v1/evidence/{evidence_id}/custody/preparation`

**Description:** Membuat laporan preparation (persiapan) untuk evidence. Endpoint ini digunakan untuk mencatat proses persiapan evidence sebelum dilakukan ekstraksi, termasuk hipotesis dan tools yang akan digunakan.

**Headers:**
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID Evidence yang akan dibuat laporan preparation-nya |

**Request Body (Form Data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `investigator` | string | No | Nama investigator. Jika tidak diisi, akan menggunakan fullname dari current user |
| `location` | string | No | Lokasi persiapan evidence |
| `evidence_source` | string | No | Sumber evidence (jika tidak diisi, akan mengambil dari evidence.source) |
| `evidence_type` | string | No | Tipe evidence |
| `evidence_detail` | string | No | Detail evidence |
| `notes` | string | No | Catatan tambahan |
| `hypothesis` | array[string] | Yes | Daftar hipotesis untuk analisis |
| `tools` | array[string] | Yes | Daftar tools yang akan digunakan (harus sesuai jumlah hypothesis) |

**Note:**
- `investigator` akan default ke `fullname` dari current user jika tidak diisi
- `created_by` akan otomatis diisi dengan `email` dari current user
- `evidence_source` akan mengambil nilai dari `evidence.source` jika tidak diisi
- Jumlah `hypothesis` dan `tools` akan di-pair berdasarkan index

**Request Example:**
```bash
POST /api/v1/evidence/1/custody/preparation
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

investigator: "John Doe"
location: "Forensic Lab"
evidence_source: "Hp"
evidence_type: "File"
evidence_detail: "Samsung Galaxy S21"
notes: "Preparing for extraction"
hypothesis: ["Extract call logs", "Extract messages", "Extract contacts"]
tools: ["Magnet Axiom", "Oxygen Forensics", "Cellebrite"]
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Success",
  "data": {
    "id": 2,
    "evidence_id": 1,
    "created_by": "admin@example.com",
    "investigator": "John Doe",
    "custody_type": "preparation",
    "location": "Forensic Lab",
    "evidence_source": "Hp",
    "evidence_type": "File",
    "evidence_detail": "Samsung Galaxy S21",
    "notes": "Preparing for extraction",
    "details": [
      {
        "hypothesis": "Extract call logs",
        "tools": "Magnet Axiom"
      },
      {
        "hypothesis": "Extract messages",
        "tools": "Oxygen Forensics"
      },
      {
        "hypothesis": "Extract contacts",
        "tools": "Cellebrite"
      }
    ],
    "created_at": "2025-11-25T11:00:00+07:00",
    "updated_at": null
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence not found",
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

---

## 3. Create Extraction Report

**Endpoint:** `POST /api/v1/evidence/{evidence_id}/custody/extraction`

**Description:** Membuat laporan extraction (ekstraksi) untuk evidence. Endpoint ini digunakan untuk mencatat proses ekstraksi data dari evidence, termasuk file hasil ekstraksi.

**Headers:**
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID Evidence yang akan dibuat laporan extraction-nya |

**Request Body (Form Data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `investigator` | string | No | Nama investigator. Jika tidak diisi, akan menggunakan fullname dari current user |
| `location` | string | No | Lokasi ekstraksi evidence |
| `evidence_source` | string | No | Sumber evidence (jika tidak diisi, akan mengambil dari evidence.source) |
| `evidence_type` | string | No | Tipe evidence |
| `evidence_detail` | string | No | Detail evidence |
| `notes` | string | No | Catatan tambahan |
| `extraction_file` | file | Yes | File hasil ekstraksi |

**Note:**
- `investigator` akan default ke `fullname` dari current user jika tidak diisi
- `created_by` akan otomatis diisi dengan `email` dari current user
- `evidence_source` akan mengambil nilai dari `evidence.source` jika tidak diisi
- File size akan otomatis dihitung dan dikonversi ke format human-readable

**Request Example:**
```bash
POST /api/v1/evidence/1/custody/extraction
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

investigator: "John Doe"
location: "Forensic Lab"
evidence_source: "Hp"
evidence_type: "File"
evidence_detail: "Samsung Galaxy S21"
notes: "Extraction completed successfully"
extraction_file: extraction_result.zip
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Extraction custody report created",
  "data": {
    "id": 3,
    "evidence_id": 1,
    "created_by": "admin@example.com",
    "investigator": "John Doe",
    "custody_type": "extraction",
    "location": "Forensic Lab",
    "evidence_source": "Hp",
    "evidence_type": "File",
    "evidence_detail": "Samsung Galaxy S21",
    "notes": "Extraction completed successfully",
    "details": {
      "extraction_file": "uploads/custody/extraction/xyz789.zip",
      "file_name": "extraction_result.zip",
      "file_size": "125.50 MB"
    },
    "created_at": "2025-11-25T12:00:00+07:00",
    "updated_at": null
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence not found",
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

---

## 4. Create Analysis Report

**Endpoint:** `POST /api/v1/evidence/{evidence_id}/custody/analysis`

**Description:** Membuat laporan analysis (analisis) untuk evidence. Endpoint ini digunakan untuk mencatat hasil analisis evidence, termasuk hipotesis, tools yang digunakan, hasil analisis, dan file pendukung.

**Headers:**
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID Evidence yang akan dibuat laporan analysis-nya |

**Request Body (Form Data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `location` | string | No | Lokasi analisis evidence |
| `evidence_source` | string | No | Sumber evidence (jika tidak diisi, akan mengambil dari evidence.source) |
| `evidence_type` | string | No | Tipe evidence |
| `evidence_detail` | string | No | Detail evidence |
| `notes` | string | No | Catatan tambahan |
| `hypothesis` | array[string] | Yes | Daftar hipotesis untuk analisis |
| `tools` | array[string] | Yes | Daftar tools yang digunakan (harus sesuai jumlah hypothesis) |
| `result` | array[string] | Yes | Daftar hasil analisis (harus sesuai jumlah hypothesis) |
| `files` | array[file] | No | File pendukung hasil analisis |

**Note:**
- `investigator` akan otomatis diisi dengan `fullname` dari current user (tidak bisa diisi manual)
- `created_by` akan otomatis diisi dengan `email` dari current user
- `evidence_source` akan mengambil nilai dari `evidence.source` jika tidak diisi
- Jumlah `hypothesis`, `tools`, dan `result` akan di-pair berdasarkan index

**Request Example:**
```bash
POST /api/v1/evidence/1/custody/analysis
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

location: "Forensic Lab"
evidence_source: "Hp"
evidence_type: "File"
evidence_detail: "Samsung Galaxy S21"
notes: "Analysis completed"
hypothesis: ["Analyze call logs", "Analyze messages", "Analyze contacts"]
tools: ["Magnet Axiom", "Oxygen Forensics", "Cellebrite"]
result: ["Found 150 calls", "Found 500 messages", "Found 200 contacts"]
files: [report1.pdf, report2.pdf]
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Analysis report created",
  "data": {
    "id": 4,
    "evidence_id": 1,
    "created_by": "admin@example.com",
    "investigator": "Admin Forensic",
    "custody_type": "analysis",
    "location": "Forensic Lab",
    "evidence_source": "Hp",
    "evidence_type": "File",
    "evidence_detail": "Samsung Galaxy S21",
    "notes": "Analysis completed",
    "details": {
      "results": [
        {
          "hypothesis": "Analyze call logs",
          "tools": "Magnet Axiom",
          "result": "Found 150 calls"
        },
        {
          "hypothesis": "Analyze messages",
          "tools": "Oxygen Forensics",
          "result": "Found 500 messages"
        },
        {
          "hypothesis": "Analyze contacts",
          "tools": "Cellebrite",
          "result": "Found 200 contacts"
        }
      ],
      "files": [
        {
          "file_name": "report1.pdf",
          "file_size": "2.50 MB",
          "file_path": "uploads/custody/analysis/abc123.pdf"
        },
        {
          "file_name": "report2.pdf",
          "file_size": "1.25 MB",
          "file_path": "uploads/custody/analysis/def456.pdf"
        }
      ]
    },
    "created_at": "2025-11-25T13:00:00+07:00",
    "updated_at": null
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence not found",
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

---

## 5. Get Custody Logs

**Endpoint:** `GET /api/v1/evidence/{evidence_id}/custody-logs`

**Description:** Mendapatkan daftar custody logs untuk evidence tertentu. Endpoint ini digunakan untuk melihat history chain of custody evidence.

**Headers:**
- `Authorization: Bearer <access_token>`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID Evidence yang akan diambil custody logs-nya |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter berdasarkan custody type (acquisition, preparation, extraction, analysis) |

**Request Example:**
```bash
GET /api/v1/evidence/1/custody-logs?type=acquisition
Authorization: Bearer <access_token>
```

**Response (200 OK - With Data):**
```json
{
  "status": 200,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "evidence_id": 1,
      "custody_type": "acquisition",
      "notes": "Evidence diambil dari tersangka",
      "created_at": "2025-11-25T10:30:00+07:00",
      "created_by": "John Doe"
    },
    {
      "id": 2,
      "evidence_id": 1,
      "custody_type": "preparation",
      "notes": "Preparing for extraction",
      "created_at": "2025-11-25T11:00:00+07:00",
      "created_by": "John Doe"
    },
    {
      "id": 3,
      "evidence_id": 1,
      "custody_type": "extraction",
      "notes": "Extraction completed successfully",
      "created_at": "2025-11-25T12:00:00+07:00",
      "created_by": "John Doe"
    },
    {
      "id": 4,
      "evidence_id": 1,
      "custody_type": "analysis",
      "notes": "Analysis completed",
      "created_at": "2025-11-25T13:00:00+07:00",
      "created_by": "Admin Forensic"
    }
  ]
}
```

**Response (200 OK - No Data):**
```json
{
  "status": 200,
  "message": "Success",
  "data": []
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence not found",
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

---

## Data Models

### CustodyReport

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | ID unik custody report |
| `evidence_id` | integer | ID evidence yang terkait |
| `created_by` | string | Email user yang membuat report (otomatis dari current user) |
| `investigator` | string | Nama investigator (default: fullname current user) |
| `custody_type` | string | Tipe custody (acquisition, preparation, extraction, analysis) |
| `location` | string | Lokasi proses custody |
| `evidence_source` | string | Sumber evidence |
| `evidence_type` | string | Tipe evidence |
| `evidence_detail` | string | Detail evidence |
| `notes` | string | Catatan tambahan |
| `details` | object/array | Detail spesifik berdasarkan custody_type |
| `created_at` | datetime | Waktu pembuatan report |
| `updated_at` | datetime | Waktu update terakhir |

### CustodyLog

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | ID unik custody log |
| `evidence_id` | integer | ID evidence yang terkait |
| `custody_type` | string | Tipe custody (acquisition, preparation, extraction, analysis) |
| `notes` | string | Catatan log |
| `created_at` | datetime | Waktu pembuatan log |
| `created_by` | string | Nama user yang membuat log |

---

## Notes

1. **Auto-fill Fields:**
   - `created_by`: Otomatis diisi dengan `email` dari current user
   - `investigator`: Default ke `fullname` dari current user jika tidak diisi (kecuali untuk analysis yang selalu menggunakan fullname current user)
   - `evidence_source`: Jika tidak diisi, akan mengambil dari `evidence.source`

2. **File Upload:**
   - Semua file yang diupload akan disimpan di folder `uploads/custody/{custody_type}/`
   - File size otomatis dikonversi ke format human-readable (B, KB, MB, GB, TB)

3. **Details Structure:**
   - **Acquisition**: Array of objects dengan `steps` dan `photo`
   - **Preparation**: Array of objects dengan `hypothesis` dan `tools`
   - **Extraction**: Object dengan `extraction_file`, `file_name`, dan `file_size`
   - **Analysis**: Object dengan `results` (array) dan `files` (array)

4. **Custody Logs:**
   - Otomatis dibuat setiap kali membuat custody report
   - Diurutkan berdasarkan `created_at` ascending
   - Dapat difilter berdasarkan `type` (custody_type)

---

## Best Practices

1. **Chain of Custody:**
   - Selalu buat custody report secara berurutan: Acquisition → Preparation → Extraction → Analysis
   - Pastikan semua langkah terdokumentasi dengan baik

2. **File Management:**
   - Pastikan file yang diupload tidak terlalu besar
   - Gunakan format file yang standar (jpg, png untuk foto, zip untuk extraction)

3. **Data Integrity:**
   - Selalu verifikasi `evidence_id` sebelum membuat custody report
   - Pastikan semua required fields terisi dengan benar

4. **Security:**
   - Semua endpoint memerlukan authentication
   - Pastikan user memiliki akses ke evidence yang akan dibuat custody report-nya

