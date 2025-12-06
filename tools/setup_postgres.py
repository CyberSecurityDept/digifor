#!/usr/bin/env python3
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging, os, sys, sqlite3, psycopg2, subprocess, re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.case_management.models import Case, Agency, WorkUnit
from app.evidence_management.models import Evidence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_identifier(identifier: str, identifier_type: str = "database") -> bool:
    if not identifier or not isinstance(identifier, str):
        return False
    
    if len(identifier) > 63:
        logger.error(f" {identifier_type} name too long (max 63 characters): {identifier}")
        return False
    
    if not (identifier[0].isalpha() or identifier[0] == '_'):
        logger.error(f" {identifier_type} name must start with letter or underscore: {identifier}")
        return False
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        logger.error(f" {identifier_type} name contains invalid characters: {identifier}")
        return False
    
    sql_keywords = [
        'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
        'truncate', 'exec', 'execute', 'union', 'script', 'javascript'
    ]
    if identifier.lower() in sql_keywords:
        logger.error(f" {identifier_type} name cannot be a SQL keyword: {identifier}")
        return False
    
    return True

def sanitize_identifier(identifier: str) -> str:
    if not identifier:
        return ""
    
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
    
    if sanitized and not (sanitized[0].isalpha() or sanitized[0] == '_'):
        sanitized = '_' + sanitized
    
    # Limit length
    if len(sanitized) > 63:
        sanitized = sanitized[:63]
    
    return sanitized

def check_postgres_connection():
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database='postgres'
        )
        conn.close()
        logger.info(" PostgreSQL connection successful")
        logger.info(f"   Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        logger.info(f"   User: {settings.POSTGRES_USER}")
        logger.info(f"   Database: {settings.POSTGRES_DB}")
        return True
    except Exception as e:
        logger.error(f" PostgreSQL connection failed: {e}")
        logger.error(f"   Check your .env file configuration")
        logger.error(f"   Current settings: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        return False

def create_database():
    try:
        # Validate database name to prevent SQL injection
        if not validate_identifier(settings.POSTGRES_DB, "database"):
            logger.error(f" Invalid database name: {settings.POSTGRES_DB}")
            logger.error(" Database name must contain only letters, numbers, and underscores")
            logger.error(" Database name must start with a letter or underscore")
            logger.error(" Database name cannot be a SQL keyword")
            return False
        
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.POSTGRES_DB,))
        exists = cursor.fetchone()
        
        if not exists:
            safe_db_name = sql.Identifier(settings.POSTGRES_DB)
            create_query = sql.SQL("CREATE DATABASE {}").format(safe_db_name)
            cursor.execute(create_query)
            logger.info(f" Database '{settings.POSTGRES_DB}' created successfully")
        else:
            logger.info(f" Database '{settings.POSTGRES_DB}' already exists")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f" Failed to create database: {e}")
        return False

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(" All tables created successfully")
        return True
    except Exception as e:
        logger.error(f" Failed to create tables: {e}")
        return False

def migrate_data_from_sqlite():
    sqlite_path = "./data/Digital Forensics.db"
    
    if not os.path.exists(sqlite_path):
        logger.warning(f"  SQLite database not found at {sqlite_path}")
        return True
    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        pg_engine = create_engine(settings.DATABASE_URL)
        pg_session = sessionmaker(bind=pg_engine)()
        
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        logger.info(f"Found {len(tables)} tables in SQLite database")
        
        for table in tables:
            if table == 'sqlite_sequence':
                continue

            if not validate_identifier(table, "table"):
                logger.warning(f" Skipping table with invalid name: {table}")
                continue
            
            logger.info(f"Migrating table: {table}")
            
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            column_names = [description[0] for description in sqlite_cursor.description]
            
            valid_columns = []
            for col in column_names:
                if validate_identifier(col, "column"):
                    valid_columns.append(col)
                else:
                    logger.warning(f" Skipping column with invalid name in table {table}: {col}")
            
            if not valid_columns:
                logger.warning(f" No valid columns found in table {table}, skipping")
                continue
            
            if rows:
                for row in rows:
                    try:
                        placeholders = ', '.join(['%s'] * len(valid_columns))
                        
                        safe_table = sql.Identifier(table)
                        safe_columns = [sql.Identifier(col) for col in valid_columns]
                        
                        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                            safe_table,
                            sql.SQL(', ').join(safe_columns),
                            sql.SQL(placeholders)
                        )
                        
                        pg_session.execute(insert_query, row[:len(valid_columns)])
                    except Exception as e:
                        logger.warning(f"  Failed to insert row in {table}: {e}")
                        continue
                
                pg_session.commit()
                logger.info(f" Migrated {len(rows)} rows from {table}")
        
        sqlite_conn.close()
        pg_session.close()
        logger.info(" Data migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f" Data migration failed: {e}")
        return False

def create_admin_user():
    try:
        pg_engine = create_engine(settings.DATABASE_URL)
        pg_session = sessionmaker(bind=pg_engine)()
        logger.info("ℹ User management not yet implemented - skipping admin user creation")
        return True
        pg_session.close()
        return True
    except Exception as e:
        logger.error(f" Failed to create admin user: {e}")
        return False

def main():
    logger.info(" Starting PostgreSQL setup for Digital Forensics...")
    if not check_postgres_connection():
        logger.error(" Cannot connect to PostgreSQL. Please ensure PostgreSQL is running.")
        return False
    if not create_database():
        logger.error(" Failed to create database")
        return False
    if not create_tables():
        logger.error(" Failed to create tables")
        return False
    migrate_data_from_sqlite()
    
    if not create_admin_user():
        logger.error(" Failed to create admin user")
        return False
    
    logger.info(" PostgreSQL setup completed successfully!")
    logger.info(" Next steps:")
    logger.info("   1. Update your .env file with PostgreSQL credentials")
    logger.info("   2. Run: pip install -r requirements.txt")
    logger.info("   3. Start your application")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)