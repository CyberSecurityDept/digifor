#!/usr/bin/env python3
import logging, os, sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_all_tables():
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    table_name,
                    (SELECT COUNT(*) FROM information_schema.columns 
                     WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            
            print(f"\n{'='*60}")
            print(f"Database: {settings.POSTGRES_DB}")
            print(f"Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
            print(f"{'='*60}\n")
            print(f"Total Tables: {len(tables)}\n")
            
            for i, (table_name, col_count) in enumerate(tables, 1):
                try:
                    count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                    row_count = count_result.fetchone()[0]
                    print(f"{i:2d}. {table_name:<30} ({col_count} columns, {row_count:,} rows)")
                except Exception as e:
                    print(f"{i:2d}. {table_name:<30} ({col_count} columns, error: {str(e)[:30]})")
            
            print(f"\n{'='*60}\n")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    list_all_tables()

