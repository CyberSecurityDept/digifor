"""
Production Script
Run production server with optimal settings
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run production server"""
    print("🚀 Starting production server...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Set environment variables for production
    os.environ["DEBUG"] = "false"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["RELOAD"] = "false"
    
    # Run the production server
    cmd = [
        "python", "-m", "uvicorn",
        "app.main_new:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--workers", "4",
        "--log-level", "info",
        "--access-log",
        "--loop", "uvloop",
        "--http", "httptools"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Production server stopped!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Production server failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
