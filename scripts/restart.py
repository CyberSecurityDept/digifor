import sys
import os
import subprocess
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
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
        sys.exit(1)

if __name__ == "__main__":
    main()
