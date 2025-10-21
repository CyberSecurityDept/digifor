#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.init_db import SessionLocal
from sqlalchemy import text

def verify_contacts_file_relation():
    print("🔍 VERIFYING CONTACTS-FILE RELATION")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        # Check total contacts and files
        result = db.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM contacts) as total_contacts,
                (SELECT COUNT(*) FROM files) as total_files,
                (SELECT COUNT(*) FROM devices) as total_devices;
        """))
        
        row = result.fetchone()
        print(f"📊 **DATABASE STATISTICS:**")
        print(f"   Total contacts: {row[0]}")
        print(f"   Total files: {row[1]}")
        print(f"   Total devices: {row[2]}")
        
        # Check contacts with file information
        print(f"\n📋 **CONTACTS BY FILE SOURCE:**")
        result = db.execute(text("""
            SELECT 
                f.file_name,
                f.tools,
                COUNT(c.id) as contact_count
            FROM files f
            LEFT JOIN contacts c ON f.id = c.file_id
            GROUP BY f.id, f.file_name, f.tools
            ORDER BY contact_count DESC;
        """))
        
        for row in result:
            print(f"   📁 {row[0]} ({row[1]}) - {row[2]} contacts")
        
        # Show sample contacts with full file information
        print(f"\n📝 **SAMPLE CONTACTS WITH FILE INFO:**")
        result = db.execute(text("""
            SELECT 
                c.id,
                c.display_name,
                c.phone_number,
                c.type,
                f.file_name,
                f.tools,
                d.owner_name
            FROM contacts c
            JOIN files f ON c.file_id = f.id
            JOIN devices d ON c.device_id = d.id
            ORDER BY c.id
            LIMIT 10;
        """))
        
        for row in result:
            print(f"   Contact {row[0]}: {row[1]} ({row[2]}) - Type: {row[3]}")
            print(f"      📁 Source: {row[4]} ({row[5]}) - Device: {row[6]}")
        
        # Check for any orphaned contacts (contacts without valid file_id)
        print(f"\n🔍 **CHECKING FOR ORPHANED CONTACTS:**")
        result = db.execute(text("""
            SELECT COUNT(*) as orphaned_contacts
            FROM contacts c
            LEFT JOIN files f ON c.file_id = f.id
            WHERE f.id IS NULL;
        """))
        
        row = result.fetchone()
        orphaned_count = row[0]
        
        if orphaned_count == 0:
            print("✅ No orphaned contacts found - all contacts have valid file_id")
        else:
            print(f"⚠️ Found {orphaned_count} orphaned contacts without valid file_id")
        
        # Check for any orphaned contacts (contacts without valid device_id)
        result = db.execute(text("""
            SELECT COUNT(*) as orphaned_contacts
            FROM contacts c
            LEFT JOIN devices d ON c.device_id = d.id
            WHERE d.id IS NULL;
        """))
        
        row = result.fetchone()
        orphaned_device_count = row[0]
        
        if orphaned_device_count == 0:
            print("✅ No orphaned contacts found - all contacts have valid device_id")
        else:
            print(f"⚠️ Found {orphaned_device_count} orphaned contacts without valid device_id")
        
        # Show contact distribution by file
        print(f"\n📊 **CONTACT DISTRIBUTION BY FILE:**")
        result = db.execute(text("""
            SELECT 
                f.file_name,
                f.tools,
                COUNT(c.id) as contact_count,
                COUNT(DISTINCT c.phone_number) as unique_phones,
                COUNT(DISTINCT c.display_name) as unique_names
            FROM files f
            LEFT JOIN contacts c ON f.id = c.file_id
            GROUP BY f.id, f.file_name, f.tools
            HAVING COUNT(c.id) > 0
            ORDER BY contact_count DESC;
        """))
        
        for row in result:
            print(f"   📁 {row[0]} ({row[1]}):")
            print(f"      Total contacts: {row[2]}")
            print(f"      Unique phone numbers: {row[3]}")
            print(f"      Unique display names: {row[4]}")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_contacts_file_relation()
