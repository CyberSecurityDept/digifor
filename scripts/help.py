"""
Help Script
Show help information for all scripts
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Show help information"""
    print("🚀 Digital Forensics Analysis Platform - Backend")
    print("=" * 50)
    print()
    print("📁 Available Scripts:")
    print()
    print("🔧 Setup & Development:")
    print("  python scripts/setup.py              - Setup project for development")
    print("  python scripts/dev.py               - Run development server")
    print("  python scripts/prod.py              - Run production server")
    print("  python scripts/start.py              - Start development server")
    print("  python scripts/stop.py               - Stop development server")
    print("  python scripts/restart.py            - Restart development server")
    print("  python scripts/status.py             - Check server status")
    print()
    print("🧪 Testing & Quality:")
    print("  python scripts/run_tests.py         - Run all tests")
    print("  python scripts/lint.py              - Run code linting")
    print("  python scripts/format.py            - Format code")
    print("  python scripts/run_all.py           - Run all development tasks")
    print()
    print("🗄️  Database:")
    print("  python scripts/setup_db.py          - Setup database")
    print()
    print("📚 Documentation:")
    print("  http://localhost:8000/docs          - Swagger UI")
    print("  http://localhost:8000/redoc         - ReDoc")
    print("  http://localhost:8000/health         - Health check")
    print()
    print("🔧 Environment Variables:")
    print("  DEBUG=true                           - Enable debug mode")
    print("  LOG_LEVEL=DEBUG                      - Set log level")
    print("  DATABASE_URL=postgresql://...       - Database connection")
    print()
    print("📖 For more information, see README_new.md")

if __name__ == "__main__":
    main()
