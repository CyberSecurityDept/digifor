# Digital Forensics - API Contract Analytics

### Information

| PIC | Version | Last Modified |
| --- | --- | --- |
| Goto & Dwi | v1 | 4 November |

Change Log

| Description | Date |
| --- | --- |
| - Completed response structure for `GET /api/v1/analytics/get-all-analytic`.
- Added 3 new endpoints for **`Deep Communication Analytics**.`
- Updated the filter query value in the `/api/v1/analytics/get-files` endpoint from **"Deep Communication"** to **"Deep Communication Analytics"**.
- Change query parameter in the `/api/v1/analytic/{analytic_id}/export-pdf` | 4 November |

---

### Header

| Name | Value | Description |
| --- | --- | --- |
| `Authorization` | Bearer : `{{access_token}}` | **Authentication is required for all endpoint, `don’t forget to add Header in all endpoint`** |

---

## Authentication

All endpoints require authentication (implementation depends on your auth system).

### Login

**Endpoint**: `/api/v1/auth/login`

**Method** : `POST`

**Request Body**

```json
{
  "email": "admin@gmail.com",
  "password": "password"
}
```

**Response 200**

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
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiaWF0IjoxNzYyMTQzNzQyLCJ0eXBlIjoiYWNjZXNzIn0.SV8adpdLcK4PY7E5JsN9zpWewiuHdaI5l-QaGwB17KM"
  }
}
```

---

### Logout

**Endpoint**: `/api/v1/auth/logout`

**Method** : `POST`

**Headers**: `Authorization : Bearer {{token}}`

**Response 200**

```json
{
    "status": 200,
    "message": "Logout successful. All refresh tokens revoked.",
    "data": null
}
```

**ERROR RESPONSE AUTH**

**Response 401**

```json
{
  "status": 401,
  "message": "Unauthorized"
}
```

```json
{
  "status": 401,
  "message": "Invalid or expired refresh token"
}
```

```json
{
  "status": 401,
  "message": "Invalid credentials",
}
```

```json
{
  "status": 401,
  "message": "Invalid token type",
}
```

```json
{
  "status": 401,
  "message": "Expired token",
}
```

```json
{
  "status": 401,
  "message": "Invalid token",
}
```

---

## Report Analytics

### Export Analytics PDF

**Endpoint:**`/api/v1/analytic/{analytic_id}/export-pdf`

**Method :** `GET`

---

**Path Parameter:**

| Name | Type | Description | Required |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

---

**Query Parameters:**

| Name | Type | Description | Required |
| --- | --- | --- | --- |
| `person_name` | string | Used only for method **Deep Communication Analytics** | N |
| `device_id` | integer | Used only for method **Deep Communication Analytics** | N |
| `source` | string | Used for methods **Social Media Correlation** and **Deep Communication Analytics** | N |

---

**Response:**

Returns a **PDF file download** (content-type: `application/pdf`).

---

**Response 404 — Analytic Not Found**

```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

---

**Response 400 — No Linked Devices**

```json
{
  "status": 400,
  "message": "No devices linked to this analytic",
  "data": null
}
```

---

**Response 500 — Internal Server Error**

```json
{
  "status": 500,
  "message": "Failed to generate PDF: <error_message>",
  "data": null
}
```

```json
{
	"status": 500,
	"message": "Something Wrong",
	"data": null
}
```

---

### Save Summary

**Endpoint** : `/api/v1/analytic/{analytic_id}/save-summary`

**Method** : `POST`

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

**Request Body :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `summary` | string | - | Y |

**Response 200**

```json
{
  "status": 200,
  "message": "Summary saved successfully",
  "data": {
    "analytic_id": 12,
    "analytic_name": "Communication Correlation Report",
    "summary": "Analytic summary text here...",
    "updated_at": "2025-11-02 12:00:00"
  }
}
```

**Response 404**

```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

**Response 400**

```json
{
  "status": 400,
  "message": "Summary cannot be empty",
  "data": null
}
```

**Response 500**

```json
{
  "status": 500,
  "message": "Failed to save summary: Something Wrong",
  "data": null
}
```

---

### Edit Summary

**Endpoint** : `/api/v1/analytic/{analytic_id}/edit-summary`

**Method** : `PUT`

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

**Request Body :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `summary` | string | - | Y |

**Response 200**

```json
{
  "status": 200,
  "message": "Summary updated successfully",
  "data": {
    "analytic_id": 12,
    "analytic_name": "Communication Correlation Report",
    "summary": "Updated analytic summary text here...",
    "updated_at": "2025-11-02 12:00:00"
  }
}

```

**Response 404**

```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null}

```

**Response 400**

```json
{
  "status": 400,
  "message": "Summary cannot be empty",
  "data": null}

