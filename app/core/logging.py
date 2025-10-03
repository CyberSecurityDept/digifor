import logging
import sys
from datetime import datetime
from pathlib import Path

from app.core.config import settings


def setup_logging():
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging - simplified format
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return


def log_startup_info(logger):
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"🌐 API: {settings.API_V1_STR}")
    logger.info(f"🔧 Debug: {settings.DEBUG}")


def log_database_info(logger):
    logger.info("✅ Database connected")


def log_shutdown(logger):
    logger.info("🛑 Server shutting down")
