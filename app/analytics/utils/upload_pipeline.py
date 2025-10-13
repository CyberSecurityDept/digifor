import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Tuple

from app.analytics.models import File
from app.analytics.service import encrypt_and_store_file, format_bytes, create_device
from app.analytics.utils.parser_xlsx import parse_sheet
from app.db.session import get_db


class UploadService:
    def __init__(self) -> None:
        self._progress: Dict[str, Dict[str, Any]] = {}

    # --------- State helpers ---------
    def _init_state(self, upload_id: str) -> None:
        self._progress[upload_id] = {
            "percent": 0,
            "progress_size": "0 B",
            "total_size": None,
            "cancel": False,
            "message": "Starting process...",
            "done": False,
        }

    def _is_canceled(self, upload_id: str) -> bool:
        return self._progress.get(upload_id, {}).get("cancel", False)

    def get_progress(self, upload_id: str) -> Tuple[Dict[str, Any], int]:
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
                "device_id": data.get("device_id"),
            },
        }, 200

    def cancel(self, upload_id: str) -> Tuple[Dict[str, Any], int]:
        if upload_id not in self._progress:
            return {"status": 404, "message": "Upload ID not found", "data": None}, 404

        self._progress[upload_id]["cancel"] = True
        self._progress[upload_id]["message"] = "Canceling..."
        return {"status": 200, "message": "Cancel request received", "data": None}, 200

    # --------- Main entry point ---------
    async def start_upload_and_process(
        self,
        file_id: int,
        owner_name: str,
        phone_number: str,
        upload_id: str,
    ) -> Dict[str, Any]:
        """Mulai proses dari file yang sudah diupload sebelumnya (by file_id)."""

        if upload_id in self._progress and not self._progress[upload_id].get("done"):
            return {"status": 400, "message": "Process with same ID is already running", "data": None}

        self._init_state(upload_id)
        await asyncio.sleep(0.2)
        db = next(get_db())

        try:
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return {"status": 404, "message": f"File with id {file_id} not found", "data": None}

            file_path = file_record.file_path
            if not file_path or not os.path.exists(file_path):
                return {"status": 404, "message": f"File not found at {file_path}", "data": None}

            file_size = os.path.getsize(file_path)
            self._progress[upload_id].update({
                "percent": 5,
                "progress_size": format_bytes(file_size),
                "total_size": format_bytes(file_size),
                "message": "File found, preparing process...",
            })

            asyncio.create_task(
                self._process_after_upload(
                    upload_id=upload_id,
                    file_path=file_path,
                    orig_filename=file_record.file_name,
                    owner_name=owner_name,
                    phone_number=phone_number,
                    file_id=file_id,
                )
            )

            return {"status": 200, "message": "File accepted for processing", "data": None}

        except Exception as e:
            self._progress[upload_id].update({"message": f"Unexpected error: {str(e)}", "done": True})
            return {"status": 500, "message": f"Error: {str(e)}", "data": None}

    # --------- Background process (with smooth percent updates) ---------
    async def _process_after_upload(
        self,
        upload_id: str,
        file_path: str,
        orig_filename: str,
        owner_name: str,
        phone_number: str,
        file_id: int,
    ) -> None:
        try:
            total_size = os.path.getsize(file_path)

            # ----------- PARSING STAGE -----------
            self._progress[upload_id].update({"message": "Parsing Excel sheets..."})
            for i in range(5, 35, 3):
                if self._is_canceled(upload_id):
                    return self._mark_done(upload_id, "Canceled during parsing")
                self._progress[upload_id]["percent"] = i

                # 🧠 Tambahkan simulasi progress size
                partial_size = int((i / 100) * total_size)
                self._progress[upload_id]["progress_size"] = format_bytes(partial_size)

                await asyncio.sleep(0.2)

            contacts = parse_sheet(Path(file_path), "contacts") or []
            messages = parse_sheet(Path(file_path), "messages") or []
            calls = parse_sheet(Path(file_path), "calls") or []

            # ----------- ENCRYPTION STAGE -----------
            self._progress[upload_id].update({"message": "Encrypting file..."})
            public_key_path = os.path.join(os.getcwd(), "keys", "public.key")
            if not os.path.exists(public_key_path):
                return self._mark_done(upload_id, f"Public key not found at {public_key_path}")

            for i in range(35, 70, 3):
                if self._is_canceled(upload_id):
                    return self._mark_done(upload_id, "Canceled during encryption")
                self._progress[upload_id]["percent"] = i

                # 🧠 Update progress_size juga di tahap ini
                partial_size = int((i / 100) * total_size)
                self._progress[upload_id]["progress_size"] = format_bytes(partial_size)

                await asyncio.sleep(0.15)

            with open(file_path, "rb") as f:
                file_bytes = f.read()
            encrypted_path = encrypt_and_store_file(orig_filename, file_bytes, public_key_path)

            # ----------- SAVING TO DATABASE -----------
            self._progress[upload_id].update({"message": "Saving to database..."})
            for i in range(70, 95, 4):
                if self._is_canceled(upload_id):
                    return self._mark_done(upload_id, "Canceled during saving")
                self._progress[upload_id]["percent"] = i

                partial_size = int((i / 100) * total_size)
                self._progress[upload_id]["progress_size"] = format_bytes(partial_size)

                await asyncio.sleep(0.2)

            # ----------- SIMPAN DEVICE -----------
            device_data = {
                "owner_name": owner_name,
                "phone_number": phone_number,
                "file_id": file_id,
                "file_path": encrypted_path,
            }

            device_id = create_device(
                device_data=device_data,
                contacts=contacts,
                messages=messages,
                calls=calls,
            )

            # ----------- COMPLETE -----------
            self._progress[upload_id].update({
                "percent": 100,
                "progress_size": format_bytes(total_size),
                "message": "All steps completed successfully",
                "device_id": device_id,
                "done": True,
            })

        except Exception as e:
            self._mark_done(upload_id, f"Processing error: {str(e)}")


    def _mark_done(self, upload_id: str, message: str):
        self._progress[upload_id].update({"message": message, "done": True})


upload_service = UploadService()
