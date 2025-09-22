#!/usr/bin/env python3
"""
Test Runner for Forenlytic Backend
"""
import subprocess
import sys
import time
import os

def run_test(test_file):
    """Run a specific test file"""
    print(f"\n🧪 Running {test_file}...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print(f"✅ {test_file} passed")
            print(result.stdout)
            return True
        else:
            print(f"❌ {test_file} failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False

def check_server():
    """Check if server is running"""
    import requests
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print("❌ Server is not responding properly")
            return False
    except Exception as e:
        print(f"❌ Server check failed: {e}")
        return False

def main():
    """Main test runner function"""
    print("🚀 Forenlytic Backend Test Runner")
    print("=" * 50)
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    if not check_server():
        print("❌ Server is not running. Please start the server first:")
        print("   ./run.sh")
        print("   or")
        print("   ./scripts/start_backend.sh")
        return
    
    # List of test files to run
    test_files = [
        "test_auth.py",
        "test_cases.py", 
        "test_reports.py",
        "test_api.py"  # Original comprehensive test
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for test_file in test_files:
        if os.path.exists(test_file):
            if run_test(test_file):
                passed += 1
            else:
                failed += 1
        else:
            print(f"⚠️ Test file {test_file} not found, skipping...")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {failed} test(s) failed")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
