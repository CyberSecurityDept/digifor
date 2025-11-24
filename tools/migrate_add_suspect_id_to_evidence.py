#!/usr/bin/env python3
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            trans = conn.begin()
            
            print("Starting migration...")
            print("Step 1: Adding suspect_id column to evidence table...")
            conn.execute(text("""
                ALTER TABLE evidence 
                ADD COLUMN IF NOT EXISTS suspect_id INTEGER 
                REFERENCES suspects(id) ON DELETE SET NULL;
            """))
            print("suspect_id column added to evidence table")
            
            print("Step 2: Updating existing evidence records to link to suspects...")
            conn.execute(text("""
                UPDATE evidence e
                SET suspect_id = s.id
                FROM suspects s
                WHERE e.evidence_number = s.evidence_id
                AND e.case_id = s.case_id
                AND e.suspect_id IS NULL;
            """))
            print("Existing evidence records linked to suspects")
            
            print("Step 3: Removing evidence_summary column from suspects table...")
            conn.execute(text("""
                ALTER TABLE suspects 
                DROP COLUMN IF EXISTS evidence_summary;
            """))
            print("evidence_summary column removed from suspects table")
            
            trans.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate()

