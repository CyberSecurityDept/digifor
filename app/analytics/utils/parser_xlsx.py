from pathlib import Path
import pandas as pd
import re, warnings
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.analytics.shared.models import Device, Contact, Call
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

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

def _to_str(value):
    if value is None:
        return None
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)

def normalize_str(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    s = str(val).strip()
    s = re.sub(r"\s+", " ", s)
    return s