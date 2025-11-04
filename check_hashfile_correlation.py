#!/usr/bin/env python3
"""
Script to check hashfile correlation data in database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.analytics.shared.models import Analytic, AnalyticDevice, Device
from app.analytics.device_management.models import HashFile
from sqlalchemy import or_
from collections import defaultdict

def check_hashfile_correlation(analytic_id: int = 1):
    db = SessionLocal()
    
    try:
        print(f"🔍 Checking hashfile correlation for analytic_id={analytic_id}\n")
        
        # 1. Check analytic
        analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic:
            print(f"❌ Analytic {analytic_id} not found!")
            return
        print(f"✅ Analytic found: {analytic.analytic_name} ({analytic.method})\n")
        
        # 2. Get devices
        device_links = db.query(AnalyticDevice).filter(
            AnalyticDevice.analytic_id == analytic_id
        ).all()
        
        device_ids = list({d for link in device_links for d in link.device_ids})
        if not device_ids:
            print("❌ No devices linked to this analytic")
            return
        
        print(f"📱 Device IDs: {device_ids}")
        
        devices = db.query(Device).filter(Device.id.in_(device_ids)).all()
        print(f"✅ Found {len(devices)} devices:")
        for i, d in enumerate(devices):
            print(f"   - Device {d.id}: {d.owner_name} ({d.phone_number}) - file_id={d.file_id}")
        
        file_ids = [d.file_id for d in devices]
        file_to_device = {d.file_id: d.id for d in devices}
        print(f"\n📁 File IDs: {file_ids}\n")
        
        # 3. Get hashfiles
        hashfiles = (
            db.query(
                HashFile.file_id,
                HashFile.file_name,
                HashFile.md5_hash,
                HashFile.sha1_hash,
            )
            .filter(HashFile.file_id.in_(file_ids))
            .filter(or_(HashFile.md5_hash != None, HashFile.sha1_hash != None))
            .all()
        )
        
        print(f"📊 Total hashfiles with hash: {len(hashfiles)}")
        
        if not hashfiles:
            print("\n❌ No hashfiles found with hash values!")
            return
        
        # 4. Show sample data
        print(f"\n📋 Sample hashfiles (first 10):")
        for i, hf in enumerate(hashfiles[:10]):
            hash_val = hf.md5_hash or hf.sha1_hash
            print(f"   {i+1}. file_id={hf.file_id}, file_name='{hf.file_name}', hash='{hash_val[:20] if hash_val else None}...'")
        
        # 5. Check correlation logic
        print(f"\n🔗 Checking correlation logic...")
        
        correlation_map = defaultdict(lambda: {"records": [], "devices": set()})
        
        for hf in hashfiles:
            hash_value = hf.md5_hash or hf.sha1_hash
            if not hash_value or not hf.file_name:
                continue
            
            key = f"{hash_value}::{hf.file_name.strip().lower()}"
            device_id = file_to_device.get(hf.file_id)
            if not device_id:
                continue
            
            correlation_map[key]["records"].append(hf)
            correlation_map[key]["devices"].add(device_id)
        
        print(f"📊 Unique correlation keys: {len(correlation_map)}")
        
        # 6. Filter by min_devices = 2
        min_devices = 2
        correlated = {
            key: data for key, data in correlation_map.items()
            if len(data["devices"]) >= min_devices
        }
        
        print(f"✅ Correlations found (appears in >= {min_devices} devices): {len(correlated)}\n")
        
        if correlated:
            print("🎯 Correlation results:")
            for i, (key, info) in enumerate(list(correlated.items())[:10]):
                hash_part = key.split("::")[0]
                name_part = key.split("::")[1] if "::" in key else ""
                print(f"   {i+1}. Hash: {hash_part[:20]}..., File: {name_part}")
                print(f"      Devices: {sorted(info['devices'])} ({len(info['devices'])} devices)")
                print(f"      Records: {len(info['records'])} hashfiles")
        else:
            print("❌ No correlations found!")
            print("\n📊 Analysis of why no correlations:")
            
            # Check by hash only
            hash_only_map = defaultdict(lambda: {"devices": set()})
            for hf in hashfiles:
                hash_value = hf.md5_hash or hf.sha1_hash
                if not hash_value:
                    continue
                device_id = file_to_device.get(hf.file_id)
                if device_id:
                    hash_only_map[hash_value]["devices"].add(device_id)
            
            hash_correlations = {
                key: data for key, data in hash_only_map.items()
                if len(data["devices"]) >= min_devices
            }
            
            print(f"   - Correlations by hash only: {len(hash_correlations)}")
            
            # Check by file_name only
            name_only_map = defaultdict(lambda: {"devices": set()})
            for hf in hashfiles:
                if not hf.file_name:
                    continue
                device_id = file_to_device.get(hf.file_id)
                if device_id:
                    name_key = hf.file_name.strip().lower()
                    name_only_map[name_key]["devices"].add(device_id)
            
            name_correlations = {
                key: data for key, data in name_only_map.items()
                if len(data["devices"]) >= min_devices
            }
            
            print(f"   - Correlations by file_name only: {len(name_correlations)}")
            
            # Show statistics
            print(f"\n📈 Statistics:")
            print(f"   - Hashfiles with hash: {len(hashfiles)}")
            print(f"   - Hashfiles with file_name: {sum(1 for hf in hashfiles if hf.file_name)}")
            print(f"   - Hashfiles with both hash and file_name: {sum(1 for hf in hashfiles if (hf.md5_hash or hf.sha1_hash) and hf.file_name)}")
            print(f"   - Unique hashes: {len(hash_only_map)}")
            print(f"   - Unique file_names: {len(name_only_map)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    analytic_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    check_hashfile_correlation(analytic_id)

