# 📚 **COMPLETE API WORKFLOW GUIDE**
## **From Upload to Contact Correlation Analysis**

---

## 🎯 **OVERVIEW**

Panduan lengkap untuk menggunakan API Forenlytic dari upload file hingga mendapatkan hasil contact correlation analysis. Workflow ini mencakup 6 tahap utama:

1. **📤 Upload File** - Upload forensic reports
2. **🔍 View Files** - Lihat semua file yang sudah di-upload
3. **Add Device** - Buat device dengan single file (1 device = 1 file)
4. ** Create Analytic** - Buat analytic dengan linked devices
5. **🔗 Contact Correlation** - Jalankan analisis korelasi kontak
6. **Export PDF** - Export hasil ke PDF

---

## 🚀 **PREREQUISITES**

- Server berjalan di `http://localhost:8000`
- File forensic reports dalam format Excel (.xlsx)
- Tools yang didukung: Oxygen, Magnet Axiom, Cellebrite

---

## 📋 **STEP 1: UPLOAD FILE**

### **Endpoint:**
```
POST /api/v1/analytics/upload-data
```

### **Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
  -F "file=@/path/to/your/file.xlsx" \
  -F "notes=Sample forensic report" \
  -F "type=Handphone"
```

### **Request Body (Form Data):**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | ✅ | Excel file (.xlsx) |
| `notes` | String | ❌ | Deskripsi file |
| `type` | String | ❌ | Tipe device (Handphone, SSD, Harddisk, PC, Laptop, DVR) |

### **Response:**
```json
{
  "status": 200,
  "message": "File uploaded and processed successfully",
  "data": {
    "file_id": 1,
    "file_name": "Oxygen Forensics - iOS Image CCC.xlsx",
    "file_path": "uploads/data/Oxygen Forensics - iOS Image CCC.xlsx",
    "notes": "Sample forensic report",
    "type": "Handphone",
    "tools": "Oxygen",
    "total_size": 123456,
    "total_size_formatted": "120.56 KB",
    "created_at": "2025-02-17 10:30:00"
  }
}
```

### **Example:**
```bash
# Upload file dari contoh dataset
curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
  -F "file=@contoh_dataset/Oxygen Forensics - iOS Image CCC.xlsx" \
  -F "notes=iOS forensic report from Oxygen" \
  -F "type=Handphone"
```

---

## 🔍 **STEP 2: VIEW ALL UPLOADED FILES**

### **Endpoint:**
```
GET /api/v1/analytics/files/all
```

### **Request:**
```bash
curl -s "http://localhost:8000/api/v1/analytics/files/all"
```

### **Response:**
```json
{
  "status": 200,
  "message": "Files retrieved successfully",
  "data": [
    {
      "id": 1,
      "file_name": "Oxygen Forensics - iOS Image CCC.xlsx",
      "file_path": "uploads/data/Oxygen Forensics - iOS Image CCC.xlsx",
      "notes": "iOS forensic report from Oxygen",
      "type": "Handphone",
      "tools": "Oxygen",
      "total_size": 123456,
      "total_size_formatted": "120.56 KB",
      "created_at": "2025-02-17 10:30:00"
    },
    {
      "id": 2,
      "file_name": "Magnet Axiom Report - CCC.xlsx",
      "file_path": "uploads/data/Magnet Axiom Report - CCC.xlsx",
      "notes": "Android forensic report from Magnet Axiom",
      "type": "Handphone",
      "tools": "Magnet Axiom",
      "total_size": 97446,
      "total_size_formatted": "95.16 KB",
      "created_at": "2025-02-17 10:35:00"
    }
  ]
}
```

---

## **STEP 3: ADD DEVICE (1 DEVICE = 1 FILE)**

### **Endpoint:**
```
POST /api/v1/analytics/add-device
```

### **Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/add-device" \
  -F "file_id=1" \
  -F "owner_name=Bambang Ajriman" \
  -F "phone_number=082121200905"
```

