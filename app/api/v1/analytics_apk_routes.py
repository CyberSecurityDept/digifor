from fastapi import APIRouter, Depends, Query,HTTPException,UploadFile,Form, BackgroundTasks, File as FastAPIFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.analytics_management.service import analyze_apk_from_file
from app.analytics.analytics_management.models import ApkAnalytic, Analytic
from app.analytics.device_management.models import File
from app.analytics.utils.upload_pipeline import upload_service
from app.auth.models import User
from app.api.deps import get_current_user
import asyncio, time, uuid, traceback
from app.api.v1.analytics_management_routes import check_analytic_access

router = APIRouter()

@router.post("/analytics/upload-apk")
async def upload_apk(background_tasks: BackgroundTasks, file: UploadFile = FastAPIFile(...), file_name: str = Form(...)):
    try:
        if not file_name or str(file_name).strip() == "":
            return JSONResponse(
                {"status": 422, "message": "Field 'file_name' is required", "error_field": "file_name"},
                status_code=422,
            )

        allowed_ext = ["apk", "ipa"]
        ext = file.filename.lower().split(".")[-1]
        if ext not in allowed_ext:
            return JSONResponse(
                {"status": 400, "message": f"Invalid file type. Only {allowed_ext} allowed."},
                status_code=400,
            )

        file_bytes = await file.read()
        total_size = len(file_bytes)

        upload_id = f"upload_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        UPLOAD_PROGRESS[upload_id] = {
            "status": "Progress",
            "message": "Upload Progress",
            "upload_status": "Progress",
            "file_name": file_name,
            "total_size": total_size,
            "uploaded": 0,
            "percentage": 0,
            "data": [],
            "_ctx": {
                "file_obj": file,
                "file_name": file_name,
                "file_bytes": file_bytes,
                "total_size": total_size,
            },
            "_started": False,
        }

        return JSONResponse({
            "status": 200,
            "message": "Upload initialized successfully",
            "data": {
                "file_id": None,
                "upload_id": upload_id,
                "status_upload": "Pending",
                "upload_type": "apk"
            }
        })

    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Upload error: {str(e)}"},
            status_code=500,
        )

@router.post("/analytics/analyze-apk")
def analyze_apk(
    file_id: int, 
    analytic_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analytic_obj = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic_obj:
            return JSONResponse(
                {"status": 404, "message": f"Analytics Not Found", "data": None},
                status_code=404,
            )
        
        
        if current_user is not None and not check_analytic_access(analytic_obj, current_user):
            return JSONResponse(
                {"status": 403, "message": "You do not have permission to access this analytic", "data": None},
                status_code=403,
            )
        
        method_value = analytic_obj.method
        if method_value is None or str(method_value) != "APK Analytics":
            return JSONResponse(
                {
                    "status": 400,
                    "message": f"This endpoint is only for APK Analytics. Current analytic method is '{method_value}'",
                    "data": None
                },
                status_code=400,
            )
        
        file_obj = db.query(File).filter(File.id == file_id).first()
        if not file_obj:
            return JSONResponse(
                {"status": 404, "message": f"File Not Found", "data": None},
                status_code=404,
            )

        result = analyze_apk_from_file(db, file_id=file_id, analytic_id=analytic_id)
        if not result or not isinstance(result, dict):
            return JSONResponse(
                {"status": 400, "message": "Invalid analysis result or file not supported", "data": None},
                status_code=400,
            )

        analysis = result.get("permission_analysis", {})
        malware_scoring = str(analysis.get("security_score", analysis.get("safety_score", 0)))

        permissions_dict = result.get("permissions", {})
        if not permissions_dict:
            return JSONResponse(
                {"status": 400, "message": "No permissions found in analysis result", "data": None},
                status_code=400,
            )

        permissions_list = []
        for idx, (perm, value) in enumerate(permissions_dict.items(), start=1):
            if isinstance(value, dict):
                status = value.get("status", "unknown")
                desc = value.get("description", value.get("info", ""))
            else:
                status = str(value)
                desc = ""
            permissions_list.append({
                "id": idx,
                "item": perm,
                "status": status,
                "description": desc
            })

        formatted_data = {
            "analytic_name": analytic_obj.analytic_name if hasattr(analytic_obj, "analytic_name") else f"Analytic {analytic_id}",
            "method": "APK Analytics",
            "malware_scoring": malware_scoring,
            "permissions": permissions_list
        }

        return JSONResponse(
            {"status": 200, "message": "Success", "data": formatted_data},
            status_code=200,
        )

    except FileNotFoundError as e:
        return JSONResponse(
            {"status": 404, "message": f"File not found: {str(e)}", "data": None},
            status_code=404,
        )

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            {"status": 500, "message": "Something went wrong, please try again later!", "data": None},
            status_code=500,
        )

