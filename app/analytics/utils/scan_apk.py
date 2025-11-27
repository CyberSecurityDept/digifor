import json, sys, os, re

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
            status = perm_info.get("status")
        elif isinstance(perm_info, str):
            status = perm_info 
        if not status and suspicious_set and perm_name in suspicious_set:
            status = "dangerous"

        if status:
            status = str(status).lower()
            if status == "dangerous":
                dangerous_count += 1
                dangerous_found.append(perm_name)
            elif status == "normal":
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
    print(f"- Dangerous: {dangerous_count}")
    print(f"- Normal: {normal_count}")
    print(f"- Info/Other: {info_count}")
    print(f"→ Computed Safety Score: {safety_score}")

    if any(p in ("android.permission.REQUEST_INSTALL_PACKAGES", "REQUEST_INSTALL_PACKAGES") for p in perm_list):
        print("Critical permission REQUEST_INSTALL_PACKAGES detected.")
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
        return (
            safety_score,
            "Malicious",
            f"High risk: {dangerous_count} dangerous permissions found.",
            dangerous_found,
            risk_weight,
        )
    return (
        safety_score,
        "Dangerous",
        f"Critical risk: {dangerous_count} dangerous permissions detected.",
        dangerous_found,
        risk_weight,
    )

def load_suspicious_indicators(script_dir):
    indicators_file = os.path.join(script_dir, "suspicious_indicators.json")
    if not os.path.exists(indicators_file):
        print("[!] suspicious_indicators.json not found, skipping suspicious check.")
        return set()

    try:
        with open(indicators_file, "r") as f:
            data = json.load(f)
        suspicious = {
            item["name"]
            for item in data
            if item.get("platform") == "android" and item.get("type") == "permission"
        }
        print(f"[*] Loaded {len(suspicious)} suspicious indicators.")
        return suspicious
    except Exception as e:
        print(f"[!] Failed to load suspicious_indicators.json: {e}")
        return set()

def main():
    if len(sys.argv) != 2:
        print("Usage: python scan_apk.py <report.json>", file=sys.stderr)
        sys.exit(1)

    json_path = sys.argv[1]
    script_dir = os.path.dirname(os.path.realpath(__file__))

    with open(json_path, "r", encoding="utf-8") as f:
        report_json = json.load(f)

    permissions = report_json.get('permissions', {})
    if not permissions:
        print("[!] No permissions found in manifest_analysis.")
        sys.exit(0)

    suspicious_set = load_suspicious_indicators(script_dir)

    safety_score, classification, reason, dangerous_list, risk_weight = classify_permissions(
        permissions, suspicious_set
    )

    result = {
        "file_name": report_json.get("file_name", "N/A"),
        "package_name": report_json.get("package_name", "N/A"),
        "permissions": permissions,
        "permission_analysis": {
            "safety_score": safety_score,
            "classification": classification,
            "reason": reason,
            "dangerous_permissions": dangerous_list,
            "risk_weight": risk_weight,
            "total_permissions": len(permissions),
            "dangerous_count": len(dangerous_list),
        },
    }

    print("\n===================== FINAL ANALYSIS =====================")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()