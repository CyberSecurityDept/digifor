# 🐳 Docker Guide - Digital Forensics Platform

Panduan lengkap untuk menggunakan Docker dengan Digital Forensics Platform.

## 📋 Daftar Isi

1. [Prerequisites](#prerequisites)
2. [Setup Awal (First Time)](#setup-awal-first-time)
3. [Menjalankan Services](#menjalankan-services)
4. [Mengelola Container](#mengelola-container)
5. [Database Management](#database-management)
6. [Update Code & Database](#update-code--database)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Prerequisites

### Software yang Diperlukan

- **Docker Desktop** (untuk macOS/Windows) atau **Docker Engine** (untuk Linux)
- **Docker Compose** (biasanya sudah termasuk dengan Docker Desktop)
- Port **8000** dan **5432** harus tersedia

### Verifikasi Instalasi

```bash
# Cek versi Docker
docker --version

# Cek versi Docker Compose
docker-compose --version

# Test Docker
docker ps
```

---

## Setup Awal (First Time)

### Langkah 1: Buat Docker Network

```bash
docker network create digifor-network
```

**Catatan:** Network ini diperlukan agar semua container bisa berkomunikasi.

### Langkah 2: Buat dan Jalankan PostgreSQL Container

```bash
docker run --name digiforapp \
  --network digifor-network \
  -e POSTGRES_USER=digifordb \
  -e POSTGRES_PASSWORD=Grz6ayTrBXPnFkwL \
  -e POSTGRES_DB=digifor \
  -p 5432:5432 \
  -d \
  --restart always \
  postgres:16
```

**Penjelasan:**
- `--name digiforapp`: Nama container
- `--network digifor-network`: Menghubungkan ke network yang sudah dibuat
- `-e`: Environment variables untuk PostgreSQL
- `-p 5432:5432`: Port mapping (host:container)
- `-d`: Run in detached mode (background)
- `--restart always`: Auto-restart jika container stop atau setelah reboot

### Langkah 3: Buat File .env

```bash
# Copy dari template
cp env.example .env
```

**Pastikan file `.env` memiliki konfigurasi:**
```env
POSTGRES_HOST=digiforapp
POSTGRES_PORT=5432
POSTGRES_USER=digifordb
POSTGRES_PASSWORD=Grz6ayTrBXPnFkwL
POSTGRES_DB=digifor
```

### Langkah 4: Build dan Start Services

```bash
docker-compose up --build -d
```

**Apa yang terjadi:**
- Build Docker images dari Dockerfile
- Menjalankan database migrations (via Alembic)
- Start application service
- Start seed service (untuk initial data)

---

## Menjalankan Services

### Start Services

```bash
# Start semua services
docker-compose up -d

# Start dengan rebuild (jika ada perubahan code)
docker-compose up --build -d
```

### Stop Services

```bash
# Stop semua services (container tetap ada)
docker-compose stop

# Stop dan remove containers
docker-compose down

# Stop dan remove containers + volumes (hapus semua data)
docker-compose down -v
```

### Restart Services

```bash
# Restart semua services
docker-compose restart

# Restart service tertentu
docker-compose restart app
```

### Cek Status

```bash
# Cek status semua services
docker-compose ps

# Cek semua container (termasuk PostgreSQL)
docker ps

# Cek logs real-time
docker-compose logs -f app

# Cek logs semua services
docker-compose logs -f
```

---

## Mengelola Container

### Melihat Logs

```bash
# Logs aplikasi (real-time)
docker-compose logs -f app

# Logs seed service
docker-compose logs -f seed

# Logs semua services
docker-compose logs -f

# Logs dengan limit baris
docker-compose logs --tail=100 app

# Logs sejak waktu tertentu
docker-compose logs --since 10m app
```

### Masuk ke Container

```bash
# Masuk ke container app
docker-compose exec app bash

# Atau dengan container name
docker exec -it digifor-app-1 bash

# Masuk ke PostgreSQL container
docker exec -it digiforapp bash
```

### Menjalankan Perintah di Container

```bash
# Jalankan perintah Python di container
docker-compose exec app python -m app.auth.seed

# Jalankan migration
docker-compose exec app alembic upgrade head

# Jalankan test
docker-compose exec app pytest
```

---

## Database Management

### Mengakses Database via psql

```bash
# Masuk ke PostgreSQL
docker exec -it digiforapp psql -U digifordb -d digifor
```

**Perintah SQL yang Berguna:**

```sql
-- Lihat semua tabel
\dt

-- Lihat struktur tabel
\d nama_tabel

-- Lihat data dari tabel
SELECT * FROM users LIMIT 10;

-- Hitung jumlah data
SELECT COUNT(*) FROM users;

-- Lihat ukuran database
SELECT pg_size_pretty(pg_database_size('digifor'));

-- Keluar dari psql
\q
```

### Query dari Terminal (tanpa masuk psql)

```bash
# Lihat semua tabel
docker exec -it digiforapp psql -U digifordb -d digifor -c "\dt"

# Query data
docker exec -it digiforapp psql -U digifordb -d digifor -c "SELECT COUNT(*) FROM users;"
```

### Backup Database

```bash
# Backup database
docker exec digiforapp pg_dump -U digifordb digifor > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
docker exec -i digiforapp psql -U digifordb digifor < backup_file.sql
```

---

## Update Code & Database

### Scenario 1: Perubahan Code Saja

```bash
# Rebuild dan restart
docker-compose up --build -d

# Atau rebuild hanya app container (lebih cepat)
docker-compose build app
docker-compose up -d app
```

### Scenario 2: Perubahan Database Schema

```bash
# 1. Get container name
docker-compose ps

# 2. Buat migration baru
docker exec -it digifor-app-1 alembic revision --autogenerate -m "nama_perubahan"

# 3. Apply migration
docker exec -it digifor-app-1 alembic upgrade head

# 4. Rebuild container
docker-compose up --build -d
```

### Scenario 3: Perubahan Code + Database

```bash
# 1. Buat migration
docker exec -it digifor-app-1 alembic revision --autogenerate -m "deskripsi_perubahan"

# 2. Apply migration
docker exec -it digifor-app-1 alembic upgrade head

# 3. Rebuild dan restart
docker-compose up --build -d

# 4. Verifikasi
docker-compose logs -f app
```

### Migration Commands

```bash
# Cek status migration
docker exec -it digifor-app-1 alembic current

# Lihat history migration
docker exec -it digifor-app-1 alembic history

# Rollback migration
docker exec -it digifor-app-1 alembic downgrade -1

# Rollback ke migration tertentu
docker exec -it digifor-app-1 alembic downgrade <revision_id>
```

---

## Troubleshooting

### Container Tidak Start

```bash
# Cek logs untuk error
docker-compose logs app

# Cek status container
docker-compose ps

# Restart container
docker-compose restart app
```

### Database Connection Error

```bash
# Cek apakah PostgreSQL container running
docker ps | grep digiforapp

# Cek logs PostgreSQL
docker logs digiforapp

# Test koneksi dari container app
docker-compose exec app python -c "from app.db.session import engine; print('OK' if engine.connect() else 'FAIL')"
```

### Port Already in Use

```bash
# Cek port yang digunakan
lsof -i :8000
lsof -i :5432

# Stop service yang menggunakan port
# Atau ubah port di docker-compose.yml
```

### Container Name Already Exists

```bash
# Hapus container yang sudah ada
docker rm -f digiforapp

# Atau hapus semua container
docker-compose down
```

### Network Already Exists

```bash
# Hapus network (hati-hati, pastikan tidak ada container yang menggunakan)
docker network rm digifor-network

# Atau skip jika sudah ada (tidak akan error)
docker network create digifor-network
```

### Rebuild dari Scratch

```bash
# Stop dan hapus semua
docker-compose down -v

# Hapus images (opsional)
docker rmi digifor-app digifor-seed

# Rebuild tanpa cache
docker-compose build --no-cache

# Start lagi
docker-compose up -d
```

### Docker Desktop Tidak Auto-Start

**macOS/Windows:**
1. Buka Docker Desktop
2. Settings → General
3. Centang "Start Docker Desktop when you log in"
4. Apply & Restart

**Linux:**
```bash
# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker
```

---

## Best Practices

### 1. Selalu Gunakan `-d` untuk Detached Mode

```bash
# ✅ Benar
docker-compose up -d

# ❌ Salah (akan block terminal)
docker-compose up
```

### 2. Gunakan `--build` Hanya Saat Perlu

```bash
# Jika hanya restart, tidak perlu build
docker-compose restart

# Jika ada perubahan code, baru build
docker-compose up --build -d
```

### 3. Backup Database Secara Berkala

```bash
# Buat script backup otomatis
#!/bin/bash
docker exec digiforapp pg_dump -U digifordb digifor > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. Monitor Resource Usage

```bash
# Cek penggunaan resource
docker stats

# Cek disk usage
docker system df
```

### 5. Clean Up Secara Berkala

```bash
# Hapus unused images
docker image prune -a

# Hapus unused volumes
docker volume prune

# Hapus semua unused resources
docker system prune -a
```

### 6. Gunakan .env untuk Konfigurasi

Jangan hardcode credentials di docker-compose.yml. Gunakan file `.env`:

```yaml
# docker-compose.yml
services:
  app:
    env_file: .env
```

### 7. Selalu Cek Logs Setelah Update

```bash
# Setelah update, selalu cek logs
docker-compose logs -f app
```

---

## Quick Reference

### Perintah Paling Sering Digunakan

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Cek status
docker-compose ps

# Lihat logs
docker-compose logs -f app

# Rebuild setelah perubahan code
docker-compose up --build -d

# Masuk ke database
docker exec -it digiforapp psql -U digifordb -d digifor

# Jalankan migration
docker exec -it digifor-app-1 alembic upgrade head
```

---

## Akses Aplikasi

Setelah services running:

- **API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

## Catatan Penting

1. **Docker Desktop harus tetap berjalan** - Jangan tutup aplikasi Docker Desktop, minimize saja
2. **Auto-restart** - Semua services menggunakan `restart: always`, jadi akan otomatis start setelah reboot
3. **Network harus dibuat** - Pastikan `digifor-network` sudah dibuat sebelum start services
4. **Port harus tersedia** - Pastikan port 8000 dan 5432 tidak digunakan aplikasi lain

---

## Support

Jika mengalami masalah:

1. Cek logs: `docker-compose logs app`
2. Cek status: `docker-compose ps`
3. Cek dokumentasi: `README.md`
4. Cek troubleshooting section di atas

---

**🎯 Happy Dockerizing!**

