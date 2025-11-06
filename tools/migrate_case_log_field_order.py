#!/usr/bin/env python3
"""
Migration script to reorder fields in case_logs table
Move status field to be after notes field
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

<<<<<<< HEAD
# Add the parent directory to the path so we can import from app
=======
>>>>>>> analytics-fix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def migrate_case_log_field_order():
    """Reorder fields in case_logs table to put status after notes"""
    
<<<<<<< HEAD
    # Create database connection
=======
>>>>>>> analytics-fix
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with engine.connect() as connection:
<<<<<<< HEAD
            print("🔄 Reordering case_logs table fields...")
            
            # First, backup existing data
            print("📋 Backing up existing case_logs data...")
=======
            print(" Reordering case_logs table fields...")
            
            print(" Backing up existing case_logs data...")
>>>>>>> analytics-fix
            backup_query = text("""
                CREATE TEMP TABLE case_logs_backup AS 
                SELECT * FROM case_logs
            """)
            connection.execute(backup_query)
            connection.commit()
<<<<<<< HEAD
            print("✅ Data backed up to temporary table")
            
            # Drop the existing table
            print("🗑️ Dropping existing case_logs table...")
            drop_table_query = text("DROP TABLE case_logs CASCADE")
            connection.execute(drop_table_query)
            connection.commit()
            print("✅ Existing table dropped")
            
            # Create the table with correct field order
            print("🏗️ Creating case_logs table with correct field order...")
=======
            print(" Data backed up to temporary table")
            
            print(" Dropping existing case_logs table...")
            drop_table_query = text("DROP TABLE case_logs CASCADE")
            connection.execute(drop_table_query)
            connection.commit()
            print(" Existing table dropped")
            
            print(" Creating case_logs table with correct field order...")
>>>>>>> analytics-fix
            create_table_query = text("""
                CREATE TABLE case_logs (
                    id SERIAL PRIMARY KEY,
                    case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                    action VARCHAR(50) NOT NULL,
                    changed_by VARCHAR(255) NOT NULL,
                    change_detail TEXT,
                    notes TEXT,
                    status casestatus NOT NULL DEFAULT 'Open',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            connection.execute(create_table_query)
            connection.commit()
<<<<<<< HEAD
            print("✅ New table created with correct field order")
            
            # Restore data from backup
            print("📥 Restoring data from backup...")
=======
            print(" New table created with correct field order")
            
            print(" Restoring data from backup...")
>>>>>>> analytics-fix
            restore_query = text("""
                INSERT INTO case_logs (id, case_id, action, changed_by, change_detail, notes, status, created_at)
                SELECT id, case_id, action, changed_by, change_detail, notes, status, created_at
                FROM case_logs_backup
                ORDER BY id
            """)
            connection.execute(restore_query)
            connection.commit()
<<<<<<< HEAD
            print("✅ Data restored from backup")
            
            # Drop backup table
            print("🧹 Cleaning up backup table...")
            drop_backup_query = text("DROP TABLE case_logs_backup")
            connection.execute(drop_backup_query)
            connection.commit()
            print("✅ Backup table cleaned up")
            
            # Verify the new structure
            print("🔍 Verifying new table structure...")
=======
            print(" Data restored from backup")
            
            print(" Cleaning up backup table...")
            drop_backup_query = text("DROP TABLE case_logs_backup")
            connection.execute(drop_backup_query)
            connection.commit()
            print(" Backup table cleaned up")
            
            print(" Verifying new table structure...")
>>>>>>> analytics-fix
            verify_query = text("""
                SELECT column_name, ordinal_position
                FROM information_schema.columns 
                WHERE table_name = 'case_logs' 
                ORDER BY ordinal_position
            """)
            result = connection.execute(verify_query).fetchall()
            
<<<<<<< HEAD
            print("📋 New case_logs table field order:")
            for row in result:
                print(f"  {row[1]}. {row[0]}")
            
            # Check if status is in correct position (should be 7th)
=======
            print(" New case_logs table field order:")
            for row in result:
                print(f"  {row[1]}. {row[0]}")
            
>>>>>>> analytics-fix
            status_position = next((row[1] for row in result if row[0] == 'status'), None)
            notes_position = next((row[1] for row in result if row[0] == 'notes'), None)
            
            if status_position and notes_position and status_position == notes_position + 1:
<<<<<<< HEAD
                print("✅ Status field is correctly positioned after notes field")
            else:
                print(f"❌ Status field position incorrect. Notes: {notes_position}, Status: {status_position}")
                raise Exception("Field order migration failed")
            
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
=======
                print(" Status field is correctly positioned after notes field")
            else:
                print(f" Status field position incorrect. Notes: {notes_position}, Status: {status_position}")
                raise Exception("Field order migration failed")
            
    except Exception as e:
        print(f" Error during migration: {str(e)}")
>>>>>>> analytics-fix
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
<<<<<<< HEAD
    print("🚀 Starting case_logs field order migration...")
    migrate_case_log_field_order()
    print("✅ Migration completed successfully!")
=======
    print(" Starting case_logs field order migration...")
    migrate_case_log_field_order()
    print(" Migration completed successfully!")
>>>>>>> analytics-fix
