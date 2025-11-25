# API Contract - Case Log Management

## 1. Get Case Logs

Mengambil daftar log untuk case tertentu dengan pagination.

### Endpoint
```
GET /api/v1/case-logs/case/logs/{case_id}
```

### Authentication
Required - Bearer Token

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | ID dari case yang akan diambil log-nya |

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | integer | No | 0 | Jumlah record yang akan di-skip (untuk pagination) |
| `limit` | integer | No | 10 | Jumlah maksimal record yang akan dikembalikan (1-100) |

### Request Example
```http
GET /api/v1/case-logs/case/logs/1?skip=0&limit=10
Authorization: Bearer <token>
```

### Success Response (200 OK)
```json
{
  "status": 200,
  "message": "Case logs retrieved successfully",
  "data": [
    {
      "id": 6,
      "case_id": 1,
      "action": "Re-open",
      "created_at": "25 November 2025, 22:02",
      "status": "Re-open",
      "notes": "Kasus dibuka kembali",
      "edit": [
        {
          "changed_by": "By: Admin Forensic",
          "change_detail": "Change: Adding Status Re-open"
        }
      ]
    },
    {
      "id": 5,
      "case_id": 1,
      "action": "Edit",
      "created_at": "25 November 2025, 21:43",
      "edit": [
        {
          "changed_by": "By: Admin Forensic",
          "change_detail": "Change: Case Name: testing update cases | testing update cases......"
        }
      ]
    },
    {
      "id": 4,
      "case_id": 1,
      "action": "Edit",
      "created_at": "25 November 2025, 21:43",
      "edit": [
        {
          "changed_by": "By: Admin Forensic",
          "change_detail": "Change: Adding person Andika"
        }
      ]
    },
    {
      "id": 1,
      "case_id": 1,
      "action": "Open",
      "created_at": "25 November 2025, 00:39",
      "status": "Open"
    }
  ],
  "total": 4,
  "page": 1,
  "size": 10
}
```

### Response Fields

#### Response Object
| Field | Type | Description |
|-------|------|-------------|
| `status` | integer | HTTP status code (200) |
| `message` | string | Pesan response |
| `data` | array | Array of case log objects |
| `total` | integer | Total jumlah log untuk case ini |
| `page` | integer | Halaman saat ini (calculated from skip/limit) |
| `size` | integer | Ukuran halaman (limit) |

#### Case Log Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | ID dari log |
| `case_id` | integer | Yes | ID dari case |
| `action` | string | Yes | Action yang dilakukan (Open, Edit, Closed, Re-open) |
| `created_at` | string | Yes | Tanggal dan waktu log dibuat (format: "DD Month YYYY, HH:MM") |
| `status` | string | No | Status case saat log dibuat (hanya untuk action Open, Closed, Re-open) |
| `notes` | string | No | Catatan tambahan (hanya muncul jika ada nilai) |
| `edit` | array | No | Array of edit details (hanya muncul untuk action Edit dan Re-open) |

#### Edit Item Object (dalam array `edit`)
| Field | Type | Description |
|-------|------|-------------|
| `changed_by` | string | User yang melakukan perubahan (format: "By: {user_name}") |
| `change_detail` | string | Detail perubahan (format: "Change: {field}: {old_value} \| {new_value}") |

### Action Types

#### 1. Action: "Open"
- Log dibuat saat case pertama kali dibuat
- Field yang muncul: `id`, `case_id`, `action`, `created_at`, `status`
- Tidak ada field `edit` atau `notes`

#### 2. Action: "Edit"
- Log dibuat saat ada perubahan pada case (field: case_number, title, description, main_investigator, agency, work_unit, notes)
- Field yang muncul: `id`, `case_id`, `action`, `created_at`, `edit`
- Field `edit` berisi array dengan `changed_by` dan `change_detail`
- Format `change_detail`: `"Change: {Field Name}: {old_value} | {new_value}"`
- Contoh: `"Change: Case Name: testing update cases | testing update cases......"`

#### 3. Action: "Closed"
- Log dibuat saat case ditutup
- Field yang muncul: `id`, `case_id`, `action`, `created_at`, `status`, `notes` (jika ada)

#### 4. Action: "Re-open"
- Log dibuat saat case dibuka kembali
- Field yang muncul: `id`, `case_id`, `action`, `created_at`, `status`, `notes` (jika ada), `edit`
- Field `edit` berisi array dengan `changed_by` (dari current user) dan `change_detail` (format: "Change: Adding Status {status}")