```

**Response 500**

```json
{
  "status": 500,
  "message": "Something Wrong",
  "data": null
}
```

---

## File Management

### Upload Data

**Endpoint** : `/api/v1/analytics/upload-data`

**Method** : `POST`

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `file` | file | The file to be uploaded (currently must be in `.sdp` format) | Y |
| `file_name` | string | The name of the uploaded file | Y |
| `notes` | string | Additional notes related to the file | Y |
| `type` | string | Type of device (e.g., Mobile Phone, SSD, Hard Drive, PC, Laptop, DVR) | Y |
| `tools` | string | Tools used (e.g., Magnet Axiom, Cellebrite, Oxygen, Encase) | Y |
| `method` | string | Analysis method (e.g., Deep Communication Analytics, Social Media Correlation, Contact Correlation, Hashfile Analytics) | Y |

**Allowed Values :**

| Field | Allowed Values |
| --- | --- |
| `type` | `Handphone`, `SSD`, `Harddisk`, `PC`, `Laptop`, `DVR` |
| `tools` | `Magnet Axiom`, `Cellebrite`, `Oxygen`, `Encase` |
| `method` | `Deep communication analytics`, `Social Media Correlation`, `Contact Correlation`, `Hashfile Analytics` |

**Validation Rules:**

- Only files with the `.sdp` extension are accepted
- Maximum file size: **100 MB**
- All form fields are required and must not be empty

**Response 200**

```json
{
  "status": 200,
  "message": "File uploaded, encrypted & parsed successfully",
  "data": {
    "upload_id": "upload_1730558981_8df7b3a1",
    "status_upload": "Pending",
    "upload_type": "data"
  }
}
```

**Response 400**

```json
{
  "status": 400,
  "message": "Only .sdp files are accepted. Please upload encrypted .sdp first"
}
```

**Response 400 (Invalid Method/Tools/Type)**

```json
{
  "status": 400,
  "message": "Invalid method. Must be one of: ['Deep communication analytics', 'Social Media Correlation', 'Contact Correlation', 'Hashfile Analytics']"
}
```

**Response 422**

```json
{
  "status": 422,
  "message": "Field 'file_name' is required and cannot be empty",
  "error_field": "file_name"
}
```

**Response 500**

```json
{
  "status": 500,
  "message": "Upload error: Something Wrong"
}
```

---

### Upload Progress

**Endpoint** : `/api/v1/analytics/upload-progress`

**Method** : `GET`

**Query Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `upload_id` | string | ID dari proses upload yang ingin dicek | Y |
| `type` | string | Jenis upload (`data` atau `apk`) | N (default = `data`) |

**Response 200 (Progress)**

```json
{
  "status": "Progress",
  "message": "Upload Progress",
  "upload_id": "upload_1762102934_d45ac90f",
  "file_name": "Testing",
  "size": "0.000/1.716 MB",
  "percentage": 0,
  "upload_status": "Progress",
  "data": []
}
```

**Response 200 (Success)**

```json
{
  "status": "Success",
  "message": "Upload successful",
  "upload_id": "upload_1762102550_16bf143b",
  "file_name": "Testing",
  "size": "1.72 MB",
  "percentage": 100,
  "upload_status": "Success",
  "data": [
    {
      "file_id": 1,
      "file_path": "data/uploads/data/Exported_results_realme_hikari.xlsx",
      "notes": "testing",
      "type": "Handphone",
      "tools": "Oxygen",
      "method": "Contact Correlation",
      "total_size": "1.716 MB",
      "amount_of_data": "0",
      "create_at": "2025-11-02 23:56:36",
      "update_at": "2025-11-02 23:56:36"
    }
  ]
}
```

**Response 404**

```json
{
  "status": "Failed",
  "message": "Upload ID not found",
  "upload_id": "upload_1730558981_xxxx",
  "file_name": null,
  "size": "Upload Failed! Please try again",
  "percentage": "Error",
  "upload_status": "Failed",
  "data": []
}
```

**Response 500**

```json
{
  "status": "Failed",
  "message": "Internal server error: Something Wrong",
  "upload_id": "upload_1730558981_8df7b3a1"
}
```

---

### Get Files

**Endpoint** : `/api/v1/analytics/get-files`

**Method** : `GET`

---

**Query Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `search` | string | Cari berdasarkan `file_name`, `notes`, `tools`, atau `method` | N |
| `filter` | string | Filter berdasarkan metode analisis (`Deep Communication Analytics`, `Social Media Correlation`, `Contact Correlation`, `Hashfile Analytics`, `All`) | N (default = `All`) |

---

**Response 200**

```json
{
  "status": 200,
  "message": "Retrieved 1 files successfully",
  "data": [
    {
      "id": 1,
      "file_name": "Testing",
      "file_path": "data/uploads/data/Exported_results_realme_hikari.xlsx",
      "notes": "testing",
      "type": "Handphone",
      "tools": "Oxygen",
      "method": "Contact Correlation",
      "total_size": 1799426,
      "total_size_formatted": "1.716 MB",
      "amount_of_data": 0,
      "created_at": "2025-11-02 23:56:35.648929",
      "date": "02/11/2025"
    }
  ]
}
```

---

**Response 500**

```json
{
  "status": 500,
  "message": "Failed to get files: Something Wrong",
  "data": []
}
```

---

## Analytics Management

### Start Analyzing

**Endpoint** : `/api/v1/analytics/start-analyzing`

**Method** : `POST`

**Request Body :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_name` | string | - | Y |
| `method` | string | check the allowed values | Y |

**Allowed Values :**

| Field | Allowed Values |
| --- | --- |
| `method` | `Deep Communication Analytics`, `Social Media Correlation`, `Contact Correlation`, `APK Analytics`, `Hashfile Analytics` |

---

**Response 200**

```json
{
  "status": 200,
  "message": "Analytics created successfully",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "Testing",
      "method": "Contact Correlation",
      "summary": null,
      "created_at": "2025-11-02 23:51:53.751478"
    }
  }
}
```

---

**Response 400**

```json
{
  "status": 400,
  "message": "analytic_name wajib diisi",
  "data": []
}
```

---

**Response 400**

```json
{
  "status": 400,
  "message": "Invalid method. Must be one of: ['Deep Communication Analytics', 'Social Media Correlation', 'Contact Correlation', 'APK Analytics', 'Hashfile Analytics']",
  "data": []
}
```

---

**Response 500**

```json
{
  "status": 500,
  "message": "Gagal membuat analytic: ",
  "data": []
}
```

---

### Start Data Extraction

**Endpoint** : `/api/v1/analytics/{analytic_id}/start-extraction`

**Method** : `POST`

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

---

**Response 200 (Contact Correlation)**

```json
{
  "status": 200,
  "message": "Data extraction completed. Use GET /analytic/{analytic_id}/contact-correlation to retrieve results",
  "data": {
    "analytic_id": 1,
    "method": "Contact Correlation",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytic/{analytic_id}/contact-correlation"
  }
}

```

---

**Response 200 (Hashfile Analytics)**

