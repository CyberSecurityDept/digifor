#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_db
from sqlalchemy import text

def migrate_add_sheet_name_to_social_media():
    
    db = next(get_db())
    
    try:
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'social_media' 
            AND column_name = 'sheet_name'
        """))
        
        if result.fetchone():
            print("✅ Column 'sheet_name' already exists in social_media table")
            return
        
        db.execute(text("""
            ALTER TABLE social_media 
            ADD COLUMN sheet_name VARCHAR(255)
        """))
        
        db.commit()
        print("✅ Successfully added 'sheet_name' column to social_media table")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding sheet_name column: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_sheet_name_to_social_media()
