#!/usr/bin/env python3
import os
import sys
import subprocess
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

<<<<<<< HEAD
# Add the parent directory to the path so we can import app modules
=======
>>>>>>> analytics-fix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.case_management.models import Case, CasePerson, Agency, WorkUnit
from app.evidence_management.models import Evidence
from app.suspect_management.models import Person

<<<<<<< HEAD
# Configure logging
=======
>>>>>>> analytics-fix
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_postgres_connection():
    """Check if PostgreSQL is running and accessible"""
    try:
<<<<<<< HEAD
        # Use environment variables from settings
=======
>>>>>>> analytics-fix
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
<<<<<<< HEAD
            database='postgres'  # Connect to default postgres database first
        )
        conn.close()
        logger.info("✅ PostgreSQL connection successful")
=======
            database='postgres'
        )
        conn.close()
        logger.info(" PostgreSQL connection successful")
>>>>>>> analytics-fix
        logger.info(f"   Host: {settings.postgres_host}:{settings.postgres_port}")
        logger.info(f"   User: {settings.postgres_user}")
        logger.info(f"   Database: {settings.postgres_db}")
        return True
    except Exception as e:
        logger.error(f" PostgreSQL connection failed: {e}")
        logger.error(f"   Check your .env file configuration")
        logger.error(f"   Current settings: {settings.postgres_host}:{settings.postgres_port}")
        return False


def create_database():
    """Create the Digital Forensics database if it doesn't exist"""
    try:
<<<<<<< HEAD
        # Connect to PostgreSQL server (not to a specific database)
=======
>>>>>>> analytics-fix
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
<<<<<<< HEAD
        # Check if database exists
=======
>>>>>>> analytics-fix
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.postgres_db,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{settings.postgres_db}"')
<<<<<<< HEAD
            logger.info(f"✅ Database '{settings.postgres_db}' created successfully")
        else:
            logger.info(f"✅ Database '{settings.postgres_db}' already exists")
=======
            logger.info(f" Database '{settings.postgres_db}' created successfully")
        else:
            logger.info(f" Database '{settings.postgres_db}' already exists")
>>>>>>> analytics-fix
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f" Failed to create database: {e}")
        return False


def create_tables():
    """Create all tables in PostgreSQL"""
    try:
<<<<<<< HEAD
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully")
=======
        Base.metadata.create_all(bind=engine)
        logger.info(" All tables created successfully")
>>>>>>> analytics-fix
        return True
    except Exception as e:
        logger.error(f" Failed to create tables: {e}")
        return False


def migrate_data_from_sqlite():
    """Migrate data from SQLite to PostgreSQL"""
    sqlite_path = "./data/Digital Forensics.db"
    
    if not os.path.exists(sqlite_path):
<<<<<<< HEAD
        logger.warning(f"⚠️  SQLite database not found at {sqlite_path}")
        return True
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to PostgreSQL
        pg_engine = create_engine(settings.database_url)
        pg_session = sessionmaker(bind=pg_engine)()
        
        # Get list of tables from SQLite
=======
        logger.warning(f"  SQLite database not found at {sqlite_path}")
        return True
    
    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        pg_engine = create_engine(settings.database_url)
        pg_session = sessionmaker(bind=pg_engine)()
        
>>>>>>> analytics-fix
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        logger.info(f"Found {len(tables)} tables in SQLite database")
        
        for table in tables:
            if table == 'sqlite_sequence':
                continue
                
            logger.info(f"Migrating table: {table}")
            
<<<<<<< HEAD
            # Get table data
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in sqlite_cursor.description]
            
            if rows:
                # Insert data into PostgreSQL
                for row in rows:
                    try:
                        # Create insert statement with proper parameter binding
=======
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            column_names = [description[0] for description in sqlite_cursor.description]
            
            if rows:
                for row in rows:
                    try:
>>>>>>> analytics-fix
                        placeholders = ', '.join(['%s'] * len(row))
                        columns = ', '.join(column_names)
                        insert_sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                        
<<<<<<< HEAD
                        # Convert row to tuple for psycopg2
                        pg_session.execute(text(insert_sql), row)
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to insert row in {table}: {e}")
                        continue
                
                pg_session.commit()
                logger.info(f"✅ Migrated {len(rows)} rows from {table}")
        
        sqlite_conn.close()
        pg_session.close()
        logger.info("✅ Data migration completed successfully")
=======
                        pg_session.execute(text(insert_sql), row)
                    except Exception as e:
                        logger.warning(f"  Failed to insert row in {table}: {e}")
                        continue
                
                pg_session.commit()
                logger.info(f" Migrated {len(rows)} rows from {table}")
        
        sqlite_conn.close()
        pg_session.close()
        logger.info(" Data migration completed successfully")
>>>>>>> analytics-fix
        return True
        
    except Exception as e:
        logger.error(f" Data migration failed: {e}")
        return False


def create_admin_user():
    """Create default admin user"""
    try:
<<<<<<< HEAD
        # Note: User model and security utilities not yet implemented
        # from app.models.user import User
        # from app.utils.security import get_password_hash
=======
>>>>>>> analytics-fix
        
        pg_engine = create_engine(settings.database_url)
        pg_session = sessionmaker(bind=pg_engine)()
        
<<<<<<< HEAD
        # Note: User model not yet implemented - skipping admin user creation
        logger.info("ℹ️ User management not yet implemented - skipping admin user creation")
=======
        logger.info("ℹ User management not yet implemented - skipping admin user creation")
>>>>>>> analytics-fix
        return True
        
        pg_session.close()
        return True
        
    except Exception as e:
        logger.error(f" Failed to create admin user: {e}")
        return False


def main():
    """Main setup function"""
<<<<<<< HEAD
    logger.info("🚀 Starting PostgreSQL setup for Digital Forensics...")
    
    # Step 1: Check PostgreSQL connection
=======
    logger.info(" Starting PostgreSQL setup for Digital Forensics...")
    
>>>>>>> analytics-fix
    if not check_postgres_connection():
        logger.error(" Cannot connect to PostgreSQL. Please ensure PostgreSQL is running.")
        return False
    
<<<<<<< HEAD
    # Step 2: Create database
=======
>>>>>>> analytics-fix
    if not create_database():
        logger.error(" Failed to create database")
        return False
    
<<<<<<< HEAD
    # Step 3: Create tables
=======
>>>>>>> analytics-fix
    if not create_tables():
        logger.error(" Failed to create tables")
        return False
    
<<<<<<< HEAD
    # Step 4: Migrate data from SQLite (if exists)
    migrate_data_from_sqlite()
    
    # Step 5: Create admin user
=======
    migrate_data_from_sqlite()
    
>>>>>>> analytics-fix
    if not create_admin_user():
        logger.error(" Failed to create admin user")
        return False
    
<<<<<<< HEAD
    logger.info("🎉 PostgreSQL setup completed successfully!")
    logger.info("📝 Next steps:")
=======
    logger.info(" PostgreSQL setup completed successfully!")
    logger.info(" Next steps:")
>>>>>>> analytics-fix
    logger.info("   1. Update your .env file with PostgreSQL credentials")
    logger.info("   2. Run: pip install -r requirements.txt")
    logger.info("   3. Start your application")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