```json
{
  "status": 200,
  "message": "Data extraction completed. Use GET /analytic/{analytic_id}/hashfile-analytics to retrieve results",
  "data": {
    "analytic_id": 1,
    "method": "Hashfile Analytics",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytic/{analytic_id}/hashfile-analytics"
  }
}

```

---

**Response 200 (Deep Communication Analytics)**

```json
{
  "status": 200,
  "message": "Data extraction completed. Use GET /analytic/{analytic_id}/deep-communication-analytics to retrieve results",
  "data": {
    "analytic_id": 1,
    "method": "Deep communication analytics",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytic/{analytic_id}/deep-communication-analytics"
  }
}
```

---

**Response 200 (Social Media Correlation)**

```json
{
  "status": 200,
  "message": "Data extraction completed. Use GET /analytic/{analytic_id}/social-media-correlation to retrieve results",
  "data": {
    "analytic_id": 1,
    "method": "Social Media Correlation",
    "device_count": 2,
    "status": "completed",
    "next_step": "GET /api/v1/analytic/{analytic_id}/social-media-correlation"
  }
}

```

---

**Response 400**

```json
{
  "status": 400,
  "message": "Minimum 2 devices required. Currently have 1 device(s)",
  "data": {
    "device_count": 1,
    "required": 2
  }
}
```

---

**Response 404**

```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": []
}
```

---

**Response 500**

```json
{
  "status": 500,
  "message": "Failed to start data extraction: ",
  "data": []
}
```

---

### Get All Analytics

**Endpoint** : `/api/v1/analytics/get-all-analytic`

**Method** : `GET`

---

 Query Parameters :

| Name | Type | Description | Required |
| --- | --- | --- | --- |
| `search` | string | Kata kunci pencarian untuk nama analytic (`analytic_name`) atau ringkasan (`summary`). | N |
| `method` | string | Filter berdasarkan metode analisis. Contoh: `"Social Media Correlation"`, `"Hashfile Analytics"`, `"APK Analytics"`, `"Deep Communication Analytics"` | N |

---

**Response 200 (Success)**

```json
{
  "status": 200,
  "message": "Retrieved 3 analytics successfully",
  "data": [
    {
      "id": 12,
      "analytic_name": "APK Malware Detection - SampleApp",
      "method": "APK Analytics",
      "summary": "Detected 3 high-risk permissions and 1 malware signature",
      "date": "01/11/2025"
    },
    {
      "id": 11,
      "analytic_name": "Social Media Correlation Case #21",
      "method": "Social Media Correlation",
      "summary": "Found 4 overlapping accounts between devices",
      "date": "28/10/2025"
    },
    {
      "id": 10,
      "analytic_name": "Hashfile Analysis - USB Forensics",
      "method": "Hashfile Analytics",
      "summary": "Identified 12 identical files across 3 devices",
      "date": "26/10/2025"
    }
  ]
}
```

---

**Response 200 (Success — No Results Found)**

```json
{
  "status": 200,
  "message": "Retrieved 0 analytics successfully",
  "data": []
}
```

---

**Response 500 (Internal Server Error)**

```json
{
  "status": 500,
  "message": "Gagal mengambil data: Database connection error",
  "data": []
}
```

---

## Device Management

### Add Device

**Endpoint** : `/api/v1/analytics/add-device`

**Method** : `POST`

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `file_id` | integer | - | Y |
| `name` | string | - | Y |
| `phone_number` | string | - | Y |

**Response 200**

```json
{
  "status": 200,
  "message": "Device added successfully",
  "data": {
    "analytics": [
      {
        "analytic_id": 1,
        "analytic_name": "Testing",
        "method": "Contact Correlation",
        "summary": "Testing Edit Summary",
        "date": "02/11/2025",
        "device": [
          {
            "device_label": "A",
            "device_id": 1,
            "owner_name": "testing",
            "phone_number": "085298492839482"
          }
        ],
        "file_info": {
          "file_id": 1,
          "file_name": "Testing",
          "file_type": "Handphone",
          "notes": "testing",
          "tools": "Oxygen",
          "method": "Contact Correlation",
          "total_size": 1799426,
          "total_size_formatted": "1.72 MB"
        }
      }
    ]
  }
}
```

**Response 400 (File Method Mismatch)**

```json
{
  "status": 400,
  "message": "File method '...' does not match analytic method '...'",
  "data": []
}
```

**Response 400 (File Already Used by Another Device)**

```json
{
  "status": 400,
  "message": "This file is already used by another device in this analytic",
  "data": {
    "device_id": ,
    "owner_name": "",
    "phone_number": ""
  }
}
```

**Response 404 (No Analytic Found)**

```json
{
  "status": 404,
  "message": "No analytic found. Please create an analytic first.",
  "data": []
}
```

**Response 404 (File Not Found)**

```json
{
  "status": 404,
  "message": "File not found",
  "data": []
}
```

**Response 500**

```json
{
  "status": 500,
  "message": "Failed to add device: ",
  "data": []
}
```

---

### Get Devices by Analytic ID

**Endpoint** : `/api/v1/analytics/{analytic_id}/get-devices`

**Method** : `GET`

---

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

---

**Response 200 (Tidak Ada Device Terhubung)**

```json
{
  "status": 200,
  "message": "No devices linked to this analytic yet",
  "data": {
    "analytic": {
      "id": 2,
      "analytic_name": "testing",
      "method": "Social Media Correlation"
    },
    "devices": [],
    "device_count": 0
  }
}
```

---

**Response 200 (Berhasil Mengambil Device)**

```json
{
  "status": 200,
  "message": "Retrieved 2 devices for Contact Correlation",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "Testing",
      "method": "Contact Correlation"
    },
    "devices": [
      {
        "label": "Device A",
        "device_id": "1",
        "name": "testing",
        "phone_number": "085298492839482",
        "file_name": "Testing",
        "file_size": "1.72 MB"
      },
      {
        "label": "Device B",
        "device_id": "2",
        "name": "testing",
        "phone_number": "0892348923852",
        "file_name": "Testing",
        "file_size": "1.72 MB"
      }
    ],
    "device_count": 2
  }
}
```

