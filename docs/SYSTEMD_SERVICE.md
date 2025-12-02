# Systemd Service untuk Digital Forensics API

Dokumentasi ini menjelaskan cara menginstall dan menggunakan systemd service untuk menjalankan Digital Forensics API secara otomatis.

## Persyaratan

1. Ubuntu dengan systemd (sudah terinstall secara default)
2. Aplikasi sudah dikonfigurasi dengan benar
3. File `.env` sudah ada di direktori project dan dikonfigurasi dengan benar
4. Virtual environment (`venv`) sudah dibuat dan dependencies sudah diinstall
5. Database PostgreSQL sudah berjalan dan bisa diakses
6. User `digifor` memiliki akses ke direktori project

## Instalasi

### 1. Install Service

Jalankan script instalasi dengan hak akses root:

```bash
sudo ./scripts/install-systemd-service.sh
```

**Catatan:** Script `install-systemd-service.sh` sekarang berada di folder `scripts/`.

Script ini akan:
- Menyalin file service ke `/etc/systemd/system/`
- Reload systemd daemon
- Enable service untuk start otomatis saat boot

### 2. Mulai Service

Setelah instalasi, mulai service:

```bash
sudo systemctl start digifor-v2
```

### 3. Verifikasi Status

Cek status service:

```bash
sudo systemctl status digifor-v2
```

### 4. Verifikasi Service Berjalan

Setelah service berjalan, verifikasi dengan mengakses endpoint:

```bash
# Test endpoint root (public, tidak perlu auth)
curl http://172.15.1.207/

# Test health check
curl http://172.15.1.207/health/health

# Test API documentation
curl http://172.15.1.207/docs
```

Jika berhasil, akan mendapatkan response JSON atau halaman HTML.

## Perintah yang Berguna

### Mengelola Service

```bash
# Start service
sudo systemctl start digifor-v2

# Stop service
sudo systemctl stop digifor-v2

# Restart service
sudo systemctl restart digifor-v2

# Reload daemon (WAJIB setelah edit service file)
sudo systemctl daemon-reload

# Cek status
sudo systemctl status digifor-v2

# Enable auto-start on boot
sudo systemctl enable digifor-v2

# Disable auto-start on boot
sudo systemctl disable digifor-v2
```

### Melihat Logs

```bash
# Lihat logs real-time
sudo journalctl -u digifor-v2 -f

# Lihat logs terakhir (50 baris)
sudo journalctl -u digifor-v2 -n 50

# Lihat logs sejak hari ini
sudo journalctl -u digifor-v2 --since today

# Lihat logs dengan filter level
sudo journalctl -u digifor-v2 -p err
```

## Konfigurasi Service

File service (`digifor-v2.service`) berisi konfigurasi berikut:

### Konfigurasi Dasar

- **Port:** 8000
- **Host:** 0.0.0.0 (semua interface network)
- **User:** digifor
- **Group:** digifor
- **Working Directory:** /home/digifor/digifor-v2
- **Auto Restart:** Ya (setelah 10 detik jika crash)
- **Restart Policy:** Always
- **Start on Boot:** Ya (jika di-enable)
- **Log Level:** info
- **Environment File:** `/home/digifor/digifor-v2/.env`

### Startup Sequence

Service akan menjalankan beberapa langkah sebelum aplikasi dimulai (dalam urutan):

1. **Install/Update Dependencies** (`ExecStartPre`)
   - Menjalankan: `pip install --quiet --upgrade -r requirements.txt`
   - Memastikan semua package dependencies terinstall dan terupdate
   - Flag `--quiet` mengurangi output log
   - Flag `--upgrade` memastikan package selalu terupdate

2. **Check Database Connection** (`ExecStartPre`)
   - Menjalankan: `scripts/check-db-connection.py`
   - Memverifikasi koneksi ke database PostgreSQL
   - Service akan gagal start jika database tidak dapat diakses

3. **Initialize Database** (`ExecStartPre`)
   - Menjalankan: `scripts/init-database.py`
   - Membuat semua tabel database jika belum ada
   - Memastikan schema database siap digunakan

4. **Seed Users** (`ExecStartPre`)
   - Menjalankan: `python3 -m app.auth.seed`
   - Menambahkan user default ke database
   - User akan di-update jika sudah ada

5. **Start Application** (`ExecStart`)
   - Menjalankan: `scripts/start-service.sh`
   - Menjalankan aplikasi FastAPI dengan uvicorn