### **Request Body (Form Data):**
```
file_id: 1                    // ID file dari step 2
owner_name: "Bambang Ajriman" // Nama pemilik device
phone_number: "082121200905"  // Nomor telepon device
```

**Note:** 1 device = 1 file (sederhana dan mudah digunakan)

### **Response:**
```json
{
  "status": 200,
  "message": "Device created/updated successfully",
  "data": {
    "device_id": 1,
    "file_id": 1,
    "owner_name": "Bambang Ajriman",
    "phone_number": "082121200905",
    "device_name": "Bambang Ajriman Device",
    "file_info": {
      "file_name": "Oxygen Forensics - iOS Image CCC.xlsx",
      "file_type": "Handphone",
      "notes": "iOS forensic report from Oxygen",
      "tools": "Oxygen",
      "total_size": 123456,
      "total_size_formatted": "120.56 KB"
    },
    "created_at": "2025-02-17 10:40:00"
  }
}
```

---

##  **STEP 4: CREATE ANALYTIC WITH DEVICES**

### **Endpoint:**
```
POST /api/v1/analytics/create-analytic-with-devices
```

### **Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/create-analytic-with-devices" \
  -H "Content-Type: application/json" \
  -d '{
    "analytic_name": "Contact Correlation Analysis - Case 123",
    "method": "Contact Correlation",
    "notes": "Analysis of contact correlations between suspects",
    "device_ids": [1, 2, 3]
  }'
```

### **Request Body:**
```json
{
  "analytic_name": "string",        // Nama analisis
  "method": "string",               // Metode analisis
  "notes": "string",                // Catatan analisis
  "device_ids": [1, 2, 3]          // Array ID device dari step 4
}
```

### **Response:**
```json
{
  "status": 200,
  "message": "Analytic created successfully with linked devices",
  "data": {
    "analytic": {
      "id": 1,
      "analytic_name": "Contact Correlation Analysis - Case 123",
      "method": "Contact Correlation",
      "notes": "Analysis of contact correlations between suspects",
      "created_at": "2025-02-17 10:45:00"
    },
    "linked_devices": [
      {
        "device_id": 1,
        "owner_name": "Bambang Ajriman",
        "phone_number": "082121200905"
      },
      {
        "device_id": 2,
        "owner_name": "Riko Suloyo",
        "phone_number": "089660149979"
      },
      {
        "device_id": 3,
        "owner_name": "Andika",
        "phone_number": "08112157462"
      }
    ],
    "total_linked_devices": 3
  }
}
```

---

## 🔗 **STEP 5: CONTACT CORRELATION ANALYSIS**

### **Endpoint:**
```
GET /api/v1/analytic/{analytic_id}/contact-correlation
```

### **Request:**
```bash
curl -s "http://localhost:8000/api/v1/analytic/1/contact-correlation"
```

### **Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analytic_id` | Integer | ✅ | ID analytic dari step 5 |

### **What is Contact Correlation?**
Contact correlation mencari **kontak yang sama** (nomor telepon yang sama) yang muncul di **beberapa device berbeda**. Ini membantu investigator menemukan:

- **Kontak bersama** antara suspect yang berbeda
- **Jaringan komunikasi** yang menghubungkan beberapa device
- **Kontak yang sering muncul** di multiple device (mungkin kontak penting)
- **Korelasi sosial** antara pemilik device yang berbeda

### **How it Works:**
1. **Extract Contacts**: Ambil semua kontak dari setiap device
2. **Normalize Phone Numbers**: Normalisasi nomor telepon (0812... → 62812...)
3. **Find Matches**: Cari nomor telepon yang sama di beberapa device
4. **Filter by Threshold**: Hanya tampilkan kontak yang muncul di minimal 2 device
5. **Generate Report**: Buat laporan korelasi dengan detail device dan nama kontak

