import pandas as pd
import warnings
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.analytics.device_management.models import HashFile
import os
from datetime import datetime

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class HashFileParser:
    
    def __init__(self, db: Session):
        self.db = db
    
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
                '.pdf': 'PDF document',
                '.doc': 'Microsoft Word document',
                '.docx': 'Microsoft Word document',
                '.xls': 'Microsoft Excel spreadsheet',
                '.xlsx': 'Microsoft Excel spreadsheet',
                '.txt': 'Plain text document',
                '.jpg': 'JPEG image',
                '.jpeg': 'JPEG image',
                '.png': 'PNG image',
                '.gif': 'GIF image',
                '.mp4': 'MPEG-4 video',
                '.avi': 'AVI video',
                '.mov': 'QuickTime movie',
                '.mp3': 'MP3 audio',
                '.wav': 'WAV audio',
                '.zip': 'ZIP archive',
                '.rar': 'RAR archive',
                '.xml': 'XML document',
                '.csv': 'CSV document',
                '.json': 'JSON document'
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
    
    def parse_hashfile(self, file_path: str, device_id: int, file_id: int, tools: str, original_file_path: str = None) -> List[Dict[str, Any]]:
        
        if tools == "Magnet Axiom":
            return self.parse_axiom_hashfile(file_path, device_id, file_id, original_file_path)
        elif tools == "Cellebrite":
            return self.parse_cellebrite_hashfile(file_path, device_id, file_id, original_file_path)
        elif tools == "Oxygen":
            return self.parse_oxygen_hashfile(file_path, device_id, file_id, original_file_path)
        elif tools == "Encase":
            return self.parse_encase_hashfile(file_path, device_id, file_id, original_file_path)
        else:
            print(f"Unknown tool: {tools}. Supported tools: Magnet Axiom, Cellebrite, Oxygen, Encase")
            return []
    
    def parse_axiom_hashfile(self, file_path: str, device_id: int, file_id: int, original_file_path: str = None) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path, dtype=str)
                
                for _, row in df.iterrows():
                    hashfile_data = {
                        "device_id": device_id,
                        "file_id": file_id,
                        "name": str(row.get('Name', '')),
                        "file_name": str(row.get('Name', '')),
                        "kind": "Unknown",
                        "path_original": str(row.get('Full path', '')),
                        "size_bytes": str(row.get('Size (bytes)', '0')),
                        "created_at_original": str(row.get('Created', '')),
                        "modified_at_original": str(row.get('Modified', '')),
                        "file_type": "CSV File",
                        "md5_hash": str(row.get('MD5 hash', '')),
                        "sha1_hash": str(row.get('SHA1 hash', '')),
                        "source_tool": "magnet_axiom"
                    }
                    
                    if hashfile_data["file_name"] and hashfile_data["file_name"] != 'nan':
                        results.append(hashfile_data)
            else:
                xls = pd.ExcelFile(file_path, engine='openpyxl')
                
                hashfile_sheets = []
                for sheet_name in xls.sheet_names:
                    if any(keyword in sheet_name.lower() for keyword in ['hash', 'file', 'artifact']):
                        hashfile_sheets.append(sheet_name)
                
                if not hashfile_sheets:
                    print("No hashfile sheets found in Axiom file")
                    return results
                
                for sheet_name in hashfile_sheets:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    
                    for _, row in df.iterrows():
                        hashfile_data = {
                            "device_id": device_id,
                            "file_id": file_id,
                            "name": str(row.get('Name', '')),
                            "file_name": str(row.get('Name', '')),
                            "kind": "Unknown",
                            "path_original": str(row.get('Path', '')),
                            "size_bytes": str(row.get('Size', '0')),
                            "created_at_original": str(row.get('Created', '')),
                            "modified_at_original": str(row.get('Modified', '')),
                            "file_type": sheet_name.strip(),
                            "md5_hash": str(row.get('MD5', '')),
                            "sha1_hash": str(row.get('SHA1', '')),
                            "source_tool": "magnet_axiom"
                        }
                        
                        if hashfile_data["file_name"] and hashfile_data["file_name"] != 'nan':
                            results.append(hashfile_data)
            
            for hashfile in results:
                existing = (
                    self.db.query(HashFile)
                    .filter(
                        HashFile.file_name == hashfile["file_name"],
                        HashFile.device_id == device_id,
                        HashFile.md5_hash == hashfile["md5_hash"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(HashFile(**hashfile))
            
            self.db.commit()
            print(f"Successfully saved {len(results)} Axiom hashfiles to database")
            
        except Exception as e:
            print(f"Error parsing Axiom hashfile: {e}")
            self.db.rollback()
            raise e
        
        return results
    
    def parse_cellebrite_hashfile(self, file_path: str, device_id: int, file_id: int, original_file_path: str = None) -> List[Dict[str, Any]]:
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            hashfile_sheets = []
            for sheet_name in xls.sheet_names:
                if any(keyword in sheet_name.lower() for keyword in ['hash', 'file', 'artifact', 'md5', 'sha1']):
                    hashfile_sheets.append(sheet_name)
            
            if not hashfile_sheets:
                print("No hashfile sheets found in Cellebrite file")
                return results
            
            for sheet_name in hashfile_sheets:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                
                for _, row in df.iterrows():
                    # Handle Cellebrite format with Unnamed columns
                    file_name = str(row.get('Name', row.get('Unnamed: 0', '')))
                    hash_value = str(row.get('MD5', row.get('SHA1', row.get('Unnamed: 1', ''))))
                    
                    # Determine hash type based on sheet name or column content
                    hash_type = 'md5' if 'md5' in sheet_name.lower() else 'sha1'
                    
                    hashfile_data = {
                        "device_id": device_id,
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
                    }
                    
                    if hashfile_data["file_name"] and hashfile_data["file_name"] != 'nan':
                        results.append(hashfile_data)
            
            for hashfile in results:
                existing = (
                    self.db.query(HashFile)
                    .filter(
                        HashFile.file_name == hashfile["file_name"],
                        HashFile.device_id == device_id,
                        HashFile.md5_hash == hashfile["md5_hash"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(HashFile(**hashfile))
            
            self.db.commit()
            print(f"Successfully saved {len(results)} Cellebrite hashfiles to database")
            
        except Exception as e:
            print(f"Error parsing Cellebrite hashfile: {e}")
            self.db.rollback()
            raise e
        
        return results
    
    def parse_oxygen_hashfile(self, file_path: str, device_id: int, file_id: int, original_file_path: str = None) -> List[Dict[str, Any]]:
        results = []
        
        try:
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()
            if file_extension == '.xls':
                engine = "xlrd"
            else:
                engine = "openpyxl"
            
            xls = pd.ExcelFile(file_path, engine=engine)
            
            hashfile_sheets = []
            for sheet_name in xls.sheet_names:
                if sheet_name.lower() not in ['table of contents']:
                    hashfile_sheets.append(sheet_name)
            
            if not hashfile_sheets:
                print("No hashfile sheets found in Oxygen file")
                return results
            
            for sheet_name in hashfile_sheets:
                df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine)
                
                info_path = original_file_path if original_file_path else file_path
                file_info = self._get_file_info(info_path)
                
                for _, row in df.iterrows():
                    hashfile_data = {
                        "device_id": device_id,
                        "file_id": file_id,
                        "name": str(row.get('Name', '')),
                        "file_name": str(row.get('Name', '')),
                        "kind": file_info["kind"],
                        "path_original": file_info["path_original"],
                        "size_bytes": file_info["size_bytes"],
                        "created_at_original": file_info["created_at_original"],
                        "modified_at_original": file_info["modified_at_original"],
                        "file_type": sheet_name.strip(),
                        "md5_hash": str(row.get('Hash(MD5)', row.get('MD5', ''))),
                        "sha1_hash": str(row.get('Hash(SHA1)', row.get('Hash(SHA-1)', row.get('SHA1', ''))))
                    }
                    
                    if hashfile_data["file_name"] and hashfile_data["file_name"] != 'nan':
                        results.append(hashfile_data)
            
            for hashfile in results:
                existing = (
                    self.db.query(HashFile)
                    .filter(
                        HashFile.file_name == hashfile["file_name"],
                        HashFile.device_id == device_id,
                        HashFile.md5_hash == hashfile["md5_hash"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(HashFile(**hashfile))
            
            self.db.commit()
            print(f"Successfully saved {len(results)} Oxygen hashfiles to database")
            
        except Exception as e:
            print(f"Error parsing Oxygen hashfile: {e}")
            self.db.rollback()
            raise e
        
        return results
    
    def parse_encase_hashfile(self, file_path: str, device_id: int, file_id: int, original_file_path: str = None) -> List[Dict[str, Any]]:
        results = []

        try:
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()

            if file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

                for line in lines:
                    if '\t' in line:
                        parts = line.strip().split('\t')
                        if len(parts) >= 3:
                            hashfile_data = {
                                "device_id": device_id,
                                "file_id": file_id,
                                "name": parts[0].strip(),
                                "file_name": parts[0].strip(),
                                "kind": "Unknown",
                                "path_original": "",
                                "size_bytes": 0,
                                "created_at_original": None,
                                "modified_at_original": None,
                                "file_type": "TXT File",
                                "md5_hash": parts[1].strip() if len(parts) > 1 else '',
                                "sha1_hash": parts[2].strip() if len(parts) > 2 else '',
                                "source_tool": "encase"
                            }
                            
                            if hashfile_data["file_name"] and hashfile_data["file_name"] != 'nan':
                                results.append(hashfile_data)
                    else:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            hashfile_data = {
                                "device_id": device_id,
                                "file_id": file_id,
                                "name": parts[-1] if len(parts) > 1 else '',
                                "file_name": parts[-1] if len(parts) > 1 else '',
                                "kind": "Unknown",
                                "path_original": "",
                                "size_bytes": 0,
                                "created_at_original": None,
                                "modified_at_original": None,
                                "file_type": "TXT File",
                                "md5_hash": parts[0] if len(parts) > 0 else '',
                                "sha1_hash": parts[1] if len(parts) > 1 else '',
                                "source_tool": "encase"
                            }

                            if hashfile_data["md5_hash"] and hashfile_data["file_name"]:
                                results.append(hashfile_data)

            elif file_extension in ['.xls', '.xlsx']:
                if file_extension == '.xls':
                    engine = "xlrd"
                else:
                    engine = "openpyxl"

                xls = pd.ExcelFile(file_path, engine=engine)

                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine)

                    for _, row in df.iterrows():
                        hashfile_data = {
                            "device_id": device_id,
                            "file_id": file_id,
                            "file_name": str(row.get('Name', '')).strip(),
                            "file_path": str(row.get('Path', '')).strip(),
                            "file_type": str(row.get('Type', '')).strip(),
                            "file_size": str(row.get('Size', '')).strip(),
                            "md5_hash": str(row.get('MD5', '')).strip(),
                            "sha1_hash": str(row.get('SHA1', '')).strip(),
                            "created_at": str(row.get('Created', '')).strip(),
                            "modified_at": str(row.get('Modified', '')).strip(),
                            "source_tool": "encase"
                        }

                        if hashfile_data["file_name"] and hashfile_data["file_name"].lower() != 'nan':
                            results.append(hashfile_data)

            for hashfile in results:
                existing = (
                    self.db.query(HashFile)
                    .filter(
                        HashFile.file_name == hashfile["file_name"],
                        HashFile.device_id == device_id,
                        HashFile.md5_hash == hashfile["md5_hash"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(HashFile(**hashfile))

            self.db.commit()
            print(f"✅ Successfully saved {len(results)} EnCase hashfiles to database")
                
        except Exception as e:
            print(f"❌ Error parsing EnCase hashfile: {e}")
            self.db.rollback()
            raise e

        return results
