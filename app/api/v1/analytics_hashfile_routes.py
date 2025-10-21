from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, Device, AnalyticDevice, HashFile, File as FileModel
from app.analytics.utils.hashfile_parser import hashfile_parser
from collections import defaultdict
import hashlib
import os
from pathlib import Path
import tempfile
import uuid

router = APIRouter()

@router.get("/analytic/{analytic_id}/hashfile-analytics")
def get_hashfile_analytics(analytic_id: int, db: Session = Depends(get_db)):
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

    # Get all hashfiles from linked devices
    hashfiles = (
        db.query(HashFile)
        .filter(HashFile.device_id.in_(device_ids))
        .order_by(HashFile.id)
        .all()
    )

    # Get device information
    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    device_info = {
        d.id: {
            "device_name": d.owner_name,
            "phone_number": d.phone_number,
            "device_id": d.id
        }
        for d in devices
    }

    # Analyze hashfiles for correlation
    file_analysis = defaultdict(list)
    suspicious_files = []
    duplicate_files = []
    hash_correlations = defaultdict(list)

    for hf in hashfiles:
        file_name = os.path.basename(hf.file_path) if hf.file_path else f"file_{hf.id}"
        file_size = "0 MB"
        if hf.file_path and os.path.exists(hf.file_path):
            file_size_bytes = os.path.getsize(hf.file_path)
            if file_size_bytes < 1024:
                file_size = f"{file_size_bytes} bytes"
            elif file_size_bytes < 1024 * 1024:
                file_size = f"{file_size_bytes / 1024:.2f} KB"
            else:
                file_size = f"{file_size_bytes / (1024*1024):.2f} MB"
        
        # Generate hash from file path for correlation
        file_hash = hashlib.md5(hf.file_path.encode()).hexdigest() if hf.file_path else f"hash_{hf.id}"
        
        file_info = {
            "file_name": file_name,
            "file_path": hf.file_path,
            "file_hash": file_hash,
            "file_size": file_size,
            "device_id": hf.device_id,
            "device_name": device_info.get(hf.device_id, {}).get("device_name", f"Device {hf.device_id}"),
            "phone_number": device_info.get(hf.device_id, {}).get("phone_number", "N/A"),
            "created_at": hf.created_at
        }
        
        file_analysis[file_hash].append(file_info)
        hash_correlations[file_hash].append(hf.device_id)
        
        # Check for suspicious files
        if file_name.lower().endswith(('.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.vbs', '.js')):
            suspicious_files.append(file_info)

    # Find duplicate files across devices
    for file_hash, files in file_analysis.items():
        if len(files) > 1:
            duplicate_files.append({
                "file_hash": file_hash,
                "file_name": files[0]["file_name"],
                "occurrences": len(files),
                "devices": files,
                "correlation_strength": len(files)
            })

    # Sort by correlation strength
    duplicate_files.sort(key=lambda x: x["occurrences"], reverse=True)
    suspicious_files.sort(key=lambda x: x["file_name"])

    # Create device headers for UI
    headers = [
        {
            "device_id": did,
            "owner_name": info["device_name"],
            "phone_number": info["phone_number"],
        }
        for did, info in device_info.items()
    ]

    # Calculate correlation statistics
    total_unique_files = len(file_analysis)
    files_in_multiple_devices = len(duplicate_files)
    correlation_rate = (files_in_multiple_devices / total_unique_files * 100) if total_unique_files > 0 else 0

    return JSONResponse(
        content={
            "status": 200,
            "message": "Hashfile analytics completed",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name,
                    "total_devices": len(device_ids)
                },
                "devices": headers,
                "file_statistics": {
                "total_files": len(hashfiles),
                    "total_unique_files": total_unique_files,
                    "duplicate_count": len(duplicate_files),
                    "suspicious_count": len(suspicious_files),
                    "correlation_rate": round(correlation_rate, 2)
                },
                "duplicate_files": duplicate_files[:20],  # Top 20
                "suspicious_files": suspicious_files,
                "correlation_analysis": {
                    "high_correlation_files": [f for f in duplicate_files if f["occurrences"] >= 3],
                    "medium_correlation_files": [f for f in duplicate_files if f["occurrences"] == 2],
                    "total_correlations": len(duplicate_files)
                }
            }
        },
        status_code=200
    )

