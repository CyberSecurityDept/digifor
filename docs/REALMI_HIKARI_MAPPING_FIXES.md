# Realmi Hikari - Mapping Fixes untuk Chat Detail Viewer

## 📋 Overview

Dokumentasi ini menjelaskan perbaikan mapping kolom Excel ke field database untuk file `Realmi Hikari/Axiom/Exported results.xlsx` agar Chat Detail Viewer dapat bekerja dengan baik.

## 🔍 Fields Penting untuk Chat Detail Viewer

Untuk query percakapan antara 2 pihak, field berikut **HARUS** terisi dengan benar:

1. **thread_id** atau **chat_id**: Untuk mengelompokkan percakapan antara 2 pihak
2. **from_name** dan **to_name**: Untuk identifikasi siapa berbicara dengan siapa  
3. **sender_number** dan **recipient_number**: Untuk backup identifikasi
4. **timestamp**: Untuk sorting urutan pesan kronologis
5. **direction**: Untuk membedakan incoming/outgoing (Incoming/Outgoing)
6. **message_id**: Unik untuk setiap pesan
7. **message_text**: Konten pesan

## 📊 Perbaikan Mapping per Sheet

### 1. Telegram Messages - Android ✅

**Status**: ✅ **FIXED**

| Excel Column | Database Field | Notes |
|-------------|----------------|-------|
| `Message Body` | `message_text` | ✅ |
| `Sender` | `from_name` | ✅ |
| `Sender ID` | `sender_number` | ✅ |
| `Recipient` | `to_name` | ✅ |
| `Recipient ID` | `recipient_number` | ✅ |
| `Created Date/Time - UTC+00:00 (dd/MM/yyyy)` | `timestamp` | ✅ Fallback ke Message Sent Date/Time |
| `_ChatId` | `chat_id` | ✅ |
| `_ThreadID` | `thread_id` | ✅ |
| `Item ID` | `message_id` | ✅ |
| `Type` | `message_type` | ✅ |
| `Direction` (Sent/Received) | `direction` (Outgoing/Incoming) | ✅ Mapping: Sent → Outgoing, Received → Incoming |

**Data Quality**: 636/803 messages with text, 803 rows dengan chat_id ✅

---

### 2. WhatsApp Messages - Android ✅

**Status**: ✅ **FIXED**

| Excel Column | Database Field | Notes |
|-------------|----------------|-------|
| `Message` | `message_text` | ✅ |
| `Sender` | `from_name` | ✅ Extract phone jika ada @s.whatsapp.net |
| `Sender` (extract phone) | `sender_number` | ✅ Auto-extract dari format @s.whatsapp.net |
| `Recipient` | `to_name` | ✅ Extract phone jika ada @s.whatsapp.net |
| `Recipient` (extract phone) | `recipient_number` | ✅ Auto-extract dari format @s.whatsapp.net |
| `Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)` | `timestamp` | ✅ |
| `Chat ID` (if available) | `chat_id` | ✅ Auto-generate jika tidak ada |
| `_ThreadID` (if available) | `thread_id` | ✅ Auto-generate dari participants jika tidak ada |
| `Item ID` | `message_id` | ✅ |
| `Type` | `message_type` | ✅ |
| `Message Status` | `direction` | ✅ Mapping: Received → Incoming, Sent → Outgoing |

**Auto-generate thread_id/chat_id**: Jika tidak ada, generate dari kombinasi sorted `sender_number` dan `recipient_number`

**Data Quality**: 43/53 messages with text ✅

---

### 3. Android Messages (SMS) ✅

**Status**: ✅ **NEW - Added Support**

| Excel Column | Database Field | Notes |
|-------------|----------------|-------|
| `Message` | `message_text` | ✅ |
| `Sender` | `from_name` | ✅ |
| `Sender Phone Number` | `sender_number` | ✅ |
| `Recipient` | `to_name` | ✅ Parse format "Name <Phone>" |
| `Recipient` (extract phone) | `recipient_number` | ✅ Auto-extract dari format "Name <Phone>" |
| `Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)` | `timestamp` | ✅ |
| `_ThreadID` | `thread_id` | ✅ |
| `_ThreadID` | `chat_id` | ✅ (same as thread_id) |
| `Item ID` | `message_id` | ✅ |
| `Message Type` | `message_type` | ✅ |
| `Message Status` / `Message Direction` | `direction` | ✅ Mapping: Received → Incoming, Sent → Outgoing |

**Data Quality**: 159/159 messages with text, 25 unique threads ✅

---

### 4. Instagram Direct Messages ✅

**Status**: ✅ **FIXED**

