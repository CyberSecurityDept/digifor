# Evidence Management & PDF Export API Contract

## Important Notes

### Evidence Model Changes
- **Removed:** `EvidenceType` table and `evidence_type_id` ForeignKey field
- **Added:** `source` field (String, nullable) - Evidence source
- **Added:** `evidence_type` field (String, nullable) - Evidence type
- Both `source` and `evidence_type` are now direct string fields in the `Evidence` model, not ForeignKey relationships

### Field Mapping
- Form parameter `source` → `Evidence.source` field (can be set during create)
- `Evidence.evidence_type` field is not set during create (will be null), can be updated later via update endpoint
- Both fields are optional and can be null

---

## Evidence Detail PDF Export

### Endpoint
`GET /api/v1/evidence/export-evidence-detail-pdf/{evidence_id}`

### Description
Export detail evidence secara lengkap sebagai dokumen PDF. PDF mencakup informasi evidence, case terkait, suspect, chain of custody, acquisition steps, preparation tools & hypothesis, extraction file details, dan analysis results. Dokumen memiliki format profesional dengan header dan footer di setiap halaman, pagination yang benar, dan layout yang terorganisir sesuai dengan standar digital forensics reporting.

**Access Control:** Requires authentication. All authenticated users can export PDF for evidence they have access to.

### Headers
```
Authorization: Bearer <access_token>
```

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID Evidence yang akan di-export |

### Response (200 OK)
Endpoint ini mengembalikan file PDF sebagai binary response dengan HTTP status code `200 OK` dan Content-Type `application/pdf`. File PDF akan di-download sebagai attachment dengan nama file yang unik.

**Status Code:** `200 OK`

