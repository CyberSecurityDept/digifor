# Deep Communication Analytics API Documentation

API untuk Deep Communication Analytics yang mengquery data dari tabel `chat_message` berdasarkan platform.

## Endpoint Overview

### 1. Deep Communication Analytics (Main Endpoint)
**GET** `/api/v1/analytic/{analytic_id}/deep-communication-analytics`

Endpoint utama yang menampilkan device tabs dan platform analysis dengan intensity score per person.

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `platform` (optional): Filter by platform (Instagram, Telegram, WhatsApp, Facebook, X, TikTok)

**Response:**
```json
{
  "status": 200,
  "message": "Deep communication analytics retrieved successfully",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Analysis Name"
    },
    "device_tabs": [
      {
        "device_id": 1,
        "device_name": "Riko Suloyo",
        "phone_number": "081234567890"
      }
    ],
    "platform_analysis": {
      "whatsapp": [
        {
          "person": "Briani Akbar",
          "person_id": "628123456789",
          "intensity": 810
        }
      ]
    },
    "summary": {
      "total_devices": 1,
      "total_messages": 150,
      "platforms_analyzed": ["whatsapp", "telegram"]
    }
  }
}
```

---

### 2. List Interaction Intensity
**GET** `/api/v1/analytic/{analytic_id}/interaction-intensity`

Endpoint untuk menampilkan daftar person dengan nilai intensitas untuk platform tertentu.

**Query Parameters:**
- `platform` (required): Platform name (Instagram, Telegram, WhatsApp, Facebook, X, TikTok)
- `device_id` (optional): Filter by device ID

**Response:**
```json
{
  "status": 200,
  "message": "Interaction intensity retrieved successfully",
  "data": {
    "platform": "WhatsApp",
    "intensity_list": [
      {
        "person": "Iriana",
        "person_id": "628123456789",
        "intensity": 910
      },
      {
        "person": "Briani Akbar",
        "person_id": "628987654321",
        "intensity": 810
      }
    ],
    "summary": {
      "total_persons": 2,
      "total_messages": 1720
    }
  }
}
```

---

### 3. Chat Detail Viewer
**GET** `/api/v1/analytic/{analytic_id}/chat-detail`

Endpoint untuk menampilkan percakapan antara device owner dan person tertentu.

**Query Parameters:**
- `person_name` (required): Nama person untuk mendapatkan detail chat
- `platform` (required): Platform name
- `device_id` (optional): Filter by device ID
- `search` (optional): Search text dalam pesan

**Response:**
```json
{
  "status": 200,
  "message": "Chat detail retrieved successfully",
  "data": {
    "person_name": "Briani Akbar",
    "person_id": "628987654321",
    "platform": "WhatsApp",
    "intensity": 810,
    "chat_messages": [
      {
        "message_id": 1,
        "timestamp": "2024-01-15 20:12:00",
        "direction": "Incoming",
        "sender": "Briani Akbar",
        "recipient": "Riko Suloyo",
        "sender_id": "628987654321",
        "recipient_id": "081234567890",
        "message_text": "Aku gak bisa tidur mikirin itu lagi",
        "message_type": "text",
        "platform": "WhatsApp"
      }
    ],
    "search_query": null,
    "summary": {
      "total_messages": 810,
      "devices_involved": [1]
    }
  }
}
```

---

### 4. Chat Search
**GET** `/api/v1/analytic/{analytic_id}/chat-search`

Endpoint untuk mencari teks dalam pesan-pesan chat.

**Query Parameters:**
- `query` (required): Search query text
- `platform` (optional): Filter by platform
- `device_id` (optional): Filter by device ID
- `person_name` (optional): Filter by person name

**Response:**
```json
{
  "status": 200,
  "message": "Search completed successfully",
  "data": {
    "query": "dompet",
    "platform": "WhatsApp",
    "person_name": null,
    "results": [
      {
        "message_id": 1,
        "timestamp": "2024-01-15 20:13:00",
        "direction": "Outgoing",
        "sender": "Riko Suloyo",
        "recipient": "Briani Akbar",
        "message_text": "Kemarin siang aku dari parkiran belakang masuk ke toko. Aku ambil dompetnya waktu dia lagi bongkar rak.",
        "message_type": "text",
        "platform": "WhatsApp",
        "thread_id": "12345",
        "chat_id": "12345"
      }
    ],
    "summary": {
      "total_results": 1,
      "devices_searched": 1
    }
  }
}
```

---

## Platform Support

Platform yang didukung:
- **Instagram**: `Instagram`, `instagram`
- **Telegram**: `Telegram`, `telegram`
- **WhatsApp**: `WhatsApp`, `whatsapp`, `WA`
- **Facebook**: `Facebook`, `facebook`, `Messenger`, `messenger`
- **X (Twitter)**: `X`, `x`, `Twitter`, `twitter`
- **TikTok**: `TikTok`, `tiktok`

## Intensity Score Calculation

Intensity score dihitung berdasarkan:
- **Frekuensi pesan**: Jumlah total pesan antara device owner dan person tertentu
- Platform-specific: Score dihitung per platform

Logic:
1. Identifikasi device owner dari tabel `Device` (owner_name)
2. Identifikasi person yang berkomunikasi dengan owner (dari `from_name` atau `to_name` yang bukan owner)
3. Hitung jumlah pesan untuk setiap person
4. Urutkan berdasarkan intensity score (tertinggi ke terendah)

## Direction Logic

Direction ditentukan berdasarkan:
- **Outgoing**: Pesan dikirim oleh device owner
- **Incoming**: Pesan diterima oleh device owner

Jika kolom `direction` di tabel `chat_message` sudah terisi, akan menggunakan nilai tersebut. Jika tidak, akan dihitung berdasarkan:
- Jika `from_name` adalah device owner → Outgoing
- Jika `to_name` adalah device owner → Incoming

## Examples

### Get all platforms analytics
```bash
curl -X GET "http://localhost:8000/api/v1/analytic/1/deep-communication-analytics"
```

### Get intensity list for WhatsApp
```bash
curl -X GET "http://localhost:8000/api/v1/analytic/1/interaction-intensity?platform=WhatsApp"
```

### Get chat detail for specific person
```bash
curl -X GET "http://localhost:8000/api/v1/analytic/1/chat-detail?person_name=Briani%20Akbar&platform=WhatsApp"
```

### Search messages
```bash
curl -X GET "http://localhost:8000/api/v1/analytic/1/chat-search?query=dompet&platform=WhatsApp"
```