### Konfigurasi Keamanan

- **NoNewPrivileges:** true (mencegah privilege escalation)
- **PrivateTmp:** true (isolasi temporary files)
- **LimitNOFILE:** 65536 (batas file descriptor)

### Scripts yang Digunakan

Service menggunakan beberapa script untuk manajemen database dan service:

#### Scripts Database
- **`scripts/check-db-connection.py`** - Test koneksi database sebelum service start
- **`scripts/init-database.py`** - Initialize database (membuat tabel jika belum ada)
- **`scripts/verify-db-connection.py`** - Verifikasi lengkap koneksi (untuk troubleshooting)
- **`scripts/list-tables.py`** - List semua tabel di database (untuk troubleshooting)

#### Scripts Service
- **`scripts/start-service.sh`** - Script untuk menjalankan aplikasi FastAPI dengan uvicorn
- **`scripts/install-systemd-service.sh`** - Script untuk menginstall systemd service

Semua script berada di folder `scripts/` dan dapat dijalankan manual:

```bash
# Test koneksi database
python3 scripts/check-db-connection.py

# Verifikasi lengkap
python3 scripts/verify-db-connection.py

# List semua tabel
python3 scripts/list-tables.py

# Initialize database manual
python3 scripts/init-database.py
```

### Mengubah Konfigurasi

#### Cara Edit File dengan Nano

Untuk mengedit file konfigurasi, gunakan `nano` atau `sudo nano` tergantung pada lokasi file:

```bash
# Edit file di project (tidak perlu sudo)
nano /home/digifor/digifor-v2/scripts/start-service.sh
nano /home/digifor/digifor-v2/digifor-v2.service
nano /home/digifor/digifor-v2/docs/SYSTEMD_SERVICE.md

# Edit file systemd (perlu sudo)
sudo nano /etc/systemd/system/digifor-v2.service
```

**Tips Nano:**
- Tekan `Ctrl + O` untuk save
- Tekan `Enter` untuk konfirmasi save
- Tekan `Ctrl + X` untuk keluar
- Tekan `Ctrl + K` untuk cut line
- Tekan `Ctrl + U` untuk paste
- Tekan `Ctrl + W` untuk search
- Tekan `Ctrl + \` untuk replace

#### Perintah Setelah Edit Script/Service

Setelah melakukan perubahan pada file service atau script, jalankan perintah berikut sesuai dengan file yang diubah:

**1. Jika mengubah `scripts/start-service.sh`:**
```bash
# Edit start-service.sh
sudo nano /home/digifor/digifor-v2/scripts/start-service.sh

# Hanya perlu restart service (tidak perlu reload daemon)
sudo systemctl restart digifor-v2
```

**2. Jika mengubah `digifor-v2.service` (file template di root):**
```bash
# Edit template file
nano /home/digifor/digifor-v2/digifor-v2.service

# Option 1: Gunakan script install (recommended)
sudo ./scripts/install-systemd-service.sh

# Option 2: Manual copy dan reload
sudo cp /home/digifor/digifor-v2/digifor-v2.service /etc/systemd/system/digifor-v2.service
sudo systemctl daemon-reload
sudo systemctl restart digifor-v2
```

**3. Jika mengubah file di `/etc/systemd/system/digifor-v2.service` langsung:**
```bash
# Edit file systemd (perlu sudo)
sudo nano /etc/systemd/system/digifor-v2.service

# Wajib reload daemon setelah edit file systemd
sudo systemctl daemon-reload
sudo systemctl restart digifor-v2
```

**4. Jika mengubah script Python (check-db-connection.py, init-database.py, dll):**
```bash
# Edit script Python
nano /home/digifor/digifor-v2/scripts/check-db-connection.py
# atau
nano /home/digifor/digifor-v2/scripts/init-database.py

