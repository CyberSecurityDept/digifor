from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared import models
import re
from collections import defaultdict

router = APIRouter()

SOCIAL_MEDIA_PLATFORMS = ["instagram", "facebook", "whatsapp", "telegram", "x", "tiktok"]


# --- Helpers ---
def extract_value(pattern: str, text: str) -> str | None:
    """Ambil nilai dari pola seperti 'Nickname: xxx'."""
    if not text:
        return None
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def normalize_phone(phone: str | None) -> str | None:
    """Normalisasi nomor agar formatnya konsisten (contoh: +62812 → 62812)."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    if digits.startswith("62"):
        return digits
    return digits


@router.get("/analytics/{analytic_id}/social-media-correlation")
def social_media_correlation(
    analytic_id: int,
    db: Session = Depends(get_db),
    source: str = Query(..., description="Social media platform (required: one of instagram, facebook, whatsapp, telegram, x, tiktok)"),
):
    """Analisis keterhubungan antar device berdasarkan data Contact (sosmed)."""

    # --- Validasi source wajib diisi & valid ---
    s = (source or "").lower().strip()
    if s not in SOCIAL_MEDIA_PLATFORMS:
        return {
            "status": 400,
            "message": f"Invalid source '{source}'. Must be one of {SOCIAL_MEDIA_PLATFORMS}",
        }

    # --- Ambil semua device dalam analytic ---
    device_links = (
        db.query(models.AnalyticDevice)
        .filter(models.AnalyticDevice.analytic_id == analytic_id)
        .all()
    )
    if not device_links:
        return {"status": 404, "message": "No devices found", "data": []}

    device_ids = [link.device_id for link in device_links]
    devices = db.query(models.Device).filter(models.Device.id.in_(device_ids)).all()

    # --- Ambil semua contact dari device terkait ---
    contacts = (
        db.query(models.Contact)
        .filter(models.Contact.device_id.in_(device_ids))
        .filter(models.Contact.type.ilike("%Contact%"))
        .all()
    )
    if not contacts:
        return {"status": 404, "message": "No contacts found", "data": []}

    # --- Persiapan struktur correlation ---
    correlation = defaultdict(list)

    # --- Parsing berdasarkan platform ---
    for c in contacts:
        src = (c.source or "").strip().lower()
        contact_val = c.contact or ""
        internet_val = c.internet or ""
        phone_val = c.phones_emails or ""

        # === Instagram ===
        if s == "instagram" and "instagram" in src:
            nickname = extract_value(r"Nickname:\s*(.+)", contact_val) or contact_val.splitlines()[0]
            instaid = extract_value(r"Instagram ID:\s*(\S+)", internet_val)
            key = instaid or nickname
            if key:
                correlation[key].append({
                    "device_id": c.device_id,
                    "display_name": nickname
                })

        # === Facebook (bukan Messenger) ===
        elif s == "facebook" and "facebook" in src and "messenger" not in src:
            nickname = extract_value(r"Nickname:\s*(.+)", contact_val) or contact_val
            fb_id = extract_value(r"Facebook ID:\s*(\S+)", phone_val) or extract_value(r"Facebook ID:\s*(\S+)", internet_val)
            key = fb_id or nickname
            if key:
                correlation[key].append({
                    "device_id": c.device_id,
                    "display_name": nickname
                })

        # === X / Twitter ===
        elif s == "x" and any(word in src for word in ["x", "twitter"]):
            acc_name = extract_value(r"Account name:\s*(.+)", internet_val)
            key = acc_name or contact_val.strip()
            if key:
                correlation[key].append({
                    "device_id": c.device_id,
                    "display_name": key
                })

        # === WhatsApp ===
        elif s == "whatsapp" and "whatsapp" in src:
            phone = extract_value(r"Phone number:\s*(\+?\d+)", phone_val)
            nickname = extract_value(r"Nickname:\s*(.+)", contact_val) or extract_value(r"Full name:\s*(.+)", contact_val) or contact_val
            phone_norm = normalize_phone(phone)
            if phone_norm:
                correlation[phone_norm].append({
                    "device_id": c.device_id,
                    "display_name": nickname
                })

        # === Telegram ===
        elif s == "telegram" and "telegram" in src:
            tele_id = extract_value(r"Telegram ID:\s*(\S+)", internet_val)

            nickname_raw = extract_value(r"Nickname:\s*(.+)", contact_val) or contact_val

            if nickname_raw:
                lines = [line.strip() for line in nickname_raw.splitlines() if ":" not in line]
                nickname = " ".join(lines).strip()
            else:
                nickname = None

            key = tele_id
            if key:
                correlation[key].append({
                    "device_id": c.device_id,
                    "display_name": nickname
                })


        # === TikTok ===
        elif s == "tiktok" and "tiktok" in src:
            nickname = extract_value(r"Nickname:\s*(.+)", contact_val) or contact_val
            key = nickname
            if key:
                correlation[key].append({
                    "device_id": c.device_id,
                    "display_name": nickname
                })

    # --- Kelompokkan akun berdasarkan jumlah koneksi ---
    grouped = defaultdict(list)
    for key, devs in correlation.items():
        unique_devs = {d["device_id"]: d for d in devs}
        count = len(unique_devs)
        if count >= 2:
            all_devices_complete = []
            for device_id in device_ids:
                if device_id in unique_devs:
                    all_devices_complete.append({
                        "device_id": device_id,
                        "display_name": unique_devs[device_id]["display_name"]
                    })
                else:
                    all_devices_complete.append({
                        "device_id": device_id,
                        "display_name": None
                    })
            grouped[f"{count}_connections"].append({
                "account_key": key,
                "devices": all_devices_complete,
                "count_devices": count
            })

    # --- Urutkan berdasarkan jumlah koneksi ---
    sorted_grouped = dict(
        sorted(grouped.items(), key=lambda x: int(x[0].split("_")[0]), reverse=True)
    )

    # --- Info devices untuk header ---
    device_data = [
        {
            "device_id": d.id,
            "owner_name": d.owner_name,
            "phone_number": d.phone_number,
            "created_at": d.created_at,
        }
        for d in devices
    ]

    # --- Final Response ---
    return {
        "status": 200,
        "message": "Success",
        "data": {
            "platform": s,
            "devices": device_data,
            "correlations": sorted_grouped
        }
    }
