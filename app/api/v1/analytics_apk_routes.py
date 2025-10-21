from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, Device, AnalyticDevice, File as FileModel
import os
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
import re
import tempfile
import uuid
import time

router = APIRouter()

@router.get("/analytic/{analytic_id}/apk-analysis")
def get_apk_analysis(analytic_id: int, db: Session = Depends(get_db)):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).order_by(AnalyticDevice.id).all()
    device_ids = [link.device_id for link in device_links]
    if not device_ids:
        return JSONResponse(
            content={"status": 200, "message": "No devices linked", "data": []},
            status_code=200
        )

    apk_files = (
        db.query(File)
        .join(Device, File.id == Device.file_id)
        .filter(Device.id.in_(device_ids))
        .filter(File.file_name.like('%.apk'))
        .order_by(Device.id)
        .all()
    )

    device_info = {
        d.id: {"device_name": d.owner_name, "phone_number": d.phone_number}
        for d in db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    }

    apk_analysis_results = []
    suspicious_apps = []
    malware_indicators = []
    permission_analysis = defaultdict(int)
    
    for apk_file in apk_files:
        try:
            analysis_result = analyze_apk_file(apk_file)
            apk_analysis_results.append(analysis_result)
            
            if analysis_result["risk_score"] > 70:
                suspicious_apps.append(analysis_result)
            
            for permission in analysis_result.get("permissions", []):
                permission_analysis[permission] += 1
                
        except Exception as e:
            # Try to get basic info even if analysis fails
            basic_analysis = {
                "file_name": apk_file.file_name,
                "file_path": apk_file.file_path,
                "device_id": apk_file.device.id if hasattr(apk_file, 'device') else None,
                "package_name": extract_package_name(apk_file.file_name),
                "version": extract_version_from_filename(apk_file.file_path),
                "permissions": extract_permissions_from_filename(apk_file.file_path),
                "risk_score": calculate_risk_score(apk_file.file_name),
                "status": "basic_analysis",
                "error": str(e)
            }
            apk_analysis_results.append(basic_analysis)

    malware_patterns = [
        "android.permission.READ_SMS",
        "android.permission.SEND_SMS", 
        "android.permission.RECORD_AUDIO",
        "android.permission.CAMERA",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.READ_CONTACTS",
        "android.permission.READ_CALL_LOG",
        "android.permission.WRITE_EXTERNAL_STORAGE"
    ]
    
    for permission, count in permission_analysis.items():
        if permission in malware_patterns and count > 1:
            malware_indicators.append({
                "permission": permission,
                "occurrence_count": count,
                "risk_level": "high" if count > 3 else "medium"
            })

    headers = [
        {
            "device_id": did,
            "owner_name": info["device_name"],
            "phone_number": info["phone_number"],
        }
        for did, info in device_info.items()
    ]

    return JSONResponse(
        content={
            "status": 200,
            "message": "APK analysis completed",
            "data": {
                "devices": headers,
                "apk_analysis": apk_analysis_results,
                "suspicious_apps": suspicious_apps,
                "malware_indicators": malware_indicators,
                "permission_analysis": dict(permission_analysis),
                "summary": {
                    "total_apk_files": len(apk_files),
                    "suspicious_count": len(suspicious_apps),
                    "malware_indicators_count": len(malware_indicators),
                    "high_risk_apps": len([app for app in suspicious_apps if app["risk_score"] > 80])
                }
            }
        },
        status_code=200
    )

def analyze_apk_file(apk_file):
    file_path = apk_file.file_path
    
    # Extract real version from APK if possible
    version = extract_apk_version(file_path)
    
    # Extract real permissions from APK if possible
    permissions = extract_apk_permissions(file_path)
    
    analysis_result = {
        "file_name": apk_file.file_name,
        "file_path": apk_file.file_path,
        "device_id": apk_file.device.id if hasattr(apk_file, 'device') else None,
        "package_name": extract_package_name(apk_file.file_name),
        "version": version,
        "permissions": permissions,
        "risk_score": calculate_risk_score(apk_file.file_name),
        "status": "analyzed"
    }
    
    return analysis_result

def extract_package_name(file_name):
    base_name = os.path.splitext(file_name)[0]
    return base_name.lower().replace(" ", ".").replace("-", ".")

def extract_apk_permissions(file_path):
    permissions = []
    
    try:
        if os.path.exists(file_path) and file_path.endswith('.apk'):
            with zipfile.ZipFile(file_path, 'r') as apk_zip:
                # Look for AndroidManifest.xml
                manifest_files = [f for f in apk_zip.namelist() if 'AndroidManifest.xml' in f]
                
                if manifest_files:
                    manifest_data = apk_zip.read(manifest_files[0])
                    # Parse binary AndroidManifest.xml to extract permissions
                    permissions = parse_android_manifest_permissions(manifest_data)
                else:
                    # Fallback: extract from file name patterns
                    permissions = extract_permissions_from_filename(file_path)
        else:
            # Fallback: extract from file name patterns
            permissions = extract_permissions_from_filename(file_path)
            
    except Exception as e:
        # Fallback: extract from file name patterns
        permissions = extract_permissions_from_filename(file_path)
    
    return permissions

