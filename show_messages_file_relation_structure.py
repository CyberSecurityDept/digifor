#!/usr/bin/env python3
"""
Script untuk menampilkan struktur relasi messages dengan file
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.init_db import SessionLocal
from sqlalchemy import text

def show_messages_file_relation_structure():
    print("🔍 MESSAGES-FILE RELATION STRUCTURE")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        # Show messages table structure
        print("📋 **MESSAGES TABLE STRUCTURE:**")
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'messages' 
            ORDER BY ordinal_position;
        """))
        
        for row in result:
            nullable = "NULL" if row[2] == "YES" else "NOT NULL"
            default = f" DEFAULT {row[3]}" if row[3] else ""
            print(f"   {row[0]}: {row[1]} {nullable}{default}")
        
        # Show foreign key constraints
        print(f"\n🔗 **FOREIGN KEY CONSTRAINTS:**")
        result = db.execute(text("""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = 'messages'
            ORDER BY tc.constraint_name;
        """))
        
        for row in result:
            print(f"   {row[1]}.{row[2]} -> {row[3]}.{row[4]} ({row[0]})")
        
        # Show indexes
        print(f"\n📊 **INDEXES ON MESSAGES TABLE:**")
        result = db.execute(text("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = 'messages'
            ORDER BY indexname;
        """))
        
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        # Show relationship summary
        print(f"\n🔗 **RELATIONSHIP SUMMARY:**")
        print("   messages.device_id -> devices.id")
        print("   messages.file_id -> files.id")
        print("   devices.file_id -> files.id")
        print("")
        print("   This means:")
        print("   • Each message belongs to a device")
        print("   • Each message also directly references the source file")
        print("   • Each device belongs to a file")
        print("   • So: message -> device -> file AND message -> file (direct)")
        
        # Show sample query to get message with file info
        print(f"\n📝 **SAMPLE QUERY TO GET MESSAGE WITH FILE INFO:**")
        print("""
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
        WHERE m.type = 'iMessage'
        LIMIT 10;
        """)
        
        # Show sample query to get messages by file
        print(f"\n📝 **SAMPLE QUERY TO GET MESSAGES BY FILE:**")
        print("""
        SELECT 
            f.file_name,
            COUNT(m.id) as message_count,
            COUNT(DISTINCT m.sender) as unique_senders
        FROM files f
        LEFT JOIN messages m ON f.id = m.file_id
        GROUP BY f.id, f.file_name
        ORDER BY message_count DESC;
        """)
        
    finally:
        db.close()

if __name__ == "__main__":
    show_messages_file_relation_structure()
