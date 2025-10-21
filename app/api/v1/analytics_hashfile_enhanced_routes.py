from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.shared.models import Analytic, Device, AnalyticDevice, HashFile
from collections import defaultdict
from typing import Optional, List
import hashlib
import os

router = APIRouter()

@router.get("/analytic/{analytic_id}/hashfile-analysis")
def get_hashfile_analysis(
    analytic_id: int,
    source_type: Optional[str] = Query(None),  # iOS, Android, Hardisk, SSD
    source_tool: Optional[str] = Query(None),  # Cellebrite, Oxygen, Magnet Axiom, Encase
    hash_algorithm: Optional[str] = Query(None),  # MD5, SHA1, SHA256
    db: Session = Depends(get_db)
):
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

    # Query hashfiles
    query = db.query(HashFile).filter(HashFile.device_id.in_(device_ids))
    
    if source_type:
        query = query.filter(HashFile.source_type == source_type)
    
    if source_tool:
        query = query.filter(HashFile.source_tool == source_tool)
    
    if hash_algorithm:
        query = query.filter(HashFile.hash_algorithm == hash_algorithm)
    
    hashfiles = query.order_by(HashFile.id).all()
    
    # Get device info
    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    device_info = {
        d.id: {
            "device_id": d.id,
            "device_name": d.owner_name,
            "phone_number": d.phone_number,
            "device_type": d.device_type,
            "device_model": d.device_model,
            "extraction_tool": d.extraction_tool
        }
        for d in devices
    }

    # Analyze hashfiles
    analysis_results = {
        "by_source_type": defaultdict(list),
        "by_source_tool": defaultdict(list),
        "by_hash_algorithm": defaultdict(list),
        "duplicates": [],
        "suspicious_files": [],
        "malware_detected": [],
        "risk_analysis": {
            "low_risk": 0,
            "medium_risk": 0,
            "high_risk": 0
        }
    }
    
    # Hash correlation for duplicates
    hash_correlation = defaultdict(list)
    
    for hf in hashfiles:
        # Get file info
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
        
        # Generate hash if not exists
        file_hash = hf.file_hash
        if not file_hash and hf.file_path:
            file_hash = hashlib.md5(hf.file_path.encode()).hexdigest()
        
        file_info = {
            "hashfile_id": hf.id,
            "device_id": hf.device_id,
            "device_name": device_info.get(hf.device_id, {}).get("device_name", f"Device {hf.device_id}"),
            "device_type": device_info.get(hf.device_id, {}).get("device_type"),
            "device_model": device_info.get(hf.device_id, {}).get("device_model"),
            "extraction_tool": device_info.get(hf.device_id, {}).get("extraction_tool"),
            "file_name": file_name,
            "file_path": hf.file_path,
            "file_hash": file_hash,
            "hash_algorithm": hf.hash_algorithm,
            "file_size": file_size,
            "source_type": hf.source_type,
            "source_tool": hf.source_tool,
            "file_type": hf.file_type,
            "file_extension": hf.file_extension,
            "is_duplicate": hf.is_duplicate,
            "is_suspicious": hf.is_suspicious,
            "malware_detection": hf.malware_detection,
            "risk_level": hf.risk_level,
            "created_at": hf.created_at
        }
        
        # Group by source type
        if hf.source_type:
            analysis_results["by_source_type"][hf.source_type].append(file_info)
        
        # Group by source tool
        if hf.source_tool:
            analysis_results["by_source_tool"][hf.source_tool].append(file_info)
        
        # Group by hash algorithm
        if hf.hash_algorithm:
            analysis_results["by_hash_algorithm"][hf.hash_algorithm].append(file_info)
        
        # Check for duplicates
        if file_hash:
            hash_correlation[file_hash].append(file_info)
        
        # Check for suspicious files
        if hf.is_suspicious == "Yes":
            analysis_results["suspicious_files"].append(file_info)
        
        # Check for malware
        if hf.malware_detection and hf.malware_detection != "Clean":
            analysis_results["malware_detected"].append(file_info)
        
        # Risk analysis
        if hf.risk_level:
            if hf.risk_level.lower() == "low":
                analysis_results["risk_analysis"]["low_risk"] += 1
            elif hf.risk_level.lower() == "medium":
                analysis_results["risk_analysis"]["medium_risk"] += 1
            elif hf.risk_level.lower() == "high":
                analysis_results["risk_analysis"]["high_risk"] += 1
    
    # Find duplicates
    for file_hash, files in hash_correlation.items():
        if len(files) > 1:
            analysis_results["duplicates"].append({
                "file_hash": file_hash,
                "duplicate_count": len(files),
                "files": files
            })
    
    return JSONResponse(
        content={
            "status": 200,
            "message": "Hashfile analysis completed successfully",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "devices": list(device_info.values()),
                "analysis_results": {
                    "by_source_type": dict(analysis_results["by_source_type"]),
                    "by_source_tool": dict(analysis_results["by_source_tool"]),
                    "by_hash_algorithm": dict(analysis_results["by_hash_algorithm"]),
                    "duplicates": analysis_results["duplicates"],
                    "suspicious_files": analysis_results["suspicious_files"],
                    "malware_detected": analysis_results["malware_detected"],
                    "risk_analysis": analysis_results["risk_analysis"]
                },
                "summary": {
                    "total_hashfiles": len(hashfiles),
                    "total_duplicates": len(analysis_results["duplicates"]),
                    "suspicious_files_count": len(analysis_results["suspicious_files"]),
                    "malware_detected_count": len(analysis_results["malware_detected"]),
                    "source_types": list(analysis_results["by_source_type"].keys()),
                    "source_tools": list(analysis_results["by_source_tool"].keys()),
                    "hash_algorithms": list(analysis_results["by_hash_algorithm"].keys())
                }
            }
        },
        status_code=200
    )