def extract_permissions_from_filename(file_path):

    file_name = os.path.basename(file_path).lower()
    permissions = []
    
    # Common permissions that most apps have
    permissions.extend([
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE"
    ])
    
    # Pattern-based permission detection
    if "camera" in file_name:
        permissions.append("android.permission.CAMERA")
    if "location" in file_name:
        permissions.append("android.permission.ACCESS_FINE_LOCATION")
    if "sms" in file_name:
        permissions.append("android.permission.READ_SMS")
    if "contact" in file_name:
        permissions.append("android.permission.READ_CONTACTS")
    if "audio" in file_name:
        permissions.append("android.permission.RECORD_AUDIO")
    if "storage" in file_name:
        permissions.append("android.permission.WRITE_EXTERNAL_STORAGE")
    
    return permissions

def parse_android_manifest_permissions(manifest_data):
 
    permissions = []
    
    try:
        manifest_str = manifest_data.decode('utf-8', errors='ignore')
        
        # Common permission patterns
        permission_patterns = [
            r'android\.permission\.\w+',
            r'com\.android\.\w+\.permission\.\w+',
            r'com\.google\.\w+\.permission\.\w+'
        ]
        
        for pattern in permission_patterns:
            matches = re.findall(pattern, manifest_str)
            permissions.extend(matches)
            
    except Exception:
        # If parsing fails, return basic permissions
        permissions = [
            "android.permission.INTERNET",
            "android.permission.ACCESS_NETWORK_STATE"
        ]
    
    return list(set(permissions))  # Remove duplicates

def extract_apk_version(file_path):
    try:
        if os.path.exists(file_path) and file_path.endswith('.apk'):
            with zipfile.ZipFile(file_path, 'r') as apk_zip:
                manifest_files = [f for f in apk_zip.namelist() if 'AndroidManifest.xml' in f]
                
                if manifest_files:
                    manifest_data = apk_zip.read(manifest_files[0])
                    version = parse_android_manifest_version(manifest_data)
                    if version:
                        return version
                        
        return extract_version_from_filename(file_path)
        
    except Exception:
        return extract_version_from_filename(file_path)

def extract_version_from_filename(file_path):
    file_name = os.path.basename(file_path)

    version_patterns = [
        r'v?(\d+\.\d+\.\d+)',
        r'v?(\d+\.\d+)',
        r'v?(\d+)'
    ]
    
    for pattern in version_patterns:
        match = re.search(pattern, file_name)
        if match:
            return match.group(1)
    
    return "1.0.0"

def parse_android_manifest_version(manifest_data):
    try:
        manifest_str = manifest_data.decode('utf-8', errors='ignore')
        
        version_patterns = [
            r'android:versionName="([^"]+)"',
            r'versionName="([^"]+)"',
            r'android:versionCode="([^"]+)"',
            r'versionCode="([^"]+)"'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, manifest_str)
            if match:
                return match.group(1)
                
    except Exception:
        pass
    
    return None

def calculate_risk_score(file_name):
    risk_score = 0
    
    suspicious_keywords = [
        "hack", "crack", "keylogger", "spy", "monitor", "track",
        "steal", "virus", "malware", "trojan", "backdoor"
    ]
    
    for keyword in suspicious_keywords:
        if keyword in file_name.lower():
            risk_score += 20
    
    # Get permissions from file name patterns
    permissions = extract_permissions_from_filename(file_name)
    
    high_risk_permissions = [
        "android.permission.READ_SMS",
        "android.permission.SEND_SMS",
        "android.permission.RECORD_AUDIO",
        "android.permission.CAMERA",
        "android.permission.ACCESS_FINE_LOCATION"
    ]
    
    for permission in permissions:
        if permission in high_risk_permissions:
            risk_score += 10
    
    return min(risk_score, 100)

