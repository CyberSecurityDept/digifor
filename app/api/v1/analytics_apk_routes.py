from fastapi import APIRouter, Depends, Query,HTTPException,UploadFile,Form, BackgroundTasks, File as FastAPIFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.analytics_management.service import analyze_apk_from_file
from app.analytics.analytics_management.models import ApkAnalytic, Analytic, AnalyticFile
from app.analytics.device_management.models import File
from app.analytics.utils.upload_pipeline import upload_service
from app.auth.models import User
from app.api.deps import get_current_user
import asyncio, time, uuid, traceback
from app.api.v1.analytics_management_routes import check_analytic_access
import os
router = APIRouter()

@router.post("/analytics/upload-apk")
async def upload_apk(
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(...),
    file_name: str = Form(...)
):
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

        chunk_size = 1024 * 1024  # 1 MB
        file_bytes = bytearray()

        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            file_bytes.extend(chunk)

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
                "file_bytes": bytes(file_bytes),
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
            return JSONResponse({"status": 404, "message": "Analytics Not Found", "data": None}, 404)

        if current_user and not check_analytic_access(analytic_obj, current_user):
            return JSONResponse({"status": 403, "message": "Forbidden", "data": None}, 403)

        if getattr(analytic_obj, 'method', None) != "APK Analytics":
            return JSONResponse({"status": 400, "message": "Wrong Analytic Method", "data": None}, 400)

        file_obj = db.query(File).filter(File.id == file_id).first()
        if not file_obj:
            return JSONResponse({"status": 404, "message": "File Not Found", "data": None}, 404)

        file_size_raw = getattr(file_obj, "total_size", None)

        if not file_size_raw and os.path.exists(file_obj.file_path):
            file_size_raw = os.path.getsize(file_obj.file_path)

        formatted_file_size = format_file_size(file_size_raw)

        analytic_file = (
            db.query(AnalyticFile)
            .filter(AnalyticFile.analytic_id == analytic_id, AnalyticFile.file_id == file_id)
            .first()
        )

        if not analytic_file:
            analytic_file = AnalyticFile(
                analytic_id=analytic_id,
                file_id=file_id,
                status="pending",
            )
            db.add(analytic_file)
            db.commit()
            db.refresh(analytic_file)

        result = analyze_apk_from_file(db, file_id=file_id, analytic_id=analytic_id)
        if not isinstance(result, dict):
            return JSONResponse({"status": 400, "message": "Invalid analysis result", "data": None}, 400)

        permissions_dict = result.get("permissions", {})
        analysis = result.get("permission_analysis", {})
        scoring = str(analysis.get("security_score", analysis.get("safety_score", 0)))

        setattr(analytic_file, 'status', "scanned")
        setattr(analytic_file, 'scoring', scoring)
        db.commit()

        db.query(ApkAnalytic).filter(ApkAnalytic.analytic_file_id == analytic_file.id).delete()

        for perm, value in permissions_dict.items():
            status = value.get("status", "unknown")
            desc = value.get("description", "")

            db.add(ApkAnalytic(
                item=perm,
                status=status,
                description=desc,
                malware_scoring=scoring,
                analytic_file_id=analytic_file.id
            ))

        db.commit()

        permission_rows = db.query(ApkAnalytic).filter(
            ApkAnalytic.analytic_file_id == analytic_file.id
        ).all()

        permissions_list = [
            {
                "id": row.id,
                "item": row.item,
                "status": row.status,
                "description": row.description,
            }
            for row in permission_rows
        ]

        final_response = {
            "analytic_name": analytic_obj.analytic_name,
            "method": "APK Analytics",
            "status": analytic_file.status,
            "malware_scoring": scoring,
            "file_size": formatted_file_size,
            "permissions": permissions_list,
            "summary": analytic_obj.summary
        }

        return JSONResponse({"status": 200, "message": "Success", "data": final_response}, 200)

    except Exception:
        traceback.print_exc()
        return JSONResponse({"status": 500, "message": "Server error!", "data": None}, 500)


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
            print(f"[DEBUG] Upload complete! File saved at {data.get('file_path')}")
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
            404,
        )
    
    if current_user is not None and not check_analytic_access(analytic_obj, current_user):
        return JSONResponse(
            {"status": 403, "message": "Forbidden", "data": {}},
            403,
        )
    
    if getattr(analytic_obj, 'method', None) != "APK Analytics":
        return JSONResponse(
            {"status": 400, "message": "Wrong Method", "data": {}},
            400,
        )
    
    analytic_file = (
        db.query(AnalyticFile)
        .filter(AnalyticFile.analytic_id == analytic_id)
        .order_by(AnalyticFile.created_at.desc())
        .first()
    )

    if not analytic_file:
        return JSONResponse(
            {"status": 404, "message": "No APK analysis found", "data": {}},
            404,
        )

    file_obj = db.query(File).filter(File.id == analytic_file.file_id).first()

    file_size_raw = getattr(file_obj, "total_size", None)
    if not file_size_raw and os.path.exists(file_obj.file_path):
        file_size_raw = os.path.getsize(file_obj.file_path)

    formatted_file_size = format_file_size(file_size_raw)

    apk_records = (
        db.query(ApkAnalytic)
        .filter(ApkAnalytic.analytic_file_id == analytic_file.id)
        .order_by(ApkAnalytic.created_at.desc())
        .all()
    )

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
                "analytic_name": analytic_obj.analytic_name,
                "method": analytic_obj.method,
                "status": analytic_file.status,
                "malware_scoring": analytic_file.scoring,
                "file_size": formatted_file_size,
                "file_id": analytic_file.file_id,
                "permissions": permissions,
                "summary": analytic_obj.summary,
            }
        },
        200,
    )
@router.post("/analytics/store-analytic-file")
def store_analytic_file(
    analytic_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        analytic_obj = db.query(Analytic).filter(Analytic.id == analytic_id).first()
        if not analytic_obj:
            return JSONResponse(
                {"status": 404, "message": "Analytic not found", "data": None},
                status_code=404,
            )

        if current_user and not check_analytic_access(analytic_obj, current_user):
            return JSONResponse(
                {"status": 403, "message": "Forbidden", "data": None},
                status_code=403,
            )

        file_obj = db.query(File).filter(File.id == file_id).first()
        if not file_obj:
            return JSONResponse(
                {"status": 404, "message": "File not found", "data": None},
                status_code=404,
            )

        analytic_file = (
            db.query(AnalyticFile)
            .filter(AnalyticFile.analytic_id == analytic_id, AnalyticFile.file_id == file_id)
            .first()
        )

        if analytic_file:
            return JSONResponse(
                {"status": 200, "message": "Already exists", "data": {
                    "id": analytic_file.id,
                    "analytic_id": analytic_file.analytic_id,
                    "file_id": analytic_file.file_id,
                    "status": analytic_file.status
                }},
                status_code=200,
            )

        analytic_file = AnalyticFile(
            analytic_id=analytic_id,
            file_id=file_id,
            status="pending"
        )
        db.add(analytic_file)
        db.commit()
        db.refresh(analytic_file)

        return JSONResponse(
            {
                "status": 201,
                "message": "Analytic File Stored",
                "data": {
                    "id": analytic_file.id,
                    "analytic_id": analytic_file.analytic_id,
                    "file_id": analytic_file.file_id,
                    "status": analytic_file.status
                }
            },
            status_code=201,
        )

    except Exception:
        traceback.print_exc()
        return JSONResponse(
            {"status": 500, "message": "Server error!", "data": None},
            status_code=500,
        )
