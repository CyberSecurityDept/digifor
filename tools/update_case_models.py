#!/usr/bin/env python3
"""
Script to update database with new case management models
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings
from app.models.case import Case
from app.models.case_activity import CaseActivity, CaseStatusHistory
from app.models.user import User
from app.database import Base

def update_database():
    """Update database with new models"""
    print("🔄 Updating database with new case management models...")
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    try:
        # Create all tables (this will add new tables and columns)
        Base.metadata.create_all(bind=engine)
        print("✅ Database updated successfully!")
        
        # Check if new tables exist
        with engine.connect() as conn:
            # Check case_activities table
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='case_activities'"))
            if result.fetchone():
                print("✅ case_activities table created")
            else:
                print("❌ case_activities table not found")
            
            # Check case_status_history table
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='case_status_history'"))
            if result.fetchone():
                print("✅ case_status_history table created")
            else:
                print("❌ case_status_history table not found")
            
            # Check if new columns exist in cases table
            result = conn.execute(text("PRAGMA table_info(cases)"))
            columns = [row[1] for row in result.fetchall()]
            
            new_columns = ['reopened_count', 'last_status_change', 'status_change_reason', 'status_history']
            for col in new_columns:
                if col in columns:
                    print(f"✅ Column '{col}' added to cases table")
                else:
                    print(f"❌ Column '{col}' not found in cases table")
        
        print("\n🎉 Database update completed!")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = update_database()
    if success:
        print("\n✅ Case management models successfully implemented!")
        print("\n📋 New features available:")
        print("- Case status lifecycle: Open → Closed → Reopened")
        print("- Activity tracking with timestamps and user logs")
        print("- Status history with reason logs")
        print("- New API endpoints for case management")
    else:
        print("\n❌ Failed to update database")
        sys.exit(1)
