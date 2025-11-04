#!/usr/bin/env python3
"""
Migration script to remove 'type' column from analytics_history table
"""

import sys
import os
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def run_migration():
    """Remove 'type' column from analytics_history table"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            print("🔄 Starting migration: Remove 'type' column from analytics_history table")
            
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'analytics_history'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ Table 'analytics_history' does not exist. Skipping migration.")
                return
            
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'analytics_history' AND column_name = 'type';
            """))
            column_exists = result.fetchone()
            
            if not column_exists:
                print("ℹ️ Column 'type' does not exist in 'analytics_history' table. Already migrated.")
                return
            
            print(f" Found 'type' column with type: {column_exists[1]}")
            
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM analytics_history 
                WHERE type IS NOT NULL AND (method IS NULL OR method = '');
            """))
            records_to_update = result.scalar()
            
            if records_to_update > 0:
                print(f"📝 Found {records_to_update} records with 'type' but no 'method'. Migrating data...")
                
                conn.execute(text("""
                    UPDATE analytics_history 
                    SET method = type 
                    WHERE type IS NOT NULL AND (method IS NULL OR method = '');
                """))
                conn.commit()
                print(f"✓ Migrated {records_to_update} records from 'type' to 'method'")
            
            print("📝 Dropping 'type' column...")
            conn.execute(text("""
                ALTER TABLE analytics_history 
                DROP COLUMN IF EXISTS type;
            """))
            conn.commit()
            print("✓ Dropped 'type' column")
            
            print("✅ Migration completed successfully!")
            print("   - 'type' column removed from analytics_history table")
            print("   - Data migrated to 'method' column where needed")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("🔄 Analytics History Migration: Remove 'type' Column")
    print("=" * 50)
    run_migration()

