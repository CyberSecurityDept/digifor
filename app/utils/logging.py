"""
Centralized logging configuration for Forenlytic Backend
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(log_level: str = None, log_file: str = None) -> logging.Logger:
    """
    Setup centralized logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        
    Returns:
        Configured logger instance
    """
    # Use settings if not provided
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file
    
    # Create logger
    logger = logging.getLogger("forenlytic")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "forenlytic") -> logging.Logger:
    """
    Get logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_startup_info(logger: logging.Logger):
    """Log startup information"""
    logger.info("Forenlytic Backend is starting up...")
    logger.info(f"Version: {settings.version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Working directory: {Path.cwd()}")


def log_database_info(logger: logging.Logger):
    """Log database information"""
    logger.info("Database initialized")
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Analysis directory: {settings.analysis_dir}")
    logger.info(f"Reports directory: {settings.reports_dir}")


# def log_server_ready(logger: logging.Logger, host: str = "localhost", port: int = 8000):
#     """Log server ready information"""
#     logger.info(f"Forenlytic Backend is ready at http://{host}:{port}")
#     logger.info(f"API Documentation: http://{host}:{port}/docs")
#     logger.info(f"ReDoc: http://{host}:{port}/redoc")


def log_shutdown(logger: logging.Logger):
    """Log shutdown information"""
    logger.info("Shutting down Forenlytic Backend...")


# Initialize default logger
logger = setup_logging()