**Response Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="evidence_detail_{evidence_id}_{timestamp}.pdf"
```

**Nama File Format:** `evidence_detail_{evidence_id}_{YYYYMMDD_HHMMSS}.pdf`

**Contoh:** `evidence_detail_1_20251231_090000.pdf`

**Response Body:**
Response body berisi binary data PDF (bukan JSON). File akan otomatis di-download oleh browser/client.

### PDF Structure

#### Header (Setiap Halaman)
- **Logo:** Logo perusahaan di kiri atas (width: 175px, height: 30px)
- **Export Time:** "Exported: {date} {time} WIB" di kanan atas (font size: 10px, regular, weight: 400, color: #333333)
- Logo dan Export Time rata kiri dan rata kanan, vertikal aligned

#### Page 1 Content

**1. Case Information Section:**
- **Case Title:** Font size 20px, Bold, Weight 700
- **Case ID:** Font size 12px, Bold, Weight 700, Color: #333333
- **Case Related:** Font size 12px, Bold, Weight 700
- **Investigator:** Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Date Created:** Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Person Related:** Nama suspect terkait
- **Source:** Evidence source

**2. Summary Section:**
- **Title:** Background #CCCCCC, Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Content:** Evidence description dengan gambar di samping (jika tersedia)
  - Image size: 130px width x 78px height
  - Text: Font size 12px, Regular, Weight 400, Color: #0C0C0C, Justified

**3. Chain of Custody Section:**
- **Title:** Background #CCCCCC, Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Layout:** Horizontal table dengan 4 kolom:
  - Acquisition
  - Preparation
  - Extraction
  - Analysis
- **Data per kolom:**
  - Row 1: Custody type name
  - Row 2: Date & time (format: "DD Month YYYY, HH:MM")
  - Row 3: Investigator name

**4. Evidence Source Details:**
- Format terpisah dalam 3 baris:
  - "Evidence Source: {source}" (font size: 12px, Regular, Weight 400, Color: #0C0C0C)
  - "Evidence Type: {evidence_type}" (font size: 12px, Regular, Weight 400, Color: #0C0C0C)
  - "Evidence Detail: {evidence_detail}" (font size: 12px, Regular, Weight 400, Color: #0C0C0C)
- Setiap baris ditampilkan sebagai paragraph terpisah

**5. Acquisition Section (jika ada):**
- **Title:** Background #CCCCCC, Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Date & Investigator:** Date dan investigator di bawah title
- **Steps for Confiscating Evidence:**
  - **Title:** Background #CCCCCC
  - **Content:** List of steps dengan gambar
    - Image: 130px x 78px di kiri
    - Text: Deskripsi step di kanan
    - Layout: 30% image, 70% text

**6. Preparation Section (jika ada):**
- **Title:** Background #CCCCCC, Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Date & Investigator:** Date dan investigator di bawah title
- **Tools and Investigation Hypothesis Table:**
  - **Header:** Background #466086, Font size 12px, Regular, Weight 400, Color: #F4F6F8
  - **Columns:**
    - Tools (30% width)
    - Investigation Hypothesis (70% width)
  - **Rows:** Data dari custody report details

**7. Extraction Section (jika ada):**
- **Title:** Background #CCCCCC, Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Date & Investigator:** Date dan investigator di bawah title
- **File Details Table:**
  - **Header:** Background #466086, Font size 12px, Regular, Weight 400, Color: #F4F6F8
  - **Columns:**
    - File Size (30% width)
    - File Name (70% width)
  - **Rows:** Data dari extraction file details

**8. Analysis Section (jika ada):**
- **Title:** Background #CCCCCC, Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Date & Investigator:** Date dan investigator di bawah title
- **Investigation Hypothesis and Analysis Result Table:**
  - **Header:** Background #466086, Font size 12px, Regular, Weight 400, Color: #F4F6F8
  - **Columns:**
    - Investigation Hypothesis (50% width)
    - Analysis Result (50% width)
  - **Rows:** Data dari analysis results

**9. Summary Section (setelah setiap section):**
- **Title:** Background #CCCCCC, Font size 12px, Regular, Weight 400, Color: #0C0C0C
- **Content:** Evidence description (font size 12px, Regular, Weight 400, Color: #0C0C0C)

#### Footer (Setiap Halaman)
- **Left:** "{Case Title} - {Case ID}" (font size: 10px, Regular, Weight 400, Color: #333333)
- **Right:** "Page {current_page}" (font size: 12px, Regular, Weight 400, Color: #0C0C0C)

### Features
- **Multi-page Support:** PDF otomatis membuat halaman baru ketika konten melebihi satu halaman
- **Consistent Header/Footer:** Header dan footer ditampilkan di setiap halaman dengan informasi yang konsisten
- **Image Handling:** 
  - Gambar evidence otomatis di-resize ke 130x78px
  - Gambar steps di-resize ke 130x78px
  - Fallback ke placeholder jika gambar tidak ditemukan
- **Smart Layout:**
  - Chain of Custody ditampilkan dalam format horizontal (4 kolom)
  - Summary section ditampilkan setelah setiap custody section
  - Tabel dengan header yang konsisten
- **Data Handling:**
  - Menampilkan "N/A" untuk data yang tidak tersedia
  - Format tanggal konsisten (DD Month YYYY, HH:MM)
  - Penanganan error yang graceful untuk missing data

### Error Responses

**404 Not Found:**
```json
{
  "detail": "Evidence with ID {evidence_id} not found"
}
```

**404 Not Found (Case):**
```json
{
  "detail": "Case not found for evidence {evidence_id}"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to export evidence detail PDF: {error_message}"
}
```

### Example Request

**cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/evidence/export-evidence-detail-pdf/1" \
  -H "Authorization: Bearer {access_token}" \
  -o evidence_detail_1.pdf
```

**HTTP Request:**
```
GET /api/v1/evidence/export-evidence-detail-pdf/1
Authorization: Bearer {access_token}
```

**JavaScript (Fetch):**
```javascript
fetch('http://localhost:8000/api/v1/evidence/export-evidence-detail-pdf/1', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer {access_token}'
  }
})
.then(response => response.blob())
.then(blob => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'evidence_detail_1.pdf';
  a.click();
});
```

