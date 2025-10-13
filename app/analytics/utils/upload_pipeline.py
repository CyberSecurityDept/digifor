import asyncio
import os
from pathlib import Path
from typing import Any, Dict
from fastapi import UploadFile
from app.analytics.shared.models import File
from app.analytics.device_management.service import create_device
from app.analytics.utils.sdp_crypto import encrypt_to_sdp, generate_keypair
from app.analytics.utils.parser_xlsx import parse_sheet
from app.db.session import get_db
import tempfile

# === Folder Setup ===
BASE_DIR = os.getcwd()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DATA_DIR = os.path.join(UPLOAD_DIR, "data")
ENCRYPTED_DIR = os.path.join(UPLOAD_DIR, "encrypted")
KEY_DIR = os.path.join(BASE_DIR, "keys")

for d in [UPLOAD_DIR, DATA_DIR, ENCRYPTED_DIR, KEY_DIR]:
    os.makedirs(d, exist_ok=True)


# === Helpers ===
def encrypt_and_store_file(file: UploadFile, file_bytes: bytes, public_key_path: str) -> str:
    """Encrypt file using public key and save .sdp version of the same name under uploads/encrypted/"""
    public_key_path = os.path.join(KEY_DIR, "public.key")
    private_key_path = os.path.join(KEY_DIR, "private.key")

    # 🔐 Generate keypair if not exist
    if not (os.path.exists(public_key_path) and os.path.exists(private_key_path)):
        print("⚙️ Keypair belum ada — generate baru...")
        private_key, public_key = generate_keypair()
        with open(private_key_path, "wb") as f:
            f.write(private_key)
        with open(public_key_path, "wb") as f:
            f.write(public_key)
        print(f"✅ Keypair dibuat: {public_key_path}, {private_key_path}")

    # 🔸 pakai nama file asli untuk file terenkripsi
    base_filename = Path(file.filename).stem
    encrypted_filename = f"{base_filename}.sdp"
    encrypted_path = os.path.join(ENCRYPTED_DIR, encrypted_filename)

    # Temporary file for encryption
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

    # Return relative path (for info)
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


# === Upload Service ===
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
        return {"status": 200, "message": "Cancel request received", "data": None}, 200

    # === File Upload + Encryption ===
    async def start_file_upload(
        self,
        upload_id: str,
        file: UploadFile,
        file_name: str,  # hanya untuk field file_name di DB
        notes: str,
        type: str,
        tools: str,
        file_bytes: bytes,
    ):
        """Upload file, encrypt with same name, and save record to DB."""
        if upload_id in self._progress and not self._progress[upload_id].get("done"):
            return {"status": 400, "message": "Upload ID sedang berjalan", "data": None}

        self._init_state(upload_id)

        try:
            # === Simpan file asli (pakai nama asli upload) ===
            original_filename = file.filename
            original_path_abs = os.path.join(DATA_DIR, original_filename)
            total_size = len(file_bytes)
            self._progress[upload_id].update(
                {"total_size": format_bytes(total_size), "message": "Memulai upload..."}
            )

            # Upload stage (0–60%)
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

            # Encrypt stage (60–95%)
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

            # Save record ke DB (95–100%)
            rel_path = os.path.relpath(original_path_abs, BASE_DIR)
            db = next(get_db())
            file_record = File(
                file_name=file_name,   # 🧩 dari input form user
                file_path=rel_path,    # 🧩 file asli (nama upload)
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
                "message": "Upload & encryption complete",
                "done": True,
                "file_id": file_record.id,
            })

            return {
                "status": 200,
                "message": "File uploaded & encrypted successfully",
                "data": {
                    "percent": 100,
                    "progress_size": format_bytes(total_size),
                    "total_size": format_bytes(total_size),
                    "done": True,
                    "file_id": file_record.id,
                    "encrypted_path": encrypted_path,
                },
            }

        except Exception as e:
            self._mark_done(upload_id, f"Upload error: {str(e)}")
            return {"status": 500, "message": f"Unexpected upload error: {str(e)}", "data": None}


upload_service = UploadService()
