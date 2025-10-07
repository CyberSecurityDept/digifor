from pathlib import Path
import pandas as pd
import re
import json
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.db.init_db import SessionLocal, engine, Base
from app.analytics.models import Group, Device, Contact, Message, Call

# Buat tabel kalau belum ada
Base.metadata.create_all(bind=engine)

# ---------- Parsing Helpers ----------
def sanitize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(axis=1, how='all')

    def _norm(c):
        if not isinstance(c, str):
            return c
        c = c.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
        c = re.sub(r"\s+", " ", c).strip()
        return c

    df.columns = [_norm(c) for c in df.columns]

    if hasattr(df.columns, "str"):
        df = df.loc[:, ~df.columns.str.match(r"^Unnamed:\s*\d+$")]

    return df


def cell_to_value(text: Optional[str]):
    if text is None:
        return None
    sval = str(text).strip()
    if sval == "" or sval.lower() == "nan":
        return None
    if "\n" in sval or "\r" in sval:
        parts = sval.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        clean = [p.strip() for p in parts if p.strip() and p.strip().lower() != "nan"]
        return clean if clean else None
    return sval


def parse_sheet(xlsx_path: Path, sheet_keyword: str) -> Optional[List[dict]]:
    xls = pd.ExcelFile(xlsx_path)
    target = next((s for s in xls.sheet_names if sheet_keyword.lower() in s.lower()), None)
    if not target:
        return None
    df = pd.read_excel(xlsx_path, sheet_name=target, dtype=str)
    df = sanitize_headers(df)

    records: List[dict] = []
    for i, row in df.iterrows():
        rec = {"index": i + 1}
        for col in df.columns:
            rec[col] = cell_to_value(row.get(col))
        records.append(rec)
    return records


def _to_str(value):
    """Helper: list -> newline-joined string; None -> None; else str(value)."""
    if value is None:
        return None
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)


def normalize_str(val: Optional[str]) -> Optional[str]:
    """Hilangkan whitespace berlebih, normalisasi string supaya konsisten"""
    if not val:
        return None
    s = str(val).strip()
    s = re.sub(r"\s+", " ", s)
    return s


# ---------- Persistence ----------
def save_device(
    device_data: Dict[str, Any],
    contacts: List[dict],
    messages: List[dict],
    calls: List[dict],
) -> int:
    db: Session = SessionLocal()
    try:
        # --- Ambil data sosial media kalau ada ---
        social_media = device_data.get("social_media", {}) or {}

        # --- Buat Device ---
        device = Device(
            owner_name=device_data.get("owner_name"),
            phone_number=device_data.get("phone_number"),
            instagram=social_media.get("instagram"),
            whatsapp=social_media.get("whatsapp"),
            x=social_media.get("x"),
            facebook=social_media.get("facebook"),
            tiktok=social_media.get("tiktok"),
            telegram=social_media.get("telegram"),
        )
        db.add(device)
        db.commit()
        db.refresh(device)

        # --- Contacts dari sheet ---
        for c in contacts:
            db.add(Contact(
                device_id=device.id,
                index_row=c.get("index"),
                type=_to_str(c.get("Type")),
                source=_to_str(c.get("Source")),
                contact=_to_str(c.get("Contact")),
                messages=_to_str(c.get("Messages")),
                phones_emails=_to_str(c.get("Phones & Emails")),
                internet=_to_str(c.get("Internet")),
                other=_to_str(c.get("Other")),
                raw_json=json.dumps(c, ensure_ascii=False),
            ))

        # --- Messages ---
        for m in messages:
            db.add(Message(
                device_id=device.id,
                index_row=m.get("index"),
                direction=_to_str(m.get("Direction")),
                source=_to_str(m.get("Source")),
                type=_to_str(m.get("Type")),
                timestamp=normalize_str(_to_str(m.get("Time stamp (UTC 0)"))),
                text=_to_str(m.get("Text")),
                sender=_to_str(m.get("From")),
                receiver=_to_str(m.get("To")),
                details=_to_str(m.get("Details")),
                thread_id=normalize_str(_to_str(m.get("Thread id"))),
                attachment=_to_str(m.get("Attachment")),
                raw_json=json.dumps(m, ensure_ascii=False),
            ))

        # --- Calls ---
        for c in calls:
            db.add(Call(
                device_id=device.id,
                index_row=c.get("index"),
                direction=_to_str(c.get("Direction")),
                source=_to_str(c.get("Source")),
                type=_to_str(c.get("Type")),
                timestamp=normalize_str(_to_str(c.get("Time stamp (UTC 0)"))),
                duration=_to_str(c.get("Duration")),
                caller=_to_str(c.get("From")),
                receiver=_to_str(c.get("To")),
                details=_to_str(c.get("Details")),
                thread_id=normalize_str(_to_str(c.get("Thread id"))),
                raw_json=json.dumps(c, ensure_ascii=False),
            ))

        db.commit()
        return device.id

    finally:
        db.close()
