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

# Reload daemon (setelah edit service file)
sudo systemctl daemon-reload

# Restart service setelah edit config
sudo systemctl restart digifor-v2

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

### Konfigurasi Keamanan

- **NoNewPrivileges:** true (mencegah privilege escalation)
- **PrivateTmp:** true (isolasi temporary files)
- **LimitNOFILE:** 65536 (batas file descriptor)

### Mengubah Konfigurasi

#### Mengubah Port

Jika ingin mengubah port, edit file `/etc/systemd/system/digifor-v2.service`:

```bash
sudo nano /etc/systemd/system/digifor-v2.service
```

Ubah baris `ExecStart`:
```ini
ExecStart=/home/digifor/digifor-v2/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
```

Ganti `--port 8000` dengan port yang diinginkan, contoh `--port 8080`.

Setelah edit, reload dan restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart digifor-v2
```

#### Mengubah Log Level

Ubah `--log-level info` di baris `ExecStart` menjadi:
- `debug` - untuk debugging (lebih detail)
- `info` - informasi standar (default)
- `warning` - hanya warning dan error
- `error` - hanya error
- `critical` - hanya critical error

#### Mengubah Host Binding

Untuk mengubah host binding, ubah `--host 0.0.0.0` menjadi:
- `0.0.0.0` - semua interface (default, bisa diakses dari luar)
- `127.0.0.1` atau `localhost` - hanya localhost (tidak bisa diakses dari luar)

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
```