**Python (requests):**
```python
import requests

url = "http://localhost:8000/api/v1/evidence/export-evidence-detail-pdf/1"
headers = {
    "Authorization": "Bearer {access_token}"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    with open("evidence_detail_1.pdf", "wb") as f:
        f.write(response.content)
    print("PDF downloaded successfully")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### Notes
- PDF di-generate menggunakan data dari endpoint `GET /api/v1/evidence/{evidence_id}/detail`
- Custody reports diurutkan berdasarkan `created_at` ascending
- Format tanggal menggunakan timezone WIB (UTC+7)
- Gambar diambil dari berbagai lokasi yang mungkin:
  - Absolute path (jika file_path adalah absolute)
  - `{UPLOAD_DIR}/{file_path}`
  - `data/uploads/{file_path}`
  - `data/evidence/{filename}`
- PDF cocok untuk official reports dan dokumentasi forensik
- File PDF disimpan di `{REPORTS_DIR}` dengan nama unik berdasarkan timestamp
- Response adalah binary PDF file, bukan JSON

### Related Endpoints
- `GET /api/v1/evidence/{evidence_id}/detail` - Get evidence detail data
- `POST /api/v1/evidence/create-evidence` - Create new evidence
- `PUT /api/v1/evidence/update-evidence/{evidence_id}` - Update evidence
- `GET /api/v1/evidence/{evidence_id}/custody` - Get custody reports
- `POST /api/v1/evidence/{evidence_id}/custody/acquisition` - Create acquisition report
- `POST /api/v1/evidence/{evidence_id}/custody/preparation` - Create preparation report
- `POST /api/v1/evidence/{evidence_id}/custody/extraction` - Create extraction report
- `POST /api/v1/evidence/{evidence_id}/custody/analysis` - Create analysis report

---

## Evidence Management API

### Create Evidence

**Endpoint:** `POST /api/v1/evidence/create-evidence`

**Description:** Create a new evidence item and associate it with a case. Supports file upload and can be associated with a person of interest.

**Access Control:** Requires authentication. All authenticated users can create evidence for all cases.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `case_id` | integer | Yes | Case ID where evidence will be added |
| `evidence_number` | string | No | Evidence number (optional - can be generated automatically or manually input) |
| `title` | string | No | Evidence title (optional - defaults to case title) |
| `source` | string | No | Evidence source (will be saved to `source` field) |
| `evidence_file` | file | No | Evidence file (PDF or Image: jpg, jpeg, png, gif, bmp, webp) |
| `evidence_summary` | string | No | Evidence description/summary |
| `investigator` | string | Yes | Investigator name |
| `person_name` | string | No | Person name (required if `is_unknown_person` is false) |
| `suspect_status` | string | No | Suspect status (required if `is_unknown_person` is false) |
| `is_unknown_person` | boolean | No | Whether person is unknown (default: false) |
| `suspect_id` | integer | No | Existing suspect ID to link evidence to |

**Note:** Field `evidence_type` will be set to `null` when creating evidence. It can be updated later using the update endpoint.

**Response (201 Created):**
```json
{
  "status": 201,
  "message": "Evidence created successfully",
  "data": {
    "id": 1,
    "case_id": 1,
    "evidence_number": "EVID-1-20251124-0001",
    "source": "Mobile Phone",
    "file_path": "data/evidence/evidence_20251124_162102_EVID-1-20251124-0001.jpeg",
    "description": "Evidence description",
    "title": "Case Title",
    "investigator": "Solehun",
    "agency": "Agency Name",
    "person_name": "Person Name",
    "created_at": "24/11/2025"
  }
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "status": 400,
  "detail": "evidence_number cannot be empty when provided manually"
}
```

**404 Not Found:**
```json
{
  "status": 404,
  "detail": "Case with ID {case_id} not found"
}
```

---

### Get Evidence Detail

**Endpoint:** `GET /api/v1/evidence/{evidence_id}/detail`

**Description:** Get comprehensive evidence detail including case, suspect, custody logs, and custody reports.

**Access Control:** Requires authentication. All authenticated users can access evidence details.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID Evidence yang akan diambil |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": 1,
    "evidence_number": "EVID-1-20251124-0001",
    "title": "Evidence Title",
    "description": "Evidence description",
    "suspect_name": "Suspect Name",
    "case_name": "Case Name",
    "source": "Mobile Phone",
    "evidence_type": "Digital Device",
    "investigator": "Solehun",
    "notes": null,
    "created_at": "2025-11-24T16:21:02.027123+07:00",
    "updated_at": "2025-11-24T16:21:02.027123+07:00",
    "custody_logs": [
      {
        "id": 1,
        "custody_type": "acquisition",
        "notes": "Notes",
        "created_by": "User",
        "created_at": "2025-11-24T16:21:02.027123+07:00"
      }
    ],
    "custody_reports": [
      {
        "id": 1,
        "custody_type": "acquisition",
        "investigator": "Solehun",
        "location": "Location",
        "notes": "Notes",
        "details": {},
        "evidence_source": "Source",
        "evidence_type": "Type",
        "evidence_detail": "Detail",
        "created_at": "2025-11-24T16:21:02.027123+07:00",
        "updated_at": "2025-11-24T16:21:02.027123+07:00"
      }
    ]
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

---

### Update Evidence

**Endpoint:** `PUT /api/v1/evidence/update-evidence/{evidence_id}`

**Description:** Update evidence information including source, evidence_type, description, and file.

**Access Control:** Requires authentication. All authenticated users can update evidence.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `evidence_id` | integer | Yes | ID Evidence yang akan di-update |

**Request Body (form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence_number` | string | No | Evidence number |
| `type` | string | No | Evidence type (will update `evidence_type` field) |
| `source` | string | No | Evidence source (will update `source` field) |
| `evidence_summary` | string | No | Evidence description |
| `investigator` | string | No | Investigator name |
| `evidence_file` | file | No | New evidence file |
| `person_name` | string | No | Person name |
| `suspect_status` | string | No | Suspect status |
| `is_unknown_person` | boolean | No | Whether person is unknown |
| `suspect_id` | integer | No | Suspect ID to link evidence to |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence updated successfully",
  "data": {
    "id": 1,
    "evidence_number": "EVID-1-20251124-0001",
    "source": "Updated Source",
    "evidence_type": "Updated Type",
    "description": "Updated description"
  }
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Evidence with ID {evidence_id} not found",
  "data": null
}
```

---

### Get Evidence List

**Endpoint:** `GET /api/v1/evidence/get-evidence-list`

**Description:** Get paginated list of evidence with search and sorting capabilities.

**Access Control:** Requires authentication. All authenticated users can access evidence list.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `skip` | integer | No | Number of records to skip (default: 0) |
| `limit` | integer | No | Number of records to return (default: 10, max: 100) |
| `search` | string | No | Search term (searches in evidence_number, title, description) |
| `sort_by` | string | No | Field to sort by (valid: 'created_at', 'id') |
| `sort_order` | string | No | Sort order (valid: 'asc', 'desc') |

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence list retrieved successfully",
  "data": [
    {
      "id": 1,
      "case_id": 1,
      "evidence_number": "EVID-1-20251124-0001",
      "title": "Case Title",
      "investigator": "Solehun",
      "agency": "Agency Name",
      "created_at": "24/11/2025"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 10
}
```

