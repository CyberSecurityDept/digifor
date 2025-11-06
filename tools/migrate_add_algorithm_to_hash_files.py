import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate_add_algorithm_to_hash_files():
    print("Starting migration: Add 'algorithm' column to hash_files table")
    db = SessionLocal()
    try:
        # Check if the 'algorithm' column exists before attempting to add it
        with db.connection() as connection:
            # Check if column exists
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'hash_files' AND column_name = 'algorithm'
            """))
            
            if result.fetchone():
                print("Column 'algorithm' already exists in 'hash_files' table. No action needed.")
            else:
                print("Column 'algorithm' not found. Adding it...")
                connection.execute(text("""
                    ALTER TABLE hash_files 
                    ADD COLUMN algorithm VARCHAR
                """))
                connection.commit()
                print("Column 'algorithm' successfully added to 'hash_files' table.")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        db.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate_add_algorithm_to_hash_files()

