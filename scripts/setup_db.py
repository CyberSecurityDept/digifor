"""
Database Setup Script
Initialize database with tables and sample data
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.db.init_db import init_db
from app.core.logging import setup_logging

def main():
    """Setup database"""
    logger = setup_logging()
    
    try:
        logger.info("Starting database setup...")
        
        # Initialize database
        init_db()
        logger.info("Database tables created successfully")
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
