#!/usr/bin/env python3
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import init_db
from app.core.config import settings
import os

def main():
    print("Initializing Digital Forensics Database...")
    
    os.makedirs("./data", exist_ok=True)
    
    init_db()
    
    print("Database initialized successfully!")
    print(f"Database location: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else '***'}")
    print("Ready to start the application!")

if __name__ == "__main__":
    main()
