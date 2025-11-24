#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path
import psycopg2

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_env_file():
    env_file = Path('.env')
    
    if not env_file.exists():
        logger.error(" File .env tidak ditemukan!")
        logger.info("   Solusi: cp env.example .env")
        return False
    
    if not env_file.is_file():
        logger.error(" .env bukan file!")
        return False
    
    stat = env_file.stat()
    if stat.st_mode & 0o077:
        logger.warning("File .env readable by others (permission issue)")
        logger.info("   Solusi: chmod 600 .env")
    
    logger.info("✅ File .env ditemukan dan readable")
    return True


def check_database_config():
    logger.info("🔍 Checking database configuration...")
    
    if not settings.DATABASE_URL:
        logger.error(" DATABASE_URL tidak terkonfigurasi!")
        return False
    
    if not settings.DATABASE_URL.startswith('postgresql://'):
        logger.error(" DATABASE_URL bukan PostgreSQL!")
        logger.info(f"   Current: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else '***'}")
        return False
    
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else '***'}")

    postgres_settings = [
        ('POSTGRES_HOST', settings.POSTGRES_HOST),
        ('POSTGRES_PORT', settings.POSTGRES_PORT),
        ('POSTGRES_USER', settings.POSTGRES_USER),
        ('POSTGRES_PASSWORD', '***' if settings.POSTGRES_PASSWORD else None),
        ('POSTGRES_DB', settings.POSTGRES_DB),
    ]
    
    for name, value in postgres_settings:
        if not value:
            logger.error(f" {name} tidak terkonfigurasi!")
            return False
        logger.info(f"{name}: {value}")
    
    return True


def check_security_config():
    logger.info("Checking security configuration...")
    
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here-change-in-production":
        logger.warning("SECRET_KEY masih menggunakan default value!")
        logger.info("   Solusi: Update SECRET_KEY di .env dengan nilai yang aman")
    
    if not settings.ENCRYPTION_KEY or settings.ENCRYPTION_KEY == "your-encryption-key-here-32-chars":
        logger.warning("ENCRYPTION_KEY masih menggunakan default value!")
        logger.info("   Solusi: Update ENCRYPTION_KEY di .env dengan nilai yang aman")
    
    logger.info("Security configuration checked")
    return True


def check_environment_variables():
    logger.info("🔍 Checking environment variables...")
    
    logger.info("Environment variables loaded via pydantic-settings")
    return True


def test_database_connection():
    logger.info("🔍 Testing database connection...")
    
    try:
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database='postgres'  # Connect to default postgres database first
        )
        conn.close()
        logger.info("✅ Database connection successful")
        return True
        
    except ImportError:
        logger.error(" psycopg2 tidak terinstall!")
        logger.info("   Solusi: pip install psycopg2-binary")
        return False
        
    except Exception as e:
        logger.error(f" Database connection failed: {e}")
        logger.info("   Solusi: Check PostgreSQL service dan credentials")
        return False


def show_current_config():
    logger.info("📋 Current Configuration:")
    logger.info(f"   Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else '***'}")
    logger.info(f"   PostgreSQL Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"   PostgreSQL User: {settings.POSTGRES_USER}")
    logger.info(f"   PostgreSQL Database: {settings.POSTGRES_DB}")
    logger.info(f"   Debug Mode: {settings.DEBUG}")
    logger.info(f"   Log Level: {settings.LOG_LEVEL}")


def main():
    logger.info("Digital Forensics Environment Variables Checker")
    logger.info("=" * 50)
    
    all_checks_passed = True
    
    if not check_env_file():
        all_checks_passed = False
    
    if not check_environment_variables():
        all_checks_passed = False
    
    if not check_database_config():
        all_checks_passed = False

    check_security_config()
    
    if not test_database_connection():
        all_checks_passed = False
    
    show_current_config()
    
    logger.info("=" * 50)
    
    if all_checks_passed:
        logger.info("Semua konfigurasi environment variables sudah benar!")
        logger.info("Aplikasi siap dijalankan")
        return True
    else:
        logger.error(" Ada masalah dengan konfigurasi environment variables")
        logger.info("Lihat dokumentasi: docs/ENVIRONMENT_VARIABLES.md")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
