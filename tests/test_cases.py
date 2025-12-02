#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://172.15.4.26"

def get_auth_token():
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
            return response.json()['access_token']
        else:
            return None
    except Exception as e:
        print(f" Authentication error: {e}")
        return None

def test_create_case():
    print(" Testing case creation...")
    
    token = get_auth_token()
    if not token:
        print(" Cannot proceed without authentication token")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    case_data = {
        "case_number": "TEST-CASE-001",
        "title": "Test Case for API Testing",
        "description": "This is a test case created by automated testing",
        "case_type": "criminal",
        "priority": "high",
        "jurisdiction": "Jakarta",
        "case_officer": "John Doe",
        "tags": {"category": "test", "status": "active"}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/cases/",
            headers=headers,
            json=case_data
        )
        
        if response.status_code == 200:
            case = response.json()
            print("Case created successfully")
            print(f"   Case ID: {case['id']}")
            print(f"   Case Number: {case['case_number']}")
            print(f"   Title: {case['title']}")
            return case['id']
        else:
            print(f" Case creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f" Case creation error: {e}")
        return None

def test_get_case(case_id):
    print(f"\n Testing get case {case_id}...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/cases/{case_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            case = response.json()
            print("Get case successful")
            print(f"   Case Number: {case['case_number']}")
            print(f"   Status: {case['status']}")
            return True
        else:
            print(f" Get case failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Get case error: {e}")
        return False

def test_list_cases():
    print("\n Testing list cases...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/cases/",
            headers=headers
        )
        
        if response.status_code == 200:
            cases = response.json()
            print("List cases successful")
            print(f"   Total cases: {len(cases)}")
            return True
        else:
            print(f" List cases failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" List cases error: {e}")
        return False

def test_update_case(case_id):
    print(f"\n Testing update case {case_id}...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    update_data = {
        "status": "in_progress",
        "notes": "Updated via automated testing",
        "priority": "critical"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/v1/cases/{case_id}",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            case = response.json()
            print("Update case successful")
            print(f"   New status: {case['status']}")
            print(f"   New priority: {case['priority']}")
            return True
        else:
            print(f" Update case failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Update case error: {e}")
        return False

def test_add_person(case_id):
    print(f"\n Testing add person to case {case_id}...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    person_data = {
        "person_type": "suspect",
        "full_name": "Test Suspect",
        "phone": "08123456789",
        "email": "suspect@test.com",
        "description": "Test suspect for automated testing",
        "is_primary": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/cases/{case_id}/persons",
            headers=headers,
            json=person_data
        )
        
        if response.status_code == 200:
            person = response.json()
            print("Add person successful")
            print(f"   Person ID: {person['id']}")
            print(f"   Name: {person['full_name']}")
            print(f"   Type: {person['person_type']}")
            return person['id']
        else:
            print(f" Add person failed: {response.status_code}")
            return None
    except Exception as e:
        print(f" Add person error: {e}")
        return None

def test_get_case_persons(case_id):
    print(f"\n Testing get case persons for case {case_id}...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/cases/{case_id}/persons",
            headers=headers
        )
        
        if response.status_code == 200:
            persons = response.json()
            print("Get case persons successful")
            print(f"   Total persons: {len(persons)}")
            return True
        else:
            print(f" Get case persons failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Get case persons error: {e}")
        return False

def test_get_case_stats(case_id):
    print(f"\nTesting get case stats for case {case_id}...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/cases/{case_id}/stats",
            headers=headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            print("Get case stats successful")
            print(f"   Evidence count: {stats['evidence_count']}")
            print(f"   Analysis count: {stats['analysis_count']}")
            print(f"   Analysis progress: {stats['analysis_progress']}%")
            return True
        else:
            print(f" Get case stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Get case stats error: {e}")
        return False

def test_case_filters():
    print("\nTesting case filters...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/cases/?status=in_progress",
            headers=headers
        )
        
        if response.status_code == 200:
            cases = response.json()
            print("Status filter successful")
            print(f"   Cases with 'in_progress' status: {len(cases)}")
        else:
            print(f" Status filter failed: {response.status_code}")
    except Exception as e:
        print(f" Status filter error: {e}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/cases/?priority=high",
            headers=headers
        )
        
        if response.status_code == 200:
            cases = response.json()
            print("Priority filter successful")
            print(f"   Cases with 'high' priority: {len(cases)}")
        else:
            print(f" Priority filter failed: {response.status_code}")
    except Exception as e:
        print(f" Priority filter error: {e}")
    
    return True

def main():
    print(" Starting Case Management Tests...")
    print("=" * 50)
    
    case_id = test_create_case()
    if not case_id:
        print(" Cannot proceed without case ID")
        return
    
    test_get_case(case_id)
    
    test_list_cases()
    
    test_update_case(case_id)
    
    person_id = test_add_person(case_id)
    
    test_get_case_persons(case_id)
    
    test_get_case_stats(case_id)
    
    test_case_filters()
    
    print("\n" + "=" * 50)
    print(" Case Management Tests completed!")
    print(f" Test case ID: {case_id}")
    if person_id:
        print(f" Test person ID: {person_id}")

if __name__ == "__main__":
    main()
