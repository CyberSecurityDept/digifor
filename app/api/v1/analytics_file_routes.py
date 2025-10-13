from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.device_management.service import create_file_record, get_all_files
import os
import uuid

router = APIRouter()

@router.get("/analytics/get-all-file")
def get_files(db: Session = Depends(get_db)):
    return get_all_files(db)

@router.post("/analytics/upload-data")
async def upload_data(
    file: UploadFile = File(),
    notes: str = Form(),
    type: str = Form(),
    tools: str = Form()
):
    try:
        if not file.filename:
            return JSONResponse({"status": 400, "message": "File name is required"}, status_code=400)

        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return JSONResponse({"status": 400, "message": "Only Excel files (.xlsx, .xls) are allowed"}, status_code=400)

        content = await file.read()
        if len(content) > 104857600:  # 100MB
            return JSONResponse({"status": 400, "message": "File size exceeds 100MB limit"}, status_code=400)

        save_dir = "uploads/data"
        try:
            os.makedirs(save_dir, exist_ok=True)
        except PermissionError:
            return JSONResponse({"status": 500, "message": "Permission denied: Cannot create upload directory"}, status_code=500)

        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"{save_dir}/{unique_filename}"

        try:
            with open(file_path, "wb") as f:
                f.write(content)
        except PermissionError:
            return JSONResponse({"status": 500, "message": "Permission denied: Cannot write file"}, status_code=500)
        except OSError as e:
            return JSONResponse({"status": 500, "message": f"File system error: {str(e)}"}, status_code=500)

        try:
            file_record = create_file_record(
                file_name=file.filename,
                file_path=file_path,
                notes=notes,
                type=type,
                tools=tools
            )
        except Exception as db_error:
            if os.path.exists(file_path):
                os.remove(file_path)
            return JSONResponse({"status": 500, "message": f"Database error: {str(db_error)}"}, status_code=500)

        return JSONResponse({
            "status": 200,
            "message": "File uploaded successfully",
            "data": {"file_id": file_record.id, "file_path": file_path}
        })

    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Upload error: {str(e)}"}, status_code=500)
