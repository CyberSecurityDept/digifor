"""
Code Formatting Script
Format code with black and isort
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
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Format code"""
    print("🔧 Formatting code...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Commands to run
    commands = [
        (["python", "-m", "black", "app/"], "Black formatting"),
        (["python", "-m", "isort", "app/"], "Import sorting"),
    ]
    
    all_passed = True
    
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
    
    if all_passed:
        print("✅ Code formatting completed!")
        return 0
    else:
        print("❌ Code formatting failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