@router.get("/analytic/{analytic_id}/hashfile-correlation")
def get_hashfile_correlation(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    """
    Analisis korelasi hashfile antar device
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

    hashfiles = db.query(HashFile).filter(HashFile.device_id.in_(device_ids)).order_by(HashFile.id).all()
    
    # Get device info
    devices = db.query(Device).filter(Device.id.in_(device_ids)).order_by(Device.id).all()
    device_info = {
        d.id: {
            "device_id": d.id,
            "device_name": d.owner_name,
            "phone_number": d.phone_number,
            "device_type": d.device_type,
            "device_model": d.device_model
        }
        for d in devices
    }

    # Build correlation matrix
    correlation_matrix = []
    file_analysis = defaultdict(list)

    for hf in hashfiles:
        file_hash = hf.file_hash
        if not file_hash and hf.file_path:
            file_hash = hashlib.md5(hf.file_path.encode()).hexdigest()
        
        file_analysis[file_hash].append({
            "device_id": hf.device_id,
            "file_name": os.path.basename(hf.file_path) if hf.file_path else f"file_{hf.id}",
            "file_path": hf.file_path,
            "source_type": hf.source_type,
            "source_tool": hf.source_tool,
            "risk_level": hf.risk_level
        })

    # Create correlation pairs
    for i, device_id_1 in enumerate(device_ids):
        for j, device_id_2 in enumerate(device_ids):
            if i < j:  # Avoid duplicates and self-comparison
                device_1_name = device_info.get(device_id_1, {}).get("device_name", f"Device {device_id_1}")
                device_2_name = device_info.get(device_id_2, {}).get("device_name", f"Device {device_id_2}")
                
                # Find common files
                common_files = []
                for file_hash, files in file_analysis.items():
                    device_ids_in_hash = [f["device_id"] for f in files]
                    if device_id_1 in device_ids_in_hash and device_id_2 in device_ids_in_hash:
                        common_files.append({
                            "file_hash": file_hash,
                            "files": files
                        })
                
                correlation_matrix.append({
                    "device_1": {
                        "device_id": device_id_1,
                        "device_name": device_1_name,
                        "device_type": device_info.get(device_id_1, {}).get("device_type")
                    },
                    "device_2": {
                        "device_id": device_id_2,
                        "device_name": device_2_name,
                        "device_type": device_info.get(device_id_2, {}).get("device_type")
                    },
                    "common_files_count": len(common_files),
                    "common_files": common_files,
                    "correlation_strength": len(common_files)
                })

    # Sort by correlation strength
    correlation_matrix.sort(key=lambda x: x["correlation_strength"], reverse=True)

    return JSONResponse(
        content={
            "status": 200,
            "message": "Hashfile correlation analysis completed",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "devices": list(device_info.values()),
                "correlation_matrix": correlation_matrix,
                "summary": {
                    "total_devices": len(device_ids),
                    "total_hashfiles": len(hashfiles),
                    "correlation_pairs": len(correlation_matrix),
                    "strong_correlations": len([c for c in correlation_matrix if c["correlation_strength"] > 0])
                }
            }
        },
        status_code=200
    )

@router.get("/analytic/{analytic_id}/hashfile-statistics")
def get_hashfile_statistics(
    analytic_id: int,
    db: Session = Depends(get_db)
):
    """
    Get statistics untuk hashfile analysis
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

    hashfiles = db.query(HashFile).filter(HashFile.device_id.in_(device_ids)).order_by(HashFile.id).all()
    
    stats = {
        "total_files": len(hashfiles),
        "by_source_type": defaultdict(int),
        "by_source_tool": defaultdict(int),
        "by_hash_algorithm": defaultdict(int),
        "by_file_type": defaultdict(int),
        "by_risk_level": defaultdict(int),
        "duplicates_count": 0,
        "suspicious_count": 0,
        "malware_count": 0,
        "total_size": 0
    }
    
    for hf in hashfiles:
        # Source type stats
        if hf.source_type:
            stats["by_source_type"][hf.source_type] += 1
        
        # Source tool stats
        if hf.source_tool:
            stats["by_source_tool"][hf.source_tool] += 1
        
        # Hash algorithm stats
        if hf.hash_algorithm:
            stats["by_hash_algorithm"][hf.hash_algorithm] += 1
        
        # File type stats
        if hf.file_type:
            stats["by_file_type"][hf.file_type] += 1
        
        # Risk level stats
        if hf.risk_level:
            stats["by_risk_level"][hf.risk_level] += 1
        
        # Special counts
        if hf.is_duplicate == "Yes":
            stats["duplicates_count"] += 1
        
        if hf.is_suspicious == "Yes":
            stats["suspicious_count"] += 1
        
        if hf.malware_detection and hf.malware_detection != "Clean":
            stats["malware_count"] += 1
        
        # File size
        if hf.file_size:
            stats["total_size"] += hf.file_size
    
    return JSONResponse(
        content={
            "status": 200,
            "message": "Hashfile statistics retrieved successfully",
            "data": {
                "analytic_info": {
                    "analytic_id": analytic_id,
                    "analytic_name": analytic.analytic_name
                },
                "statistics": {
                    "total_files": stats["total_files"],
                    "by_source_type": dict(stats["by_source_type"]),
                    "by_source_tool": dict(stats["by_source_tool"]),
                    "by_hash_algorithm": dict(stats["by_hash_algorithm"]),
                    "by_file_type": dict(stats["by_file_type"]),
                    "by_risk_level": dict(stats["by_risk_level"]),
                    "duplicates_count": stats["duplicates_count"],
                    "suspicious_count": stats["suspicious_count"],
                    "malware_count": stats["malware_count"],
                    "total_size_bytes": stats["total_size"],
                    "total_size_mb": round(stats["total_size"] / (1024 * 1024), 2) if stats["total_size"] > 0 else 0
                }
            }
        },
        status_code=200
    )
