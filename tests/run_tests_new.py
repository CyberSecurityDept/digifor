"""
Test Runner
Run all tests with proper configuration
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([
        "tests/",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--cov=app",  # Coverage report
        "--cov-report=html",  # HTML coverage report
        "--cov-report=term-missing",  # Show missing lines
        "--cov-fail-under=80",  # Fail if coverage below 80%
        "-x",  # Stop on first failure
    ])
