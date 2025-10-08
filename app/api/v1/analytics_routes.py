from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.analytics.service import create_group, get_all_groups
from app.analytics.utils.upload_pipeline import upload_service
from app.analytics.schemas import GroupCreate

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/get-all-analytic")
def get_all_analytic(db: Session = Depends(get_db)):
    try:
        groups = get_all_groups(db)
        return {
            "status": 200,
            "message": "Success",
            "data": groups
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal mengambil data: {str(e)}",
            "data": []
        }

@router.post("/create-analytic")
def create_analytic(data: GroupCreate, db: Session = Depends(get_db)):
    try:
        if not data.analytic_name.strip():
            return {
                "status": 400,
                "message": "analytic_name wajib diisi",
                "data": []
            }

        new_group = create_group(
            db=db,
            analytic_name=data.analytic_name,
            type=data.type,
            notes=data.notes,
        )

        result = {
            "id": new_group.id,
            "analytic_name": new_group.analytic_name,
            "type": new_group.type,
            "notes": new_group.notes,
            "created_at": str(new_group.created_at)
        }

        return {
            "status": 200,
            "message": "Analytics created successfully",
            "data": result
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Gagal membuat analytic: {str(e)}",
            "data": []
        }
    
@router.post("/add-device")
async def add_device(
    file: UploadFile = File(..., description="Excel file (.xlsx atau .xls)"),
    group_id: int = Form(..., description="ID grup device"),
    owner_name: str = Form(..., description="Nama pemilik device"),
    phone_number: str = Form(..., description="Nomor telepon pemilik"),
    social_media: Optional[str] = Form(None, description="JSON string social media"),
    upload_id: str = Form(..., description="Unique upload ID dari client"),
):
    
    try:
        # Validasi file extension
        if not file.filename:
            return JSONResponse(
                {"status": 400, "message": "File name is required"},
                status_code=400
            )
            
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return JSONResponse(
                {"status": 400, "message": "Only Excel files (.xlsx, .xls) are allowed"},
                status_code=400
            )

        # Validasi upload_id tidak kosong
        if not upload_id or upload_id.strip() == "":
            return JSONResponse(
                {"status": 400, "message": "upload_id is required"},
                status_code=400
            )

        # Call service untuk proses upload
        resp = await upload_service.start_upload_and_process(
            file=file,
            group_id=group_id,
            owner_name=owner_name,
            phone_number=phone_number,
            social_media=social_media,
            upload_id=upload_id,
        )
        
        # Gunakan status dari response sebagai HTTP status code
        status_code = resp.get("status", 200)
        return JSONResponse(resp, status_code=status_code)
        
    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Unexpected error: {str(e)}"}, 
            status_code=500
        )

@router.get("/upload-progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    data, status_code = upload_service.get_progress(upload_id)
    return JSONResponse(data, status_code=status_code)


@router.post("/upload-cancel/{upload_id}")
async def cancel_upload(upload_id: str):
    data, status_code = upload_service.cancel(upload_id)
    return JSONResponse(data, status_code=status_code)

@router.post('/start-extraction')
async def start_extraction(): 
    return {"message": "Not implemented yet"}
