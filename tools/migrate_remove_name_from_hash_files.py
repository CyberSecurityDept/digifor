"""
Migration script to remove 'name' column from hash_files table.
This script should be run after updating the model to remove the name field.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def remove_name_column_from_hash_files():
    """Remove the 'name' column from hash_files table."""
    print("Starting migration: Remove 'name' column from hash_files table")
    
    # Create database connection
    database_url = settings.DATABASE_URL
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if column exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'hash_files' 
                AND column_name = 'name'
            """)
            result = conn.execute(check_query)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                print("Column 'name' does not exist in hash_files table. Migration not needed.")
                return
            
            print("⚠️ Column 'name' found. Removing it...")
            
            # Remove the column
            alter_query = text("""
                ALTER TABLE hash_files 
                DROP COLUMN IF EXISTS name
            """)
            conn.execute(alter_query)
            conn.commit()
            
            print("Successfully removed 'name' column from hash_files table")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    remove_name_column_from_hash_files()

