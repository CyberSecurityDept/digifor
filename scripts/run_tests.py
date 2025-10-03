"""
Test Runner Script
Run all tests with proper configuration
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run all tests"""
    print("🧪 Running tests...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Run pytest with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=app",  # Coverage report
        "--cov-report=html",  # HTML coverage report
        "--cov-report=term-missing",  # Show missing lines
        "--cov-fail-under=80",  # Fail if coverage below 80%
        "-x",  # Stop on first failure
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ All tests passed!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed with exit code {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(main())
