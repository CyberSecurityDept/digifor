#!/usr/bin/env python3
"""
Migration script to add total_data column to files table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_add_total_data_to_files():
    """Add total_data column to files table"""
    
    # Database connection
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'files' 
                AND column_name = 'total_data'
            """))
            
            if result.fetchone():
                print("Column 'total_data' already exists in 'files' table")
                return
            
            # Add total_data column
            conn.execute(text("""
                ALTER TABLE files 
                ADD COLUMN total_data INTEGER
            """))
            
            conn.commit()
            print("✅ Successfully added 'total_data' column to 'files' table")
            
    except Exception as e:
        print(f"❌ Error adding 'total_data' column: {str(e)}")
        raise e

if __name__ == "__main__":
    migrate_add_total_data_to_files()