@router.post("/analytic/{analytic_id}/upload-hashfile")
async def upload_hashfile(
    analytic_id: int,
    file: UploadFile = File(...),
    format_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload dan parse hashfile untuk analytics
    """
    analytic = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic:
        raise HTTPException(status_code=404, detail="Analytic not found")

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Parse hashfile
        parsed_result = hashfile_parser.parse_hashfile(Path(tmp_path), format_type)
        
        if "error" in parsed_result:
            os.unlink(tmp_path)
            return JSONResponse(
                content={
                    "status": 400,
                    "message": f"Failed to parse hashfile: {parsed_result['error']}",
                    "data": None
                },
                status_code=400
            )

        # Analyze hashfiles
        analysis = hashfile_parser.analyze_hashfiles(parsed_result["hashfiles"])
        
        # Clean up temp file
        os.unlink(tmp_path)

        return JSONResponse(
            content={
                "status": 200,
                "message": "Hashfile uploaded and analyzed successfully",
                "data": {
                    "parsed_result": parsed_result,
                    "analysis": analysis,
                    "upload_info": {
                        "filename": file.filename,
                        "format_detected": parsed_result.get("format_detected"),
                        "tool_detected": parsed_result.get("tool")
                    }
                }
            },
            status_code=200
        )

    except Exception as e:
        return JSONResponse(
            content={
                "status": 500,
                "message": f"Upload error: {str(e)}",
                "data": None
            },
            status_code=500
        )

@router.get("/analytic/{analytic_id}/hashfile-correlation-matrix")
def get_hashfile_correlation_matrix(analytic_id: int, db: Session = Depends(get_db)):
    """
    Generate correlation matrix untuk hashfile antar device
    """
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

    # Get device information
    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    device_info = {
        d.id: {
            "device_name": d.owner_name,
            "phone_number": d.phone_number
        }
        for d in devices
    }

    # Get all hashfiles
    hashfiles = (
        db.query(HashFile)
        .filter(HashFile.device_id.in_(device_ids))
        .order_by(HashFile.id)
        .all()
    )

    # Build correlation matrix
    correlation_matrix = []
    file_analysis = defaultdict(list)

    for hf in hashfiles:
        file_hash = hashlib.md5(hf.file_path.encode()).hexdigest() if hf.file_path else f"hash_{hf.id}"
        file_analysis[file_hash].append({
            "device_id": hf.device_id,
            "file_name": os.path.basename(hf.file_path) if hf.file_path else f"file_{hf.id}",
            "file_path": hf.file_path
        })

    # Create correlation pairs
    for i, device_id_1 in enumerate(device_ids):
        for device_id_2 in device_ids[i+1:]:
            files_1 = set()
            files_2 = set()
            
            for file_hash, files in file_analysis.items():
                device_ids_in_file = [f["device_id"] for f in files]
                if device_id_1 in device_ids_in_file:
                    files_1.add(file_hash)
                if device_id_2 in device_ids_in_file:
                    files_2.add(file_hash)
            
            common_files = files_1.intersection(files_2)
            total_files = files_1.union(files_2)
            
            correlation_percentage = (len(common_files) / len(total_files) * 100) if total_files else 0
            
            correlation_matrix.append({
                "device_1": device_info[device_id_1],
                "device_2": device_info[device_id_2],
                "common_files_count": len(common_files),
                "total_unique_files": len(total_files),
                "correlation_percentage": round(correlation_percentage, 2),
                "common_files": [
                    {
                        "file_hash": file_hash,
                        "file_name": file_analysis[file_hash][0]["file_name"],
                        "file_path": file_analysis[file_hash][0]["file_path"]
                    }
                    for file_hash in common_files
                ]
            })

    # Sort by correlation percentage
    correlation_matrix.sort(key=lambda x: x["correlation_percentage"], reverse=True)

    return JSONResponse(
        content={
            "status": 200,
            "message": "Hashfile correlation matrix generated",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "correlation_matrix": correlation_matrix,
                "summary": {
                    "total_device_pairs": len(correlation_matrix),
                    "high_correlation_pairs": len([p for p in correlation_matrix if p["correlation_percentage"] > 50]),
                    "medium_correlation_pairs": len([p for p in correlation_matrix if 20 <= p["correlation_percentage"] <= 50]),
                    "low_correlation_pairs": len([p for p in correlation_matrix if p["correlation_percentage"] < 20])
                }
            }
        },
        status_code=200
    )
