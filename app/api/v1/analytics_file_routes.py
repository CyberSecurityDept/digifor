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
import os, time, uuid, asyncio, re
import logging

logger = logging.getLogger(__name__)
from app.api.v1.analytics_apk_routes import UPLOAD_PROGRESS as APK_PROGRESS, run_real_upload_and_finalize as run_real_upload_and_finalize_apk
from sqlalchemy import or_
from app.auth.models import User
from app.api.deps import get_current_user
from app.utils.security import sanitize_input, validate_sql_injection_patterns, validate_file_name


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
    created_by: Optional[str],
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
                created_by=created_by,
                type=type,
                tools=tools,
                file_bytes=file_bytes,
                method=method,
            )
           
            if isinstance(resp, dict) and resp.get("status") not in (200, "200"):
                error_message = resp.get("message", "Upload Failed! Please try again")
                UPLOAD_PROGRESS[upload_id] = {
                    "status": "Failed",
                    "message": error_message,
                    "upload_id": upload_id,
                    "file_name": file_name,
                    "size": "Upload Failed! Please try again",
                    "percentage": "Error",
                    "upload_status": "Failed",
                    "data": None,
                }
                return
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
                
                is_done = svc_data.get("done", False)
                has_error = svc_data.get("error", False)
                
                if is_done or (percent >= 100 and code == 200):
                    upload_service_done = True
                    if has_error:
                        error_message = svc_resp.get("message", "Upload Failed! Please try again")
                        detected_tool = svc_data.get("detected_tool", "Unknown")
                        method_from_svc = svc_data.get("method")
                        
                        if "Upload hash data not found" in error_message or "not found" in error_message.lower():
                            tool_from_message = None
                            method_from_message = None
                            
                            if " with " in error_message and " method" in error_message:
                                try:
                                    method_part = error_message.split(" with ")[1].split(" method")[0].strip()
                                    if method_part:
                                        method_from_message = method_part
                                except:
                                    pass
                            
                            if " and " in error_message and " tools." in error_message:
                                try:
                                    tool_part = error_message.split(" and ")[-1].replace(" tools.", "").strip()
                                    if tool_part and tool_part != "Unknown":
                                        tool_from_message = tool_part
                                except:
                                    pass
                            
                            tool_for_size = tool_from_message if tool_from_message else (detected_tool if detected_tool != "Unknown" else None)
                            method_for_size = method_from_message if method_from_message else (method_from_svc if method_from_svc else method)
                            
                            if not method_for_size and "Hashfile Analytics" in error_message:
                                method_for_size = "Hashfile Analytics"
                            
                            if tool_for_size and method_for_size == "Hashfile Analytics":
                                size_value = f"File upload failed. Please upload this file using Tools {tool_for_size} with method {method_for_size}"
                            elif tool_for_size:
                                size_value = f"File upload failed. Please upload this file using Tools {tool_for_size}"
                            else:
                                size_value = error_message
                        elif detected_tool and detected_tool != "Unknown":
                            method_for_check = method_from_svc if method_from_svc else method
                            if method_for_check == "Hashfile Analytics":
                                size_value = f"File upload failed. Please upload this file using Tools {detected_tool} with method {method_for_check}"
                            else:
                                size_value = f"File upload failed. Please upload this file using Tools {detected_tool}"
                        else:
                            size_value = "Upload Failed! Please try again"
                        
                        UPLOAD_PROGRESS[upload_id] = {
                            "status": "Failed",
                            "message": error_message,
                            "upload_id": upload_id,
                            "file_name": file_name,
                            "size": size_value,
                            "percentage": "Error",
                            "upload_status": "Failed",
                            "data": None,
                            "method": method_from_svc if method_from_svc else method,
                            "tools": tools,
                            "detected_tool": detected_tool if detected_tool != "Unknown" else None,
                        }
                        return
                    await asyncio.sleep(2)
                    break
            await asyncio.sleep(0.5)
            wait_count += 1

        if upload_service_done and isinstance(resp, dict):
            resp_status = resp.get("status")
            if resp_status in (200, "200"):
                data = resp.get("data", {})
                UPLOAD_PROGRESS[upload_id] = {
                    "status": "Success",
                    "message": "Upload successful",
                    "upload_status": "Success",
                    "file_name": file_name,
                    "total_size": total_size,
                    "uploaded": total_size,
                    "percentage": 100,
                    "method": method,
                    "tools": tools,
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
                error_message = resp.get("message", "Upload Failed! Please try again")
                detected_tool = resp.get("detected_tool", None)
                
                if "Upload hash data not found" in error_message or "not found" in error_message.lower():
                    tool_from_message = None
                    method_from_message = None
                    
                    if " with " in error_message and " method" in error_message:
                        try:
                            method_part = error_message.split(" with ")[1].split(" method")[0].strip()
                            if method_part:
                                method_from_message = method_part
                        except:
                            pass
                    
                    if " and " in error_message and " tools." in error_message:
                        try:
                            tool_part = error_message.split(" and ")[-1].replace(" tools.", "").strip()
                            if tool_part and tool_part != "Unknown":
                                tool_from_message = tool_part
                        except:
                            pass
                    
                    tool_for_size = tool_from_message if tool_from_message else (detected_tool if detected_tool and detected_tool != "Unknown" else None)
                    method_for_size = method_from_message if method_from_message else method
                    
                    if not method_for_size and "Hashfile Analytics" in error_message:
                        method_for_size = "Hashfile Analytics"
                    
                    if tool_for_size and method_for_size == "Hashfile Analytics":
                        size_value = f"File upload failed. Please upload this file using Tools {tool_for_size} with method {method_for_size}"
                    elif tool_for_size:
                        size_value = f"File upload failed. Please upload this file using Tools {tool_for_size}"
                    else:
                        size_value = error_message
                elif detected_tool and detected_tool != "Unknown":
                    if method == "Hashfile Analytics":
                        size_value = f"File upload failed. Please upload this file using Tools {detected_tool} with method {method}"
                    else:
                        size_value = f"File upload failed. Please upload this file using Tools {detected_tool}"
                else:
                    size_value = "Upload Failed! Please try again"
                
                UPLOAD_PROGRESS[upload_id] = {
                    "status": "Failed",
                    "message": error_message,
                    "upload_id": upload_id,
                    "file_name": file_name,
                    "size": size_value,
                    "percentage": "Error",
                    "upload_status": "Failed",
                    "data": None,
                    "method": method,
                    "tools": tools,
                    "detected_tool": detected_tool if detected_tool and detected_tool != "Unknown" else None,
                }
        else:
            method = None
            tools = None
            if upload_id in UPLOAD_PROGRESS and UPLOAD_PROGRESS[upload_id].get("_ctx"):
                method = UPLOAD_PROGRESS[upload_id]["_ctx"].get("method")
                tools = UPLOAD_PROGRESS[upload_id]["_ctx"].get("tools")
            
            UPLOAD_PROGRESS[upload_id] = {
                "status": "Failed",
                "message": "Upload Failed! Please try again",
                "upload_id": upload_id,
                "file_name": file_name,
                "size": "Upload Failed! Please try again",
                "percentage": "Error",
                "upload_status": "Failed",
                "data": None,
                "method": method,
                "tools": tools,
            }
    except Exception as e:
        detected_tool = None
        try:
            svc_resp, code = upload_service.get_progress(upload_id)
            if code == 200:
                svc_data = svc_resp.get("data", {})
                detected_tool = svc_data.get("detected_tool", "Unknown")
        except:
            pass
        
        if detected_tool and detected_tool != "Unknown":
            size_value = f"Upload Failed! Please upload this file using Tools '{detected_tool}'"
        else:
            size_value = "Upload Failed! Please try again"

        method = None
        tools = None
        if upload_id in UPLOAD_PROGRESS and UPLOAD_PROGRESS[upload_id].get("_ctx"):
            method = UPLOAD_PROGRESS[upload_id]["_ctx"].get("method")
            tools = UPLOAD_PROGRESS[upload_id]["_ctx"].get("tools")
        
        UPLOAD_PROGRESS[upload_id] = {
            "status": "Failed",
            "message": "Upload failed. Please try again later.",
            "upload_id": upload_id,
            "file_name": file_name,
            "size": size_value,
            "percentage": "Error",
            "upload_status": "Failed",
            "data": None,
            "method": method,
            "tools": tools,
            "detected_tool": detected_tool if detected_tool and detected_tool != "Unknown" else None,
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
    current_user: User = Depends(get_current_user),
):
    try:
        # Validate and sanitize all inputs
        if not validate_sql_injection_patterns(file_name):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in file_name. Please remove any SQL injection attempts or malicious code.",
                },
                status_code=400,
            )
        file_name = sanitize_input(file_name)
        
        if notes and not validate_sql_injection_patterns(notes):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in notes. Please remove any SQL injection attempts or malicious code.",
                },
                status_code=400,
            )
        notes = sanitize_input(notes) if notes else None
        
        if not validate_sql_injection_patterns(type):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in type. Please remove any SQL injection attempts or malicious code.",
                },
                status_code=400,
            )
        type = sanitize_input(type, max_length=100)
        
        if not validate_sql_injection_patterns(tools):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in tools. Please remove any SQL injection attempts or malicious code.",
                },
                status_code=400,
            )
        tools = sanitize_input(tools, max_length=100)
        
        if not validate_sql_injection_patterns(method):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid characters detected in method. Please remove any SQL injection attempts or malicious code.",
                },
                status_code=400,
            )
        method = sanitize_input(method, max_length=100)
        
        if not validate_file_name(file.filename):
            return JSONResponse(
                {
                    "status": 400,
                    "message": "Invalid file name. File name contains dangerous characters.",
                },
                status_code=400,
            )
        
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

        db: Session = next(get_db())
        try:
            existing_file = db.query(File).filter(
                File.file_name == file_name,
                File.tools == tools,
                File.method == method
            ).first()
            
            if existing_file:
                created_at_iso = None
                if existing_file.created_at is not None:
                    created_at_iso = existing_file.created_at.isoformat()
                
                return JSONResponse({
                    "status": 409,
                    "message": "File already exists",
                    "data": {
                        "file_id": existing_file.id,
                        "file_name": existing_file.file_name,
                        "tools": existing_file.tools,
                        "method": existing_file.method,
                        "created_at": created_at_iso
                    }
                }, status_code=409)
        finally:
            db.close()

        user_fullname = getattr(current_user, 'fullname', '') or ''
        user_email = getattr(current_user, 'email', '') or ''
        created_by = f"Created by: {user_fullname} ({user_email})" if user_fullname or user_email else ""

        upload_id = f"upload_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        UPLOAD_PROGRESS[upload_id] = {
            "status": "Pending",
            "message": "Waiting for processing to start...",
            "upload_status": "Pending",
            "file_name": file_name,
            "total_size": total_size,
            "uploaded": 0,
            "percentage": 0,
            "data": None,
            "method": method,
            "tools": tools,
            "_ctx": {
                "file_obj": file,
                "file_name": file_name,
                "notes": notes,
                "created_by": created_by,
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
        logger.error(f"Error in upload_data: {str(e)}", exc_info=True)
        return JSONResponse({"status": 500, "message": "Upload error occurred. Please try again later."}, status_code=500)

@router.get("/analytics/upload-progress")
async def get_upload_progress(upload_id: str, type: str = Query("data", description="data or apk")):
    if type.lower() == "apk":
        prog_dict = APK_PROGRESS
        run_func = run_real_upload_and_finalize_apk
    else:
        prog_dict = UPLOAD_PROGRESS
        run_func = run_real_upload_and_finalize
    try:
        prog = prog_dict.get(upload_id)

        if prog and not prog.get("_started") and not prog.get("_processing") and prog.get("_ctx"):
            ctx = prog["_ctx"]
            prog["_started"] = True
            prog["_processing"] = True
            prog["status"] = "Progress"
            prog["upload_status"] = "Progress"
            prog["message"] = "Upload Progress"
            prog["percentage"] = 0

            if "method" in ctx:
                prog["method"] = ctx["method"]
            if "tools" in ctx:
                prog["tools"] = ctx["tools"]
            
            if type == "data":
                asyncio.create_task(run_func(
                    upload_id,
                    ctx["file_obj"],
                    ctx["file_name"],
                    ctx["notes"],
                    ctx.get("created_by"),
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
                    "data": None
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
                    "data": None
                }

        if upload_id not in prog_dict:
           
            detected_tool = None
            try:
                svc_resp, code = upload_service.get_progress(upload_id)
                if code == 200:
                    svc_data = svc_resp.get("data", {})
                    detected_tool = svc_data.get("detected_tool", "Unknown")
            except:
                pass
            
            
            if detected_tool and detected_tool != "Unknown":
                size_value = f"Upload Failed! Please upload this file using Tools '{detected_tool}'"
            else:
                size_value = "Upload Failed! Please try again"
            
            return JSONResponse(
                {
                    "status": "Failed",
                    "message": "Upload ID not found",
                    "upload_id": upload_id,
                    "file_name": None,
                    "size": size_value,
                    "percentage": "Error",
                    "upload_status": "Failed",
                    "data": None,
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
            has_error = bool(svc_data.get("error", False))
            percent = int((svc_data.get("percent") or 0))
            total_size_fmt = svc_data.get("total_size") or format_file_size(progress.get("total_size") or 0)

            if done and has_error:
                error_message = svc_resp.get("message", "Upload Failed! Please try again")
                detected_tool = svc_data.get("detected_tool", "Unknown")
                
                if "Decryption error" in error_message or "Decryption failed" in error_message:
                    method = progress.get("method")
                    if not method and progress.get("_ctx"):
                        method = progress.get("_ctx", {}).get("method")
                    
                    tools = progress.get("tools")
                    if not tools and progress.get("_ctx"):
                        tools = progress.get("_ctx", {}).get("tools")
                    
                    if not method or not tools:
                        try:
                            if svc_data:
                                if not method:
                                    method = svc_data.get("method")
                                if not tools:
                                    tools = svc_data.get("tools")
                        except:
                            pass
                    
                    if not method:
                        file_name_lower = (progress.get("file_name") or "").lower()
                        if "hashfile" in file_name_lower or "hash" in file_name_lower:
                            method = "Hashfile Analytics"
                        else:
                            method = "Unknown"
                    detected_tool_for_error = detected_tool if detected_tool and detected_tool != "Unknown" else None
                    
                    if not detected_tool_for_error:
                        if tools:
                            detected_tool_for_error = upload_service._normalize_tool_name(tools) or tools
                        else:
                            detected_tool_for_error = "Unknown"
                    
                    final_method = method if method and method != "Unknown" else "Hashfile Analytics"
                    
                    error_message = f"Upload hash data not found in file with {final_method} method and {detected_tool_for_error} tools."
                
                if "Upload hash data not found" in error_message or "not found" in error_message.lower():
                    tool_from_message = None
                    method_from_message = None
                    
                    if " with " in error_message and " method" in error_message:
                        try:
                            method_part = error_message.split(" with ")[1].split(" method")[0].strip()
                            if method_part:
                                method_from_message = method_part
                        except:
                            pass
                    
                    if " and " in error_message and " tools." in error_message:
                        try:
                            tool_part = error_message.split(" and ")[-1].replace(" tools.", "").strip()
                            if tool_part and tool_part != "Unknown":
                                tool_from_message = tool_part
                        except:
                            pass
                    
                    tool_for_size = tool_from_message if tool_from_message else (detected_tool if detected_tool and detected_tool != "Unknown" else None)
                    method_for_size = method_from_message if method_from_message else method
                    
                    if not method_for_size and "Hashfile Analytics" in error_message:
                        method_for_size = "Hashfile Analytics"
                    
                    if tool_for_size and method_for_size == "Hashfile Analytics":
                        size_value = f"File upload failed. Please upload this file using Tools {tool_for_size} with method {method_for_size}"
                    elif tool_for_size:
                        size_value = f"File upload failed. Please upload this file using Tools {tool_for_size}"
                    else:
                        size_value = error_message
                elif detected_tool and detected_tool != "Unknown":
                    if method == "Hashfile Analytics":
                        size_value = f"File upload failed. Please upload this file using Tools {detected_tool} with method {method}"
                    else:
                        size_value = f"File upload failed. Please upload this file using Tools {detected_tool}"
                else:
                    size_value = "Upload Failed! Please try again"
                
                method_for_storage = progress.get("method")
                if not method_for_storage and progress.get("_ctx"):
                    method_for_storage = progress.get("_ctx", {}).get("method")
                
                tools_for_storage = progress.get("tools")
                if not tools_for_storage and progress.get("_ctx"):
                    tools_for_storage = progress.get("_ctx", {}).get("tools")
                
                prog_dict[upload_id] = {
                    "status": "Failed",
                    "message": error_message,
                    "upload_id": upload_id,
                    "file_name": progress.get("file_name"),
                    "size": size_value,
                    "percentage": "Error",
                    "upload_status": "Failed",
                    "data": None,
                    "method": method_for_storage,
                    "tools": tools_for_storage,
                    "detected_tool": detected_tool if detected_tool != "Unknown" else None,
                }
                return {
                    "status": "Failed",
                    "message": error_message,
                    "upload_id": upload_id,
                    "file_name": progress.get("file_name"),
                    "size": size_value,
                    "percentage": "Error",
                    "upload_status": "Failed",
                    "data": None,
                }
            
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
                            
                            if "MB" in progress_size:
                                uploaded_bytes = int(size_num * 1024 * 1024)
                            elif "KB" in progress_size:
                                uploaded_bytes = int(size_num * 1024)
                            else:
                                uploaded_bytes = int(size_num)
                            prog_dict[upload_id]["uploaded"] = uploaded_bytes
                    elif done and percent >= 100:
                        
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
                    "data": None,
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
                    "data": None,
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
                    "data": None,
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
                    "data": None,
                }

        elif status == "Failed":
            error_message = progress.get("message", "Upload Failed! Please try again")
            detected_tool = progress.get("detected_tool", None)
            method = progress.get("method") or None
            detected_method = progress.get("detected_method", None)
            size_value = None  # Initialize size_value
            
            try:
                svc_resp, code = upload_service.get_progress(upload_id)
                if code == 200:
                    svc_data = svc_resp.get("data", {})
                    if svc_data.get("error", False):
                        svc_message = svc_resp.get("message", "")
                        if svc_message:
                            error_message = svc_message
                    if not detected_tool:
                        detected_tool = svc_data.get("detected_tool", None)
                    elif svc_data.get("detected_tool") and svc_data.get("detected_tool") != "Unknown":
                        detected_tool = svc_data.get("detected_tool")
                    if not method:
                        method = svc_data.get("method")
                    if not detected_method:
                        detected_method = svc_data.get("detected_method")
            except:
                pass
            
            is_no_data_error_check = (
                "Contact Correlation data not found in file. The file format is correct" in error_message or
                "Social Media Correlation data not found in file. The file format is correct" in error_message or
                "Deep Communication Analytics data not found in file. The file format is correct" in error_message
            )
            
            if "Upload hash data not found" in error_message and not is_no_data_error_check:
                if not detected_method:
                    try:
                        svc_resp_check, code_check = upload_service.get_progress(upload_id)
                        if code_check == 200:
                            svc_data_check = svc_resp_check.get("data", {})
                            detected_method = svc_data_check.get("detected_method")
                            if not detected_tool or detected_tool == "Unknown":
                                detected_tool = svc_data_check.get("detected_tool")
                    except:
                        pass
                
                final_method = detected_method if detected_method else (method if method else "Hashfile Analytics")
                
                if not detected_tool or detected_tool == "Unknown":
                    try:
                        svc_resp_check, code_check = upload_service.get_progress(upload_id)
                        if code_check == 200:
                            svc_data_check = svc_resp_check.get("data", {})
                            detected_tool = svc_data_check.get("detected_tool")
                            if detected_tool and detected_tool != "Unknown":
                                logger.debug(f"[ERROR HANDLING] Got detected_tool from upload_service: {detected_tool}")
                    except:
                        pass
                
                if (not detected_tool or detected_tool == "Unknown") and " and " in error_message and " tools." in error_message:
                    try:
                        tool_part = error_message.split(" and ")[-1].replace(" tools.", "").strip()
                        if tool_part and tool_part != "Unknown":
                            detected_tool = tool_part
                            logger.debug(f"[ERROR HANDLING] Extracted detected_tool from error_message: {detected_tool}")
                    except:
                        pass
                
                if not detected_tool or detected_tool == "Unknown":
                    logger.warning(f"[ERROR HANDLING] WARNING: Could not get detected_tool. Using user selection as last resort.")
                    if progress.get("tools"):
                        detected_tool = upload_service._normalize_tool_name(progress.get("tools")) or progress.get("tools")
                    else:
                        detected_tool = "Unknown"
                
                error_message = f"Upload hash data not found in file with {final_method} method and {detected_tool} tools."
            
            if not method:
                if progress.get("_ctx"):
                    method = progress.get("_ctx", {}).get("method")
                if not method:
                    try:
                        svc_resp_check, code_check = upload_service.get_progress(upload_id)
                        if code_check == 200:
                            svc_data_check = svc_resp_check.get("data", {})
                            method = svc_data_check.get("method")
                    except:
                        pass
            
            if "Decryption error" in error_message or "Decryption failed" in error_message:
                if not method:
                    method = progress.get("method") or None
                if not method and progress.get("_ctx"):
                    method = progress.get("_ctx", {}).get("method") or None
                
                tools = progress.get("tools")
                if not tools and progress.get("_ctx"):
                    tools = progress.get("_ctx", {}).get("tools")
                
                if not method or not tools:
                    try:
                        svc_resp_check, code_check = upload_service.get_progress(upload_id)
                        if code_check == 200:
                            svc_data_check = svc_resp_check.get("data", {})
                            if not method:
                                method = svc_data_check.get("method")
                            if not tools:
                                tools = svc_data_check.get("tools")
                    except:
                        pass
                
                if not method:
                    file_name_lower = (progress.get("file_name") or "").lower()
                    if "hashfile" in file_name_lower or "hash" in file_name_lower:
                        method = "Hashfile Analytics"
                    else:
                        method = "Unknown"
                
                detected_tool_for_error = detected_tool if detected_tool and detected_tool != "Unknown" else None
                if not detected_tool_for_error:
                    try:
                        file_name = progress.get("file_name")
                        if file_name:
                            try:
                                svc_resp_check, code_check = upload_service.get_progress(upload_id)
                                if code_check == 200:
                                    svc_data_check = svc_resp_check.get("data", {})
                                    detected_tool_for_error = svc_data_check.get("detected_tool")
                            except:
                                pass
                    except:
                        pass
                
                if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                    if tools:
                        detected_tool_for_error = upload_service._normalize_tool_name(tools) or tools
                    else:
                        detected_tool_for_error = "Unknown"
                
                final_method = method if method and method != "Unknown" else "Hashfile Analytics"
                
                error_message = f"Upload hash data not found in file with {final_method} method and {detected_tool_for_error} tools."
            
            if ("format error" in error_message.lower() or 
                "must contain" in error_message.lower() or 
                "No valid hashfile data" in error_message or 
                "Please check" in error_message or
                "Expected format" in error_message or
                "parsing error" in error_message.lower()):
                size_value = error_message
            elif "File upload failed. Please upload this file using Tools" in error_message:
                tool_match = error_message.split("Tools ")[1].split()[0] if "Tools " in error_message else None
                if tool_match:
                    method_for_check = method if method else progress.get("method") or detected_method
                   
                    if method_for_check == "Hashfile Analytics":
                        size_value = f"File upload failed. Please upload this file using Tools {tool_match} with method {method_for_check}"
                    else:
                        size_value = f"File upload failed. Please upload this file using Tools {tool_match}"
                else:
                    size_value = error_message
            elif "Upload hash data not found" in error_message or "not found" in error_message.lower() or "Contacts and calls data not found" in error_message or "Contact Correlation data not found" in error_message or "Social Media Correlation data not found" in error_message or "Deep Communication Analytics data not found" in error_message:
                is_no_data_error = (
                    "Contact Correlation data not found in file. The file format is correct" in error_message or
                    "Social Media Correlation data not found in file. The file format is correct" in error_message or
                    "Deep Communication Analytics data not found in file. The file format is correct" in error_message
                )
                
                if is_no_data_error:
                    size_value = error_message
                else:
                    method_from_msg = method
                    tool_from_msg = detected_tool if detected_tool and detected_tool != "Unknown" else None
                    
                    if " with " in error_message and " method" in error_message:
                        try:
                            method_part = error_message.split(" with ")[1].split(" method")[0].strip()
                            if method_part:
                                method_from_msg = method_part
                        except:
                            pass
                    
                    if " and " in error_message and " tools." in error_message:
                        try:
                            tool_part = error_message.split(" and ")[-1].replace(" tools.", "").strip()
                            if tool_part and tool_part != "Unknown":
                                tool_from_msg = tool_part
                        except:
                            pass
                    
                    if not tool_from_msg or tool_from_msg == "Unknown":
                        try:
                            svc_resp_check, code_check = upload_service.get_progress(upload_id)
                            if code_check == 200:
                                svc_data_check = svc_resp_check.get("data", {})
                                tool_from_msg = svc_data_check.get("detected_tool")
                                if tool_from_msg and tool_from_msg != "Unknown":
                                    detected_tool = tool_from_msg
                        except:
                            pass
                    
                    final_method = method_from_msg if method_from_msg else (method if method else "Hashfile Analytics")
                    final_tool = tool_from_msg if tool_from_msg and tool_from_msg != "Unknown" else (detected_tool if detected_tool and detected_tool != "Unknown" else "Unknown")
                    
                    if final_tool and final_tool != "Unknown":
                        if final_method == "Hashfile Analytics":
                            size_value = f"File upload failed. Please upload this file using Tools {final_tool} with method {final_method}"
                        else:
                            size_value = f"File upload failed. Please upload this file using Tools {final_tool}"
                    else:
                        size_value = error_message
            elif detected_tool and detected_tool != "Unknown":
                method_for_check = method if method else progress.get("method") or detected_method
                if method_for_check == "Hashfile Analytics":
                    size_value = f"File upload failed. Please upload this file using Tools {detected_tool} with method {method_for_check}"
                else:
                    size_value = f"File upload failed. Please upload this file using Tools {detected_tool}"
            else:
                size_from_progress = progress.get("size", "Upload Failed! Please try again")
                method_for_size = method if method else progress.get("method") or detected_method
                if "Please upload this file using Tools" in size_from_progress:
                    tool_match = size_from_progress.split("Tools ")[1].split()[0] if "Tools " in size_from_progress else None
                    if tool_match:
                        if method_for_size == "Hashfile Analytics":
                            size_value = f"File upload failed. Please upload this file using Tools {tool_match} with method {method_for_size}"
                        else:
                            size_value = f"File upload failed. Please upload this file using Tools {tool_match}"
                    else:
                        size_value = size_from_progress
                else:
                    size_value = size_from_progress
            
            if size_value is None:
                size_value = error_message
            
            return {
                "status": "Failed",
                "message": error_message,
                "upload_id": upload_id,
                "file_name": progress.get("file_name"),
                "size": size_value,
                "percentage": progress.get("percentage", "Error"),
                "upload_status": "Failed",
                "data": None,
            }

        else:
            return {
                "status": "Failed",
                "message": f"Unknown upload status: {status}",
                "upload_id": upload_id,
                "upload_status": "Failed",
                "data": None,
            }

    except Exception as e:
        detected_tool = None
        method = None
        
        # Determine which progress dict to use
        if type.lower() == "apk":
            prog_dict_except = APK_PROGRESS
        else:
            prog_dict_except = UPLOAD_PROGRESS
        
        try:
            prog = prog_dict_except.get(upload_id, {})
            detected_tool = prog.get("detected_tool")
            method = prog.get("method")
            
            if not method and prog.get("_ctx"):
                method = prog.get("_ctx", {}).get("method")
            
            if not detected_tool or not method:
                try:
                    svc_resp, code = upload_service.get_progress(upload_id)
                    if code == 200:
                        svc_data = svc_resp.get("data", {})
                        if not detected_tool:
                            detected_tool = svc_data.get("detected_tool")
                        if not method:
                            method = svc_data.get("method")
                except:
                    pass
        except:
            pass
        
        if detected_tool and detected_tool != "Unknown":
            final_method = method if method else "Hashfile Analytics"
            error_message = f"File upload failed. Please upload this file using Tools {detected_tool} with method {final_method}"
        else:
            error_message = "File upload failed. Please upload this file using Tools"
        
        return JSONResponse(
            {"status": "Failed", "message": error_message, "upload_id": upload_id},
            status_code=200,
        )
    
@router.get("/analytics/get-files")
def get_files(
    search: Optional[str] = Query(None, description="Search by file_name, notes, tools, or method"),
    filter: Optional[str] = Query("All", description='Method filter: "Deep Communication Analytics", "Social Media Correlation", "Contact Correlation", "Hashfile Analytics", "All"'),
    current_user: User = Depends(get_current_user),
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
        
        user_role = getattr(current_user, 'role', None)
        if user_role != "admin":
            user_fullname = getattr(current_user, 'fullname', '') or ''
            user_email = getattr(current_user, 'email', '') or ''
            if user_fullname or user_email:
                query = query.filter(
                    or_(
                        File.created_by.ilike(f"%{user_fullname}%"),
                        File.created_by.ilike(f"%{user_email}%"),
                        File.notes.ilike(f"%{user_fullname}%"),
                        File.notes.ilike(f"%{user_email}%"),
                        File.file_name.ilike(f"%{user_fullname}%"),
                        File.file_name.ilike(f"%{user_email}%")
                    )
                )

        if filter:
            if not validate_sql_injection_patterns(filter):
                return JSONResponse(
                    {
                        "status": 400,
                        "message": "Invalid characters detected in filter parameter. Please remove any SQL injection attempts or malicious code.",
                        "data": None
                    },
                    status_code=400
                )
            filter = sanitize_input(filter, max_length=100)

        if filter and filter in allowed_methods and filter != "All":
            query = query.filter(File.method == filter)

        if search:
            if not validate_sql_injection_patterns(search):
                return JSONResponse(
                    {
                        "status": 400,
                        "message": "Invalid characters detected in search parameter. Please remove any SQL injection attempts or malicious code.",
                        "data": None
                    },
                    status_code=400
                )
            search = sanitize_input(search, max_length=255)
            if search:
                term = f"%{search}%"
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
            "message": "Failed to retrieve files. Please try again later.",
                        "data": None
        }
