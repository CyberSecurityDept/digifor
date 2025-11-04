#!/usr/bin/env python3
"""
Migration script to add file_id column to contacts table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.init_db import SessionLocal
from sqlalchemy import text

def migrate_contacts_add_file_id():
    print("🔄 MIGRATING CONTACTS TABLE - ADDING FILE_ID COLUMN")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'contacts' AND column_name = 'file_id';
        """))
        
        if result.fetchone():
            print("file_id column already exists in contacts table")
            return
        
        print("**STEP 1: Adding file_id column to contacts table**")
        
        db.execute(text("""
            ALTER TABLE contacts 
            ADD COLUMN file_id INTEGER;
        """))
        
        print("Added file_id column to contacts table")
        
        print("**STEP 2: Populating file_id from device relationship**")
        
        db.execute(text("""
            UPDATE contacts 
            SET file_id = devices.file_id 
            FROM devices 
            WHERE contacts.device_id = devices.id;
        """))
        
        print("Populated file_id from device relationship")
        
        print("**STEP 3: Adding foreign key constraint**")
        
        db.execute(text("""
            ALTER TABLE contacts 
            ADD CONSTRAINT fk_contacts_file_id 
            FOREIGN KEY (file_id) REFERENCES files(id);
        """))
        
        print("Added foreign key constraint")
        
        print("**STEP 4: Making file_id NOT NULL**")
        
        db.execute(text("""
            ALTER TABLE contacts 
            ALTER COLUMN file_id SET NOT NULL;
        """))
        
        print("Made file_id NOT NULL")
        
        print("**STEP 5: Adding index for performance**")
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_file_id 
            ON contacts(file_id);
        """))
        
        print("Added index on file_id")
        
        db.commit()
        
        print("\n🎯 **MIGRATION COMPLETED SUCCESSFULLY!**")
        
        print("\n **VERIFICATION:**")
        
        result = db.execute(text("""
            SELECT COUNT(*) as total_contacts,
                   COUNT(file_id) as contacts_with_file_id
            FROM contacts;
        """))
        
        row = result.fetchone()
        print(f"   Total contacts: {row[0]}")
        print(f"   Contacts with file_id: {row[1]}")
        
        result = db.execute(text("""
            SELECT c.id, c.display_name, c.phone_number, f.file_name
            FROM contacts c
            JOIN files f ON c.file_id = f.id
            LIMIT 5;
        """))
        
        print(f"\n📝 **SAMPLE DATA:**")
        for row in result:
            print(f"   Contact {row[0]}: {row[1]} ({row[2]}) - Source: {row[3]}")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_contacts_add_file_id()