---

### Get Evidence Summary

**Endpoint:** `GET /api/v1/evidence/get-evidence-summary`

**Description:** Get summary statistics of evidence.

**Access Control:** Requires authentication. All authenticated users can access evidence summary.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Evidence summary retrieved successfully",
  "data": {
    "total_evidence": 100,
    "pending_analysis": 50,
    "in_progress": 30,
    "completed": 20
  }
}
```

---

## Case Detail PDF Export

### Endpoint
`GET /api/v1/cases/export-case-details-pdf/{case_id}`

### Description
Export detail kasus secara lengkap sebagai dokumen PDF. PDF mencakup informasi kasus, person of interest beserta evidence mereka, dan catatan kasus. Dokumen memiliki format profesional dengan header dan footer di setiap halaman, pagination yang benar, dan layout yang terorganisir.

**Access Control:** Requires authentication. All authenticated users can export PDF for all cases.

### Headers
```
Authorization: Bearer <access_token>
```

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `case_id` | integer | Yes | ID Case yang akan di-export |

### Response (200 OK)
Endpoint ini mengembalikan file PDF sebagai binary response dengan HTTP status code `200 OK` dan Content-Type `application/pdf`.

**Status Code:** `200 OK`

**Response Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="case_detail_{case_number}_{timestamp}.pdf"
```

**Nama File Format:** `case_detail_{case_number}_{YYYYMMDD_HHMMSS}.pdf`

**Contoh:** `case_detail_34124325_20251231_090000.pdf`

### PDF Structure

