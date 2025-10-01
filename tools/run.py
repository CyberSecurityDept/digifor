#!/usr/bin/env python3
"""
Digital Forensics Backend Runner Script
"""
import uvicorn
from app.config import settings
from app.utils.logging import setup_logging

if __name__ == "__main__":
    # Setup logging
    logger = setup_logging()
    
    logger.info("========================================")
    logger.info("Digital Forensics Backend - Production Server")
    logger.info("========================================")
    logger.info("Starting server...")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )
