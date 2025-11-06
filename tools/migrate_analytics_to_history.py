#!/usr/bin/env python3
"""
Migration script to migrate data from 'analytics' table to 'analytics_history' table
and update all references
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate_analytics_to_history():
    """Migrate data from analytics to analytics_history and update references"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                print(" Starting migration: Move data from 'analytics' to 'analytics_history'")
                
                result = conn.execute(text("SELECT COUNT(*) FROM analytics;"))
                analytics_count = result.scalar()
                print(f" Found {analytics_count} records in 'analytics' table")
                
                if analytics_count == 0:
                    print("  No data in 'analytics' table. Nothing to migrate.")
                    trans.rollback()
                    return
                
                result = conn.execute(text("SELECT COUNT(*) FROM analytics_history;"))
                analytics_history_count = result.scalar()
                
                if analytics_history_count > 0:
                    print("  'analytics_history' table is not empty. Cannot migrate.")
                    trans.rollback()
                    return
                
                print(" Copying data from 'analytics' to 'analytics_history'...")
                conn.execute(text("""
                    INSERT INTO analytics_history (id, analytic_name, type, notes, method, status, summary, created_at)
                    SELECT id, analytic_name, type, notes, method, status, summary, created_at
                    FROM analytics;
                """))
                
                print(" Updating foreign key constraint...")
                
                conn.execute(text("""
                    ALTER TABLE analytic_device 
                    DROP CONSTRAINT IF EXISTS analytic_device_analytic_id_fkey;
                """))
                
                conn.execute(text("""
                    ALTER TABLE analytic_device 
                    ADD CONSTRAINT analytic_device_analytic_id_fkey 
                    FOREIGN KEY (analytic_id) REFERENCES analytics_history(id) ON DELETE CASCADE;
                """))
                
                print("  Dropping old 'analytics' table...")
                conn.execute(text("DROP TABLE analytics;"))
                
                trans.commit()
                print(" Migration completed successfully!")
                print("   - Data copied from 'analytics' to 'analytics_history'")
                print("   - Foreign key references updated")
                print("   - Old 'analytics' table removed")
                
            except Exception as e:
                print(f" Migration failed: {e}")
                trans.rollback()
                raise
                
    except Exception as e:
        print(f" Database connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print(" Analytics to Analytics History Migration")
    print("=" * 50)
    
    success = migrate_analytics_to_history()
    
    if success:
        print("\n Migration completed successfully!")
        print("The 'analytics' table has been migrated to 'analytics_history'")
    else:
        print("\n Migration failed!")
        sys.exit(1)
