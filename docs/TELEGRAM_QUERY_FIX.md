# Fix: Query Telegram Messages

## Masalah

Query ini tidak mengembalikan data:
```sql
SELECT * FROM chat_messages WHERE platform = 'Telegram';
```

## Penyebab

**Case Sensitivity**: Data disimpan sebagai lowercase `'telegram'`, tapi query menggunakan capitalized `'Telegram'`.

PostgreSQL case-sensitive, jadi:
- ✅ `platform = 'telegram'` → 5 rows (BERHASIL)
- ❌ `platform = 'Telegram'` → 0 rows (GAGAL)
- ❌ `platform = 'TELEGRAM'` → 0 rows (GAGAL)

## Solusi

### Opsi 1: Gunakan Lowercase (Recommended)
```sql
SELECT * 
FROM chat_messages 
WHERE platform = 'telegram';
```

### Opsi 2: Gunakan ILIKE (Case-Insensitive)
```sql
SELECT * 
FROM chat_messages 
WHERE platform ILIKE 'telegram';
```

### Opsi 3: Lower Function
```sql
SELECT * 
FROM chat_messages 
WHERE LOWER(platform) = 'telegram';
```

## Verifikasi Data Ada

Dari log parsing:
- ✅ Platform detected: `'telegram'` (6 messages parsed)
- ✅ Platform breakdown: `{'telegram': 6}`
- ✅ Total saved: 15871 messages

Dari database check:
- ✅ Platform `"telegram"`: 5 rows
- ✅ Messages tersimpan dengan benar

## Query Lengkap

```sql
-- Get all Telegram messages
SELECT 
    id,
    file_id,
    platform,
    message_text,
    from_name,
    sender_number,
    to_name,
    recipient_number,
    timestamp,
    thread_id,
    chat_id,
    message_id,
    message_type,
    direction
FROM chat_messages 
WHERE platform = 'telegram'
ORDER BY timestamp;
```

## Platform Values di Database

Semua platform disimpan sebagai **lowercase**:
- `'telegram'`
- `'whatsapp'`
- `'instagram'`
- `'facebook'`
- `'x'` (bukan 'twitter')

Jadi selalu gunakan lowercase dalam query!

