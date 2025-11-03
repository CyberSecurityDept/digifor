#!/usr/bin/env python3
"""
Migration script untuk menambahkan field baru ke table social_media
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_db

def migrate_social_media_fields():
    """Menambahkan field baru ke table social_media"""
    db = next(get_db())
    
    try:
        new_fields = [
            ("user_id", "VARCHAR"),
            ("full_name", "TEXT"),
            ("friends", "INTEGER"),
            ("statuses", "INTEGER"),
            ("phone_number", "VARCHAR"),
            ("email", "VARCHAR"),
            ("biography", "TEXT"),
            ("profile_picture_url", "TEXT"),
            ("is_private", "BOOLEAN"),
            ("is_local_user", "BOOLEAN"),
            ("chat_content", "TEXT"),
            ("last_message", "TEXT"),
            ("last_seen", "TIMESTAMP"),
            ("other_info", "TEXT"),
            ("source_tool", "VARCHAR"),
        ]
        
        print("=== MIGRATING SOCIAL_MEDIA TABLE ===")
        print()
        
        for field_name, field_type in new_fields:
            try:
                check_query = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'social_media' 
                    AND column_name = '{field_name}'
                """)
                
                result = db.execute(check_query).fetchone()
                
                if result:
                    print(f"✅ Column '{field_name}' already exists")
                else:
                    alter_query = text(f"ALTER TABLE social_media ADD COLUMN {field_name} {field_type}")
                    db.execute(alter_query)
                    db.commit()
                    print(f"✅ Added column '{field_name}' ({field_type})")
                    
            except Exception as e:
                print(f"❌ Error adding column '{field_name}': {e}")
                db.rollback()
        
        print()
        print("=== MIGRATION COMPLETED ===")
        
        print("\n=== CURRENT TABLE STRUCTURE ===")
        structure_query = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'social_media'
            ORDER BY ordinal_position
        """)
        
        result = db.execute(structure_query).fetchall()
        for row in result:
            print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_social_media_fields()
