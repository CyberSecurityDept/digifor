# EXCEL COLUMN MAPPING - Riko Suloyo-MT6765-20102025165759.xls

## 📋 OVERVIEW

Dokumentasi ini menjelaskan mapping kolom dari file Excel Oxygen Forensic ke tabel `social_media` di database.

## 🔍 STRUKTUR FILE

File: `Riko Suloyo-MT6765-20102025165759.xls`

**Total Sheets: 14**
1. Table of contents
2. Device information 
3. Activity 
4. Calls 
5. Contacts ⭐ (Multi-platform)
6. Facebook ⭐
7. Gmail 
8. Instagram ⭐
9. Phonebook 
10. Snapchat 
11. Telegram ⭐
12. WhatsApp Messenger ⭐
13. WhatsApp Messenger backup 
14. X (Twitter) ⭐

## 📊 FIELD MAPPING PER PLATFORM

### 1. WHATSAPP

**Requirement**: `platform, account_name, account_id, user_id, full_name, phone_number, source_tool, sheet_name, created_at, updated_at`

#### Sheet: WhatsApp Messenger 
- **Header Detection**: Dynamic - mencari row yang berisi "Full name", "User name", "User ID", "Phone number"
- **Kolom Mapping**:
  - `full_name` ← Kolom "Full name"
  - `account_name` ← Kolom "User name" (atau fallback ke full_name atau phone_number)
  - `user_id` ← Kolom "User ID" (atau fallback ke phone_number)
  - `account_id` ← Phone number (normalized) sebagai identifier unik
  - `phone_number` ← Kolom "Phone number" (normalized, Required)
  - `platform` ← "whatsapp"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "WhatsApp Messenger"

**Validation**:
- Skip rows yang berisi: "Source", "Status", "Received", "Delivered", "Seen", "Categories", "Direction", "Time stamp", "Timestamp", "Deleted", "Chats\\", "Calls\\", "At the server", "Failed call", "Outgoing", "Incoming", "Message", "Call"
- Skip rows yang berisi path chat: "\chats\" atau "\calls\"
- Validasi phone_number: minimal 10 digit setelah normalize

#### Sheet: Contacts (WhatsApp detected dari Source field)
- **Kolom Mapping**:
  - `full_name` ← Extract dari kolom "Contact"
  - `account_name` ← Extract dari kolom "Contact" (nickname/username)
  - `account_id` ← Extract "WhatsApp ID" dari kolom "Internet"
  - `user_id` ← Extract "WhatsApp ID" dari kolom "Internet"
  - `phone_number` ← Extract dari kolom "Phones & Emails" (format: "Phone number: Mobile: 123, Mobile: 081214861970")
  - `platform` ← "whatsapp"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "Contacts"

### 2. INSTAGRAM

**Requirement**: `platform, account_name, account_id, user_id, full_name, phone_number (optional), source_tool, sheet_name, created_at, updated_at`

#### Sheet: Instagram 
- **Structure**: 
  - Row 0: "Identifier"
  - Row 1: "User data"
  - Row 2: "Accounts"
  - Row 3: "Categories" (Header) - Source, Deleted, Full name, User name, Last accessed, ...
  - Row 4+: Data
- **Kolom Mapping** (berdasarkan index setelah row 3):
  - `full_name` ← `row.iloc[2]` (Full name)
  - `account_name` ← `row.iloc[3]` (User name)
  - `biography` ← `row.iloc[5]` (optional, tidak disimpan)
  - `profile_picture_url` ← `row.iloc[6]` (optional, tidak disimpan)
  - `followers_count` ← `row.iloc[7]` → `followers`
  - `following_count` ← `row.iloc[8]` → `following`
  - `user_id` ← `row.iloc[19]` (User ID - numeric)
  - `account_id` ← `user_id` (User ID sebagai identifier unik)
  - `platform` ← "instagram"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "Instagram"

**Validation**:
- Skip jika `user_name` dalam ['Accounts', 'Source', 'Categories']
- Validasi `user_id` harus numeric (`user_id.isdigit()`)

#### Sheet: Contacts (Instagram detected dari Source field)
- **Kolom Mapping**:
  - `full_name` ← Extract dari kolom "Contact"
  - `account_name` ← Extract dari kolom "Contact" (nickname/username)
  - `account_id` ← Extract "Instagram ID" dari kolom "Internet" (numeric ID)
  - `user_id` ← Extract "Instagram ID" dari kolom "Internet"
  - `platform` ← "instagram"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "Contacts"

### 3. FACEBOOK

**Requirement**: `platform, account_name, account_id, user_id, full_name, phone_number (optional), source_tool, sheet_name, created_at, updated_at`

#### Sheet: Facebook 
- **Structure**: Mirip dengan Instagram
  - Row 3: "Categories" (Header) - Source, Deleted, Full name, User name, Emails, ...
  - Row 4+: Data
- **Kolom Mapping**:
  - `full_name` ← `row.iloc[2]` (Full name)
  - `account_name` ← `row.iloc[3]` (User name)
  - `email` ← `row.iloc[4]` (optional, tidak disimpan)
  - `phone_number` ← `row.iloc[5]` (optional)
  - `profile_picture_url` ← `row.iloc[6]` (optional, tidak disimpan)
  - `user_id` ← `row.iloc[14]` (User ID - numeric)
  - `account_id` ← `user_id` (User ID sebagai identifier unik)
  - `platform` ← "facebook"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "Facebook"

