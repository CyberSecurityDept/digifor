#!/usr/bin/env python3
"""
Script untuk testing endpoint social-media-correlation
Mengetes query SQL dan response format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, AnalyticDevice, Device
import json
from typing import Dict, Any

def test_sql_query(analytic_id: int, platform: str = "instagram"):
    """Test query SQL langsung"""
    print("=" * 100)
    print("TEST SQL QUERY LANGSUNG")
    print("=" * 100)
    
    db = next(get_db())
    
    try:
        # Query yang sama dengan endpoint
        sql_query = text("""
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
                    dfi.device_label,
                    dfi.owner_name AS device_owner,
                    dfi.phone_number AS device_phone,
                    dfi.device_num,
                    sm.file_id
                FROM social_media sm
                INNER JOIN device_file_ids dfi ON sm.file_id = dfi.file_id
                WHERE LOWER(TRIM(sm.platform)) = :selected_platform
                  AND TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
                  AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
            ),
            account_device_counts AS (
                SELECT 
                    account_identifier,
                    display_name,
                    platform,
                    COUNT(DISTINCT device_id) AS device_count,
                    ARRAY_AGG(DISTINCT device_id ORDER BY device_id) AS device_ids,
                    STRING_AGG(DISTINCT device_owner, ', ' ORDER BY device_owner) AS device_owners
                FROM social_accounts
                GROUP BY account_identifier, display_name, platform
                HAVING COUNT(DISTINCT device_id) >= 2
            )
            SELECT 
                adc.account_identifier,
                adc.display_name AS account_name,
                adc.platform,
                adc.device_count AS total_connections,
                adc.device_owners,
                sa.device_label,
                sa.device_id,
                sa.device_owner,
                sa.device_phone,
                sa.device_num
            FROM account_device_counts adc
            INNER JOIN social_accounts sa ON 
                adc.account_identifier = sa.account_identifier 
                AND adc.platform = sa.platform
            ORDER BY 
                adc.device_count DESC,
                adc.display_name ASC,
                sa.device_num ASC
        """)
        
        platform_lower = platform.lower().strip()
        platform_map = {
            "instagram": "instagram",
            "facebook": "facebook",
            "whatsapp": "whatsapp",
            "tiktok": "tiktok",
            "telegram": "telegram",
            "x": "x",
            "twitter": "x"
        }
        selected_platform = platform_map.get(platform_lower, "instagram")
        
        print(f"\n📋 Parameter Query:")
        print(f"   Analytic ID: {analytic_id}")
        print(f"   Platform (input): {platform}")
        print(f"   Platform (normalized): {selected_platform}")
        print()
        
        # Execute query
        query_result = db.execute(
            sql_query, 
            {"analytic_id": analytic_id, "selected_platform": selected_platform}
        ).fetchall()
        
        print(f"📊 Hasil Query:")
        print(f"   Total rows: {len(query_result)}")
        print()
        
        if query_result:
            print("✅ Data Correlation Ditemukan:")
            print("-" * 100)
            print(f"{'No':<5} {'Platform':<15} {'Account Name':<30} {'Device Count':<15} {'Device IDs':<30}")
            print("-" * 100)
            
            for idx, row in enumerate(query_result[:20], 1):  # Limit 20 untuk preview
                account_id = row[0]
                account_name = (row[1] or "N/A")[:28]
                platform_name = (row[2] or "N/A")[:13]
                device_count = row[3]
                device_ids_str = str(row[5] if len(row) > 5 else "N/A")[:28]
                
                print(f"{idx:<5} {platform_name:<15} {account_name:<30} {device_count:<15} {device_ids_str:<30}")
            
            if len(query_result) > 20:
                print(f"\n... dan {len(query_result) - 20} rows lainnya")
        else:
            print("Tidak ada correlation ditemukan")
            print("   (Tidak ada akun yang muncul di minimal 2 device)")
        
        print()
        
        # Cek data device dan file_id
        print("Info Device & File ID:")
        print("-" * 100)
        
        device_query = text("""
            SELECT DISTINCT 
                d.id AS device_id,
                d.file_id,
                d.owner_name,
                d.phone_number
            FROM devices d
            INNER JOIN analytic_device ad ON d.id = ANY(ad.device_ids)
            WHERE ad.analytic_id = :analytic_id
            ORDER BY d.id
        """)
        
        device_result = db.execute(device_query, {"analytic_id": analytic_id}).fetchall()
        
        if device_result:
            print(f"{'Device ID':<12} {'File ID':<10} {'Owner Name':<30} {'Phone':<20}")
            print("-" * 72)
            for row in device_result:
                print(f"{row[0]:<12} {row[1]:<10} {(row[2] or 'N/A')[:28]:<30} {(row[3] or 'N/A')[:18]:<20}")
        else:
            print("Tidak ada device ditemukan untuk analytic ini")
        
        print()
        
        # Cek data social_media untuk analytic ini
        print("Data Social Media di Database:")
        print("-" * 100)
        
        sm_query = text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT sm.file_id) as total_file_ids,
                COUNT(DISTINCT LOWER(TRIM(sm.platform))) as total_platforms,
                COUNT(DISTINCT LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, '')))) as total_accounts
            FROM social_media sm
            INNER JOIN devices d ON sm.file_id = d.file_id
            INNER JOIN analytic_device ad ON d.id = ANY(ad.device_ids)
            WHERE ad.analytic_id = :analytic_id
              AND TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
        """)
        
        sm_stats = db.execute(sm_query, {"analytic_id": analytic_id}).fetchone()
        
        if sm_stats:
            print(f"Total Records        : {sm_stats[0]:,}")
            print(f"Total File IDs       : {sm_stats[1]:,}")
            print(f"Total Platforms      : {sm_stats[2]:,}")
            print(f"Total Accounts       : {sm_stats[3]:,}")
        
        print()
        
        # Cek per platform
        sm_platform_query = text("""
            SELECT 
                LOWER(TRIM(sm.platform)) as platform,
                COUNT(*) as records,
                COUNT(DISTINCT sm.file_id) as file_ids,
                COUNT(DISTINCT LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, '')))) as accounts
            FROM social_media sm
            INNER JOIN devices d ON sm.file_id = d.file_id
            INNER JOIN analytic_device ad ON d.id = ANY(ad.device_ids)
            WHERE ad.analytic_id = :analytic_id
              AND TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
              AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
            GROUP BY LOWER(TRIM(sm.platform))
            ORDER BY records DESC
        """)
        
        sm_platform_result = db.execute(sm_platform_query, {"analytic_id": analytic_id}).fetchall()
        
        if sm_platform_result:
            print("Per Platform:")
            print(f"{'Platform':<20} {'Records':<15} {'File IDs':<12} {'Accounts':<15}")
            print("-" * 62)
            for row in sm_platform_result:
                print(f"{(row[0] or 'N/A')[:18]:<20} {row[1]:,<15} {row[2]:<12} {row[3]:,<15}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_endpoint_logic(analytic_id: int, platform: str = "Instagram"):
    """Test logika endpoint tanpa HTTP"""
    print("\n" + "=" * 100)
    print("TEST ENDPOINT LOGIC (Simulasi)")
    print("=" * 100)
    
    db = next(get_db())
    
    try:
        # Step 1: Cek analytic
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            print(f"❌ Analytic dengan ID {analytic_id} tidak ditemukan")
            return
        
        print(f"✅ Analytic ditemukan:")
        print(f"   ID: {analytic.id}")
        print(f"   Name: {analytic.analytic_name}")
        print(f"   Method: {analytic.method}")
        print()
        
        if analytic.method != "Social Media Correlation":
            print(f"Warning: Method bukan 'Social Media Correlation'")
            print(f"   Current method: '{analytic.method}'")
            print()
        
        # Step 2: Get devices
        device_links = (
            db.query(AnalyticDevice)
            .filter(AnalyticDevice.analytic_id == analytic_id)
            .all()
        )
        
        if not device_links:
            print("❌ Tidak ada device ditemukan")
            return
        
        device_ids = []
        for link in device_links:
            device_ids.extend(link.device_ids)
        
        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        
        print(f"✅ Devices ditemukan: {len(devices)}")
        for d in devices:
            print(f"   - Device ID {d.id}: {d.owner_name or 'N/A'} (File ID: {d.file_id})")
        print()
        
        # Step 3: Normalize platform
        platform_lower = (platform or "Instagram").lower().strip()
        platform_map = {
            "instagram": "instagram",
            "facebook": "facebook",
            "whatsapp": "whatsapp",
            "tiktok": "tiktok",
            "telegram": "telegram",
            "x": "x",
            "twitter": "x"
        }
        selected_platform = platform_map.get(platform_lower, "instagram")
        
        print(f"✅ Platform normalization:")
        print(f"   Input: '{platform}'")
        print(f"   Normalized: '{selected_platform}'")
        print()
        
        # Step 4: Execute query
        sql_query = text("""
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
                    dfi.device_label,
                    dfi.owner_name AS device_owner,
                    dfi.phone_number AS device_phone,
                    dfi.device_num,
                    sm.file_id
                FROM social_media sm
                INNER JOIN device_file_ids dfi ON sm.file_id = dfi.file_id
                WHERE LOWER(TRIM(sm.platform)) = :selected_platform
                  AND TRIM(COALESCE(sm.account_id, sm.account_name, '')) != ''
                  AND LOWER(TRIM(COALESCE(sm.account_id, sm.account_name, ''))) NOT IN ('nan', 'none', 'null', '')
            ),
            account_device_counts AS (
                SELECT 
                    account_identifier,
                    display_name,
                    platform,
                    COUNT(DISTINCT device_id) AS device_count,
                    ARRAY_AGG(DISTINCT device_id ORDER BY device_id) AS device_ids,
                    STRING_AGG(DISTINCT device_owner, ', ' ORDER BY device_owner) AS device_owners
                FROM social_accounts
                GROUP BY account_identifier, display_name, platform
                HAVING COUNT(DISTINCT device_id) >= 2
            )
            SELECT 
                adc.account_identifier,
                adc.display_name AS account_name,
                adc.platform,
                adc.device_count AS total_connections,
                adc.device_owners,
                sa.device_label,
                sa.device_id,
                sa.device_owner,
                sa.device_phone,
                sa.device_num
            FROM account_device_counts adc
            INNER JOIN social_accounts sa ON 
                adc.account_identifier = sa.account_identifier 
                AND adc.platform = sa.platform
            ORDER BY 
                adc.device_count DESC,
                adc.display_name ASC,
                sa.device_num ASC
        """)
        
        query_result = db.execute(
            sql_query, 
            {"analytic_id": analytic_id, "selected_platform": selected_platform}
        ).fetchall()
        
        print(f"✅ Query executed: {len(query_result)} rows returned")
        print()
        
        # Step 5: Process results (simulasi endpoint)
        device_order = sorted(devices, key=lambda d: d.id)
        device_label_map = {}
        device_labels = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        for idx, d in enumerate(device_order):
            if idx < len(device_labels):
                device_label_map[d.id] = device_labels[idx]
            else:
                first_char = chr(65 + (idx - 26) // 26)
                second_char = chr(65 + (idx - 26) % 26)
                device_label_map[d.id] = f"{first_char}{second_char}"
        
        account_info_map = {}
        account_device_map = {}
        
        for row in query_result:
            account_id = row.account_identifier
            if account_id not in account_info_map:
                account_info_map[account_id] = {
                    'display_name': row.account_name,
                    'device_count': row.total_connections,
                    'devices': set()
                }
            account_info_map[account_id]['devices'].add(row.device_id)
            
            if account_id not in account_device_map:
                account_device_map[account_id] = {}
            account_device_map[account_id][row.device_id] = {
                'device_label': row.device_label,
                'device_owner': row.device_owner,
                'device_phone': row.device_phone
            }
        
        print(f"✅ Processed results:")
        print(f"   Total accounts with correlation: {len(account_info_map)}")
        print(f"   Total devices: {len(device_order)}")
        print()
        
        # Summary
        print("📊 SUMMARY RESULT:")
        print("-" * 100)
        for account_id, account_info in sorted(account_info_map.items(), key=lambda x: x[1]['device_count'], reverse=True):
            print(f"Account: {account_info['display_name']}")
            print(f"  - Device count: {account_info['device_count']}")
            print(f"  - Device IDs: {sorted(list(account_info['devices']))}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def list_analytics():
    """List semua analytics dengan method Social Media Correlation"""
    print("=" * 100)
    print("LIST ANALYTICS - SOCIAL MEDIA CORRELATION")
    print("=" * 100)
    
    db = next(get_db())
    
    try:
        analytics = db.query(Analytic).filter(
            Analytic.method == "Social Media Correlation"
        ).all()
        
        if analytics:
            print(f"\n✅ Ditemukan {len(analytics)} analytics:")
            print(f"{'ID':<10} {'Name':<50} {'Created At':<25}")
            print("-" * 85)
            for a in analytics:
                print(f"{a.id:<10} {(a.analytic_name or 'N/A')[:48]:<50} {str(a.created_at)[:24]:<25}")
        else:
            print("\nTidak ada analytics dengan method 'Social Media Correlation'")
            print("\n📋 Semua analytics:")
            all_analytics = db.query(Analytic).all()
            if all_analytics:
                print(f"{'ID':<10} {'Name':<50} {'Method':<30}")
                print("-" * 90)
                for a in all_analytics:
                    print(f"{a.id:<10} {(a.analytic_name or 'N/A')[:48]:<50} {(a.method or 'N/A')[:28]:<30}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Social Media Correlation Endpoint")
    parser.add_argument("--analytic-id", type=int, help="Analytic ID to test")
    parser.add_argument("--platform", type=str, default="Instagram", help="Platform filter (default: Instagram)")
    parser.add_argument("--list", action="store_true", help="List all Social Media Correlation analytics")
    
    args = parser.parse_args()
    
    if args.list:
        list_analytics()
    elif args.analytic_id:
        test_sql_query(args.analytic_id, args.platform)
        test_endpoint_logic(args.analytic_id, args.platform)
    else:
        print("Usage:")
        print("  List analytics: python test_social_media_correlation_endpoint.py --list")
        print("  Test endpoint: python test_social_media_correlation_endpoint.py --analytic-id <ID> --platform <Platform>")
        print("\nExample:")
        print("  python test_social_media_correlation_endpoint.py --list")
        print("  python test_social_media_correlation_endpoint.py --analytic-id 1 --platform Instagram")

