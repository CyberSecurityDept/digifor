#!/usr/bin/env python3
"""
Migration script to add 'method' field to files table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from sqlalchemy import text

def migrate_add_method_to_files():
    """Add method field to files table"""
    db = SessionLocal()
    try:
        print("Adding 'method' field to files table...")
        
        db.execute(text("ALTER TABLE files ADD COLUMN method VARCHAR"))
        
        db.commit()
        print("✅ Successfully added 'method' field to files table")
        
    except Exception as e:
        print(f"❌ Error adding method field: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_add_method_to_files()
