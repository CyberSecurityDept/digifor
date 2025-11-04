from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File as FastAPIFile,
    Form,
    Query,
    BackgroundTasks
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics.device_management.service import get_all_files
from app.analytics.shared.models import File, Analytic
from app.analytics.utils.upload_pipeline import upload_service
from typing import Optional
import os, time, uuid, asyncio
from app.api.v1.analytics_apk_routes import UPLOAD_PROGRESS as APK_PROGRESS, run_real_upload_and_finalize as run_real_upload_and_finalize_apk
from sqlalchemy import or_


router = APIRouter()
UPLOAD_PROGRESS = {}

# ============================================================
# 🔧 Helper
# ============================================================
def format_file_size(size_bytes: int) -> str:
    if not size_bytes:
        return "0 MB"
    mb = size_bytes / (1024 * 1024)
    return f"{mb:.3f} MB"


# ============================================================
# Fungsi upload & finalize data
# ============================================================
async def run_real_upload_and_finalize(
    upload_id: str,
    file: UploadFile,
    file_name: str,
    notes: str,
    type: str,
    tools: str,
    file_bytes: bytes,
    method: str,
    total_size: int,
):
    try:
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

        max_wait = 300
        wait_count = 0
        while wait_count < max_wait:
            svc_resp, code = upload_service.get_progress(upload_id)
            if code == 200:
                svc_data = svc_resp.get("data", {})
                if svc_data.get("done"):
                    break
            await asyncio.sleep(1)
            wait_count += 1

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
                        "notes": notes,
                        "type": type,
                        "tools": tools,
                        "method": method,
                        "total_size": format_file_size(total_size),
                        "amount_of_data": str((data.get("parsing_result") or {}).get("amount_of_data_count", 0)),
                        "create_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "update_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                ],
            }
        else:
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


@router.post("/analytics/upload-data")
async def upload_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(...),
    file_name: str = Form(...),
    notes: str = Form(...),
    type: str = Form(...),
    tools: str = Form(...),
    method: str = Form(...),
):
    try:
        required_fields = {
            "file_name": file_name,
            "notes": notes,
            "type": type,
            "tools": tools,
            "method": method,
        }
        for field, value in required_fields.items():
            if not value or str(value).strip() == "":
                return JSONResponse(
                    {
                        "status": 422,
                        "message": f"Field '{field}' is required and cannot be empty",
                        "error_field": field,
                    },
                    status_code=422,
                )

        allowed_extensions = {
            "Handphone": ["xlsx", "xls", "csv", "txt", "xml", "apk", "ipa"],
            "SSD": ["xlsx", "xls", "csv", "txt", "xml"],
            "Harddisk": ["xlsx", "xls", "csv", "txt", "xml"],
            "PC": ["xlsx", "xls", "csv", "txt", "xml"],
            "Laptop": ["xlsx", "xls", "csv", "txt", "xml"],
            "DVR": ["xlsx", "xls", "csv", "txt", "xml", "mp4", "avi", "mov"],
        }

        if type not in allowed_extensions:
            return JSONResponse(
                {"status": 400, "message": f"Invalid type. Allowed types: {list(allowed_extensions.keys())}"},
                status_code=400,
            )

        file_extension = file.filename.lower().split('.')[-1]
        if file_extension != 'sdp':
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Only .sdp files are accepted. Please upload encrypted .sdp first"
                },
                status_code=400,
            )

        valid_methods = [
            "Deep Communication Analytics",
            "Social Media Correlation",
            "Contact Correlation",
            "Hashfile Analytics",
        ]
        valid_tools = ["Magnet Axiom", "Cellebrite", "Oxygen", "Encase"]

        if method not in valid_methods:
            return JSONResponse(
                {"status": 400, "message": f"Invalid method. Must be one of: {valid_methods}"}, status_code=400
            )
        if tools not in valid_tools:
            return JSONResponse(
                {"status": 400, "message": f"Invalid tools. Must be one of: {valid_tools}"}, status_code=400
            )

        file_bytes = await file.read()
        total_size = len(file_bytes)
        if total_size > 104_857_600:
            return JSONResponse({"status": 400, "message": "File size exceeds 100MB limit"}, status_code=400)

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
                "notes": notes,
                "type": type,
                "tools": tools,
                "file_bytes": file_bytes,
                "method": method,
                "total_size": total_size,
            },
            "_started": False,
        }

        return JSONResponse({
            "status": 200,
            "message": "File uploaded, encrypted & parsed successfully",
            "data": {
                "upload_id": upload_id,
                "status_upload": "Pending",
                "upload_type": "data"
            }
        })

    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Upload error: {str(e)}"}, status_code=500)


