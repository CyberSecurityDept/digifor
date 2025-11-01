#!/usr/bin/env python3
"""
Script untuk membersihkan data invalid di tabel social_media
Menghapus data yang terdeteksi sebagai header, metadata, atau data tidak valid
"""

import sys
import os
import re
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
from sqlalchemy import text
from app.analytics.device_management.models import SocialMedia

def is_header_or_metadata(value: str) -> bool:
    """Cek apakah value adalah header kolom atau metadata sistem"""
    if not value:
        return False
    
    value_str = str(value).strip()
    value_lower = value_str.lower()
    
    # Header kolom yang umum ditemukan di Excel (exact match)
    exact_header_keywords = [
        "source", "file name", "file size", "source file", "source table",
        "source file size", "source table", "path", "/", 
        "user picture url", "thumbnail url", "tweet url", "remote party name"
    ]
    
    if value_lower in exact_header_keywords:
        return True
    
    # Cek apakah value adalah ukuran file (berisi angka + KB/MB/GB)
    if re.search(r'^\d+[,\s\.]?\d*\s*(kb|mb|gb)$', value_lower):
        return True
    
    # Cek apakah value terlalu pendek (kecuali untuk username yang sangat pendek yang valid)
    if len(value_str) <= 1:
        # Single character bisa valid untuk beberapa platform, tapi "/" jelas tidak valid
        if value_str == "/":
            return True
        # Skip single character yang bukan alphanumeric
        if not value_str.isalnum():
            return True
    
    # Cek apakah value adalah hanya simbol tanpa karakter valid
    if not re.search(r'[a-zA-Z0-9]', value_str):
        return True
    
    return False

def is_system_path(value: str) -> bool:
    """Cek apakah value terlihat seperti system path yang bukan social media account"""
    if not value:
        return False
    
    value_str = str(value).strip()
    
    # Cek apakah mengandung backslash (Windows path)
    if '\\' in value_str:
        path_parts = value_str.split('\\')
        if len(path_parts) >= 2:
            first_part = path_parts[0].lower()
            # Cek bagian pertama yang umum untuk system paths
            if first_part in ["cache", "cookies", "source", "users"]:
                # Cek apakah bagian berikutnya juga terlihat seperti path sistem
                if any(part.lower() in ["links", "cache", "cookies"] for part in path_parts[1:]):
                    return True
    
    # Cek pattern seperti "Cache\Links" atau "Source" yang jelas bukan account
    suspicious_patterns = [
        r'^cache\\links?$',
        r'^cookies$',
        r'^source$',
    ]
    
    for pattern in suspicious_patterns:
        if re.match(pattern, value_str.lower()):
            return True
    
    return False

