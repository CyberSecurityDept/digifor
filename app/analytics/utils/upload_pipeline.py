import asyncio
import os
from pathlib import Path
from typing import Any, Dict
from fastapi import UploadFile
from app.analytics.shared.models import File
from app.analytics.device_management.service import create_device
from app.analytics.utils.sdp_crypto import encrypt_to_sdp, generate_keypair
from app.analytics.utils.parser_xlsx import parse_sheet
from app.analytics.utils.tools_parser import tools_parser
from app.analytics.utils.hashfile_parser import hashfile_parser
from app.analytics.utils.performance_optimizer import performance_optimizer
from app.analytics.device_management.service import save_hashfiles_to_database
from app.db.session import get_db
from app.core.config import settings
import tempfile
import time
from datetime import datetime

BASE_DIR = os.getcwd()
UPLOAD_DIR = settings.UPLOAD_DIR
APK_DIR_BASE = settings.APK_DIR
DATA_DIR = os.path.join(UPLOAD_DIR, "data")
ENCRYPTED_DIR = os.path.join(UPLOAD_DIR, "encrypted")
KEY_DIR = os.path.join(BASE_DIR, "keys")

for d in [UPLOAD_DIR, DATA_DIR, ENCRYPTED_DIR, KEY_DIR]:
    os.makedirs(d, exist_ok=True)


