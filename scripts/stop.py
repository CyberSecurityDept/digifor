"""
Stop Script
Stop the development server
"""

import sys
import os
import signal
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Stop development server"""
    print("🛑 Stopping development server...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Find and kill uvicorn processes
    try:
        # Find uvicorn processes
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*app.main_new:app"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"🛑 Killing process {pid}")
                    os.kill(int(pid), signal.SIGTERM)
            print("✅ Development server stopped!")
        else:
            print("ℹ️  No development server processes found")
            
    except Exception as e:
        print(f"❌ Error stopping development server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
