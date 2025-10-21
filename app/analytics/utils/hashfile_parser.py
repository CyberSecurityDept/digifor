from pathlib import Path
import pandas as pd
import re
import csv
import xml.etree.ElementTree as ET
import warnings
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

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
        """
        Parse hashfile dari berbagai format tools forensik
        """
        if format_type:
            format_enum = self._detect_format_from_name(format_type)
        else:
            format_enum = self._auto_detect_format(file_path)
        
        parser_func = self.format_parsers.get(format_enum, self._parse_automatic)
        
        try:
            result = parser_func(file_path)
            result["format_detected"] = format_enum.value
            result["file_path"] = str(file_path)
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
                hashfiles.append({
                    "index": i,
                    "name": parts[1] if len(parts) > 1 else "",
                    "md5": parts[2] if len(parts) > 2 else "",
                    "sha1": parts[3] if len(parts) > 3 else "",
                    "file_path": "",
                    "size": "",
                    "created_date": "",
                    "modified_date": "",
                    "source": "Encase"
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
                        "source": "Encase"
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
                    hashfiles.append({
                        "index": i,
                        "name": row.get('Name', ''),
                        "md5": row.get('MD5 hash', ''),
                        "sha1": row.get('SHA1 hash', ''),
                        "file_path": row.get('Full path', ''),
                        "size": row.get('Size (bytes)', ''),
                        "created_date": row.get('Created', ''),
                        "modified_date": row.get('Modified', ''),
                        "source": "Magnet Axiom"
                    })
        except Exception as e:
            # Fallback parsing
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            headers = lines[0].strip().split(',')
            for i, line in enumerate(lines[1:], 1):
                values = line.strip().split(',')
                if len(values) >= len(headers):
                    hashfiles.append({
                        "index": i,
                        "name": values[0] if len(values) > 0 else "",
                        "md5": values[10] if len(values) > 10 else "",
                        "sha1": values[11] if len(values) > 11 else "",
                        "file_path": values[1] if len(values) > 1 else "",
                        "size": values[2] if len(values) > 2 else "",
                        "created_date": values[3] if len(values) > 3 else "",
                        "modified_date": values[5] if len(values) > 5 else "",
                        "source": "Magnet Axiom"
                    })
        
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
            xls = pd.ExcelFile(file_path)
            
            # Try to find hashfile sheet
            sheet_name = None
            for sheet in xls.sheet_names:
                if 'hash' in sheet.lower() or 'file' in sheet.lower():
                    sheet_name = sheet
                    break
            
            if not sheet_name:
                sheet_name = xls.sheet_names[0]
            
            df = pd.read_excel(xls, sheet_name=sheet_name, engine='openpyxl')
            
            for i, row in df.iterrows():
                hashfiles.append({
                    "index": i + 1,
                    "name": str(row.get('Name', '')),
                    "md5": str(row.get('MD5', '')),
                    "sha1": str(row.get('SHA1', '')),
                    "file_path": str(row.get('Path', '')),
                    "size": str(row.get('Size', '')),
                    "created_date": str(row.get('Created', '')),
                    "modified_date": str(row.get('Modified', '')),
                    "source": "Cellebrite"
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
            xls = pd.ExcelFile(file_path)
            df = pd.read_excel(xls, sheet_name=0, engine='openpyxl')  # First sheet
            
            for i, row in df.iterrows():
                hashfiles.append({
                    "index": i + 1,
                    "name": str(row.get('Name', '')),
                    "md5": str(row.get('MD5', '')),
                    "sha1": str(row.get('SHA1', '')),
                    "file_path": str(row.get('Path', '')),
                    "size": str(row.get('Size', '')),
                    "created_date": str(row.get('Created', '')),
                    "modified_date": str(row.get('Modified', '')),
                    "source": "Oxygen Forensics"
                })
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
        """Analyze parsed hashfiles untuk correlation"""
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
        
        # Find duplicates
        md5_duplicates = {k: v for k, v in md5_groups.items() if len(v) > 1}
        sha1_duplicates = {k: v for k, v in sha1_groups.items() if len(v) > 1}
        name_duplicates = {k: v for k, v in name_groups.items() if len(v) > 1}
        
        # Find suspicious files
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

# Global instance
hashfile_parser = HashFileParser()
