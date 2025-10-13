from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, Device, AnalyticDevice, Contact

router = APIRouter()

@router.get("/analytic/{analytic_id}/contact-correlation")
def get_contact_correlation(analytic_id: int, db: Session = Depends(get_db)):
    # Ambil semua device dalam analytic
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        return {"status": 404, "message": "Analytic not found", "data": []}

    # Ambil semua device_id dalam analytic
    device_links = db.query(AnalyticDevice).filter(
        AnalyticDevice.analytic_id == analytic_id
    ).all()
    device_ids = [link.device_id for link in device_links]
    if not device_ids:
        return {"status": 200, "message": "No devices linked", "data": []}

    # Ambil semua kontak dari device tersebut
    contacts = (
        db.query(Contact)
        .filter(Contact.device_id.in_(device_ids))
        .all()
    )

    # Struktur data: { device_id: {phone_number: contact_name}}
    from collections import defaultdict
    import re

    device_contacts = defaultdict(dict)

    phone_regex = re.compile(r"(\+?\d{7,15})")
    name_regex = re.compile(r"First name:\s*(.*)", re.IGNORECASE)

    for c in contacts:
        # ambil nomor dari field contact
        phone_match = phone_regex.search(c.contact or "")
        phone = phone_match.group(1) if phone_match else None
        if not phone:
            continue

        # ambil nama kalau ada
        name_match = name_regex.search(c.contact or "")
        name = name_match.group(1).strip() if name_match else phone

        device_contacts[c.device_id][phone] = name

    # Buat mapping global: {phone_number: {device_id: contact_name}}
    correlation = defaultdict(dict)
    for device_id, phone_dict in device_contacts.items():
        for phone, name in phone_dict.items():
            correlation[phone][device_id] = name

    # Filter hanya nomor yang muncul di >= 2 device
    correlation = {
        phone: devices
        for phone, devices in correlation.items()
        if len(devices) >= 2
    }

    # Urutkan berdasarkan jumlah kemunculan (descending)
    sorted_correlation = dict(
        sorted(correlation.items(), key=lambda x: len(x[1]), reverse=True)
    )

    # Ambil info device untuk label
    device_info = {
        d.id: {"device_name": d.owner_name, "phone_number": d.phone_number}
        for d in db.query(Device).filter(Device.id.in_(device_ids)).all()
    }

    # Format hasil untuk wireframe
    data = []
    for phone, devices in sorted_correlation.items():
        row = {"contact": phone, "devices": []}
        for device_id in device_ids:
            if device_id in devices:
                row["devices"].append(devices[device_id])
            else:
                row["devices"].append("")  # kosong kalau contact gak ada di device itu
        data.append(row)

    # Susun header device seperti di wireframe
    headers = [
        {
            "device_id": did,
            "owner_name": info["device_name"],
            "phone_number": info["phone_number"],
        }
        for did, info in device_info.items()
    ]

    return {
        "status": 200,
        "message": "Contact correlation success",
        "data": {
            "devices": headers,
            "correlations": data,
        },
    }