**Validation**:
- Skip jika `user_name` dalam ['Accounts', 'Source', 'Categories']
- Validasi `user_id` harus numeric (`user_id.isdigit()`)

### 4. TELEGRAM

**Requirement**: `platform, account_name, account_id, user_id, full_name, phone_number (optional), source_tool, sheet_name, created_at, updated_at`

#### Sheet: Telegram 
- **Structure**: Mirip dengan platform lain
  - Row 3+: Data
- **Kolom Mapping** (berdasarkan index):
  - `full_name` ← `row.iloc[1]` (Full name)
  - `user_name` ← `row.iloc[2]` (User name)
  - `phone_number` ← `row.iloc[3]` (optional)
  - `profile_picture_url` ← `row.iloc[4]` (optional, tidak disimpan)
  - `user_id` ← `row.iloc[5]` (User ID)
  - `account_id` ← `user_id` (User ID sebagai identifier unik)
  - `platform` ← "telegram"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "Telegram"

**Validation**:
- Require `user_name` dan `user_id` untuk valid record

#### Sheet: Contacts (Telegram detected dari Source field)
- **Kolom Mapping**:
  - `full_name` ← Extract dari kolom "Contact"
  - `account_name` ← Extract dari kolom "Contact" (nickname/username)
  - `account_id` ← Extract "Telegram ID" dari kolom "Internet" (numeric ID)
  - `user_id` ← Extract "Telegram ID" dari kolom "Internet"
  - `phone_number` ← Extract dari kolom "Phones & Emails"
  - `platform` ← "telegram"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "Contacts"

### 5. X (TWITTER)

**Requirement**: `platform, account_name, account_id, user_id, full_name, phone_number (optional), source_tool, sheet_name, created_at, updated_at`

#### Sheet: X (Twitter) 
- **Structure**: Mirip dengan platform lain
  - Row 3+: Data
- **Kolom Mapping**:
  - `full_name` ← `row.iloc[1]` (Full name)
  - `user_name` ← `row.iloc[2]` (User name)
  - `biography` ← `row.iloc[3]` (optional, tidak disimpan)
  - `profile_picture_url` ← `row.iloc[4]` (optional, tidak disimpan)
  - `followers_count` ← `row.iloc[5]` → `followers`
  - `following_count` ← `row.iloc[6]` → `following`
  - `user_id` ← `row.iloc[7]` (User ID)
  - `account_id` ← `user_id` (User ID sebagai identifier unik)
  - `platform` ← "x"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "X (Twitter)"

**Validation**:
- Require `user_name` dan `user_id` untuk valid record

#### Sheet: Contacts (X/Twitter detected dari Source field)
- **Kolom Mapping**:
  - `full_name` ← Extract dari kolom "Contact"
  - `account_name` ← Extract dari kolom "Contact" (username)
  - `account_id` ← Extract "X ID" atau "Twitter ID" dari kolom "Internet"
  - `user_id` ← Extract "X ID" atau "Twitter ID" dari kolom "Internet"
  - `platform` ← "x"
  - `source_tool` ← "Oxygen"
  - `sheet_name` ← "Contacts"

### 6. TIKTOK

**Requirement**: `platform, account_name, account_id, user_id, full_name, phone_number (optional), source_tool, sheet_name, created_at, updated_at`

- Struktur mirip dengan platform lain
- Mapping mengikuti pola yang sama

## 🧹 DATA CLEANING RULES

### Phone Number Extraction
Format yang didukung:
- `"Phone number: Mobile: 123, Mobile: 081214861970"` → Extract "123" dan "081214861970", ambil yang terpanjang/valid
- `"Phone number: 333"` → Extract "333" (jika satu-satunya nomor)

### Skip Rules (WhatsApp Messenger Sheet)
Skip rows yang berisi keyword berikut:
- "Source", "Status", "Received", "Delivered", "Seen", "Categories"
- "Direction", "Time stamp", "Timestamp", "Deleted"
- "Chats\\", "Calls\\", "At the server", "Failed call"
- "Outgoing", "Incoming", "Message", "Call"
- Path chat: "\chats\" atau "\calls\"

### Kolom yang TIDAK di-parse
- **Internet**: Hanya digunakan untuk extract `account_id` dan `user_id` (identifier)
- **Addresses**: Tidak digunakan
- **Other**: Tidak digunakan

## ✅ VALIDATION RULES

1. **WhatsApp**:
   - Harus ada `phone_number` yang valid (minimal 10 digit)
   - Harus ada `full_name` atau `account_name`

2. **Instagram, Facebook, Telegram, X, TikTok**:
   - Harus ada `account_id` atau `user_id`
   - Harus ada `account_name`
   - `user_id` harus numeric untuk Instagram dan Facebook

3. **Umum**:
   - Skip jika semua field kosong atau hanya whitespace
   - Skip jika berisi keyword invalid
   - Normalize phone_number (remove +, -, spaces, @s.whatsapp.net)

## 📝 NOTES

- `created_at` dan `updated_at` otomatis di-set oleh database (default timestamps)
- `following` dan `followers` hanya diisi jika ada data di sheet (bisa None)
- `phone_number` optional untuk semua platform kecuali WhatsApp (required untuk WhatsApp)

