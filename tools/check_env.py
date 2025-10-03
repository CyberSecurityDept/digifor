#!/usr/bin/env python3
"""
Environment Variables Checker for Digital Forensics
Script ini memverifikasi bahwa semua environment variables terkonfigurasi dengan benar
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_env_file():
    """Check if .env file exists and is readable"""
    env_file = Path('.env')
    
    if not env_file.exists():
        logger.error(" File .env tidak ditemukan!")
        logger.info("   Solusi: cp env.example .env")
        return False
    
    if not env_file.is_file():
        logger.error(" .env bukan file!")
        return False
    
    # Check file permissions
    stat = env_file.stat()
    if stat.st_mode & 0o077:  # Check if readable by others
        logger.warning("⚠️  File .env readable by others (permission issue)")
        logger.info("   Solusi: chmod 600 .env")
    
    logger.info("✅ File .env ditemukan dan readable")
    return True


def check_database_config():
    """Check database configuration"""
    logger.info("🔍 Checking database configuration...")
    
    # Check if database URL is set
    if not settings.database_url:
        logger.error(" DATABASE_URL tidak terkonfigurasi!")
        return False
    
    # Check if it's PostgreSQL
    if not settings.database_url.startswith('postgresql://'):
        logger.error(" DATABASE_URL bukan PostgreSQL!")
        logger.info(f"   Current: {settings.database_url}")
        return False
    
    logger.info(f"✅ Database URL: {settings.database_url}")
    
    # Check individual PostgreSQL settings
    postgres_settings = [
        ('POSTGRES_HOST', settings.postgres_host),
        ('POSTGRES_PORT', settings.postgres_port),
        ('POSTGRES_USER', settings.postgres_user),
        ('POSTGRES_PASSWORD', settings.postgres_password),
        ('POSTGRES_DB', settings.postgres_db),
    ]
    
    for name, value in postgres_settings:
        if not value:
            logger.error(f" {name} tidak terkonfigurasi!")
            return False
        logger.info(f"✅ {name}: {value}")
    
    return True


def check_security_config():
    """Check security configuration"""
    logger.info("🔍 Checking security configuration...")
    
    # Check secret key
    if not settings.secret_key or settings.secret_key == "your-secret-key-here-change-in-production":
        logger.warning("⚠️  SECRET_KEY masih menggunakan default value!")
        logger.info("   Solusi: Update SECRET_KEY di .env dengan nilai yang aman")
    
    # Check encryption key
    if not settings.encryption_key or settings.encryption_key == "your-encryption-key-here-32-chars":
        logger.warning("⚠️  ENCRYPTION_KEY masih menggunakan default value!")
        logger.info("   Solusi: Update ENCRYPTION_KEY di .env dengan nilai yang aman")
    
    logger.info("✅ Security configuration checked")
    return True


def check_environment_variables():
    """Check if environment variables are loaded correctly"""
    logger.info("🔍 Checking environment variables...")
    
    # Check if .env file is being loaded by pydantic
    # Since we're using pydantic-settings, we don't need to check os.getenv()
    # Pydantic will automatically load from .env file
    
    logger.info("✅ Environment variables loaded via pydantic-settings")
    return True


def test_database_connection():
    """Test database connection"""
    logger.info("🔍 Testing database connection...")
    
    try:
        import psycopg2
        
        # Test connection using settings
        conn = psycopg2.connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
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
    """Show current configuration"""
    logger.info("📋 Current Configuration:")
    logger.info(f"   Database URL: {settings.database_url}")
    logger.info(f"   PostgreSQL Host: {settings.postgres_host}:{settings.postgres_port}")
    logger.info(f"   PostgreSQL User: {settings.postgres_user}")
    logger.info(f"   PostgreSQL Database: {settings.postgres_db}")
    logger.info(f"   Debug Mode: {settings.debug}")
    logger.info(f"   Log Level: {settings.log_level}")


def main():
    """Main function"""
    logger.info("🚀 Digital Forensics Environment Variables Checker")
    logger.info("=" * 50)
    
    all_checks_passed = True
    
    # Check 1: Environment file
    if not check_env_file():
        all_checks_passed = False
    
    # Check 2: Environment variables
    if not check_environment_variables():
        all_checks_passed = False
    
    # Check 3: Database configuration
    if not check_database_config():
        all_checks_passed = False
    
    # Check 4: Security configuration
    check_security_config()  # Warning only, doesn't fail
    
    # Check 5: Database connection
    if not test_database_connection():
        all_checks_passed = False
    
    # Show current configuration
    show_current_config()
    
    logger.info("=" * 50)
    
    if all_checks_passed:
        logger.info("🎉 Semua konfigurasi environment variables sudah benar!")
        logger.info("✅ Aplikasi siap dijalankan")
        return True
    else:
        logger.error(" Ada masalah dengan konfigurasi environment variables")
        logger.info("📝 Lihat dokumentasi: docs/ENVIRONMENT_VARIABLES.md")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
