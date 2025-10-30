from sqlalchemy.orm import Session
from app.analytics.analytics_management.models import Analytic, AnalyticDevice
from app.analytics.device_management.models import Device, File
from app.analytics.analytics_management.models import ApkAnalytic
from typing import List
from app.utils.timezone import get_indonesia_time
from app.analytics.utils.scan_apk import classify_app, safe_get, load_suspicious_indicators
import os
import json
import hashlib
import requests
import re
from datetime import datetime

def store_analytic(db: Session, analytic_name: str, method: str = None):
    new_analytic = Analytic(
        analytic_name=analytic_name,
        method=method,
        created_at=get_indonesia_time()
    )
    db.add(new_analytic)
    db.commit()
    db.refresh(new_analytic)
    return new_analytic

def get_all_analytics(db: Session):
    analytics = db.query(Analytic).order_by(Analytic.id.desc()).all()
    
    formatted_analytics = []
    for analytic in analytics:
        formatted_analytic = {
            "id": analytic.id,
            "analytic_name": analytic.analytic_name,
            "method": analytic.method,
            "summary": analytic.summary,
            "created_at": analytic.created_at,
            "updated_at": analytic.updated_at
        }
        formatted_analytics.append(formatted_analytic)
    
    return formatted_analytics

def get_analytic_by_id(db: Session, analytic_id: int):
    return db.query(Analytic).filter(Analytic.id == analytic_id).first()

def link_device_to_analytic(db: Session, device_id: int, analytic_id: int):
    # Check if analytic already exists
    existing_link = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).first()
    
    if existing_link:
        # Add device_id to existing array if not already present
        if device_id not in existing_link.device_ids:
            existing_link.device_ids.append(device_id)
            db.commit()
            return {"status": 200, "message": "Device added to existing analytic"}
        else:
            return {"status": 409, "message": "Device already linked to this analytic"}
    else:
        # Create new link with device_ids array
        new_link = AnalyticDevice(
            device_ids=[device_id],
            analytic_id=analytic_id,
            created_at=get_indonesia_time()
        )
    db.add(new_link)
    db.commit()
    return {"status": 200, "message": "Linked successfully"}

def get_analytic_devices(db: Session, analytic_id: int):
    devices = db.query(Device).filter(Device.analytic_id == analytic_id).all()
    return devices

MOBSF_URL = "http://localhost:8000"
def get_mobsf_api_key():
    secret_path = os.path.expanduser("~/.MobSF/secret")
    if not os.path.exists(secret_path):
        raise FileNotFoundError("❌ File ~/.MobSF/secret tidak ditemukan.")
    with open(secret_path, "r") as f:
        secret = f.read().strip()
    return hashlib.sha256(secret.encode()).hexdigest()

