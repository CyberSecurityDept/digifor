# 📊 MODEL RELATIONSHIPS DOCUMENTATION

## Relasi Model Database

### 1. **Analytic** (analytics_history)
```
┌─────────────────────────────────────┐
│ Analytic                            │
├─────────────────────────────────────┤
│ id (PK)                             │
│ analytic_name                       │
│ type                                │
│ method ⭐                            │
│ summary                             │
│ created_at                          │
│ updated_at                          │
└─────────────────────────────────────┘
         │
         │ 1:N
         ↓
┌─────────────────────────────────────┐
│ AnalyticDevice                      │
├─────────────────────────────────────┤
│ id (PK)                             │
│ analytic_id (FK → Analytic)         │
│ device_ids (ARRAY[Integer]) ⭐      │
│ created_at                          │
│ updated_at                          │
└─────────────────────────────────────┘
```

**Relasi:**
- `Analytic` → `AnalyticDevice` (one-to-many)
- `AnalyticDevice` → `Analytic` (many-to-one)

### 2. **File** (files)
```
┌─────────────────────────────────────┐
│ File                                │
├─────────────────────────────────────┤
│ id (PK)                             │
│ file_name                           │
│ file_path                           │
│ file_encrypted                      │
│ notes                               │
│ type                                │
│ tools                               │
│ method ⭐                            │
│ total_size                          │
│ amount_of_data                       │
│ created_at                          │
│ updated_at                          │
└─────────────────────────────────────┘
         │
         │ 1:N
         ↓
┌─────────────────────────────────────┐
│ Device                              │
├─────────────────────────────────────┤
│ id (PK)                             │
│ file_id (FK → File) ⭐              │
│ owner_name                          │
│ phone_number                        │
│ device_name                         │
│ ...                                 │
└─────────────────────────────────────┘
```

**Relasi:**
- `File` → `Device` (one-to-many)
- `Device` → `File` (many-to-one)

### 3. **File → Data Models** (one-to-many)
```
File
 ├── Contact (contacts)
 ├── Call (calls)
 ├── SocialMedia (social_media)
 ├── HashFile (hash_files)
 └── ChatMessage (chat_messages)
```

Semua data models memiliki `file_id` sebagai foreign key ke `File`.

---

## 🔗 RELATIONSHIP CHAIN

### Workflow Relasi:

```
Analytic (method: "Contact Correlation")
    ↓
AnalyticDevice (device_ids: [1, 2, 3])
    ↓
Device (id: 1, file_id: 5)
    ↓
File (id: 5, method: "Contact Correlation")
    ↓
Data Models (Contact, Call, SocialMedia, etc.)
```

### Validasi Method:

```
✅ Analytic.method == File.method
   → Device dapat di-link ke Analytic
   
❌ Analytic.method != File.method
   → Error: Method mismatch
```

---

## 📋 FIELD IMPORTANT UNTUK WORKFLOW

### 1. **Analytic.method**
- Field yang dipilih saat create analytic
- Digunakan untuk filter file yang sesuai

### 2. **File.method**
- Field yang disimpan saat upload-data
- Harus match dengan Analytic.method untuk bisa di-link

### 3. **AnalyticDevice.device_ids**
- Array of Device IDs yang terhubung ke Analytic
- Di-update otomatis saat add-device dengan analytic_id

### 4. **Device.file_id**
- Foreign key ke File
- Satu Device = satu File

---

## ✅ RELASI YANG SUDAH BENAR

1. ✅ **Analytic ↔ AnalyticDevice** - Sudah benar
2. ✅ **File ↔ Device** - Sudah benar
3. ✅ **File ↔ Data Models** - Sudah benar
4. ✅ **Method validation** - Sudah diimplementasi di endpoint

---

## 🔧 RELASI YANG PERLU DIPERHATIKAN

1. **Device tidak memiliki analytic_id langsung**
   - Device di-link ke Analytic melalui AnalyticDevice.device_ids
   - Ini sudah benar untuk many-to-many relationship

2. **File.method harus match dengan Analytic.method**
   - Validasi sudah diimplementasi di endpoint add-device
   - Filter sudah diimplementasi di endpoint get files

---

## 💡 KESIMPULAN

**Relasi model sudah benar dan konsisten dengan workflow:**

1. ✅ Analytic memiliki method
2. ✅ File memiliki method  
3. ✅ Device di-link ke File melalui file_id
4. ✅ Device di-link ke Analytic melalui AnalyticDevice.device_ids
5. ✅ Validasi method match sudah diimplementasi
6. ✅ Cascade delete sudah dikonfigurasi dengan benar

**Tidak ada perubahan relasi model yang diperlukan!**

