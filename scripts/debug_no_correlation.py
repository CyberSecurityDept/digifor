#!/usr/bin/env python3
"""
Script untuk debug kenapa tidak ada correlation
Menganalisis data aktual di database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_db
from app.analytics.shared.models import Analytic, AnalyticDevice, Device

def debug_correlation(analytic_id: int):
    """Debug kenapa tidak ada correlation"""
    
    print("=" * 100)
    print("DEBUG: KENAPA TIDAK ADA CORRELATION")
    print("=" * 100)
    print()
    
    db = next(get_db())
    
    try:
        # 1. Cek analytic dan devices
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            print(f"❌ Analytic dengan ID {analytic_id} tidak ditemukan")
            return
        
        print(f"✅ Analytic: {analytic.analytic_name}")
        print(f"   Method: {analytic.method}")
        print()
        
        # 2. Cek devices
        device_links = (
            db.query(AnalyticDevice)
            .filter(AnalyticDevice.analytic_id == analytic_id)
            .all()
        )
        
        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        
        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        
        print(f"Devices ({len(devices)}):")
        for d in devices:
            print(f"   - Device ID {d.id}: {d.owner_name} (File ID: {d.file_id})")
        print()
        
        # 3. Cek data social_media untuk setiap file_id
        print("📊 DATA SOCIAL MEDIA PER FILE_ID:")
        print("-" * 100)
        
        for device in devices:
            file_id = device.file_id
            
            query = text("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT LOWER(TRIM(platform))) as platforms,
                    COUNT(DISTINCT LOWER(TRIM(COALESCE(account_id, account_name, '')))) as unique_accounts
                FROM social_media
                WHERE file_id = :file_id
                  AND TRIM(COALESCE(account_id, account_name, '')) != ''
                  AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
            """)
            
            stats = db.execute(query, {"file_id": file_id}).fetchone()
            
            print(f"\nFile ID {file_id} (Device: {device.owner_name}):")
            if stats:
                print(f"   Total Records: {stats[0]:,}")
                print(f"   Platforms: {stats[1]}")
                print(f"   Unique Accounts: {stats[2]:,}")
            
            # Sample data
            sample_query = text("""
                SELECT 
                    platform,
                    account_name,
                    account_id,
                    LOWER(TRIM(COALESCE(account_id, account_name, ''))) AS normalized_id
                FROM social_media
                WHERE file_id = :file_id
                  AND TRIM(COALESCE(account_id, account_name, '')) != ''
                  AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
                LIMIT 10
            """)
            
            samples = db.execute(sample_query, {"file_id": file_id}).fetchall()
            if samples:
                print(f"   Sample accounts (first 10):")
                for s in samples:
                    print(f"      - {s[0]}: {s[1] or 'N/A'} (ID: {s[2] or 'N/A'}) -> normalized: {s[3]}")
        
        print()
        print("=" * 100)
        print("🔍 ANALISIS CORRELATION LANGSUNG:")
        print("=" * 100)
        
        # 4. Cek apakah ada akun yang sama antara file_id
        if len(devices) >= 2:
            file_ids = [d.file_id for d in devices]
            
            print(f"\nMencari akun yang sama antara File ID {file_ids[0]} dan File ID {file_ids[1]}:")
            
            # Query untuk menemukan akun yang sama
            correlation_query = text("""
                WITH 
                accounts_file1 AS (
                    SELECT DISTINCT
                        LOWER(TRIM(COALESCE(account_id, account_name, ''))) AS account_identifier,
                        COALESCE(account_name, account_id, '') AS display_name,
                        LOWER(TRIM(platform)) AS platform,
                        account_id AS raw_account_id,
                        account_name AS raw_account_name
                    FROM social_media
                    WHERE file_id = :file_id_1
                      AND TRIM(COALESCE(account_id, account_name, '')) != ''
                      AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
                ),
                accounts_file2 AS (
                    SELECT DISTINCT
                        LOWER(TRIM(COALESCE(account_id, account_name, ''))) AS account_identifier,
                        COALESCE(account_name, account_id, '') AS display_name,
                        LOWER(TRIM(platform)) AS platform,
                        account_id AS raw_account_id,
                        account_name AS raw_account_name
                    FROM social_media
                    WHERE file_id = :file_id_2
                      AND TRIM(COALESCE(account_id, account_name, '')) != ''
                      AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
                )
                SELECT 
                    a1.account_identifier,
                    a1.display_name AS name_file1,
                    a1.platform,
                    a1.raw_account_id AS account_id_file1,
                    a1.raw_account_name AS account_name_file1,
                    a2.display_name AS name_file2,
                    a2.raw_account_id AS account_id_file2,
                    a2.raw_account_name AS account_name_file2
                FROM accounts_file1 a1
                INNER JOIN accounts_file2 a2 ON 
                    a1.account_identifier = a2.account_identifier
                    AND a1.platform = a2.platform
                ORDER BY a1.platform, a1.display_name
            """)
            
            correlations = db.execute(correlation_query, {
                "file_id_1": file_ids[0],
                "file_id_2": file_ids[1]
            }).fetchall()
            
            if correlations:
                print(f"\n✅ DITEMUKAN {len(correlations)} AKUN YANG SAMA:")
                print("-" * 100)
                for idx, row in enumerate(correlations, 1):
                    print(f"\n{idx}. Platform: {row[2]}")
                    print(f"   Account Identifier (normalized): {row[0]}")
                    print(f"   File ID {file_ids[0]}: {row[1]} (ID: {row[3] or 'N/A'}, Name: {row[4] or 'N/A'})")
                    print(f"   File ID {file_ids[1]}: {row[5]} (ID: {row[6] or 'N/A'}, Name: {row[7] or 'N/A'})")
            else:
                print(f"\nTIDAK ADA AKUN YANG SAMA ANTARA FILE ID {file_ids[0]} DAN {file_ids[1]}")
                print("\nKemungkinan penyebab:")
                print("   1. Data memang tidak memiliki overlap (setiap device memiliki akun unik)")
                print("   2. Normalisasi account_id/account_name mungkin terlalu ketat")
                print("   3. Data mungkin berasal dari device yang berbeda pemilik")
                
                # Cek beberapa contoh untuk verifikasi
                print("\n🔍 Verifikasi: Cek beberapa contoh account:")
                
                sample_query1 = text("""
                    SELECT DISTINCT
                        LOWER(TRIM(COALESCE(account_id, account_name, ''))) AS account_identifier,
                        COALESCE(account_name, account_id, '') AS display_name,
                        LOWER(TRIM(platform)) AS platform
                    FROM social_media
                    WHERE file_id = :file_id
                      AND TRIM(COALESCE(account_id, account_name, '')) != ''
                      AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
                      AND platform = 'instagram'
                    LIMIT 5
                """)
                
                print(f"\n   Sample dari File ID {file_ids[0]} (Instagram):")
                samples1 = db.execute(sample_query1, {"file_id": file_ids[0]}).fetchall()
                for s in samples1:
                    print(f"      - {s[0]} ({s[2]})")
                
                print(f"\n   Sample dari File ID {file_ids[1]} (Instagram):")
                samples2 = db.execute(sample_query1, {"file_id": file_ids[1]}).fetchall()
                for s in samples2:
                    print(f"      - {s[0]} ({s[2]})")
        
        print()
        print("=" * 100)
        print("✅ KESIMPULAN")
        print("=" * 100)
        
        if len(devices) >= 2:
            file_ids = [d.file_id for d in devices]
            
            # Final check dengan query endpoint
            endpoint_query = text("""
                WITH 
                device_file_ids AS (
                    SELECT DISTINCT 
                        d.id AS device_id, 
                        d.file_id,
                        d.owner_name,
                        d.phone_number,
                        ROW_NUMBER() OVER (ORDER BY d.id) as device_num,
                        CASE 
                            WHEN ROW_NUMBER() OVER (ORDER BY d.id) <= 26 
                            THEN CHR(64 + ROW_NUMBER() OVER (ORDER BY d.id)::INTEGER)
                            ELSE CHR(64 + ((ROW_NUMBER() OVER (ORDER BY d.id)::INTEGER - 26) / 26)) || 
                                 CHR(64 + ((ROW_NUMBER() OVER (ORDER BY d.id)::INTEGER - 26) % 26))
                        END AS device_label
                    FROM devices d
                    INNER JOIN analytic_device ad ON d.id = ANY(ad.device_ids)
                    WHERE ad.analytic_id = :analytic_id
                ),
                social_accounts AS (
                    SELECT 
                        LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) AS account_identifier,
                        COALESCE(sm.account_name, sm.account_id, '') AS display_name,
                        LOWER(TRIM(sm.platform)) AS platform,
                        dfi.device_id,
                        dfi.file_id
                    FROM social_media sm
                    INNER JOIN device_file_ids dfi ON sm.file_id = dfi.file_id
                    WHERE TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
                      AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
                ),
                account_device_counts AS (
                    SELECT 
                        account_identifier,
                        platform,
                        COUNT(DISTINCT device_id) AS device_count
                    FROM social_accounts
                    GROUP BY account_identifier, platform
                    HAVING COUNT(DISTINCT device_id) >= 2
                )
                SELECT COUNT(*) as total_correlations
                FROM account_device_counts
            """)
            
            result = db.execute(endpoint_query, {"analytic_id": analytic_id}).fetchone()
            total_correlations = result[0] if result else 0
            
            print(f"\nTotal Correlation (semua platform): {total_correlations}")
            
            if total_correlations == 0:
                print("\n❌ TIDAK ADA CORRELATION DITEMUKAN")
                print("\nPenjelasan:")
                print("   - Query endpoint sudah benar")
                print("   - Data di database memang tidak memiliki akun yang sama antar device")
                print("   - Ini berarti setiap device memiliki set akun social media yang unik")
                print("   - Kemungkinan besar device berasal dari pemilik yang berbeda")
            else:
                print(f"\n✅ DITEMUKAN {total_correlations} CORRELATIONS!")
                print("   Endpoint seharusnya mengembalikan data correlation")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug kenapa tidak ada correlation")
    parser.add_argument("--analytic-id", type=int, default=1, help="Analytic ID (default: 1)")
    
    args = parser.parse_args()
    
    debug_correlation(args.analytic_id)

