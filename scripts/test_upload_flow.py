import os
import time
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db
from app.analytics.shared.models import File


def run_upload_flow(sample_path: str, file_name: str, notes: str, ftype: str, tools: str, method: str):
    client = TestClient(app)

    with open(sample_path, "rb") as f:
        files = {"file": (file_name, f, "application/octet-stream")}
        data = {
            "file_name": file_name,
            "notes": notes,
            "type": ftype,
            "tools": tools,
            "method": method,
        }
        resp = client.post("/api/v1/analytics/upload-data", files=files, data=data)
    print("Upload response:", resp.status_code, resp.json())

    js = resp.json()
    assert js.get("status") == 200, f"Upload failed: {js}"

    upload_id = None
    # try to read upload_id from response
    data_obj = js.get("data") or {}
    upload_id = data_obj.get("upload_id")

    if upload_id:
        # poll progress once
        pr = client.get(f"/api/v1/analytics/upload-progress", params={"upload_id": upload_id})
        print("Progress:", pr.status_code, pr.json())

    file_id = data_obj.get("file_id")
    assert file_id, "file_id missing in response"

    # verify record in DB
    db = next(get_db())
    rec = db.query(File).filter(File.id == file_id).first()
    assert rec is not None, "File record not found in DB"
    print("DB record:", {
        "id": rec.id,
        "file_name": rec.file_name,
        "method": rec.method,
        "total_size": rec.total_size,
        "amount_of_data": rec.amount_of_data,
    })


if __name__ == "__main__":
    # choose a sample file available in repo
    sample = os.path.join(os.getcwd(), "sample_hashfile", "Magnet Axiom - File Details.csv")
    if not os.path.exists(sample):
        raise SystemExit(f"Sample file not found: {sample}")

    run_upload_flow(
        sample_path=sample,
        file_name="Magnet Axiom - File Details.csv",
        notes="testing upload flow",
        ftype="Handphone",
        tools="Magnet Axiom",
        method="Hashfile Analytics",
    )