---

**Response 404**

```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": []
}
```

---

**Response 500**

```json
{
  "status": 500,
  "message": "Failed to get devices: ",
  "data": []
}
```

---

## Contact Correlation

**Endpoint** : `/api/v1/analytic/{analytic_id}/contact-correlation`

**Method** : `GET`

---

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

---

**Response 200 (Berhasil Menampilkan Data)**

```json
{
  "status": 200,
  "message": "Contact correlation analysis completed",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "owner_name": "John Doe",
        "phone_number": "+6281234567890"
      },
      {
        "device_label": "Device B",
        "owner_name": "Jane Doe",
        "phone_number": "+6289876543210"
      }
    ],
    "correlations": [
      {
        "contact_number": "+6281122334455",
        "devices_found_in": [
          {
            "device_label": "Device A",
            "contact_name": "Andi"
          },
          {
            "device_label": "Device B",
            "contact_name": "Andi"
          }
        ]
      }
    ],
    "summary": "Contacts found in both devices indicate shared connections between John and Jane."
  }
}

```

---

**Response 200** 

```json
{
  "status": 200,
  "message": "No devices linked",
  "data": {
    "devices": [],
    "correlations": []
  }
}
```

---

**Response 400**

```json
{
  "status": 400,
  "message": "This endpoint is only for Contact Correlation. Current analytic method is 'Hashfile Analytics'",
  "data": null
}
```

---

**Response 404**

```json
{
  "status": 404,
  "message": "Analytic not found"
}
```

---

**Response 500**

```json
{
  "status": 500,
  "message": "Failed to get contact correlation: Something Wrong",
  "data": null
}

```

---

## Social Media Correlation

**Endpoint** : `/api/v1/analytics/{analytic_id}/social-media-correlation`

**Method** : `GET`

---

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

**Query Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `platform` | string | Social media platform filter. Supported values: `"Instagram"`, `"Facebook"`, `"WhatsApp"`, `"TikTok"`, `"Telegram"`, `"X"` | N (default = `"Instagram"`) |

---

**Response 200** 

```json
{
  "status": 200,
  "message": "Success analyzing social media correlation for 'testing 2'",
  "data": {
    "analytic_id": 2,
    "analytic_name": "testing 2",
    "total_devices": 3,
    "devices": [
      {
        "device_id": 4,
        "owner_name": "Device 4",
        "phone_number": "08587384578345",
        "device_name": "Device 4 Device",
        "created_at": "2025-11-03 09:42:40.496792"
      },
      {
        "device_id": 5,
        "owner_name": "Device 5",
        "phone_number": "08582374823",
        "device_name": "Device 5 Device",
        "created_at": "2025-11-03 09:42:50.165803"
      },
      {
        "device_id": 6,
        "owner_name": "Device 6",
        "phone_number": "08582374823",
        "device_name": "Device 6 Device",
        "created_at": "2025-11-03 09:43:27.970779"
      }
    ],
    "correlations": {
      "Instagram": {
        "buckets": [
          {
            "label": "3 koneksi",
            "devices": [
              [
                "25130295109",
                "Riko Suloyo",
                "Riko Suloyo"
              ]
            ]
          },
          {
            "label": "2 koneksi",
            "devices": [
              [
                null,
                "Nurcahya Hikari",
                "Nurcahya Hikari"
              ]
            ]
          }
        ]
      }
    },
    "summary": null
  }
}
```

---

**Response 200**

```json
{
  "status": 200,
  "message": "No social media data found for platform 'tiktok'",
  "data": {
    "analytic_id": 2,
    "analytic_name": "testing 2",
    "total_devices": 3,
    "devices": [
      {
        "device_id": 4,
        "owner_name": "Device 4",
        "phone_number": "08587384578345",
        "device_name": "Device 4 Device",
        "created_at": "2025-11-03 09:42:40.496792"
      },
      {
        "device_id": 5,
        "owner_name": "Device 5",
        "phone_number": "08582374823",
        "device_name": "Device 5 Device",
        "created_at": "2025-11-03 09:42:50.165803"
      },
      {
        "device_id": 6,
        "owner_name": "Device 6",
        "phone_number": "08582374823",
        "device_name": "Device 6 Device",
        "created_at": "2025-11-03 09:43:27.970779"
      }
    ],
    "correlations": {
      "Tiktok": {
        "buckets": []
      }
    },
    "summary": null
  }
}
```

---

**Response 400**

```json
{
  "status": 400,
  "message": "This endpoint is only for Social Media Correlation. Current analytic method is 'Contact Correlation'",
  "data": null
}
```

---

**Response 404**

```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": {}
}
```

atau

```json
{
  "status": 404,
  "message": "No linked devices",
  "data": {}
}
```

---

**Response 500**

```json
{
  "status": 500,
  "message": "Failed to analyze social media correlation: Something Wrong",
  "data": null
}
```

---

## Hashfile Analytics

**Endpoint** : `/api/v1/analytic/{analytic_id}/hashfile-analytics`

**Method** : `GET`

---

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

---

**Response 200 (Berhasil Menampilkan Data)**

```json
{
  "status": 200,
  "message": "Hashfile correlation (by hash + name) completed successfully",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "owner_name": "Device 7",
        "phone_number": "08582374823"
      },
      {
        "device_label": "Device B",
        "owner_name": "Device 8",
        "phone_number": "08582374823"
      },
      {
        "device_label": "Device C",
        "owner_name": "Device 9",
        "phone_number": "08582374823"
      }
    ],
    "correlations": [
      {
        "hash_value": "97d170e1550eee4afc0af065b78cda302a97674c",
        "file_name": "params_names_v4_u0.txt",
        "file_type": "Documents",
        "devices": [
          "Device A",
          "Device B"
        ]
      },
      {
        "hash_value": "3c585604e87f855973731fea83e21fab9392d2fc",
        "file_name": "version",
        "file_type": "Other files",
        "devices": [
          "Device A",
          "Device B"
        ]
      }
    ],
    "summary": null
  }
}
```

