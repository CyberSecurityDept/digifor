# Perbedaan Message Count vs Intensity

## Penjelasan Singkat

- **`message_count`**: Total semua pesan di platform tersebut untuk device tersebut (dari semua person)
- **`intensity`**: Jumlah pesan dari **1 person saja** (person dengan intensity tertinggi/top person)

---

## Detail Penjelasan

### 1. Message Count

**Definisi:**
- **Total jumlah semua pesan** di platform tersebut untuk device tersebut
- Menghitung semua pesan tanpa peduli dari siapa pesannya
- Bisa dari banyak person yang berbeda

**Cara Perhitungan:**
```python
# Count semua messages untuk platform ini
platform_messages = [msg for msg in device_messages 
                     if normalize_platform_name(msg.platform or '') == platform_key]
message_count = len(platform_messages)  # Total semua pesan
```

**Contoh:**
- Platform WhatsApp punya **4599 pesan total**
- Ini berarti ada 4599 pesan dari semua person yang berkomunikasi dengan device owner di WhatsApp

---

### 2. Intensity

**Definisi:**
- **Jumlah pesan dari 1 person saja** (person dengan intensity tertinggi)
- Menunjukkan person yang paling aktif berkomunikasi dengan device owner di platform tersebut
- Hanya menghitung pesan dari person tersebut, bukan dari semua person

**Cara Perhitungan:**
```python
# Hitung intensity untuk setiap person
for msg in platform_messages:
    person_name = identify_person_from_message(msg)
    person_intensity[person_name] += 1

# Ambil person dengan intensity tertinggi
top_person = sorted(person_intensity.items(), key=lambda x: x[1], reverse=True)[0]
intensity = top_person["intensity"]  # Jumlah pesan dari person tersebut
```

**Contoh:**
- Platform WhatsApp punya **4599 pesan total** (message_count)
- Person "Briani Akbar" punya **810 pesan** (intensity)
- Artinya ada **4599 - 810 = 3789 pesan** dari person lain (bisa lebih dari 1 person)

---

## Contoh Lengkap

### Platform WhatsApp

```json
{
  "platform": "WhatsApp",
  "platform_key": "whatsapp",
  "has_data": true,
  "message_count": 4599,        // ← Total semua pesan dari semua person
  "person": "Briani Akbar",       // ← Person dengan intensity tertinggi
  "intensity": 810                // ← Jumlah pesan dari "Briani Akbar" saja
}
```

**Breakdown:**
- Total pesan WhatsApp: **4599 pesan**
- Pesan dari "Briani Akbar": **810 pesan** (intensity)
- Pesan dari person lain: **4599 - 810 = 3789 pesan**

Mungkin ada beberapa person lain seperti:
- Person A: 500 pesan
- Person B: 1000 pesan
- Person C: 1000 pesan
- Person D: 1289 pesan
- **Total: 3789 pesan**

---

## Perbandingan Visual

| Field | Scope | Description |
|-------|-------|-------------|
| **message_count** | Platform-wide | Total semua pesan di platform (dari semua person) |
| **intensity** | Single person | Jumlah pesan dari person dengan intensity tertinggi saja |

---

## Use Case

### Message Count
- **Gunakan untuk**: Menunjukkan volume komunikasi total di platform
- **Contoh UI**: "WhatsApp: 4599 messages total"

### Intensity
- **Gunakan untuk**: Menunjukkan person yang paling aktif
- **Contoh UI**: "Top contact: Briani Akbar (810 messages)"

---

## Real Example dari Platform Cards

```json
{
  "platform_cards": [
    {
      "platform": "WhatsApp",
      "platform_key": "whatsapp",
      "has_data": true,
      "message_count": 4599,      // Total: 4599 pesan dari semua person
      "person": "Briani Akbar",    // Top person
      "intensity": 810             // 810 pesan dari "Briani Akbar"
    },
    {
      "platform": "Telegram",
      "platform_key": "telegram",
      "has_data": true,
      "message_count": 740,       // Total: 740 pesan dari semua person
      "person": "cuan cepat",     // Top person
      "intensity": 197             // 197 pesan dari "cuan cepat"
    }
  ]
}
```

---

## Kesimpulan

- **`message_count`** = Total semua pesan (bigger number, includes all persons)
- **`intensity`** = Pesan dari top person saja (smaller number, single person)

**Rule of thumb:**
- `message_count` ≥ `intensity` (selalu lebih besar atau sama, karena intensity adalah subset dari message_count)
- Jika `message_count == intensity`, berarti hanya ada 1 person yang berkomunikasi
- Jika `message_count > intensity`, berarti ada lebih dari 1 person yang berkomunikasi

