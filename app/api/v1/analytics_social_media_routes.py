from collections import defaultdict
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, AnalyticDevice, Device, SocialMedia

router = APIRouter()

@router.get("/analytics/{analytic_id}/social-media-correlation")
def social_media_correlation(
    analytic_id: int,
    db: Session = Depends(get_db),
):
    # --- Validasi Analytic ---
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        return JSONResponse(
            {"status": 404, "message": f"Analytic with ID {analytic_id} not found", "data": {}},
            status_code=404
        )
    
    # Check if analytic type is "Social Media Correlation"
    if analytic.type != "Social Media Correlation":
        return JSONResponse(
            content={
                "status": 400, 
                "message": f"This endpoint is only for Social Media Correlation. Current analytic type is '{analytic.type}'", 
                "data": None
            },
            status_code=400,
        )

    # --- Ambil semua device terkait analytic ---
    device_links = (
        db.query(AnalyticDevice)
        .filter(AnalyticDevice.analytic_id == analytic_id)
        .all()
    )
    if not device_links:
        return JSONResponse(
            {"status": 404, "message": "No devices found for this analytic", "data": {}},
            status_code=404
        )

    device_ids = []
    for link in device_links:
        device_ids.extend(link.device_ids)
    devices = db.query(Device).filter(Device.id.in_(device_ids)).all()

    if not devices:
        return JSONResponse(
            {"status": 404, "message": "Devices not found", "data": {}},
            status_code=404
        )

    # --- Ambil semua akun sosial media dari devices itu ---
    social_accounts = (
        db.query(SocialMedia)
        .filter(SocialMedia.device_id.in_(device_ids))
        .all()
    )

    if not social_accounts:
        return JSONResponse(
            {"status": 200, "message": "No social media accounts found", "data": {}},
            status_code=200
        )

    # --- Analisis korelasi berdasarkan platform ---
    correlations = {}
    for platform in ["instagram", "facebook", "whatsapp", "tiktok", "telegram", "x"]:
        correlation = defaultdict(list)

        # Ambil semua akun untuk platform ini
        platform_accounts = [a for a in social_accounts if (a.platform or "").lower() == platform]

        for acc in platform_accounts:
            key = (acc.account_id or acc.account_name or "").strip()
            if not key:
                continue

            correlation[key].append({
                "device_id": acc.device_id,
                "account_name": acc.account_name,
                "account_id": acc.account_id,
            })

        # --- Kelompokkan berdasarkan jumlah device yang punya akun yang sama ---
        grouped = defaultdict(list)
        for key, devs in correlation.items():
            unique_devs = {d["device_id"]: d for d in devs}
            count = len(unique_devs)

            if count >= 2:  # hanya korelasi antar device
                all_devices_complete = []
                for device_id in device_ids:
                    if device_id in unique_devs:
                        all_devices_complete.append(unique_devs[device_id]["account_name"])
                    else:
                        all_devices_complete.append(None)
                grouped[f"{count}_connections"].append(all_devices_complete)

        # --- Siapkan hasil per platform ---
        buckets = []
        for label, dev_groups in sorted(
            grouped.items(), key=lambda x: int(x[0].split("_")[0]), reverse=True
        ):
            buckets.append({
                "label": f"{label.split('_')[0]} koneksi",
                "devices": dev_groups
            })

        correlations[platform.capitalize()] = {"buckets": buckets}

    # --- Siapkan data devices untuk frontend ---
    devices_data = [
        {
            "device_id": d.id,
            "owner_name": d.owner_name,
            "phone_number": d.phone_number,
            "device_name": d.device_name,
            "created_at": str(d.created_at),
        }
        for d in devices
    ]

    return JSONResponse(
        {
            "status": 200,
            "message": f"Success analyzing social media correlation for '{analytic.analytic_name}'",
            "data": {
                "analytic_id": analytic.id,
                "analytic_name": analytic.analytic_name,
                "total_devices": len(devices),
                "devices": devices_data,
                "correlations": correlations,
            }
        },
        status_code=200
    )
