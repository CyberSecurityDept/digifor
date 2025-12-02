#!/usr/bin/env python3
"""
Test script for suspect management endpoints
"""

import requests
import json
import sys

BASE_URL = "http://172.15.1.207"

def test_endpoint(url, method="GET", data=None):
    """Test an endpoint and return response"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        
        print(f"\n{'='*60}")
        print(f"Testing: {method} {url}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"{'='*60}")
        
        return response
    except Exception as e:
        print(f"Error testing {url}: {e}")
        return None

def main():
    """Test all suspect management endpoints"""
    print("🧪 Testing Suspect Management Endpoints")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        ("GET", f"{BASE_URL}/api/v1/suspects/"),
        ("GET", f"{BASE_URL}/api/v1/suspects/stats/summary"),
        ("GET", f"{BASE_URL}/api/v1/suspects/?search=john"),
        ("GET", f"{BASE_URL}/api/v1/suspects/?status=active"),
        ("GET", f"{BASE_URL}/api/v1/suspects/?risk_level=high"),
    ]
    
    for method, url in endpoints:
        test_endpoint(url, method)
    
    # Test creating a suspect
    suspect_data = {
        "full_name": "John Doe",
        "alias": "Johnny",
        "gender": "male",
        "phone_number": "+1234567890",
        "email": "john.doe@example.com",
        "status": "active",
        "risk_level": "medium",
        "is_primary_suspect": True,
        "has_criminal_record": False
    }
    
    print("\n🧪 Testing Create Suspect")
    response = test_endpoint(f"{BASE_URL}/api/v1/suspects/", "POST", suspect_data)
    
    if response and response.status_code == 201:
        suspect_id = response.json().get("data", {}).get("id")
        if suspect_id:
            print(f"\n🧪 Testing Get Suspect by ID: {suspect_id}")
            test_endpoint(f"{BASE_URL}/api/v1/suspects/{suspect_id}")
            
            print(f"\n🧪 Testing Get Suspect Evidence: {suspect_id}")
            test_endpoint(f"{BASE_URL}/api/v1/suspects/{suspect_id}/evidence")
            
            print(f"\n🧪 Testing Export PDF: {suspect_id}")
            test_endpoint(f"{BASE_URL}/api/v1/suspects/{suspect_id}/export-pdf", "POST")
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    main()
