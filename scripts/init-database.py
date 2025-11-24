#!/usr/bin/env python3
import logging, sys, os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, inspect  # type: ignore
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.auth.models import *
from app.analytics.shared.models import *
from app.case_management.models import *
from app.evidence_management.models import *
from app.suspect_management.models import *
from app.analytics.device_management.models import *
from app.analytics.analytics_management.models import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database():
    try:
        logger.info("Initializing database...")
        logger.info(f"Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        logger.info(f"Database: {settings.POSTGRES_DB}")
        logger.info(f"User: {settings.POSTGRES_USER}")
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if existing_tables:
            logger.info(f"Found {len(existing_tables)} existing tables in database")
        else:
            logger.info("No existing tables found, creating all tables...")
        
        Base.metadata.create_all(bind=engine)
        
        inspector = inspect(engine)
        tables_after = inspector.get_table_names()
        
        logger.info(f"✓ Database initialization complete!")
        logger.info(f"  Total tables: {len(tables_after)}")
        
        if tables_after:
            logger.info(f"  Tables: {', '.join(tables_after[:5])}" + 
                       (f" ... and {len(tables_after) - 5} more" if len(tables_after) > 5 else ""))
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        logger.error(f"  Please check your database configuration in .env file")
        logger.error(f"  Make sure PostgreSQL is running and accessible")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)

