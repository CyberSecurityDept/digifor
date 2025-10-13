from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.device_management.service import create_file_record, get_all_files
import os
import uuid
from app.analytics.utils.upload_pipeline import upload_service

router = APIRouter()

@router.get("/analytics/get-all-file")
def get_files(db: Session = Depends(get_db)):
    return get_all_files(db)

@router.post("/analytics/upload-data")
async def upload_data(
    upload_id: str = Form(...),
    file: UploadFile = File(...),
    file_name: str = Form(...),
    notes: str = Form(...),
    type: str = Form(...),
    tools: str = Form(...),
):
    try:
        if not file.filename:
            return JSONResponse({"status": 400, "message": "File name is required"}, status_code=400)

        if not file.filename.lower().endswith((".xlsx", ".xls")):
            return JSONResponse({"status": 400, "message": "Only Excel files (.xlsx, .xls) are allowed"}, status_code=400)

        file_bytes = await file.read()

        if len(file_bytes) > 104857600:
            return JSONResponse({"status": 400, "message": "File size exceeds 100MB limit"}, status_code=400)

        resp = await upload_service.start_file_upload(
            upload_id=upload_id,
            file=file,
            file_name=file_name,
            notes=notes,
            type=type,
            tools=tools,
            file_bytes=file_bytes,
        )

        return JSONResponse(resp, status_code=resp.get("status", 200))

    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Upload error: {str(e)}"}, status_code=500)
