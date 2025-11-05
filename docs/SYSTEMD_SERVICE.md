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
curl http://localhost:8000/

# Test health check
curl http://localhost:8000/health/health

# Test API documentation
curl http://localhost:8000/docs
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

#### Perintah Setelah Edit Script/Service

Setelah melakukan perubahan pada file service atau script, jalankan perintah berikut sesuai dengan file yang diubah:

**1. Jika mengubah `scripts/start-service.sh`:**
```bash
# Hanya perlu restart service (tidak perlu reload daemon)
sudo systemctl restart digifor-v2
```

**2. Jika mengubah `digifor-v2.service` (file template di root):**
```bash
# Option 1: Gunakan script install (recommended)
sudo ./scripts/install-systemd-service.sh

# Option 2: Manual copy dan reload
sudo cp /home/digifor/digifor-v2/digifor-v2.service /etc/systemd/system/digifor-v2.service
sudo systemctl daemon-reload
sudo systemctl restart digifor-v2
```

**3. Jika mengubah file di `/etc/systemd/system/digifor-v2.service` langsung:**
```bash
# Wajib reload daemon setelah edit file systemd
sudo systemctl daemon-reload
sudo systemctl restart digifor-v2
```

**4. Jika mengubah script Python (check-db-connection.py, init-database.py, dll):**
```bash
# Hanya perlu restart service
sudo systemctl restart digifor-v2
```

**Ringkasan:**
- Edit script `.sh` → Hanya `restart`
- Edit template `.service` → `copy` + `daemon-reload` + `restart`
- Edit file systemd langsung → `daemon-reload` + `restart`
- Edit script Python → Hanya `restart`

#### Mengubah Port

Jika ingin mengubah port, edit file `/etc/systemd/system/digifor-v2.service` dan ubah file `scripts/start-service.sh`:

```bash
# Edit start-service.sh
nano /home/digifor/digifor-v2/scripts/start-service.sh
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

Edit file `scripts/start-service.sh` dan ubah `--log-level info` menjadi:
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

Edit file `scripts/start-service.sh` dan ubah `--host 0.0.0.0` menjadi:
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

**Terakhir diupdate:** 2025-11-05

