#!/usr/bin/env python3
"""
Migration script to add file_id column to calls table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.init_db import SessionLocal
from sqlalchemy import text

def migrate_calls_add_file_id():
    print("🔄 MIGRATING CALLS TABLE - ADDING FILE_ID COLUMN")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'calls' AND column_name = 'file_id';
        """))
        
        if result.fetchone():
            print("file_id column already exists in calls table")
            return
        
        print("**STEP 1: Adding file_id column to calls table**")
        
        db.execute(text("""
            ALTER TABLE calls 
            ADD COLUMN file_id INTEGER;
        """))
        
        print("Added file_id column to calls table")
        
        print("**STEP 2: Populating file_id from device relationship**")
        
        db.execute(text("""
            UPDATE calls 
            SET file_id = devices.file_id 
            FROM devices 
            WHERE calls.device_id = devices.id;
        """))
        
        print("Populated file_id from device relationship")
        
        print("**STEP 3: Adding foreign key constraint**")
        
        db.execute(text("""
            ALTER TABLE calls 
            ADD CONSTRAINT fk_calls_file_id 
            FOREIGN KEY (file_id) REFERENCES files(id);
        """))
        
        print("Added foreign key constraint")
        
        print("**STEP 4: Making file_id NOT NULL**")
        
        db.execute(text("""
            ALTER TABLE calls 
            ALTER COLUMN file_id SET NOT NULL;
        """))
        
        print("Made file_id NOT NULL")
        
        print("**STEP 5: Adding index for performance**")
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_calls_file_id 
            ON calls(file_id);
        """))
        
        print("Added index on file_id")
        
        db.commit()
        
        print("\n🎯 **MIGRATION COMPLETED SUCCESSFULLY!**")
        
        print("\n **VERIFICATION:**")
        
        result = db.execute(text("""
            SELECT COUNT(*) as total_calls,
                   COUNT(file_id) as calls_with_file_id
            FROM calls;
        """))
        
        row = result.fetchone()
        print(f"   Total calls: {row[0]}")
        print(f"   Calls with file_id: {row[1]}")
        
        result = db.execute(text("""
            SELECT c.id, c.caller, c.receiver, c.duration, f.file_name
            FROM calls c
            JOIN files f ON c.file_id = f.id
            LIMIT 5;
        """))
        
        print(f"\n📝 **SAMPLE DATA:**")
        for row in result:
            print(f"   Call {row[0]}: {row[1]} -> {row[2]} ({row[3]}) - Source: {row[4]}")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_calls_add_file_id()
