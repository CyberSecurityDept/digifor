from fastapi import APIRouter, UploadFile, File as FastAPIFile, Query
from fastapi.responses import JSONResponse, FileResponse
import os
from app.analytics.utils.sdp_crypto import encrypt_to_sdp, generate_keypair
import re
import io
import zipfile


router = APIRouter()


def _sanitize_name(name: str) -> str:
    base = os.path.basename(name)
    base = re.sub(r"\s+", "_", base)
    base = re.sub(r"[^A-Za-z0-9_.-]", "", base)
    base = re.sub(r"_+", "_", base).strip("._")
    return base


@router.post("/analytics/convert-to-sdp")
async def convert_to_sdp(
    file: UploadFile = FastAPIFile(...),
):
    try:
        allowed = {"xlsx", "xls", "csv", "txt"}
        base_dir = os.getcwd()
        tmp_dir = os.path.join(base_dir, "data", "uploads", "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        converted_dir = os.path.join(base_dir, "data", "uploads", "converted")
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
        with open(pub_path, "rb") as f:
            pub_key = f.read()

        filename = file.filename or "uploaded"
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in allowed:
            return JSONResponse(
                {
                    "status": 400,
                    "message": f"Invalid source extension. Allowed: {sorted(list(allowed))}"
                },
                status_code=400
            )

        safe_name = _sanitize_name(filename)
        src_tmp_path = os.path.join(tmp_dir, safe_name)
        content = await file.read()
        with open(src_tmp_path, "wb") as f:
            f.write(content)

        out_name = f"{safe_name}.sdp"
        out_path = os.path.join(converted_dir, out_name)
        encrypt_to_sdp(pub_key, src_tmp_path, out_path)

        return JSONResponse(
            {
                "status": 200,
                "message": "Successfully convert file to .sdp",
                "data": [{"file": out_name, "status": "Converted"}]
            },
            status_code=200
        )

    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Convert error: {str(e)}"}, status_code=500)

@router.get("/analytics/download-sdp")
def download_sdp(
    filename: str = Query(..., description="Nama file .sdp yang berada di staging (converted) dan akan disalin ke Downloads saat diunduh"),
):
    try:
        if not filename.lower().endswith(".sdp"):
            return JSONResponse(
                {"status": 400, "message": "filename harus berakhiran .sdp"},
                status_code=400
            )
        base_dir = os.getcwd()
        converted_dir = os.path.join(base_dir, "data", "uploads", "converted")
        src_path = os.path.join(converted_dir, filename)
        if not os.path.exists(src_path):
            return JSONResponse(
                {"status": 404, "message": f"File belum tersedia untuk diunduh: {filename}"},
                status_code=404
            )

        downloads_dir = os.path.expanduser("~/Downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        dst_path = os.path.join(downloads_dir, filename)
        try:
            import shutil
            shutil.copyfile(src_path, dst_path)
        except Exception:
            pass

        return JSONResponse(
            {
                "status": 200,
                "message": "Successfully download file",
                "data": [{"file": filename}]
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse({"status": 500, "message": f"Download error: {str(e)}"}, status_code=500)


