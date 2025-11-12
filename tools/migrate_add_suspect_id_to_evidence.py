#!/usr/bin/env python3
"""
Migration script to:
1. Add suspect_id column to evidence table
2. Remove evidence_summary column from suspects table
3. Update existing evidence records to link to suspects based on evidence_id
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    """Run migration"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Start transaction
            trans = conn.begin()
            
            print("🔄 Starting migration...")
            
            # Step 1: Add suspect_id column to evidence table (if not exists)
            print("📝 Step 1: Adding suspect_id column to evidence table...")
            conn.execute(text("""
                ALTER TABLE evidence 
                ADD COLUMN IF NOT EXISTS suspect_id INTEGER 
                REFERENCES suspects(id) ON DELETE SET NULL;
            """))
            print("✅ suspect_id column added to evidence table")
            
            # Step 2: Update existing evidence records to link to suspects
            # based on evidence_number matching suspects.evidence_id
            print("📝 Step 2: Updating existing evidence records to link to suspects...")
            conn.execute(text("""
                UPDATE evidence e
                SET suspect_id = s.id
                FROM suspects s
                WHERE e.evidence_number = s.evidence_id
                AND e.case_id = s.case_id
                AND e.suspect_id IS NULL;
            """))
            print("✅ Existing evidence records linked to suspects")
            
            # Step 3: Remove evidence_summary column from suspects table
            print("📝 Step 3: Removing evidence_summary column from suspects table...")
            conn.execute(text("""
                ALTER TABLE suspects 
                DROP COLUMN IF EXISTS evidence_summary;
            """))
            print("✅ evidence_summary column removed from suspects table")
            
            # Commit transaction
            trans.commit()
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate()

