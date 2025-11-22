# API Contract Documentation - Suspect Notes Management

## Digital Forensics Analysis Platform - Backend API

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**API Version:** `/api/v1`

---

## 📋 Table of Contents

1. [Save Suspect Notes](#1-save-suspect-notes)
2. [Edit Suspect Notes](#2-edit-suspect-notes)

---

## 1. Save Suspect Notes

**Endpoint:** `POST /api/v1/persons/save-suspect-notes/{suspect_id}`

**Description:** Save new notes for a suspect. **Endpoint ini digunakan untuk menyimpan catatan baru tentang suspect**. Endpoint ini hanya dapat digunakan untuk menyimpan notes baru jika suspect belum memiliki notes. Jika notes sudah ada, gunakan endpoint `PUT /api/v1/persons/edit-suspect-notes/{suspect_id}` untuk mengupdate notes yang sudah ada.

Notes akan disimpan di field `notes` dari evidence pertama yang terhubung dengan suspect sebagai JSON dengan key `suspect_notes`. Evidence dipilih berdasarkan urutan ID (sorted by ID ascending) untuk memastikan konsistensi. Jika tidak ada evidence yang terhubung dengan suspect, endpoint akan mengembalikan error. 

**Access Control:** User harus memiliki akses ke case yang terkait dengan suspect. Jika suspect memiliki `case_id`, sistem akan memeriksa apakah user memiliki permission untuk mengakses case tersebut.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | **Yes** | Suspect ID |

**Request Body (JSON):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notes` | string | **Yes** | Notes text to save for the suspect (cannot be empty) |

**Example Request:**
```
POST /api/v1/persons/save-suspect-notes/1
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "notes": "Dokumentasi detail, isolasi jaringan, serta pencatatan chain of custody sangat penting untuk memastikan integritas bukti GPS handphone dan dapat dipertanggungjawabkan di pengadilan."
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Suspect notes saved successfully",
  "data": {
    "suspect_id": 1,
    "notes": "Dokumentasi detail, isolasi jaringan, serta pencatatan chain of custody sangat penting untuk memastikan integritas bukti GPS handphone dan dapat dipertanggungjawabkan di pengadilan."
  }
}
```

**Error Responses:**

**400 Bad Request (No evidence found):**
```json
{
  "status": 400,
  "message": "Cannot save notes: No evidence found for this suspect. Please create evidence first."
}
```

**400 Bad Request (Notes already exist):**
```json
{
  "status": 400,
  "message": "Notes already exist for this suspect. Use PUT /api/v1/persons/edit-suspect-notes/{suspect_id} to update existing notes."
}
```

**400 Bad Request (Notes cannot be empty):**
```json
{
  "status": 400,
  "message": "Notes cannot be empty"
}
```

**403 Forbidden (No permission to access case):**
```json
{
  "status": 403,
  "message": "You do not have permission to access this case"
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID 1 not found"
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

**Notes:**
- Endpoint ini hanya untuk **menyimpan notes baru**. Jika notes sudah ada, endpoint akan mengembalikan error 400
- Notes akan disimpan di field `notes` dari evidence pertama yang terhubung dengan suspect (dipilih berdasarkan ID ascending untuk konsistensi)
- Notes disimpan sebagai JSON dengan key `suspect_notes`
- Jika evidence sudah memiliki notes (dict atau string), notes baru akan ditambahkan sebagai `suspect_notes`, tetapi notes lain di dalam dict tidak akan dihapus
- Endpoint ini secara otomatis membuat case log entry ketika notes di-save
- Notes yang disimpan akan muncul di endpoint `get-suspect-detail` di field `suspect_notes`
- Untuk melihat notes yang sudah disimpan, gunakan endpoint `GET /api/v1/suspects/get-suspect-detail/{suspect_id}`
- Untuk mengupdate notes yang sudah ada, gunakan endpoint `PUT /api/v1/persons/edit-suspect-notes/{suspect_id}`
- Sistem akan mencari evidence berdasarkan `suspect_id` dan `evidence_number` dari suspect, kemudian mengurutkan berdasarkan ID untuk memastikan evidence yang sama digunakan untuk menyimpan dan membaca notes

---

## 2. Edit Suspect Notes

**Endpoint:** `PUT /api/v1/persons/edit-suspect-notes/{suspect_id}`

**Description:** Edit existing notes for a suspect. **Endpoint ini digunakan untuk mengupdate catatan yang sudah ada tentang suspect**. Endpoint ini hanya dapat digunakan untuk mengupdate notes yang sudah ada. Jika notes belum ada, gunakan endpoint `POST /api/v1/persons/save-suspect-notes/{suspect_id}` untuk membuat notes baru.

Notes akan diupdate di field `notes` dari evidence pertama yang terhubung dengan suspect sebagai JSON dengan key `suspect_notes`. Evidence dipilih berdasarkan urutan ID (sorted by ID ascending) untuk memastikan konsistensi. Jika tidak ada evidence yang terhubung dengan suspect, endpoint akan mengembalikan error.

**Access Control:** User harus memiliki akses ke case yang terkait dengan suspect. Jika suspect memiliki `case_id`, sistem akan memeriksa apakah user memiliki permission untuk mengakses case tersebut.

**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | **Yes** | Suspect ID |

**Request Body (JSON):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notes` | string | **Yes** | Notes text to update for the suspect (cannot be empty) |

**Example Request:**
```
PUT /api/v1/persons/edit-suspect-notes/1
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "notes": "Updated notes: Dokumentasi detail telah diperbarui dengan informasi tambahan tentang isolasi jaringan dan chain of custody."
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Suspect notes updated successfully",
  "data": {
    "suspect_id": 1,
    "notes": "Updated notes: Dokumentasi detail telah diperbarui dengan informasi tambahan tentang isolasi jaringan dan chain of custody."
  }
}
```

**Error Responses:**

**400 Bad Request (No evidence found):**
```json
{
  "status": 400,
  "message": "Cannot edit notes: No evidence found for this suspect. Please create evidence first."
}
```

**400 Bad Request (No notes found):**
```json
{
  "status": 400,
  "message": "No notes found for this suspect. Use POST /api/v1/persons/save-suspect-notes/{suspect_id} to create new notes."
}
```

**400 Bad Request (Notes cannot be empty):**
```json
{
  "status": 400,
  "message": "Notes cannot be empty"
}
```

**403 Forbidden (No permission to access case):**
```json
{
  "status": 403,
  "message": "You do not have permission to access this case"
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Suspect with ID 1 not found"
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

**Notes:**
- Endpoint ini hanya untuk **mengupdate notes yang sudah ada**. Jika notes belum ada, endpoint akan mengembalikan error 400
- Notes akan diupdate di field `notes` dari evidence pertama yang terhubung dengan suspect (dipilih berdasarkan ID ascending untuk konsistensi)
- Notes disimpan sebagai JSON dengan key `suspect_notes`
- Notes baru akan menggantikan nilai `suspect_notes` yang lama, tetapi notes lain di dalam dict tidak akan dihapus
- Endpoint ini secara otomatis membuat case log entry ketika notes di-update
- Notes yang diupdate akan muncul di endpoint `get-suspect-detail` di field `suspect_notes` (menggunakan evidence yang sama untuk membaca notes)
- Untuk melihat notes yang sudah disimpan, gunakan endpoint `GET /api/v1/suspects/get-suspect-detail/{suspect_id}`
- Untuk membuat notes baru, gunakan endpoint `POST /api/v1/persons/save-suspect-notes/{suspect_id}`
- Sistem akan mencari evidence berdasarkan `suspect_id` dan `evidence_number` dari suspect, kemudian mengurutkan berdasarkan ID untuk memastikan evidence yang sama digunakan untuk menyimpan dan membaca notes

---

## 📝 Additional Information

### Notes Storage Structure

Notes disimpan di field `notes` dari Evidence model sebagai JSON dengan struktur berikut:

**Jika evidence.notes adalah dict:**
```json
{
  "suspect_notes": "Catatan tentang suspect...",
  "text": "Catatan lain tentang evidence..."
}
```

**Jika evidence.notes adalah string:**
Setelah save/edit, akan menjadi:
```json
{
  "suspect_notes": "Catatan tentang suspect...",
  "text": "String notes yang lama"
}
```

**Jika evidence.notes adalah null/empty:**
Setelah save, akan menjadi:
```json
{
  "suspect_notes": "Catatan tentang suspect..."
}
```

### Evidence Lookup Logic

Sistem akan mencari evidence untuk suspect dengan urutan berikut:
1. Mencari semua evidence yang memiliki `suspect_id` sama dengan suspect ID, diurutkan berdasarkan ID ascending
2. Jika suspect memiliki `evidence_number`, mencari semua evidence dengan `evidence_number` yang sama dan `case_id` yang sama, diurutkan berdasarkan ID ascending
3. Menggabungkan hasil dari kedua pencarian (menghindari duplikasi)
4. Mengurutkan semua evidence berdasarkan ID ascending untuk memastikan konsistensi
5. Menggunakan evidence pertama dari list yang sudah diurutkan untuk menyimpan/update notes

**Penting:** Urutan evidence berdasarkan ID memastikan bahwa evidence yang sama digunakan untuk menyimpan dan membaca notes, sehingga notes yang diupdate akan langsung terlihat di endpoint `get-suspect-detail`.

### Case Log

Setiap kali notes di-save atau di-edit, sistem akan secara otomatis membuat case log entry dengan:
- `action`: "Edit"
- `change_detail`: "Change: Added notes for suspect {suspect.name}" (untuk save) atau "Change: Updated notes for suspect {suspect.name}" (untuk edit)
- `changed_by`: Fullname atau email dari current user
- `status`: Status case saat ini

### Access Control

- User harus memiliki akses ke case yang terkait dengan suspect
- Jika suspect memiliki `case_id`, sistem akan memeriksa permission menggunakan `check_case_access()`
- Jika user tidak memiliki akses, endpoint akan mengembalikan 403 Forbidden

### Technical Implementation Details

**JSON Field Update:**
- Sistem menggunakan `flag_modified()` untuk memastikan SQLAlchemy mendeteksi perubahan pada field JSON
- Setelah update, sistem melakukan `db.flush()` dan `db.commit()` untuk memastikan perubahan tersimpan ke database
- `db.refresh()` digunakan untuk memastikan object memiliki data terbaru dari database

**Notes Reading:**
- Endpoint `get-suspect-detail` membaca notes dari evidence pertama yang terhubung dengan suspect
- Evidence dipilih menggunakan logika yang sama dengan endpoint save/edit (sorted by ID ascending)
- Notes dibaca dari field `notes` dengan prioritas key `suspect_notes`, fallback ke `text` jika `suspect_notes` tidak ada
- Jika `suspect.notes` sudah ada, sistem akan menggunakan notes dari suspect model terlebih dahulu