#### Header (Setiap Halaman)
- Logo perusahaan (175px x 30px)
- Case title (font size: 20px, Bold, Weight 700)
- Case ID (font size: 12px, Bold, Weight 700, Color: #333333)
- Investigator & Date Created (font size: 12px, Regular, Weight 400, Color: #0C0C0C)
- Export time (font size: 10px, Regular, Weight 400, Color: #333333)

#### Content Sections
1. **Case Description:** Background #CCCCCC, font size 12px
2. **Person of Interest:** 
   - Title dengan background #CCCCCC
   - Info table: Name, Status, Total Evidence
   - Evidence table dengan gambar (130px x 78px)
3. **Notes:** Background #F2F2F2, font size 12px

#### Footer (Setiap Halaman)
- Left: "{Case Title} - {Case ID}" (font size: 10px, Color: #333333)
- Right: "Page {current_page}" (font size: 12px, Color: #0C0C0C)

### Error Responses

**404 Not Found:**
```json
{
  "status": 404,
  "message": "Case with ID {case_id} not found",
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

**500 Internal Server Error:**
```json
{
  "status": 500,
  "message": "Failed to export case detail PDF: {error_message}",
  "data": null
}
```

### Example Request
```
GET /api/v1/cases/export-case-details-pdf/1
Authorization: Bearer {access_token}
```

---

## Suspect Detail PDF Export

### Endpoint
`GET /api/v1/suspects/export-suspect-detail-pdf/{suspect_id}`

### Description
Export detail suspect secara lengkap sebagai dokumen PDF. PDF mencakup informasi suspect, case terkait, dan evidence yang terkait dengan suspect tersebut.

**Access Control:** Requires authentication. All authenticated users can export PDF for suspects they have access to.

### Headers
```
Authorization: Bearer <access_token>
```

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `suspect_id` | integer | Yes | ID Suspect yang akan di-export |

### Response (200 OK)
Endpoint ini mengembalikan file PDF sebagai binary response dengan HTTP status code `200 OK` dan Content-Type `application/pdf`.

**Status Code:** `200 OK`

**Response Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="suspect_detail_{suspect_id}_{timestamp}.pdf"
```

### PDF Structure

#### Header (Setiap Halaman)
- Logo perusahaan (175px x 30px)
- Suspect name (font size: 20px, Bold, Weight 700)
- Case Related (font size: 12px, Bold, Weight 700)
- Investigator & Date Created (font size: 12px, Regular, Weight 400, Color: #0C0C0C)
- Export time (font size: 10px, Regular, Weight 400, Color: #333333)

#### Content Sections
1. **Suspect Information:** Name, Status, Total Evidence
2. **Evidence Table:**
   - Columns: Picture (130px x 78px), Evidence ID, Summary
   - Header: Font size 12px, Regular, Weight 400, Color: #F4F6F8
   - Values: Font size 12px, Regular, Weight 400, Color: #0C0C0C
3. **Notes:** Background #F2F2F2, font size 12px

#### Footer (Setiap Halaman)
- Left: "{Case Name} - {Suspect Name}" (font size: 10px, Color: #333333)
- Right: "Page {current_page}" (font size: 12px, Color: #0C0C0C)

### Error Responses

**404 Not Found:**
```json
{
  "detail": "Suspect with ID {suspect_id} not found"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to export suspect detail PDF: {error_message}"
}
```

### Example Request
```
GET /api/v1/suspects/export-suspect-detail-pdf/1
Authorization: Bearer {access_token}
```

---

## Common PDF Export Features

### Image Handling
- Automatic resizing to fixed dimensions (130px x 78px for evidence images)
- Support for multiple image formats (PNG, JPEG, etc.)
- Fallback to placeholder if image not found
- Image path resolution from multiple possible locations

### Page Management
- Automatic page breaks
- Consistent headers and footers on all pages
- Page numbering
- Smart content flow to prevent awkward page breaks

### Data Formatting
- Consistent date/time formatting (WIB timezone)
- Proper handling of missing/null data
- Professional typography and spacing
- Color-coded sections for better readability

### File Naming
All exported PDFs follow the pattern: `{type}_detail_{id}_{timestamp}.pdf`
- `{type}`: evidence, case, atau suspect
- `{id}`: ID dari entity yang di-export
- `{timestamp}`: Format `YYYYMMDD_HHMMSS`

### Storage
PDF files are stored in the directory specified by `REPORTS_DIR` configuration, typically:
- `app/data/reports/` (development)
- `/var/digifor/reports/` (production)

