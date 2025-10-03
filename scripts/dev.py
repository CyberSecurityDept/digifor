simport sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run development server"""
    print("🚀 Starting development server...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Set environment variables for development
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["RELOAD"] = "true"
    
    # Run the development server
    cmd = [
        "python", "-m", "uvicorn",
        "app.main_new:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "debug",
        "--access-log",
        "--reload-dir", "app",
        "--reload-exclude", "*.pyc",
        "--reload-exclude", "__pycache__",
        "--reload-exclude", "*.log"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Development server stopped!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Development server failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
