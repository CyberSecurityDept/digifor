from sqlalchemy.orm import Session
from app.analytics.analytics_management.models import Analytic, AnalyticDevice
from app.analytics.device_management.models import Device, File
from app.analytics.analytics_management.models import ApkAnalytic, AnalyticFile
from typing import List
from app.utils.timezone import get_indonesia_time
from app.analytics.utils.scan_apk import load_suspicious_indicators
from app.core.config import settings
import os, json, hashlib, requests, re, logging
from datetime import datetime

def store_analytic(db: Session, analytic_name: str, method: str = None, summary: str = None, created_by: str = None):
    new_analytic = Analytic(
        analytic_name=analytic_name,
        method=method,
        summary=summary,
        created_by=created_by,
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
    existing_link = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).first()
    
    if existing_link:
        if device_id not in existing_link.device_ids:
            existing_link.device_ids.append(device_id)
            db.commit()
            return {"status": 200, "message": "Device added to existing analytic"}
        else:
            return {"status": 409, "message": "Device already linked to this analytic"}
    else:
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

def classify_permissions(permissions, suspicious_set=None):
    if not permissions:
        print("[!] No permissions found in report.")
        return 100, "Safe", "No permissions requested.", [], 0

    perm_list = list(permissions.keys()) if isinstance(permissions, dict) else []
    total_perms = len(perm_list)
    if total_perms == 0:
        print("[!] Permission list is empty.")
        return 100, "Safe", "No permissions requested.", [], 0

    dangerous_count = 0
    normal_count = 0
    info_count = 0
    dangerous_found = []

    for perm_name, perm_info in permissions.items():
        status = None
        if isinstance(perm_info, dict):
            status = perm_info.get('status')
        elif isinstance(perm_info, str):
            status = perm_info
        if not status and suspicious_set and perm_name in suspicious_set:
            status = 'dangerous'

        if status:
            status = str(status).lower()
            if status == 'dangerous':
                dangerous_count += 1
                dangerous_found.append(perm_name)
            elif status == 'normal':
                normal_count += 1
            else:
                info_count += 1
        else:
            info_count += 1

    risk_weight = (dangerous_count * 3) + (normal_count * 1) + (info_count * 0.5)
    max_possible_risk = total_perms * 3
    safety_score = int((1 - (risk_weight / max_possible_risk)) * 100)
    safety_score = max(0, min(100, safety_score))

    print(f"[*] Total permissions: {total_perms}")
    print(f"    - Dangerous: {dangerous_count}")
    print(f"    - Normal: {normal_count}")
    print(f"    - Info/Other: {info_count}")
    print(f"    → Computed Safety Score: {safety_score}")

    if any(p in ("android.permission.REQUEST_INSTALL_PACKAGES", "REQUEST_INSTALL_PACKAGES") for p in perm_list):
        print("[⚠️] Critical permission REQUEST_INSTALL_PACKAGES detected.")
        return (
            min(40, safety_score),
            "Dangerous",
            "REQUEST_INSTALL_PACKAGES permission detected (critical risk indicator).",
            dangerous_found,
            risk_weight,
        )

    if safety_score > 70 and dangerous_count == 0:
        return (safety_score, "Safe", "Application has low risk permissions.", dangerous_found, risk_weight)
    if safety_score > 40 or (safety_score > 30 and dangerous_count <= 2):
        return (safety_score, "Malicious", f"High risk: {dangerous_count} dangerous permissions found.", dangerous_found, risk_weight)
    return (safety_score, "Dangerous", f"Critical risk: {dangerous_count} dangerous permissions detected.", dangerous_found, risk_weight)

def normalize_permission_entry(entry):
    if isinstance(entry, dict):
        return entry.get("status", ""), entry.get("description", "")
    elif isinstance(entry, str):
        return entry, ""
    elif entry is None:
        return "", ""
    else:
        return str(entry), ""

def get_mobsf_api_key():
    secret_path = os.path.expanduser("~/.MobSF/secret")
    if not os.path.exists(secret_path):
        raise FileNotFoundError("File ~/.MobSF/secret tidak ditemukan.")
    with open(secret_path, "r") as f:
        secret = f.read().strip()
    print("[*] MobSF secret loaded successfully.")
    return hashlib.sha256(secret.encode()).hexdigest()


def load_suspicious_indicators(script_dir):
    indicators_file = os.path.join(script_dir, 'suspicious_indicators.json')
    if not os.path.exists(indicators_file):
        print("[!] suspicious_indicators.json tidak ditemukan, skip.")
        return set()
    try:
        with open(indicators_file, 'r') as f:
            data = json.load(f)
        suspicious = {
            item['name']
            for item in data
            if item.get('platform') == 'android' and item.get('type') == 'permission'
        }
        print(f"[*] Loaded {len(suspicious)} suspicious indicators.")
        return suspicious
    except Exception as e:
        print(f"[!] Gagal load suspicious_indicators.json: {e}")
        return set()


