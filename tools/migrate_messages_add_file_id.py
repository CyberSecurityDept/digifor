#!/usr/bin/env python3
"""
Migration script to add file_id column to messages table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.init_db import SessionLocal
from sqlalchemy import text

def migrate_messages_add_file_id():
    print("🔄 MIGRATING MESSAGES TABLE - ADDING FILE_ID COLUMN")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Check if file_id column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'messages' AND column_name = 'file_id';
        """))
        
        if result.fetchone():
            print("✅ file_id column already exists in messages table")
            return
        
        print("📋 **STEP 1: Adding file_id column to messages table**")
        
        # Add file_id column
        db.execute(text("""
            ALTER TABLE messages 
            ADD COLUMN file_id INTEGER;
        """))
        
        print("✅ Added file_id column to messages table")
        
        print("📋 **STEP 2: Populating file_id from device relationship**")
        
        # Update file_id based on device relationship
        db.execute(text("""
            UPDATE messages 
            SET file_id = devices.file_id 
            FROM devices 
            WHERE messages.device_id = devices.id;
        """))
        
        print("✅ Populated file_id from device relationship")
        
        print("📋 **STEP 3: Adding foreign key constraint**")
        
        # Add foreign key constraint
        db.execute(text("""
            ALTER TABLE messages 
            ADD CONSTRAINT fk_messages_file_id 
            FOREIGN KEY (file_id) REFERENCES files(id);
        """))
        
        print("✅ Added foreign key constraint")
        
        print("📋 **STEP 4: Making file_id NOT NULL**")
        
        # Make file_id NOT NULL
        db.execute(text("""
            ALTER TABLE messages 
            ALTER COLUMN file_id SET NOT NULL;
        """))
        
        print("✅ Made file_id NOT NULL")
        
        print("📋 **STEP 5: Adding index for performance**")
        
        # Add index for performance
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_messages_file_id 
            ON messages(file_id);
        """))
        
        print("✅ Added index on file_id")
        
        # Commit all changes
        db.commit()
        
        print("\n🎯 **MIGRATION COMPLETED SUCCESSFULLY!**")
        
        # Verify the migration
        print("\n📊 **VERIFICATION:**")
        
        # Check messages with file_id
        result = db.execute(text("""
            SELECT COUNT(*) as total_messages,
                   COUNT(file_id) as messages_with_file_id
            FROM messages;
        """))
        
        row = result.fetchone()
        print(f"   Total messages: {row[0]}")
        print(f"   Messages with file_id: {row[1]}")
        
        # Check sample data
        result = db.execute(text("""
            SELECT m.id, m.sender, m.receiver, m.text, f.file_name
            FROM messages m
            JOIN files f ON m.file_id = f.id
            LIMIT 5;
        """))
        
        print(f"\n📝 **SAMPLE DATA:**")
        for row in result:
            text_preview = row[3][:50] + "..." if row[3] and len(row[3]) > 50 else row[3]
            print(f"   Message {row[0]}: {row[1]} -> {row[2]} - '{text_preview}' - Source: {row[4]}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_messages_add_file_id()
