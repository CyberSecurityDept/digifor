import sys
import os
import subprocess
import requests
from pathlib import Path


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("Checking server status...")
    
    os.chdir(project_root)

    try:
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*app.main_new:app"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"Development server is running (PID: {', '.join(pids)})")
            
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print("Server is responding to health checks")
                else:
                    print(f"Server is running but health check failed (status: {response.status_code})")
            except Exception as e:
                print(f"Server is running but not responding: {e}")
                
        else:
            print("Development server is not running")
            
    except Exception as e:
        print(f"Error checking server status: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
