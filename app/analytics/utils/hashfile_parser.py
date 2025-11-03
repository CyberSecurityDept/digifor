import pandas as pd
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.analytics.device_management.models import HashFile
import os
from datetime import datetime
from sqlalchemy import text

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')


# ============================================================
# 🔧 Utility Functions
# ============================================================
def detect_encoding(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
            if raw_data[:2] == b'\xff\xfe':
                return 'utf-16-le'
            elif raw_data[:2] == b'\xfe\xff':
                return 'utf-16-be'
            elif raw_data[:3] == b'\xef\xbb\xbf':
                return 'utf-8-sig'
            for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    raw_data.decode(enc)
                    return enc
                except UnicodeDecodeError:
                    continue
            return 'utf-8'
    except Exception:
        return 'utf-8'


def clean_string(value: str) -> str:
    if not value:
        return ''
    cleaned = value.replace('\x00', '').replace('\r', '').strip()
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in ['\n', '\t'])
    return cleaned


def safe_int(value) -> int | None:
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ['', 'nan', 'none', 'null', '-']:
            return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


def safe_str(value) -> str | None:
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value.lower() in ['nan', 'none', 'null', '']:
            return None
    return str(value)


def safe_datetime(value) -> Optional[datetime]:
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, datetime):
        return value
    date_str = str(value).strip()
    if date_str.lower() in ['nan', 'none', 'null', '']:
        return None
    formats_to_try = [
        '%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y',
        '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d',
        '%d-%m-%Y %H:%M:%S', '%d-%m-%Y'
    ]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