@router.post("/analytic/{analytic_id}/upload-apk")
async def upload_apk_file(
    analytic_id: int,
    file: UploadFile = File(...),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    if not file.filename.lower().endswith('.apk'):
        return JSONResponse(
            content={"status": 400, "message": "Only APK files are allowed"},
            status_code=400
        )

    try:
        file_bytes = await file.read()
        
        if len(file_bytes) > 100 * 1024 * 1024:
            return JSONResponse(
                content={"status": 400, "message": "File size exceeds 100MB limit"},
                status_code=400
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix='.apk') as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        analysis_result = analyze_apk_file_content(tmp_path, file.filename)

        os.unlink(tmp_path)

        file_record = FileModel(
            file_name=file.filename,
            file_path=f"uploads/apk/{file.filename}",
            notes=notes,
            type="APK",
            tools="APK Analyzer"
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)

        return JSONResponse(
            content={
                "status": 200,
                "message": "APK uploaded and analyzed successfully",
                "data": {
                    "file_id": file_record.id,
                    "file_name": file.filename,
                    "file_size": f"{len(file_bytes) / (1024*1024):.2f} MB",
                    "analysis_result": analysis_result
                }
            },
            status_code=200
        )

    except Exception as e:
        return JSONResponse(
            content={"status": 500, "message": f"Upload error: {str(e)}"},
            status_code=500
        )

@router.get("/analytic/{analytic_id}/apk-analysis-detail/{file_id}")
def get_apk_analysis_detail(
    analytic_id: int,
    file_id: int,
    db: Session = Depends(get_db)
):
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    apk_file = db.query(File).filter(File.id == file_id).first()
    if not apk_file:
        raise HTTPException(status_code=404, detail="APK file not found")

    analysis_result = analyze_apk_file_content(apk_file.file_path, apk_file.file_name)
    
    file_size_bytes = 0
    if os.path.exists(apk_file.file_path):
        file_size_bytes = os.path.getsize(apk_file.file_path)
    
    if file_size_bytes == 0:
        file_size = "0 MB"
    elif file_size_bytes < 1024:
        file_size = f"{file_size_bytes} bytes"
    elif file_size_bytes < 1024 * 1024:
        file_size = f"{file_size_bytes / 1024:.2f} KB"
    else:
        file_size = f"{file_size_bytes / (1024*1024):.2f} MB"

    malicious_permissions = []
    common_permissions = []
    
    for permission in analysis_result.get("permissions", []):
        if permission in [
            "android.permission.READ_SMS",
            "android.permission.SEND_SMS",
            "android.permission.RECORD_AUDIO",
            "android.permission.CAMERA",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.READ_CONTACTS",
            "android.permission.READ_CALL_LOG"
        ]:
            malicious_permissions.append({
                "permission": permission,
                "description": get_permission_description(permission)
            })
        else:
            common_permissions.append({
                "permission": permission,
                "description": get_permission_description(permission)
            })

    return JSONResponse(
        content={
            "status": 200,
            "message": "APK analysis detail retrieved successfully",
            "data": {
                "file_info": {
                    "file_id": file_id,
                    "file_name": apk_file.file_name,
                    "file_size": file_size,
                    "package_name": analysis_result.get("package_name"),
                    "version": analysis_result.get("version")
                },
                "malware_analysis": {
                    "malware_probability": analysis_result.get("risk_score", 0),
                    "risk_level": "High" if analysis_result.get("risk_score", 0) > 70 else "Medium" if analysis_result.get("risk_score", 0) > 40 else "Low"
                },
                "permissions_analysis": {
                    "malicious_permissions": {
                        "count": len(malicious_permissions),
                        "total": len(analysis_result.get("permissions", [])),
                        "permissions": malicious_permissions
                    },
                    "common_permissions": {
                        "count": len(common_permissions),
                        "permissions": common_permissions
                    }
                },
                "summary": {
                    "total_permissions": len(analysis_result.get("permissions", [])),
                    "malicious_count": len(malicious_permissions),
                    "common_count": len(common_permissions)
                }
            }
        },
        status_code=200
    )

def analyze_apk_file_content(file_path: str, file_name: str):
    version = extract_apk_version(file_path)
    
    permissions = extract_apk_permissions(file_path)
    
    analysis_result = {
        "file_name": file_name,
        "package_name": extract_package_name(file_name),
        "version": version,
        "permissions": permissions,
        "risk_score": calculate_risk_score(file_name),
        "status": "analyzed"
    }
    
    return analysis_result

def get_permission_description(permission: str):
    descriptions = {
        "android.permission.READ_SMS": "Can read SMS messages",
        "android.permission.SEND_SMS": "Can send SMS messages",
        "android.permission.RECORD_AUDIO": "Can record audio",
        "android.permission.CAMERA": "Can access camera",
        "android.permission.ACCESS_FINE_LOCATION": "Can access precise location",
        "android.permission.READ_CONTACTS": "Can read contacts",
        "android.permission.READ_CALL_LOG": "Can read call log",
        "android.permission.INTERNET": "Can access internet",
        "android.permission.ACCESS_NETWORK_STATE": "Can access network state",
        "android.permission.WRITE_EXTERNAL_STORAGE": "Can write to external storage"
    }
    
    return descriptions.get(permission, "Unknown permission")