# Hanya perlu restart service
sudo systemctl restart digifor-v2
```

**Ringkasan:**
- Edit script `.sh` → Hanya `restart`
- Edit template `.service` → `copy` + `daemon-reload` + `restart`
- Edit file systemd langsung → `daemon-reload` + `restart`
- Edit script Python → Hanya `restart`

#### Mengubah Port

Jika ingin mengubah port, edit file `scripts/start-service.sh`:

```bash
# Edit start-service.sh
sudo nano /home/digifor/digifor-v2/scripts/start-service.sh
```

Ubah baris uvicorn:
```bash
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --log-level info --no-access-log
```

Ganti `--port 8000` dengan port yang diinginkan, contoh `--port 8080`.

Setelah edit, restart service:
```bash
sudo systemctl restart digifor-v2
```

#### Mengubah Log Level

Edit file `scripts/start-service.sh`:

```bash
sudo nano /home/digifor/digifor-v2/scripts/start-service.sh
```

Ubah `--log-level info` menjadi:
- `debug` - untuk debugging (lebih detail)
- `info` - informasi standar (default)
- `warning` - hanya warning dan error
- `error` - hanya error
- `critical` - hanya critical error

Setelah edit, restart service:
```bash
sudo systemctl restart digifor-v2
```

#### Mengubah Host Binding

Edit file `scripts/start-service.sh`:

```bash
sudo nano /home/digifor/digifor-v2/scripts/start-service.sh
```

Ubah `--host 0.0.0.0` menjadi:
- `0.0.0.0` - semua interface (default, bisa diakses dari luar)
- `127.0.0.1` atau `localhost` - hanya localhost (tidak bisa diakses dari luar)

Setelah edit, restart service:
```bash
sudo systemctl restart digifor-v2
```

#### Menonaktifkan Auto-Install Dependencies

Jika tidak ingin auto-install dependencies setiap start (misalnya untuk production), hapus atau comment baris:

```ini
# ExecStartPre=/home/digifor/digifor-v2/venv/bin/pip install --quiet --upgrade -r /home/digifor/digifor-v2/requirements.txt
```

Atau ganti dengan versi yang lebih cepat (hanya install jika ada perubahan):

```ini
ExecStartPre=/bin/bash -c '/home/digifor/digifor-v2/venv/bin/pip install --quiet --upgrade -r /home/digifor/digifor-v2/requirements.txt || true'
```

Flag `|| true` memastikan service tetap start meskipun pip install gagal.

## Uninstall Service

Untuk menghapus service:

```bash
sudo systemctl stop digifor-v2
sudo systemctl disable digifor-v2
sudo rm /etc/systemd/system/digifor-v2.service
sudo systemctl daemon-reload
```

## Catatan Penting

1. **Database:** Pastikan database PostgreSQL sudah berjalan sebelum service dimulai
2. **Auto Restart:** Service akan otomatis restart jika crash (setelah 10 detik)
3. **Logs:** Logs tersedia melalui `journalctl -u digifor-v2`
4. **Environment:** Pastikan file `.env` sudah dikonfigurasi dengan benar dan ada di `/home/digifor/digifor-v2/.env`
5. **Port:** Port 8000 harus tersedia (tidak digunakan aplikasi lain)
6. **User:** Service berjalan sebagai user `digifor`, pastikan user ini memiliki akses ke direktori project
7. **Network:** Service binding ke `0.0.0.0:8000` berarti bisa diakses dari jaringan lain (jika firewall mengizinkan)
8. **Security:** Service menggunakan security settings seperti `NoNewPrivileges` dan `PrivateTmp`
9. **Dependencies:** Service akan auto-install/update dependencies setiap start (dapat dinonaktifkan)
10. **Database Initialization:** Service akan otomatis membuat tabel dan seed user saat start pertama kali
11. **Daemon Reload:** SELALU jalankan `sudo systemctl daemon-reload` setelah edit file service

## Firewall Configuration

Jika ingin mengakses dari jaringan lain, pastikan port 8000 terbuka di firewall:

```bash
# Untuk UFW (Ubuntu Firewall)
sudo ufw allow 8000/tcp
sudo ufw reload

# Untuk firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## Troubleshooting Detail

### Service Gagal Start

Jika service gagal start, cek urutan troubleshooting:

1. **Cek apakah semua ExecStartPre berhasil:**
   ```bash
   sudo journalctl -u digifor-v2 -n 50
   ```
   Lihat apakah ada error di:
   - pip install
   - check-db-connection
   - init-database
   - seed users

2. **Test manual setiap script:**
   ```bash
   # Test pip install
   cd /home/digifor/digifor-v2
   source venv/bin/activate
   pip install --quiet --upgrade -r requirements.txt
   
   # Test database connection
   python3 scripts/check-db-connection.py
   
   # Test database initialization
   python3 scripts/init-database.py
   
   # Test seed
   python3 -m app.auth.seed
   ```

