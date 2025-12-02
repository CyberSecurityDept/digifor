#!/usr/bin/env python3
import requests
import json
import os
import time
from pathlib import Path

BASE_URL = "http://172.15.4.26"
DATASET_PATH = "sample_dataset"

SAMPLE_FILES = [
    {
        "file_path": f"{DATASET_PATH}/Oxygen Forensics - iOS Image CCC.xlsx",
        "file_name": "Oxygen Forensics - iOS Image CCC.xlsx",
        "notes": "iOS forensic report from Oxygen",
        "type": "Handphone",
        "tools": "Oxygen"
    },
    {
        "file_path": f"{DATASET_PATH}/Oxygen Forensics - Android Image CCC.xlsx",
        "file_name": "Oxygen Forensics - Android Image CCC.xlsx", 
        "notes": "Android forensic report from Oxygen",
        "type": "Handphone",
        "tools": "Oxygen"
    },
    {
        "file_path": f"{DATASET_PATH}/Magnet Axiom Report - CCC.xlsx",
        "file_name": "Magnet Axiom Report - CCC.xlsx",
        "notes": "Magnet Axiom forensic report",
        "type": "Handphone",
        "tools": "Magnet Axiom"
    }
]

SAMPLE_DEVICES = [
    {
        "owner_name": "Bambang Ajriman",
        "phone_number": "082121200905",
        "file_id": 1
    },
    {
        "owner_name": "Riko Suloyo",
        "phone_number": "089660149979", 
        "file_id": 2
    },
    {
        "owner_name": "Andika",
        "phone_number": "08112157462",
        "file_id": 3
    }
]

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {title}")
    print(f"{'='*60}")

def print_response(response, title="Response"):
    print(f"\n{title}:")
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except:
        print(f"Response: {response.text}")
        return None

def upload_file(file_path, notes, file_type, file_name, tools):
    if not os.path.exists(file_path):
        print(f" File not found: {file_path}")
        return None
    
    url = f"{BASE_URL}/api/v1/analytics/upload-data"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'file_name': file_name,
            'notes': notes,
            'type': file_type,
            'tools': tools
        }
        
        response = requests.post(url, files=files, data=data)
        return print_response(response, f"Upload {os.path.basename(file_path)}")

def get_all_files():
    url = f"{BASE_URL}/api/v1/analytics/files/all"
    response = requests.get(url)
    return print_response(response, "Get All Files")


def add_device(owner_name, phone_number, file_id):
    url = f"{BASE_URL}/api/v1/analytics/add-device"
    
    data = {
        "file_id": file_id,
        "owner_name": owner_name,
        "phone_number": phone_number
    }
    
    response = requests.post(url, data=data)
    return print_response(response, f"Add Device: {owner_name}")

def create_analytic(analytic_name, method, notes, device_ids):
    url = f"{BASE_URL}/api/v1/analytics/create-analytic-with-devices"
    
    payload = {
        "analytic_name": analytic_name,
        "method": method,
        "notes": notes,
        "device_ids": device_ids
    }
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return print_response(response, "Create Analytic")

def get_all_analytics():
    url = f"{BASE_URL}/api/v1/analytics/get-all-analytic"
    response = requests.get(url)
    return print_response(response, "Get All Analytics")

def run_contact_correlation(analytic_id):
    url = f"{BASE_URL}/api/v1/analytic/{analytic_id}/contact-correlation"
    response = requests.get(url)
    return print_response(response, "Contact Correlation Analysis")

