#!/usr/bin/env python3
"""
Script untuk memeriksa masalah insert data di tabel social_media
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
from sqlalchemy import text
from app.analytics.device_management.models import SocialMedia, File

def check_social_media_data():
    """Memeriksa data social_media di database untuk menemukan masalah"""
    
    print("=" * 80)
    print("PEMERIKSAAN DATA SOCIAL_MEDIA DI DATABASE")
    print("=" * 80)
    print()
    
    db = next(get_db())
    
    try:
        # 1. Cek total data
        total_query = text("SELECT COUNT(*) FROM social_media")
        total = db.execute(total_query).fetchone()[0]
        print(f"📊 Total records di social_media: {total:,}")
        print()
        
        # 2. Cek records dengan field kosong/null
        print("🔍 RECORDS DENGAN FIELD KOSONG/NULL")
        print("-" * 80)
        
        checks = [
            ("platform IS NULL", "Platform NULL"),
            ("account_name IS NULL OR account_name = ''", "Account Name kosong"),
            ("account_id IS NULL OR account_id = ''", "Account ID kosong"),
            ("platform IS NULL AND account_name IS NULL", "Semua field utama NULL"),
            ("file_id IS NULL", "File ID NULL"),
        ]
        
        for condition, label in checks:
            query = text(f"SELECT COUNT(*) FROM social_media WHERE {condition}")
            count = db.execute(query).fetchone()[0]
            if count > 0:
                print(f"  ⚠️  {label}: {count:,} records")
        
        print()
        
        # 3. Cek records dengan data invalid
        print("❌ RECORDS DENGAN DATA INVALID")
        print("-" * 80)
        
        invalid_checks = [
            ("account_name = 'nan' OR account_name = 'None' OR account_name = 'null'", "Account Name invalid"),
            ("account_id = 'nan' OR account_id = 'None' OR account_id = 'null'", "Account ID invalid"),
            ("platform = 'nan' OR platform = 'None' OR platform = 'null'", "Platform invalid"),
        ]
        
        for condition, label in invalid_checks:
            query = text(f"SELECT COUNT(*) FROM social_media WHERE {condition}")
            count = db.execute(query).fetchone()[0]
            if count > 0:
                print(f"  ⚠️  {label}: {count:,} records")
        
        print()
        
        # 4. Cek duplicate records
        print("🔄 DUPLICATE RECORDS")
        print("-" * 80)
        
        duplicate_query = text("""
            SELECT 
                platform,
                account_id,
                account_name,
                file_id,
                COUNT(*) as count
            FROM social_media
            WHERE platform IS NOT NULL
              AND account_id IS NOT NULL
              AND account_id != ''
              AND file_id IS NOT NULL
            GROUP BY platform, account_id, account_name, file_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 20
        """)
        
        duplicates = db.execute(duplicate_query).fetchall()
        if duplicates:
            print(f"  Ditemukan {len(duplicates)} kombinasi dengan duplicate:")
            for dup in duplicates[:10]:
                print(f"    - Platform: {dup[0]}, Account ID: {dup[1]}, File ID: {dup[3]} ({dup[4]}x)")
        else:
            print("  ✅ Tidak ada duplicate berdasarkan (platform, account_id, file_id)")
        
        print()
        
        # 5. Cek records per file_id
        print("📁 STATISTIK PER FILE_ID")
        print("-" * 80)
        
        file_stats_query = text("""
            SELECT 
                f.id,
                f.file_name,
                f.tools,
                COUNT(sm.id) as social_media_count
            FROM files f
            LEFT JOIN social_media sm ON sm.file_id = f.id
            WHERE f.type = 'social_media' OR sm.id IS NOT NULL
            GROUP BY f.id, f.file_name, f.tools
            ORDER BY social_media_count DESC
            LIMIT 20
        """)
        
        file_stats = db.execute(file_stats_query).fetchall()
        print(f"  Top 20 file dengan social media records:")
        for stat in file_stats:
            print(f"    - File ID {stat[0]}: {stat[1][:50]} ({stat[3]:,} records) - Tools: {stat[2]}")
        
        print()
        
        # 6. Cek records dengan platform yang tidak standar
        print("🏷️  PLATFORM YANG TIDAK STANDAR")
        print("-" * 80)
        
        platform_query = text("""
            SELECT 
                LOWER(platform) as platform,
                COUNT(*) as count
            FROM social_media
            WHERE platform IS NOT NULL
            GROUP BY LOWER(platform)
            ORDER BY count DESC
        """)
        
        platforms = db.execute(platform_query).fetchall()
        standard_platforms = ['instagram', 'facebook', 'whatsapp', 'telegram', 'x', 'tiktok', 'twitter']
        
        for platform in platforms:
            if platform[0] and platform[0] not in standard_platforms:
                print(f"  ⚠️  Platform non-standar: '{platform[0]}' ({platform[1]:,} records)")
        
        print()
        
        # 7. Sample data untuk review
        print("📋 SAMPLE DATA (10 RECORDS)")
        print("-" * 80)
        
        sample_query = text("""
            SELECT 
                id,
                file_id,
                platform,
                account_name,
                account_id,
                source_tool,
                sheet_name
            FROM social_media
            ORDER BY id DESC
            LIMIT 10
        """)
        
        samples = db.execute(sample_query).fetchall()
        for sample in samples:
            print(f"  ID: {sample[0]}, File: {sample[1]}, Platform: {sample[2]}, Account: {sample[3][:30] if sample[3] else 'None'}, Account ID: {sample[4][:30] if sample[4] else 'None'}")
        
        print()
        
        # 8. Cek data yang mencurigakan (kemungkinan bukan social media)
        print("🚨 DATA YANG MENcurigakan (Kemungkinan Bukan Social Media)")
        print("-" * 80)
        
        suspicious_patterns = [
            ("account_name LIKE '%\\%' OR account_name LIKE '%Source%' OR account_name LIKE '%Cache%'", "Mengandung path atau kata 'Source/Cache'"),
            ("account_id IN ('/', 'Path', 'File name', 'Source table', 'Source file size')", "Account ID adalah label kolom"),
            ("account_id LIKE '%KB%' OR account_id LIKE '%MB%'", "Account ID adalah ukuran file"),
            ("account_name LIKE '%Cookies%' OR account_name LIKE '%Cache%'", "Mengandung kata sistem"),
        ]
        
        for pattern, description in suspicious_patterns:
            query = text(f"SELECT COUNT(*) FROM social_media WHERE {pattern}")
            count = db.execute(query).fetchone()[0]
            if count > 0:
                print(f"  ⚠️  {description}: {count:,} records")
                
                # Tampilkan sample
                sample_query = text(f"""
                    SELECT id, platform, account_name, account_id
                    FROM social_media
                    WHERE {pattern}
                    LIMIT 5
                """)
                samples = db.execute(sample_query).fetchall()
                for sample in samples:
                    print(f"      - ID {sample[0]}: Platform={sample[1]}, Account={sample[2][:40] if sample[2] else 'None'}, AccountID={sample[3][:40] if sample[3] else 'None'}")
        
        print()
        
        # 9. Cek records dengan account_name atau account_id yang terlalu pendek/singkat
        print("📏 DATA DENGAN FIELD TERLALU PENDEK")
        print("-" * 80)
        
        short_query = text("""
            SELECT COUNT(*) 
            FROM social_media
            WHERE (LENGTH(account_name) <= 1 AND account_name IS NOT NULL)
               OR (LENGTH(account_id) <= 1 AND account_id IS NOT NULL)
        """)
        short_count = db.execute(short_query).fetchone()[0]
        if short_count > 0:
            print(f"  ⚠️  Records dengan field terlalu pendek (<=1 karakter): {short_count:,}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_social_media_data()

