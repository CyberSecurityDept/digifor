from fastapi import (  # type: ignore
    APIRouter,
    Depends,
    UploadFile,
    File as FastAPIFile,
    Form,
    Query,
    BackgroundTasks
)
from fastapi.responses import JSONResponse  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from app.db.session import get_db
from app.analytics.device_management.service import get_all_files
from app.analytics.shared.models import File, Analytic
from app.analytics.utils.upload_pipeline import upload_service
from typing import Optional
import os, time, uuid, asyncio, re
from app.api.v1.analytics_apk_routes import UPLOAD_PROGRESS as APK_PROGRESS, run_real_upload_and_finalize as run_real_upload_and_finalize_apk
from sqlalchemy import or_  # type: ignore


router = APIRouter()
UPLOAD_PROGRESS = {}


def format_file_size(size_bytes: int) -> str:
    if not size_bytes:
        return "0 MB"
    mb = size_bytes / (1024 * 1024)
    return f"{mb:.3f} MB"

async def run_real_upload_and_finalize(
    upload_id: str,
    file: UploadFile,
    file_name: str,
    notes: Optional[str],
    type: str,
    tools: str,
    file_bytes: bytes,
    method: str,
    total_size: int,
):
    try:
        svc_resp, svc_code = upload_service.get_progress(upload_id)
        upload_service_ready = svc_code == 200
        
        if upload_id in UPLOAD_PROGRESS:
            if UPLOAD_PROGRESS[upload_id].get("_processing") and upload_service_ready:
                print(f"Upload {upload_id} is already being processed, skipping duplicate call")
                return
            UPLOAD_PROGRESS[upload_id]["status"] = "Progress"
            UPLOAD_PROGRESS[upload_id]["upload_status"] = "Progress"
            UPLOAD_PROGRESS[upload_id]["_processing"] = True
        
        if not upload_service_ready:
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
        else:
            resp = {"status": 200, "message": "Upload in progress", "data": {}}

        max_wait = 300
        wait_count = 0
        upload_service_done = False
        last_percent = 0
        stuck_count = 0
        
        while wait_count < max_wait:
            svc_resp, code = upload_service.get_progress(upload_id)
            if code == 200:
                svc_data = svc_resp.get("data", {})
                if upload_id in UPLOAD_PROGRESS:
                    percent = int((svc_data.get("percent") or 0))
                    progress_size = svc_data.get("progress_size") or "0 MB"
                    
                    if percent == last_percent and percent > 0:
                        stuck_count += 1
                        if stuck_count >= 30:
                            print(f"[WARNING] Upload {upload_id} stuck at {percent}% for {stuck_count * 0.5} seconds")
                            if percent >= 75:
                                if svc_data.get("done") or percent >= 100:
                                    upload_service_done = True
                                    break
                    else:
                        stuck_count = 0
                        last_percent = percent
                    
                    UPLOAD_PROGRESS[upload_id]["percentage"] = percent
                    message = svc_resp.get("message", "Preparing...")
                    if percent > 0 and "(" not in message:
                        message = f"Preparing... ({percent}%)"
                    UPLOAD_PROGRESS[upload_id]["message"] = message
                    
                    try:
                        if progress_size and progress_size != "0 MB":
                            match = re.search(r'([\d.]+)', progress_size)
                            if match:
                                size_num = float(match.group(1))
                                if "MB" in progress_size:
                                    uploaded_bytes = int(size_num * 1024 * 1024)
                                elif "KB" in progress_size:
                                    uploaded_bytes = int(size_num * 1024)
                                else:
                                    uploaded_bytes = int(size_num)
                                UPLOAD_PROGRESS[upload_id]["uploaded"] = uploaded_bytes
                            else:
                                UPLOAD_PROGRESS[upload_id]["uploaded"] = int((percent / 100) * total_size) if percent > 0 else 0
                        else:
                            UPLOAD_PROGRESS[upload_id]["uploaded"] = int((percent / 100) * total_size) if percent > 0 else 0
                    except:
                        UPLOAD_PROGRESS[upload_id]["uploaded"] = int((percent / 100) * total_size) if percent > 0 else 0
                    
                    UPLOAD_PROGRESS[upload_id]["status"] = "Progress"
                    UPLOAD_PROGRESS[upload_id]["upload_status"] = "Progress"
                
                # Check if done flag is set or percent is 100
                if svc_data.get("done") or (percent >= 100 and code == 200):
                    upload_service_done = True
                    await asyncio.sleep(2)
                    break
            await asyncio.sleep(0.5)
            wait_count += 1

        if upload_service_done and isinstance(resp, dict) and resp.get("status") in (200, "200"):
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
    notes: Optional[str] = Form(None),
    type: str = Form(...),
    tools: str = Form(...),
    method: str = Form(...),
):
    try:
        required_fields = {
            "file_name": file_name,
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
            "status": "Pending",
            "message": "Waiting for processing to start...",
            "upload_status": "Pending",
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
            "_processing": False,
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


@router.get("/analytics/upload-progress")
async def get_upload_progress(upload_id: str, type: str = Query("data", description="data or apk")):
    try:
        if type.lower() == "apk":
            prog_dict = APK_PROGRESS
            run_func = run_real_upload_and_finalize_apk
        else:
            prog_dict = UPLOAD_PROGRESS
            run_func = run_real_upload_and_finalize

        prog = prog_dict.get(upload_id)

        if prog and not prog.get("_started") and not prog.get("_processing") and prog.get("_ctx"):
            ctx = prog["_ctx"]
            prog["_started"] = True
            prog["_processing"] = True
            prog["status"] = "Progress"
            prog["upload_status"] = "Progress"
            prog["message"] = "Upload Progress"
            prog["percentage"] = 0
            
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
            
            svc_resp = None
            code = 404
            for retry in range(5):
                await asyncio.sleep(0.2 * (retry + 1))
                svc_resp, code = upload_service.get_progress(upload_id)
                if code == 200:
                    svc_data = svc_resp.get("data", {})
                    percent = svc_data.get("percent", 0)
                    if percent > 0:
                        break
            
            if code == 200:
                svc_data = svc_resp.get("data", {})
                percent = int((svc_data.get("percent") or 0))
                progress_size = svc_data.get("progress_size") or "0 MB"
                total_size_fmt = svc_data.get("total_size") or format_file_size(prog.get("total_size", 0))
                
                if upload_id in prog_dict:
                    prog_dict[upload_id]["percentage"] = percent
                    message = svc_resp.get("message", "Preparing...")
                    if percent > 0 and "(" not in message:
                        message = f"Preparing... ({percent}%)"
                    prog_dict[upload_id]["message"] = message
                
                size_out = f"{progress_size}/{total_size_fmt}"
                
                return {
                    "status": "Progress",
                    "message": message if percent > 0 else "Upload Progress",
                    "upload_id": upload_id,
                    "file_name": prog.get("file_name"),
                    "size": size_out,
                    "percentage": percent,
                    "upload_status": "Progress",
                    "data": []
                }
            else:
                total_size_mb = prog.get("total_size", 0) / (1024 * 1024)
                total_size_fmt = f"{total_size_mb:.3f} MB"
                return {
                    "status": "Progress",
                    "message": "Upload Progress",
                    "upload_id": upload_id,
                    "file_name": prog.get("file_name"),
                    "size": f"0.000/{total_size_fmt}",
                    "percentage": 0,
                    "upload_status": "Progress",
                    "data": []
                }

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
            return {
                "status": "Success",
                "message": progress.get("message", "Upload successful"),
                "upload_id": upload_id,
                "file_name": progress.get("file_name"),
                "size": total_size_fmt,
                "percentage": progress.get("percentage"),
                "upload_status": progress.get("upload_status"),
                "data": progress.get("data"),
            }

        svc_resp, code = upload_service.get_progress(upload_id)
        if code == 200:
            svc_data = svc_resp.get("data", {})
            done = bool(svc_data.get("done"))
            percent = int((svc_data.get("percent") or 0))
            total_size_fmt = svc_data.get("total_size") or format_file_size(progress.get("total_size") or 0)
            
            if done and percent == 100 and status == "Progress":
                percent = 97
                message = "Finalizing... (97%)"
            else:
                message = svc_resp.get("message", "Preparing...")
                if percent > 0 and "(" not in message:
                    message = f"Preparing... ({percent}%)"
            
            progress_size = svc_data.get("progress_size") or "0 MB"
            if done and percent >= 100:
                size_out = f"{total_size_fmt}/{total_size_fmt}"
            else:
                size_out = f"{progress_size}/{total_size_fmt}"
            
            if upload_id in prog_dict:
                prog_dict[upload_id]["percentage"] = percent
                prog_dict[upload_id]["message"] = message
                try:
                    if progress_size and progress_size != "0 MB":
                        match = re.search(r'([\d.]+)', progress_size)
                        if match:
                            size_num = float(match.group(1))
                            # Convert to bytes (assuming MB)
                            if "MB" in progress_size:
                                uploaded_bytes = int(size_num * 1024 * 1024)
                            elif "KB" in progress_size:
                                uploaded_bytes = int(size_num * 1024)
                            else:
                                uploaded_bytes = int(size_num)
                            prog_dict[upload_id]["uploaded"] = uploaded_bytes
                    elif done and percent >= 100:
                        # If done, set uploaded to total_size
                        prog_dict[upload_id]["uploaded"] = progress.get("total_size", 0)
                except:
                    pass

            if status == "Pending":
                return {
                    "status": "Pending",
                    "message": message if message else "Preparing...",
                    "upload_id": upload_id,
                    "file_name": progress.get("file_name"),
                    "size": f"0 MB/{total_size_fmt}",
                    "percentage": 0,
                    "upload_status": "Pending",
                    "data": [],
                }
            else:
                return {
                    "status": "Progress",
                    "message": message,
                    "upload_id": upload_id,
                    "file_name": progress.get("file_name"),
                    "size": size_out,
                    "percentage": percent,
                    "upload_status": "Progress",
                    "data": [],
                }

        elif status == "Progress" or status == "Pending":
            uploaded_mb = progress.get("uploaded", 0) / (1024 * 1024)
            total_mb = progress.get("total_size", 1) / (1024 * 1024)
            percentage = progress.get("percentage", 0)
            message = progress.get("message", "Preparing...")
            if percentage > 0 and "(" not in message:
                message = f"Preparing... ({percentage}%)"
            
            if status == "Pending":
                total_size_fmt = format_file_size(progress.get("total_size", 0))
                return {
                    "status": "Pending",
                    "message": message,
                    "upload_id": upload_id,
                    "file_name": progress.get("file_name"),
                    "size": f"0 MB/{total_size_fmt}",
                    "percentage": 0,
                    "upload_status": "Pending",
                    "data": [],
                }
            else:
                return {
                    "status": "Progress",
                    "message": message,
                    "upload_id": upload_id,
                    "file_name": progress.get("file_name"),
                    "size": f"{uploaded_mb:.2f} MB/{total_mb:.2f} MB",
                    "percentage": percentage,
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

        if filter and filter in allowed_methods and filter != "All":
            query = query.filter(File.method == filter)

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
                "total_size_formatted": format_file_size(f.total_size) if f.total_size is not None else None,
                "amount_of_data": f.amount_of_data,
                "created_at": str(f.created_at),
                "date": f.created_at.strftime("%d/%m/%Y") if f.created_at is not None else None
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
