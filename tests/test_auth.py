#!/usr/bin/env python3
"""
Authentication Tests for Forenlytic Backend
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
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_register_user():
    """Test user registration"""
    print("\n👤 Testing user registration...")
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass123",
        "role": "investigator"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data
        )
        
        if response.status_code == 200:
            print("✅ User registration successful")
            print(f"   User: {response.json()['username']}")
            return True
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ User registration error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n🔐 Testing user login...")
    
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

def test_get_user_info(token):
    """Test get user info"""
    print("\n👤 Testing get user info...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers=headers
        )
        
        if response.status_code == 200:
            user_info = response.json()
            print("✅ Get user info successful")
            print(f"   Username: {user_info['username']}")
            print(f"   Role: {user_info['role']}")
            return True
        else:
            print(f"❌ Get user info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get user info error: {e}")
        return False

def test_refresh_token(token):
    """Test token refresh"""
    print("\n🔄 Testing token refresh...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/refresh",
            headers=headers
        )
        
        if response.status_code == 200:
            new_token_data = response.json()
            print("✅ Token refresh successful")
            print(f"   New token type: {new_token_data['token_type']}")
            return True
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Token refresh error: {e}")
        return False

def test_invalid_credentials():
    """Test invalid credentials"""
    print("\n❌ Testing invalid credentials...")
    
    login_data = {
        "username": "invalid",
        "password": "wrongpass"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/token",
            data=login_data
        )
        
        if response.status_code == 401:
            print("✅ Invalid credentials properly rejected")
            return True
        else:
            print(f"❌ Invalid credentials not properly handled: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid credentials test error: {e}")
        return False

def main():
    """Main authentication test function"""
    print("🔐 Starting Authentication Tests...")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("❌ Cannot proceed without health check")
        return
    
    # Test user registration
    test_register_user()
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    # Test get user info
    test_get_user_info(token)
    
    # Test token refresh
    test_refresh_token(token)
    
    # Test invalid credentials
    test_invalid_credentials()
    
    print("\n" + "=" * 50)
    print("🎯 Authentication Tests completed!")

if __name__ == "__main__":
    main()
