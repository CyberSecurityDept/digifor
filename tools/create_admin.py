#!/usr/bin/env python3
"""
Create admin user script
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.utils.security import get_password_hash

def create_admin_user():
    """Create admin user"""
    db = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@forenlytic.com",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            department="IT",
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("Please change the password after first login!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
