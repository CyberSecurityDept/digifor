#!/usr/bin/env python3
"""
Script to add account_name column to chat_messages table
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.config import settings

def add_account_name_column():
    """Add account_name column to chat_messages table"""
    db = SessionLocal()
    try:
        print("Checking if account_name column exists...")
        
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='chat_messages' AND column_name='account_name'
        """)
        result = db.execute(check_query).fetchone()
        
        if result:
            print("✓ Column 'account_name' already exists in chat_messages table")
            return
        
        print("Adding account_name column to chat_messages table...")
        
        # Add column
        add_column_query = text("""
            ALTER TABLE chat_messages 
            ADD COLUMN account_name VARCHAR
        """)
        db.execute(add_column_query)
        db.commit()
        
        print("✓ Successfully added 'account_name' column to chat_messages table")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error adding column: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print(f"Database: {settings.POSTGRES_DB}@{settings.POSTGRES_HOST}")
    add_account_name_column()

