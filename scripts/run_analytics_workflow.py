#!/usr/bin/env python3
import requests
import json
import os
import sys
import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 30

class AnalyticsWorkflow:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        
        # Store IDs for workflow
        self.file_id = None
        self.device_id = None
        self.analytic_id = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_server(self):
        """Check if server is running"""
        try:
            response = self.session.get(f"{self.base_url.replace('/api/v1', '')}/health")
            if response.status_code == 200:
                self.log("Server is running and healthy")
                return True
            else:
                self.log(f"Server health check failed: {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"Server is not running: {e}", "ERROR")
            return False
    
    def upload_file(self, file_path, file_name, tools):
        """Upload file untuk analisis"""
        self.log(f"Uploading file: {file_name}")
        
        if not os.path.exists(file_path):
            self.log(f"File not found: {file_path}", "ERROR")
            return False
            
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'file_name': file_name,
                    'tools': tools
                }
                response = self.session.post(f"{self.base_url}/analytics/upload-data", files=files, data=data)
                
            if response.status_code == 200:
                result = response.json()
                self.file_id = result['data']['file_id']
                self.log(f"File uploaded successfully. File ID: {self.file_id}")
                return True
            else:
                self.log(f"Upload failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Upload error: {e}", "ERROR")
            return False
    
    def add_device(self, owner_name, phone_number, file_id=None):
        if file_id is None:
            file_id = self.file_id
            
        if file_id is None:
            self.log("No file ID available", "ERROR")
            return False
            
        self.log(f"Adding device for owner: {owner_name}")
        
        try:
            data = {
                'owner_name': owner_name,
                'phone_number': phone_number,
                'file_id': file_id
            }
            response = self.session.post(f"{self.base_url}/analytics/device/add-device", data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.device_id = result['data']['device_id']
                self.log(f"Device added successfully. Device ID: {self.device_id}")
                return True
            else:
                self.log(f"Add device failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Add device error: {e}", "ERROR")
            return False
    
    def create_analytic(self, name, description, method, device_ids=None):
        """Buat analytic baru"""
        if device_ids is None:
            device_ids = [self.device_id] if self.device_id else []
            
        if not device_ids:
            self.log("No device IDs available", "ERROR")
            return False
            
        self.log(f"Creating analytic: {name}")
        
        try:
            data = {
                'name': name,
                'description': description,
                'method': method,
                'device_ids': device_ids
            }
            response = self.session.post(f"{self.base_url}/analytics/create-analytic-with-devices", json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.analytic_id = result['data']['analytic_id']
                self.log(f"Analytic created successfully. Analytic ID: {self.analytic_id}")
                return True
            else:
                self.log(f"Create analytic failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Create analytic error: {e}", "ERROR")
            return False
    
    def run_contact_correlation(self, analytic_id=None):
        if analytic_id is None:
            analytic_id = self.analytic_id
            
        if analytic_id is None:
            self.log("No analytic ID available", "ERROR")
            return False
            
        self.log(f"Running contact correlation for analytic ID: {analytic_id}")
        
        try:
            data = {'analytic_id': analytic_id}
            response = self.session.post(f"{self.base_url}/analytic/{analytic_id}/contact-correlation", json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.log("Contact correlation analysis completed successfully")
                
                # Display results
                devices = result['data']['devices']
                correlations = result['data']['correlations']
                
                self.log(f"Devices analyzed: {len(devices)}")
                for device in devices:
                    self.log(f"  - {device['device_label']}: {device['owner_name']} ({device['phone_number']})")
                
                self.log(f"Correlations found: {len(correlations)}")
                for correlation in correlations:
                    self.log(f"  - {correlation['contact_name']} ({correlation['phone_number']}) found in {len(correlation['devices_found_in'])} devices")
                
                return result
            else:
                self.log(f"Contact correlation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Contact correlation error: {e}", "ERROR")
            return False
    
    def export_pdf(self, analytic_id=None, output_path=None):
        """Export hasil ke PDF"""
        if analytic_id is None:
            analytic_id = self.analytic_id
            
        if analytic_id is None:
            self.log("No analytic ID available", "ERROR")
            return False
            
        self.log(f"Exporting PDF for analytic ID: {analytic_id}")
        
        try:
            response = self.session.get(f"{self.base_url}/analytic/{analytic_id}/export-pdf")
            
            if response.status_code == 200:
                if output_path is None:
                    output_path = f"contact_correlation_report_{analytic_id}.pdf"
                    
                with open(output_path, "wb") as f:
                    f.write(response.content)
                    
                self.log(f"PDF exported successfully: {output_path}")
                return True
            else:
                self.log(f"PDF export failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"PDF export error: {e}", "ERROR")
            return False
    
    def get_all_files(self):
        try:
            response = self.session.get(f"{self.base_url}/analytics/files/all")
            if response.status_code == 200:
                result = response.json()
                self.log(f"Retrieved {len(result['data'])} files")
                return result['data']
            else:
                self.log(f"Get files failed: {response.status_code}", "ERROR")
                return []
        except Exception as e:
            self.log(f"Get files error: {e}", "ERROR")
            return []
    
    def get_all_devices(self):
        try:
            response = self.session.get(f"{self.base_url}/analytics/device/get-all-devices")
            if response.status_code == 200:
                result = response.json()
                self.log(f"Retrieved {len(result['data'])} devices")
                return result['data']
            else:
                self.log(f"Get devices failed: {response.status_code}", "ERROR")
                return []
        except Exception as e:
            self.log(f"Get devices error: {e}", "ERROR")
            return []
    
    def get_all_analytics(self):
        try:
            response = self.session.get(f"{self.base_url}/analytics/get-all-analytics")
            if response.status_code == 200:
                result = response.json()
                self.log(f"Retrieved {len(result['data'])} analytics")
                return result['data']
            else:
                self.log(f"Get analytics failed: {response.status_code}", "ERROR")
                return []
        except Exception as e:
            self.log(f"Get analytics error: {e}", "ERROR")
            return []

def main():
    print("=" * 60)
    print("FORENLYTIC ANALYTICS WORKFLOW")
    print("=" * 60)
    
    # Initialize workflow
    workflow = AnalyticsWorkflow()
    
    # Check server
    if not workflow.check_server():
        print("Please start the server first: ./scripts/start.sh")
        sys.exit(1)
    
    # Example workflow
    print("\n1. Uploading sample file...")
    sample_file = "sample_dataset/contacts_sample.xlsx"
    if os.path.exists(sample_file):
        if not workflow.upload_file(sample_file, "contacts_sample.xlsx", "oxygen"):
            sys.exit(1)
    else:
        print(f"Sample file not found: {sample_file}")
        print("Please provide a file path:")
        file_path = input("File path: ").strip()
        if not workflow.upload_file(file_path, os.path.basename(file_path), "oxygen"):
            sys.exit(1)
    
    print("\n2. Adding device...")
    owner_name = input("Owner name (default: John Doe): ").strip() or "John Doe"
    phone_number = input("Phone number (default: 081234567890): ").strip() or "081234567890"
    
    if not workflow.add_device(owner_name, phone_number):
        sys.exit(1)
    
    print("\n3. Creating analytic...")
    analytic_name = input("Analytic name (default: Contact Correlation Analysis): ").strip() or "Contact Correlation Analysis"
    analytic_description = input("Analytic description (default: Analysis of contact correlations): ").strip() or "Analysis of contact correlations"
    
    if not workflow.create_analytic(analytic_name, analytic_description, "Contact Correlation"):
        sys.exit(1)
    
    print("\n4. Running contact correlation...")
    correlation_result = workflow.run_contact_correlation()
    if not correlation_result:
        sys.exit(1)
    
    print("\n5. Exporting PDF...")
    export_pdf = input("Export PDF? (y/n, default: y): ").strip().lower()
    if export_pdf != 'n':
        if not workflow.export_pdf():
            print("PDF export failed, but analysis completed successfully")
    
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    # Display summary
    print(f"File ID: {workflow.file_id}")
    print(f"Device ID: {workflow.device_id}")
    print(f"Analytic ID: {workflow.analytic_id}")
    
    if correlation_result:
        correlations = correlation_result['data']['correlations']
        print(f"Correlations found: {len(correlations)}")
        
        if correlations:
            print("\nCorrelation Details:")
            for i, corr in enumerate(correlations, 1):
                print(f"{i}. {corr['contact_name']} ({corr['phone_number']})")
                for device in corr['devices_found_in']:
                    print(f"   - {device['device_label']}: {device['owner_name']}")

if __name__ == "__main__":
    main()
