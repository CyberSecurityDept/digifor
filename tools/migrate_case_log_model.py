#!/usr/bin/env python3
"""
Migration script to update CaseLog model with new fields:
- change_detail (replaces description)
- notes (new field)
- CASCADE delete constraint
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def migrate_case_log_model():
    """Migrate CaseLog model to new structure"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with engine.connect() as connection:
            print("🔄 Starting CaseLog model migration...")
            
            # Check if case_logs table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'case_logs'
                );
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ case_logs table does not exist. Please run initial database setup first.")
                return False
            
            # Check current table structure
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'case_logs'
                ORDER BY ordinal_position;
            """))
            
            columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in result}
            print(f"📋 Current table structure: {list(columns.keys())}")
            
            # Add new columns if they don't exist
            if 'change_detail' not in columns:
                print("➕ Adding change_detail column...")
                connection.execute(text("""
                    ALTER TABLE case_logs 
                    ADD COLUMN change_detail TEXT;
                """))
                print("✅ change_detail column added")
            else:
                print("ℹ️  change_detail column already exists")
            
            if 'notes' not in columns:
                print("➕ Adding notes column...")
                connection.execute(text("""
                    ALTER TABLE case_logs 
                    ADD COLUMN notes TEXT;
                """))
                print("✅ notes column added")
            else:
                print("ℹ️  notes column already exists")
            
            # Migrate data from description to change_detail if description exists
            if 'description' in columns and 'change_detail' in columns:
                print("🔄 Migrating data from description to change_detail...")
                connection.execute(text("""
                    UPDATE case_logs 
                    SET change_detail = description 
                    WHERE change_detail IS NULL AND description IS NOT NULL;
                """))
                print("✅ Data migration completed")
            
            # Update foreign key constraint to add CASCADE delete
            print("🔗 Updating foreign key constraint...")
            try:
                # Drop existing foreign key constraint
                connection.execute(text("""
                    ALTER TABLE case_logs 
                    DROP CONSTRAINT IF EXISTS case_logs_case_id_fkey;
                """))
                
                # Add new foreign key constraint with CASCADE
                connection.execute(text("""
                    ALTER TABLE case_logs 
                    ADD CONSTRAINT case_logs_case_id_fkey 
                    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE;
                """))
                print("✅ Foreign key constraint updated with CASCADE delete")
            except Exception as e:
                print(f"⚠️  Warning: Could not update foreign key constraint: {e}")
            
            # Update created_at column to use timezone if needed
            print("🕐 Checking created_at column...")
            result = connection.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'case_logs' AND column_name = 'created_at';
            """))
            
            current_type = result.scalar()
            if current_type and 'timestamp' in current_type.lower() and 'timezone' not in current_type.lower():
                print("🔄 Updating created_at column to use timezone...")
                try:
                    connection.execute(text("""
                        ALTER TABLE case_logs 
                        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;
                    """))
                    print("✅ created_at column updated to use timezone")
                except Exception as e:
                    print(f"⚠️  Warning: Could not update created_at column: {e}")
            else:
                print("ℹ️  created_at column already has timezone support")
            
            connection.commit()
            print("🎉 CaseLog model migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_case_log_model()
    if success:
        print("\n✅ Migration completed successfully!")
        print("📝 New CaseLog model structure:")
        print("   - action: String(50), not null")
        print("   - changed_by: String(255), not null") 
        print("   - change_detail: Text, nullable")
        print("   - notes: Text, nullable")
        print("   - created_at: DateTime with timezone")
        print("   - Foreign key with CASCADE delete")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
