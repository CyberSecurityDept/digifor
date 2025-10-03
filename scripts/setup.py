"""
Setup Script
Setup the project for development
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
        result = subprocess.run(cmd, check=True, shell=True)
        print(f"✅ {description} completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e}")
        return False

def main():
    """Setup project"""
    print("🚀 Setting up project...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Commands to run
    commands = [
        ("pip install -r requirements_new.txt", "Installing dependencies"),
        ("python -m pip install --upgrade pip", "Upgrading pip"),
        ("python -m pip install -e .", "Installing project in development mode"),
    ]
    
    all_passed = True
    
    for cmd, description in commands:
        if not run_command(cmd, description):
            all_passed = False
            break  # Stop on first failure
    
    if all_passed:
        print("✅ Project setup completed successfully!")
        print("🚀 You can now run:")
        print("  - python scripts/dev.py (development server)")
        print("  - python scripts/prod.py (production server)")
        print("  - python scripts/run_tests.py (run tests)")
        print("  - python scripts/lint.py (run linting)")
        print("  - python scripts/format.py (format code)")
        return 0
    else:
        print("❌ Project setup failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
