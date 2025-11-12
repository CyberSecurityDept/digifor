import logging, sys, socket
from datetime import datetime
from pathlib import Path
from app.core.config import settings

def get_server_ip():
    try:
        if hasattr(settings, 'SERVER_IP') and settings.SERVER_IP:
            return settings.SERVER_IP
        if hasattr(settings, 'POSTGRES_HOST') and settings.POSTGRES_HOST:
            return settings.POSTGRES_HOST
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = 'localhost'
        finally:
            s.close()
        return ip
    except Exception:
        return 'unknown'

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        server_ip = get_server_ip()
        formatted_message = f"| {color}{record.levelname}{reset}| {settings.PROJECT_NAME} |{server_ip}| {record.getMessage()}"
        return formatted_message

def setup_logging():
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    colored_formatter = ColoredFormatter()
    file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(colored_formatter)
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(file_formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.WARNING)
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.WARNING)
    return logging.getLogger(__name__)

def log_startup_info(logger):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"API: {settings.API_V1_STR}")
    logger.info(f"Debug: {settings.DEBUG}")

def log_database_info(logger):
    logger.info("Database connected")

def log_shutdown(logger):
    logger.info("Server shutting down")
