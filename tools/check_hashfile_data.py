#!/usr/bin/env python3
"""
Script to check hashfile data in database for correlation analysis
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.analytics.shared.models import Analytic, AnalyticDevice, Device
from app.analytics.device_management.models import HashFile
from sqlalchemy import func, or_

def check_hashfile_data(analytic_id: int = 1):
    """Check hashfile data for given analytic_id"""
    db = SessionLocal()
    
    try:
        print(f"=" * 80)
        print(f"Checking hashfile data for Analytic ID: {analytic_id}")
        print(f"=" * 80)
        
        # 1. Check Analytic
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            print(f"❌ Analytic ID {analytic_id} not found!")
            return
        
        print(f"\nAnalytic found:")
        print(f"   ID: {analytic.id}")
        print(f"   Name: {analytic.analytic_name}")
        print(f"   Method: {analytic.method}")
        
        # 2. Check Devices
        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).all()
        
        device_ids = list({d for link in device_links for d in link.device_ids})
        print(f"\n📱 Device IDs from AnalyticDevice: {device_ids}")
        
        if not device_ids:
            print("❌ No devices linked to this analytic!")
            return
        
        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        print(f"Found {len(devices)} devices:")
        for d in devices:
            print(f"   Device ID: {d.id}, File ID: {d.file_id}, Owner: {d.owner_name}")
        
        file_ids = [d.file_id for d in devices]
        print(f"\n📁 File IDs: {file_ids}")
        
        # 3. Check Hashfiles
        hashfiles = (
            db.query(HashFile)
            .filter(HashFile.file_id.in_(file_ids))
            .filter(or_(HashFile.md5_hash != None, HashFile.sha1_hash != None))
            .all()
        )
        
        print(f"\n📊 Hashfile Statistics:")
        print(f"   Total hashfiles with hash: {len(hashfiles)}")
        
        if not hashfiles:
            print("❌ No hashfiles found with hash values!")
            return
        
        # Count by file_id
        hashfiles_by_file = {}
        for hf in hashfiles:
            if hf.file_id not in hashfiles_by_file:
                hashfiles_by_file[hf.file_id] = []
            hashfiles_by_file[hf.file_id].append(hf)
        
        print(f"\n📋 Hashfiles by File ID:")
        for file_id, hfs in hashfiles_by_file.items():
            print(f"   File ID {file_id}: {len(hfs)} hashfiles")
            md5_count = sum(1 for hf in hfs if hf.md5_hash)
            sha1_count = sum(1 for hf in hfs if hf.sha1_hash)
            with_name = sum(1 for hf in hfs if hf.file_name)
            print(f"      - MD5 hashes: {md5_count}")
            print(f"      - SHA1 hashes: {sha1_count}")
            print(f"      - With file_name: {with_name}")
        
        # 4. Check for correlations (hash + file_name)
        print(f"\n🔍 Checking Correlations (hash + file_name):")
        
        # Group by hash + file_name
        correlation_map = {}
        for hf in hashfiles:
            hash_value = hf.md5_hash or hf.sha1_hash
            if not hash_value or not hf.file_name:
                continue
            
            key = f"{hash_value}::{hf.file_name.strip().lower()}"
            if key not in correlation_map:
                correlation_map[key] = {"file_ids": set(), "devices": set(), "count": 0}
            
            correlation_map[key]["file_ids"].add(hf.file_id)
            # Find device_id for this file_id
            for d in devices:
                if d.file_id == hf.file_id:
                    correlation_map[key]["devices"].add(d.id)
            correlation_map[key]["count"] += 1
        
        print(f"   Total unique correlation keys: {len(correlation_map)}")
        
        # Count correlations that appear in multiple devices
        multi_device_correlations = {
            key: data for key, data in correlation_map.items()
            if len(data["devices"]) >= 2
        }
        
        print(f"   Correlations in >= 2 devices: {len(multi_device_correlations)}")
        
        if multi_device_correlations:
            print(f"\nSample Correlations (first 5):")
            for i, (key, data) in enumerate(list(multi_device_correlations.items())[:5]):
                hash_part = key.split("::")[0][:20] + "..." if len(key.split("::")[0]) > 20 else key.split("::")[0]
                name_part = key.split("::")[1] if "::" in key else "N/A"
                print(f"   {i+1}. Hash: {hash_part}, Name: {name_part[:50]}")
                print(f"      Devices: {data['devices']}, Files: {data['file_ids']}, Count: {data['count']}")
        else:
            print(f"\n⚠️  No correlations found in multiple devices!")
            print(f"   This could mean:")
            print(f"   - Hashfiles have different hashes in different devices")
            print(f"   - Hashfiles have same hash but different file_name")
            print(f"   - Hashfiles don't have file_name set")
        
        # 5. Check hash-only correlations
        print(f"\n🔍 Checking Hash-Only Correlations:")
        hash_only_map = {}
        for hf in hashfiles:
            hash_value = hf.md5_hash or hf.sha1_hash
            if not hash_value:
                continue
            
            if hash_value not in hash_only_map:
                hash_only_map[hash_value] = {"file_ids": set(), "devices": set(), "count": 0}
            
            hash_only_map[hash_value]["file_ids"].add(hf.file_id)
            for d in devices:
                if d.file_id == hf.file_id:
                    hash_only_map[hash_value]["devices"].add(d.id)
            hash_only_map[hash_value]["count"] += 1
        
        multi_device_hash_only = {
            key: data for key, data in hash_only_map.items()
            if len(data["devices"]) >= 2
        }
        
        print(f"   Hash-only correlations in >= 2 devices: {len(multi_device_hash_only)}")
        
        if multi_device_hash_only:
            print(f"\nSample Hash-Only Correlations (first 3):")
            for i, (hash_val, data) in enumerate(list(multi_device_hash_only.items())[:3]):
                hash_display = hash_val[:30] + "..." if len(hash_val) > 30 else hash_val
                print(f"   {i+1}. Hash: {hash_display}")
                print(f"      Devices: {data['devices']}, Files: {data['file_ids']}, Count: {data['count']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analytic_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    check_hashfile_data(analytic_id)

