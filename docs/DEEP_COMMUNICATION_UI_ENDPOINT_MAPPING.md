# Deep Communication Analytics - UI to Endpoint Mapping

Dokumentasi mapping antara UI components di dashboard dengan endpoint yang digunakan.

## UI Components → Endpoint Mapping

### 1. **Device Tabs (Left Panel - Names dengan Phone Number)**
**UI Element:** List nama device dengan nomor telepon (Rio, Paul, Mag)

**Endpoint:**
```
GET /api/v1/analytic/{analytic_id}/deep-communication-analytics
```

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `platform` (optional): Filter by platform

**Response Field:**
```json
{
  "data": {
    "device_tabs": [
      {
        "device_id": 1,
        "device_name": "Rio",
        "phone_number": "08131323421"
      }
    ]
  }
}
```

**Usage:**
- Dipanggil saat pertama kali load dashboard
- Menampilkan daftar semua device yang terkait dengan analytic
- User bisa click untuk filter by device

---

### 2. **Platform Dropdown Selection**
**UI Element:** Dropdown untuk memilih platform (WhatsApp, Instagram, Telegram, dll)

**Endpoint yang digunakan setelah selection:**
```
GET /api/v1/analytic/{analytic_id}/interaction-intensity?platform={selected_platform}&device_id={device_id}
```

**Platform Options:**
- Instagram
- Telegram
- WhatsApp
- Facebook
- X (Twitter)
- TikTok

---

### 3. **List Interaction Intensity (Table: Person & Intensity)**
**UI Element:** Tabel dengan kolom "Person" dan "Intensity Score"

**Endpoint:**
```
GET /api/v1/analytic/{analytic_id}/interaction-intensity?platform={platform}&device_id={device_id}
```

**Query Parameters:**
- `platform` (required): Platform name
- `device_id` (optional): Filter by device ID

**Response Field:**
```json
{
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

**Usage:**
- Dipanggil saat user memilih platform dari dropdown
- Menampilkan list person dengan intensity score (diurutkan dari tertinggi)
- User bisa click person untuk melihat chat detail

---

### 4. **Chat Detail Viewer (Right Panel)**
**UI Element:** Panel kanan yang menampilkan percakapan chat messages

**Endpoint:**
```
GET /api/v1/analytic/{analytic_id}/chat-detail?person_name={person_name}&platform={platform}&device_id={device_id}&search={search}
```

**Query Parameters:**
- `person_name` (optional): Person name untuk filter
- `platform` (optional): Platform name
- `device_id` (optional): Filter by device ID
- `search` (optional): Search text dalam messages

**Response Field:**
```json
{
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
        "recipient": "Rio",
        "message_text": "Aku gak bisa tidur...",
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

**Usage:**
- Dipanggil saat user click person dari list intensity
- Menampilkan semua chat messages antara device owner dan person tersebut
- Support search untuk filter messages

---

### 5. **Search Bar (Q Search)**
**UI Element:** Search bar untuk mencari teks dalam messages

**Endpoint:**
Sama dengan Chat Detail Viewer, menggunakan parameter `search`:
```
GET /api/v1/analytic/{analytic_id}/chat-detail?search={query}&platform={platform}&device_id={device_id}&person_name={person_name}
```

**Usage:**
- User ketik query di search bar
- Filter messages yang mengandung query text
- Bisa dikombinasikan dengan person_name filter

---

### 6. **Export PDF Button**
**UI Element:** Button "Export PDF" di header

**Endpoint:**
(Tidak ada endpoint khusus, ini client-side functionality untuk export data yang sudah di-fetch)

**Data yang bisa di-export:**
- Device tabs dari `deep-communication-analytics`
- Intensity list dari `interaction-intensity`
- Chat messages dari `chat-detail`

---

## Flow Diagram

```
1. Load Dashboard
   ↓
   GET /api/v1/analytic/{id}/deep-communication-analytics
   ↓
   Display: Device Tabs

2. User Select Device (optional)
   ↓
   Filter by device_id

3. User Select Platform (WhatsApp, Instagram, dll)
   ↓
   GET /api/v1/analytic/{id}/interaction-intensity?platform={platform}&device_id={device_id}
   ↓
   Display: List Person & Intensity Score

4. User Click Person
   ↓
   GET /api/v1/analytic/{id}/chat-detail?person_name={person}&platform={platform}&device_id={device_id}
   ↓
   Display: Chat Messages

5. User Search (optional)
   ↓
   GET /api/v1/analytic/{id}/chat-detail?person_name={person}&platform={platform}&search={query}
   ↓
   Display: Filtered Chat Messages
```

---

## Example API Calls untuk Complete Flow

### Step 1: Get Device Tabs
```bash
GET /api/v1/analytic/1/deep-communication-analytics
```

### Step 2: Get Intensity List for WhatsApp
```bash
GET /api/v1/analytic/1/interaction-intensity?platform=WhatsApp&device_id=1
```

### Step 3: Get Chat Detail for Person
```bash
GET /api/v1/analytic/1/chat-detail?person_name=Briani%20Akbar&platform=WhatsApp&device_id=1
```

### Step 4: Search in Chat (optional)
```bash
GET /api/v1/analytic/1/chat-detail?person_name=Briani%20Akbar&platform=WhatsApp&search=dompet&device_id=1
```

---

## Notes

- Semua endpoint menggunakan `analytic_id` sebagai path parameter
- `device_id` dan `platform` bisa digunakan sebagai filter di semua endpoint
- Response format konsisten dengan `status`, `message`, dan `data`
- Error handling sudah lengkap dengan status 400, 404, dan 500

