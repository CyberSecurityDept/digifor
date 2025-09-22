#!/usr/bin/env python3
"""
Forenlytic Backend API Testing Script
"""
import requests
import json
import time

# API Base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_auth():
    """Test authentication"""
    print("\n🔐 Testing authentication...")
    
    # Test login
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/token",
            data=login_data
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Login successful")
            print(f"   Token type: {token_data['token_type']}")
            return token_data['access_token']
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_cases(token):
    """Test case management"""
    print("\n📁 Testing case management...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test create case
    case_data = {
        "case_number": "TEST-001",
        "title": "Test Case",
        "description": "Test case for API testing",
        "case_type": "criminal",
        "priority": "high",
        "jurisdiction": "Jakarta",
        "case_officer": "John Doe"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/cases/",
            headers=headers,
            json=case_data
        )
        
        if response.status_code == 200:
            case = response.json()
            print("✅ Case created successfully")
            print(f"   Case ID: {case['id']}")
            print(f"   Case Number: {case['case_number']}")
            return case['id']
        else:
            print(f"❌ Case creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Case creation error: {e}")
        return None

def test_case_operations(token, case_id):
    """Test case operations"""
    print("\n🔧 Testing case operations...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get case
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/cases/{case_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Get case successful")
        else:
            print(f"❌ Get case failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get case error: {e}")
    
    # Test update case
    update_data = {
        "status": "in_progress",
        "notes": "Updated via API test"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/v1/cases/{case_id}",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            print("✅ Update case successful")
        else:
            print(f"❌ Update case failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Update case error: {e}")
    
    # Test add person
    person_data = {
        "person_type": "suspect",
        "full_name": "Test Suspect",
        "phone": "08123456789",
        "email": "suspect@test.com",
        "is_primary": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/cases/{case_id}/persons",
            headers=headers,
            json=person_data
        )
        
        if response.status_code == 200:
            print("✅ Add person successful")
        else:
            print(f"❌ Add person failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Add person error: {e}")
    
    # Test get case stats
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/cases/{case_id}/stats",
            headers=headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Get case stats successful")
            print(f"   Evidence count: {stats['evidence_count']}")
            print(f"   Analysis count: {stats['analysis_count']}")
        else:
            print(f"❌ Get case stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Get case stats error: {e}")

def test_reports(token, case_id):
    """Test report generation"""
    print("\n📄 Testing report generation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test generate comprehensive report
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/generate?report_type=comprehensive",
            headers=headers
        )
        
        if response.status_code == 200:
            report_data = response.json()
            print("✅ Generate comprehensive report successful")
            print(f"   Filename: {report_data['filename']}")
        else:
            print(f"❌ Generate report failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Generate report error: {e}")
    
    # Test list reports
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/reports",
            headers=headers
        )
        
        if response.status_code == 200:
            reports = response.json()
            print("✅ List reports successful")
            print(f"   Total reports: {reports['total_reports']}")
        else:
            print(f"❌ List reports failed: {response.status_code}")
    except Exception as e:
        print(f"❌ List reports error: {e}")

def main():
    """Main testing function"""
    print("🚀 Starting Forenlytic Backend API Tests...")
    print("=" * 50)
    
    # Test health
    test_health()
    
    # Test authentication
    token = test_auth()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    # Test case management
    case_id = test_cases(token)
    if not case_id:
        print("❌ Cannot proceed without case ID")
        return
    
    # Test case operations
    test_case_operations(token, case_id)
    
    # Test reports
    test_reports(token, case_id)
    
    print("\n" + "=" * 50)
    print("🎯 API Testing completed!")
    print(f"📖 API Documentation: {BASE_URL}/docs")
    print(f"📚 ReDoc: {BASE_URL}/redoc")

if __name__ == "__main__":
    main()
