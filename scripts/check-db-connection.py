#!/usr/bin/env python3
import os, sys, logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database_connection():
    try:
        logger.info("Checking database connection...")
        logger.info(f"Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        logger.info(f"Database: {settings.POSTGRES_DB}")
        logger.info(f"User: {settings.POSTGRES_USER}")
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.info("✓ Database connection successful!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        logger.error(f"  Please check your database configuration in .env file")
        logger.error(f"  Make sure PostgreSQL is running and accessible")
        return False

if __name__ == "__main__":
    success = check_database_connection()
    sys.exit(0 if success else 1)

