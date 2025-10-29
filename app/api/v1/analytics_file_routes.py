from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.device_management.service import get_all_files
import os
import uuid
import time
from app.analytics.utils.upload_pipeline import upload_service

router = APIRouter()

@router.get("/analytics/files/all")
def get_files(db: Session = Depends(get_db)):
    return get_all_files(db)

@router.post("/analytics/upload-data")
async def upload_data(
    file: UploadFile = File(...),
    file_name: str = Form(...),
    notes: str = Form(...),
    type: str = Form(...),
    tools: str = Form(...),
    method: str = Form(None),
):
    try:
        if not file.filename:
            return JSONResponse({"status": 400, "message": "File name is required"}, status_code=400)

        file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ""
        
        allowed_extensions = {
            "Handphone": ["xlsx", "xls", "csv", "txt", "xml", "apk", "ipa"],
            "SSD": ["xlsx", "xls", "csv", "txt", "xml"],
            "Harddisk": ["xlsx", "xls", "csv", "txt", "xml"],
            "PC": ["xlsx", "xls", "csv", "txt", "xml"],
            "Laptop": ["xlsx", "xls", "csv", "txt", "xml"],
            "DVR": ["xlsx", "xls", "csv", "txt", "xml", "mp4", "avi", "mov"]
        }
        
        if type not in allowed_extensions:
            return JSONResponse({"status": 400, "message": f"Invalid type. Must be one of: {list(allowed_extensions.keys())}"}, status_code=400)
        
        if file_extension not in allowed_extensions[type]:
            return JSONResponse({"status": 400, "message": f"Invalid file extension for type '{type}'. Allowed: {allowed_extensions[type]}"}, status_code=400)

        valid_methods = [
            "Deep communication analytics",
            "Social Media Correlation", 
            "Contact Correlation",
            "Hashfile Analytics"
        ]
        
        if not method or method.strip() == "":
            return JSONResponse({"status": 400, "message": "Method parameter is required and cannot be empty"}, status_code=400)
        
        if method not in valid_methods:
            return JSONResponse({"status": 400, "message": f"Invalid method. Must be one of: {valid_methods}"}, status_code=400)

        valid_tools = [
            "Magnet Axiom",
            "Cellebrite", 
            "Oxygen",
            "Encase"
        ]
        
        if tools and tools not in valid_tools:
            return JSONResponse({"status": 400, "message": f"Invalid tools. Must be one of: {valid_tools}"}, status_code=400)

        file_bytes = await file.read()

        if len(file_bytes) > 104857600:
            return JSONResponse({"status": 400, "message": "File size exceeds 100MB limit"}, status_code=400)

        upload_id = f"upload_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        if file.filename.lower().endswith((".apk", ".ipa")):
            resp = await upload_service.start_app_upload(
                upload_id=upload_id,
                file=file,
                file_name=file_name,
                notes=notes,
                type=type,
                tools=tools,
                file_bytes=file_bytes,
                method=method,
            )
        else:
            resp = await upload_service.start_file_upload(
                upload_id=upload_id,
                file=file,
                file_name=file_name,
                notes=notes,
                type=type,
                tools=tools,
                file_bytes=file_bytes,
                method=method,
            )

        return JSONResponse(resp, status_code=resp.get("status", 200))

    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Upload error: {str(e)}"}, status_code=500)
