#!/usr/bin/env python3
"""
Script untuk test upload-progress endpoint
"""
import sys
import os
import requests
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_upload_progress():
    """Test upload-progress endpoint"""
    print("="*60)
    print("UPLOAD PROGRESS TEST")
    print("="*60)
    
    # Test dengan upload_id yang tidak ada (should return 404)
    print("\n1. Testing with non-existent upload_id...")
    test_upload_id = "test_upload_12345"
    api_url = "http://172.15.2.105:8000"
    
    try:
        response = requests.get(
            f"{api_url}/api/v1/analytics/upload-progress",
            params={"upload_id": test_upload_id, "type": "data"},
            timeout=5
        )
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ Endpoint berfungsi (return 404 for non-existent ID)")
        else:
            print(f"   Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to API server")
        print("   Make sure the service is running on http://172.15.2.105:8000")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test endpoint accessibility
    print("\n2. Testing endpoint accessibility...")
    try:
        response = requests.get(f"{api_url}/health/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ API server is accessible")
        else:
            print(f"   ⚠️  API server returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Cannot access API server: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ Upload-progress endpoint test completed")
    print("="*60)
    print("\nNote: Upload-progress menggunakan in-memory storage")
    print("      Tidak memerlukan Redis untuk tracking progress")
    print("      Redis hanya digunakan untuk Celery task queue (jika ada)")
    return True

if __name__ == "__main__":
    success = test_upload_progress()
    sys.exit(0 if success else 1)

