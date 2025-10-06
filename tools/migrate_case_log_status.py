#!/usr/bin/env python3
"""
Migration script to add status field to case_logs table
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def migrate_case_log_status():
    """Add status column to case_logs table"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with engine.connect() as connection:
            # Check if status column already exists
            check_column_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'case_logs' 
                AND column_name = 'status'
            """)
            
            result = connection.execute(check_column_query).fetchone()
            
            if result:
                print("✅ Status column already exists in case_logs table")
                return
            
            print("🔄 Adding status column to case_logs table...")
            
            # Add status column
            add_column_query = text("""
                ALTER TABLE case_logs 
                ADD COLUMN status VARCHAR(20) DEFAULT NULL
            """)
            
            connection.execute(add_column_query)
            connection.commit()
            
            print("✅ Successfully added status column to case_logs table")
            
            # Update existing records with case status
            print("🔄 Updating existing case logs with case status...")
            
            update_status_query = text("""
                UPDATE case_logs 
                SET status = (
                    SELECT c.status 
                    FROM cases c 
                    WHERE c.id = case_logs.case_id
                )
                WHERE status IS NULL
            """)
            
            result = connection.execute(update_status_query)
            connection.commit()
            
            print(f"✅ Updated {result.rowcount} existing case log records with case status")
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("🚀 Starting case_logs status migration...")
    migrate_case_log_status()
    print("✅ Migration completed successfully!")
