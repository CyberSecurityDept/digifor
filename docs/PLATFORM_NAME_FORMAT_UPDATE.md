# Update: Platform Name Format ke Capitalized

## Perubahan

Platform names sekarang disimpan dalam format **capitalized** (proper case):
- ✅ `'telegram'` → `'Telegram'`
- ✅ `'whatsapp'` → `'WhatsApp'`
- ✅ `'instagram'` → `'Instagram'`
- ✅ `'facebook'` → `'Facebook'`
- ✅ `'tiktok'` → `'TikTok'`
- ✅ `'x'` → `'X'`

## Code Changes

### 1. Helper Function `_normalize_platform_name()`
**Location**: `app/analytics/utils/social_media_parsers_extended.py` line 25-49

```python
def _normalize_platform_name(self, platform: str) -> str:
    """
    Normalize platform name to proper capitalized format:
    - 'whatsapp' -> 'WhatsApp'
    - 'telegram' -> 'Telegram'
    - 'instagram' -> 'Instagram'
    - 'facebook' -> 'Facebook'
    - 'tiktok' -> 'TikTok'
    - 'x' -> 'X'
    """
    platform_lower = platform.lower().strip()
    platform_map = {
        'whatsapp': 'WhatsApp',
        'telegram': 'Telegram',
        'instagram': 'Instagram',
        'facebook': 'Facebook',
        'tiktok': 'TikTok',
        'x': 'X',
        'twitter': 'X'  # Twitter is now X
    }
    return platform_map.get(platform_lower, platform)
```

### 2. Updated Methods

#### `_parse_oxygen_messages_sheet()`
- **Location**: Line 2587-2589
- Platform dinormalize setelah detection, sebelum disimpan

#### `_parse_cellebrite_chats_messages()`
- **Location**: Line 2056-2058
- Platform dinormalize setelah detection

#### `_parse_oxygen_telegram_messages()`
- **Location**: Line 3387
- Hardcoded changed: `"platform": "telegram"` → `"platform": "Telegram"`

#### `axiom_parser.py` - `_parse_telegram_messages()`
- **Location**: Line 826
- Hardcoded changed: `"platform": "telegram"` → `"platform": "Telegram"`

## Update Data Existing di Database

Script untuk mengupdate data existing:

```bash
python scripts/update_platform_names.py
```

Script ini akan:
- Update semua `'telegram'` → `'Telegram'`
- Update semua `'whatsapp'` → `'WhatsApp'`
- Update semua `'instagram'` → `'Instagram'`
- Update semua `'facebook'` → `'Facebook'`
- Update semua `'tiktok'` → `'TikTok'`
- Update semua `'x'` → `'X'`

## Query Examples

Setelah update, gunakan capitalized format:

```sql
-- ✅ BENAR - Capitalized format
SELECT * FROM chat_messages WHERE platform = 'Telegram';
SELECT * FROM chat_messages WHERE platform = 'WhatsApp';
SELECT * FROM chat_messages WHERE platform = 'Instagram';
SELECT * FROM chat_messages WHERE platform = 'Facebook';
SELECT * FROM chat_messages WHERE platform = 'TikTok';
SELECT * FROM chat_messages WHERE platform = 'X';

-- ❌ SALAH - Lowercase (tidak akan match)
SELECT * FROM chat_messages WHERE platform = 'telegram';
```

Atau gunakan case-insensitive:

```sql
-- ✅ Case-insensitive
SELECT * FROM chat_messages WHERE platform ILIKE 'telegram';
SELECT * FROM chat_messages WHERE LOWER(platform) = 'telegram';
```

## Testing

Setelah menjalankan script update:

```sql
-- Check platform distribution
SELECT platform, COUNT(*) 
FROM chat_messages 
GROUP BY platform 
ORDER BY platform;
```

Expected output:
```
platform  | count
----------|------
Facebook  |  8
Telegram  |  5
WhatsApp  | 15848
X         | 10
```

## Migration Steps

1. **Update Code** ✅ (Sudah dilakukan)
   - Helper function ditambahkan
   - Methods diupdate untuk normalize platform

2. **Update Existing Data**
   ```bash
   python scripts/update_platform_names.py
   ```

3. **Verify**
   ```sql
   SELECT platform, COUNT(*) FROM chat_messages GROUP BY platform;
   ```

4. **Test New Uploads**
   - Upload file baru
   - Verify platform tersimpan sebagai capitalized format

## Impact

### ✅ Positive
- Format konsisten dan professional
- Cocok dengan format UI/display
- Query lebih readable dengan capitalized names

### ⚠️ Breaking Changes
- **API queries perlu diupdate** jika menggunakan exact match
- Existing queries dengan lowercase tidak akan match (kecuali pakai ILIKE)

### 🔧 Mitigation
- Gunakan `ILIKE` atau `LOWER()` function untuk case-insensitive queries
- Atau update semua queries ke capitalized format

## Rollback (Jika Diperlukan)

Jika perlu rollback, jalankan:

```sql
-- Rollback to lowercase
UPDATE chat_messages SET platform = LOWER(platform);
```

Lalu revert code changes.

