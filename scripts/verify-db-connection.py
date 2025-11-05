#!/usr/bin/env python3
"""
Script untuk verifikasi koneksi database dan menampilkan tabel
Membantu troubleshoot jika tabel tidak muncul di database client
"""
import sys
import os

# Add project root to path (go up one level from scripts/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text  # type: ignore
from app.core.config import settings
import psycopg2  # type: ignore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_connection():
    """Verifikasi koneksi dan tampilkan informasi detail"""
    print("\n" + "="*70)
    print("DATABASE CONNECTION VERIFICATION")
    print("="*70)
    
    print(f"\n📋 Configuration from .env:")
    print(f"   Host: {settings.POSTGRES_HOST}")
    print(f"   Port: {settings.POSTGRES_PORT}")
    print(f"   Database: {settings.POSTGRES_DB}")
    print(f"   User: {settings.POSTGRES_USER}")
    
    try:
        # Test connection
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        cur = conn.cursor()
        
        # Get connection info
        cur.execute("""
            SELECT 
                current_database() as db,
                current_user as user,
                inet_server_addr() as server_ip,
                inet_server_port() as server_port,
                version() as pg_version
        """)
        info = cur.fetchone()
        
        print(f"\n✅ Connection Successful!")
        print(f"   Connected Database: {info[0]}")
        print(f"   Connected User: {info[1]}")
        print(f"   Server IP: {info[2] or 'localhost'}")
        print(f"   Server Port: {info[3]}")
        print(f"   PostgreSQL Version: {info[4].split(',')[0]}")
        
        # List all databases on server
        cur.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false 
            ORDER BY datname
        """)
        databases = [d[0] for d in cur.fetchall()]
        print(f"\n📚 Available Databases on Server:")
        for db in databases:
            marker = " ← CURRENT" if db == settings.POSTGRES_DB else ""
            print(f"   - {db}{marker}")
        
        # List all schemas
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)
        schemas = [s[0] for s in cur.fetchall()]
        print(f"\n📂 Available Schemas:")
        for schema in schemas:
            marker = " ← DEFAULT" if schema == 'public' else ""
            print(f"   - {schema}{marker}")
        
        # List all tables in public schema
        cur.execute("""
            SELECT 
                table_name,
                (SELECT COUNT(*) 
                 FROM information_schema.columns 
                 WHERE table_schema = 'public' 
                 AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        print(f"\n📊 Tables in 'public' schema ({len(tables)} total):")
        if tables:
            for i, (table_name, col_count) in enumerate(tables, 1):
                # Get row count
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    row_count = cur.fetchone()[0]
                    print(f"   {i:2d}. {table_name:<35} ({col_count:2d} cols, {row_count:6,} rows)")
                except Exception as e:
                    print(f"   {i:2d}. {table_name:<35} ({col_count:2d} cols, error: {str(e)[:30]})")
        else:
            print("   ⚠️  No tables found in 'public' schema!")
        
        # Check user permissions
        cur.execute("""
            SELECT 
                has_database_privilege(%s, %s, 'CONNECT') as can_connect,
                has_database_privilege(%s, %s, 'CREATE') as can_create,
                has_schema_privilege(%s, 'public', 'USAGE') as can_use_schema,
                has_schema_privilege(%s, 'public', 'CREATE') as can_create_in_schema
        """, (settings.POSTGRES_USER, settings.POSTGRES_DB, 
              settings.POSTGRES_USER, settings.POSTGRES_DB,
              settings.POSTGRES_USER, settings.POSTGRES_USER))
        perms = cur.fetchone()
        
        print(f"\n🔐 User Permissions:")
        print(f"   Can connect to database: {'✅' if perms[0] else '❌'}")
        print(f"   Can create in database: {'✅' if perms[1] else '❌'}")
        print(f"   Can use public schema: {'✅' if perms[2] else '❌'}")
        print(f"   Can create in public schema: {'✅' if perms[3] else '❌'}")
        
        cur.close()
        conn.close()
        
        print(f"\n" + "="*70)
        print("✅ VERIFICATION COMPLETE")
        print("="*70)
        
        print(f"\n💡 Troubleshooting Tips:")
        print(f"   1. In your database client (pgAdmin/DBeaver), make sure you:")
        print(f"      - Connect to database: {settings.POSTGRES_DB}")
        print(f"      - NOT to database: postgres")
        print(f"      - View schema: public (not information_schema)")
        print(f"      - Use host: {settings.POSTGRES_HOST}")
        print(f"      - Use port: {settings.POSTGRES_PORT}")
        print(f"   2. Refresh the connection in your client (F5 or right-click > Refresh)")
        print(f"   3. Expand: Database → {settings.POSTGRES_DB} → Schemas → public → Tables")
        print(f"   4. If tables still don't appear, check if you're connected to the correct server")
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        print(f"\n" + "="*70)
        print("❌ VERIFICATION FAILED")
        print("="*70)
        return False


if __name__ == "__main__":
    verify_connection()

