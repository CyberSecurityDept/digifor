from pathlib import Path
import pandas as pd  # type: ignore
import re
import csv
import xml.etree.ElementTree as ET
import warnings
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from datetime import datetime
from .file_validator import file_validator

# Suppress openpyxl warnings globally
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', message='.*OLE2 inconsistency.*')
warnings.filterwarnings('ignore', message='.*file size.*not.*multiple of sector size.*')
warnings.filterwarnings('ignore', message='.*SSCS size is 0 but SSAT size is non-zero.*')
warnings.filterwarnings('ignore', message='.*WARNING \*\*\*.*')

class HashFileFormat(Enum):
    ENCASE_TXT = "Encase_TXT"
    ENCASE_XML = "Encase_XML"
    MAGNET_AXIOM_CSV = "Magnet_Axiom_CSV"
    CELEBRATE_XLSX = "Celebrate_XLSX"
    OXYGEN_XLS = "Oxygen_XLS"
    OXYGEN_PDF = "Oxygen_PDF"
    AUTOMATIC = "Automatic"

class HashFileParser:
    
    def __init__(self):
        self.format_parsers = {
            HashFileFormat.ENCASE_TXT: self._parse_encase_txt,
            HashFileFormat.ENCASE_XML: self._parse_encase_xml,
            HashFileFormat.MAGNET_AXIOM_CSV: self._parse_magnet_axiom_csv,
            HashFileFormat.CELEBRATE_XLSX: self._parse_celebrate_xlsx,
            HashFileFormat.OXYGEN_XLS: self._parse_oxygen_xls,
            HashFileFormat.OXYGEN_PDF: self._parse_oxygen_pdf,
            HashFileFormat.AUTOMATIC: self._parse_automatic
        }
    
    def parse_hashfile(self, file_path: Path, format_type: str = None) -> Dict[str, Any]:
        # Validasi file terlebih dahulu - hanya untuk Excel files
        file_extension = file_path.suffix.lower()
        if file_extension in ['.xlsx', '.xls']:
            validation = file_validator.validate_excel_file(file_path)
            file_validator.print_validation_summary(validation)
            
            if not validation["is_valid"]:
                return {"error": f"File validation failed: {validation['errors']}", "hashfiles": []}
        
        if format_type:
            format_enum = self._detect_format_from_name(format_type)
        else:
            format_enum = self._auto_detect_format(file_path)
        
        parser_func = self.format_parsers.get(format_enum, self._parse_automatic)
        
        try:
            result = parser_func(file_path)
            result["format_detected"] = format_enum.value
            result["file_path"] = str(file_path)
            
            # Add original file path to each hashfile for reference
            original_file_path = self._get_full_original_path(file_path)
            original_file_name = file_path.name
            original_file_size = file_path.stat().st_size if file_path.exists() else 0
            original_file_kind = self._get_file_kind(file_path)
            original_created_at = self._get_file_created_time(file_path)
            original_modified_at = self._get_file_modified_time(file_path)
            
            for hashfile in result.get("hashfiles", []):
                if not hashfile.get("file_path") or hashfile.get("file_path") == "":
                    hashfile["file_path"] = original_file_path
                # Also add original file info for context
                hashfile["original_file_path"] = original_file_path
                hashfile["original_file_name"] = original_file_name
                hashfile["original_file_size"] = original_file_size
                hashfile["original_file_kind"] = original_file_kind
                hashfile["original_created_at"] = original_created_at
                hashfile["original_modified_at"] = original_modified_at
                
            return result
        except Exception as e:
            return {
                "error": f"Failed to parse hashfile: {str(e)}",
                "format_detected": format_enum.value,
                "file_path": str(file_path),
                "hashfiles": []
            }
    
    def _auto_detect_format(self, file_path: Path) -> HashFileFormat:
        """Auto detect format berdasarkan file extension dan content"""
        file_name = file_path.name.lower()
        
        if file_name.endswith('.txt') and 'encase' in file_name:
            return HashFileFormat.ENCASE_TXT
        elif file_name.endswith('.xml') and 'encase' in file_name:
            return HashFileFormat.ENCASE_XML
        elif file_name.endswith('.csv') and 'magnet' in file_name:
            return HashFileFormat.MAGNET_AXIOM_CSV
        elif file_name.endswith('.xlsx') and 'cellebrite' in file_name:
            return HashFileFormat.CELEBRATE_XLSX
        elif file_name.endswith('.xls') and 'oxygen' in file_name:
            return HashFileFormat.OXYGEN_XLS
        elif file_name.endswith('.pdf') and 'oxygen' in file_name:
            return HashFileFormat.OXYGEN_PDF
        else:
            return HashFileFormat.AUTOMATIC
    
    def _detect_format_from_name(self, format_name: str) -> HashFileFormat:
        """Detect format dari nama yang diberikan"""
        format_lower = format_name.lower()
        
        if 'encase' in format_lower:
            if 'xml' in format_lower:
                return HashFileFormat.ENCASE_XML
            else:
                return HashFileFormat.ENCASE_TXT
        elif 'magnet' in format_lower or 'axiom' in format_lower:
            return HashFileFormat.MAGNET_AXIOM_CSV
        elif 'cellebrite' in format_lower or 'celebrate' in format_lower:
            return HashFileFormat.CELEBRATE_XLSX
        elif 'oxygen' in format_lower:
            if 'pdf' in format_lower:
                return HashFileFormat.OXYGEN_PDF
            else:
                return HashFileFormat.OXYGEN_XLS
        else:
            return HashFileFormat.AUTOMATIC
    
    def _parse_encase_txt(self, file_path: Path) -> Dict[str, Any]:
        """Parse Encase hashfile format (.txt)"""
        hashfiles = []
        
        try:
            # Try UTF-16 first (common for Encase)
            with open(file_path, 'r', encoding='utf-16') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Fallback to UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Skip header line
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) >= 3:
                # Extract file name from path if available
                file_name = parts[1] if len(parts) > 1 else f"file_{i}"
                if '/' in file_name or '\\' in file_name:
                    file_name = file_name.split('/')[-1].split('\\')[-1]
                
                # Get file path from the data
                file_path_from_data = parts[1] if len(parts) > 1 else f"/unknown/{file_name}"
                
                # Get MD5 and SHA1 hashes
                md5_hash = parts[2] if len(parts) > 2 else ""
                sha1_hash = parts[3] if len(parts) > 3 else ""
                
                # Skip if no hash values
                if not md5_hash and not sha1_hash:
                    continue
                
                # Determine algorithm based on available hashes
                algorithm = "MD5"  # Default
                if sha1_hash and not md5_hash:
                    algorithm = "SHA-1"
                elif md5_hash and not sha1_hash:
                    algorithm = "MD5"
                elif md5_hash and sha1_hash:
                    algorithm = "MD5"  # Prefer MD5 if both available
                
                hashfiles.append({
                    "index": i,
                    "name": file_name,
                    "md5": md5_hash,
                    "sha1": sha1_hash,
                    "file_path": file_path_from_data,
                    "size": parts[4] if len(parts) > 4 else "0",
                    "created_date": parts[5] if len(parts) > 5 else "",
                    "modified_date": parts[6] if len(parts) > 6 else "",
                    "source": "Encase",
                    "algorithm": algorithm
                })
        
        return {
            "tool": "Encase",
            "format": "TXT",
            "hashfiles": hashfiles,
            "total_files": len(hashfiles)
        }
    
    def _parse_encase_xml(self, file_path: Path) -> Dict[str, Any]:
        """Parse Encase hashfile format (.xml)"""
        hashfiles = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Parse XML structure (adjust based on actual XML structure)
            for i, row in enumerate(root.findall('.//row'), 1):
                cells = row.findall('.//c')
                if len(cells) >= 2:
                    hashfiles.append({
                        "index": i,
                        "name": cells[1].text if len(cells) > 1 else "",
                        "md5": "",
                        "sha1": "",
                        "file_path": "",
                        "size": "",
                        "created_date": "",
                        "modified_date": "",
                        "source": "Encase",
                        "algorithm": "MD5"  # Default for XML format
                    })
        except ET.ParseError:
            # Fallback to text parsing
            return self._parse_encase_txt(file_path)
        
        return {
            "tool": "Encase",
            "format": "XML",
            "hashfiles": hashfiles,
            "total_files": len(hashfiles)
        }
    
    def _parse_magnet_axiom_csv(self, file_path: Path) -> Dict[str, Any]:
        """Parse Magnet Axiom hashfile format (.csv)"""
        hashfiles = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader, 1):
                    # Get file information
                    name = row.get('Name', '')
                    md5_hash = row.get('MD5 hash', '')
                    sha1_hash = row.get('SHA1 hash', '')
                    file_path = row.get('Full path', '')
                    
                    # Skip if no hash values
                    if not md5_hash and not sha1_hash:
                        continue
                    
                    # Extract file name from path if available
                    if not name and file_path:
                        if '/' in file_path or '\\' in file_path:
                            name = file_path.split('/')[-1].split('\\')[-1]
                        else:
                            name = file_path
                    
                    # If no file path, use name as path
                    if not file_path and name:
                        file_path = f"/unknown/{name}"
                    
                    # Determine algorithm based on available hashes
                    algorithm = "MD5"  # Default
                    if sha1_hash and not md5_hash:
                        algorithm = "SHA-1"
                    elif md5_hash and not sha1_hash:
                        algorithm = "MD5"
                    elif md5_hash and sha1_hash:
                        algorithm = "MD5"  # Prefer MD5 if both available
                    
                    hashfiles.append({
                        "index": i,
                        "name": name,
                        "md5": md5_hash,
                        "sha1": sha1_hash,
                        "file_path": file_path,
                        "size": row.get('Size (bytes)', ''),
                        "created_date": row.get('Created', ''),
                        "modified_date": row.get('Modified', ''),
                        "source": "Magnet Axiom",
                        "algorithm": algorithm
                    })
        except Exception as e:
            # Fallback parsing
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                headers = lines[0].strip().split(',')
                for i, line in enumerate(lines[1:], 1):
                    values = line.strip().split(',')
                    if len(values) >= len(headers):
                        # Find hash columns by position
                        md5_hash = values[10] if len(values) > 10 else ""
                        sha1_hash = values[11] if len(values) > 11 else ""
                        
                        # Skip if no hash values
                        if not md5_hash and not sha1_hash:
                            continue
                        
                        # Determine algorithm based on available hashes
                        algorithm = "MD5"  # Default
                        if sha1_hash and not md5_hash:
                            algorithm = "SHA-1"
                        elif md5_hash and not sha1_hash:
                            algorithm = "MD5"
                        elif md5_hash and sha1_hash:
                            algorithm = "MD5"  # Prefer MD5 if both available
                        
                        hashfiles.append({
                            "index": i,
                            "name": values[0] if len(values) > 0 else "",
                            "md5": md5_hash,
                            "sha1": sha1_hash,
                            "file_path": values[1] if len(values) > 1 else "",
                            "size": values[2] if len(values) > 2 else "",
                            "created_date": values[3] if len(values) > 3 else "",
                            "modified_date": values[5] if len(values) > 5 else "",
                            "source": "Magnet Axiom",
                            "algorithm": algorithm
                        })
            except Exception as e2:
                pass
        
        return {
            "tool": "Magnet Axiom",
            "format": "CSV",
            "hashfiles": hashfiles,
            "total_files": len(hashfiles)
        }
    
    def _parse_celebrate_xlsx(self, file_path: Path) -> Dict[str, Any]:
        """Parse Cellebrite hashfile format (.xlsx)"""
        hashfiles = []
        
        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                xls = pd.ExcelFile(file_path)
                
                # Try to find hashfile sheet
                sheet_name = None
                for sheet in xls.sheet_names:
                    if 'md5' in sheet.lower() or 'hash' in sheet.lower():
                        sheet_name = sheet
                        break
                
                if not sheet_name:
                    sheet_name = xls.sheet_names[0]
                
                df = pd.read_excel(xls, sheet_name=sheet_name, engine='openpyxl')
                
                # Handle Cellebrite specific structure
                # Columns are usually: ['Unnamed: 0', 'Unnamed: 1'] where first is Name, second is MD5
                for i, row in df.iterrows():
                    # Skip header row
                    if i == 0:
                        continue
                    
                    # Get values from unnamed columns
                    name = str(row.iloc[0]) if len(row) > 0 else ""
                    md5_hash = str(row.iloc[1]) if len(row) > 1 else ""
                    
                    # Skip if no hash value or invalid hash
                    if not md5_hash or md5_hash == 'nan' or len(md5_hash) != 32:
                        continue
                    
                    # Clean name
                    if name == 'nan' or not name:
                        name = f"file_{i}"
                    
                    # Extract file name from path if available
                    if '/' in name or '\\' in name:
                        file_name = name.split('/')[-1].split('\\')[-1]
                    else:
                        file_name = name
                    
                    hashfiles.append({
                        "index": i,
                        "name": file_name,
                        "md5": md5_hash,
                        "sha1": "",  # Cellebrite MD5 files usually don't have SHA1
                        "file_path": name,
                        "size": "",
                        "created_date": "",
                        "modified_date": "",
                        "source": "Cellebrite",
                        "sheet": sheet_name,
                        "algorithm": "MD5"  # Cellebrite uses MD5
                    })
                    
        except Exception as e:
            return {"error": f"Failed to parse Cellebrite XLSX: {str(e)}", "hashfiles": []}
        
        return {
            "tool": "Cellebrite",
            "format": "XLSX",
            "hashfiles": hashfiles,
            "total_files": len(hashfiles)
        }
    
    def _parse_oxygen_xls(self, file_path: Path) -> Dict[str, Any]:
        """Parse Oxygen Forensics hashfile format (.xls)"""
        hashfiles = []
        
        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                xls = pd.ExcelFile(file_path)
                
                # Parse all sheets that contain hash data
                for sheet_name in xls.sheet_names:
                    # Skip table of contents
                    if 'table of contents' in sheet_name.lower():
                        continue
                        
                    try:
                        df = pd.read_excel(xls, sheet_name=sheet_name)
                        
                        # Check if this sheet has hash data (look for Hash(SHA-1) or Hash(MD5) columns)
                        hash_column = None
                        hash_type = None
                        
                        if 'Hash(SHA-1)' in df.columns:
                            hash_column = 'Hash(SHA-1)'
                            hash_type = 'sha1'
                        elif 'Hash(MD5)' in df.columns:
                            hash_column = 'Hash(MD5)'
                            hash_type = 'md5'
                        
                        if hash_column:
                            for i, row in df.iterrows():
                                # Get file information
                                name = str(row.get('Name', ''))
                                hash_value = str(row.get(hash_column, ''))
                                
                                # Skip if no hash or invalid hash
                                if not hash_value or hash_value == 'nan':
                                    continue
                                
                                # Validate hash length based on type
                                if hash_type == 'sha1' and len(hash_value) != 40:
                                    continue
                                elif hash_type == 'md5' and len(hash_value) != 32:
                                    continue
                                
                                # Clean name
                                if not name or name == 'nan':
                                    name = f"file_{i+1}"
                                
                                # Extract file name from path if available
                                if '/' in name or '\\' in name:
                                    file_name = name.split('/')[-1].split('\\')[-1]
                                else:
                                    file_name = name
                                
                                # Create hashfile entry based on hash type
                                hashfile_entry = {
                                    "index": len(hashfiles) + 1,
                                    "name": file_name,
                                    "file_path": name,
                                    "size": str(row.get('Size', '')),
                                    "created_date": str(row.get('Created', '')),
                                    "modified_date": str(row.get('Modified', '')),
                                    "source": "Oxygen Forensics",
                                    "sheet": sheet_name
                                }
                                
                                # Set hash values based on type
                                if hash_type == 'sha1':
                                    hashfile_entry["md5"] = ""
                                    hashfile_entry["sha1"] = hash_value
                                    hashfile_entry["algorithm"] = "SHA-1"
                                else:  # md5
                                    hashfile_entry["md5"] = hash_value
                                    hashfile_entry["sha1"] = ""
                                    hashfile_entry["algorithm"] = "MD5"
                                
                                hashfiles.append(hashfile_entry)
                    except Exception as e:
                        # Skip sheets that can't be parsed
                        continue
                        
        except Exception as e:
            return {"error": f"Failed to parse Oxygen XLS: {str(e)}", "hashfiles": []}
        
        return {
            "tool": "Oxygen Forensics",
            "format": "XLS",
            "hashfiles": hashfiles,
            "total_files": len(hashfiles)
        }
    
    def _parse_oxygen_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Parse Oxygen Forensics hashfile format (.pdf)"""
        # PDF parsing would require additional libraries like PyPDF2 or pdfplumber
        # For now, return empty result with note
        return {
            "tool": "Oxygen Forensics",
            "format": "PDF",
            "hashfiles": [],
            "total_files": 0,
            "note": "PDF parsing not implemented yet. Please use XLS format."
        }
    
    def _parse_automatic(self, file_path: Path) -> Dict[str, Any]:
        """Automatic format detection and parsing"""
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.txt':
            return self._parse_encase_txt(file_path)
        elif file_extension == '.xml':
            return self._parse_encase_xml(file_path)
        elif file_extension == '.csv':
            return self._parse_magnet_axiom_csv(file_path)
        elif file_extension == '.xlsx':
            return self._parse_celebrate_xlsx(file_path)
        elif file_extension == '.xls':
            return self._parse_oxygen_xls(file_path)
        elif file_extension == '.pdf':
            return self._parse_oxygen_pdf(file_path)
        else:
            return {
                "error": f"Unsupported file format: {file_extension}",
                "hashfiles": []
            }
    
    def analyze_hashfiles(self, hashfiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not hashfiles:
            return {"analysis": "No hashfiles to analyze"}
        
        # Group by hash values
        md5_groups = {}
        sha1_groups = {}
        name_groups = {}
        
        for hf in hashfiles:
            # Group by MD5
            if hf.get('md5'):
                if hf['md5'] not in md5_groups:
                    md5_groups[hf['md5']] = []
                md5_groups[hf['md5']].append(hf)
            
            # Group by SHA1
            if hf.get('sha1'):
                if hf['sha1'] not in sha1_groups:
                    sha1_groups[hf['sha1']] = []
                sha1_groups[hf['sha1']].append(hf)
            
            # Group by filename
            if hf.get('name'):
                if hf['name'] not in name_groups:
                    name_groups[hf['name']] = []
                name_groups[hf['name']].append(hf)
        
        md5_duplicates = {k: v for k, v in md5_groups.items() if len(v) > 1}
        sha1_duplicates = {k: v for k, v in sha1_groups.items() if len(v) > 1}
        name_duplicates = {k: v for k, v in name_groups.items() if len(v) > 1}
        
        suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.vbs', '.js']
        suspicious_files = []
        
        for hf in hashfiles:
            name = hf.get('name', '').lower()
            if any(name.endswith(ext) for ext in suspicious_extensions):
                suspicious_files.append(hf)
        
        return {
            "total_files": len(hashfiles),
            "unique_md5": len(md5_groups),
            "unique_sha1": len(sha1_groups),
            "unique_names": len(name_groups),
            "md5_duplicates": len(md5_duplicates),
            "sha1_duplicates": len(sha1_duplicates),
            "name_duplicates": len(name_duplicates),
            "suspicious_files": len(suspicious_files),
            "duplicate_groups": {
                "md5": md5_duplicates,
                "sha1": sha1_duplicates,
                "names": name_duplicates
            },
            "suspicious_file_list": suspicious_files
        }

    def _get_file_kind(self, file_path: Path) -> str:
        if not file_path.exists():
            return "Unknown"
        
        extension = file_path.suffix.lower()
        
        kind_mapping = {
            '.xlsx': 'Microsoft Excel Workbook (.xlsx)',
            '.xls': 'Microsoft Excel 97-2004 Workbook (.xls)',
            '.csv': 'Comma Separated Spreadsheet (.csv)',
            '.txt': 'Plain Text Document',
            '.xml': 'XML Document (.xml)',
            '.pdf': 'PDF Document (.pdf)',
            '.doc': 'Microsoft Word Document (.doc)',
            '.docx': 'Microsoft Word Document (.docx)',
            '.jpg': 'JPEG Image (.jpg)',
            '.jpeg': 'JPEG Image (.jpeg)',
            '.png': 'PNG Image (.png)',
            '.gif': 'GIF Image (.gif)',
            '.mp4': 'MPEG-4 Video (.mp4)',
            '.avi': 'AVI Video (.avi)',
            '.mov': 'QuickTime Movie (.mov)',
            '.mp3': 'MP3 Audio (.mp3)',
            '.wav': 'WAV Audio (.wav)',
            '.zip': 'ZIP Archive (.zip)',
            '.rar': 'RAR Archive (.rar)',
            '.exe': 'Executable (.exe)',
            '.dll': 'Dynamic Library (.dll)',
            '.sys': 'System File (.sys)',
            '.cmd': 'Command Script (.cmd)',
            '.bat': 'Batch File (.bat)',
            '.scr': 'Screen Saver (.scr)',
            '.pif': 'Program Information File (.pif)',
            '.com': 'Command File (.com)',
            '.vbs': 'VBScript (.vbs)',
            '.js': 'JavaScript (.js)'
        }
        
        return kind_mapping.get(extension, f"Unknown File ({extension})")
    
    def _get_file_created_time(self, file_path: Path) -> Optional[datetime]:
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            return datetime.fromtimestamp(stat.st_ctime)
        except Exception:
            return None
    
    def _get_file_modified_time(self, file_path: Path) -> Optional[datetime]:
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            return datetime.fromtimestamp(stat.st_mtime)
        except Exception:
            return None
    
    def _get_full_original_path(self, file_path: Path) -> str:
        import platform
        import os
        
        if not file_path.exists():
            return str(file_path)
        
        try:
            abs_path = file_path.resolve()
            
            system = platform.system().lower()
            
            if system == "darwin":
                try:
                    real_path = abs_path.resolve()
                    if str(real_path).startswith('/Volumes/'):
                        return str(real_path)
                    else:
                        cwd = os.getcwd()
                        if cwd.startswith('/Volumes/'):
                            return str(real_path)
                        else:
                            main_drive = "Macintosh HD"
                            if str(real_path).startswith('/'):
                                relative_path = str(real_path)[1:]
                                return f"/{main_drive}/{relative_path}"
                            else:
                                return str(real_path)
                except Exception:
                    return str(abs_path)
                    
            elif system == "linux":
                return str(abs_path)
                
            elif system == "windows":
                return str(abs_path)
                
            else:
                return str(abs_path)
                
        except Exception as e:
            return str(file_path)

hashfile_parser = HashFileParser()
