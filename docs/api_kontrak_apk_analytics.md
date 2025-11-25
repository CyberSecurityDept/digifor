# API Contract - Update Evidence

## Update Evidence

Mengupdate informasi evidence yang sudah ada. Endpoint ini mendukung update sebagian atau semua field evidence, termasuk file upload, person/suspect information, dan metadata lainnya.

### Endpoint
```
PUT /api/v1/evidence/update-evidence/{evidence_id}
```

### Authentication
Required - Bearer Token

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID dari evidence yang akan diupdate |

### Request Body (Form Data)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | No | Case ID (jika ingin mengubah case yang terkait) |
| `evidence_number` | string | No | Evidence number (jika disediakan, tidak boleh kosong) |
| `title` | string | No | Evidence title |
| `type` | string | No | Evidence type name (text input dari form UI). **Jika disediakan, sistem akan mencari atau membuat evidence type** |
| `source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| `evidence_file` | File | No | Evidence file upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`) |
| `evidence_summary` | string | No | Evidence summary/description (disimpan ke field `description` di database) |
| `investigator` | string | No | Investigator name (who collected/analyzed the evidence) |
| `person_name` | string | No | Person of interest name. **Hanya digunakan jika `is_unknown_person = false` (radio button "Known Person")** |
| `suspect_status` | string | No | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be same case) |
| `is_unknown_person` | boolean | No | Flag yang menandakan apakah person tersebut unknown/tidak diketahui. **Jika `true`, maka `person_name` dan `suspect_status` akan diabaikan dan person akan di-set menjadi "Unknown"** |
| `suspect_id` | integer | No | ID dari suspect yang sudah ada (jika ingin menggunakan suspect yang sudah terdaftar) |

### Request Example
```http
PUT /api/v1/evidence/update-evidence/1
Authorization: Bearer <token>
Content-Type: multipart/form-data

case_id: 1
evidence_number: 438343040304
type: File
source: Handphone
evidence_file: <binary_file>
evidence_summary: testing update evidence 2
investigator: Solehun
person_name: Raka
suspect_status: Witness
is_unknown_person: true
```

### Success Response (200 OK)
```json
{
  "status": 200,
  "message": "Evidence updated successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "438343040304",
    "source": "Handphone",
    "file_path": "data/evidence/evidence_20251126_013853_438343040304.png",
    "description": "testing update evidence 2",
    "title": "pelari tercepat sepanjang jalan",
    "investigator": "Solehun",
    "agency": "Agen Cabe",
    "person_name": null,
    "updated_at": "26/11/2025"
  }
}
```

### Response Fields

#### Response Object
| Field | Type | Description |
|-------|------|-------------|
| `status` | integer | HTTP status code (200) |
| `message` | string | Pesan response |
| `data` | object | Data evidence yang sudah diupdate |

#### Data Object
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | ID evidence |
| `case_id` | integer | ID case yang terkait |
| `evidence_number` | string | Evidence number |
| `source` | string | Evidence source |
| `file_path` | string | Path file evidence (jika ada file upload) |
| `description` | string | Description/summary evidence |
| `title` | string | Title case (dari case yang terkait) |
| `investigator` | string | Investigator name |
| `agency` | string | Agency name (dari case yang terkait) |
| `person_name` | string/null | Person name (jika ada, null jika unknown person) |
| `updated_at` | string | Tanggal update (format: DD/MM/YYYY) |

### Error Responses

#### 400 Bad Request - Empty Evidence Number
```json
{
  "detail": "evidence_number cannot be empty when provided manually"
}
```

#### 400 Bad Request - Duplicate Evidence Number
```json
{
  "detail": "Evidence number '{evidence_number}' already exists for another evidence (ID: {existing_id})"
}
```

#### 400 Bad Request - Invalid File Type
```json
{
  "status": 400,
  "detail": "File type tidak didukung. Hanya file PDF dan Image yang diperbolehkan (extensions: pdf, jpg, jpeg, png, gif, bmp, webp)"
}
```

#### 400 Bad Request - Invalid Suspect Status
```json
{
  "detail": "Invalid suspect_status value: '{value}'. Valid values are: Witness, Reported, Suspected, Suspect, Defendant"
}
```

#### 404 Not Found - Evidence Not Found
```json
{
  "detail": "Evidence with ID {evidence_id} not found"
}
```

#### 404 Not Found - Case Not Found
```json
{
  "detail": "Case with ID {case_id} not found"
}
```

#### 404 Not Found - Suspect Not Found
```json
{
  "detail": "Suspect with ID {suspect_id} not found for this case"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Unexpected server error: {error_message}"
}
```

### Person/Suspect Handling Logic

#### 1. Jika `suspect_id` Disediakan
- Menggunakan suspect yang sudah ada dengan ID tersebut
- Jika `person_name` disediakan, update nama suspect tersebut
- Jika `suspect_status` disediakan, update status suspect tersebut
- Suspect harus terkait dengan case yang sama dengan evidence

#### 2. Jika `is_unknown_person = true`
- Jika evidence sudah memiliki `suspect_id`, update suspect tersebut menjadi unknown (name="Unknown", is_unknown=true, status=null)
- Jika evidence belum memiliki `suspect_id`, cari unknown suspect untuk case tersebut
- Jika tidak ada unknown suspect, buat unknown suspect baru
- Field `person_name` dan `suspect_status` akan diabaikan

#### 3. Jika `person_name` Disediakan (tanpa `suspect_id` dan `is_unknown_person`)
- Cari suspect dengan nama tersebut untuk case yang sama
- Jika ditemukan, gunakan suspect tersebut dan update status jika `suspect_status` disediakan
- Jika tidak ditemukan, buat suspect baru dengan nama dan status yang disediakan

### File Upload

- **Allowed Extensions**: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`
- **File Storage**: File disimpan di `data/evidence/` dengan format `evidence_{timestamp}_{evidence_number}.{extension}`
- **File Metadata**: Sistem akan menghitung file size, file hash (SHA256), file type, dan file extension
- **File Replacement**: Jika file baru diupload, file lama akan digantikan (file path akan diupdate)

### Evidence Number Validation

- Evidence number harus unique
- Jika evidence number yang diupdate sudah digunakan oleh evidence lain, akan return error 400
- Jika evidence number sama dengan yang sudah ada (tidak berubah), tidak akan error

### Notes

1. **Partial Update**: Semua field adalah optional. Hanya field yang dikirim yang akan diupdate.

2. **Person/Suspect Priority**:
   - `suspect_id` memiliki prioritas tertinggi
   - `is_unknown_person` memiliki prioritas kedua
   - `person_name` memiliki prioritas terendah

3. **Unknown Person Behavior**:
   - Ketika `is_unknown_person = true`, sistem akan mengupdate suspect yang sudah terhubung menjadi unknown (jika ada)
   - Ini mencegah pembuatan duplicate unknown suspect records

4. **Case Log**: Update evidence akan membuat case log dengan action "Edit" yang mencatat perubahan.

5. **File Upload**:
   - File akan diupload dan disimpan di server
   - File path akan diupdate di database
   - File lama tidak dihapus (dapat dihapus manual jika diperlukan)

6. **Date Format**: 
   - `updated_at` dalam response menggunakan format `DD/MM/YYYY`
   - Timestamp di database menggunakan timezone Indonesia

