# Deep Communication Analytics - Response Structure

Dokumentasi lengkap struktur response untuk Deep Communication Analytics endpoints.

## Endpoint 1: Deep Communication Analytics

**URL:** `GET /api/v1/analytic/{analytic_id}/deep-communication-analytics`

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `platform` (optional): Filter by platform (jika ingin langsung dapat platform_analysis)

### Response Structure

```json
{
  "status": 200,
  "message": "Deep Communication Analytics retrieved successfully",
  "data": {
    "analytic_info": {
      "analytic_id": 1,
      "analytic_name": "Case Analysis #1"
    },
    "device_tabs": [
      {
        "device_id": 1,
        "device_name": "Rio",
        "phone_number": "08131323421"
      },
      {
        "device_id": 2,
        "device_name": "Paul",
        "phone_number": "08131323421"
      },
      {
        "device_id": 3,
        "device_name": "Mag",
        "phone_number": "0813"
      }
    ],
    "devices": [
      {
        "device_id": 1,
        "device_name": "Rio",
        "phone_number": "08131323421",
        "platform_cards": [
            {
              "platform": "Instagram",
              "platform_key": "instagram",
              "has_data": true,
              "message_count": 12,
              "person": "John Doe",
              "intensity": 8
            },
            {
              "platform": "Telegram",
              "platform_key": "telegram",
              "has_data": true,
              "message_count": 740,
              "person": "cuan cepat",
              "intensity": 197
            },
            {
              "platform": "WhatsApp",
              "platform_key": "whatsapp",
              "has_data": true,
              "message_count": 4599,
              "person": "Briani Akbar",
              "intensity": 810
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
            "has_data": false,
            "message_count": 0
          },
          {
            "platform": "TikTok",
            "platform_key": "tiktok",
            "has_data": false,
            "message_count": 0
          }
        ]
      }
    ],
    "platform_analysis": {
      "whatsapp": [
        {
          "person": "Briani Akbar",
          "person_id": "628987654321",
          "intensity": 810
        },
        {
          "person": "Iriana",
          "person_id": "628123456789",
          "intensity": 910
        }
      ]
    },
    "summary": {
      "total_devices": 3,
      "total_messages": 5351,
      "platforms_analyzed": ["whatsapp"]
    }
  }
}
```

### Field Descriptions

#### `device_tabs`
Array of device tabs untuk ditampilkan di slider atas dashboard.

- `device_id`: ID device
- `device_name`: Nama device owner
- `phone_number`: Nomor telepon device owner

#### `devices`
Array of devices dengan platform cards untuk setiap device.

- `device_id`: ID device
- `device_name`: Nama device owner
- `phone_number`: Nomor telepon device owner
- `platform_cards`: Array of platform cards (selalu 6 platform)

**Platform Card Structure:**
- `platform`: Display name platform (Instagram, Telegram, WhatsApp, Facebook, X, TikTok)
- `platform_key`: Key untuk API calls (instagram, telegram, whatsapp, facebook, x, tiktok)
- `has_data`: Boolean, apakah platform ini punya data (true) atau tidak (false)
- `message_count`: Jumlah messages untuk platform ini
- `person`: Nama person dengan intensity tertinggi untuk platform ini (null jika tidak ada data)
- `intensity`: Intensity score (jumlah messages) dari person dengan intensity tertinggi (0 jika tidak ada data)

**Notes:**
- Platform cards **selalu mengembalikan 6 platform** (semua platform yang didukung)
- Jika `has_data: false`, berarti platform tidak punya data (tampilkan "No information")
- Jika `has_data: true`, berarti platform punya data (bisa diklik untuk melihat interaction-intensity)

#### `platform_analysis`
Object yang hanya terisi jika parameter `platform` diberikan.

- Key: platform_key (lowercase, e.g., "whatsapp", "instagram")
- Value: Array of person dengan intensity score

**Platform Analysis Structure:**
- `person`: Nama person
- `person_id`: ID person (phone number atau platform-specific ID)
- `intensity`: Intensity score (jumlah messages)

### Usage Flow

#### 1. Initial Load (Dashboard Left Panel)
```bash
GET /api/v1/analytic/1/deep-communication-analytics
```

**Response:** 
- `device_tabs`: Untuk slider device tabs
- `devices`: Untuk setiap device, tampilkan platform cards
- Jika `has_data: false` → Tampilkan "No information"
- Jika `has_data: true` → Card bisa diklik