---

**Response 200 (Tidak Ada Data Hashfile)**

```json
{
  "status": 200,
  "message": "No hashfile data found",
  "data": {
    "devices": [],
    "correlations": []
  }
}
```

---

**Response 400**

```json
{
  "status": 400,
  "message": "This endpoint is only for Hashfile Analytics. Current method: 'Contact Correlation'",
  "data": null
}
```

atau

```json
{
  "status": 400,
  "message": "No devices linked to this analytic",
  "data": null
}
```

---

**Response 404**

```json
{
  "status": 404,
  "message": "Analytic not found",
  "data": null
}
```

atau

```json
{
  "status": 404,
  "message": "No valid devices found",
  "data": null
}
```

---

**Response 500**

```json
{
  "status": 500,
  "message": "Failed to get hashfile analytics: Something Wrong",
  "data": null
}
```

---

## Deep Communication Analytics

### Get Deep Communication Analytics

**Endpoint** : `/api/v1/analytic/{analytic_id}/deep-communication-analytics`

**Method** : `GET`

---

**Path Parameter :**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

---

**Query Parameters**

| Name | Type | Description | Required |
| --- | --- | --- | --- |
| `device_id` | integer | - | N |

---

**Response 200 (Success)**

```json
{
  "status": 200,
  "message": "Deep Communication Analytics retrieved successfully",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Deep Communication Testing"
    },
    "devices": [
      {
        "device_id": 1,
        "device_name": "iphone hikari",
        "phone_number": "0858273843242",
        "platform_cards": [
          {
            "platform": "Instagram",
            "platform_key": "instagram",
            "has_data": true,
            "message_count": 4,
            "intensity_list": [
              {
                "person": "25130295109 Riko Suloyo",
                "intensity": 4
              }
            ]
          },
          {
            "platform": "Telegram",
            "platform_key": "telegram",
            "has_data": true,
            "message_count": 104,
            "intensity_list": [
              {
                "person": "7172473346 tibo",
                "intensity": 65
              },
              {
                "person": "1883670892 Ekonomi Kreatif Bandung Barat",
                "intensity": 17
              },
              {
                "person": "6460908646 tralalala",
                "intensity": 7
              },
              {
                "person": "System Message",
                "intensity": 6
              },
              {
                "person": "5039016218 cihuy",
                "intensity": 2
              },
              {
                "person": "777000 Telegram",
                "intensity": 1
              },
              {
                "person": "7576259660 C N D",
                "intensity": 1
              },
              {
                "person": "8193959715 c",
                "intensity": 1
              },
              {
                "person": "8339823065 ㅤ",
                "intensity": 1
              },
              {
                "person": "7381176823 firnaa",
                "intensity": 1
              },
              {
                "person": "6371550396 lemon",
                "intensity": 1
              },
              {
                "person": "6580828726",
                "intensity": 1
              }
            ]
          },
          {
            "platform": "WhatsApp",
            "platform_key": "whatsapp",
            "has_data": false,
            "message_count": 0,
            "person": null,
            "intensity": 0
          },
          {
            "platform": "Facebook",
            "platform_key": "facebook",
            "has_data": false,
            "message_count": 0,
            "person": null,
            "intensity": 0
          },
          {
            "platform": "X",
            "platform_key": "x",
            "has_data": true,
            "message_count": 9,
            "intensity_list": [
              {
                "person": "RikoSuloyo69 Riko Suloyo",
                "intensity": 9
              }
            ]
          },
          {
            "platform": "TikTok",
            "platform_key": "tiktok",
            "has_data": false,
            "message_count": 0,
            "person": null,
            "intensity": 0
          }
        ]
      },
      {
        "device_id": 2,
        "device_name": "realme hikari",
        "phone_number": "0858273843242",
        "platform_cards": [
          {
            "platform": "Instagram",
            "platform_key": "instagram",
            "has_data": true,
            "message_count": 4,
            "intensity_list": [
              {
                "person": "riko.suloyo Riko Suloyo",
                "intensity": 4
              }
            ]
          },
          {
            "platform": "Telegram",
            "platform_key": "telegram",
            "has_data": true,
            "message_count": 666,
            "intensity_list": [
              {
                "person": "1492837434 Andrew",
                "intensity": 169
              },
              {
                "person": "8039388995 y",
                "intensity": 142
              },
              {
                "person": "1172775053 Belalang sembah",
                "intensity": 69
              },
              {
                "person": "2236298769 FILM BIOSKOP TELEGRAM",
                "intensity": 64
              },
              {
                "person": "408727173 PokeRaider",
                "intensity": 51
              },
              {
                "person": "System Message",
                "intensity": 47
              },
              {
                "person": "2127073058 𝐉𝐀𝐊𝐀𝐑𝐓𝐀 𝐊𝐄𝐑𝐀𝐒",
                "intensity": 45
              },
              {
                "person": "1006153278 Islam itu Indah",
                "intensity": 28
              },
              {
                "person": "1883670892 Ekonomi Kreatif Bandung Barat",
                "intensity": 20
              },
              {
                "person": "1153408559 INFO LOKER BANDUNG",
                "intensity": 8
              },
              {
                "person": "6460908646 tralalala",
                "intensity": 7
              },
              {
                "person": "518128455 Kevin || Dont DM me Bitch !",
                "intensity": 5
              },
              {
                "person": "5039016218 cihuy",
                "intensity": 3
              },
              {
                "person": "8339823065 ㅤ",
                "intensity": 1
              },
              {
                "person": "7576259660 C N D",
                "intensity": 1
              },
              {
                "person": "8193959715 c",
                "intensity": 1
              },
              {
                "person": "7381176823 firnaa",
                "intensity": 1
              },
              {
                "person": "6371550396 lemon",
                "intensity": 1
              },
              {
                "person": "2020699526 y",
                "intensity": 1
              },
              {
                "person": "6580828726",
                "intensity": 1
              },
              {
                "person": "1908933908 femci",
                "intensity": 1
              }
            ]
          },
          {
            "platform": "WhatsApp",
            "platform_key": "whatsapp",
            "has_data": true,
            "message_count": 37,
            "intensity_list": [
              {
                "person": "System Message",
                "intensity": 26
              },
              {
                "person": "0@s.whatsapp.net",
                "intensity": 7
              },
              {
                "person": "6285155111222@s.whatsapp.net by.U",
                "intensity": 2
              },
              {
                "person": "628118651031@s.whatsapp.net Gojek Indonesia",
                "intensity": 2
              }
            ]
          },
          {
            "platform": "Facebook",
            "platform_key": "facebook",
            "has_data": false,
            "message_count": 0,
            "person": null,
            "intensity": 0
          },
          {
            "platform": "X",
            "platform_key": "x",
            "has_data": true,
            "message_count": 9,
            "intensity_list": [
              {
                "person": "1130597879284883457 Riko Suloyo",
                "intensity": 9
              }
            ]
          },
          {
            "platform": "TikTok",
            "platform_key": "tiktok",
            "has_data": false,
            "message_count": 0,
            "person": null,
            "intensity": 0
          }
        ]
      },
      {
        "device_id": 3,
        "device_name": "xiaomi riko",
        "phone_number": "0858273843242",
        "platform_cards": [
          {
            "platform": "Instagram",
            "platform_key": "instagram",
            "has_data": true,
            "message_count": 5,
            "intensity_list": [
              {
                "person": "hikari_noeer Nurcahya Hikari",
                "intensity": 4
              },
              {
                "person": "ramadhaniabakrie Nia Ramadhani Bakrie",
                "intensity": 1
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
          },
          {
            "platform": "WhatsApp",
            "platform_key": "whatsapp",
            "has_data": true,
            "message_count": 2257,
            "intensity_list": [
              {
                "person": "6289652052405@s.whatsapp.net",
                "intensity": 1946
              },
              {
                "person": "System Message",
                "intensity": 221
              },
              {
                "person": "6289503470803@s.whatsapp.net Asep Corona",
                "intensity": 7
              },
              {
                "person": "6281224950058@s.whatsapp.net",
                "intensity": 6
              },
              {
                "person": "6285795285554@s.whatsapp.net Arif Bedog",
                "intensity": 4
              },
              {
                "person": "62815293675470@s.whatsapp.net",
                "intensity": 3
              },
              {
                "person": "6281223213980@s.whatsapp.net",
                "intensity": 3
              },
              {
                "person": "0@s.whatsapp.net",
                "intensity": 2
              },
              {
                "person": "62895323398789@s.whatsapp.net",
                "intensity": 2
              },
              {
                "person": "628388410611@s.whatsapp.net",
                "intensity": 2
              }
            ]
          },
          {
            "platform": "Facebook",
            "platform_key": "facebook",
            "has_data": true,
            "message_count": 16,
            "intensity_list": [
              {
                "person": "100087996695508 Petualang Pemberani",
                "intensity": 3
              },
              {
                "person": "1236707212 Urip Kuwiranto",
                "intensity": 3
              },
              {
                "person": "100088072922732 Nusa Sandi",
                "intensity": 2
              },
              {
                "person": "100051336874335 Ifa",
                "intensity": 2
              },
              {
                "person": "100084272387434 Sugiyaryo Sugiyarto",
                "intensity": 1
              },
              {
                "person": "100000192543260 M Alifan Syahba D",
                "intensity": 1
              },
              {
                "person": "100022633002424 Suharningsih",
                "intensity": 1
              },
              {
                "person": "100006681695239 Markusz Verszantdro",
                "intensity": 1
              },
              {
                "person": "100006207764291 Reffi",
                "intensity": 1
              },
              {
                "person": "100006737706722 Hussein Santoso",
                "intensity": 1
              }
            ]
          },
          {
            "platform": "X",
            "platform_key": "x",
            "has_data": true,
            "message_count": 20,
            "intensity_list": [
              {
                "person": "480224156 myXLCare",
                "intensity": 10
              },
              {
                "person": "1979020219390840832 Nurcahya",
                "intensity": 9
              },
              {
                "person": "63433517 3 Indonesia",
                "intensity": 1
              }
            ]
          },
          {
            "platform": "TikTok",
            "platform_key": "tiktok",
            "has_data": false,
            "message_count": 0,
            "person": null,
            "intensity": 0
          }
        ]
      }
    ],
    "summary": null
  }
}
```

