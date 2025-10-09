import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import UploadFile

# Pakai util & repo yang sudah ada di project-mu
from app.analytics.service import encrypt_and_store_file, format_bytes
from app.analytics.utils.parser_xlsx import parse_sheet
from app.analytics.service import create_device


class UploadService:
    def __init__(self) -> None:
        # state global sederhana (single-process). Untuk production multi-worker, gunakan Redis/DB.
        self._progress: Dict[str, Dict[str, Any]] = {}

    # --------- State helpers ---------
    def _init_state(self, upload_id: str) -> None:
        self._progress[upload_id] = {
            "percent": 0,
            "progress_size": "0 B",
            "total_size": None,
            "cancel": False,
            "message": "Starting upload...",
            "done": False,
        }

    def _is_canceled(self, upload_id: str) -> bool:
        """Helper untuk cek cancel status"""
        return self._progress.get(upload_id, {}).get("cancel", False)

    def get_progress(self, upload_id: str) -> Tuple[Dict[str, Any], int]:
        data = self._progress.get(upload_id)
        if not data:
            return {
                "status": 404,
                "message": "Upload ID not found",
                "data": None
            }, 404
        
        return {
            "status": 200,
            "message": data.get("message", ""),
            "data": {
                "percent": data.get("percent", 0),
                "progress_size": data.get("progress_size", "0 B"),
                "total_size": data.get("total_size"),
                "done": data.get("done", False),
                "device_id": data.get("device_id"),
            }
        }, 200

    def cancel(self, upload_id: str) -> Tuple[Dict[str, Any], int]:
        if upload_id not in self._progress:
            return {
                "status": 404,
                "message": "Upload ID not found",
                "data": None
            }, 404
        
        # Set cancel flag
        self._progress[upload_id]["cancel"] = True
        self._progress[upload_id]["message"] = "Canceling..."
        
        return {
            "status": 200,
            "message": "Cancel request received",
            "data": None
        }, 200

    # --------- Public API ---------
    async def start_upload_and_process(
        self,
        file: UploadFile,
        analytic_id: int,
        owner_name: str,
        phone_number: str,
        social_media: Optional[str],
        upload_id: str,
    ) -> Dict[str, Any]:
        
        # blokir ID duplikat yang belum selesai
        if upload_id in self._progress and not self._progress[upload_id].get("done"):
            return {"status": 400, "message": "Upload with same ID is in progress", "data": None}

        self._init_state(upload_id)
        await asyncio.sleep(0.5)  # Jeda agar state awal terbaca

        tmp_path = None
        try:
            # Deteksi total size stream (tidak selalu ada)
            try:
                cur = file.file.tell()
                file.file.seek(0, os.SEEK_END)
                total_size = file.file.tell()
                file.file.seek(cur, os.SEEK_SET)
            except Exception:
                total_size = 0

            bytes_read = 0
            CHUNK = 1024 * 256  # 256 KB (lebih kecil agar progress lebih terlihat)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp_name = tmp.name
                
                while True:
                    # Cek cancel sebelum baca chunk
                    if self._is_canceled(upload_id):
                        tmp.close()
                        try:
                            os.remove(tmp_name)
                        except Exception:
                            pass
                        self._progress[upload_id].update({
                            "message": "Upload canceled by user",
                            "done": True,
                        })
                        return {"status": 499, "message": "Upload canceled by user", "data": None}

                    chunk = await file.read(CHUNK)
                    if not chunk:
                        break

                    tmp.write(chunk)
                    bytes_read += len(chunk)

                    if total_size > 0:
                        percent = max(0, min(99, int((bytes_read / total_size) * 100)))
                        self._progress[upload_id].update({
                            "percent": percent,
                            "progress_size": format_bytes(bytes_read),
                            "total_size": format_bytes(total_size),
                            "message": "Uploading...",
                        })
                    else:
                        self._progress[upload_id].update({
                            "percent": 0,
                            "progress_size": format_bytes(bytes_read),
                            "total_size": None,
                            "message": "Uploading...",
                        })

                    # Jeda agar progress bisa terbaca
                    await asyncio.sleep(0.1)

            # Cek cancel setelah upload selesai
            if self._is_canceled(upload_id):
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": "Upload canceled by user",
                    "done": True,
                })
                return {"status": 499, "message": "Upload canceled by user", "data": None}

            tmp_path = Path(tmp_name)
            final_total = total_size if total_size > 0 else bytes_read
            
            self._progress[upload_id].update({
                "percent": 100,
                "progress_size": format_bytes(final_total),
                "total_size": format_bytes(final_total),
                "message": "Upload complete, processing...",
            })
            
            # Jeda sebelum mulai processing
            await asyncio.sleep(0.5)

            # Cek cancel sebelum processing
            if self._is_canceled(upload_id):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": "Canceled before processing",
                    "done": True,
                })
                return {"status": 499, "message": "Upload canceled by user", "data": None}

            # mulai processing di background
            asyncio.create_task(
                self._process_after_upload(
                    upload_id=upload_id,
                    tmp_path=str(tmp_path),
                    orig_filename=file.filename,
                    analytic_id=analytic_id,
                    owner_name=owner_name,
                    phone_number=phone_number,
                    social_media=social_media,
                )
            )

            return {
                "status": 200, 
                "message": "Upload completed", 
                "data": None
            }

        except Exception as e:
            self._progress[upload_id].update({
                "message": f"Unexpected error during upload: {str(e)}",
                "done": True,
            })
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return {"status": 500, "message": "Upload failed", "data": None}

    # --------- Background processing ---------
    async def _process_after_upload(
        self,
        upload_id: str,
        tmp_path: str,
        orig_filename: str,
        analytic_id: int,
        owner_name: str,
        phone_number: str,
        social_media: Optional[str],
    ) -> None:
        try:
            # Cek cancel sebelum mulai parsing
            if self._is_canceled(upload_id):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": "Canceled before processing",
                    "done": True,
                })
                return

            # 1) Parse
            self._progress[upload_id].update({
                "message": "Parsing sheets..."
            })
            await asyncio.sleep(0.5)  # Jeda agar terbaca
            
            # Cek cancel sebelum parsing
            if self._is_canceled(upload_id):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": "Canceled during parsing",
                    "done": True,
                })
                return

            contacts = parse_sheet(Path(tmp_path), "contacts") or []
            messages = parse_sheet(Path(tmp_path), "messages") or []
            calls = parse_sheet(Path(tmp_path), "calls") or []

            # Cek cancel setelah parsing
            if self._is_canceled(upload_id):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": "Canceled after parsing",
                    "done": True,
                })
                return

            # 2) Encrypt
            public_key_path = os.path.join(os.getcwd(), "keys", "public.key")
            if not os.path.exists(public_key_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": f"Public key tidak ditemukan: {public_key_path}",
                    "done": True,
                })
                return

            self._progress[upload_id].update({
                "message": "Encrypting file..."
            })
            await asyncio.sleep(0.5)  # Jeda agar terbaca
            
            # Cek cancel sebelum encrypt
            if self._is_canceled(upload_id):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": "Canceled during encryption",
                    "done": True,
                })
                return

            with open(tmp_path, "rb") as f:
                file_bytes = f.read()
            encrypted_path = encrypt_and_store_file(orig_filename, file_bytes, public_key_path)

            # Cek cancel setelah encrypt
            if self._is_canceled(upload_id):
                # Hapus file encrypted yang sudah dibuat
                try:
                    if os.path.exists(encrypted_path):
                        os.remove(encrypted_path)
                    os.remove(tmp_path)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": "Canceled after encryption",
                    "done": True,
                })
                return

            # 3) Save DB
            self._progress[upload_id].update({
                "message": "Saving to database..."
            })
            await asyncio.sleep(0.5)  # Jeda agar terbaca
            
            # CEK CANCEL TERAKHIR SEBELUM SAVE DB (CRITICAL!)
            if self._is_canceled(upload_id):
                # Hapus file encrypted
                try:
                    if os.path.exists(encrypted_path):
                        os.remove(encrypted_path)
                    os.remove(tmp_path)
                except Exception:
                    pass
                self._progress[upload_id].update({
                    "message": "Canceled before saving to database",
                    "done": True,
                })
                return

            social_media_obj = json.loads(social_media) if social_media else {}
            device_data = {
                "analytic_id": analytic_id,
                "owner_name": owner_name,
                "phone_number": phone_number,
                "social_media": social_media_obj,
                "file_path": encrypted_path,
            }
            
            device_id = create_device(
                device_data=device_data,
                contacts=contacts,
                messages=messages,
                calls=calls,
            )

            # Sukses!
            self._progress[upload_id].update({
                "message": "All steps completed successfully",
                "device_id": device_id,
                "done": True,
            })

        except Exception as e:
            self._progress[upload_id].update({
                "message": f"Processing error: {str(e)}",
                "done": True,
            })
        finally:
            # Cleanup temp file
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
upload_service = UploadService()