3. **Cek permission:**
   ```bash
   # Pastikan user digifor memiliki akses
   ls -la /home/digifor/digifor-v2
   ls -la /home/digifor/digifor-v2/scripts/
   ls -la /home/digifor/digifor-v2/venv/bin/
   ```

4. **Cek database connection:**
   ```bash
   # Test koneksi database
   python3 scripts/verify-db-connection.py
   ```

### Service Start Tapi Crash

Jika service start tapi langsung crash:

1. **Cek logs detail:**
   ```bash
   sudo journalctl -u digifor-v2 -n 100 --no-pager
   ```

2. **Cek apakah aplikasi bisa jalan manual:**
   ```bash
   cd /home/digifor/digifor-v2
   source venv/bin/activate
   bash scripts/start-service.sh
   ```

3. **Cek port conflict:**
   ```bash
   sudo netstat -tlnp | grep 8000
   sudo lsof -i :8000
   ```

### Database Connection Issues

Jika ada masalah koneksi database:

1. **Verifikasi koneksi:**
   ```bash
   python3 scripts/verify-db-connection.py
   ```

2. **Cek konfigurasi .env:**
   ```bash
   grep -E "^(POSTGRES_|DATABASE_)" /home/digifor/digifor-v2/.env
   ```

3. **Test koneksi langsung:**
   ```bash
   psql -h localhost -U digifor -d db_forensics -c "SELECT 1;"
   ```

4. **Cek PostgreSQL service:**
   ```bash
   sudo systemctl status postgresql
   ```

Lihat dokumentasi lengkap di [DATABASE_TROUBLESHOOTING.md](DATABASE_TROUBLESHOOTING.md) untuk troubleshooting database lebih detail.

## PostgreSQL Service Management

Service `digifor-v2` memiliki dependency pada PostgreSQL service. Service ini akan menunggu PostgreSQL berjalan sebelum memulai aplikasi.

### Konfigurasi Dependency

File service (`digifor-v2.service`) dikonfigurasi dengan:
- **After:** `network.target postgresql.service` - Service akan start setelah network dan PostgreSQL ready
- **Wants:** `postgresql.service` - Service membutuhkan PostgreSQL (tidak akan gagal jika PostgreSQL tidak ada, tapi akan menunggu)

### Mengelola PostgreSQL Service

#### Cek Status PostgreSQL

```bash
# Cek status PostgreSQL service
sudo systemctl status postgresql

# Cek apakah PostgreSQL berjalan
sudo systemctl is-active postgresql

# Cek apakah PostgreSQL enabled (auto-start on boot)
sudo systemctl is-enabled postgresql
```

#### Start/Stop PostgreSQL

```bash
# Start PostgreSQL service
sudo systemctl start postgresql

# Stop PostgreSQL service
sudo systemctl stop postgresql

# Restart PostgreSQL service
sudo systemctl restart postgresql

# Reload PostgreSQL configuration (tanpa restart)
sudo systemctl reload postgresql
```

#### Enable/Disable Auto-Start

```bash
# Enable PostgreSQL untuk start otomatis saat boot
sudo systemctl enable postgresql

# Disable auto-start
sudo systemctl disable postgresql
```

#### Melihat Logs PostgreSQL

```bash
# Lihat logs real-time
sudo journalctl -u postgresql -f

# Lihat logs terakhir (50 baris)
sudo journalctl -u postgresql -n 50

# Lihat logs sejak hari ini
sudo journalctl -u postgresql --since today

# Lihat logs dengan filter level
sudo journalctl -u postgresql -p err
```

#### Verifikasi Koneksi PostgreSQL

```bash
# Test koneksi dengan psql
psql -h localhost -U digifordb -d db_forensics -c "SELECT version();"

# Test koneksi dengan Python script
python3 scripts/check-db-connection.py

# Verifikasi lengkap
python3 scripts/verify-db-connection.py
```

### Troubleshooting PostgreSQL Service

#### PostgreSQL Tidak Berjalan

Jika PostgreSQL service tidak berjalan:

1. **Cek status:**
   ```bash
   sudo systemctl status postgresql
   ```

2. **Cek error logs:**
   ```bash
   sudo journalctl -u postgresql -n 100 --no-pager
   ```

3. **Start PostgreSQL:**
   ```bash
   sudo systemctl start postgresql
   ```

