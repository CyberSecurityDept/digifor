# API Contract - Update Evidence

## Update Evidence

**Endpoint:** `PUT /api/v1/evidence/update-evidence/{evidence_id}`

**Description:** Update evidence information. All fields are optional (partial update). Supports file upload for evidence files. **Endpoint ini digunakan dari form "Edit Evidence"**. **Full Access**: All roles can update all evidence. No filtering or access restrictions.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data` (untuk upload file) atau `application/x-www-form-urlencoded`

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | **Yes** | Evidence ID yang akan di-update |

### Request Body (form-data, all fields optional)
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | No | Case ID (jika ingin mengubah case yang terkait) |
| `evidence_number` | string | No | Evidence number (jika disediakan, tidak boleh kosong) |
| `title` | string | No | Evidence title |
| `type` | string | No | Evidence type name (text input dari form UI). **Jika disediakan, sistem akan mencari atau membuat EvidenceType baru secara otomatis** |
| `source` | string | No | Evidence source: "Handphone", "SSD", "Harddisk", "PC", "Laptop", "DVR" |
| `evidence_file` | file | No | Evidence file upload. **Hanya file PDF dan Image yang diperbolehkan** (extensions: `pdf`, `jpg`, `jpeg`, `png`, `gif`, `bmp`, `webp`). File akan disimpan ke `data/evidence/` directory dengan SHA256 hash |
| `evidence_summary` | string | No | Evidence summary/description (disimpan ke field `description` di database) |
| `investigator` | string | No | Investigator name (who collected/analyzed the evidence) |
| `person_name` | string | Conditional | Person of interest name. **Hanya digunakan jika `is_unknown_person = false` (radio button "Person Name" dipilih di UI)**. Jika disediakan dan `suspect_id` tidak disediakan, sistem akan mencari existing suspect dengan nama tersebut. Jika tidak ditemukan, sistem akan otomatis membuat suspect baru dengan nama tersebut dan link evidence_number ke suspect tersebut. **Jika `is_unknown_person = true`, field ini akan diabaikan** |
| `suspect_status` | string | Conditional | Suspect status: "Witness", "Reported", "Suspected", "Suspect", "Defendant" (must be selected from UI, no default). **Hanya digunakan jika `is_unknown_person = false` (radio button "Person Name" dipilih)**. **Jika `is_unknown_person = true`, field ini akan diabaikan** |
| `is_unknown_person` | boolean/string | No | Flag yang menandakan apakah person tersebut unknown/tidak diketahui. **Dapat dikirim sebagai boolean (`true`/`false`) atau string (`"true"`/`"false"`)**. **Jika `true` (radio button "Unknown Person" dipilih di UI):** Sistem akan update suspect yang sudah terhubung menjadi unknown (jika evidence sudah memiliki suspect_id), atau mencari/membuat suspect "Unknown" baru. Field `person_name` dan `suspect_status` akan diabaikan. **Jika `false` dan `person_name` disediakan, suspect akan diupdate menjadi known person dengan nama dan status yang disediakan** |
| `suspect_id` | integer | No | Suspect ID untuk memilih suspect tertentu. **Jika `suspect_id` disediakan, evidence akan ter-link ke suspect dengan `suspect_id` tersebut (harus merupakan suspect dengan `case_id` yang sama). Jika `person_name` dan/atau `suspect_status` juga disediakan, suspect tersebut akan di-update dengan nilai baru (tidak membuat suspect baru)** |

### Request Examples

#### Example 1: Update dengan is_unknown_person = true
```http
PUT /api/v1/evidence/update-evidence/1
Authorization: Bearer <token>
Content-Type: multipart/form-data

case_id: 1
evidence_number: 438343040304
type: File
source: Handphone
evidence_file: [binary_file]
evidence_summary: Evidence dari unknown person 1.....
investigator: Solehun
is_unknown_person: true
```

#### Example 2: Update dengan is_unknown_person = false dan person_name
```http
PUT /api/v1/evidence/update-evidence/1
Authorization: Bearer <token>
Content-Type: multipart/form-data

