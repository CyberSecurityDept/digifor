from fastapi import APIRouter, UploadFile, File as FastAPIFile, Query  
from fastapi.responses import JSONResponse, FileResponse  
import os,re,json,asyncio, uuid
from datetime import datetime
from app.analytics.utils.sdp_crypto import encrypt_to_sdp, generate_keypair  

router = APIRouter()

CONVERT_PROGRESS = {}

def _sanitize_name(name: str) -> str:
    base = os.path.basename(name)
    base = re.sub(r"\s+", "_", base)
    base = re.sub(r"[^A-Za-z0-9_.-]", "", base)
    base = re.sub(r"_+", "_", base).strip("._")
    return base

@router.post("/file-encryptor/convert-to-sdp")
async def prepare_convert_to_sdp(file: UploadFile = FastAPIFile(...)):
    try:
        allowed = {"xlsx", "xls", "csv", "txt"}
        base_dir = os.getcwd()
        tmp_dir = os.path.join(base_dir, "data", "uploads", "tmp")
        converted_dir = os.path.join(base_dir, "data", "uploads", "converted")
        os.makedirs(tmp_dir, exist_ok=True)
        os.makedirs(converted_dir, exist_ok=True)

        keys_dir = os.path.join(base_dir, "keys")
        os.makedirs(keys_dir, exist_ok=True)
        pub_path = os.path.join(keys_dir, "public.key")
        priv_path = os.path.join(keys_dir, "private.key")
        if not (os.path.exists(pub_path) and os.path.exists(priv_path)):
            private_key, public_key = generate_keypair()
            with open(priv_path, "wb") as f:
                f.write(private_key)
            with open(pub_path, "wb") as f:
                f.write(public_key)

        filename = file.filename or "uploaded"
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in allowed:
            return JSONResponse(
                {
                    "status": 400,
                    "message": f"Invalid file type. Allowed extensions: {sorted(list(allowed))}"
                },
                status_code=400
            )

        safe_name = _sanitize_name(filename)
        src_tmp_path = os.path.join(tmp_dir, safe_name)
        content = await file.read()
        with open(src_tmp_path, "wb") as f:
            f.write(content)

        upload_id = safe_name

        CONVERT_PROGRESS[upload_id] = {
            "status": "waiting",
            "progress": 0,
            "message": "File ready for conversion.",
            "src_path": src_tmp_path
        }

        return JSONResponse(
            {
                "status": 200,
                "message": "File uploaded successfully and is ready for conversion.",
                "data": {
                    "upload_id": upload_id,
                }
            },
            status_code=200
        )

    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Preparation error: {str(e)}"},
            status_code=500
        )

@router.get("/file-encryptor/progress")
async def get_convert_progress(upload_id: str = Query(..., description="Upload ID")):
    try:
        progress = CONVERT_PROGRESS.get(upload_id)
        if not progress:
            return JSONResponse(
                {"status": 404, "message": "No progress data found or conversion not initialized."},
                status_code=404
            )

        if progress["status"] == "waiting":
            CONVERT_PROGRESS[upload_id]["status"] = "converting"
            CONVERT_PROGRESS[upload_id]["message"] = "Starting conversion..."
            asyncio.create_task(run_conversion(upload_id))

        return JSONResponse(
            {
                "status": 200,
                "message": "Progress retrieved successfully.",
                "data": {
                    "status": CONVERT_PROGRESS[upload_id]["status"],
                    "progress": CONVERT_PROGRESS[upload_id]["progress"],
                    "message": CONVERT_PROGRESS[upload_id]["message"]
                }
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Progress check error: {str(e)}"}, status_code=500)

async def run_conversion(upload_id: str):
    try:
        base_dir = os.getcwd()
        converted_dir = os.path.join(base_dir, "data", "uploads", "converted")
        os.makedirs(converted_dir, exist_ok=True)

        pub_path = os.path.join(base_dir, "keys", "public.key")
        with open(pub_path, "rb") as f:
            pub_key = f.read()

        src_path = CONVERT_PROGRESS[upload_id]["src_path"]
        safe_name = os.path.basename(src_path)
        unique_id = uuid.uuid4().hex[:10]
        base, ext = os.path.splitext(safe_name)
        ext = ext.lstrip('.')
        out_name = f"{base}_{unique_id}.{ext}.sdp"      
        out_path = os.path.join(converted_dir, out_name)

        for step in range(1, 6):
            CONVERT_PROGRESS[upload_id]["progress"] = step * 20
            CONVERT_PROGRESS[upload_id]["message"] = f"Converting... {step * 20}%"
            await asyncio.sleep(0.5)

        encrypt_to_sdp(pub_key, src_path, out_path)

        metadata_path = os.path.join(converted_dir, "converted_files.json")
        new_entry = {
            "original_filename": safe_name,
            "converted_filename": out_name,
            "timestamp": datetime.now().isoformat()
        }

        data = []
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

        data.append(new_entry)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        CONVERT_PROGRESS[upload_id].update({
            "status": "converted",
            "progress": 100,
            "message": "File successfully converted to .sdp."
        })

    except Exception as e:
        CONVERT_PROGRESS[upload_id].update({
            "status": "error",
            "message": f"Conversion failed: {str(e)}"
        })

@router.get("/file-encryptor/list-sdp")
def list_sdp_files():
    try:
        base_dir = os.getcwd()
        converted_dir = os.path.join(base_dir, "data", "uploads", "converted")
        metadata_path = os.path.join(converted_dir, "converted_files.json")

        if not os.path.exists(metadata_path):
            return JSONResponse(
                {"status": 404, "message": "No converted file records found."},
                status_code=404
            )

        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            try:
                data.sort(
                    key=lambda x: x.get("timestamp", ""),
                    reverse=True
                )
            except Exception as e:
                print(f"Warning: failed to sort data by timestamp: {e}")

        return JSONResponse(
            {"status": 200, "message": "Successfully retrieved SDP file list.", "data": data},
            status_code=200
        )

    except Exception as e:
        return JSONResponse(
            {"status": 500, "message": f"Error reading file list: {str(e)}"},
            status_code=500
        )

@router.get("/file-encryptor/download-sdp")
def download_sdp(
    filename: str = Query(..., description="The name of the .sdp file located in the converted folder."),
):
    try:
        if not filename.lower().endswith(".sdp"):
            return JSONResponse(
                {"status": 400, "message": "The filename must end with '.sdp'."},
                status_code=400
            )

        base_dir = os.getcwd()
        converted_dir = os.path.join(base_dir, "data", "uploads", "converted")
        src_path = os.path.join(converted_dir, filename)
        if not os.path.exists(src_path):
            return JSONResponse(
                {"status": 404, "message": f"File not found or not available for download: {filename}"},
                status_code=404
            )

        return FileResponse(
            src_path,
            filename=filename,
            media_type="application/octet-stream",
        )
    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Download error: {str(e)}"}, status_code=500)
