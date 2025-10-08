#!/usr/bin/env python3
"""
Report Generation Tests for Digital Forensics Backend
"""
import requests
import json
import time

# API Base URL
BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token"""
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

def create_test_case():
    """Create a test case for report testing"""
    token = get_auth_token()
    if not token:
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    case_data = {
        "case_number": "REPORT-TEST-001",
        "title": "Report Test Case",
        "description": "Test case for report generation testing",
        "case_type": "criminal",
        "priority": "high",
        "jurisdiction": "Jakarta",
        "case_officer": "Test Officer"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/cases/",
            headers=headers,
            json=case_data
        )
        
        if response.status_code == 200:
            return response.json()['id']
        else:
            return None
    except Exception as e:
        print(f" Create test case error: {e}")
        return None

def test_generate_comprehensive_report(case_id):
    """Test generate comprehensive report"""
    print("📄 Testing comprehensive report generation...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/generate?report_type=comprehensive",
            headers=headers
        )
        
        if response.status_code == 200:
            report_data = response.json()
            print("✅ Comprehensive report generated successfully")
            print(f"   Filename: {report_data['filename']}")
            print(f"   Report type: {report_data['report_type']}")
            return True
        else:
            print(f" Comprehensive report generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f" Comprehensive report generation error: {e}")
        return False

def test_generate_summary_report(case_id):
    """Test generate summary report"""
    print("\n📋 Testing summary report generation...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/generate?report_type=summary",
            headers=headers
        )
        
        if response.status_code == 200:
            report_data = response.json()
            print("✅ Summary report generated successfully")
            print(f"   Filename: {report_data['filename']}")
            print(f"   Report type: {report_data['report_type']}")
            return True
        else:
            print(f" Summary report generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Summary report generation error: {e}")
        return False

def test_generate_evidence_report(case_id):
    """Test generate evidence report"""
    print("\n📁 Testing evidence report generation...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/generate?report_type=evidence",
            headers=headers
        )
        
        if response.status_code == 200:
            report_data = response.json()
            print("✅ Evidence report generated successfully")
            print(f"   Filename: {report_data['filename']}")
            print(f"   Report type: {report_data['report_type']}")
            return True
        else:
            print(f" Evidence report generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Evidence report generation error: {e}")
        return False

def test_generate_analysis_report(case_id):
    """Test generate analysis report"""
    print("\n🔬 Testing analysis report generation...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/generate?report_type=analysis",
            headers=headers
        )
        
        if response.status_code == 200:
            report_data = response.json()
            print("✅ Analysis report generated successfully")
            print(f"   Filename: {report_data['filename']}")
            print(f"   Report type: {report_data['report_type']}")
            return True
        else:
            print(f" Analysis report generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Analysis report generation error: {e}")
        return False

def test_list_reports(case_id):
    """Test list reports for case"""
    print(f"\n📋 Testing list reports for case {case_id}...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/reports",
            headers=headers
        )
        
        if response.status_code == 200:
            reports = response.json()
            print("✅ List reports successful")
            print(f"   Total reports: {reports['total_reports']}")
            
            for report in reports['reports']:
                print(f"   - {report['filename']} ({report['size']} bytes)")
            
            return reports['reports']
        else:
            print(f" List reports failed: {response.status_code}")
            return []
    except Exception as e:
        print(f" List reports error: {e}")
        return []

def test_get_report(case_id, filename):
    """Test get specific report"""
    print(f"\n📖 Testing get report {filename}...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/reports/{filename}",
            headers=headers
        )
        
        if response.status_code == 200:
            report_data = response.json()
            print("✅ Get report successful")
            print(f"   Report type: {report_data.get('report_type', 'unknown')}")
            print(f"   Title: {report_data.get('title', 'No title')}")
            return True
        else:
            print(f" Get report failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Get report error: {e}")
        return False

def test_delete_report(case_id, filename):
    """Test delete specific report"""
    print(f"\n🗑️ Testing delete report {filename}...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v1/reports/cases/{case_id}/reports/{filename}",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Delete report successful")
            return True
        else:
            print(f" Delete report failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Delete report error: {e}")
        return False

def test_report_stats():
    print("\n📊 Testing report statistics...")
    
    token = get_auth_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/reports/stats",
            headers=headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Get report stats successful")
            print(f"   Total reports: {stats['total_reports']}")
            print(f"   Total size: {stats['total_size']} bytes")
            print(f"   By type: {stats['by_type']}")
            return True
        else:
            print(f" Get report stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Get report stats error: {e}")
        return False

def main():
    """Main report generation test function"""
    print("📄 Starting Report Generation Tests...")
    print("=" * 50)
    
    # Create test case
    case_id = create_test_case()
    if not case_id:
        print(" Cannot proceed without test case")
        return
    
    print(f"📁 Test case ID: {case_id}")
     
    test_generate_comprehensive_report(case_id)
    test_generate_summary_report(case_id)
    test_generate_evidence_report(case_id)
    test_generate_analysis_report(case_id)
    
    reports = test_list_reports(case_id)
    
    if reports:
        test_get_report(case_id, reports[0]['filename'])
        
    
    # Test report statistics
    test_report_stats()
    
    print("\n" + "=" * 50)
    print("🎯 Report Generation Tests completed!")
    print(f"📁 Test case ID: {case_id}")

if __name__ == "__main__":
    main()
