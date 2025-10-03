"""
Production Server Runner
Run the production server with optimal settings
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Set environment variables for production
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    os.environ.setdefault("RELOAD", "false")
    
    # Run the production server
    uvicorn.run(
        "app.main_new:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Number of worker processes
        log_level="info",
        access_log=True,
        reload=False,
        loop="uvloop",  # Use uvloop for better performance
        http="httptools"  # Use httptools for better performance
    )