### **Response (When Correlations Found):**
```json
{
  "status": 200,
  "message": "Contact correlation analysis completed",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "device_id": 1,
        "owner_name": "Bambang Ajriman",
        "phone_number": "082121200905"
      },
      {
        "device_label": "Device B",
        "device_id": 2,
        "owner_name": "Riko Suloyo",
        "phone_number": "089660149979"
      },
      {
        "device_label": "Device C",
        "device_id": 3,
        "owner_name": "Andika",
        "phone_number": "08112157462"
      }
    ],
    "correlations": [
      {
        "contact_number": "6281234567890",
        "devices_found_in": [
          {
            "device_label": "Device A",
            "contact_name": "John Doe"
          },
          {
            "device_label": "Device B",
            "contact_name": "John"
          },
          {
            "device_label": "Device C",
            "contact_name": "Unknown"
          }
        ]
      }
    ]
  }
}
```

### **Response (When No Correlations Found):**
```json
{
  "status": 200,
  "message": "Contact correlation analysis completed",
  "data": {
    "devices": [
      {
        "device_label": "Device A",
        "device_id": 1,
        "owner_name": "Bambang Ajriman",
        "phone_number": "082121200905"
      },
      {
        "device_label": "Device B",
        "device_id": 2,
        "owner_name": "Riko Suloyo",
        "phone_number": "089660149979"
      },
      {
        "device_label": "Device C",
        "device_id": 3,
        "owner_name": "Andika",
        "phone_number": "08112157462"
      }
    ],
    "correlations": []
  }
}
```

### **Example Scenarios:**

#### **Scenario 1: No Correlations Found**
- **Device A**: Bambang Ajriman (contacts: John, Mary, Bob)
- **Device B**: Riko Suloyo (contacts: Alice, Charlie, David)
- **Device C**: Andika (contacts: Eve, Frank, Grace)
- **Result**: `correlations: []` (no shared contacts)

#### **Scenario 2: Correlations Found**
- **Device A**: Bambang Ajriman (contacts: John, Mary, Bob)
- **Device B**: Riko Suloyo (contacts: Alice, John, David) ← John appears here too
- **Device C**: Andika (contacts: Eve, John, Grace) ← John appears here too
- **Result**: John's number will appear in correlations with devices A, B, and C

### **Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `devices` | Array | List device yang dianalisis |
| `correlations` | Array | List korelasi kontak yang ditemukan |
| `contact_number` | String | Nomor telepon yang berkorelasi (format: 628xxxxxxxxx) |
| `devices_found_in` | Array | Device yang memiliki kontak tersebut |
| `device_label` | String | Label device (Device A, Device B, etc.) |
| `contact_name` | String | Nama kontak atau "Unknown" jika tidak ada nama |

---

## **STEP 6: EXPORT CONTACT CORRELATION TO PDF**

### **Endpoint:**
```
GET /api/v1/analytic/{analytic_id}/contact-correlation/export-pdf
```

### **Request:**
```bash
curl -o "contact_correlation_report.pdf" \
  "http://localhost:8000/api/v1/analytic/1/contact-correlation/export-pdf"
```

### **Response:**
- **Content-Type**: `application/pdf`
- **File**: PDF report dengan hasil contact correlation analysis

### **PDF Content:**
- Header dengan informasi analytic
- Tabel device yang dianalisis
- Tabel korelasi kontak yang ditemukan
- Summary statistik

---

## 🔍 **ADDITIONAL ENDPOINTS**

### **View All Analytics:**
```bash
curl -s "http://localhost:8000/api/v1/analytics/get-all-analytic"
```

### **View All Devices:**
```bash
curl -s "http://localhost:8000/api/v1/analytics/device/get-all-devices"
```

### **View Device Details:**
```bash
curl -s "http://localhost:8000/api/v1/analytics/device/1"
```

---

## 🚨 **ERROR HANDLING**

### **Common Error Responses:**

#### **404 - Not Found:**
```json
{
  "detail": "Analytic not found"
}
```

#### **422 - Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "owner_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### **500 - Server Error:**
```json
{
  "status": 500,
  "message": "Failed to process file: Invalid file format",
  "data": []
}
```

---

## 📝 **COMPLETE WORKFLOW EXAMPLE**

