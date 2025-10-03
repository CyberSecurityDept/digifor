"""
Run All Scripts
Run all development tasks
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_script(script_name, description):
    """Run a script and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"✅ {description} completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False

def main():
    """Run all development tasks"""
    print("🚀 Running all development tasks...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Scripts to run
    scripts = [
        ("scripts/format.py", "Code formatting"),
        ("scripts/lint.py", "Code linting"),
        ("scripts/run_tests.py", "Running tests"),
    ]
    
    all_passed = True
    
    for script, description in scripts:
        if not run_script(script, description):
            all_passed = False
            break  # Stop on first failure
    
    if all_passed:
        print("✅ All development tasks completed successfully!")
        return 0
    else:
        print("❌ Some development tasks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
