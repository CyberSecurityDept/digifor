#!/usr/bin/env python3
import uvicorn
from app.core.config import settings
from app.core.logging import setup_logging

if __name__ == "__main__":
    logger = setup_logging()
    
    logger.info("========================================")
    logger.info("Digital Forensics Backend - Production Server")
    logger.info("========================================")
    logger.info("Starting server...")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
