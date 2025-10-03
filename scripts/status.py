"""
Status Script
Check the status of the development server
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Check server status"""
    print("🔍 Checking server status...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Check if uvicorn processes are running
    try:
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*app.main_new:app"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ Development server is running (PID: {', '.join(pids)})")
            
            # Check if server is responding
            try:
                import requests
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is responding to health checks")
                else:
                    print(f"⚠️  Server is running but health check failed (status: {response.status_code})")
            except Exception as e:
                print(f"⚠️  Server is running but not responding: {e}")
                
        else:
            print("❌ Development server is not running")
            
    except Exception as e:
        print(f"❌ Error checking server status: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
