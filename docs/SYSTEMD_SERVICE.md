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
sudo ./install-systemd-service.sh
```

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

# Restart service setelah edit config
sudo systemctl restart digifor-v2

# Cek status
sudo systemctl status digifor-v2

# Enable auto-start on boot
sudo systemctl enable digifor-v2

# Disable auto-start on boot
sudo systemctl disable digifor-v2

# Edit service file (manual)
sudo nano /etc/systemd/system/digifor-v2.service
# Setelah edit, reload daemon dan restart service
sudo systemctl daemon-reload
sudo systemctl restart digifor-v2
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

### Troubleshooting

Jika service tidak berjalan:

1. **Cek status service:**
   ```bash
   sudo systemctl status digifor-v2
   ```

2. **Cek logs untuk error:**
   ```bash
   sudo journalctl -u digifor-v2 -n 100
   ```

3. **Pastikan virtual environment ada:**
   ```bash
   ls -la /home/digifor/digifor-v2/venv/bin/uvicorn
   ```

4. **Pastikan file .env ada:**
   ```bash
   ls -la /home/digifor/digifor-v2/.env
   ```

5. **Test manual menjalankan aplikasi:**
   ```bash
   cd /home/digifor/digifor-v2
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

6. **Cek apakah port sudah digunakan:**
   ```bash
   sudo netstat -tlnp | grep 8000
   # atau
   sudo ss -tlnp | grep 8000
   ```

7. **Cek apakah database PostgreSQL berjalan:**
   ```bash
   sudo systemctl status postgresql
   # atau
   sudo service postgresql status
   ```

8. **Cek permission file dan direktori:**
   ```bash
   ls -la /home/digifor/digifor-v2
   # Pastikan user digifor memiliki akses read dan execute
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
   - Menjalankan: `start-service.sh`
   - Menjalankan aplikasi FastAPI dengan uvicorn

### Konfigurasi Keamanan

- **NoNewPrivileges:** true (mencegah privilege escalation)
- **PrivateTmp:** true (isolasi temporary files)
- **LimitNOFILE:** 65536 (batas file descriptor)

### Scripts Database yang Digunakan

Service menggunakan beberapa script Python untuk manajemen database:

- **`scripts/check-db-connection.py`** - Test koneksi database sebelum service start
- **`scripts/init-database.py`** - Initialize database (membuat tabel jika belum ada)
- **`scripts/verify-db-connection.py`** - Verifikasi lengkap koneksi (untuk troubleshooting)
- **`scripts/list-tables.py`** - List semua tabel di database (untuk troubleshooting)

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

#### Edit File Service

Untuk mengubah konfigurasi service, edit file service:

```bash
sudo nano /etc/systemd/system/digifor-v2.service
```

Atau jika ingin edit file di project directory:

```bash
nano /home/digifor/digifor-v2/digifor-v2.service
# Kemudian copy ke systemd
sudo cp digifor-v2.service /etc/systemd/system/digifor-v2.service
```

**Setelah edit, WAJIB reload daemon dan restart service:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart digifor-v2
```

#### Mengubah Port

Jika ingin mengubah port, edit file `/etc/systemd/system/digifor-v2.service` dan ubah file `start-service.sh`:

```bash
# Edit start-service.sh
nano /home/digifor/digifor-v2/start-service.sh
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

Edit file `start-service.sh` dan ubah `--log-level info` menjadi:
- `debug` - untuk debugging (lebih detail)
- `info` - informasi standar (default)
- `warning` - hanya warning dan error
- `error` - hanya error
- `critical` - hanya critical error

#### Mengubah Host Binding

Edit file `start-service.sh` dan ubah `--host 0.0.0.0` menjadi:
- `0.0.0.0` - semua interface (default, bisa diakses dari luar)
- `127.0.0.1` atau `localhost` - hanya localhost (tidak bisa diakses dari luar)

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

## Endpoint yang Tersedia

### Endpoint Public (Tidak Perlu Authentication)

- `GET /` - Info API dan version
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI schema
- `GET /health/health` - Health check
- `GET /health/health/ready` - Readiness check
- `GET /health/health/live` - Liveness check
- `POST /api/v1/auth/login` - Login endpoint
- `POST /api/v1/auth/register` - Register endpoint
- `POST /api/v1/auth/refresh` - Refresh token endpoint

### Endpoint yang Memerlukan Authentication

Semua endpoint lainnya memerlukan Bearer token di header Authorization:
```
Authorization: Bearer <your-jwt-token>
```

### Contoh Penggunaan

```bash
# Test endpoint root (public)
curl http://localhost:8000/

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Test endpoint dengan authentication
curl http://localhost:8000/api/v1/analytics/files \
  -H "Authorization: Bearer <your-token>"
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

## Monitoring Service

### Cek Resource Usage

```bash
# Cek memory dan CPU usage
systemctl status digifor-v2

# Cek process details
ps aux | grep uvicorn

# Cek network connections
sudo netstat -tlnp | grep 8000
```

### Cek Logs Real-time

```bash
# Follow logs
sudo journalctl -u digifor-v2 -f

# Filter logs by level
sudo journalctl -u digifor-v2 -p err -f  # Error only
sudo journalctl -u digifor-v2 -p warning -f  # Warning and above

# Cek logs startup sequence
sudo journalctl -u digifor-v2 --since "5 minutes ago" | grep -E "(pip install|check-db|init-database|seed|Started)"
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
   bash start-service.sh
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

**Terakhir diupdate:** 2025-11-04