def export_contact_correlation_pdf(analytic_id):
    url = f"{BASE_URL}/api/v1/analytics/analytic/{analytic_id}/contact-correlation/export-pdf"
    response = requests.get(url)
    
    if response.status_code == 200:
        filename = f"contact_correlation_report_{analytic_id}.pdf"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"\n PDF exported successfully: {filename}")
        return filename
    else:
        print(f"\n Failed to export PDF: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    print(" Starting Forenlytic Complete Workflow")
    print(f"Base URL: {BASE_URL}")
    print(f"Dataset Path: {DATASET_PATH}")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print(" Server is not running. Please start the server first.")
            return
    except:
        print(" Cannot connect to server. Please start the server first.")
        return
    
    print(" Server is running")
    
    print_step(1, "UPLOAD FILES")
    uploaded_files = []
    
    for i, file_info in enumerate(SAMPLE_FILES, 1):
        print(f"\n Uploading file {i}/{len(SAMPLE_FILES)}: {file_info['file_path']}")
        result = upload_file(
            file_info['file_path'],
            file_info['notes'],
            file_info['type'],
            file_info['file_name'],
            file_info['tools']
        )
        
        if result and result.get('status') == 200:
            file_id = result.get('data', {}).get('file_id')
            uploaded_files.append(file_id)
            print(f" File uploaded successfully with ID: {file_id}")
        else:
            print(f" Failed to upload file: {file_info['file_path']}")
    
    if not uploaded_files:
        print(" No files uploaded successfully. Exiting.")
        return
    
    print_step(2, "VIEW ALL FILES")
    get_all_files()
    
    print_step(3, "ADD DEVICES")
    device_ids = []
    
    for i, device_info in enumerate(SAMPLE_DEVICES, 1):
        print(f"\n Adding device {i}/{len(SAMPLE_DEVICES)}: {device_info['owner_name']}")
        result = add_device(
            device_info['owner_name'],
            device_info['phone_number'],
            device_info['file_id']
        )
        
        if result and result.get('status') == 200:
            device_data = result.get('data', {})
            if isinstance(device_data, list) and device_data:
                first_item = device_data[0]
                if isinstance(first_item, dict):
                    device_id = first_item.get('device_id')
                else:
                    device_id = None
            elif isinstance(device_data, dict):
                device_id = device_data.get('device_id')
            else:
                device_id = None
            
            if device_id:
                device_ids.append(device_id)
                print(f" Device added successfully with ID: {device_id}")
            else:
                print(" Failed to get device ID from response")
        else:
            print(f" Failed to add device: {device_info['owner_name']}")
    
    if not device_ids:
        print(" No devices added successfully. Exiting.")
        return
    
    print_step(4, "CREATE ANALYTIC")
    result = create_analytic(
        "Contact Correlation Analysis - Case 123",
        "Contact Correlation",
        "Analysis of contact correlations between suspects",
        device_ids
    )
    
    analytic_id = None
    if result and result.get('status') == 200:
        analytic_id = result.get('data', {}).get('analytic', {}).get('id')
        print(f" Analytic created successfully with ID: {analytic_id}")
    else:
        print(" Failed to create analytic. Exiting.")
        return
    
    print_step(5, "VIEW ALL ANALYTICS")
    get_all_analytics()
    
    print_step(6, "CONTACT CORRELATION ANALYSIS")
    result = run_contact_correlation(analytic_id)
    
    if result and result.get('status') == 200:
        correlations = result.get('data', {}).get('correlations', [])
        devices = result.get('data', {}).get('devices', [])
        
        print(f"\n Analysis Results:")
        print(f"   - Total Devices: {len(devices)}")
        print(f"   - Total Correlations: {len(correlations)}")
        
        if correlations:
            print(f"\n Found {len(correlations)} correlations:")
            for i, corr in enumerate(correlations, 1):
                print(f"   {i}. Phone: {corr.get('contact_number')}")
                for device in corr.get('devices_found_in', []):
                    print(f"      - {device.get('device_label')}: {device.get('contact_name')}")
        else:
            print("\n No cross-device correlations found (this is normal for different people)")
    else:
        print(" Failed to run contact correlation analysis")
        return
    
    print_step(7, "EXPORT TO PDF")
    pdf_file = export_contact_correlation_pdf(analytic_id)
    
    print(f"\n{'='*60}")
    print(" WORKFLOW COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f" Files Uploaded: {len(uploaded_files)}")
    print(f" Devices Created: {len(device_ids)}")
    print(f" Analytic Created: {analytic_id}")
    print(f" Correlations Found: {len(correlations) if 'correlations' in locals() else 0}")
    if pdf_file:
        print(f" PDF Exported: {pdf_file}")
    
    print(f"\n All steps completed successfully!")
    print(f" You can also test the API using Postman collection:")
    print(f"   docs/Forenlytic_Complete_Workflow.postman_collection.json")

if __name__ == "__main__":
    main()
