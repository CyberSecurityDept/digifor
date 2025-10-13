from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from app.analytics.utils.upload_pipeline import upload_service

router = APIRouter()

@router.post("/analytics/add-device")
async def add_device(
    file_id: int = Form(),
    owner_name: str = Form(),
    phone_number: str = Form(),
    upload_id: str = Form(),
):
    try:
        resp = await upload_service.start_upload_and_process(
            file_id=file_id,
            owner_name=owner_name,
            phone_number=phone_number,
            upload_id=upload_id,
        )
        return JSONResponse(resp, status_code=resp.get("status", 200))
    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Unexpected error: {str(e)}"},
            status_code=500
        )

@router.get("/analytics/upload-progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    data, status_code = upload_service.get_progress(upload_id)
    return JSONResponse(content=data, status_code=status_code)

@router.post("/analytics/upload-cancel/{upload_id}")
async def cancel_upload(upload_id: str):
    data, status_code = upload_service.cancel(upload_id)
    return JSONResponse(content=data, status_code=status_code)
