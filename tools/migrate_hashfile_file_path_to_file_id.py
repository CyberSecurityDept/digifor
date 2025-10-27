#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker

def migrate_hashfile_file_path_to_file_id():
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("Starting migration: Replace file_path with file_id in hash_files table")
        
        # Step 1: Add new file_id column
        print("Step 1: Adding file_id column...")
        session.execute(text("""
            ALTER TABLE hash_files 
            ADD COLUMN file_id INTEGER;
        """))
        session.commit()
        print("✓ Added file_id column")
        
        # Step 2: Update file_id based on file_path
        print("Step 2: Updating file_id based on file_path...")
        session.execute(text("""
            UPDATE hash_files 
            SET file_id = (
                SELECT f.id 
                FROM files f 
                WHERE f.file_name = (
                    SELECT SUBSTRING(hf.file_path FROM '[^/]+$')
                    FROM hash_files hf 
                    WHERE hf.id = hash_files.id
                )
                LIMIT 1
            )
            WHERE file_id IS NULL;
        """))
        session.commit()
        print("✓ Updated file_id based on file_path")
        
        # Step 3: Add foreign key constraint
        print("Step 3: Adding foreign key constraint...")
        session.execute(text("""
            ALTER TABLE hash_files 
            ADD CONSTRAINT fk_hash_files_file_id 
            FOREIGN KEY (file_id) REFERENCES files(id);
        """))
        session.commit()
        print("✓ Added foreign key constraint")
        
        # Step 4: Make file_id NOT NULL
        print("Step 4: Making file_id NOT NULL...")
        session.execute(text("""
            ALTER TABLE hash_files 
            ALTER COLUMN file_id SET NOT NULL;
        """))
        session.commit()
        print("✓ Made file_id NOT NULL")
        
        # Step 5: Drop file_path column
        print("Step 5: Dropping file_path column...")
        session.execute(text("""
            ALTER TABLE hash_files 
            DROP COLUMN file_path;
        """))
        session.commit()
        print("✓ Dropped file_path column")
        
        print("\n🎉 Migration completed successfully!")
        print("hash_files table now uses file_id instead of file_path")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_hashfile_file_path_to_file_id()
