"""
Development Server Runner
Run the development server with hot reload
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Set environment variables for development
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    os.environ.setdefault("RELOAD", "true")
    
    # Run the development server
    uvicorn.run(
        "app.main_new:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        access_log=True,
        reload_dirs=["app"],
        reload_excludes=["*.pyc", "__pycache__", "*.log"]
    )