def log_response(prefix: str, resp):
    print(f"    → {prefix} response: {resp.status_code}")
    try:
        data = resp.json()
        dump = json.dumps(data, indent=2)[:500]
        print(f"       Response JSON (truncated):\n{dump}")
    except Exception:
        print(f"       Response text (truncated): {resp.text[:500]}")
def analyze_apk_from_file(db, file_id: int, analytic_id: int):
    print(f"\n==== Starting analysis for file_id={file_id}, analytic_id={analytic_id} ====")

    # ============================
    # 1. VALIDASI FILE
    # ============================
    file_obj = db.query(File).filter(File.id == file_id).first()
    if not file_obj:
        raise ValueError(f"File dengan id={file_id} tidak ditemukan")

    file_path = file_obj.file_path
    if not file_path:
        raise ValueError("File path tidak ditemukan di DB")

    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

    print(f"[*] File found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    scan_type = "apk" if ext == ".apk" else "ipa" if ext == ".ipa" else "app"

    # ============================
    # 2. UPLOAD TO MOBSF
    # ============================
    api_key = get_mobsf_api_key()
    headers = {"Authorization": api_key}

    print("[*] Uploading to MobSF...")
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
        resp = requests.post(f"{settings.MOBSF_URL}/api/v1/upload", files=files, headers=headers)

    log_response("Upload", resp)
    if resp.status_code != 200:
        raise RuntimeError(f"Upload gagal: {resp.text}")

    resp_json = resp.json()
    file_hash = resp_json.get("hash")
    if not file_hash:
        raise RuntimeError("Tidak dapat membaca hash dari response upload")

    # ============================
    # 3. MULAI SCAN
    # ============================
    print("[*] Starting MobSF scan...")
    scan_resp = requests.post(f"{settings.MOBSF_URL}/api/v1/scan", data={"hash": file_hash}, headers=headers)
    log_response("Scan", scan_resp)
    if scan_resp.status_code != 200:
        raise RuntimeError(f"Scan gagal: {scan_resp.text}")

    # ============================
    # 4. GET REPORT JSON
    # ============================
    print("[*] Fetching MobSF JSON report...")
    json_resp = requests.post(f"{settings.MOBSF_URL}/api/v1/report_json", data={"hash": file_hash}, headers=headers)
    log_response("Report JSON", json_resp)
    if json_resp.status_code != 200:
        raise RuntimeError(f"Gagal ambil report JSON: {json_resp.text}")

    report_json = json_resp.json()

    permissions = report_json.get("permissions", {})
    print(f"[*] Extracted {len(permissions)} permissions from report.")

    # ============================
    # 5. ANALYZE PERMISSIONS
    # ============================
    suspicious_set = load_suspicious_indicators(os.path.dirname(os.path.realpath(__file__)))

    safety_score, classification, reason, dangerous_list, risk_weight = classify_permissions(
        permissions, suspicious_set
    )
    security_score = report_json.get("appsec", {}).get("security_score")

    # =====================================================
    # 6. TEMUKAN analytic_file UNTUK MENYIMPAN HASIL
    # =====================================================
    analytic_file = (
        db.query(AnalyticFile)
        .filter(AnalyticFile.analytic_id == analytic_id, AnalyticFile.file_id == file_id)
        .first()
    )

    if not analytic_file:
        raise RuntimeError("AnalyticFile tidak ditemukan! Pastikan endpoint store-analytic-file dipanggil terlebih dahulu.")

    analytic_file.scoring = security_score or safety_score
    analytic_file.status = "scanned"
    db.commit()

    # ============================
    # 7. SIMPAN PERMISSION KE ApkAnalytic
    # ============================
    print("[*] Saving analysis results to database...")

    # Hapus existing permissions
    db.query(ApkAnalytic).filter(ApkAnalytic.analytic_file_id == analytic_file.id).delete()

    for perm, value in permissions.items():
        status, desc = normalize_permission_entry(value)
        print(f"    • {perm} → status={status}")

        db.add(
            ApkAnalytic(
                item=perm,
                status=status,
                description=desc,
                malware_scoring=security_score,
                analytic_file_id=analytic_file.id,   # 🔥 satu-satunya FK yang valid sekarang
                created_at=datetime.utcnow(),
            )
        )

    db.commit()

    # ============================
    # 8. RETURN RESULT
    # ============================
    result = {
        "file": os.path.basename(file_path),
        "package": report_json.get("package_name", "N/A"),
        "permissions": permissions,
        "permission_analysis": {
            "security_score": security_score,
            "safety_score": safety_score,
            "classification": classification,
            "reason": reason,
            "dangerous_permissions": dangerous_list,
            "risk_weight": risk_weight,
            "total_permissions": len(permissions),
            "dangerous_count": len(dangerous_list),
        }
    }

    print(f"[+] Analysis completed!")
    return result
