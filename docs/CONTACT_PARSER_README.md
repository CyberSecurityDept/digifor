# Contact Parser Documentation

## Overview
Contact Parser adalah tool untuk mengekstrak data kontak dari file forensik Excel dengan fokus pada 4 field utama:
- **Display Name**: Nama kontak
- **Phone Number**: Nomor telepon
- **Type**: Tipe kontak (Contact, WhatsApp Contact, Telegram Contact, dll)
- **Last Time Contacted**: Waktu terakhir kontak

## Model Contact Baru
Model Contact telah disederhanakan dengan field berikut:
- `id` - Primary key
- `device_id` - Foreign key ke device
- `display_name` - Nama kontak
- `phone_number` - Nomor telepon
- `type` - Tipe kontak
- `last_time_contacted` - Waktu terakhir kontak
- `created_at` - Timestamp pembuatan
- `updated_at` - Timestamp update

## Supported File Formats

### 1. Magnet Axiom Reports
- **File**: `Magnet Axiom Report - CCC.xlsx`
- **Sheets**: 
  - `Android Contacts` - Kontak dari Android
  - `Android WhatsApp Contacts` - Kontak WhatsApp
  - `Telegram Contacts - Android` - Kontak Telegram

### 2. Oxygen Forensics Reports
- **File**: `Oxygen Forensics - Android Image CCC.xlsx`
- **File**: `Oxygen Forensics - iOS Image CCC.xlsx`
- **Sheets**: `Contacts` - Kontak terintegrasi

## Usage

### 1. Basic Usage - Extract Contacts
```bash
# Extract kontak dari file Magnet Axiom
python extract_contacts.py "data/uploads/data/Magnet Axiom Report - CCC.xlsx"

# Extract kontak dari file Oxygen Forensics Android
python extract_contacts.py "data/uploads/data/Oxygen Forensics - Android Image CCC.xlsx"

# Extract kontak dari file Oxygen Forensics iOS
python extract_contacts.py "data/uploads/data/Oxygen Forensics - iOS Image CCC.xlsx"
```

### 2. Summary View
```bash
# Tampilkan ringkasan kontak
python contact_summary.py "data/uploads/data/Magnet Axiom Report - CCC.xlsx"
```

### 3. Programmatic Usage
```python
from app.analytics.utils.contact_parser import contact_parser
from pathlib import Path

# Parse kontak dari file
file_path = Path("data/uploads/data/Magnet Axiom Report - CCC.xlsx")
contacts = contact_parser.parse_contacts_from_file(file_path)

# Normalize kontak
normalized_contacts = contact_parser.normalize_contacts(contacts)

# Access contact data
for contact in normalized_contacts:
    print(f"Name: {contact.get('display_name')}")
    print(f"Phone: {contact.get('phone_number')}")
    print(f"Type: {contact.get('type')}")
    print(f"Last Contacted: {contact.get('last_time_contacted')}")
```

## Data Structure

### Contact Object (Model Baru)
```python
{
    'display_name': str,           # Nama kontak
    'phone_number': str,           # Nomor telepon utama
    'type': str,                   # Tipe kontak
    'last_time_contacted': datetime # Waktu terakhir kontak
}
```

### Contact Types
- `Contact` - Kontak standar
- `WhatsApp Contact` - Kontak WhatsApp
- `Telegram Contact` - Kontak Telegram
- `Account (merged)` - Akun terintegrasi
- `Group (merged)` - Grup terintegrasi
- `com.lge.sync` - Kontak LG Sync
- `com.android.contacts.sim` - Kontak SIM Android

## Sample Data Results

### Magnet Axiom Report - CCC.xlsx
```
✅ Total kontak ditemukan: 57
✅ Setelah normalisasi: 47
Kontak dengan nomor telepon: 17
⏰ Kontak dengan info last contacted: 13

 Kontak berdasarkan tipe:
   Contact: 15
   Telegram Contact: 7
   WhatsApp Contact: 8
   com.android.contacts.sim: 9
   com.lge.sync: 6
   org.telegram.messenger: 2
```

### Oxygen Forensics - Android Image CCC.xlsx
```
✅ Total kontak ditemukan: 455
✅ Setelah normalisasi: 455
Kontak dengan nomor telepon: 321
⏰ Kontak dengan info last contacted: 0
```

### Oxygen Forensics - iOS Image CCC.xlsx
```
✅ Total kontak ditemukan: 36
✅ Setelah normalisasi: 36
Kontak dengan nomor telepon: 15
⏰ Kontak dengan info last contacted: 0
```

## Key Features

### 1. Phone Number Normalization
- Otomatis convert ke format Indonesia (+62)
- Handle multiple phone number formats
- Remove duplicates

### 2. Data Deduplication
- Remove kontak duplikat berdasarkan nomor telepon dan tipe
- Merge kontak dengan informasi yang sama
- Smart deduplication yang mempertahankan kontak dengan tipe berbeda

### 3. Display Name Validation
- Otomatis deteksi jika display name berupa nomor telepon
- Set display name ke "Unknown" jika berupa nomor telepon
- Preserve display name asli jika bukan nomor telepon

### 4. Multi-Source Support
- Magnet Axiom (Android Contacts, WhatsApp, Telegram)
- Oxygen Forensics (Android & iOS)
- Generic Excel files

### 5. Error Handling
- Graceful handling of missing data
- Continue processing even if some contacts fail
- Detailed error logging

## Database Integration

### Save to Database
```python
from app.analytics.utils.contact_service import contact_service

# Parse dan simpan ke database
result = contact_service.parse_and_save_contacts(file_path, device_id)
print(f"Saved {result['contacts_saved']} contacts")
```

### Get Contact Statistics
```python
# Get statistik kontak
stats = contact_service.get_contact_statistics(device_id)
print(f"Total contacts: {stats['total_contacts']}")
print(f"Contacts with phone: {stats['contacts_with_phone']}")
print(f"Contacts with last contacted: {stats['contacts_with_last_contacted']}")
```

## File Structure
```
app/analytics/utils/
├── contact_parser.py      # Main parser logic
├── contact_service.py     # Database service
└── parser_xlsx.py         # Excel parsing utilities

Scripts:
├── extract_contacts.py    # Full contact extraction
├── contact_summary.py     # Summary view
└── show_contact_details.py # Detailed contact analysis
```

## Dependencies
- `pandas` - Excel file processing
- `sqlalchemy` - Database operations
- `pathlib` - File path handling
- `re` - Regular expressions for phone number parsing

## Notes
- Parser mendukung file Excel dengan multiple sheets
- Phone number normalization khusus untuk format Indonesia
- Data normalization menghilangkan duplikat dan whitespace
- Error handling memastikan proses tetap berjalan meski ada data yang rusak