---

**Response 200 (No Linked Devices)**

```json
{
  "status": 200,
  "message": "No devices linked to this analytic",
  "data": {
    "analytic_info": {
      "analytic_id": 17,
      "analytic_name": "Chat Behavior Analysis Case #17"
    },
    "devices": [],
    "summary": "No device data found for this analytic."
  }
}
```

---

Response 404 (Analytic Not Found)

```json
{
  "status": 404,
  "message": "Analytic not found"
}
```

---

Response 404 (Device Not Found in Analytic)

```json
{
  "status": 404,
  "message": "Device not found in this analytic"
}
```

---

Response 500 (Internal Server Error)

```json
{
  "status": 500,
  "message": "Internal server error: Failed to retrieve deep communication analytics",
  "data": null
}
```

---

### Get Platform Cards Intensity

**Endpoint:** `/api/v1/analytic/{analytic_id}/platform-cards/intensity`

**Method:** `GET`

---

**Path Parameter**

| Name | Type | Description | Required |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | Y |

---

**Query Parameters**

| Name | Type | Description | Required |
| --- | --- | --- | --- |
| `platform` | string | Nama platform yang akan dianalisis. Nilai valid: `Instagram`, `Telegram`, `WhatsApp`, `Facebook`, `X`, `TikTok`. | Y |
| `device_id` | integer | - | N |

---

**Response 200 (Success)**

