#!/usr/bin/env python3
"""
Migration script to rename total_data column to amount_of_data in files table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_rename_total_data_to_amount_of_data():
    """Rename total_data column to amount_of_data in files table"""
    
    # Database connection
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if total_data column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'files' 
                AND column_name = 'total_data'
            """))
            
            if not result.fetchone():
                print("Column 'total_data' does not exist in 'files' table")
                return
            
            # Check if amount_of_data column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'files' 
                AND column_name = 'amount_of_data'
            """))
            
            if result.fetchone():
                print("Column 'amount_of_data' already exists in 'files' table")
                return
            
            # Rename total_data to amount_of_data
            conn.execute(text("""
                ALTER TABLE files 
                RENAME COLUMN total_data TO amount_of_data
            """))
            
            conn.commit()
            print("✅ Successfully renamed 'total_data' column to 'amount_of_data' in 'files' table")
            
    except Exception as e:
        print(f"❌ Error renaming column: {str(e)}")
        raise e

if __name__ == "__main__":
    migrate_rename_total_data_to_amount_of_data()
