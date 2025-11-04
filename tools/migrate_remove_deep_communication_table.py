#!/usr/bin/env python3
"""
Migration script to remove deep_communication table
Since we're now using chat_messages table instead
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import get_db

def remove_deep_communication_table():
    """Remove deep_communication table and related data"""
    
    db = next(get_db())
    
    try:
        print("🗑️  Starting removal of deep_communication table...")
        
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'deep_communication'
            );
        """))
        
        table_exists = result.scalar()
        
        if not table_exists:
            print("deep_communication table does not exist, nothing to remove")
            return
        
        print(" Found deep_communication table, proceeding with removal...")
        
        print("🔗 Dropping foreign key constraints...")
        
        fk_result = db.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'deep_communication' 
            AND constraint_type = 'FOREIGN KEY';
        """))
        
        fk_constraints = [row[0] for row in fk_result]
        
        for constraint in fk_constraints:
            try:
                db.execute(text(f"ALTER TABLE deep_communication DROP CONSTRAINT {constraint};"))
                print(f"   Dropped constraint: {constraint}")
            except Exception as e:
                print(f"   Could not drop constraint {constraint}: {e}")
        
        print("📇 Dropping indexes...")
        try:
            db.execute(text("DROP INDEX IF EXISTS ix_deep_communication_id;"))
            print("   Dropped index: ix_deep_communication_id")
        except Exception as e:
            print(f"   Could not drop index: {e}")
        
        print("🗑️  Dropping deep_communication table...")
        db.execute(text("DROP TABLE IF EXISTS deep_communication CASCADE;"))
        
        db.commit()
        print("Successfully removed deep_communication table")
        
        verify_result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'deep_communication'
            );
        """))
        
        still_exists = verify_result.scalar()
        
        if not still_exists:
            print("Verification: deep_communication table successfully removed")
        else:
            print("Verification failed: deep_communication table still exists")
            
    except Exception as e:
        print(f"Error removing deep_communication table: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🗑️  DEEP COMMUNICATION TABLE REMOVAL MIGRATION")
    print("=" * 60)
    print()
    
    remove_deep_communication_table()
    
    print()
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)
