#!/usr/bin/env python3
import uvicorn, sys, os
from pathlib import Path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.logging import setup_logging

def main():
    logger = setup_logging()
    
    logger.info("==============================================")
    logger.info("Digital Forensik Backend - Development Server")
    logger.info("==============================================")
    logger.info("Activating virtual environment...")
    logger.info("Starting server...")
    
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/analysis", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
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