4. **Jika masih gagal, cek konfigurasi:**
   ```bash
   # Cek file konfigurasi PostgreSQL
   sudo cat /etc/postgresql/*/main/postgresql.conf | grep -E "^(port|listen_addresses)"
   
   # Cek file pg_hba.conf untuk authentication
   sudo cat /etc/postgresql/*/main/pg_hba.conf
   ```

#### PostgreSQL Berjalan Tapi Aplikasi Tidak Bisa Connect

1. **Verifikasi koneksi:**
   ```bash
   python3 scripts/verify-db-connection.py
   ```

2. **Cek credentials di .env:**
   ```bash
   grep -E "^(POSTGRES_|DATABASE_)" /home/digifor/digifor-v2/.env
   ```

3. **Test koneksi langsung:**
   ```bash
   psql -h 172.15.1.207 -U digifordb -d db_forensics -c "SELECT 1;"
   ```

4. **Cek firewall:**
   ```bash
   # Jika PostgreSQL di server berbeda, pastikan port 5432 terbuka
   sudo ufw status | grep 5432
   ```

#### PostgreSQL Crash atau Restart Berulang

1. **Cek logs detail:**
   ```bash
   sudo journalctl -u postgresql -n 200 --no-pager
   ```

2. **Cek disk space:**
   ```bash
   df -h
   ```

3. **Cek memory:**
   ```bash
   free -h
   ```

4. **Cek PostgreSQL data directory:**
   ```bash
   sudo du -sh /var/lib/postgresql/*/main
   ```

## Database Tables Management

Aplikasi menggunakan PostgreSQL sebagai database dan SQLAlchemy sebagai ORM. Semua tabel database dibuat secara otomatis saat pertama kali aplikasi dijalankan atau saat service start.

### Daftar Tabel Database

Aplikasi menggunakan tabel-tabel berikut:

#### Authentication & Authorization
- **`users`** - Tabel untuk menyimpan data user (email, password, role, dll)
- **`refresh_tokens`** - Tabel untuk menyimpan refresh token untuk authentication
- **`blacklisted_tokens`** - Tabel untuk menyimpan token yang sudah di-blacklist

#### Case Management
- **`agencies`** - Tabel untuk menyimpan data agency/instansi
- **`work_units`** - Tabel untuk menyimpan data work unit/satuan kerja
- **`cases`** - Tabel untuk menyimpan data kasus
- **`case_logs`** - Tabel untuk menyimpan log aktivitas kasus

#### Evidence Management
- **`evidence_types`** - Tabel untuk menyimpan tipe-tipe evidence
- **`evidence`** - Tabel untuk menyimpan data evidence
- **`custody_logs`** - Tabel untuk menyimpan log custody evidence
- **`custody_reports`** - Tabel untuk menyimpan laporan custody

#### Suspect Management
- **`suspects`** - Tabel untuk menyimpan data suspect/tersangka

#### Analytics & Device Management
- **`analytics_history`** - Tabel untuk menyimpan history analytics
- **`analytic_device`** - Tabel untuk relasi analytics dengan devices
- **`apk_analytics`** - Tabel untuk menyimpan hasil analisis APK
- **`devices`** - Tabel untuk menyimpan data device
- **`files`** - Tabel untuk menyimpan data file dari device
- **`hash_files`** - Tabel untuk menyimpan hash file
- **`contacts`** - Tabel untuk menyimpan data kontak dari device
- **`calls`** - Tabel untuk menyimpan data panggilan dari device
- **`social_media`** - Tabel untuk menyimpan data social media dari device
- **`chat_messages`** - Tabel untuk menyimpan data chat messages dari device

### Melihat Daftar Tabel

Untuk melihat semua tabel yang ada di database:

```bash
# Menggunakan script Python
python3 scripts/list-tables.py

# Menggunakan psql langsung
psql -h localhost -U digifordb -d db_forensics -c "\dt"

# Atau dengan detail lebih lengkap
psql -h localhost -U digifordb -d db_forensics -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
```

### Update Database Tables

#### Menggunakan Alembic (Recommended)

Aplikasi menggunakan Alembic untuk database migration. Untuk update schema database:

1. **Buat migration baru setelah mengubah model:**
   ```bash
   # Masuk ke virtual environment
   source venv/bin/activate
   
   # Buat migration baru
   alembic revision --autogenerate -m "deskripsi_perubahan"
   
   # Review file migration di alembic/versions/
   # Pastikan perubahan sesuai dengan yang diinginkan
   ```

2. **Apply migration:**
   ```bash
   # Apply semua pending migrations
   alembic upgrade head
   
   # Atau apply satu migration
   alembic upgrade +1
   ```