```json
{
  "status": 200,
  "message": "Platform cards intensity retrieved successfully",
  "data": {
    "analytic_id": 1,
    "platform": "Telegram",
    "device_id": 1,
    "intensity_list": [
      {
        "person": "7172473346 tibo",
        "person_id": null,
        "intensity": 65
      },
      {
        "person": "1883670892 Ekonomi Kreatif Bandung Barat",
        "person_id": null,
        "intensity": 17
      },
      {
        "person": "6460908646 tralalala",
        "person_id": null,
        "intensity": 7
      },
      {
        "person": "System Message",
        "person_id": null,
        "intensity": 6
      },
      {
        "person": "5039016218 cihuy",
        "person_id": null,
        "intensity": 2
      },
      {
        "person": "777000 Telegram",
        "person_id": null,
        "intensity": 1
      },
      {
        "person": "7576259660 C N D",
        "person_id": null,
        "intensity": 1
      },
      {
        "person": "8193959715 c",
        "person_id": null,
        "intensity": 1
      },
      {
        "person": "8339823065 ㅤ",
        "person_id": null,
        "intensity": 1
      },
      {
        "person": "7381176823 firnaa",
        "person_id": null,
        "intensity": 1
      },
      {
        "person": "6371550396 lemon",
        "person_id": null,
        "intensity": 1
      },
      {
        "person": "6580828726",
        "person_id": null,
        "intensity": 1
      }
    ],
    "summary": null
  }
}
```

---

**Response 200 (No Devices Linked)**

```json
{
  "status": 200,
  "message": "Platform cards intensity retrieved successfully",
  "data": {
    "analytic_id": 25,
    "platform": "Telegram",
    "device_id": null,
    "intensity_list": [],
    "summary": "No devices linked to this analytic."
  }
}
```

---

**Response 400 (Missing or Invalid Platform)**

```json
{
  "status": 400,
  "message": "Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok"
}
```

atau jika parameter `platform` tidak diisi:

```json
{
  "status": 400,
  "message": "Platform parameter is required"
}
```

---

**Response 404 (Analytic Not Found)**

```json
{
  "status": 404,
  "message": "Analytic not found"
}
```

---

**Response 404 (Device Not Found in Analytic)**

```json
{
  "status": 404,
  "message": "Device not found in this analytic"
}
```

---

**Response 500 (Internal Server Error)**

```json
{
  "status": 500,
  "message": "Internal server error: Failed to retrieve platform cards intensity",
  "data": null
}
```

---

### Get Chat Detail

**Endpoint:** `/api/v1/analytic/{analytic_id}/chat-detail`

**Method:** `GET`

---

**Path Parameter**

| Name | Type | Description | Required |
| --- | --- | --- | --- |
| analytic_id | integer | ID analytic yang memuat data chat | Y |

---

**Query Parameters**

| Name | Type | Description | Required |
| --- | --- | --- | --- |
| person_name | string | Nama lawan bicara. Bisa parsial. Wajib jika search kosong. | Conditional |
| platform | string | Platform chat (Instagram, WhatsApp, Telegram, Facebook, X, TikTok) | N |
| device_id | integer | Filter percakapan pada device tertentu saja | N |
| search | string | Text search pada pesan chat. Wajib jika person_name kosong. | Conditional |

**Catatan:**

Minimal salah satu: `person_name` atau `search` wajib ada.

---

**Success Response (200)**

Jika ditemukan chat detail:

```json
{
  "status": 200,
  "message": "Chat detail retrieved successfully",
  "data": {
    "person_name": "6460908646 tralalala",
    "person_id": null,
    "platform": null,
    "intensity": 7,
    "chat_messages": [
      {
        "message_id": 6,
        "timestamp": "2025-10-20T14:25:35+07:00",
        "times": "14:25",
        "direction": "Outgoing",
        "sender": "8229898490 Nurcahya Hikari",
        "recipient": "6460908646 tralalala",
        "sender_id": "",
        "recipient_id": "",
        "message_text": "Halo",
        "message_type": "Unknown",
        "platform": "Telegram",
        "thread_id": "6460908646",
        "chat_id": ""
      },
      {
        "message_id": 7,
        "timestamp": "2025-10-20T14:36:22+07:00",
        "times": "14:36",
        "direction": "Incoming",
        "sender": "6460908646 tralalala",
        "recipient": "8229898490 Nurcahya Hikari",
        "sender_id": "",
        "recipient_id": "",
        "message_text": "hi",
        "message_type": "Unknown",
        "platform": "Telegram",
        "thread_id": "6460908646",
        "chat_id": ""
      },
      {
        "message_id": 8,
        "timestamp": "2025-10-20T14:39:41+07:00",
        "times": "14:39",
        "direction": "Outgoing",
        "sender": "8229898490 Nurcahya Hikari",
        "recipient": "6460908646 tralalala",
        "sender_id": "",
        "recipient_id": "",
        "message_text": "namanya lala?",
        "message_type": "Unknown",
        "platform": "Telegram",
        "thread_id": "6460908646",
        "chat_id": ""
      },
      {
        "message_id": 9,
        "timestamp": "2025-10-20T14:40:53+07:00",
        "times": "14:40",
        "direction": "Incoming",
        "sender": "6460908646 tralalala",
        "recipient": "8229898490 Nurcahya Hikari",
        "sender_id": "",
        "recipient_id": "",
        "message_text": "iya klo u",
        "message_type": "Unknown",
        "platform": "Telegram",
        "thread_id": "6460908646",
        "chat_id": ""
      },
      {
        "message_id": 10,
        "timestamp": "2025-10-20T15:47:52+07:00",
        "times": "15:47",
        "direction": "Outgoing",
        "sender": "8229898490 Nurcahya Hikari",
        "recipient": "6460908646 tralalala",
        "sender_id": "",
        "recipient_id": "",
        "message_text": "Aku fajar",
        "message_type": "Unknown",
        "platform": "Telegram",
        "thread_id": "6460908646",
        "chat_id": ""
      },
      {
        "message_id": 11,
        "timestamp": "2025-10-20T15:48:01+07:00",
        "times": "15:48",
        "direction": "Outgoing",
        "sender": "8229898490 Nurcahya Hikari",
        "recipient": "6460908646 tralalala",
        "sender_id": "",
        "recipient_id": "",
        "message_text": "Oiya salken ya",
        "message_type": "Unknown",
        "platform": "Telegram",
        "thread_id": "6460908646",
        "chat_id": ""
      },
      {
        "message_id": 12,
        "timestamp": "2025-10-20T19:32:51+07:00",
        "times": "19:32",
        "direction": "Incoming",
        "sender": "6460908646 tralalala",
        "recipient": "8229898490 Nurcahya Hikari",
        "sender_id": "",
        "recipient_id": "",
        "message_text": "iya slkn jh",
        "message_type": "Unknown",
        "platform": "Telegram",
        "thread_id": "6460908646",
        "chat_id": ""
      }
    ],
    "summary": null
  }
}
```

