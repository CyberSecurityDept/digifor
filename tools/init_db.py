#!/usr/bin/env python3
"""
Database initialization script
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import init_db
from app.config import settings
import os

def main():
    """Initialize database and create tables"""
    print("Initializing Digital Forensics Database...")
    
    # Create data directory if it doesn't exist
    os.makedirs("./data", exist_ok=True)
    
    # Initialize database
    init_db()
    
    print("Database initialized successfully!")
    print(f"Database location: {settings.database_url}")
    print("Ready to start the application!")

if __name__ == "__main__":
    main()
