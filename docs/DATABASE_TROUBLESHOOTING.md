# Database Troubleshooting Guide

Panduan untuk mengatasi masalah koneksi database dan tabel tidak muncul di database client.

## 🔍 Masalah: Tabel Tidak Muncul di Database Client

### Penyebab Umum

1. **Connect ke database yang salah**
   - Connect ke database `postgres` (default) bukan `db_forensics`
   - Tabel ada di database `db_forensics`, bukan `postgres`

2. **Melihat schema yang salah**
   - Tabel ada di schema `public`, bukan `information_schema`
   - Pastikan expand: `Schemas → public → Tables`

3. **Cache client database**
   - Client belum di-refresh setelah tabel dibuat
   - Perlu reconnect atau refresh

4. **Koneksi ke server yang berbeda**
   - Connect ke IP server yang salah
   - Atau connect ke localhost padahal seharusnya ke IP server

## Solusi Step-by-Step

### 1. Verifikasi Koneksi dengan Script

Jalankan script verifikasi untuk memastikan koneksi benar:

```bash
python3 scripts/verify-db-connection.py
```

Script ini akan menampilkan:
- Database yang terhubung
- IP server yang digunakan
- Semua tabel yang ada
- Permissions user

### 2. Cek Konfigurasi di .env

Pastikan file `.env` memiliki konfigurasi yang benar:

```env
POSTGRES_HOST=localhost          # atau IP server (contoh: 172.15.2.160)
POSTGRES_PORT=5432
POSTGRES_USER=digifor
POSTGRES_PASSWORD=passwordD*8
POSTGRES_DB=db_forensics
DATABASE_URL=postgresql://digifor:passwordD*8@localhost:5432/db_forensics
```

### 3. Panduan untuk Database Client

#### **pgAdmin:**

1. **Pastikan connect ke database yang benar:**
   - Di sidebar kiri, expand: `Servers → [Your Server] → Databases`
   - Klik kanan pada `db_forensics` → **Refresh**
   - JANGAN gunakan database `postgres`

2. **Lihat tabel:**
   - Expand: `db_forensics → Schemas → public → Tables`
   - Jika tidak muncul, klik kanan pada `public` → **Refresh**

3. **Cek koneksi:**
   - Klik kanan pada server → **Properties**
   - Pastikan Host: `localhost` atau IP server yang benar
   - Pastikan Port: `5432`

#### **DBeaver:**

1. **Pastikan connect ke database yang benar:**
   - Di Database Navigator, expand: `Databases → db_forensics`
   - Klik kanan pada `db_forensics` → **Refresh**

2. **Lihat tabel:**
   - Expand: `db_forensics → Schemas → public → Tables`
   - Tekan `F5` untuk refresh

3. **Cek koneksi:**
   - Klik kanan pada connection → **Edit Connection**
   - Tab **Main**: Pastikan Database: `db_forensics`
   - Tab **Main**: Pastikan Host: `localhost` atau IP server yang benar
   - Tab **Main**: Pastikan Port: `5432`

#### **psql (Command Line):**

```bash
# Connect ke database
psql -h localhost -U digifor -d db_forensics

# Atau jika ke IP server:
psql -h 172.15.2.160 -U digifor -d db_forensics

# List semua tabel
\dt

# List semua tabel dengan detail
\dt+

# List semua database
\l

# List semua schema
\dn
```

### 4. Update Konfigurasi ke IP Server

Jika Anda perlu connect ke IP server (bukan localhost):

**Cara Manual:**

Edit file `.env`:
```bash
nano .env
# atau
vim .env
```

Ubah:
```env
POSTGRES_HOST=172.15.2.160  # ganti dengan IP server Anda
DATABASE_URL=postgresql://digifor:passwordD*8@172.15.2.160:5432/db_forensics
```

**Cara Otomatis (Script):**

```bash
chmod +x update-db-to-server.sh
./update-db-to-server.sh
```

Script akan meminta IP server dan mengupdate konfigurasi otomatis.

### 5. Test Koneksi Setelah Update

Setelah mengubah konfigurasi:

```bash
# Test koneksi
python3 scripts/check-db-connection.py

# Verifikasi lengkap
python3 scripts/verify-db-connection.py

# List semua tabel
python3 scripts/list-tables.py
```

### 6. Jika Masih Tidak Muncul

1. **Cek apakah tabel benar-benar ada:**
   ```bash
   python3 scripts/verify-db-connection.py
   ```
   Jika script menunjukkan tabel ada, berarti masalah di client database.

2. **Recreate tabel (jika perlu):**
   ```bash
   python3 tools/setup_postgres.py
   ```
   Atau:
   ```python
   from app.db.session import engine
   from app.db.base import Base
   from app.auth.models import *
   from app.analytics.shared.models import *
   from app.case_management.models import *
   from app.evidence_management.models import *
   from app.suspect_management.models import *
   Base.metadata.create_all(bind=engine)
   ```

3. **Cek permissions:**
   - Pastikan user `digifor` memiliki akses ke database `db_forensics`
   - Pastikan user memiliki akses ke schema `public`

4. **Reconnect di client:**
   - Disconnect dan connect ulang
   - Atau restart client database

## 🔧 Script-Script yang Tersedia

Semua script database ada di folder `scripts/`:

1. **scripts/check-db-connection.py** - Test koneksi database
2. **scripts/verify-db-connection.py** - Verifikasi lengkap koneksi dan tabel
3. **scripts/list-tables.py** - List semua tabel dengan detail
4. **scripts/init-database.py** - Initialize database (membuat tabel jika belum ada)
5. **update-db-to-server.sh** - Update konfigurasi ke IP server

## 📝 Checklist

- [ ] Konfigurasi `.env` benar (host, port, database, user, password)
- [ ] Connect ke database `db_forensics` (bukan `postgres`)
- [ ] Melihat schema `public` (bukan schema lain)
- [ ] Client database sudah di-refresh
- [ ] IP server benar (jika connect ke remote)
- [ ] User memiliki permissions yang cukup
- [ ] Tabel benar-benar ada (verifikasi dengan script)

## 🆘 Masih Bermasalah?

Jika setelah semua langkah di atas tabel masih tidak muncul:

1. **Cek log aplikasi:**
   ```bash
   sudo journalctl -u digifor-v2 -n 50
   ```

2. **Test koneksi manual:**
   ```bash
   psql -h localhost -U digifor -d db_forensics -c "\dt"
   ```

3. **Cek apakah aplikasi bisa connect:**
   ```bash
   curl http://localhost:8000/health/health
   ```

4. **Cek firewall:**
   - Pastikan port 5432 terbuka
   - Jika connect ke remote, pastikan firewall mengizinkan koneksi

---

**Terakhir diupdate:** 2025-11-04

