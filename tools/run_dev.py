#!/usr/bin/env python3
"""
Forenlytic Backend Development Runner
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.utils.logging import setup_logging

def main():
    """Run the development server"""
    # Setup logging
    logger = setup_logging()
    
    logger.info("========================================")
    logger.info("Forenlytic Backend - Development Server")
    logger.info("========================================")
    logger.info("Activating virtual environment...")
    logger.info("Starting server...")
    
    # Ensure data directories exist
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/analysis", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
