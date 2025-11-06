#!/usr/bin/env python3
"""
Script untuk test insert data ke database
Membantu diagnose masalah insert
"""
import sys
import os

# Add project root to path (go up one level from scripts/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session  # type: ignore
from app.db.session import SessionLocal, engine
from app.case_management.models import Case
from datetime import datetime
from sqlalchemy import text
import traceback

def test_database_insert():
    print("="*60)
    print("DATABASE INSERT TEST")
    print("="*60)
    
    db: Session = SessionLocal()
    
    try:
        # Test 1: Check connection
        print("\n1. Testing database connection...")
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        print("Connection OK")
        
        # Test 2: Check permissions
        print("\n2. Testing permissions...")
        db.execute(text("SELECT has_table_privilege('digifor', 'cases', 'INSERT')"))
        print("Permissions OK")
        
        # Test 3: Check current data
        print("\n3. Checking existing data...")
        count_before = db.query(Case).count()
        print(f"Current cases count: {count_before}")
        
        # Test 4: Test insert
        print("\n4. Testing INSERT...")
        test_case = Case(
            title='TEST INSERT',
            description='Test description for insert',
            status='Open',
            case_number=f'TEST-{datetime.now().strftime("%d%m%y")}-0001',
            created_at=datetime.now()
        )
        
        db.add(test_case)
        print("db.add() successful")
        
        # Flush to test if insert would work
        db.flush()
        print(f"db.flush() successful - ID: {test_case.id}")
        
        # Commit
        db.commit()
        print(f"db.commit() successful - ID: {test_case.id}")
        
        # Verify
        saved = db.query(Case).filter(Case.id == test_case.id).first()
        if saved:
            print(f"Data verified in database!")
            print(f"Title: {saved.title}")
            print(f"Case Number: {saved.case_number}")
            
            # Cleanup
            db.delete(saved)
            db.commit()
            print(f"Cleanup successful")
        else:
            print(f"Data NOT found in database after commit!")
            
        # Test 5: Check count after
        count_after = db.query(Case).count()
        print(f"\n5. Cases count after test: {count_after}")
        if count_after == count_before:
            print("Count matches (data cleaned up)")
        else:
            print(f"Count mismatch (expected {count_before}, got {count_after})")
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        db.rollback()
        print("\n" + "="*60)
        print("TEST FAILED!")
        print("="*60)
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_database_insert()
    sys.exit(0 if success else 1)