| Excel Column | Database Field | Notes |
|-------------|----------------|-------|
| `Message` | `message_text` | ✅ |
| `Sender` | `from_name` | ✅ |
| `Recipient` | `to_name` | ✅ |
| `Message Date/Time - UTC+00:00 (dd/MM/yyyy)` | `timestamp` | ✅ |
| `_ThreadID` | `thread_id` | ✅ |
| `Chat ID` | `chat_id` | ✅ |
| `Item ID` | `message_id` | ✅ |
| `Type` | `message_type` | ✅ |
| `Direction` | `direction` | ✅ |

**Data Quality**: 4/4 messages with text, 1 unique thread ✅

---

### 5. TikTok Messages ✅

**Status**: ✅ **FIXED**

| Excel Column | Database Field | Notes |
|-------------|----------------|-------|
| `Message` | `message_text` | ✅ |
| `Sender` | `from_name` | ✅ |
| `Recipient` | `to_name` | ✅ |
| `Created Date/Time - UTC+00:00 (dd/MM/yyyy)` | `timestamp` | ✅ |
| `_ThreadID` | `thread_id` | ✅ |
| `Item ID` | `message_id` | ✅ |
| `Message Type` | `message_type` | ✅ |
| `Direction` (if available) | `direction` | ⚠️ Empty jika tidak ada (TikTok tidak punya direction) |

**Data Quality**: 6053/7122 messages with text, 96 unique threads ✅

---

### 6. Twitter Direct Messages ✅

**Status**: ✅ **FIXED**

| Excel Column | Database Field | Notes |
|-------------|----------------|-------|
| `Text` | `message_text` | ✅ |
| `Sender Name` | `from_name` | ✅ |
| `Sender ID` | `sender_number` | ✅ |
| `Recipient Name(s)` | `to_name` | ✅ |
| `Recipient ID(s)` | `recipient_number` | ✅ |
| `Sent/Received Date/Time - UTC+00:00 (dd/MM/yyyy)` | `timestamp` | ✅ |
| `_ThreadID` | `thread_id` | ✅ |
| `Item ID` | `message_id` | ✅ |
| `Direction` | `direction` | ✅ |

**Data Quality**: 19/19 messages with text, 2 unique threads ✅

---

## 🔑 Key Improvements

### 1. Timestamp Handling
- ✅ Semua parser sekarang menggunakan fallback multiple column names untuk timestamp
- ✅ Mencari: `Message Sent Date/Time`, `Message Date/Time`, `Created Date/Time`, `Timestamp`, dll

### 2. Thread ID / Chat ID
- ✅ WhatsApp: Auto-generate dari kombinasi sender+recipient jika tidak ada
- ✅ Android Messages: Menggunakan `_ThreadID` sebagai `chat_id` juga
- ✅ Semua sheet: Memastikan thread_id atau chat_id terisi untuk grouping percakapan

### 3. Phone Number Extraction
- ✅ WhatsApp: Auto-extract dari format `@s.whatsapp.net`
- ✅ Android Messages: Parse format `"Name <Phone>"`
- ✅ Fallback ke regex extraction jika format berbeda

### 4. Direction Mapping
- ✅ Telegram Android: `Sent` → `Outgoing`, `Received` → `Incoming`
- ✅ WhatsApp: `Message Status` dengan Received/Sent mapping
- ✅ Android Messages: `Message Status` / `Message Direction` mapping

## 📝 Query untuk Chat Detail Viewer

Dengan mapping yang sudah diperbaiki, query untuk Chat Detail Viewer bisa menggunakan:

```sql
-- Contoh: Get conversation antara 2 pihak
SELECT 
    message_id,
    from_name,
    to_name,
    message_text,
    timestamp,
    direction,
    platform
FROM chat_messages
WHERE 
    thread_id = :thread_id  -- atau chat_id
    AND file_id = :file_id
ORDER BY timestamp ASC;
```

## ✅ Testing Checklist

Setelah upload file Realmi Hikari, pastikan:

1. ✅ `thread_id` atau `chat_id` terisi untuk semua pesan
2. ✅ `from_name` dan `to_name` terisi
3. ✅ `timestamp` terisi untuk sorting
4. ✅ `direction` terisi (Incoming/Outgoing)
5. ✅ Query Chat Detail Viewer bisa mengelompokkan percakapan dengan benar

## 📌 Notes

- **Telegram Messages - Android**: Menggunakan kolom khusus (`Message Body`, `_ChatId`, `Item ID`)
- **WhatsApp Messages**: Auto-generate thread_id jika tidak ada untuk consistency
- **Android Messages**: Platform = "SMS" (bukan "Android Messages")
- **TikTok**: Direction mungkin kosong karena TikTok tidak punya arah pesan
- Semua field menggunakan `pd.notna()` check untuk handle empty values dengan benar

