"""
Linting Script
Run code quality checks
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Run all linting checks"""
    print("🔍 Running code quality checks...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Commands to run
    commands = [
        (["python", "-m", "black", "--check", "app/"], "Black formatting check"),
        (["python", "-m", "isort", "--check-only", "app/"], "Import sorting check"),
        (["python", "-m", "flake8", "app/"], "Flake8 linting"),
        (["python", "-m", "mypy", "app/"], "MyPy type checking"),
    ]
    
    all_passed = True
    
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
    
    if all_passed:
        print("✅ All code quality checks passed!")
        return 0
    else:
        print("❌ Some code quality checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