case_id: 1
evidence_number: 438343040304
type: File
source: Handphone
evidence_file: [binary_file]
evidence_summary: Evidence dari unknown person 1.....
investigator: Solehun
is_unknown_person: false
person_name: Raka
suspect_status: Witness
```

### Success Response (200 OK)

#### Response ketika is_unknown_person = true
```json
{
  "status": 200,
  "message": "Evidence updated successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "438343040304",
    "source": "Handphone",
    "file_path": "data/evidence/evidence_20251126_114157_438343040304.jpeg",
    "description": "Evidence dari unknown person 1.....",
    "title": "pelari tercepat sepanjang jalan",
    "investigator": "Solehun",
    "agency": "Agen Cabe",
    "person_name": null,
    "updated_at": "26/11/2025"
  }
}
```

#### Response ketika is_unknown_person = false dan person_name disediakan
```json
{
  "status": 200,
  "message": "Evidence updated successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "438343040304",
    "source": "Handphone",
    "file_path": "data/evidence/evidence_20251126_114157_438343040304.jpeg",
    "description": "Evidence dari unknown person 1.....",
    "title": "pelari tercepat sepanjang jalan",
    "investigator": "Solehun",
    "agency": "Agen Cabe",
    "person_name": "Raka",
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
| `person_name` | string/null | Person name dari suspect yang terhubung. **Akan `null` jika suspect adalah unknown person (`is_unknown = true`)**. Akan berisi nama suspect jika suspect adalah known person (`is_unknown = false`) |
| `updated_at` | string | Tanggal update (format: DD/MM/YYYY) |

### Person/Suspect Handling Logic

#### 1. Jika `suspect_id` Disediakan
- Menggunakan suspect yang sudah ada dengan ID tersebut
- Jika `person_name` disediakan, update nama suspect tersebut dan set `is_unknown = false`
- Jika `suspect_status` disediakan, update status suspect tersebut
- Suspect harus terkait dengan case yang sama dengan evidence
- Tidak akan membuat suspect baru

#### 2. Jika `is_unknown_person = true`
- **Jika evidence sudah memiliki `suspect_id`:**
  - Update suspect yang sudah terhubung menjadi unknown (set `name = "Unknown"`, `is_unknown = true`, `status = null`)
  - **Suspect yang sama akan diupdate, bukan membuat record baru** (mencegah duplicate records)
  - `suspect_id` tetap sama, tidak berubah
- **Jika evidence belum memiliki `suspect_id`:**
  - Cari unknown suspect untuk case tersebut (yang paling baru berdasarkan `id DESC`)
  - Jika ditemukan, link evidence ke unknown suspect tersebut
  - Jika tidak ditemukan, buat unknown suspect baru
- Field `person_name` dan `suspect_status` akan diabaikan (tidak digunakan)
- **Response `person_name` akan menjadi `null`** karena suspect adalah unknown

#### 3. Jika `is_unknown_person = false` dan `person_name` Disediakan
- **Jika evidence sudah memiliki `suspect_id`:**
  - Update suspect yang sudah terhubung menjadi known person (set `name = person_name`, `is_unknown = false`, `status = suspect_status` jika disediakan)
  - **Suspect yang sama akan diupdate, bukan membuat record baru** (mengubah dari unknown menjadi known atau mengupdate data known person)
  - `suspect_id` tetap sama, tidak berubah
- **Jika evidence belum memiliki `suspect_id`:**
  - Cari suspect dengan nama tersebut untuk case yang sama
  - Jika ditemukan, gunakan suspect tersebut dan update status jika `suspect_status` disediakan
  - Jika tidak ditemukan, buat suspect baru dengan nama dan status yang disediakan
- **Response `person_name` akan berisi nama suspect** karena suspect adalah known person

#### 4. Jika Hanya `person_name` Disediakan (tanpa `suspect_id` dan `is_unknown_person`)
- Cari suspect dengan nama tersebut untuk case yang sama
- Jika ditemukan, gunakan suspect tersebut dan update status jika `suspect_status` disediakan
- Jika tidak ditemukan, buat suspect baru dengan nama dan status yang disediakan
- Suspect akan dibuat sebagai known person (`is_unknown = false`)

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

#### 401 Unauthorized
```json
{
  "status": 401,
  "message": "Invalid token",
  "data": null
}
```

#### 500 Internal Server Error
```json
{
  "status": 500,
  "detail": "Unexpected server error: {error_message}"
}
```

### Notes

1. **Partial Update**: Semua field adalah optional. Hanya field yang dikirim yang akan diupdate.

2. **Person/Suspect Priority**:
   - `suspect_id` memiliki prioritas tertinggi
   - `is_unknown_person` memiliki prioritas kedua
   - `person_name` memiliki prioritas terendah

3. **Unknown Person Behavior**:
   - Ketika `is_unknown_person = true`, sistem akan mengupdate suspect yang sudah terhubung menjadi unknown (jika ada)
   - Ini mencegah pembuatan duplicate unknown suspect records
   - Jika evidence sudah memiliki suspect_id, suspect tersebut akan diupdate menjadi unknown, bukan membuat record baru
   - **Transisi antara unknown dan known person**: 
     - Jika evidence sebelumnya terhubung ke known person dan diupdate menjadi `is_unknown_person = true`, suspect yang sama akan diupdate menjadi unknown
     - Jika evidence sebelumnya terhubung ke unknown person dan diupdate menjadi `is_unknown_person = false` dengan `person_name`, suspect yang sama akan diupdate menjadi known person
   - **Response `person_name` akan dinamis**: `null` jika unknown, nama suspect jika known

4. **Case Log**: Update evidence akan membuat case log dengan action "Edit" yang mencatat perubahan.

5. **File Upload**:
   - File akan diupload dan disimpan di server
   - File path akan diupdate di database
   - File lama tidak dihapus (dapat dihapus manual jika diperlukan)
   - File disimpan dengan format: `evidence_{timestamp}_{evidence_number}.{extension}`

6. **Date Format**: 
   - `updated_at` dalam response menggunakan format `DD/MM/YYYY`
   - Timestamp di database menggunakan timezone Indonesia

7. **Evidence Number Validation**:
   - Evidence number harus unique
   - Jika evidence number yang diupdate sudah digunakan oleh evidence lain, akan return error 400
   - Jika evidence number sama dengan yang sudah ada (tidak berubah), tidak akan error

8. **Evidence Type**:
   - Jika `type` disediakan, sistem akan mencari EvidenceType dengan nama tersebut
   - Jika tidak ditemukan, sistem akan otomatis membuat EvidenceType baru

9. **is_unknown_person Parsing**:
   - Field `is_unknown_person` dapat dikirim sebagai boolean (`true`/`false`) atau string (`"true"`/`"false"`)
   - Sistem akan otomatis mengkonversi string ke boolean jika diperlukan
   - String `"true"`, `"1"`, atau `"yes"` akan dikonversi menjadi boolean `true`
   - String lainnya akan dikonversi menjadi boolean `false`

10. **Database Transaction**:
    - Semua perubahan suspect dan evidence dilakukan dalam satu transaksi
    - Commit dilakukan setelah semua perubahan selesai untuk memastikan konsistensi data
    - Jika terjadi error, semua perubahan akan di-rollback

