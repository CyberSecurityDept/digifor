import pandas as pd
import warnings
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', message='.*OLE2 inconsistency.*')
warnings.filterwarnings('ignore', message='.*file size.*not.*multiple of sector size.*')
warnings.filterwarnings('ignore', message='.*SSCS size is 0 but SSAT size is non-zero.*')
warnings.filterwarnings('ignore', message=r'.*WARNING \*\*\*.*')

class FileValidator:
    def __init__(self):
        warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
        warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
        warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
        warnings.filterwarnings("ignore", message=".*SSCS size is 0 but SSAT size is non-zero.*")
    
    def validate_excel_file(self, file_path: Path) -> Dict[str, Any]:
        validation_result = {
            "is_valid": False,
            "file_size": 0,
            "sheets": [],
            "has_contacts_sheet": False,
            "contacts_sheet_name": None,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        try:
            if not file_path.exists():
                validation_result["errors"].append(f"File not found: {file_path}")
                return validation_result
            
            file_size = file_path.stat().st_size
            validation_result["file_size"] = file_size
            
            if file_size % 512 != 0:
                validation_result["warnings"].append(
                    f"File size ({file_size:,} bytes) is not a multiple of sector size (512 bytes)"
                )
                validation_result["recommendations"].append(
                    "File may have OLE2 inconsistency. This is common with forensic tools and usually safe to ignore."
                )
            
            if file_size < 1024:
                validation_result["warnings"].append("File size is very small, may be corrupted")
                validation_result["recommendations"].append("Check if file is complete and not corrupted")
            
            if file_size > 100 * 1024 * 1024:
                validation_result["warnings"].append("File size is very large, may cause performance issues")
                validation_result["recommendations"].append("Consider splitting large files into smaller chunks")
            
            file_extension = file_path.suffix.lower()
            
            if file_extension in ['.xlsx', '.xls']:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    pd.options.mode.chained_assignment = None
                    xls = pd.ExcelFile(file_path)
                    validation_result["sheets"] = xls.sheet_names
                    
                    file_name_lower = file_path.name.lower()
                    is_hashfile = (
                        "hashfile" in file_name_lower or 
                        "hash" in file_name_lower or
                        ('cellebrite' in file_name_lower and file_name_lower.endswith('.xlsx')) or
                        ('oxygen' in file_name_lower and 'hashfile' in file_name_lower) or
                        ('encase' in file_name_lower and file_name_lower.endswith('.txt')) or
                        ('magnet' in file_name_lower and file_name_lower.endswith('.csv'))
                    )
                    
                    if not is_hashfile:
                        contacts_sheet = self._find_contacts_sheet(xls.sheet_names)
                        if contacts_sheet:
                            validation_result["has_contacts_sheet"] = True
                            validation_result["contacts_sheet_name"] = contacts_sheet
                        else:
                            validation_result["warnings"].append("No 'Contacts' sheet found")
                            validation_result["recommendations"].append(
                                "Ensure file contains a 'Contacts' sheet or check if file is from the correct forensic tool"
                            )
                    else:
                        hash_sheets = [sheet for sheet in xls.sheet_names if isinstance(sheet, str) and ('hash' in str(sheet).lower() or 'md5' in str(sheet).lower())]
                        oxygen_sheets = [sheet for sheet in xls.sheet_names if isinstance(sheet, str) and any(keyword in str(sheet).lower() for keyword in ['images', 'videos', 'documents', 'plists', 'databases', 'archives', 'json files', 'other files'])]
                        
                        if hash_sheets:
                            validation_result["has_contacts_sheet"] = True
                            validation_result["contacts_sheet_name"] = hash_sheets[0]
                            validation_result["recommendations"].append(f"Hashfile detected with hash sheets: {hash_sheets}")
                        elif oxygen_sheets:
                            validation_result["has_contacts_sheet"] = True
                            validation_result["contacts_sheet_name"] = oxygen_sheets[0]
                            validation_result["recommendations"].append(f"Oxygen hashfile detected with sheets: {oxygen_sheets}")
                        else:
                            validation_result["warnings"].append("No hash-related sheets found")
                            validation_result["recommendations"].append("This may not be a valid hashfile")
                    
                    empty_sheets = []
                    for sheet_name in xls.sheet_names:
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=1)
                            if df.empty:
                                empty_sheets.append(sheet_name)
                        except Exception:
                            empty_sheets.append(sheet_name)
                    
                    if empty_sheets:
                        validation_result["warnings"].append(f"Empty sheets found: {empty_sheets}")
                    
                    validation_result["is_valid"] = True
            else:
                validation_result["sheets"] = []
                validation_result["is_valid"] = True
                
                if file_extension == '.txt':
                    validation_result["recommendations"].append("TXT file detected - this is likely a hashfile from Encase")
                elif file_extension == '.csv':
                    validation_result["recommendations"].append("CSV file detected - this is likely a hashfile from Magnet Axiom")
                elif file_extension == '.xml':
                    validation_result["recommendations"].append("XML file detected - this is likely a hashfile from Encase")
                elif file_extension == '.pdf':
                    validation_result["recommendations"].append("PDF file detected - this is likely a hashfile from Oxygen Forensics")
                
        except Exception as e:
            validation_result["errors"].append(f"Error validating file: {str(e)}")
            validation_result["recommendations"].append(
                "File may be corrupted or not a valid Excel file. Try opening with Excel first."
            )
        
        return validation_result
    
    def _find_contacts_sheet(self, sheet_names: List[str]) -> Optional[str]:
        contact_patterns = [
            "Contacts ",
            "Contacts",
            "Contact",
            "contacts",
            "contact",
            "CONTACTS",
            "CONTACT",
        ]
        
        for pattern in contact_patterns:
            if pattern in sheet_names:
                return pattern
        
        for sheet_name in sheet_names:
            sheet_lower = sheet_name.lower().strip()
            if 'contact' in sheet_lower:
                return sheet_name
        
        return None
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        file_info = {
            "file_name": file_path.name,
            "file_size": 0,
            "file_extension": file_path.suffix.lower(),
            "created_time": None,
            "modified_time": None,
            "is_excel": False,
            "validation_result": None
        }
        
        try:
            if file_path.exists():
                stat = file_path.stat()
                file_info["file_size"] = stat.st_size
                file_info["created_time"] = datetime.fromtimestamp(stat.st_ctime)
                file_info["modified_time"] = datetime.fromtimestamp(stat.st_mtime)
                
                if file_path.suffix.lower() in ['.xlsx', '.xls']:
                    file_info["is_excel"] = True
                    file_info["validation_result"] = self.validate_excel_file(file_path)
        
        except Exception as e:
            file_info["error"] = str(e)
        
        return file_info
    
    def print_validation_summary(self, validation_result: Dict[str, Any]) -> None:
        if validation_result["errors"] or validation_result["warnings"]:
            print("\n" + "="*60)
            print("FILE VALIDATION SUMMARY")
            print("="*60)
            
            if validation_result["is_valid"]:
                print("File is valid and can be processed")
            else:
                print("File validation failed")
            
            print(f"File size: {validation_result['file_size']:,} bytes")
            
            if validation_result["errors"]:
                print("\nERRORS:")
                for error in validation_result["errors"]:
                    print(f"   • {error}")
            
            if validation_result["warnings"]:
                print("\nWARNINGS:")
                for warning in validation_result["warnings"]:
                    print(f"   • {warning}")
            
            print("="*60)


file_validator = FileValidator()