def analyze_apk_from_file(db, file_id: int, analytic_id: int):
    file_obj = db.query(File).filter(File.id == file_id).first()
    if not file_obj:
        raise ValueError(f"File dengan id={file_id} tidak ditemukan")

    file_path = getattr(file_obj, "file_path", None) or getattr(file_obj, "path", None)
    if not file_path:
        raise ValueError("File path tidak ditemukan di DB")
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    scan_type = "apk" if ext == ".apk" else "ipa" if ext == ".ipa" else "app"

    api_key = get_mobsf_api_key()
    headers = {"Authorization": api_key}

    with open(file_path, "rb") as f:
        filename = os.path.basename(file_path)
        files = {"file": (filename, f, "application/octet-stream")}
        resp = requests.post(f"{MOBSF_URL}/api/v1/upload", files=files, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"Upload gagal: {resp.text}")

    upload_data = resp.json()
    file_hash = upload_data.get("hash")
    if not file_hash:
        raise RuntimeError(f"Upload gagal: {resp.text}")

    scan_resp = requests.post(f"{MOBSF_URL}/api/v1/scan", data={"hash": file_hash}, headers=headers)
    if scan_resp.status_code != 200:
        raise RuntimeError(f"Scan gagal: {scan_resp.text}")

    json_resp = requests.post(f"{MOBSF_URL}/api/v1/report_json", data={"hash": file_hash}, headers=headers)
    if json_resp.status_code != 200:
        raise RuntimeError(f"Gagal ambil JSON report: {json_resp.text}")
    report_json = json_resp.json()

    output_dir = os.path.join(os.getcwd(), "mobsf_output")
    os.makedirs(output_dir, exist_ok=True)
    report_base = os.path.splitext(os.path.basename(file_path))[0]
    json_path = os.path.join(output_dir, f"report_{report_base}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)

    pdf_path = os.path.join(output_dir, f"report_{report_base}.pdf")
    pdf_resp = requests.post(
        f"{MOBSF_URL}/api/v1/download_pdf",
        data={"hash": file_hash, "scan_type": scan_type},
        headers=headers
    )
    if pdf_resp.status_code == 200:
        with open(pdf_path, "wb") as f:
            f.write(pdf_resp.content)

    suspicious_perms_db = load_suspicious_indicators(os.path.dirname(os.path.realpath(__file__)))

    permissions = []
    if "permissions" in report_json and isinstance(report_json["permissions"], dict):
        for key, value in report_json["permissions"].items():
            if isinstance(value, dict):
                permissions.append({
                    "item": key,
                    "info": value.get("info", ""),
                    "status": value.get("status", ""),
                    "description": value.get("description", "")
                })
            else:
                permissions.append({
                    "item": key,
                    "info": "",
                    "status": "",
                    "description": ""
                })

    security_score = report_json.get("security_score")
    if security_score is None:
        raw_str = json.dumps(report_json)
        match = re.search(r'"security_score"\s*:\s*([0-9]+(?:\.[0-9]+)?)', raw_str)
        if match:
            val = match.group(1)
            security_score = float(val) if '.' in val else int(val)
        else:
            security_score = 0

    if 'high_count' in report_json:
        scoring = {
            'security_score': security_score,
            'high_risk': report_json.get('high_count', 0),
            'medium_risk': report_json.get('medium_count', 0),
            'low_risk': report_json.get('low_count', 0),
            'total_issues': report_json.get('high_count', 0)
                             + report_json.get('medium_count', 0)
                             + report_json.get('low_count', 0)
        }
    elif 'manifest_analysis' in report_json and 'manifest_summary' in report_json['manifest_analysis']:
        ms = report_json['manifest_analysis']['manifest_summary']
        scoring = {
            'security_score': security_score,
            'high_risk': safe_get(ms, 'high'),
            'medium_risk': safe_get(ms, 'warning'),
            'low_risk': safe_get(ms, 'info'),
            'total_issues': safe_get(ms, 'high') + safe_get(ms, 'warning') + safe_get(ms, 'info')
        }
    elif 'binary_analysis' in report_json and isinstance(report_json['binary_analysis'], dict) and 'summary' in report_json['binary_analysis']:
        bs = report_json['binary_analysis']['summary']
        scoring = {
            'security_score': security_score,
            'high_risk': safe_get(bs, 'high'),
            'medium_risk': safe_get(bs, 'warning'),
            'low_risk': safe_get(bs, 'info'),
            'total_issues': safe_get(bs, 'high') + safe_get(bs, 'warning') + safe_get(bs, 'info')
        }
    else:
        scoring = {
            'security_score': security_score,
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': 0,
            'total_issues': 0
        }

    apkid = report_json.get('apkid', {})
    malware_indicators = {
        'has_anti_debug': False,
        'has_anti_vm': False,
        'security_score_low': (security_score or 0) < 50
    }
    if apkid:
        for _, v in apkid.items():
            if isinstance(v, dict):
                if 'anti_debug' in v and len(v['anti_debug']) > 0:
                    malware_indicators['has_anti_debug'] = True
                if 'anti_vm' in v and len(v['anti_vm']) > 0:
                    malware_indicators['has_anti_vm'] = True

    classification, reason, risk_weight = classify_app(
        security_score=scoring.get('security_score'),
        high_risk=scoring.get('high_risk', 0),
        medium_risk=scoring.get('medium_risk', 0),
        low_risk=scoring.get('low_risk', 0),
        has_anti_debug=malware_indicators.get('has_anti_debug', False),
        has_anti_vm=malware_indicators.get('has_anti_vm', False),
        suspicious_perm_count=0,
        total_perms=len(permissions),
        suspicious_perms_found=[]
    )

    filtered_output = {
        "file": os.path.basename(file_path),
        "package": report_json.get("package_name", report_json.get("bundle_id", "N/A")),
        "permissions": permissions,
        "malware_indicators": malware_indicators,
        "scoring": scoring,
        "classification": classification,
        "risk_details": {
            "total_risk_weight": risk_weight,
            "suspicious_permission_count": 0,
            "total_permissions": len(permissions),
            "suspicious_permissions_matched": [],
            "reason": reason
        }
    }

    db.add_all([
        ApkAnalytic(
            item=p["item"],
            description=p["description"],
            status=p["status"],
            malware_scoring=scoring["security_score"],
            file_id=file_id,
            analytic_id=analytic_id,
            created_at=datetime.utcnow()
        )
        for p in permissions
    ])
    db.commit()

    return filtered_output