def encrypt_and_store_file(file: UploadFile, file_bytes: bytes, public_key_path: str) -> str:
    public_key_path = os.path.join(KEY_DIR, "public.key")
    private_key_path = os.path.join(KEY_DIR, "private.key")

    if not (os.path.exists(public_key_path) and os.path.exists(private_key_path)):
        print("Keypair belum ada - generate baru...")
        private_key, public_key = generate_keypair()
        with open(private_key_path, "wb") as f:
            f.write(private_key)
        with open(public_key_path, "wb") as f:
            f.write(public_key)
        print(f"Keypair dibuat: {public_key_path}, {private_key_path}")

    base_filename = Path(file.filename).stem
    encrypted_filename = f"{base_filename}.sdp"
    encrypted_path = os.path.join(ENCRYPTED_DIR, encrypted_filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with open(public_key_path, "rb") as f:
            pub_key = f.read()
        encrypt_to_sdp(pub_key, tmp_path, encrypted_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return os.path.relpath(encrypted_path, BASE_DIR)


def format_bytes(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i, x = 0, float(n)
    while x >= 1024 and i < len(units) - 1:
        x /= 1024.0
        i += 1
    return f"{int(x)} {units[i]}" if i == 0 else f"{x:.2f} {units[i]}"


class UploadService:
    def __init__(self):
        self._progress: Dict[str, Dict[str, Any]] = {}

    def _init_state(self, upload_id: str):
        self._progress[upload_id] = {
            "percent": 0,
            "progress_size": "0 B",
            "total_size": None,
            "cancel": False,
            "message": "Starting upload...",
            "done": False,
        }

    def _is_canceled(self, upload_id: str) -> bool:
        data = self._progress.get(upload_id)
        if not data or not isinstance(data, dict):
            return True
        return data.get("cancel", False)

    def _mark_done(self, upload_id: str, message: str):
        data = self._progress.get(upload_id)
        if not data:
            self._progress[upload_id] = {"message": message, "done": True}
        else:
            data.update({"message": message, "done": True})

    def get_progress(self, upload_id: str):
        data = self._progress.get(upload_id)
        if not data:
            return {"status": 404, "message": "Upload ID not found", "data": None}, 404
        return {
            "status": 200,
            "message": data.get("message", ""),
            "data": {
                "percent": data.get("percent", 0),
                "progress_size": data.get("progress_size", "0 B"),
                "total_size": data.get("total_size"),
                "done": data.get("done", False),
                "file_id": data.get("file_id"),
            },
        }, 200

    def cancel(self, upload_id: str):
        if upload_id not in self._progress:
            return {"status": 404, "message": "Upload ID not found", "data": None}, 404
        self._progress[upload_id]["cancel"] = True
        self._progress[upload_id]["message"] = "Canceling..."

    def _serialize_contacts_for_json(self, contacts: list) -> list:
        serialized_contacts = []
        for contact in contacts:
            serialized_contact = contact.copy()
            if 'last_time_contacted' in serialized_contact and serialized_contact['last_time_contacted']:
                if isinstance(serialized_contact['last_time_contacted'], datetime):
                    serialized_contact['last_time_contacted'] = serialized_contact['last_time_contacted'].isoformat()
            serialized_contacts.append(serialized_contact)
        return serialized_contacts

    async def start_file_upload(
        self,
        upload_id: str,
        file: UploadFile,
        file_name: str,
        notes: str,
        type: str,
        tools: str,
        file_bytes: bytes,
    ):
        start_time = time.time()
        if upload_id in self._progress and not self._progress[upload_id].get("done"):
            return {"status": 400, "message": "Upload ID sedang berjalan", "data": None}

        self._init_state(upload_id)

        try:
            original_filename = file.filename
            original_path_abs = os.path.join(DATA_DIR, original_filename)
            total_size = len(file_bytes)
            self._progress[upload_id].update(
                {"total_size": format_bytes(total_size), "message": "Memulai upload..."}
            )

            chunk_size = 1024 * 512
            written = 0
            with open(original_path_abs, "wb") as f:
                for i in range(0, total_size, chunk_size):
                    if self._is_canceled(upload_id):
                        self._mark_done(upload_id, "Upload canceled")
                        return {"status": 200, "message": "Upload canceled", "data": {"done": True}}

                    chunk = file_bytes[i:i + chunk_size]
                    f.write(chunk)
                    written += len(chunk)

                    percent = (written / total_size) * 60
                    progress_bytes = int((percent / 100) * total_size)
                    self._progress[upload_id].update({
                        "percent": round(percent, 2),
                        "progress_size": format_bytes(progress_bytes),
                        "message": f"Uploading... ({percent:.2f}%)",
                    })
                    await asyncio.sleep(0.02)

            self._progress[upload_id]["message"] = "Encrypting file..."
            public_key_path = os.path.join(KEY_DIR, "public.key")
            encrypted_path = encrypt_and_store_file(file, file_bytes, public_key_path)

            for i in range(60, 95):
                if self._is_canceled(upload_id):
                    self._mark_done(upload_id, "Encryption canceled")
                    return {"status": 200, "message": "Encryption canceled", "data": {"done": True}}

                phase_ratio = (i - 60) / 35
                current_bytes = int(0.6 * total_size + phase_ratio * 0.4 * total_size)
                self._progress[upload_id].update({
                    "percent": i,
                    "progress_size": format_bytes(current_bytes),
                    "message": f"Encrypting... ({i}%)"
                })
                await asyncio.sleep(0.03)

            rel_path = os.path.relpath(original_path_abs, BASE_DIR)
            db = next(get_db())
            file_record = File(
                file_name=file_name,
                file_path=rel_path,
                notes=notes,
                type=type,
                tools=tools,
                total_size=total_size,
            )
            db.add(file_record)
            db.commit()
            db.refresh(file_record)

            self._progress[upload_id].update({
                "message": "Starting data parsing...",
                "percent": 95
            })

            parsed_data = tools_parser.parse_file(Path(original_path_abs), tools)
            
            # Parse hashfile if it's a hashfile
            hashfiles_data = []
            hashfiles_count = 0
            if "hashfile" in file_name.lower() or "hash" in file_name.lower():
                try:
                    hashfile_result = hashfile_parser.parse_hashfile(Path(original_path_abs), tools)
                    if "error" not in hashfile_result:
                        hashfiles_data = hashfile_result.get("hashfiles", [])
                        hashfiles_count = len(hashfiles_data)
                except Exception as e:
                    print(f"Hashfile parsing error: {str(e)}")
            
            parsing_result = {
                "tool_used": parsed_data.get("tool", tools),
                "contacts_count": len(parsed_data.get("contacts", [])),
                "messages_count": len(parsed_data.get("messages", [])),
                "calls_count": len(parsed_data.get("calls", [])),
                "hashfiles_count": hashfiles_count,
                "parsing_success": "error" not in parsed_data
            }

            if "error" in parsed_data:
                parsing_result["parsing_error"] = parsed_data["error"]
                parsing_result["fallback_used"] = "fallback" in parsed_data

            device_data = {
                "owner_name": "Temporary",
                "phone_number": "Temporary",
                "file_id": file_record.id
            }
            
            device_id = create_device(
                device_data=device_data,
                contacts=parsed_data.get("contacts", []),
                messages=parsed_data.get("messages", []),
                calls=parsed_data.get("calls", [])
            )
            
            if hashfiles_data:
                try:
                    saved_hashfiles = save_hashfiles_to_database(device_id, hashfiles_data, tools)
                    parsing_result["hashfiles_saved"] = saved_hashfiles
                except Exception as e:
                    print(f"Error saving hashfiles to database: {str(e)}")
                    parsing_result["hashfiles_save_error"] = str(e)

            self._progress[upload_id].update({
                "percent": 100,
                "progress_size": format_bytes(total_size),
                "message": "Upload, encryption & parsing complete",
                "done": True,
                "file_id": file_record.id,
            })

            # Optimize response for large datasets
            total_records = len(parsed_data.get("contacts", [])) + len(parsed_data.get("messages", [])) + len(parsed_data.get("calls", []))
            
            if total_records > 5000:  # Threshold for large datasets
                response_data = performance_optimizer.create_summary_response(
                    total_records=total_records,
                    file_size=total_size,
                    processing_time=time.time() - start_time
                )
                response_data["data"].update({
                    "file_id": file_record.id,
                    "device_id": device_id,
                    "upload_id": upload_id,
                    "percentage": 100,
                    "progress_size": format_bytes(total_size),
                    "total_size": format_bytes(total_size),
                    "done": True,
                    "encrypted_path": encrypted_path,
                    "parsing_result": parsing_result
                })
            else:
                # For smaller datasets, return full data
                response_data = {
                    "status": 200,
                    "message": "File uploaded, encrypted & parsed successfully",
                    "data": {
                        "file_id": file_record.id,
                        "device_id": device_id,
                        "upload_id": upload_id,
                        "percentage": 100,
                        "progress_size": format_bytes(total_size),
                        "total_size": format_bytes(total_size),
                        "done": True,
                        "encrypted_path": encrypted_path,
                        "parsing_result": parsing_result,
                        "parsed_data": {
                            "contacts": self._serialize_contacts_for_json(parsed_data.get("contacts", [])),
                            "messages": parsed_data.get("messages", []),
                            "calls": parsed_data.get("calls", [])
                        }
                    },
                }
            
            return response_data

        except Exception as e:
            self._mark_done(upload_id, f"Upload error: {str(e)}")
            return {"status": 500, "message": f"Unexpected upload error: {str(e)}", "data": None}

    async def start_device_processing(
        self,
        upload_id: str,
        file_id: int,
        owner_name: str,
        phone_number: str,
        tools: str,
        device_id: int = None
    ) -> Dict[str, Any]:
        try:
            db = next(get_db())
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return {"status": 404, "message": "File not found", "data": None}
            
            self._init_state(upload_id)
            self._progress[upload_id].update({
                "message": f"Processing with {tools} parser...",
                "percent": 10
            })
            
            file_path = Path(file_record.file_path)
            if not file_path.exists():
                return {"status": 404, "message": "File not found on disk", "data": None}
            
            self._progress[upload_id].update({
                "message": f"Parsing {tools} format...",
                "percent": 30
            })
            
            parsed_data = tools_parser.parse_file(file_path, tools)
            
            if "error" in parsed_data:
                self._progress[upload_id].update({
                    "message": f"Parser error: {parsed_data['error']}",
                    "percent": 50
                })

                parsed_data = parsed_data.get("fallback", {})
            
            self._progress[upload_id].update({
                "message": "Creating device record...",
                "percent": 70
            })
            
            if device_id:
                device_data = {
                    "owner_name": owner_name,
                    "phone_number": phone_number,
                    "file_id": file_id
                }
                
                device_id = create_device(
                    device_data=device_data,
                    contacts=parsed_data.get("contacts", []),
                    messages=parsed_data.get("messages", []),
                    calls=parsed_data.get("calls", []),
                    existing_device_id=device_id
                )
            else:
                device_data = {
                    "owner_name": owner_name,
                    "phone_number": phone_number,
                    "file_id": file_id
                }
                
                device_id = create_device(
                    device_data=device_data,
                    contacts=parsed_data.get("contacts", []),
                    messages=parsed_data.get("messages", []),
                    calls=parsed_data.get("calls", [])
                )
            
            self._progress[upload_id].update({
                "message": "Device processing complete",
                "percent": 100,
                "done": True,
                "device_id": device_id,
                "parsed_data": {
                    "tool": parsed_data.get("tool", "Forensic Tool"),
                    "contacts_count": len(parsed_data.get("contacts", [])),
                    "messages_count": len(parsed_data.get("messages", [])),
                    "calls_count": len(parsed_data.get("calls", []))
                }
            })
            
            return {
                "status": 200,
                "message": "Device processing completed successfully",
                "data": {
                    "device_id": device_id,
                    "tool_used": parsed_data.get("tool", "Forensic Tool"),
                    "parsed_data": {
                        "contacts_count": len(parsed_data.get("contacts", [])),
                        "messages_count": len(parsed_data.get("messages", [])),
                        "calls_count": len(parsed_data.get("calls", []))
                    }
                }
            }
            
        except Exception as e:
            self._mark_done(upload_id, f"Device processing error: {str(e)}")
            return {"status": 500, "message": f"Device processing error: {str(e)}", "data": None}

    async def start_upload_and_process(
        self,
        file_id: int,
        owner_name: str,
        phone_number: str,
        device_id: int = None
    ) -> Dict[str, Any]:
        try:
            db = next(get_db())
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return {"status": 404, "message": "File not found", "data": None}
            
            upload_id = f"process_{file_id}_{int(time.time())}"
            
            return await self.start_device_processing(
                upload_id=upload_id,
                file_id=file_id,
                owner_name=owner_name,
                phone_number=phone_number,
                tools=file_record.tools,
                device_id=device_id
            )
            
        except Exception as e:
            return {"status": 500, "message": f"Processing error: {str(e)}", "data": None}

    async def start_app_upload(
        self,
        upload_id: str,
        file: UploadFile,
        file_name: str,
        notes: str,
        type:str,
        tools: str,
        file_bytes: bytes,
    ):
        APK_DIR = os.path.join(APK_DIR_BASE, "apk")
        os.makedirs(APK_DIR, exist_ok=True)

        if upload_id in self._progress and not self._progress[upload_id].get("done"):
            return {"status": 400, "message": "Upload ID sedang berjalan", "data": None}

        self._init_state(upload_id)

        try:
            safe_filename = Path(file.filename).name
            target_path = os.path.join(APK_DIR, safe_filename)
            total_size = len(file_bytes)

            self._progress[upload_id].update(
                {"total_size": format_bytes(total_size), "message": "Memulai upload..."}
            )

            chunk_size = 1024 * 512
            written = 0
            with open(target_path, "wb") as f:
                for i in range(0, total_size, chunk_size):
                    if self._is_canceled(upload_id):
                        self._mark_done(upload_id, "Upload canceled")
                        return {"status": 200, "message": "Upload canceled", "data": {"done": True}}

                    chunk = file_bytes[i:i + chunk_size]
                    f.write(chunk)
                    written += len(chunk)

                    percent = (written / total_size) * 100
                    progress_bytes = int((percent / 100) * total_size)
                    self._progress[upload_id].update({
                        "percent": round(percent, 2),
                        "progress_size": format_bytes(progress_bytes),
                        "message": f"Uploading app... ({percent:.2f}%)",
                    })
                    await asyncio.sleep(0.02)

            rel_path = os.path.relpath(target_path, BASE_DIR)
            db = next(get_db())
            file_record = File(
                file_name=file_name,   
                file_path=rel_path,
                notes=notes,
                type=type,
                tools=tools,
            )
            db.add(file_record)
            db.commit()
            db.refresh(file_record)

            self._progress[upload_id].update({
                "percent": 100,
                "progress_size": format_bytes(total_size),
                "message": "App upload complete",
                "done": True,
                "file_id": file_record.id,
            })

            return {
                "status": 200,
                "message": "Application uploaded successfully",
                "data": {
                    "percent": 100,
                    "progress_size": format_bytes(total_size),
                    "total_size": format_bytes(total_size),
                    "done": True,
                    "file_id": file_record.id,
                    "file_path": rel_path,
                },
            }

        except Exception as e:
            self._mark_done(upload_id, f"App upload error: {str(e)}")
            return {"status": 500, "message": f"Unexpected app upload error: {str(e)}", "data": None}
upload_service = UploadService()