#### 2. User Select Device (Rio)
```bash
GET /api/v1/analytic/1/deep-communication-analytics?device_id=1
```

**Response:**
- Hanya return device dengan `device_id=1` di array `devices`
- Platform cards untuk device Rio saja

#### 3. User Click Platform Card (WhatsApp)
Frontend akan memanggil endpoint **interaction-intensity** (bukan deep-communication-analytics lagi):

```bash
GET /api/v1/analytic/1/interaction-intensity?platform=WhatsApp&device_id=1
```

---

## Endpoint 2: Interaction Intensity

**URL:** `GET /api/v1/analytic/{analytic_id}/interaction-intensity`

**Query Parameters:**
- `platform` (required): Platform name
- `device_id` (optional): Filter by device ID

### Response Structure

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
      },
      {
        "person": "Faturahman",
        "person_id": "628111222333",
        "intensity": 800
      }
    ],
    "summary": {
      "total_persons": 3,
      "total_messages": 2520,
      "devices_involved": [1]
    }
  }
}
```

### Usage

- Dipanggil ketika user **click platform card**
- Menampilkan list person dengan intensity score (sorted descending)
- User bisa click person untuk melihat chat detail

---

## Endpoint 3: Chat Detail

**URL:** `GET /api/v1/analytic/{analytic_id}/chat-detail`

**Query Parameters:**
- `person_name` (optional): Person name to filter
- `platform` (optional): Platform name
- `device_id` (optional): Filter by device ID
- `search` (optional): Search text in messages

### Response Structure

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
        "message_id": 123,
        "timestamp": "2024-01-15 20:12:00",
        "direction": "Incoming",
        "sender": "Briani Akbar",
        "recipient": "Rio",
        "sender_id": "628987654321",
        "recipient_id": "08131323421",
        "message_text": "Aku gak bisa tidur...",
        "message_type": "text",
        "platform": "WhatsApp",
        "thread_id": "",
        "chat_id": ""
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

### Usage

- Dipanggil ketika user **click person** dari intensity list
- Menampilkan semua chat messages antara device owner dan person tersebut
- Support search untuk filter messages

---

## Complete Flow Example

### Step 1: Load Dashboard
```bash
GET /api/v1/analytic/1/deep-communication-analytics
```
**Use:** `device_tabs` dan `devices[].platform_cards`

### Step 2: Select Device (Rio)
```bash
GET /api/v1/analytic/1/deep-communication-analytics?device_id=1
```
**Use:** `devices[0].platform_cards` (hanya untuk device Rio)

### Step 3: Click Platform Card (WhatsApp)
```bash
GET /api/v1/analytic/1/interaction-intensity?platform=WhatsApp&device_id=1
```
**Use:** `intensity_list` untuk ditampilkan di tabel

### Step 4: Click Person (Briani Akbar)
```bash
GET /api/v1/analytic/1/chat-detail?person_name=Briani%20Akbar&platform=WhatsApp&device_id=1
```
**Use:** `chat_messages` untuk ditampilkan di chat viewer

### Step 5: Search Messages (optional)
```bash
GET /api/v1/analytic/1/chat-detail?person_name=Briani%20Akbar&platform=WhatsApp&device_id=1&search=dompet
```
**Use:** `chat_messages` yang sudah di-filter berdasarkan search query

---

## Error Responses

### Status 400 - Bad Request
```json
{
  "status": 400,
  "message": "Invalid platform. Supported platforms: Instagram, Telegram, WhatsApp, Facebook, X, TikTok"
}
```

### Status 404 - Not Found
```json
{
  "status": 404,
  "message": "Analytic not found"
}
```

### Status 500 - Internal Server Error
```json
{
  "status": 500,
  "message": "Internal server error: Failed to retrieve deep communication analytics",
  "error": "Error details...",
  "data": null
}
```

---

## Platform Keys vs Display Names

| Platform Key | Display Name |
|--------------|--------------|
| `instagram`  | Instagram    |
| `telegram`   | Telegram     |
| `whatsapp`   | WhatsApp     |
| `facebook`   | Facebook     |
| `x`          | X            |
| `tiktok`     | TikTok       |

**Note:** Selalu gunakan `platform_key` untuk API calls, gunakan `platform` (display name) untuk UI display.

