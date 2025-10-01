#!/usr/bin/env python3
"""
Script to add new columns to cases table
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def add_case_columns():
    """Add new columns to cases table"""
    print("🔄 Adding new columns to cases table...")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Add new columns to cases table
            columns_to_add = [
                "reopened_count INTEGER DEFAULT 0",
                "last_status_change DATETIME",
                "status_change_reason TEXT",
                "status_history JSON"
            ]
            
            for column in columns_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE cases ADD COLUMN {column}"))
                    print(f"✅ Added column: {column.split()[0]}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠️  Column {column.split()[0]} already exists")
                    else:
                        print(f" Error adding column {column.split()[0]}: {e}")
            
            # Update status column to include 'reopened'
            try:
                conn.execute(text("""
                    UPDATE cases 
                    SET status = 'reopened' 
                    WHERE status = 'closed' AND reopened_count > 0
                """))
                print("✅ Updated status values")
            except Exception as e:
                print(f"⚠️  Could not update status values: {e}")
            
            conn.commit()
        
        print("\n✅ Case columns added successfully!")
        
    except Exception as e:
        print(f" Error adding columns: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = add_case_columns()
    if success:
        print("\n🎉 Case management columns successfully added!")
    else:
        print("\n Failed to add columns")
        sys.exit(1)
