#!/usr/bin/env python3
"""
Script untuk menjalankan server dengan log yang benar-benar bersih
Menghapus SEMUA log SQLAlchemy
"""

import uvicorn
import sys
import os
import logging
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def disable_all_verbose_logs():
    """Disable ALL verbose logging completely"""

def main():
    """Run the FastAPI server with NO logs at all"""
    print("🚀 Starting Digital Forensics Backend Server (Clean Mode)")
    print("=" * 60)
    
    # Disable ALL verbose logging
    disable_all_verbose_logs()
    
    # Server configuration
    host = "0.0.0.0"
    port = 8000
    reload = True
    
    print(f"📡 Server: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🔍 Health: http://{host}:{port}/health/health")
    print("=" * 60)
    print("💡 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Run the server with NO logging at all
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="critical",  # Only critical errors
            access_log=False,  # No access logs
            reload_dirs=["./app"]
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
