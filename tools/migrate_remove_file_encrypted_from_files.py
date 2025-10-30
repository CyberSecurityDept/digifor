#!/usr/bin/env python3
"""
Migration script to remove 'file_encrypted' column from 'files' table.
- If the column exists, migrate (no data move needed) and drop it safely.
"""

import sys
import os
from sqlalchemy import create_engine, text

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings  # type: ignore


def run_migration():
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        try:
            print("🔄 Starting migration: Remove 'file_encrypted' from files table")

            # Check table exists
            exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'files'
                );
            """)).scalar()
            if not exists:
                print("❌ Table 'files' does not exist. Skipping.")
                return

            # Check column exists
            col_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='files' AND column_name='file_encrypted'
                );
            """)).scalar()
            if not col_exists:
                print("ℹ️ Column 'file_encrypted' not found. Nothing to do.")
                return

            # Drop the column
            print("📝 Dropping column 'file_encrypted' ...")
            conn.execute(text("ALTER TABLE files DROP COLUMN IF EXISTS file_encrypted;"))
            conn.commit()
            print("✓ Column dropped")
            print("✅ Migration completed successfully")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    print("🔄 Files Table Migration: Remove 'file_encrypted' Column")
    print("=" * 60)
    run_migration()
