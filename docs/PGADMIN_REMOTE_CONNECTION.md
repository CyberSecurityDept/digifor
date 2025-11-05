# Panduan Remote Connection PostgreSQL dengan pgAdmin4

Panduan lengkap untuk connect ke PostgreSQL server remote dari pgAdmin4 lokal dan melihat tabel.

## 🔍 Masalah: Tabel Tidak Muncul di pgAdmin4

### Penyebab Umum

1. **Connect ke database yang salah**
   - Connect ke database `postgres` (default) bukan `db_forensics`
   - Tabel ada di database `db_forensics`

2. **Tabel belum dibuat di database remote**
   - Tabel hanya ada di database lokal, belum di remote
   - Perlu run `init-database.py` untuk membuat tabel di remote

3. **Melihat schema yang salah**
   - Tabel ada di schema `public`, bukan schema lain

4. **Cache pgAdmin4**
   - Perlu refresh setelah tabel dibuat

## ✅ Solusi Step-by-Step

### 1. Pastikan Tabel Ada di Database Remote

Jalankan script untuk membuat tabel di database remote:

```bash
cd /home/digifor/digifor-v2
source venv/bin/activate
python3 scripts/init-database.py
```

Atau verifikasi apakah tabel sudah ada:

```bash
python3 scripts/verify-db-connection.py
python3 scripts/list-tables.py
```

### 2. Setup Remote Connection di pgAdmin4

#### **Langkah 1: Buat Server Connection**

1. Buka pgAdmin4
2. Klik kanan pada **Servers** di sidebar kiri
3. Pilih **Create** → **Server...**

#### **Langkah 2: Konfigurasi General Tab**

- **Name:** `Digifor Remote Server` (atau nama lain)
- **Server Group:** `Servers` (default)

#### **Langkah 3: Konfigurasi Connection Tab**

**Connection Settings:**
- **Host name/address:** `172.15.2.105` (IP server remote)
- **Port:** `5432`
- **Maintenance database:** `postgres` (untuk koneksi awal)
- **Username:** `digifor`
- **Password:** `passwordD*8` (atau password Anda)
- **Save password?:** ✅ Centang (opsional, untuk convenience)

**Advanced Settings (Opsional):**
- **DB restriction:** `db_forensics` (hanya tampilkan database ini)

#### **Langkah 4: Test Connection**

1. Klik **Save** untuk menyimpan connection
2. pgAdmin4 akan mencoba connect
3. Jika berhasil, server akan muncul di sidebar

### 3. Connect ke Database yang Benar

**PENTING:** Pastikan connect ke database `db_forensics`, bukan `postgres`!

1. Di sidebar, expand: `Servers → Digifor Remote Server → Databases`
2. Klik kanan pada **`db_forensics`** → **Connect Server**
3. JANGAN gunakan database `postgres` (database default)

### 4. Lihat Tabel

1. Expand: `db_forensics → Schemas → public → Tables`
2. Jika tabel tidak muncul:
   - Klik kanan pada **`public`** → **Refresh**
   - Atau klik kanan pada **`db_forensics`** → **Refresh**
   - Tekan `F5` untuk refresh

### 5. Verifikasi Tabel

Jika masih tidak muncul, verifikasi dengan query:

1. Klik kanan pada **`db_forensics`** → **Query Tool**
2. Jalankan query:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```

Atau:
```sql
\dt
```

## 🔧 Troubleshooting

### Tabel Tidak Muncul Setelah Refresh

**Solusi 1: Pastikan Tabel Sudah Dibuat**

Di server remote, jalankan:
```bash
cd /home/digifor/digifor-v2
source venv/bin/activate
python3 scripts/init-database.py
python3 scripts/list-tables.py
```

**Solusi 2: Cek Database yang Benar**

Pastikan Anda melihat database `db_forensics`, bukan `postgres`:
- ✅ `db_forensics → Schemas → public → Tables`
- ❌ `postgres → Schemas → public → Tables`

**Solusi 3: Cek Schema**

Pastikan melihat schema `public`:
- ✅ `Schemas → public → Tables`
- ❌ `Schemas → information_schema → Tables`

**Solusi 4: Cek Permissions**

Pastikan user `digifor` memiliki akses:
```sql
-- Cek permissions
SELECT 
    has_database_privilege('digifor', 'db_forensics', 'CONNECT') as can_connect,
    has_schema_privilege('digifor', 'public', 'USAGE') as can_use_schema,
    has_schema_privilege('digifor', 'public', 'CREATE') as can_create;
```

### Connection Timeout atau Gagal

**Solusi 1: Cek Firewall**

Pastikan port 5432 terbuka di server remote:
```bash
# Di server remote
sudo ufw status
sudo ufw allow 5432/tcp
```

**Solusi 2: Cek PostgreSQL Config**

Di server remote, edit `/etc/postgresql/14/main/postgresql.conf`:
```conf
listen_addresses = '*'  # atau '0.0.0.0'
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:
```conf
# Allow remote connections
host    all             all             0.0.0.0/0               md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

**Solusi 3: Test Connection dari Command Line**

Test dari komputer lokal:
```bash
psql -h 172.15.2.105 -U digifor -d db_forensics
```

### Masalah Authentication

Jika ada error authentication:

1. **Cek password di .env:**
   ```bash
   grep POSTGRES_PASSWORD /home/digifor/digifor-v2/.env
   ```

2. **Reset password (jika perlu):**
   ```sql
   -- Di server remote, sebagai postgres user
   ALTER USER digifor WITH PASSWORD 'new_password';
   ```

## 📋 Checklist

- [ ] Tabel sudah dibuat di database remote (`init-database.py` sudah dijalankan)
- [ ] Connect ke database `db_forensics` (bukan `postgres`)
- [ ] Melihat schema `public` (bukan schema lain)
- [ ] pgAdmin4 sudah di-refresh
- [ ] Port 5432 terbuka di firewall
- [ ] PostgreSQL config mengizinkan remote connection
- [ ] User `digifor` memiliki permissions yang cukup

## 🔍 Verifikasi Manual

### Dari Server Remote

```bash
# Test koneksi
psql -h 172.15.2.105 -U digifor -d db_forensics -c "\dt"

# List semua tabel
psql -h 172.15.2.105 -U digifor -d db_forensics -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
```

### Dari Script Python

```bash
cd /home/digifor/digifor-v2
source venv/bin/activate
python3 scripts/verify-db-connection.py
python3 scripts/list-tables.py
```

## 💡 Tips

1. **Gunakan Query Tool untuk Verifikasi:**
   - Buka Query Tool di pgAdmin4
   - Jalankan `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';`
   - Harus menunjukkan jumlah tabel (23 tabel)

2. **Refresh Secara Berkala:**
   - Setelah membuat tabel baru, refresh di pgAdmin4
   - Gunakan `F5` atau klik kanan → Refresh

3. **Cek Logs:**
   - Di server remote, cek logs untuk melihat aktivitas:
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-14-main.log
   ```

---

**Terakhir diupdate:** 2025-11-04

