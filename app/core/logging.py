import logging
import sys
from datetime import datetime
from pathlib import Path

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and structured format"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create formatted message
        formatted_message = f"{timestamp} | {color}{record.levelname}{reset}| {settings.PROJECT_NAME} | {record.getMessage()}"
        
        return formatted_message


def setup_logging():
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    colored_formatter = ColoredFormatter()
    file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(colored_formatter)
    
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.handlers.clear()  # Clear existing handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Return the logger instance
    return logging.getLogger(__name__)


def log_startup_info(logger):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"API: {settings.API_V1_STR}")
    logger.info(f"Debug: {settings.DEBUG}")


def log_database_info(logger):
    logger.info("Database connected")


def log_shutdown(logger):
    logger.info("Server shutting down")
