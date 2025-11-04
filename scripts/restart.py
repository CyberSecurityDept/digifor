<<<<<<< HEAD
"""
Restart Script
Restart the development server
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
=======
import sys
import os
import subprocess
import time
from pathlib import Path

>>>>>>> analytics-fix
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
<<<<<<< HEAD
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
=======
    print("Restarting development server...")
    
    os.chdir(project_root)
    
    print("Stopping server...")
    try:
        subprocess.run(["pkill", "-f", "uvicorn.*app.main:app"], check=False)
        print("Server stopped")
    except Exception:
        print("No server to stop")
    
    time.sleep(2)
    
    print("Starting server...")
    try:
        subprocess.run(["./scripts/start.sh"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to start server: {e}")
>>>>>>> analytics-fix
        sys.exit(1)

if __name__ == "__main__":
    main()