UPLOAD_PROGRESS = {}
def format_file_size(size_bytes: int) -> str:
    if not size_bytes:
        return "0 MB"
    mb = size_bytes / (1024 * 1024)
    return f"{mb:.3f} MB"

async def run_real_upload_and_finalize(upload_id: str, file: UploadFile, file_name: str, file_bytes: bytes, total_size: int):
    try:
        print(f"[DEBUG] Starting upload for {file_name} (upload_id={upload_id})")
        resp = await upload_service.start_app_upload(
            upload_id=upload_id,
            file=file,
            file_name=file_name,
            file_bytes=file_bytes,
        )
        print(f"[DEBUG] upload_service response: {resp}")

        if isinstance(resp, dict) and resp.get("status") in (200, "200"):
            data = resp.get("data", {})
            UPLOAD_PROGRESS[upload_id] = {
                "status": "Success",
                "message": "Upload successful",
                "upload_status": "Success",
                "file_name": file_name,
                "total_size": total_size,
                "uploaded": total_size,
                "percentage": 100,
                "data": [
                    {
                        "file_id": data.get("file_id"),
                        "file_path": data.get("file_path"),
                        "file_name": file_name,
                        "total_size": format_file_size(total_size),
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                ],
            }
            print(f"📦 [DEBUG] Upload complete! File saved at {data.get('file_path')}")
        else:
            print(f"[WARN] Upload failed! Response: {resp}")
            UPLOAD_PROGRESS[upload_id] = {
                "status": "Failed",
                "message": "Upload Failed! Please try again",
                "upload_id": upload_id,
                "file_name": file_name,
                "size": "Upload Failed! Please try again",
                "percentage": "Error",
                "upload_status": "Failed",
                "data": [],
            }

    except Exception as e:
        print(f"[ERROR] run_real_upload_and_finalize error: {str(e)}")
        traceback.print_exc()
        UPLOAD_PROGRESS[upload_id] = {
            "status": "Failed",
            "message": f"Upload Failed! {str(e)}",
            "upload_id": upload_id,
            "file_name": file_name,
            "size": "Upload Failed! Please try again",
            "percentage": "Error",
            "upload_status": "Failed",
            "data": [],
        }

@router.get("/analytics/apk-analytic")
def get_apk_analysis(
    analytic_id: int = Query(..., description="Analytic ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    analytic_obj = db.query(Analytic).filter(Analytic.id == analytic_id).first()
    if not analytic_obj:
        return JSONResponse(
            {"status": 404, "message": "Analytic not found", "data": {}},
            status_code=404,
        )
    
    if current_user is not None and not check_analytic_access(analytic_obj, current_user):
        return JSONResponse(
            {"status": 403, "message": "You do not have permission to access this analytic", "data": {}},
            status_code=403,
        )
    
    method_value = analytic_obj.method
    if method_value is None or str(method_value) != "APK Analytics":
        return JSONResponse(
            {
                "status": 400,
                "message": f"This endpoint is only for APK Analytics. Current analytic method is '{method_value}'",
                "data": {}
            },
            status_code=400,
        )
    
    apk_records = (
        db.query(ApkAnalytic)
        .filter(ApkAnalytic.analytic_id == analytic_id)
        .order_by(ApkAnalytic.created_at.desc())
        .all()
    )
    
    if not apk_records:
        return JSONResponse(
            {
                "status": 404,
                "message": f"No APK analysis found for analytic_id={analytic_id}",
                "data": {}
            },
            status_code=404,
        )

    malware_scoring = apk_records[0].malware_scoring if apk_records else None

    permissions = [
        {
            "id": r.id,
            "item": r.item,
            "status": r.status,
            "description": r.description,
        }
        for r in apk_records
    ]

    return JSONResponse(
        {
            "status": 200,
            "message": "Success",
            "data": {
                "analytic_name": apk_records[0].analytic.analytic_name if apk_records else None,
                "method": apk_records[0].analytic.method if apk_records else None,
                "malware_scoring": malware_scoring,
                "permissions": permissions,
                "summary" : apk_records[0].analytic.summary if apk_records else None,
            }
        },
        status_code=200,
    )