### **1. Upload Files:**
```bash
# Upload iOS report
curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
  -F "file=@sample_dataset/Oxygen Forensics - iOS Image CCC.xlsx" \
  -F "file_name=Oxygen Forensics - iOS Image CCC.xlsx" \
  -F "notes=iOS forensic report" \
  -F "type=Handphone" \
  -F "tools=Oxygen"

# Upload Android report  
curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
  -F "file=@sample_dataset/Oxygen Forensics - Android Image CCC.xlsx" \
  -F "file_name=Oxygen Forensics - Android Image CCC.xlsx" \
  -F "notes=Android forensic report" \
  -F "type=Handphone" \
  -F "tools=Oxygen"

# Upload Magnet Axiom report
curl -X POST "http://localhost:8000/api/v1/analytics/upload-data" \
  -F "file=@sample_dataset/Magnet Axiom Report - CCC.xlsx" \
  -F "file_name=Magnet Axiom Report - CCC.xlsx" \
  -F "notes=Magnet Axiom report" \
  -F "type=Handphone" \
  -F "tools=Magnet Axiom"
```

### **2. Add Devices (1 Device = 1 File):**
```bash
# Add Device 1 (iOS)
curl -X POST "http://localhost:8000/api/v1/analytics/add-device" \
  -F "file_id=1" \
  -F "owner_name=Bambang Ajriman" \
  -F "phone_number=082121200905"

# Add Device 2 (Android)
curl -X POST "http://localhost:8000/api/v1/analytics/add-device" \
  -F "file_id=2" \
  -F "owner_name=Riko Suloyo" \
  -F "phone_number=089660149979"

# Add Device 3 (Magnet Axiom)
curl -X POST "http://localhost:8000/api/v1/analytics/add-device" \
  -F "file_id=3" \
  -F "owner_name=Andika" \
  -F "phone_number=08112157462"
```

### **3. Create Analytic:**
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/create-analytic-with-devices" \
  -H "Content-Type: application/json" \
  -d '{
    "analytic_name": "Contact Correlation Analysis - Case 123",
    "method": "Contact Correlation",
    "notes": "Analysis of contact correlations between suspects",
    "device_ids": [1, 2, 3]
  }'
```

### **4. Run Contact Correlation:**
```bash
curl -s "http://localhost:8000/api/v1/analytic/1/contact-correlation"
```

### **5. Export to PDF:**
```bash
curl -o "contact_correlation_report.pdf" \
  "http://localhost:8000/api/v1/analytic/1/contact-correlation/export-pdf"
```

---

## 🎯 **KEY FEATURES**

### **Multi-Device Support:**
- Satu analytic bisa menganalisis multiple devices
- Setiap device bisa punya multiple files
- Tools selection per file untuk fleksibilitas

### **🔍 Smart Phone Normalization:**
- Otomatis normalize nomor telepon ke format `628xxxxxxxxx`
- Support berbagai format input: `+62`, `0812`, `0812-8415-3434`
- Handle nomor tanpa nama sebagai "Unknown"

### ** Cross-Device Correlation:**
- Deteksi kontak yang sama di minimal 2 device
- Sorting berdasarkan jumlah device (descending)
- Support untuk nama berbeda di device berbeda

### **PDF Export:**
- Generate PDF report dengan hasil analisis
- Include device information dan correlation details
- Professional formatting untuk forensic reports

---

## 🔧 **TROUBLESHOOTING**

### **File Upload Issues:**
- Pastikan file format .xlsx
- Check file size (max 50MB)
- Verify file tidak corrupted

### **No Correlations Found:**
- Normal jika dataset berbeda orang
- Pastikan minimal 2 device di analytic
- Check phone number normalization

### **Tools Filter Not Working:**
- Gunakan nama tools yang tepat: `oxygen`, `magnet axiom`, `cellebrite`
- Case sensitive untuk beberapa tools
- Check tools field di database

---

## 📞 **SUPPORT**

Untuk bantuan lebih lanjut:
- Check server logs di `logs/forenlytic.log`
- Verify database connection
- Test individual endpoints dengan curl

---