def cleanup_invalid_social_media():
    """Menghapus data invalid dari tabel social_media"""
    
    print("=" * 80, flush=True)
    print("CLEANUP DATA INVALID DI TABEL SOCIAL_MEDIA", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)
    
    try:
        db = next(get_db())
        print("✅ Database connected", flush=True)
    except Exception as e:
        print(f"❌ Error connecting to database: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return
    
    try:
        # 1. Identifikasi records yang perlu dihapus
        print("🔍 Mencari data invalid...", flush=True)
        print("-" * 80, flush=True)
        
        # Query untuk menemukan records dengan data invalid
        print("  Mengambil semua records dari database...", flush=True)
        all_records = db.query(SocialMedia).all()
        print(f"  Total records ditemukan: {len(all_records)}", flush=True)
        
        invalid_ids = []
        invalid_reasons = {}
        
        for record in all_records:
            reason = None
            
            # Cek account_name
            if record.account_name:
                if is_header_or_metadata(record.account_name):
                    reason = f"account_name is header/metadata: '{record.account_name}'"
                elif is_system_path(record.account_name):
                    # Cek apakah account_id juga invalid
                    if not record.account_id or is_header_or_metadata(str(record.account_id)):
                        reason = f"account_name is system path: '{record.account_name}'"
            
            # Cek account_id
            if not reason and record.account_id:
                if is_header_or_metadata(str(record.account_id)):
                    reason = f"account_id is header/metadata: '{record.account_id}'"
                elif is_system_path(str(record.account_id)):
                    if not record.account_name or is_system_path(str(record.account_name)):
                        reason = f"account_id is system path: '{record.account_id}'"
            
            # Cek jika account_name atau account_id invalid values
            if not reason:
                invalid_values = ["nan", "none", "null", "", "n/a", "undefined"]
                if record.account_name and str(record.account_name).strip().lower() in invalid_values:
                    reason = f"account_name has invalid value: '{record.account_name}'"
                elif record.account_id and str(record.account_id).strip().lower() in invalid_values:
                    reason = f"account_id has invalid value: '{record.account_id}'"
            
            # Cek jika keduanya kosong atau tidak valid
            if not reason:
                if not record.account_name and not record.account_id:
                    reason = "both account_name and account_id are empty"
                elif (not record.account_name or str(record.account_name).strip() in ["", "nan", "none", "null"]) and \
                     (not record.account_id or str(record.account_id).strip() in ["", "nan", "none", "null"]):
                    reason = "both account_name and account_id are invalid"
            
            if reason:
                invalid_ids.append(record.id)
                invalid_reasons[record.id] = reason
        
        print(f"  Ditemukan {len(invalid_ids)} records yang invalid", flush=True)
        print(flush=True)
        
        # 2. Tampilkan sample records yang akan dihapus
        if invalid_ids:
            print("📋 SAMPLE RECORDS YANG AKAN DIHAPUS (10 pertama):")
            print("-" * 80)
            sample_ids = invalid_ids[:10]
            sample_records = db.query(SocialMedia).filter(SocialMedia.id.in_(sample_ids)).all()
            
            for record in sample_records:
                print(f"  ID {record.id}: Platform={record.platform}, Account={record.account_name[:40] if record.account_name else 'None'}, "
                      f"AccountID={record.account_id[:40] if record.account_id else 'None'}")
                print(f"      Alasan: {invalid_reasons[record.id]}")
            print()
            
            # 3. Konfirmasi dan hapus
            print(f"⚠️  PERINGATAN: Akan menghapus {len(invalid_ids)} records dari database!")
            print("   (Script dijalankan dalam mode otomatis)")
            print()
            
            # Otomatis lanjut tanpa konfirmasi untuk automation
            response = "y"
            
            if response.lower() == 'y':
                # Backup: Simpan ID yang akan dihapus ke file
                backup_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "backup_deleted_social_media_ids.txt")
                with open(backup_file, 'w') as f:
                    f.write(f"# Backup ID records yang dihapus pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    for record_id in invalid_ids:
                        record = db.query(SocialMedia).filter(SocialMedia.id == record_id).first()
                        if record:
                            account_name = str(record.account_name).replace('|', '_') if record.account_name else 'None'
                            account_id = str(record.account_id).replace('|', '_') if record.account_id else 'None'
                            reason = invalid_reasons[record_id].replace('|', '_')
                            f.write(f"{record_id}|{record.platform}|{account_name}|{account_id}|{reason}\n")
                
                print(f"  ✅ Backup tersimpan di: {backup_file}")
                print()
                
                # Hapus records
                deleted_count = 0
                for record_id in invalid_ids:
                    try:
                        record = db.query(SocialMedia).filter(SocialMedia.id == record_id).first()
                        if record:
                            db.delete(record)
                            deleted_count += 1
                    except Exception as e:
                        print(f"  ⚠️  Error menghapus record ID {record_id}: {e}")
                
                db.commit()
                
                print(f"  ✅ Berhasil menghapus {deleted_count} records invalid")
                print()
                
                # 4. Statistik setelah cleanup
                print("📊 STATISTIK SETELAH CLEANUP")
                print("-" * 80)
                
                total_after = db.query(SocialMedia).count()
                print(f"  Total records tersisa: {total_after:,}")
                print()
                
                # Cek apakah masih ada data invalid
                remaining_invalid = []
                remaining_records = db.query(SocialMedia).all()
                
                for record in remaining_records:
                    if record.account_name and is_header_or_metadata(record.account_name):
                        remaining_invalid.append(record.id)
                    elif record.account_id and is_header_or_metadata(str(record.account_id)):
                        remaining_invalid.append(record.id)
                
                if remaining_invalid:
                    print(f"  ⚠️  Masih ada {len(remaining_invalid)} records yang mungkin invalid")
                else:
                    print("  ✅ Tidak ada data invalid yang tersisa")
                
            else:
                print("  ❌ Cleanup dibatalkan")
        else:
            print("  ✅ Tidak ada data invalid yang ditemukan")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_invalid_social_media()

