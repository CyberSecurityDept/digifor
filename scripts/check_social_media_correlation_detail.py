#!/usr/bin/env python3
"""
Script untuk melihat detail correlation antar file_id di tabel social_media
Menampilkan akun yang muncul di beberapa file_id (termasuk yang hanya 1 untuk verifikasi)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_db

def format_number(num):
    """Format angka dengan separator ribuan"""
    return f"{num:,}".replace(",", ".")

def show_detailed_correlation():
    """Menampilkan detail correlation antar file_id"""
    
    print("=" * 100)
    print("DETAIL CORRELATION ANTAR FILE_ID DI TABEL SOCIAL_MEDIA")
    print("=" * 100)
    print()
    
    db = next(get_db())
    
    try:
        # Query untuk menemukan semua akun yang muncul di beberapa file_id
        print("📋 DAFTAR AKUN YANG MUNCUL DI BEBERAPA FILE_ID")
        print("-" * 100)
        print()
        
        # 1. Akun dengan correlation (muncul di ≥2 file_id)
        print("✅ AKUN DENGAN CORRELATION (Muncul di minimal 2 File ID):")
        print("-" * 100)
        
        correlation_query = text("""
            SELECT 
                LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) AS account_identifier,
                COALESCE(sm.account_name, sm.account_id, 'N/A') AS display_name,
                LOWER(TRIM(sm.platform)) AS platform,
                COUNT(DISTINCT sm.file_id) AS file_count,
                COUNT(*) AS total_records,
                ARRAY_AGG(DISTINCT sm.file_id ORDER BY sm.file_id) AS file_ids,
                STRING_AGG(DISTINCT CAST(sm.file_id AS TEXT), ', ' ORDER BY CAST(sm.file_id AS TEXT)) AS file_ids_list,
                STRING_AGG(DISTINCT 
                    CASE 
                        WHEN sm.full_name IS NOT NULL AND TRIM(sm.full_name) != '' 
                        THEN sm.full_name 
                        ELSE NULL 
                    END, 
                    ' | ' 
                ) AS full_names,
                STRING_AGG(DISTINCT 
                    CASE 
                        WHEN sm.user_id IS NOT NULL AND TRIM(sm.user_id) != '' 
                        THEN sm.user_id 
                        ELSE NULL 
                    END, 
                    ' | ' 
                ) AS user_ids
            FROM social_media sm
            WHERE TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
              AND sm.platform IS NOT NULL
            GROUP BY 
                LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))),
                COALESCE(sm.account_name, sm.account_id, 'N/A'),
                LOWER(TRIM(sm.platform))
            HAVING COUNT(DISTINCT sm.file_id) >= 2
            ORDER BY file_count DESC, platform ASC, display_name ASC
        """)
        
        correlations = db.execute(correlation_query).fetchall()
        
        if correlations:
            for idx, row in enumerate(correlations, 1):
                account_id = row[0]
                display_name = row[1]
                platform = row[2] or "N/A"
                file_count = row[3]
                total_records = row[4]
                file_ids = row[5]
                file_ids_list = row[6]
                full_names = row[7]
                user_ids = row[8]
                
                print(f"\n{idx}. {platform.upper()} - {display_name}")
                print(f"   Account ID (normalized): {account_id}")
                if full_names and full_names != "NULL":
                    print(f"   Full Name(s): {full_names}")
                if user_ids and user_ids != "NULL":
                    print(f"   User ID(s): {user_ids}")
                print(f"   Muncul di {file_count} file_id berbeda")
                print(f"   Total records: {format_number(total_records)}")
                print(f"   File IDs: {file_ids_list}")
                
                # Ambil detail per file_id
                detail_query = text("""
                    SELECT 
                        sm.file_id,
                        COUNT(*) as records_in_file,
                        sm.account_name,
                        sm.account_id,
                        sm.full_name,
                        sm.user_id,
                        f.file_name
                    FROM social_media sm
                    LEFT JOIN files f ON sm.file_id = f.id
                    WHERE LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) = :account_id
                      AND LOWER(TRIM(sm.platform)) = :platform
                    GROUP BY sm.file_id, sm.account_name, sm.account_id, sm.full_name, sm.user_id, f.file_name
                    ORDER BY sm.file_id
                """)
                
                details = db.execute(detail_query, {
                    "account_id": account_id,
                    "platform": platform
                }).fetchall()
                
                print(f"   Detail per File ID:")
                for detail in details:
                    file_id = detail[0]
                    records = detail[1]
                    acc_name = detail[2] or "N/A"
                    acc_id = detail[3] or "N/A"
                    full_name = detail[4] or "N/A"
                    user_id = detail[5] or "N/A"
                    file_name = detail[6] or "N/A"
                    
                    print(f"      • File ID {file_id} ({file_name}):")
                    print(f"        - Records: {records}")
                    print(f"        - Account Name: {acc_name}")
                    print(f"        - Account ID: {acc_id}")
                    if full_name != "N/A":
                        print(f"        - Full Name: {full_name}")
                    if user_id != "N/A":
                        print(f"        - User ID: {user_id}")
        else:
            print("Tidak ada akun yang muncul di minimal 2 file_id berbeda.")
        
        print()
        print()
        
        # 2. Statistik per file_id untuk melihat overlap
        print("📊 STATISTIK PER FILE_ID (Untuk Analisis Overlap)")
        print("-" * 100)
        
        file_stats_query = text("""
            SELECT 
                sm.file_id,
                f.file_name,
                COUNT(*) as total_records,
                COUNT(DISTINCT LOWER(TRIM(sm.platform))) as platform_count,
                COUNT(DISTINCT LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, '')))) as unique_accounts,
                STRING_AGG(DISTINCT LOWER(TRIM(sm.platform)), ', ' ORDER BY LOWER(TRIM(sm.platform))) as platforms
            FROM social_media sm
            LEFT JOIN files f ON sm.file_id = f.id
            WHERE TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
            GROUP BY sm.file_id, f.file_name
            ORDER BY sm.file_id
        """)
        
        file_stats = db.execute(file_stats_query).fetchall()
        if file_stats:
            print(f"{'File ID':<10} {'File Name':<50} {'Records':<12} {'Platforms':<10} {'Akun Unik':<12}")
            print("-" * 94)
            for row in file_stats:
                file_id = row[0]
                file_name = (row[1] or "N/A")[:48]
                records = row[2]
                platform_count = row[3]
                unique_accounts = row[4]
                
                print(f"{file_id:<10} {file_name:<50} {format_number(records):<12} {platform_count:<10} {format_number(unique_accounts):<12}")
        
        print()
        print()
        
        # 3. Query untuk melihat apakah ada akun yang mirip (kemungkinan typo atau variasi)
        print("🔍 ANALISIS AKUN YANG MIRIP (Kemungkinan Typo/Variasi)")
        print("-" * 100)
        print("(Mencari akun dengan nama yang mirip tapi berbeda file_id)")
        print()
        
        similar_query = text("""
            WITH account_info AS (
                SELECT DISTINCT
                    sm.file_id,
                    LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) AS account_identifier,
                    COALESCE(sm.account_name, sm.account_id, '') AS display_name,
                    LOWER(TRIM(sm.platform)) AS platform
                FROM social_media sm
                WHERE TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
                  AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
                  AND sm.platform IS NOT NULL
            )
            SELECT 
                ai1.account_identifier AS account_1,
                ai1.display_name AS name_1,
                ai1.file_id AS file_id_1,
                ai2.account_identifier AS account_2,
                ai2.display_name AS name_2,
                ai2.file_id AS file_id_2,
                ai1.platform
            FROM account_info ai1
            INNER JOIN account_info ai2 ON 
                ai1.platform = ai2.platform
                AND ai1.file_id < ai2.file_id
                AND ai1.account_identifier != ai2.account_identifier
                AND (
                    ai1.account_identifier LIKE '%' || ai2.account_identifier || '%'
                    OR ai2.account_identifier LIKE '%' || ai1.account_identifier || '%'
                    OR LENGTH(ai1.account_identifier) = LENGTH(ai2.account_identifier)
                )
            WHERE LENGTH(ai1.account_identifier) >= 3
              AND LENGTH(ai2.account_identifier) >= 3
            ORDER BY ai1.platform, ai1.account_identifier
            LIMIT 20
        """)
        
        similar_accounts = db.execute(similar_query).fetchall()
        if similar_accounts:
            print(f"Ditemukan {len(similar_accounts)} pasangan akun yang mirip:")
            print()
            for idx, row in enumerate(similar_accounts, 1):
                print(f"{idx}. Platform: {row[6] or 'N/A'}")
                print(f"   File ID {row[2]}: {row[1]} (ID: {row[0]})")
                print(f"   File ID {row[5]}: {row[4]} (ID: {row[3]})")
                print()
        else:
            print("Tidak ditemukan akun yang mirip antar file_id.")
        
        print()
        print("=" * 100)
        print("Selesai!")
        print("=" * 100)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    show_detailed_correlation()

