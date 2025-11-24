import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def remove_name_column_from_hash_files():
    print("Starting migration: Remove 'name' column from hash_files table")
    
    database_url = settings.DATABASE_URL
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
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
            
            print("Column 'name' found. Removing it...")
            
            alter_query = text("""
                ALTER TABLE hash_files 
                DROP COLUMN IF EXISTS name
            """)
            conn.execute(alter_query)
            conn.commit()
            
            print("Successfully removed 'name' column from hash_files table")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    remove_name_column_from_hash_files()

