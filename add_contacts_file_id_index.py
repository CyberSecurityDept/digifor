#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.init_db import SessionLocal
from sqlalchemy import text

def add_contacts_file_id_index():
    print("🔧 ADDING INDEX ON CONTACTS.FILE_ID")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        # Check if index already exists
        result = db.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'contacts' 
            AND indexname = 'idx_contacts_file_id';
        """))
        
        if result.fetchone():
            print("✅ Index idx_contacts_file_id already exists")
            return
        
        print("📋 **ADDING INDEX ON FILE_ID FOR PERFORMANCE**")
        
        # Add index on file_id
        db.execute(text("""
            CREATE INDEX idx_contacts_file_id 
            ON contacts(file_id);
        """))
        
        print("✅ Added index idx_contacts_file_id on contacts.file_id")
        
        # Commit changes
        db.commit()
        
        # Verify the index was created
        result = db.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes 
            WHERE tablename = 'contacts' 
            AND indexname = 'idx_contacts_file_id';
        """))
        
        row = result.fetchone()
        if row:
            print(f"✅ Index created successfully: {row[1]}")
        else:
            print("❌ Index creation failed")
        
        # Show all indexes on contacts table
        print(f"\n📊 **ALL INDEXES ON CONTACTS TABLE:**")
        result = db.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes 
            WHERE tablename = 'contacts'
            ORDER BY indexname;
        """))
        
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Index creation failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_contacts_file_id_index()
