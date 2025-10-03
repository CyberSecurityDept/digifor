"""
Restart Script
Restart the development server
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Restart development server"""
    print("🔄 Restarting development server...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Stop the server first
    print("🛑 Stopping server...")
    try:
        subprocess.run([sys.executable, "scripts/stop.py"], check=True)
    except subprocess.CalledProcessError:
        print("ℹ️  No server to stop")
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Start the server
    print("🚀 Starting server...")
    try:
        subprocess.run([sys.executable, "scripts/start.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
