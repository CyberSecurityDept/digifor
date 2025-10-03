#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.base import Base
from app.case_management.models import Case
from app.suspect_management.models import Person

def migrate_enum_status():
    print("🔄 Starting Enum Status Migration")
    print("=" * 50)
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL, echo=True)
    
    try:
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                print("📝 Step 1: Creating new Enum types...")
                
                # Create case_status enum
                connection.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE case_status AS ENUM ('Open', 'Closed', 'Re-open');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                # Create person_status enum
                connection.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE person_status AS ENUM ('Active', 'Inactive', 'Deceased');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                print("✅ Enum types created successfully")
                
                print("📝 Step 2: Updating existing data...")
                
                # Update case status values
                connection.execute(text("""
                    UPDATE cases SET status = 'Open' WHERE status = 'open';
                    UPDATE cases SET status = 'Closed' WHERE status = 'closed';
                    UPDATE cases SET status = 'Re-open' WHERE status = 'reopened';
                """))
                
                # Update person status values
                connection.execute(text("""
                    UPDATE persons SET status = 'Active' WHERE status = 'active';
                    UPDATE persons SET status = 'Inactive' WHERE status = 'inactive';
                    UPDATE persons SET status = 'Deceased' WHERE status = 'deceased';
                """))
                
                print("✅ Data updated successfully")
                
                print("📝 Step 3: Altering column types...")
                
                # Alter case status column
                connection.execute(text("""
                    ALTER TABLE cases 
                    ALTER COLUMN status TYPE case_status 
                    USING status::case_status;
                """))
                
                # Alter person status column
                connection.execute(text("""
                    ALTER TABLE persons 
                    ALTER COLUMN status TYPE person_status 
                    USING status::person_status;
                """))
                
                print("✅ Column types altered successfully")
                
                # Commit transaction
                trans.commit()
                print("✅ Migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"❌ Migration failed: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

def test_enum_status():
    """Test the new Enum status"""
    print("\n🧪 Testing Enum Status")
    print("=" * 30)
    
    try:
        from app.db.session import SessionLocal
        from app.case_management.models import Case
        from app.suspect_management.models import Person
        
        db = SessionLocal()
        
        # Test case status
        cases = db.query(Case).all()
        print(f"📊 Total cases: {len(cases)}")
        for case in cases:
            print(f"  - Case {case.case_number}: {case.status}")
        
        # Test person status
        persons = db.query(Person).all()
        print(f"📊 Total persons: {len(persons)}")
        for person in persons:
            print(f"  - Person {person.full_name}: {person.status}")
        
        db.close()
        print("✅ Enum status test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def main():
    print("🚀 Enum Status Migration Tool")
    print("=" * 50)
    
    try:
        # Run migration
        migrate_enum_status()
        
        # Test results
        test_enum_status()
        
        print("\n🎉 Migration completed successfully!")
        print("✅ Case status: Open, Closed, Re-open")
        print("✅ Person status: Active, Inactive, Deceased")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