# ============================================================
# 🧠 Simulate Upload Progress (Dummy)
# ============================================================
async def simulate_upload_process(upload_id, file_name, total_size, notes, type, tools, method):
    try:
        for i in range(1, 101):
            await asyncio.sleep(0.05)
            UPLOAD_PROGRESS[upload_id]["uploaded"] = int((i / 100) * total_size)
            UPLOAD_PROGRESS[upload_id]["percentage"] = i

        UPLOAD_PROGRESS[upload_id].update({
            "status": "Success",
            "upload_status": "Success",
            "message": "Upload successful",
            "percentage": 100,
        })

    except Exception as e:
        UPLOAD_PROGRESS[upload_id].update({
            "status": "Failed",
            "upload_status": "Failed",
            "message": f"Upload Failed! {str(e)}",
            "percentage": "Error",
            "data": []
        })

@router.get("/analytics/upload-progress")
async def get_upload_progress(upload_id: str, type: str = Query("data", description="data or apk")):
    try:
        # Pilih sumber progress
        if type.lower() == "apk":
            prog_dict = APK_PROGRESS
            run_func = run_real_upload_and_finalize_apk
        else:
            prog_dict = UPLOAD_PROGRESS
            run_func = run_real_upload_and_finalize

        prog = prog_dict.get(upload_id)

        # === Start upload kalau belum dimulai ===
        if prog and not prog.get("_started") and prog.get("_ctx"):
            ctx = prog["_ctx"]
            prog["_started"] = True
            if type == "data":
                asyncio.create_task(run_func(
                    upload_id,
                    ctx["file_obj"],
                    ctx["file_name"],
                    ctx["notes"],
                    ctx["type"],
                    ctx["tools"],
                    ctx["file_bytes"],
                    ctx["method"],
                    ctx["total_size"],
                ))
            else:
                asyncio.create_task(run_func(
                    upload_id,
                    ctx["file_obj"],
                    ctx["file_name"],
                    ctx["file_bytes"],
                    ctx["total_size"],
                ))
            prog["_ctx"] = None

        svc_resp, code = upload_service.get_progress(upload_id)
        if code == 200:
            svc_data = svc_resp.get("data", {})
            done = bool(svc_data.get("done"))
            percent = int((svc_data.get("percent") or 0))
            total_size_fmt = svc_data.get("total_size") or format_file_size((prog or {}).get("total_size") or 0)

            if done:
                data_block = (prog or {}).get("data") or []
                return {
                    "status": "Success",
                    "message": "Upload successful",
                    "upload_id": upload_id,
                    "file_name": (prog or {}).get("file_name"),
                    "size": total_size_fmt,
                    "percentage": 100,
                    "upload_status": "Success",
                    "data": data_block,
                }
            else:
                size_out = (svc_data.get("progress_size") or "0 MB") + "/" + (total_size_fmt or "0 MB")
                return {
                    "status": "Progress",
                    "message": svc_resp.get("message", "Upload Progress"),
                    "upload_id": upload_id,
                    "file_name": (prog or {}).get("file_name"),
                    "size": size_out,
                    "percentage": percent,
                    "upload_status": "Progress",
                    "data": [],
                }

        # === Jika tidak ditemukan ===
        if upload_id not in prog_dict:
            return JSONResponse(
                {
                    "status": "Failed",
                    "message": "Upload ID not found",
                    "upload_id": upload_id,
                    "file_name": None,
                    "size": "Upload Failed! Please try again",
                    "percentage": "Error",
                    "upload_status": "Failed",
                    "data": [],
                },
                status_code=404,
            )


        progress = prog_dict[upload_id]
        status = progress.get("status")

        if status == "Success":
            total_size_fmt = format_file_size(progress.get("total_size"))
            uploaded_fmt = format_file_size(progress.get("uploaded", progress.get("total_size", 0)))
            size_out = f"{uploaded_fmt}/{total_size_fmt}"
            return {
                "status": "Success",
                "message": progress.get("message", "Upload successful"),
                "upload_id": upload_id,
                "file_name": progress.get("file_name"),
                "size": size_out,
                "percentage": progress.get("percentage"),
                "upload_status": progress.get("upload_status"),
                "data": progress.get("data"),
            }

        elif status == "Progress":
            uploaded_mb = progress.get("uploaded", 0) / (1024 * 1024)
            total_mb = progress.get("total_size", 1) / (1024 * 1024)
            return {
                "status": "Progress",
                "message": progress.get("message", "Upload Progress"),
                "upload_id": upload_id,
                "file_name": progress.get("file_name"),
                "size": f"{uploaded_mb:.3f}/{total_mb:.3f} MB",
                "percentage": progress.get("percentage"),
                "upload_status": progress.get("upload_status"),
                "data": [],
            }

        elif status == "Failed":
            return {
                "status": "Failed",
                "message": progress.get("message", "Upload Failed! Please try again"),
                "upload_id": upload_id,
                "file_name": progress.get("file_name"),
                "upload_status": "Failed",
                "data": [],
            }

        else:
            return {
                "status": "Failed",
                "message": f"Unknown upload status: {status}",
                "upload_id": upload_id,
                "upload_status": "Failed",
                "data": [],
            }

    except Exception as e:
        return JSONResponse(
            {"status": "Failed", "message": f"Internal server error: {str(e)}", "upload_id": upload_id},
            status_code=500,
        )
    
