# 📋 DOKUMENTASI MAPPING FIELD SOCIAL MEDIA

Dokumen ini menjelaskan mapping field `account_name`, `account_id`, `user_id`, dan `profile_picture_url` dari berbagai tool forensic.

## 🔍 Definisi Field

- **account_name**: Username yang bisa berubah (misal: @username, username)
- **account_id**: Identifier yang unik dan tidak berubah (harus digunakan untuk correlation)
- **user_id**: ID numeric yang unik untuk user (biasanya sama dengan account_id)
- **profile_picture_url**: URL gambar profil

## ⚠️ Prinsip Penting

1. **account_id harus selalu menggunakan identifier yang unik** (bukan username)
   - Instagram: User ID (numeric)
   - WhatsApp: Phone Number (normalized)
   - X/Twitter: User ID (numeric)
   - Telegram: Account ID atau User ID (numeric)
   
2. **account_name adalah username yang bisa berubah**, tidak cocok untuk correlation

3. **Untuk correlation analysis, gunakan account_id**, bukan account_name

---

## 🔵 OXYGEN FORENSICS

### Instagram

#### Users-Following Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `User name` | Username |
| account_id | `User ID` | Numeric ID (UNIK) |
| user_id | `User ID` | Numeric ID |
| profile_picture_url | `User picture URL` | Direct URL |

#### Users-Followers Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `User name` | Username |
| account_id | `UID` | Numeric ID (UNIK) |
| user_id | `UID` | Numeric ID |
| profile_picture_url | `User picture URL` | Direct URL |

### X/Twitter

#### Users-Followers Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `User name` | Username |
| account_id | `UID` | Numeric ID (UNIK) |
| user_id | `UID` | Numeric ID |
| profile_picture_url | `User picture URL` | Direct URL |

#### Tweets-Following / Tweets-Other
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `User name` | Username |
| account_id | `User ID` | Numeric ID (UNIK) |
| user_id | `User ID` | Numeric ID |
| profile_picture_url | `None` | Tidak ada di sheet ini |

### Contacts Sheet (All Platforms)

Field-field di-extract menggunakan pattern regex:

#### account_id
- **Instagram**: `r'Instagram ID:\s*(\S+)'` dari `Internet` field
- **Facebook**: `r'Facebook ID:\s*(\S+)'` dari `Internet` field
- **Telegram**: `r'Telegram ID:\s*(\S+)'` dari `Internet` field
- **X/Twitter**: `r'Account name:\s*(\S+)'` dari `Internet` field
- **WhatsApp**: `r'(WhatsApp|Phone)\s*(ID|number):\s*([+\d\s\-\(\)]+)'` dari `Internet` atau `Phones & Emails` field

#### user_id
- **Instagram**: `r'instagram\s+id[:\s]*(\d+)'` dari `Internet` atau `Phones & Emails` field
- **X/Twitter**: `r'x\s+id[:\s]*(\d+)'` atau `r'twitter\s+id[:\s]*(\d+)'`
- **Telegram**: `r'telegram\s+id[:\s]*(\d+)'`

#### profile_picture_url
- Pattern: `r'https?://[^\s]+\.(?:jpg|jpeg|png|gif)'` dari `Internet` field

---

## 🔴 MAGNET AXIOM

### Instagram Profiles Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `User Name` | Username |
| account_id | `User ID` | Numeric ID (UNIK) - **PERBAIKAN: Sebelumnya menggunakan username** |
| user_id | `User ID` | Numeric ID |
| profile_picture_url | `Profile Picture URL` | Direct URL |

### Android Instagram Following Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `User Name` | Username |
| account_id | `ID` | Numeric ID (UNIK) - **PERBAIKAN: Sebelumnya menggunakan username** |
| user_id | `ID` | Numeric ID |
| profile_picture_url | `Profile Picture URL` | Direct URL |

### Android Instagram Users Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `User Name` | Username |
| account_id | `ID` | Numeric ID (UNIK) - **PERBAIKAN: Sebelumnya menggunakan username** |
| user_id | `ID` | Numeric ID |
| profile_picture_url | `Profile Picture URL` | Direct URL (jika ada) |

### Twitter Users Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `Screen Name` atau `User Name` | Username |
| account_id | `User ID` | Numeric ID (UNIK) - **PERBAIKAN: Sebelumnya menggunakan username** |
| user_id | `User ID` | Numeric ID |
| profile_picture_url | `Image URL` | Direct URL |

