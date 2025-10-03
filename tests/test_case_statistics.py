#!/usr/bin/env python3
"""
Test script for case statistics endpoint
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_statistics_endpoint():
    """Test the case statistics endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cases/statistics/summary")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Statistics Response:")
            print(f"  - Total Cases: {data['data']['total_cases']}")
            print(f"  - Open Cases: {data['data']['open_cases']}")
            print(f"  - Closed Cases: {data['data']['closed_cases']}")
            print(f"  - Reopened Cases: {data['data']['reopened_cases']}")
            
            # Check if all required fields are present
            required_fields = ['total_cases', 'open_cases', 'closed_cases', 'reopened_cases']
            missing_fields = [field for field in required_fields if field not in data['data']]
            
            if missing_fields:
                print(f"\n❌ Missing fields: {missing_fields}")
            else:
                print("\n✅ All required fields present!")
                
        return response
    except Exception as e:
        print(f"Error testing statistics endpoint: {e}")
        return None

def main():
    """Test case statistics endpoint"""
    print("🧪 Testing Case Statistics Endpoint")
    print("=" * 50)
    
    test_statistics_endpoint()
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    main()
