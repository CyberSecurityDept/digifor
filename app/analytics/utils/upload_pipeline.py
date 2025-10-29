import asyncio
import os
from pathlib import Path
from typing import Any, Dict
from fastapi import UploadFile  # type: ignore
from app.analytics.shared.models import File
from app.analytics.device_management.service import create_device
from app.analytics.utils.sdp_crypto import encrypt_to_sdp, generate_keypair
from app.analytics.utils.tools_parser import tools_parser
from app.analytics.utils.performance_optimizer import performance_optimizer
from app.analytics.device_management.service import save_hashfiles_to_database
from app.db.session import get_db
from app.core.config import settings
import tempfile
import time
from datetime import datetime
from app.analytics.utils.social_media_parser import SocialMediaParser

sm_db = next(get_db())
sm_parser = SocialMediaParser(db=sm_db)

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

    file_extension = Path(file.filename).suffix.lower()
    if file_extension == '.csv':
        suffix = '.csv'
    elif file_extension == '.txt':
        suffix = '.txt'
    else:
        suffix = '.xlsx'
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
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
        method: str = None,
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

            self._progress[upload_id].update({
                "message": "Starting data parsing...",
                "percent": 95
            })

            parsed_data = tools_parser.parse_file(Path(original_path_abs), tools)
            
            hashfiles_data = []
            hashfiles_count = 0
            
            is_hashfile = (
                "hashfile" in file_name.lower() or 
                "hash" in file_name.lower() or
                file_name.lower().endswith(('.txt', '.csv', '.xml')) or
                ('cellebrite' in file_name.lower() and file_name.lower().endswith('.xlsx')) or
                ('oxygen' in file_name.lower() and 'hashfile' in file_name.lower()) or
                ('encase' in file_name.lower() and file_name.lower().endswith('.txt')) or
                ('magnet' in file_name.lower() and file_name.lower().endswith('.csv'))
            )
            
            if is_hashfile:
                try:
                    hashfile_result = {"hashfiles": []}
                    if "error" not in hashfile_result:
                        hashfiles_data = hashfile_result.get("hashfiles", [])
                        hashfiles_count = len(hashfiles_data)
                    else:
                        pass
                except Exception as e:
                    pass
            
            
            is_social_media = (
                "social" in file_name.lower() or
                "instagram" in file_name.lower() or
                "facebook" in file_name.lower() or
                "whatsapp" in file_name.lower() or
                "telegram" in file_name.lower() or
                "twitter" in file_name.lower() or
                "x" in file_name.lower() or
                "tiktok" in file_name.lower() or
                ('axiom' in file_name.lower() and file_name.lower().endswith('.xlsx')) or
                ('cellebrite' in file_name.lower() and file_name.lower().endswith('.xlsx')) or
                ('oxygen' in file_name.lower() and file_name.lower().endswith('.xls'))
            )
            social_media_count = 0
            if is_social_media:
                try:
                    if tools.lower() in ['axiom', 'magnet axiom']:
                        social_media_count = sm_parser.count_axiom_social_media(original_path_abs)
                    elif tools.lower() == 'cellebrite':
                        social_media_count = sm_parser.count_cellebrite_social_media(original_path_abs)
                    else:
                        social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, 1, 1)
                        social_media_count = len(social_media_result) if social_media_result else 0
                except Exception as e:
                    pass

            rel_path = os.path.relpath(original_path_abs, BASE_DIR)
            db = next(get_db())
            file_record = File(
                file_name=file_name,
                file_path=rel_path,
                file_encrypted=encrypted_path,
                notes=notes,
                type=type,
                tools=tools,
                method=method,
                total_size=total_size,
                amount_of_data=0,
            )
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            parsing_result = {
                "tool_used": parsed_data.get("tool", tools),
                "contacts_count": len(parsed_data.get("contacts", [])),
                "messages_count": len(parsed_data.get("messages", [])),
                "calls_count": len(parsed_data.get("calls", [])),
                "hashfiles_count": hashfiles_count,
                "social_media_count": social_media_count,
                "parsing_success": "error" not in parsed_data
            }

            if "error" in parsed_data:
                parsing_result["parsing_error"] = parsed_data["error"]
                parsing_result["fallback_used"] = "fallback" in parsed_data

            print(f"Parsing data with file_id only (no device_id needed)")
            
            if hashfiles_data:
                try:
                    saved_hashfiles = save_hashfiles_to_database(file_record.id, hashfiles_data, tools)
                    parsing_result["hashfiles_saved"] = saved_hashfiles
                except Exception as e:
                    parsing_result["hashfiles_save_error"] = str(e)

            if method == "Social Media Correlation":
                try:
                    if tools == "Magnet Axiom":
                        social_media_result = sm_parser.parse_axiom_social_media(original_path_abs, file_record.id)
                    elif tools == "Cellebrite":
                        social_media_result = sm_parser.parse_cellebrite_social_media(original_path_abs, file_record.id)
                    elif tools == "Oxygen":
                        try:
                            import pandas as pd
                            xls = pd.ExcelFile(original_path_abs, engine='xlrd')
                            # Check if this is a complex Oxygen UFED file with multiple social media sheets
                            social_media_sheets = ['Instagram ', 'Telegram ', 'WhatsApp Messenger ', 'X (Twitter) ', 'Users-Following ', 'Users-Followers ']
                            has_social_media_sheets = any(sheet in xls.sheet_names for sheet in social_media_sheets)
                            
                            if has_social_media_sheets:
                                # Use enhanced parser for complex Oxygen files
                                social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, file_record.id)
                            else:
                                # Use UFED parser for simple Oxygen files
                                social_media_result = sm_parser.parse_oxygen_ufed_social_media(original_path_abs, file_record.id)
                        except Exception as e:
                            print(f"Error determining Oxygen format: {e}")
                            social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, file_record.id)
                    else:
                        social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, file_record.id)
                    
                    if social_media_result:
                        parsing_result["social_media_count"] = len(social_media_result)
                except Exception as e:
                    print(f"Error parsing social media: {e}")
                    parsing_result["social_media_error"] = str(e)
            
            elif method == "Deep communication analytics":
                try:
                    if tools == "Magnet Axiom":
                        chat_messages_result = sm_parser.parse_axiom_chat_messages(original_path_abs, file_record.id)
                    elif tools == "Cellebrite":
                        chat_messages_result = sm_parser.parse_cellebrite_chat_messages(original_path_abs, file_record.id)
                    elif tools == "Oxygen":
                        chat_messages_result = []
                    else:
                        chat_messages_result = []
                    
                    if chat_messages_result:
                        parsing_result["chat_messages_count"] = len(chat_messages_result)
                except Exception as e:
                    print(f"Error parsing chat messages: {e}")
                    parsing_result["chat_messages_error"] = str(e)
            
            elif method == "Contact Correlation":
                try:
                    from app.analytics.utils.contact_parser import ContactParser
                    contact_parser = ContactParser(db=sm_db)
                    
                    if tools == "Magnet Axiom":
                        contacts_result = contact_parser.parse_axiom_contacts(original_path_abs, file_record.id)
                        calls_result = contact_parser.parse_axiom_calls(original_path_abs, file_record.id)
                    elif tools == "Cellebrite":
                        contacts_result = contact_parser.parse_cellebrite_contacts(original_path_abs, file_record.id)
                        calls_result = contact_parser.parse_cellebrite_calls(original_path_abs, file_record.id)
                    elif tools == "Oxygen":
                        contacts_result = contact_parser.parse_oxygen_contacts(original_path_abs, file_record.id)
                        calls_result = contact_parser.parse_oxygen_calls(original_path_abs, file_record.id)
                    else:
                        contacts_result = contact_parser.parse_oxygen_contacts(original_path_abs, file_record.id)
                        calls_result = contact_parser.parse_oxygen_calls(original_path_abs, file_record.id)
                    
                    if contacts_result:
                        parsing_result["contacts_count"] = len(contacts_result)
                    if calls_result:
                        parsing_result["calls_count"] = len(calls_result)
                except Exception as e:
                    print(f"Error parsing contacts/calls: {e}")
                    parsing_result["contacts_calls_error"] = str(e)
            
            elif method == "Hashfile Analytics":
                try:
                    from app.analytics.utils.hashfile_parser import HashFileParser
                    hashfile_parser_instance = HashFileParser(db=sm_db)
                    
                    is_sample_file = any(pattern in original_filename.lower() for pattern in [
                        'oxygen', 'cellebrite', 'magnet axiom', 'encase', 'hashfile'
                    ])
                    
                    if is_sample_file:
                        original_file_path = os.path.abspath(os.path.join(os.getcwd(), 'sample_hashfile', original_filename))
                    else:
                        original_file_path = original_path_abs
                    
                    hashfiles_result = hashfile_parser_instance.parse_hashfile(original_path_abs, file_record.id, tools, original_file_path)
                    
                    if hashfiles_result:
                        parsing_result["hashfiles_count"] = len(hashfiles_result)
                except Exception as e:
                    print(f"Error parsing hashfiles: {e}")
                    parsing_result["hashfiles_error"] = str(e)
            
            else:
                if is_social_media:
                    try:
                        if tools == "Magnet Axiom":
                            social_media_result = sm_parser.parse_axiom_social_media(original_path_abs, file_record.id)
                            chat_messages_result = sm_parser.parse_axiom_chat_messages(original_path_abs, file_record.id)
                        elif tools == "Cellebrite":
                            social_media_result = sm_parser.parse_cellebrite_social_media(original_path_abs, file_record.id)
                            chat_messages_result = sm_parser.parse_cellebrite_chat_messages(original_path_abs, file_record.id)
                        elif tools == "Oxygen":
                            social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, file_record.id)
                        else:  # Default to Encase parser
                            social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, file_record.id)
                        
                        if social_media_result:
                            parsing_result["social_media_count"] = len(social_media_result)
                        if chat_messages_result:
                            parsing_result["chat_messages_count"] = len(chat_messages_result)
                    except Exception as e:
                        print(f"Error parsing social media/chat: {e}")
                        parsing_result["social_media_error"] = str(e)

            # Note: DeepCommunication parsing has been moved to social media parser
            # Chat messages are now handled by parse_axiom_chat_messages above

            # Calculate actual counts from database first
            from app.analytics.device_management.models import SocialMedia, Contact, Call, HashFile, ChatMessage
            
            actual_social_media_count = db.query(SocialMedia).filter(SocialMedia.file_id == file_record.id).count()
            actual_contacts_count = db.query(Contact).filter(Contact.file_id == file_record.id).count()
            actual_calls_count = db.query(Call).filter(Call.file_id == file_record.id).count()
            actual_hashfiles_count = db.query(HashFile).filter(HashFile.file_id == file_record.id).count()
            actual_chat_messages_count = db.query(ChatMessage).filter(ChatMessage.file_id == file_record.id).count()
            
            actual_amount_of_data = actual_social_media_count + actual_contacts_count + actual_calls_count + actual_hashfiles_count + actual_chat_messages_count
            
            # Update file record with actual amount_of_data from database
            file_record.amount_of_data = actual_amount_of_data
            db.commit()
            
            print(f"Updated amount_of_data to {actual_amount_of_data} (Social Media: {actual_social_media_count}, Contacts: {actual_contacts_count}, Calls: {actual_calls_count}, Hash Files: {actual_hashfiles_count}, Chat Messages: {actual_chat_messages_count})")
            
            # Calculate amount_of_data_count based on method-based parsing results
            amount_of_data_count = (
                parsing_result.get("contacts_count", 0) +
                parsing_result.get("messages_count", 0) +
                parsing_result.get("calls_count", 0) +
                parsing_result.get("hashfiles_count", 0) +
                parsing_result.get("social_media_count", 0) +
                parsing_result.get("chat_messages_count", 0)
            )
            
            # Clean parsing_result based on method - only show relevant data
            if method == "Social Media Correlation":
                # Only show social media related data
                cleaned_parsing_result = {
                    "tool_used": parsing_result.get("tool_used"),
                    "social_media_count": actual_social_media_count,
                    "parsing_success": parsing_result.get("parsing_success", True),
                    "amount_of_data_count": actual_social_media_count
                }
                if "social_media_error" in parsing_result:
                    cleaned_parsing_result["parsing_error"] = parsing_result["social_media_error"]
            elif method == "Contact Correlation":
                # Only show contact and call related data
                cleaned_parsing_result = {
                    "tool_used": parsing_result.get("tool_used"),
                    "contacts_count": actual_contacts_count,
                    "calls_count": actual_calls_count,
                    "parsing_success": parsing_result.get("parsing_success", True),
                    "amount_of_data_count": actual_contacts_count + actual_calls_count
                }
                if "contacts_calls_error" in parsing_result:
                    cleaned_parsing_result["parsing_error"] = parsing_result["contacts_calls_error"]
            elif method == "Hashfile Analytics":
                # Only show hashfile related data
                cleaned_parsing_result = {
                    "tool_used": parsing_result.get("tool_used"),
                    "hashfiles_count": actual_hashfiles_count,
                    "parsing_success": parsing_result.get("parsing_success", True),
                    "amount_of_data_count": actual_hashfiles_count
                }
                if "hashfiles_error" in parsing_result:
                    cleaned_parsing_result["parsing_error"] = parsing_result["hashfiles_error"]
            elif method == "Deep communication analytics":
                # Only show chat messages related data
                cleaned_parsing_result = {
                    "tool_used": parsing_result.get("tool_used"),
                    "chat_messages_count": actual_chat_messages_count,
                    "parsing_success": parsing_result.get("parsing_success", True),
                    "amount_of_data_count": actual_chat_messages_count
                }
                if "chat_messages_error" in parsing_result:
                    cleaned_parsing_result["parsing_error"] = parsing_result["chat_messages_error"]
            else:
                # Default: show all data
                cleaned_parsing_result = parsing_result.copy()
                cleaned_parsing_result["amount_of_data_count"] = amount_of_data_count
            
            # Update parsing_result with cleaned version
            parsing_result = cleaned_parsing_result

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
                        "upload_id": upload_id,
                        "percentage": 100,
                        "progress_size": format_bytes(total_size),
                        "total_size": format_bytes(total_size),
                        "done": True,
                        "encrypted_path": encrypted_path,
                        "parsing_result": parsing_result
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
                
                # Create device in the same session as the parser
                from app.analytics.device_management.models import Device
                from app.utils.timezone import get_indonesia_time
                
                device = Device(
                    owner_name=device_data.get("owner_name"),
                    phone_number=device_data.get("phone_number"),
                    file_id=device_data.get("file_id"),
                    created_at=get_indonesia_time(),
                )
                
                sm_db.add(device)
                sm_db.commit()
                sm_db.refresh(device)
                device_id = device.id
                
                print(f"Created device ID {device_id} in same session as parser")
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
        method: str = None,
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
                method=method,
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