### Telegram Accounts Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `User Name` atau `First Name` + `Last Name` | Username atau Full Name |
| account_id | `Account ID` (atau `User ID` jika tidak ada) | Account ID (UNIK) |
| user_id | `User ID` | Numeric ID |
| profile_picture_url | `None` | Biasanya tidak ada |

### WhatsApp Accounts Information / User Profiles
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `WhatsApp Name` | Display name |
| account_id | `Phone Number` | Phone number (normalized) - UNIK |
| user_id | `Phone Number` | Phone number (sama dengan account_id) |
| profile_picture_url | `None` atau kolom khusus | Biasanya tidak ada |

---

## 🟢 CELEBRITE

### Social Media Sheet
| Field | Source Column | Notes |
|-------|---------------|-------|
| account_name | `Author` field (bagian setelah user_id) | Extract dari parsing string |
| account_id | `Author` field (bagian pertama) atau `Account` column | User ID (numeric) atau Account name |
| user_id | `Author` field (bagian pertama) | User ID (numeric) |
| profile_picture_url | `URL` column | Direct URL |

### User Accounts Sheet
| Field | Source | Notes |
|-------|--------|-------|
| account_name | `Username` column | Username |
| account_id | Extract dari `Entries` field | Pattern: `User ID-<value>`, `User Id: <value>`, `WhatsApp User Id: <value>`, `Facebook Id: <value>`. Jika tidak ada, gunakan `Username` |
| user_id | Extract dari `Entries` field | Sama dengan account_id |
| profile_picture_url | Extract dari `Entries` field | Pattern: `Profile Picture-<value>`, `Profile Picture Url: <value>`, `Pic Square: <value>`, `profile_picture_url: <value>` |

### Contacts Sheet
| Field | Source | Notes |
|-------|--------|-------|
| account_name | Extract dari URL/pattern | Instagram: `instagram.com/(username)`, Facebook: `Facebook Id: (id)`, WhatsApp: `(+phone)@s.whatsapp.net`, Twitter: `twitter.com/(username)`, TikTok: `tiktok.com/@(username)`, Telegram: `@(username)` |
| account_id | Sama dengan account_name | Untuk kebanyakan platform |
| user_id | Sama dengan account_id | |
| profile_picture_url | `None` | Tidak ada di Contacts sheet |

### Chats Sheet
| Field | Source | Notes |
|-------|--------|-------|
| account_name | Extract dari `Participants` field | Bagian setelah user_id |
| account_id | Extract dari `Participants` field | Bagian pertama (user_id) |
| user_id | Extract dari `Participants` field | Bagian pertama |
| profile_picture_url | `None` | Tidak ada di Chats sheet |

---

## ✅ Perbaikan yang Sudah Dilakukan

1. **Magnet Axiom Instagram**: 
   - ❌ Sebelumnya: `account_id = User Name` (username)
   - ✅ Sekarang: `account_id = User ID` (numeric ID)

2. **Magnet Axiom X/Twitter**:
   - ❌ Sebelumnya: `account_id = User Name` (username)
   - ✅ Sekarang: `account_id = User ID` (numeric ID)

3. **Magnet Axiom Telegram**:
   - ✅ Sudah benar: `account_id = Account ID` atau `User ID`

4. **Oxygen Instagram**:
   - ✅ Sudah benar: `account_id = User ID` atau `UID` (numeric)

---

## 📝 Rekomendasi Penggunaan

Untuk **correlation analysis**, selalu gunakan:
- ✅ `account_id` (identifier unik)
- ❌ Jangan gunakan `account_name` (bisa berubah)

Query correlation endpoint sudah menggunakan:
```sql
LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) AS account_identifier
```

Ini berarti akan fallback ke `account_name` jika `account_id` tidak ada, tapi sebaiknya selalu pastikan `account_id` terisi dengan nilai yang benar.

---

## 🔧 Troubleshooting

Jika correlation tidak ditemukan:

1. Cek apakah `account_id` sudah terisi dengan benar (bukan username)
2. Pastikan `account_id` menggunakan identifier yang unik dan konsisten
3. Verifikasi normalisasi account_id (lowercase, trimmed, dll)
4. Cek apakah ada data di multiple file_id dengan account_id yang sama