---

**Response 200 (No devices attached)**

```json
{
  "status": 200,
  "message": "No devices linked",
  "data": {
    "person_name": "Alice",
    "platform": "WhatsApp",
    "chat_messages": []
  }
}
```

---

**Bad Request (400)**

Jika `person_name` dan `search` dua-duanya kosong:

```json
{
  "status": 400,
  "message": "Either person_name or search parameter must be provided"
}

```

Jika platform tidak valid:

```json
{
  "status": 400,
  "message": "Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok"
}
```

---

**Not Found (404)**

Analytic tidak ditemukan:

```json
{
  "status": 404,
  "message": "Analytic not found"
}
```

Device tidak ada dalam analytic:

```json
{
  "status": 404,
  "message": "Device not found in this analytic"
}
```

---

**Internal Server Error (500)**

```json
{
  "status": 500,
  "message": "Internal server error: Failed to retrieve chat detail",
  "data": null
}
```

---

## APK Analytics

### Upload APK

**Endpoint** : `/api/v1/analytics/upload-apk`

**Method** : `POST`

---

**Request Body (Form Data):**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `file` | file | only file `.apk` and `.ipa` | Y |
| `file_name` | string | - | Y |

---

**Validation Rules:**

- Allowed file extensions: `.apk`, `.ipa` only
- The `file_name` field must not be empty

---

**Response 200 (Upload Initialized Successfully)**

```json
{
  "status": 200,
  "message": "Upload initialized successfully",
  "data": {
    "file_id": null,
    "upload_id": "upload_1730560243_a1b2c3d4",
    "status_upload": "Pending",
    "upload_type": "apk"
  }
}
```

---

**Response 400 (Invalid File Type)**

```json
{
  "status": 400,
  "message": "Invalid file type. Only ['apk', 'ipa'] allowed."
}
```

---

**Response 400 (File Size Too Large)**

```json
{
  "status": 400,
  "message": "File size exceeds 100MB limit"
}
```

---

**Response 422 (Missing Required Field)**

```json
{
  "status": 422,
  "message": "Field 'file_name' is required",
  "error_field": "file_name"
}
```

---

**Response 500**

```json
{
  "status": 500,
  "message": "Upload error: Something went wrong"
}
```

---

### Analyzing APK

**Endpoint** : `/api/v1/analytics/analyze-apk`

**Method** : `POST`

---

**Request Body (Form Data / Query Params):**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `file_id` | integer | - | Y |
| `analytic_id` | integer | - | Y |

---

**Response 200 (Success)**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "analytic_name": "testing",
    "method": "APK Analytics",
    "malware_scoring": "47",
    "permissions": [
      {
        "id": 1,
        "item": "easy.sudoku.puzzle.solver.free.permission.C2D_MESSAGE",
        "status": "unknown",
        "description": "Unknown permission from android reference"
      },
      {
        "id": 2,
        "item": "android.permission.SCHEDULE_EXACT_ALARM",
        "status": "normal",
        "description": "Allows an app to use exact alarm scheduling APIs to perform timing sensitive background work."
      }
    ]
  }
}
```

---

**Response 400 (Invalid / Unsupported File)**

```json
{
  "status": 400,
  "message": "Invalid analysis result or file not supported",
  "data": null
}
```

atau

```json
{
  "status": 400,
  "message": "No permissions found in analysis result",
  "data": null
}
```

---

**Response 404 (Analytic or File Not Found)**

```json
{
  "status": 404,
  "message": "Analytics Not Found",
  "data": null
}
```

atau

```json
{
  "status": 404,
  "message": "File Not Found",
  "data": null
}
```

---

**Response 500 (Internal Server Error)**

```json
{
  "status": 500,
  "message": "Something went wrong, please try again later!",
  "data": null
}
```

---

### Get APK Analytic Result

**Endpoint** : `/api/v1/analytics/{analytic_id}/apk-analytic`

**Method** : `GET`

---

**Path Parameter:**

| Name | Type | Description | Required? |
| --- | --- | --- | --- |
| `analytic_id` | integer | - | |

---

**Response 200 (Success)**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "analytic_name": "testing",
    "method": "APK Analytics",
    "malware_scoring": "47",
    "permissions": [
      {
        "id": 1,
        "item": "easy.sudoku.puzzle.solver.free.permission.C2D_MESSAGE",
        "status": "unknown",
        "description": "Unknown permission from android reference"
      },
      {
        "id": 2,
        "item": "android.permission.SCHEDULE_EXACT_ALARM",
        "status": "normal",
        "description": "Allows an app to use exact alarm scheduling APIs to perform timing sensitive background work."
      }
    ]
  }
}
```

---

**Response 404 (No Data Found)**

```json
{
  "status": 404,
  "message": "No APK analysis found for analytic_id=12",
  "data": {}
}
```

---

**Response 500 (Internal Server Error)**

```json
{
  "status": 500,
  "message": "Failed to get APK analysis: Something went wrong",
  "data": {}
}
```