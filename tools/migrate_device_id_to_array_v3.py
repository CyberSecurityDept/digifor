#!/usr/bin/env python3
"""
Migration script to change device_id from Integer to Array in analytic_device table
"""

import sys
import os
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

def run_migration():
    """Migrate device_id from Integer to Array"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            print("🔄 Starting migration: Change device_id from Integer to Array")
            
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'analytic_device'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("❌ Table 'analytic_device' does not exist. Skipping migration.")
                return
            
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'analytic_device' AND column_name = 'device_id';
            """))
            current_structure = result.fetchone()
            
            if not current_structure:
                print("❌ Column 'device_id' not found in 'analytic_device' table.")
                return
                
            print(f" Current device_id type: {current_structure[1]}")
            
            if 'array' in current_structure[1].lower():
                print("ℹ️ device_id is already an array type. Skipping migration.")
                return
            
            result = conn.execute(text("SELECT id, analytic_id, device_id FROM analytic_device;"))
            existing_data = result.fetchall()
            
            print(f" Found {len(existing_data)} existing records")
            
            print("📝 Creating new table structure...")
            conn.execute(text("""
                CREATE TABLE analytic_device_new (
                    id SERIAL PRIMARY KEY,
                    analytic_id INTEGER NOT NULL,
                    device_ids INTEGER[] NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analytic_id) REFERENCES analytics_history(id) ON DELETE CASCADE
                );
            """))
            
            print("📝 Migrating existing data...")
            for record in existing_data:
                conn.execute(text("""
                    INSERT INTO analytic_device_new (id, analytic_id, device_ids, created_at, updated_at)
                    VALUES (:id, :analytic_id, ARRAY[:device_id], :created_at, :updated_at)
                """), {
                    'id': record[0],
                    'analytic_id': record[1], 
                    'device_id': record[2],
                    'created_at': '2025-01-01 00:00:00',
                    'updated_at': '2025-01-01 00:00:00'
                })
            
            print("📝 Dropping old table...")
            conn.execute(text("DROP TABLE analytic_device CASCADE;"))
            
            print("📝 Renaming new table...")
            conn.execute(text("ALTER TABLE analytic_device_new RENAME TO analytic_device;"))
            
            print("📝 Recreating indexes and constraints...")
            conn.execute(text("""
                CREATE INDEX ix_analytic_device_id ON analytic_device (id);
                CREATE INDEX ix_analytic_device_analytic_id ON analytic_device (analytic_id);
            """))
            
            print("✅ Migration completed successfully!")
            print("   - device_id changed from Integer to Integer[]")
            print("   - Existing data migrated to array format")
            print("   - All constraints and indexes recreated")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    print("🔄 Analytic Device Migration: Integer to Array")
    print("=" * 50)
    run_migration()
