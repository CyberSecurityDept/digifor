#!/usr/bin/env python3
import requests
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'

class ForenlyticAnalyzer:
    def __init__(self, base_url: str = "http://172.15.2.105"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session = requests.Session()
        self.analytic_id: Optional[int] = None
        self.device_ids: List[int] = []
        self.file_ids: List[int] = []
        
    def print_step(self, step: int, message: str):
        """Print step with colored output"""
        print(f"{Colors.BLUE}[STEP {step}]{Colors.NC} {message}")
        
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")
        
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")
        
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")
        
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.CYAN}[INFO]{Colors.NC} {message}")
        
    def check_server(self) -> bool:
        """Check if server is running"""
        self.print_step(0, "Checking if server is running...")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.print_success(f"Server is running at {self.base_url}")
                return True
            else:
                self.print_error(f"Server returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error("Server is not running. Please start the server first:")
            print("  source venv/bin/activate")
            print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
            return False
            
    def create_analytic(self) -> bool:
        """Create a new analytic"""
        self.print_step(1, "Creating analytic...")
        
        payload = {
            "analytic_name": "Multi-Device Forensic Analysis CCC",
            "type": "Contact Correlation",
            "method": "Deep Communication",
            "notes": "Complete analysis of 3 devices with hashfile correlation for CCC case"
        }
        
        try:
            response = self.session.post(
                f"{self.api_base}/analytics/create-analytic",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "analytic_id" in data["data"]:
                    self.analytic_id = data["data"]["analytic_id"]
                    self.print_success(f"Analytic created with ID: {self.analytic_id}")
                    self.print_info(f"Response: {json.dumps(data, indent=2)}")
                    return True
                else:
                    self.print_error("Invalid response format")
                    return False
            else:
                self.print_error(f"Failed to create analytic: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception occurred: {str(e)}")
            return False
            
    def upload_device_data(self) -> bool:
        self.print_step(2, "Uploading device data...")
        
        device_files = [
            {
                "file_path": "contoh_dataset/Oxygen Forensics - iOS Image CCC.xlsx",
                "file_name": "Oxygen Forensics - iOS Image CCC.xlsx",
                "notes": "iPhone device extraction from Oxygen Forensics",
                "type": "Handphone",
                "tools": "Oxygen"
            },
            {
                "file_path": "contoh_dataset/Oxygen Forensics - Android Image CCC.xlsx",
                "file_name": "Oxygen Forensics - Android Image CCC.xlsx",
                "notes": "Android device extraction from Oxygen Forensics",
                "type": "Handphone",
                "tools": "Oxygen"
            },
            {
                "file_path": "contoh_dataset/Magnet Axiom Report - CCC.xlsx",
                "file_name": "Magnet Axiom Report - CCC.xlsx",
                "notes": "Device extraction from Magnet Axiom",
                "type": "Handphone",
                "tools": "Magnet Axiom"
            }
        ]
        
        success_count = 0
        for i, device_file in enumerate(device_files, 1):
            self.print_step(f"2.{i}", f"Uploading {device_file['file_name']}...")
            
            if not os.path.exists(device_file["file_path"]):
                self.print_error(f"File not found: {device_file['file_path']}")
                continue
                
            try:
                with open(device_file["file_path"], "rb") as f:
                    files = {"file": f}
                    data = {
                        "file_name": device_file["file_name"],
                        "notes": device_file["notes"],
                        "type": device_file["type"],
                        "tools": device_file["tools"]
                    }
                    
                    response = self.session.post(
                        f"{self.api_base}/analytics/upload-data",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if "data" in response_data and "file_id" in response_data["data"]:
                            file_id = response_data["data"]["file_id"]
                            self.file_ids.append(file_id)
                            self.print_success(f"{device_file['file_name']} uploaded with file ID: {file_id}")
                            success_count += 1
                        else:
                            self.print_error(f"Invalid response format for {device_file['file_name']}")
                    else:
                        self.print_error(f"Failed to upload {device_file['file_name']}: {response.status_code}")
                        self.print_error(f"Response: {response.text}")
                        
            except Exception as e:
                self.print_error(f"Exception occurred while uploading {device_file['file_name']}: {str(e)}")
                
        return success_count == len(device_files)
        
    def add_devices(self) -> bool:
        """Add devices to the system"""
        self.print_step(3, "Adding devices...")
        
        device_info = [
                {
                    "file_id": self.file_ids[0] if len(self.file_ids) > 0 else None,
                    "owner_name": "Bambang Ajriman - iPhone",
                    "phone_number": "+6282121200905"
                },
                {
                    "file_id": self.file_ids[1] if len(self.file_ids) > 1 else None,
                    "owner_name": "Riko Suloyo - Android",
                    "phone_number": "+6289660149979"
                },
                {
                    "file_id": self.file_ids[2] if len(self.file_ids) > 2 else None,
                    "owner_name": "Local User - Android Devices",
                    "phone_number": "+628112157462"
                }
        ]
        
        success_count = 0
        for i, device in enumerate(device_info, 1):
            if device["file_id"] is None:
                self.print_error(f"File ID not available for device {i}")
                continue
                
            self.print_step(f"3.{i}", f"Adding device: {device['owner_name']}...")
            
            try:
                data = {
                    "file_id": device["file_id"],
                    "owner_name": device["owner_name"],
                    "phone_number": device["phone_number"]
                }
                
                response = self.session.post(
                    f"{self.api_base}/analytics/add-device",
                    data=data
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if "data" in response_data and "device_id" in response_data["data"]:
                        device_id = response_data["data"]["device_id"]
                        self.device_ids.append(device_id)
                        self.print_success(f"Device added with ID: {device_id}")
                        success_count += 1
                    else:
                        self.print_error(f"Invalid response format for device {i}")
                else:
                    self.print_error(f"Failed to add device {i}: {response.status_code}")
                    self.print_error(f"Response: {response.text}")
                    
            except Exception as e:
                self.print_error(f"Exception occurred while adding device {i}: {str(e)}")
                
        return success_count == len(device_info)
        
    def link_devices(self) -> bool:
        """Link devices to analytic"""
        self.print_step(4, "Linking devices to analytic...")
        
        if not self.analytic_id or not self.device_ids:
            self.print_error("Analytic ID or device IDs not available")
            return False
            
        try:
            payload = {"device_ids": self.device_ids}
            
            response = self.session.post(
                f"{self.api_base}/analytics/{self.analytic_id}/link-multiple-devices",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if "linked successfully" in response_data.get("message", ""):
                    self.print_success("Devices linked to analytic successfully")
                    self.print_info(f"Response: {json.dumps(response_data, indent=2)}")
                    return True
                else:
                    self.print_error("Failed to link devices")
                    return False
            else:
                self.print_error(f"Failed to link devices: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Exception occurred while linking devices: {str(e)}")
            return False
            
    def upload_hashfiles(self) -> bool:
        """Upload hashfile data"""
        self.print_step(5, "Uploading hashfiles...")
        
        hashfile_files = [
            {
                "file_path": "contoh_hashfile/Oxygen iPhone - Hashfile MD5.xls",
                "notes": "iPhone hashfile from Oxygen Forensics"
            },
            {
                "file_path": "contoh_hashfile/Oxygen Android - Hashfile MD5.xls",
                "notes": "Android hashfile from Oxygen Forensics"
            },
            {
                "file_path": "contoh_hashfile/Cellebrite Inseyets iPhone - MD5.xlsx",
                "notes": "iPhone hashfile from Cellebrite"
            },
            {
                "file_path": "contoh_hashfile/Cellebrite Inseyets Android - Hashfile MD5.xlsx",
                "notes": "Android hashfile from Cellebrite"
            },
            {
                "file_path": "contoh_hashfile/Encase - Hashfile.txt",
                "notes": "Hashfile from Encase"
            },
            {
                "file_path": "contoh_hashfile/Magnet Axiom - File Details.csv",
                "notes": "File details from Magnet Axiom"
            }
        ]
        
        success_count = 0
        for i, hashfile in enumerate(hashfile_files, 1):
            self.print_step(f"5.{i}", f"Uploading {os.path.basename(hashfile['file_path'])}...")
            
            if not os.path.exists(hashfile["file_path"]):
                self.print_error(f"File not found: {hashfile['file_path']}")
                continue
                
            try:
                with open(hashfile["file_path"], "rb") as f:
                    files = {"file": f}
                    data = {"notes": hashfile["notes"]}
                    
                    response = self.session.post(
                        f"{self.api_base}/analytic/{self.analytic_id}/upload-hashfile",
                        files=files,
                        data=data
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if "uploaded successfully" in response_data.get("message", ""):
                            self.print_success(f"Hashfile uploaded successfully")
                            success_count += 1
                        else:
                            self.print_warning(f"Hashfile upload failed or already exists")
                            self.print_info(f"Response: {response_data}")
                    else:
                        self.print_warning(f"Hashfile upload failed: {response.status_code}")
                        self.print_info(f"Response: {response.text}")
                        
            except Exception as e:
                self.print_error(f"Exception occurred while uploading hashfile: {str(e)}")
                
        return success_count > 0
        
    def run_analytics(self) -> bool:
        self.print_step(6, "Running analytics...")
        
        analytics_endpoints = [
            {
                "name": "Contact Correlation",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/contact-correlation?min_devices=2"
            },
            {
                "name": "Contact Analytics",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/contact-analytics"
            },
            {
                "name": "Hashfile Analytics",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/hashfile-analytics"
            },
            {
                "name": "Social Media Correlation",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/social-media-correlation"
            },
            {
                "name": "Deep Communication Analytics",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/deep-communication-analytics"
            }
        ]
        
        success_count = 0
        for i, analytic in enumerate(analytics_endpoints, 1):
            self.print_step(f"6.{i}", f"Running {analytic['name']}...")
            
            try:
                response = self.session.get(analytic["url"])
                
                if response.status_code == 200:
                    response_data = response.json()
                    if "analytics" in response_data.get("message", "") or "correlation" in response_data.get("message", ""):
                        self.print_success(f"{analytic['name']} completed")
                        success_count += 1
                    else:
                        self.print_warning(f"{analytic['name']} failed or no data")
                        self.print_info(f"Response: {response_data}")
                else:
                    self.print_warning(f"{analytic['name']} failed: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    
            except Exception as e:
                self.print_error(f"Exception occurred while running {analytic['name']}: {str(e)}")
                
        return success_count > 0
        
    def export_reports(self) -> bool:
        """Export PDF reports"""
        self.print_step(7, "Exporting reports...")
        
        os.makedirs("reports", exist_ok=True)
        
        report_endpoints = [
            {
                "name": "Contact Correlation PDF",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/export-contact-correlation-pdf",
                "filename": "reports/contact_correlation_report.pdf"
            },
            {
                "name": "Hashfile Correlation PDF",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/export-hashfile-correlation-pdf",
                "filename": "reports/hashfile_correlation_report.pdf"
            },
            {
                "name": "Social Media Correlation PDF",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/export-social-media-correlation-pdf",
                "filename": "reports/social_media_correlation_report.pdf"
            },
            {
                "name": "Comprehensive Report PDF",
                "url": f"{self.api_base}/analytic/{self.analytic_id}/export-comprehensive-report-pdf",
                "filename": "reports/comprehensive_report.pdf"
            }
        ]
        
        success_count = 0
        for i, report in enumerate(report_endpoints, 1):
            self.print_step(f"7.{i}", f"Exporting {report['name']}...")
            
            try:
                response = self.session.get(report["url"])
                
                if response.status_code == 200:
                    with open(report["filename"], "wb") as f:
                        f.write(response.content)
                    
                    if os.path.exists(report["filename"]) and os.path.getsize(report["filename"]) > 0:
                        self.print_success(f"{report['name']} exported")
                        success_count += 1
                    else:
                        self.print_warning(f"{report['name']} export failed - empty file")
                else:
                    self.print_warning(f"{report['name']} export failed: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    
            except Exception as e:
                self.print_error(f"Exception occurred while exporting {report['name']}: {str(e)}")
                
        return success_count > 0
        
    def update_status(self) -> bool:
        """Update analytic status"""
        self.print_step(8, "Updating analytic status...")
        
        try:
            payload = {
                "status": "completed",
                "summary": "Analysis completed successfully with all devices and hashfiles processed"
            }
            
            response = self.session.put(
                f"{self.api_base}/analytics/{self.analytic_id}/update-status",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if "updated successfully" in response_data.get("message", ""):
                    self.print_success("Analytic status updated to completed")
                    self.print_info(f"Response: {json.dumps(response_data, indent=2)}")
                    return True
                else:
                    self.print_warning("Failed to update analytic status")
                    return False
            else:
                self.print_warning(f"Failed to update analytic status: {response.status_code}")
                self.print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Exception occurred while updating status: {str(e)}")
            return False
            
    def get_summary(self) -> bool:
        """Get final summary"""
        self.print_step(9, "Getting final summary...")
        
        summary_endpoints = [
            {
                "name": "All Analytics",
                "url": f"{self.api_base}/analytics/get-all-analytic"
            },
            {
                "name": "All Files",
                "url": f"{self.api_base}/analytics/files/all"
            },
            {
                "name": "Analytic Detail",
                "url": f"{self.api_base}/analytics/{self.analytic_id}"
            },
            {
                "name": "Analytic Devices",
                "url": f"{self.api_base}/analytics/{self.analytic_id}/devices"
            }
        ]
        
        success_count = 0
        for i, endpoint in enumerate(summary_endpoints, 1):
            self.print_step(f"9.{i}", f"Getting {endpoint['name']}...")
            
            try:
                response = self.session.get(endpoint["url"])
                
                if response.status_code == 200:
                    response_data = response.json()
                    self.print_success(f"{endpoint['name']} retrieved")
                    self.print_info(f"Response: {json.dumps(response_data, indent=2)}")
                    success_count += 1
                else:
                    self.print_warning(f"{endpoint['name']} failed: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    
            except Exception as e:
                self.print_error(f"Exception occurred while getting {endpoint['name']}: {str(e)}")
                
        return success_count > 0
        
    def run_complete_analysis(self) -> bool:
        """Run complete analysis workflow"""
        print("=" * 80)
        print(" FORENLYTIC ANALYTICS - COMPLETE ANALYSIS SCRIPT")
        print("=" * 80)
        print("This script will run a complete forensic analysis using sample data")
        print("from contoh_dataset and contoh_hashfile directories.")
        print("=" * 80)
        print()
        
        if not os.path.exists("contoh_dataset"):
            self.print_error("contoh_dataset directory not found!")
            return False
            
        if not os.path.exists("contoh_hashfile"):
            self.print_error("contoh_hashfile directory not found!")
            return False
            
        steps = [
            self.check_server,
            self.create_analytic,
            self.upload_device_data,
            self.add_devices,
            self.link_devices,
            self.upload_hashfiles,
            self.run_analytics,
            self.export_reports,
            self.update_status,
            self.get_summary
        ]
        
        success_count = 0
        for step in steps:
            if step():
                success_count += 1
            else:
                self.print_warning(f"Step failed, continuing...")
                
        print()
        print("=" * 80)
        if success_count == len(steps):
            print(" ANALYSIS COMPLETED SUCCESSFULLY!")
        else:
            print(f"  ANALYSIS COMPLETED WITH {len(steps) - success_count} FAILURES")
        print("=" * 80)
        print(f"Analytic ID: {self.analytic_id}")
        print(f"Devices: {', '.join(map(str, self.device_ids))}")
        print(f"Files: {', '.join(map(str, self.file_ids))}")
        print("Reports exported to: reports/")
        print("=" * 80)
        
        return success_count == len(steps)

def main():
    """Main function"""
    analyzer = ForenlyticAnalyzer()
    success = analyzer.run_complete_analysis()
    
    if success:
        print(f"{Colors.GREEN} All steps completed successfully!{Colors.NC}")
        sys.exit(0)
    else:
        print(f"{Colors.RED} Some steps failed. Check the output above.{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
