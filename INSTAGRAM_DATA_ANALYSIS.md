# Analisis Data Instagram Messages

## Struktur Data

Berdasarkan data yang diberikan, berikut adalah breakdown kolom-kolomnya:

### Message 36 (Outgoing)
```
id: 36
file_id: 1
platform: "Instagram"
message_text: "Main ig juga mas"
from_name: "Nurcahya Hikari"
sender_number: "hikari_noeer"
to_name: "340282366841710301244259523079730425447" ❌ (MASALAH!)
recipient_number: (kosong)
timestamp: "2025-10-17 13:40:21"
thread_id: "707651c78965f2c17cf01ec7b25b14f0"
chat_id: "707651c78965f2c17cf01ec7b25b14f0"
message_id: "32478872785078946743965924968103936"
message_type: "text"
direction: "Outgoing"
source_tool: "oxygen"
sheet_name: "Messages "
```

### Message 37 (Incoming)
```
id: 37
file_id: 1
platform: "Instagram"
message_text: "Iyo"
from_name: "25130295109"
sender_number: (kosong)
to_name: "340282366841710301244259523079730425447" ❌ (MASALAH!)
recipient_number: (kosong)
timestamp: "2025-10-17 13:40:44"
thread_id: "707651c78965f2c17cf01ec7b25b14f0"
chat_id: "707651c78965f2c17cf01ec7b25b14f0"
message_id: "32478873207756332594829406741987328"
message_type: "text"
direction: "Incoming"
source_tool: "oxygen"
sheet_name: "Messages "
```

### Message 38 (Outgoing)
```
id: 38
file_id: 1
platform: "Instagram"
message_text: "Folbek dulu lah"
from_name: "Nurcahya Hikari"
sender_number: "hikari_noeer"
to_name: "340282366841710301244259523079730425447" ❌ (MASALAH!)
recipient_number: (kosong)
timestamp: "2025-10-17 13:40:49"
thread_id: "707651c78965f2c17cf01ec7b25b14f0"
chat_id: "707651c78965f2c17cf01ec7b25b14f0"
message_id: "32478873298932150637493995746361344"
message_type: "text"
direction: "Outgoing"
source_tool: "oxygen"
sheet_name: "Messages "
```

### Message 39 (Incoming)
```
id: 39
file_id: 1
platform: "Instagram"
message_text: "Done"
from_name: "25130295109"
sender_number: (kosong)
to_name: "340282366841710301244259523079730425447" ❌ (MASALAH!)
recipient_number: (kosong)
timestamp: "2025-10-17 13:41:13"
thread_id: "707651c78965f2c17cf01ec7b25b14f0"
chat_id: "707651c78965f2c17cf01ec7b25b14f0"
message_id: "32478873743736092410122831621259264"
message_type: "text"
direction: "Incoming"
source_tool: "oxygen"
sheet_name: "Messages "
```

## Identifikasi Masalah

### 1. **Masalah Mapping `to_name`**
- **Nilai yang salah**: `"340282366841710301244259523079730425447"` (39 karakter, terlalu panjang untuk nama)
- **Kemungkinan**: Nilai ini seharusnya di field lain (mungkin chat_id atau identifier lain)
- **Dampak**: Ketika direction="Outgoing", sistem mengambil `to_name` sebagai person, padahal nilainya adalah ID panjang yang bukan nama orang

### 2. **Struktur Data yang Benar**

Berdasarkan arah pesan:

**Outgoing (Device Owner → Person):**
- `from_name` = "Nurcahya Hikari" ✅ (Device Owner)
- `sender_number` = "hikari_noeer" ✅
- `to_name` = Seharusnya "25130295109" atau nama person ❌ (Saat ini salah)
- `recipient_number` = Seharusnya ada ID person ❌ (Kosong)

**Incoming (Person → Device Owner):**
- `from_name` = "25130295109" ✅ (Person - BENAR!)
- `sender_number` = Seharusnya ada ID person ❌ (Kosong)
- `to_name` = Seharusnya "Nurcahya Hikari" atau nama device owner ❌ (Saat ini salah)
- `recipient_number` = Seharusnya "hikari_noeer" ❌ (Kosong)

### 3. **Kesimpulan**

Masalahnya ada di **parsing data dari Excel/CSV ke database**. Field `to_name` diisi dengan nilai yang seharusnya bukan nama orang (kemungkinan Chat ID atau identifier lain).

## Solusi untuk Endpoint Intensity

Karena data sudah tersimpan dengan mapping yang salah, kita perlu:

1. **Untuk Incoming messages**: ✅ SUDAH BENAR
   - Gunakan `from_name` = "25130295109" sebagai person ✅

2. **Untuk Outgoing messages**: ❌ PERLU PERBAIKAN
   - Jangan gunakan `to_name` jika nilainya terlalu panjang (>50 karakter) atau terlihat seperti ID
   - Skip message jika `to_name` tidak valid
   - Atau gunakan logika fallback yang lebih baik

## Rekomendasi Perbaikan

1. **Perbaiki parser Instagram** untuk memastikan `to_name` dan `recipient_number` diisi dengan benar
2. **Perbaiki endpoint intensity** untuk:
   - Skip `to_name` jika terlalu panjang (seperti chat_id)
   - Gunakan `recipient_number` jika tersedia dan valid
   - Jika tidak ada data valid, skip message tersebut