@router.get("/analytics/get-files")
def get_files(
    search: Optional[str] = Query(None, description="Search by file_name, notes, tools, or method"),
    filter: Optional[str] = Query("All", description='Method filter: "Deep Communication Analytics", "Social Media Correlation", "Contact Correlation", "Hashfile Analytics", "All"'),
    db: Session = Depends(get_db)
):
    try:
        allowed_methods = {
            "Deep Communication Analytics",
            "Social Media Correlation",
            "Contact Correlation",
            "Hashfile Analytics",
            "All"
        }

        query = db.query(File)

        # Apply method filter
        if filter and filter in allowed_methods and filter != "All":
            query = query.filter(File.method == filter)

        # Apply search filter
        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    File.file_name.ilike(term),
                    File.notes.ilike(term),
                    File.tools.ilike(term),
                    File.method.ilike(term),
                )
            )

        files = query.order_by(File.created_at.desc()).all()

        result = [
            {
                "id": f.id,
                "file_name": f.file_name,
                "file_path": f.file_path,
                "notes": f.notes,
                "type": f.type,
                "tools": f.tools,
                "method": f.method,
                "total_size": f.total_size,
                "total_size_formatted": format_file_size(f.total_size) if f.total_size else None,
                "amount_of_data": f.amount_of_data,
                "created_at": str(f.created_at),
                "date": f.created_at.strftime("%d/%m/%Y") if f.created_at else None
            }
            for f in files
        ]

        return {
            "status": 200,
            "message": f"Retrieved {len(result)} files successfully",
            "data": result
        }

    except Exception as e:
        return {
            "status": 500,
            "message": f"Failed to get files: {str(e)}",
            "data": []
        }
