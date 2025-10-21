#!/usr/bin/env python3
"""
Migration script to update case_logs status field to use Enum
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def migrate_case_log_status_enum():
    """Update status column in case_logs table to use Enum"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with engine.connect() as connection:
            print(" Updating case_logs status column to use Enum...")
            
            # First, update existing NULL values to 'Open' (default)
            update_null_status_query = text("""
                UPDATE case_logs 
                SET status = 'Open' 
                WHERE status IS NULL
            """)
            
            result = connection.execute(update_null_status_query)
            connection.commit()
            print(f" Updated {result.rowcount} NULL status records to 'Open'")
            
            # Create the enum type if it doesn't exist
            create_enum_query = text("""
                DO $$ BEGIN
                    CREATE TYPE casestatus AS ENUM ('Open', 'Closed', 'Re-open');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            connection.execute(create_enum_query)
            connection.commit()
            print(" Created casestatus enum type")
            
            # First, drop the default value
            drop_default_query = text("""
                ALTER TABLE case_logs 
                ALTER COLUMN status DROP DEFAULT
            """)
            
            connection.execute(drop_default_query)
            connection.commit()
            print(" Dropped default value from status column")
            
            # Alter the column to use the enum type
            alter_column_query = text("""
                ALTER TABLE case_logs 
                ALTER COLUMN status TYPE casestatus 
                USING status::casestatus
            """)
            
            connection.execute(alter_column_query)
            connection.commit()
            print(" Updated status column to use casestatus enum")
            
            # Set default value
            set_default_query = text("""
                ALTER TABLE case_logs 
                ALTER COLUMN status SET DEFAULT 'Open'
            """)
            
            connection.execute(set_default_query)
            connection.commit()
            print(" Set default value for status column")
            
            # Make column NOT NULL
            set_not_null_query = text("""
                ALTER TABLE case_logs 
                ALTER COLUMN status SET NOT NULL
            """)
            
            connection.execute(set_not_null_query)
            connection.commit()
            print(" Set status column to NOT NULL")
            
    except Exception as e:
        print(f" Error during migration: {str(e)}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    print(" Starting case_logs status enum migration...")
    migrate_case_log_status_enum()
    print(" Migration completed successfully!")
