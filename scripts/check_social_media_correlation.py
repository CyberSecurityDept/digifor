#!/usr/bin/env python3
"""
Script untuk mengecek correlation antar file_id di tabel social_media
Mencari akun social media yang muncul di beberapa file_id berbeda (menunjukkan koneksi antar device)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_db
from collections import defaultdict

def format_number(num):
    """Format angka dengan separator ribuan"""
    return f"{num:,}".replace(",", ".")

def analyze_correlation():
    """Analisis correlation antar file_id di tabel social_media"""
    
    print("=" * 80)
    print("ANALISIS CORRELATION ANTAR FILE_ID DI TABEL SOCIAL_MEDIA")
    print("=" * 80)
    print()
    
    db = next(get_db())
    
    try:
        # 1. Cek total data di tabel social_media
        print("📊 STATISTIK UMUM")
        print("-" * 80)
        
        total_query = text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT file_id) as total_file_ids,
                COUNT(DISTINCT platform) as total_platforms,
                COUNT(DISTINCT LOWER(TRIM(COALESCE(account_id, account_name, '')))) as total_unique_accounts
            FROM social_media
            WHERE TRIM(COALESCE(account_id, account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
        """)
        
        stats = db.execute(total_query).fetchone()
        if stats:
            print(f"Total Records          : {format_number(stats[0])}")
            print(f"Total File ID Berbeda  : {format_number(stats[1])}")
            print(f"Total Platform         : {format_number(stats[2])}")
            print(f"Total Akun Unik        : {format_number(stats[3])}")
        print()
        
        # 2. Statistik per platform
        print("STATISTIK PER PLATFORM")
        print("-" * 80)
        
        platform_query = text("""
            SELECT 
                LOWER(TRIM(platform)) as platform,
                COUNT(*) as total_records,
                COUNT(DISTINCT file_id) as total_files,
                COUNT(DISTINCT LOWER(TRIM(COALESCE(account_id, account_name, '')))) as unique_accounts
            FROM social_media
            WHERE platform IS NOT NULL
              AND TRIM(COALESCE(account_id, account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
            GROUP BY LOWER(TRIM(platform))
            ORDER BY total_files DESC, unique_accounts DESC
        """)
        
        platform_stats = db.execute(platform_query).fetchall()
        if platform_stats:
            print(f"{'Platform':<20} {'Records':<15} {'File IDs':<15} {'Akun Unik':<15}")
            print("-" * 65)
            for row in platform_stats:
                platform_name = row[0] or "NULL"
                print(f"{platform_name:<20} {format_number(row[1]):<15} {format_number(row[2]):<15} {format_number(row[3]):<15}")
        print()
        
        # 3. Mencari correlation: Akun yang muncul di banyak file_id
        print("🔗 CORRELATION ANALYSIS - Akun yang Muncul di Banyak File ID")
        print("-" * 80)
        print("(Mencari akun social media yang muncul di minimal 2 file_id berbeda)")
        print()
        
        correlation_query = text("""
            SELECT 
                LOWER(TRIM(COALESCE(account_id, account_name, ''))) AS account_identifier,
                COALESCE(account_name, account_id, '') AS display_name,
                LOWER(TRIM(platform)) AS platform,
                COUNT(DISTINCT file_id) AS file_count,
                COUNT(*) AS total_records,
                ARRAY_AGG(DISTINCT file_id ORDER BY file_id) AS file_ids,
                STRING_AGG(DISTINCT CAST(file_id AS TEXT), ', ' ORDER BY CAST(file_id AS TEXT)) AS file_ids_list
            FROM social_media
            WHERE TRIM(COALESCE(account_id, account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
              AND platform IS NOT NULL
            GROUP BY 
                LOWER(TRIM(COALESCE(account_id, account_name, ''))),
                COALESCE(account_name, account_id, ''),
                LOWER(TRIM(platform))
            HAVING COUNT(DISTINCT file_id) >= 2
            ORDER BY file_count DESC, platform ASC, display_name ASC
            LIMIT 50
        """)
        
        correlations = db.execute(correlation_query).fetchall()
        
        if correlations:
            print(f"Total Akun dengan Correlation: {format_number(len(correlations))}")
            print()
            print(f"{'No':<5} {'Platform':<15} {'Account Name':<30} {'File Count':<12} {'File IDs':<30}")
            print("-" * 92)
            
            for idx, row in enumerate(correlations, 1):
                account_id = row[0]
                display_name = (row[1] or "N/A")[:28]
                platform = (row[2] or "N/A")[:13]
                file_count = row[3]
                file_ids_str = row[6] or ""
                
                if len(file_ids_str) > 28:
                    file_ids_str = file_ids_str[:25] + "..."
                
                print(f"{idx:<5} {platform:<15} {display_name:<30} {file_count:<12} {file_ids_str:<30}")
            
            print()
            print("📋 DETAIL CORRELATION (Top 10)")
            print("-" * 80)
            
            for idx, row in enumerate(correlations[:10], 1):
                account_id = row[0]
                display_name = row[1] or "N/A"
                platform = row[2] or "N/A"
                file_count = row[3]
                total_records = row[4]
                file_ids = row[5]
                
                print(f"\n{idx}. Platform: {platform.upper()}")
                print(f"   Account: {display_name}")
                print(f"   Account ID (normalized): {account_id}")
                print(f"   Muncul di {file_count} file_id berbeda")
                print(f"   Total records: {format_number(total_records)}")
                print(f"   File IDs: {', '.join(map(str, file_ids))}")
                
        else:
            print("Tidak ditemukan correlation antar file_id")
            print("   (Tidak ada akun yang muncul di minimal 2 file_id berbeda)")
        print()
        
        # 4. Detail per file_id
        print("📁 DISTRIBUSI DATA PER FILE_ID")
        print("-" * 80)
        
        file_distribution_query = text("""
            SELECT 
                file_id,
                COUNT(*) as total_records,
                COUNT(DISTINCT LOWER(TRIM(platform))) as platform_count,
                COUNT(DISTINCT LOWER(TRIM(COALESCE(account_id, account_name, '')))) as account_count,
                STRING_AGG(DISTINCT LOWER(TRIM(platform)), ', ' ORDER BY LOWER(TRIM(platform))) as platforms
            FROM social_media
            WHERE TRIM(COALESCE(account_id, account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
            GROUP BY file_id
            ORDER BY total_records DESC
            LIMIT 20
        """)
        
        file_dist = db.execute(file_distribution_query).fetchall()
        if file_dist:
            print(f"{'File ID':<10} {'Records':<15} {'Platforms':<10} {'Akun Unik':<15} {'Platforms':<30}")
            print("-" * 80)
            for row in file_dist:
                platforms_str = row[4] or "N/A"
                if len(platforms_str) > 28:
                    platforms_str = platforms_str[:25] + "..."
                print(f"{row[0]:<10} {format_number(row[1]):<15} {row[2]:<10} {format_number(row[3]):<15} {platforms_str:<30}")
        print()
        
        # 5. Matrix correlation sederhana (file_id x file_id)
        print("🔢 MATRIX CORRELATION FILE_ID")
        print("-" * 80)
        print("(Menunjukkan berapa banyak akun yang sama antara dua file_id)")
        print()
        
        matrix_query = text("""
            WITH file_accounts AS (
                SELECT DISTINCT
                    file_id,
                    LOWER(TRIM(COALESCE(account_id, account_name, ''))) AS account_identifier,
                    LOWER(TRIM(platform)) AS platform
                FROM social_media
                WHERE TRIM(COALESCE(account_id, account_name, '')) != ''
                  AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
                  AND platform IS NOT NULL
            ),
            file_pairs AS (
                SELECT 
                    fa1.file_id AS file_id_1,
                    fa2.file_id AS file_id_2,
                    COUNT(DISTINCT fa1.account_identifier) AS shared_accounts
                FROM file_accounts fa1
                INNER JOIN file_accounts fa2 ON 
                    fa1.account_identifier = fa2.account_identifier
                    AND fa1.platform = fa2.platform
                    AND fa1.file_id < fa2.file_id
                GROUP BY fa1.file_id, fa2.file_id
                HAVING COUNT(DISTINCT fa1.account_identifier) > 0
            )
            SELECT 
                file_id_1,
                file_id_2,
                shared_accounts
            FROM file_pairs
            ORDER BY shared_accounts DESC
            LIMIT 30
        """)
        
        matrix_results = db.execute(matrix_query).fetchall()
        if matrix_results:
            print(f"{'File ID 1':<12} {'File ID 2':<12} {'Shared Accounts':<15}")
            print("-" * 39)
            for row in matrix_results:
                print(f"{row[0]:<12} {row[1]:<12} {format_number(row[2]):<15}")
        else:
            print("Tidak ada file_id yang saling berbagi akun yang sama")
        print()
        
        # 6. Summary
        print("=" * 80)
        print("📌 KESIMPULAN")
        print("=" * 80)
        
        summary_query = text("""
            SELECT 
                COUNT(DISTINCT sm.file_id) as total_files,
                COUNT(DISTINCT LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, '')))) as total_accounts,
                COUNT(DISTINCT CASE 
                    WHEN account_counts.file_count >= 2 
                    THEN LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, '')))
                END) as correlated_accounts
            FROM social_media sm
            LEFT JOIN (
                SELECT 
                    LOWER(TRIM(COALESCE(account_id, account_name, ''))) AS normalized_account_id,
                    COUNT(DISTINCT file_id) AS file_count
                FROM social_media
                WHERE TRIM(COALESCE(account_id, account_name, '')) != ''
                  AND LOWER(TRIM(COALESCE(account_id, account_name, ''))) NOT IN ('nan', 'none', 'null', '')
                GROUP BY LOWER(TRIM(COALESCE(account_id, account_name, '')))
            ) account_counts ON LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) = account_counts.normalized_account_id
            WHERE TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
        """)
        
        summary = db.execute(summary_query).fetchone()
        if summary:
            total_files = summary[0] or 0
            total_accounts = summary[1] or 0
            correlated_accounts = summary[2] or 0
            
            print(f"Total File ID yang dianalisis     : {format_number(total_files)}")
            print(f"Total Akun Unik                   : {format_number(total_accounts)}")
            print(f"Akun dengan Correlation (≥2 file) : {format_number(correlated_accounts)}")
            
            if total_accounts > 0:
                percentage = (correlated_accounts / total_accounts) * 100
                print(f"Persentase Correlation          : {percentage:.2f}%")
            else:
                print("Persentase Correlation          : 0%")
            
            print()
            if correlated_accounts > 0:
                print("✅ Ditemukan correlation antar file_id!")
                print("   Ini menunjukkan bahwa beberapa device berbagi akun social media yang sama.")
            else:
                print("ℹ️  Tidak ada correlation yang ditemukan.")
                print("   Setiap file_id memiliki akun social media yang unik.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print()
    print("=" * 80)
    print("Selesai!")
    print("=" * 80)

if __name__ == "__main__":
    analyze_correlation()

