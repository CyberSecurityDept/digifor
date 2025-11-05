# Troubleshooting: Endpoint Tidak Bisa Insert Data ke Database

Panduan untuk mengatasi masalah endpoint yang tidak bisa insert data ke database.

## 🔍 Gejala Masalah

- Endpoint mengembalikan response 200/201 (success)
- Tidak ada error di log
- Tapi data tidak tersimpan di database
- Query SELECT tidak menemukan data yang baru di-insert

## 🔎 Penyebab Umum

### 1. **Transaction Tidak Di-Commit**

**Masalah:** `db.commit()` tidak dipanggil atau exception terjadi sebelum commit.

**Solusi:** Pastikan semua service layer memanggil `db.commit()` setelah `db.add()`:

```python
try:
    db.add(new_object)
    db.commit()
    db.refresh(new_object)
except Exception as e:
    db.rollback()
    raise
```

### 2. **Exception Handler Global Mengintervensi**

**Masalah:** Exception handler global menangkap exception sebelum commit terjadi.

**Solusi:** Pastikan exception handler tidak mengganggu transaction. Service layer harus handle exception sendiri.

### 3. **Database Session Tidak Di-Rollback Saat Exception**

**Masalah:** Jika ada exception, transaction tidak di-rollback, menyebabkan session dalam state tidak valid.

**Solusi:** Sudah diperbaiki di `app/db/session.py` - sekarang otomatis rollback jika ada exception.

### 4. **Constraint Violation (NOT NULL, UNIQUE, dll)**

**Masalah:** Data yang di-insert melanggar constraint database (field required tidak diisi, duplicate key, dll).

**Solusi:** 
- Cek model untuk field yang `nullable=False`
- Pastikan semua required field diisi
- Cek log untuk error constraint violation

### 5. **Database Connection Issue**

**Masalah:** Koneksi database terputus atau timeout.

**Solusi:** 
- Cek koneksi database dengan `scripts/check-db-connection.py`
- Pastikan database server accessible
- Cek connection pool settings

## ✅ Solusi Step-by-Step

### 1. Verifikasi Database Connection

```bash
python3 scripts/check-db-connection.py
python3 scripts/verify-db-connection.py
```

### 2. Test Insert Manual

```bash
python3 scripts/test-db-insert.py
```

Script ini akan:
- Test koneksi database
- Test permissions
- Test insert dengan commit
- Verify data tersimpan
- Cleanup test data

### 3. Cek Log untuk Error

```bash
# Cek log service
sudo journalctl -u digifor-v2 -n 100 | grep -iE "(error|exception|rollback|commit)"

# Atau cek log aplikasi
tail -f logs/Digital\ Forensics.log | grep -iE "(error|exception)"
```

### 4. Cek Model Constraints

Pastikan semua field required diisi. Contoh untuk `Case`:
- `case_number` - required (NOT NULL)
- `title` - required (NOT NULL)
- `main_investigator` - required (NOT NULL)
- `status` - required (NOT NULL)

### 5. Test Endpoint dengan Debug

Tambahkan logging di service layer:

```python
try:
    db.add(new_object)
    print(f"DEBUG: Added object, ID: {new_object.id}")
    db.commit()
    print(f"DEBUG: Committed, ID: {new_object.id}")
    db.refresh(new_object)
    print(f"DEBUG: Refreshed, ID: {new_object.id}")
except Exception as e:
    print(f"DEBUG: Error: {e}")
    db.rollback()
    raise
```

### 6. Verifikasi Data di Database

```bash
# Test query langsung
psql -h 172.15.2.105 -U digifor -d db_forensics -c "SELECT COUNT(*) FROM cases;"

# Atau dengan script
python3 scripts/list-tables.py
```

## 🔧 Perbaikan yang Sudah Dilakukan

### 1. Auto-Rollback di get_db()

File `app/db/session.py` sudah diperbaiki untuk otomatis rollback jika ada exception:

```python
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

### 2. Exception Handling di Service Layer

Service layer sudah menggunakan try-except dengan rollback:

```python
try:
    db.add(object)
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

## 📋 Checklist Troubleshooting

- [ ] Database connection berhasil (`check-db-connection.py`)
- [ ] Permissions user cukup (`verify-db-connection.py`)
- [ ] Test insert manual berhasil (`test-db-insert.py`)
- [ ] Tidak ada error di log service
- [ ] Tidak ada constraint violation
- [ ] Semua required field diisi
- [ ] `db.commit()` dipanggil setelah `db.add()`
- [ ] Exception handling dengan rollback sudah benar
- [ ] Data benar-benar tidak ada (bukan masalah query)

## 🧪 Test Script

Gunakan script `scripts/test-db-insert.py` untuk test insert:

```bash
cd /home/digifor/digifor-v2
source venv/bin/activate
python3 scripts/test-db-insert.py
```

Script ini akan:
1. Test koneksi database
2. Test permissions
3. Test insert dengan commit
4. Verify data tersimpan
5. Cleanup test data

## 💡 Tips

1. **Selalu cek log setelah insert gagal:**
   ```bash
   sudo journalctl -u digifor-v2 -f
   ```

2. **Gunakan transaction secara eksplisit:**
   ```python
   with db.begin():
       db.add(object)
       # commit otomatis jika tidak ada exception
   ```

3. **Cek apakah data benar-benar tidak ada:**
   ```sql
   SELECT * FROM cases ORDER BY id DESC LIMIT 10;
   ```

4. **Test dengan minimal data:**
   - Pastikan semua required field diisi
   - Test dengan data sederhana dulu
   - Tambahkan field optional setelah berhasil

## 🆘 Masih Bermasalah?

Jika setelah semua langkah di atas masih tidak bisa insert:

1. **Cek apakah masalah di semua endpoint atau hanya beberapa:**
   - Test dengan endpoint yang berbeda
   - Cek apakah ada pattern tertentu

2. **Cek database transaction isolation:**
   ```sql
   SHOW transaction_isolation;
   ```

3. **Cek apakah ada trigger atau constraint di database:**
   ```sql
   \d+ cases
   ```

4. **Test dengan psql langsung:**
   ```sql
   INSERT INTO cases (case_number, title, status, main_investigator) 
   VALUES ('TEST-001', 'Test', 'Open', 'Test Investigator');
   ```

---

**Terakhir diupdate:** 2025-11-04

