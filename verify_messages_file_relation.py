#!/usr/bin/env python3
"""
Script untuk verifikasi relasi messages dengan file
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.init_db import SessionLocal
from sqlalchemy import text

def verify_messages_file_relation():
    print("🔍 VERIFYING MESSAGES-FILE RELATION")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        # Check total messages and files
        result = db.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM messages) as total_messages,
                (SELECT COUNT(*) FROM files) as total_files,
                (SELECT COUNT(*) FROM devices) as total_devices;
        """))
        
        row = result.fetchone()
        print(f"📊 **DATABASE STATISTICS:**")
        print(f"   Total messages: {row[0]}")
        print(f"   Total files: {row[1]}")
        print(f"   Total devices: {row[2]}")
        
        # Check messages with file information
        print(f"\n📋 **MESSAGES BY FILE SOURCE:**")
        result = db.execute(text("""
            SELECT 
                f.file_name,
                f.tools,
                COUNT(m.id) as message_count
            FROM files f
            LEFT JOIN messages m ON f.id = m.file_id
            GROUP BY f.id, f.file_name, f.tools
            ORDER BY message_count DESC;
        """))
        
        for row in result:
            print(f"   📁 {row[0]} ({row[1]}) - {row[2]} messages")
        
        # Show sample messages with full file information
        print(f"\n📝 **SAMPLE MESSAGES WITH FILE INFO:**")
        result = db.execute(text("""
            SELECT 
                m.id,
                m.sender,
                m.receiver,
                m.text,
                m.type,
                f.file_name,
                f.tools,
                d.owner_name
            FROM messages m
            JOIN files f ON m.file_id = f.id
            JOIN devices d ON m.device_id = d.id
            WHERE m.text IS NOT NULL AND m.text != 'None'
            ORDER BY m.id
            LIMIT 10;
        """))
        
        for row in result:
            text_preview = row[3][:60] + "..." if row[3] and len(row[3]) > 60 else row[3]
            print(f"   Message {row[0]}: {row[1]} -> {row[2]}")
            print(f"      Type: {row[4]} - Text: '{text_preview}'")
            print(f"      📁 Source: {row[5]} ({row[6]}) - Device: {row[7]}")
        
        # Check for any orphaned messages (messages without valid file_id)
        print(f"\n🔍 **CHECKING FOR ORPHANED MESSAGES:**")
        result = db.execute(text("""
            SELECT COUNT(*) as orphaned_messages
            FROM messages m
            LEFT JOIN files f ON m.file_id = f.id
            WHERE f.id IS NULL;
        """))
        
        row = result.fetchone()
        orphaned_count = row[0]
        
        if orphaned_count == 0:
            print("✅ No orphaned messages found - all messages have valid file_id")
        else:
            print(f"⚠️ Found {orphaned_count} orphaned messages without valid file_id")
        
        # Check for any orphaned messages (messages without valid device_id)
        result = db.execute(text("""
            SELECT COUNT(*) as orphaned_messages
            FROM messages m
            LEFT JOIN devices d ON m.device_id = d.id
            WHERE d.id IS NULL;
        """))
        
        row = result.fetchone()
        orphaned_device_count = row[0]
        
        if orphaned_device_count == 0:
            print("✅ No orphaned messages found - all messages have valid device_id")
        else:
            print(f"⚠️ Found {orphaned_device_count} orphaned messages without valid device_id")
        
        # Show message distribution by file
        print(f"\n📊 **MESSAGE DISTRIBUTION BY FILE:**")
        result = db.execute(text("""
            SELECT 
                f.file_name,
                f.tools,
                COUNT(m.id) as message_count,
                COUNT(DISTINCT m.sender) as unique_senders,
                COUNT(DISTINCT m.receiver) as unique_receivers
            FROM files f
            LEFT JOIN messages m ON f.id = m.file_id
            GROUP BY f.id, f.file_name, f.tools
            HAVING COUNT(m.id) > 0
            ORDER BY message_count DESC;
        """))
        
        for row in result:
            print(f"   📁 {row[0]} ({row[1]}):")
            print(f"      Total messages: {row[2]}")
            print(f"      Unique senders: {row[3]}")
            print(f"      Unique receivers: {row[4]}")
        
        # Show message types distribution
        print(f"\n📊 **MESSAGE TYPES DISTRIBUTION:**")
        result = db.execute(text("""
            SELECT 
                m.type,
                COUNT(*) as count
            FROM messages m
            WHERE m.type IS NOT NULL
            GROUP BY m.type
            ORDER BY count DESC;
        """))
        
        for row in result:
            print(f"   {row[0]}: {row[1]} messages")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_messages_file_relation()