3. **Rollback migration (jika perlu):**
   ```bash
   # Rollback satu migration
   alembic downgrade -1
   
   # Rollback ke migration tertentu
   alembic downgrade <revision_id>
   ```

4. **Cek status migration:**
   ```bash
   # Cek migration yang sudah di-apply
   alembic current
   
   # Lihat history migrations
   alembic history
   ```

#### Menggunakan SQLAlchemy create_all (Development Only)

**Peringatan:** Metode ini hanya untuk development. Untuk production, gunakan Alembic.

1. **Update tabel otomatis:**
   ```bash
   # Script akan membuat semua tabel yang belum ada
   python3 scripts/init-database.py
   ```

2. **Atau menggunakan tool:**
   ```bash
   python3 tools/migrate_database.py
   ```

**Catatan:** `Base.metadata.create_all()` hanya akan membuat tabel baru, tidak akan mengubah struktur tabel yang sudah ada. Untuk mengubah struktur tabel yang sudah ada, gunakan Alembic.

### Backup Database

#### Backup Manual

```bash
# Backup database ke file SQL
pg_dump -h localhost -U digifordb -d db_forensics > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup dengan format custom (lebih cepat untuk restore)
pg_dump -h localhost -U digifordb -d db_forensics -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# Backup hanya schema (tanpa data)
pg_dump -h localhost -U digifordb -d db_forensics --schema-only > schema_backup.sql
```

#### Restore Database

```bash
# Restore dari file SQL
psql -h localhost -U digifordb -d db_forensics < backup_20250101_120000.sql

# Restore dari format custom
pg_restore -h localhost -U digifordb -d db_forensics backup_20250101_120000.dump

# Restore hanya schema
psql -h localhost -U digifordb -d db_forensics < schema_backup.sql
```

### Maintenance Database

#### Vacuum Database

```bash
# Vacuum database untuk optimize storage
psql -h localhost -U digifordb -d db_forensics -c "VACUUM ANALYZE;"

# Vacuum full (lebih agresif, butuh lock table)
psql -h localhost -U digifordb -d db_forensics -c "VACUUM FULL;"
```

#### Reindex Database

```bash
# Reindex semua index
psql -h localhost -U digifordb -d db_forensics -c "REINDEX DATABASE db_forensics;"
```

#### Cek Database Size

```bash
# Cek ukuran database
psql -h localhost -U digifordb -d db_forensics -c "SELECT pg_size_pretty(pg_database_size('db_forensics'));"

# Cek ukuran setiap tabel
psql -h localhost -U digifordb -d db_forensics -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Troubleshooting Database Tables

#### Tabel Tidak Terbuat

Jika tabel tidak terbuat setelah service start:

1. **Cek logs:**
   ```bash
   sudo journalctl -u digifor-v2 -n 100 | grep -i "database\|table\|init"
   ```

2. **Jalankan init database manual:**
   ```bash
   python3 scripts/init-database.py
   ```

3. **Cek permission database user:**
   ```bash
   psql -h localhost -U digifordb -d db_forensics -c "\du digifordb"
   ```

#### Error Migration

Jika ada error saat migration:

1. **Cek migration status:**
   ```bash
   alembic current
   alembic history
   ```

2. **Cek error detail:**
   ```bash
   alembic upgrade head --sql  # Preview SQL tanpa execute
   ```

3. **Rollback dan coba lagi:**
   ```bash
   alembic downgrade -1
   # Fix migration file
   alembic upgrade head
   ```

---

## Struktur File Service

File-file terkait systemd service:

- **`digifor-v2.service`** (di root project) - Template file service untuk version control
- **`scripts/start-service.sh`** - Script untuk menjalankan aplikasi
- **`scripts/install-systemd-service.sh`** - Script untuk install/update systemd service
- **`/etc/systemd/system/digifor-v2.service`** - File aktif yang digunakan systemd

**Catatan Penting:**
- File `digifor-v2.service` di root project adalah **template** yang disimpan di Git
- File di `/etc/systemd/system/` adalah **file aktif** yang digunakan systemd
- Setelah edit template, jalankan `sudo ./scripts/install-systemd-service.sh` untuk update file aktif
- Atau manual: `sudo cp digifor-v2.service /etc/systemd/system/` lalu `sudo systemctl daemon-reload`

---

**Terakhir diupdate:** 2025-01-15

