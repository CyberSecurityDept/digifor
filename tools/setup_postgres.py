#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script for Digital Forensics
This script helps set up PostgreSQL database and migrate from SQLite
"""

import os
import sys
import subprocess
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base, engine
from app.models import user, case, evidence, analysis, case_activity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_postgres_connection():
    """Check if PostgreSQL is running and accessible"""
    try:
        # Use environment variables from settings
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database='postgres'  # Connect to default postgres database first
        )
        conn.close()
        logger.info("✅ PostgreSQL connection successful")
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
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.postgres_db,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{settings.postgres_db}"')
            logger.info(f"✅ Database '{settings.postgres_db}' created successfully")
        else:
            logger.info(f"✅ Database '{settings.postgres_db}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f" Failed to create database: {e}")
        return False


def create_tables():
    """Create all tables in PostgreSQL"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created successfully")
        return True
    except Exception as e:
        logger.error(f" Failed to create tables: {e}")
        return False


def migrate_data_from_sqlite():
    """Migrate data from SQLite to PostgreSQL"""
    sqlite_path = "./data/Digital Forensics.db"
    
    if not os.path.exists(sqlite_path):
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
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        logger.info(f"Found {len(tables)} tables in SQLite database")
        
        for table in tables:
            if table == 'sqlite_sequence':
                continue
                
            logger.info(f"Migrating table: {table}")
            
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
                        placeholders = ', '.join(['%s'] * len(row))
                        columns = ', '.join(column_names)
                        insert_sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                        
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
        return True
        
    except Exception as e:
        logger.error(f" Data migration failed: {e}")
        return False


def create_admin_user():
    """Create default admin user"""
    try:
        from app.models.user import User
        from app.utils.security import get_password_hash
        
        pg_engine = create_engine(settings.database_url)
        pg_session = sessionmaker(bind=pg_engine)()
        
        # Check if admin user exists
        existing_admin = pg_session.query(User).filter(User.username == "admin").first()
        
        if not existing_admin:
            admin_user = User(
                username="admin",
                email="admin@Digital Forensics.com",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
                role="admin"
            )
            pg_session.add(admin_user)
            pg_session.commit()
            logger.info("✅ Admin user created (username: admin, password: admin123)")
        else:
            logger.info("✅ Admin user already exists")
        
        pg_session.close()
        return True
        
    except Exception as e:
        logger.error(f" Failed to create admin user: {e}")
        return False


def main():
    """Main setup function"""
    logger.info("🚀 Starting PostgreSQL setup for Digital Forensics...")
    
    # Step 1: Check PostgreSQL connection
    if not check_postgres_connection():
        logger.error(" Cannot connect to PostgreSQL. Please ensure PostgreSQL is running.")
        return False
    
    # Step 2: Create database
    if not create_database():
        logger.error(" Failed to create database")
        return False
    
    # Step 3: Create tables
    if not create_tables():
        logger.error(" Failed to create tables")
        return False
    
    # Step 4: Migrate data from SQLite (if exists)
    migrate_data_from_sqlite()
    
    # Step 5: Create admin user
    if not create_admin_user():
        logger.error(" Failed to create admin user")
        return False
    
    logger.info("🎉 PostgreSQL setup completed successfully!")
    logger.info("📝 Next steps:")
    logger.info("   1. Update your .env file with PostgreSQL credentials")
    logger.info("   2. Run: pip install -r requirements.txt")
    logger.info("   3. Start your application")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