### Error Responses

#### 404 Not Found - Case Not Found
```json
{
  "detail": "Case with ID {case_id} not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Unexpected server error, please try again later"
}
```

---

## 2. Get Case Log Detail

Mengambil detail dari satu log tertentu.

### Endpoint
```
GET /api/v1/case-logs/log/{log_id}
```

### Authentication
Required - Bearer Token

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `log_id` | integer | Yes | ID dari log yang akan diambil |

### Request Example
```http
GET /api/v1/case-logs/log/5
Authorization: Bearer <token>
```

### Success Response (200 OK)
```json
{
  "status": 200,
  "message": "Case log detail retrieved successfully",
  "data": {
    "id": 5,
    "case_id": 1,
    "action": "Edit",
    "created_at": "25 November 2025, 21:43",
    "edit": [
      {
        "changed_by": "By: Admin Forensic",
        "change_detail": "Change: Case Name: testing update cases | testing update cases......"
      }
    ]
  }
}
```

### Response Fields

#### Response Object
| Field | Type | Description |
|-------|------|-------------|
| `status` | integer | HTTP status code (200) |
| `message` | string | Pesan response |
| `data` | object | Case log object |

#### Case Log Object
Struktur sama dengan Case Log Object pada Get Case Logs, namun hanya mengembalikan satu object.

### Error Responses

#### 404 Not Found - Log Not Found
```json
{
  "detail": "Case log not found"
}
```

#### 404 Not Found - Case Not Found
```json
{
  "detail": "Case with ID {case_id} not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Unexpected server error: {error_message}"
}
```

---

## 3. Update Case Log

Mengupdate log case (biasanya untuk mengubah status case).

### Endpoint
```
PUT /api/v1/case-logs/change-log/{case_id}
```

### Authentication
Required - Bearer Token

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | ID dari case yang log-nya akan diupdate |

### Request Body
```json
{
  "status": "Closed",
  "notes": "Case telah selesai ditangani"
}
```

### Request Body Schema
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | Status baru untuk case (Open, Closed, Re-open) |
| `notes` | string | Yes | Catatan wajib diisi saat update status |

### Request Example
```http
PUT /api/v1/case-logs/change-log/1
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "Closed",
  "notes": "Case telah selesai ditangani"
}
```

### Success Response (200 OK)
```json
{
  "status": 200,
  "message": "Case log updated successfully",
  "data": {
    "id": 7,
    "case_id": 1,
    "action": "Closed",
    "created_at": "25 November 2025, 22:15",
    "status": "Closed",
    "notes": "Case telah selesai ditangani"
  }
}
```

### Response Fields

#### Response Object
| Field | Type | Description |
|-------|------|-------------|
| `status` | integer | HTTP status code (200) |
| `message` | string | Pesan response |
| `data` | object | Updated case log object |

### Error Responses

#### 400 Bad Request - Invalid Status
```json
{
  "detail": "Invalid status value. Valid values are: Open, Closed, Re-open"
}
```

#### 400 Bad Request - Missing Notes
```json
{
  "detail": "Notes is required when updating case status"
}
```

#### 404 Not Found - Case Not Found
```json
{
  "detail": "Case with ID {case_id} not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Unexpected server error: {error_message}"
}
```

---

## Notes

1. **Pagination**: 
   - `skip` digunakan untuk skip records (offset)
   - `limit` maksimal 100 records per request
   - `page` dihitung dari `skip // limit + 1`

2. **Date Format**: 
   - Format tanggal menggunakan format Indonesia: "DD Month YYYY, HH:MM"
   - Contoh: "25 November 2025, 22:02"

3. **Edit Field**:
   - Field `edit` hanya muncul untuk action "Edit" dan "Re-open"
   - Format `change_detail` menggunakan pipe (`|`) sebagai separator antara old value dan new value
   - Contoh: `"Change: Case Name: old value | new value"`

4. **Changed By Field**:
   - Format selalu dimulai dengan "By: " diikuti nama user
   - Untuk action "Re-open", `changed_by` diambil dari current logged-in user
   - Untuk action "Edit", `changed_by` diambil dari database atau current user jika kosong

5. **Status Values**:
   - Valid status values: "Open", "Closed", "Re-open"
   - Case sensitive

6. **Notes Field**:
   - Field `notes` optional untuk action "Open"
   - Field `notes` wajib diisi untuk action "Closed" dan "Re-open" saat update via change-log endpoint

