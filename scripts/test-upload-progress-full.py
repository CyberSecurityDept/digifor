#!/usr/bin/env python3
import sys, os, requests, json, time, datetime, traceback
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def format_timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def test_upload_progress_full():
    """Test upload-progress endpoint dengan upload file dan polling"""
    print("="*80)
    print("UPLOAD PROGRESS FULL TEST")
    print("="*80)
    
    api_url = "http://172.15.2.105:8000"
    
    # Step 1: Upload file
    print(f"\n[{format_timestamp()}] Step 1: Uploading file...")
    
    # Create a test file
    test_file_path = "/tmp/test_upload.xlsx"
    if not os.path.exists(test_file_path):
        # Create a minimal Excel file (or use existing test file)
        print(f"Test file not found: {test_file_path}")
        print("   Please provide a test file path")
        test_file_path = input("   Enter test file path (or press Enter to skip upload test): ").strip()
        if not test_file_path:
            print("   Skipping upload test...")
            return test_progress_only(api_url)
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'file_name': 'test_upload_progress.xlsx',
                'notes': 'Testing upload progress',
                'type': 'Handphone',
                'tools': 'Cellebrite',
                'method': 'Hashfile Analytics'
            }
            
            print(f"   Uploading {test_file_path}...")
            response = requests.post(
                f"{api_url}/api/v1/analytics/upload-data",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Upload failed: {response.status_code}")
                print(f"   Response: {response.json()}")
                return False
            
            upload_response = response.json()
            upload_id = upload_response.get("data", {}).get("upload_id")
            
            if not upload_id:
                print(f"No upload_id in response: {upload_response}")
                return False
            
            print(f"Upload initiated")
            print(f"Upload ID: {upload_id}")
            print(f"Status: {upload_response.get('data', {}).get('status_upload', 'Unknown')}")
    
    except Exception as e:
        print(f"Upload error: {e}")
        
        traceback.print_exc()
        return False
    
    # Step 2: Poll progress endpoint
    print(f"\n[{format_timestamp()}] Step 2: Polling progress endpoint...")
    print(f"   Polling every 0.5 seconds...")
    print("-" * 80)
    
    status_history = []
    max_polls = 120  # 60 seconds max
    poll_count = 0
    last_status = None
    
    while poll_count < max_polls:
        try:
            response = requests.get(
                f"{api_url}/api/v1/analytics/upload-progress",
                params={"upload_id": upload_id, "type": "data"},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"\nError: {response.status_code}")
                print(f"   Response: {response.text}")
                break
            
            result = response.json()
            current_status = result.get("status")
            percentage = result.get("percentage", 0)
            message = result.get("message", "")
            
            # Only print if status changed
            if current_status != last_status or poll_count % 10 == 0:
                timestamp = format_timestamp()
                status_info = f"[{timestamp}] Status: {current_status:8} | Percentage: {percentage:3}% | Message: {message}"
                print(status_info)
                
                status_history.append({
                    "timestamp": timestamp,
                    "status": current_status,
                    "percentage": percentage,
                    "message": message,
                    "poll_count": poll_count
                })
            
            last_status = current_status
            
            # Stop if Success or Failed
            if current_status == "Success":
                print(f"\nUpload completed successfully!")
                break
            elif current_status == "Failed":
                print(f"\nUpload failed!")
                break
            
            time.sleep(0.5)
            poll_count += 1
            
        except requests.exceptions.Timeout:
            print(f"\nTimeout waiting for response")
            break
        except Exception as e:
            print(f"\nError polling: {e}")
            break
    
    # Step 3: Summary
    print("\n" + "="*80)
    print("STATUS HISTORY SUMMARY")
    print("="*80)
    
    if status_history:
        print(f"\nTotal status changes: {len(status_history)}")
        print(f"Total polls: {poll_count}")
        
        # Group by status
        status_counts = {}
        for entry in status_history:
            status = entry["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("\nStatus distribution:")
        for status, count in status_counts.items():
            print(f"  - {status}: {count} times")
        
        # Check if we saw Progress status
        saw_pending = any(e["status"] == "Pending" for e in status_history)
        saw_progress = any(e["status"] == "Progress" for e in status_history)
        saw_success = any(e["status"] == "Success" for e in status_history)
        
        print("\nStatus transitions:")
        if saw_pending:
            print("Saw Pending status")
        else:
            print("Never saw Pending status")
        
        if saw_progress:
            print("Saw Progress status")
        else:
            print("Never saw Progress status - THIS IS THE PROBLEM!")
        
        if saw_success:
            print("Saw Success status")
        else:
            print("Never saw Success status")
        
        # Show first and last status
        if len(status_history) > 0:
            print(f"\nFirst status: {status_history[0]['status']} ({status_history[0]['timestamp']})")
            print(f"Last status: {status_history[-1]['status']} ({status_history[-1]['timestamp']})")
            
            # Show all unique statuses
            unique_statuses = list(set(e["status"] for e in status_history))
            print(f"\nUnique statuses seen: {', '.join(unique_statuses)}")
            
            if len(unique_statuses) < 2:
                print("\nWARNING: Only saw one status! Expected: Pending -> Progress -> Success")
    else:
        print("\nNo status history recorded!")
    
    print("\n" + "="*80)
    return True

def test_progress_only(api_url):
    """Test progress endpoint only with existing upload_id"""
    print(f"\n[{format_timestamp()}] Testing progress endpoint with existing upload_id...")
    upload_id = input("Enter upload_id to test: ").strip()
    
    if not upload_id:
        print("   No upload_id provided, skipping...")
        return False
    
    print(f"   Polling upload_id: {upload_id}")
    print("-" * 80)
    
    status_history = []
    max_polls = 20
    poll_count = 0
    
    while poll_count < max_polls:
        try:
            response = requests.get(
                f"{api_url}/api/v1/analytics/upload-progress",
                params={"upload_id": upload_id, "type": "data"},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                break
            
            result = response.json()
            current_status = result.get("status")
            percentage = result.get("percentage", 0)
            message = result.get("message", "")
            
            timestamp = format_timestamp()
            status_info = f"[{timestamp}] Status: {current_status:8} | Percentage: {percentage:3}% | Message: {message}"
            print(status_info)
            
            status_history.append({
                "timestamp": timestamp,
                "status": current_status,
                "percentage": percentage,
                "message": message
            })
            
            if current_status in ["Success", "Failed"]:
                break
            
            time.sleep(0.5)
            poll_count += 1
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    return True

if __name__ == "__main__":
    try:
        success = test_upload_progress_full()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nest failed: {e}")
        
        traceback.print_exc()
        sys.exit(1)