# ============================================================
# 🧩 Main Parser Class
# ============================================================
class HashFileParser:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return {
                    "kind": "Unknown",
                    "size_bytes": 0,
                    "path_original": "",
                    "created_at_original": None,
                    "modified_at_original": None
                }

            stat = path_obj.stat()
            extension = path_obj.suffix.lower()
            kind_mapping = {
                '.pdf': 'PDF document', '.doc': 'Microsoft Word document',
                '.docx': 'Microsoft Word document', '.xls': 'Microsoft Excel spreadsheet',
                '.xlsx': 'Microsoft Excel spreadsheet', '.txt': 'Plain text document',
                '.jpg': 'JPEG image', '.jpeg': 'JPEG image', '.png': 'PNG image',
                '.gif': 'GIF image', '.mp4': 'MPEG-4 video', '.avi': 'AVI video',
                '.mov': 'QuickTime movie', '.mp3': 'MP3 audio', '.wav': 'WAV audio',
                '.zip': 'ZIP archive', '.rar': 'RAR archive', '.xml': 'XML document',
                '.csv': 'CSV document', '.json': 'JSON document'
            }

            kind = kind_mapping.get(extension, f"{extension[1:].upper()} file" if extension else "File")
            created_time = datetime.fromtimestamp(stat.st_ctime)
            modified_time = datetime.fromtimestamp(stat.st_mtime)

            return {
                "kind": kind,
                "size_bytes": stat.st_size,
                "path_original": str(path_obj),
                "created_at_original": created_time.strftime("%Y-%m-%d %H:%M:%S"),
                "modified_at_original": modified_time.strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return {
                "kind": "Unknown",
                "size_bytes": 0,
                "path_original": "",
                "created_at_original": None,
                "modified_at_original": None
            }

    # ============================================================
    # ⚡ Optimized Bulk Insert Helper
    # ============================================================
    def _bulk_insert_ultrafast(self, data: List[Dict[str, Any]], file_id: int):
        """🚀 Ultra-fast bulk insert via raw SQL (no ORM overhead)"""
        if not data:
            return 0

        # Filter duplikat berdasarkan md5_hash
        existing_md5s = set(
            h[0] for h in self.db.query(HashFile.md5_hash)
            .filter(HashFile.file_id == file_id, HashFile.md5_hash.isnot(None))
            .all()
        )

        records = [d for d in data if d.get("md5_hash") not in existing_md5s]
        if not records:
            print("⚠️ No new hashfiles to insert (all duplicates).")
            return 0

        inserted = 0
        try:
            conn = self.db.connection()
            insert_query = text("""
                INSERT INTO hash_files (
                    file_id, name, file_name, kind, path_original, size_bytes,
                    created_at_original, modified_at_original, file_type,
                    md5_hash, sha1_hash, source_tool
                )
                VALUES (
                    :file_id, :name, :file_name, :kind, :path_original, :size_bytes,
                    :created_at_original, :modified_at_original, :file_type,
                    :md5_hash, :sha1_hash, :source_tool
                )
            """)

            batch_size = 100000
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                conn.execute(insert_query, batch)
                inserted += len(batch)

            self.db.commit()
            print(f"🚀 Ultra-fast inserted {inserted:,} rows directly via SQL")
            return inserted
        except Exception as e:
            self.db.rollback()
            print(f"❌ Ultra-fast insert failed: {e}")
            raise

    # ============================================================
    # 🧠 Dispatcher
    # ============================================================
    def parse_hashfile(self, file_path: str, file_id: int, tools: str, original_file_path: str = None):
        if tools == "Magnet Axiom":
            return self.parse_axiom_hashfile(file_path, file_id, original_file_path)
        elif tools == "Cellebrite":
            return self.parse_cellebrite_hashfile(file_path, file_id, original_file_path)
        elif tools == "Oxygen":
            return self.parse_oxygen_hashfile(file_path, file_id, original_file_path)
        elif tools == "Encase":
            return self.parse_encase_hashfile(file_path, file_id, original_file_path)
        else:
            print(f"Unknown tool: {tools}. Supported tools: Magnet Axiom, Cellebrite, Oxygen, Encase")
            return []

    # ============================================================
    # 🧩 Axiom Parser
    # ============================================================
    def parse_axiom_hashfile(self, file_path: str, file_id: int, original_file_path: str = None):
        results = []
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path, dtype=str)
                sheets = [df]
            else:
                xls = pd.ExcelFile(file_path, engine='openpyxl')
                sheets = [pd.read_excel(file_path, sheet_name=s, engine='openpyxl', dtype=str)
                          for s in xls.sheet_names if any(k in s.lower() for k in ['hash', 'file', 'artifact'])]

            for df in sheets:
                for _, row in df.iterrows():
                    file_name_val = safe_str(row.get('Name', ''))
                    if not file_name_val:
                        continue
                    results.append({
                        "file_id": file_id,
                        "name": file_name_val,
                        "file_name": file_name_val,
                        "kind": "Unknown",
                        "path_original": safe_str(row.get('Full path', row.get('Path', ''))),
                        "size_bytes": safe_int(row.get('Size (bytes)', row.get('Size', '0'))),
                        "created_at_original": safe_datetime(row.get('Created', '')),
                        "modified_at_original": safe_datetime(row.get('Modified', '')),
                        "file_type": "CSV File",
                        "md5_hash": safe_str(row.get('MD5 hash', row.get('MD5', ''))),
                        "sha1_hash": safe_str(row.get('SHA1 hash', row.get('SHA1', ''))),
                        "source_tool": "magnet_axiom"
                    })

            inserted_count = self._bulk_insert_ultrafast(results, file_id)
            print(f"✅ Successfully saved {inserted_count} Axiom hashfiles to database")
            return inserted_count

        except Exception as e:
            print(f"Error parsing Axiom hashfile: {e}")
            self.db.rollback()
            raise e

    # ============================================================
    # 🧩 Cellebrite Parser
    # ============================================================
    def parse_cellebrite_hashfile(self, file_path: str, file_id: int, original_file_path: str = None):
        results = []
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            hashfile_sheets = [s for s in xls.sheet_names if any(k in s.lower() for k in ['hash', 'file', 'artifact', 'md5', 'sha1'])]
            for sheet_name in hashfile_sheets:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                for _, row in df.iterrows():
                    file_name = str(row.get('Name', row.get('Unnamed: 0', '')))
                    hash_value = str(row.get('MD5', row.get('SHA1', row.get('Unnamed: 1', ''))))
                    hash_type = 'md5' if 'md5' in sheet_name.lower() else 'sha1'
                    if not file_name or file_name.lower() == 'nan':
                        continue
                    results.append({
                        "file_id": file_id,
                        "name": file_name,
                        "file_name": file_name,
                        "kind": "Unknown",
                        "path_original": "",
                        "size_bytes": 0,
                        "created_at_original": None,
                        "modified_at_original": None,
                        "file_type": sheet_name.strip(),
                        "md5_hash": hash_value if hash_type == 'md5' else '',
                        "sha1_hash": hash_value if hash_type == 'sha1' else '',
                        "source_tool": "cellebrite"
                    })

            inserted_count = self._bulk_insert_ultrafast(results, file_id)
            print(f"✅ Successfully saved {inserted_count} Cellebrite hashfiles to database")
            return inserted_count

        except Exception as e:
            print(f"Error parsing Cellebrite hashfile: {e}")
            self.db.rollback()
            raise e

    # ============================================================
    # 🧩 Oxygen Parser
    # ============================================================
    def parse_oxygen_hashfile(self, file_path: str, file_id: int, original_file_path: str = None):
        results = []
        try:
            file_path_obj = Path(file_path)
            engine = "xlrd" if file_path_obj.suffix.lower() == '.xls' else "openpyxl"
            xls = pd.ExcelFile(file_path, engine=engine)
            hashfile_sheets = [s for s in xls.sheet_names if s.lower() not in ['table of contents']]
            for sheet_name in hashfile_sheets:
                df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine)
                info_path = original_file_path if original_file_path else file_path
                file_info = self._get_file_info(info_path)
                for _, row in df.iterrows():
                    name_val = str(row.get('Name', ''))
                    if not name_val or name_val.lower() == 'nan':
                        continue
                    results.append({
                        "file_id": file_id,
                        "name": name_val,
                        "file_name": name_val,
                        "kind": file_info["kind"],
                        "path_original": file_info["path_original"],
                        "size_bytes": file_info["size_bytes"],
                        "created_at_original": file_info["created_at_original"],
                        "modified_at_original": file_info["modified_at_original"],
                        "file_type": sheet_name.strip(),
                        "md5_hash": str(row.get('Hash(MD5)', row.get('MD5', ''))),
                        "sha1_hash": str(row.get('Hash(SHA1)', row.get('Hash(SHA-1)', row.get('SHA1', '')))),
                        "source_tool": "oxygen"
                    })

            inserted_count = self._bulk_insert_ultrafast(results, file_id)
            print(f"✅ Successfully saved {inserted_count} Oxygen hashfiles to database")
            return inserted_count

        except Exception as e:
            print(f"Error parsing Oxygen hashfile: {e}")
            self.db.rollback()
            raise e

    # ============================================================
    # 🧩 EnCase Parser
    # ============================================================
    def parse_encase_hashfile(self, file_path: str, file_id: int, original_file_path: str = None):
        results = []
        try:
            file_extension = Path(file_path).suffix.lower()
            if file_extension == '.txt':
                encoding = detect_encoding(file_path)
                try:
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                for raw_line in lines:
                    line = clean_string(raw_line.replace('\ufeff', ''))
                    if not line:
                        continue
                    parts = [clean_string(p.strip().strip('"')) for p in line.split('\t') if p is not None]
                    if len(parts) < 3:
                        continue
                    lower_parts = [p.lower() for p in parts]
                    if 'name' in lower_parts and 'md5' in lower_parts and 'sha1' in lower_parts:
                        continue
                    if parts[0].isdigit() and len(parts) >= 4:
                        name_val, md5_val, sha1_val = parts[1], parts[2], parts[3]
                    else:
                        name_val = parts[0]
                        md5_val = parts[1] if len(parts) > 1 else ''
                        sha1_val = parts[2] if len(parts) > 2 else ''
                    if not name_val or name_val.lower() == 'nan':
                        continue
                    results.append({
                        "file_id": file_id,
                        "name": name_val,
                        "file_name": name_val,
                        "kind": "Unknown",
                        "path_original": "",
                        "size_bytes": 0,
                        "created_at_original": None,
                        "modified_at_original": None,
                        "file_type": "TXT File",
                        "md5_hash": md5_val,
                        "sha1_hash": sha1_val,
                        "source_tool": "encase"
                    })
            elif file_extension in ['.xls', '.xlsx']:
                engine = "xlrd" if file_extension == '.xls' else "openpyxl"
                xls = pd.ExcelFile(file_path, engine=engine)
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine)
                    for _, row in df.iterrows():
                        name_val = clean_string(str(row.get('Name', '')))
                        if not name_val or name_val.lower() == 'nan':
                            continue
                        results.append({
                            "file_id": file_id,
                            "file_name": name_val,
                            "name": name_val,
                            "path_original": clean_string(str(row.get('Path', ''))),
                            "kind": "Unknown",
                            "size_bytes": safe_int(row.get('Size', '0')),
                            "created_at_original": safe_datetime(row.get('Created', '')),
                            "modified_at_original": safe_datetime(row.get('Modified', '')),
                            "file_type": clean_string(str(row.get('Type', ''))),
                            "md5_hash": clean_string(str(row.get('MD5', ''))),
                            "sha1_hash": clean_string(str(row.get('SHA1', ''))),
                            "source_tool": "encase"
                        })

            inserted_count = self._bulk_insert_ultrafast(results, file_id)
            print(f"✅ Successfully saved {inserted_count} EnCase hashfiles to database")
            return inserted_count

        except Exception as e:
            print(f"❌ Error parsing EnCase hashfile: {e}")
            self.db.rollback()
            raise e
