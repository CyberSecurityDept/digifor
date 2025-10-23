from pathlib import Path
import pandas as pd
import re
import warnings
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from .contact_parser import contact_parser

# Suppress openpyxl warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class ExtractionTool(Enum):
    CELEBRATE = "Celebrate"
    OXYGEN = "Oxygen"
    MAGNET_AXIOM = "Magnet Axiom"
    AUTOMATIC = "Automatic"

class ToolsParser:
    
    def __init__(self):
        self.tool_parsers = {
            ExtractionTool.CELEBRATE: self._parse_celebrate,
            ExtractionTool.OXYGEN: self._parse_oxygen,
            ExtractionTool.MAGNET_AXIOM: self._parse_magnet_axiom,
            ExtractionTool.AUTOMATIC: self._parse_automatic
        }
    
    def parse_file(self, file_path: Path, tools: str) -> Dict[str, Any]:
        tools_normalized = self._normalize_tools_name(tools)
        
        parser_func = self.tool_parsers.get(tools_normalized, self._parse_automatic)
        
        try:
            return parser_func(file_path)
        except Exception as e:
            return {
                "error": f"Failed to parse with {tools_normalized.value}: {str(e)}",
                "fallback": self._parse_automatic(file_path)
            }
    
    def _normalize_tools_name(self, tools: str) -> ExtractionTool:
        tools_lower = tools.lower()
        
        if "celebrate" in tools_lower:
            return ExtractionTool.CELEBRATE
        elif "oxygen" in tools_lower:
            return ExtractionTool.OXYGEN
        elif "magnet" in tools_lower and "axiom" in tools_lower:
            return ExtractionTool.MAGNET_AXIOM
        else:
            return ExtractionTool.AUTOMATIC
    
    def _parse_celebrate(self, file_path: Path) -> Dict[str, Any]:
        xls = pd.ExcelFile(file_path)
        
        result = {
            "tool": "Celebrate",
            "contacts": [],
            "messages": [],
            "calls": [],
            "metadata": {}
        }
        
        sheet_mappings = {
            "contacts": ["contacts", "contact", "phonebook"],
            "messages": ["messages", "text", "chat"],
            "calls": ["calls", "call_log", "call history"]
        }
        
        for data_type, sheet_keywords in sheet_mappings.items():
            sheet_data = self._find_and_parse_sheet(xls, sheet_keywords)
            if sheet_data:
                result[data_type] = self._normalize_celebrate_data(sheet_data, data_type)
        
        return result
    
    def _parse_oxygen(self, file_path: Path) -> Dict[str, Any]:
        # Use the improved contact parser for Oxygen files
        contacts = contact_parser.parse_contacts_from_file(file_path)
        normalized_contacts = contact_parser.normalize_contacts(contacts)
        
        result = {
            "tool": "Oxygen",
            "contacts": normalized_contacts,
            "messages": [],
            "calls": [],
            "metadata": {}
        }
        
        # Parse other data types using existing logic
        xls = pd.ExcelFile(file_path)
        sheet_mappings = {
            "messages": ["messages", "text messages", "im"],
            "calls": ["calls", "call log", "call history", "phone calls"]
        }
        
        for data_type, sheet_keywords in sheet_mappings.items():
            sheet_data = self._find_and_parse_sheet(xls, sheet_keywords)
            if sheet_data:
                result[data_type] = self._normalize_oxygen_data(sheet_data, data_type)
        
        return result
    
    def _parse_magnet_axiom(self, file_path: Path) -> Dict[str, Any]:
        # Use the improved contact parser for Magnet Axiom files
        contacts = contact_parser.parse_contacts_from_file(file_path)
        normalized_contacts = contact_parser.normalize_contacts(contacts)
        
        result = {
            "tool": "Magnet Axiom",
            "contacts": normalized_contacts,
            "messages": [],
            "calls": [],
            "metadata": {}
        }
        
        # Parse other data types using existing logic
        xls = pd.ExcelFile(file_path)
        sheet_mappings = {
            "messages": ["messages", "text", "chat", "conversations"],
            "calls": ["calls", "call log", "call history", "phone calls"]
        }
        
        for data_type, sheet_keywords in sheet_mappings.items():
            sheet_data = self._find_and_parse_sheet(xls, sheet_keywords)
            if sheet_data:
                result[data_type] = self._normalize_magnet_axiom_data(sheet_data, data_type)
        
        return result
    
    def _parse_automatic(self, file_path: Path) -> Dict[str, Any]:
        # Use the improved contact parser for automatic detection
        contacts = contact_parser.parse_contacts_from_file(file_path)
        normalized_contacts = contact_parser.normalize_contacts(contacts)
        
        result = {
            "tool": "Automatic Detection",
            "contacts": normalized_contacts,
            "messages": [],
            "calls": [],
            "metadata": {}
        }
        
        # Parse other data types using existing logic
        xls = pd.ExcelFile(file_path)
        sheet_mappings = {
            "messages": ["message", "text", "chat", "conversation"],
            "calls": ["call", "phone", "dial"]
        }
        
        for data_type, sheet_keywords in sheet_mappings.items():
            sheet_data = self._find_and_parse_sheet(xls, sheet_keywords)
            if sheet_data:
                result[data_type] = self._normalize_generic_data(sheet_data, data_type)
        
        return result
    
    def _find_and_parse_sheet(self, xls: pd.ExcelFile, keywords: List[str]) -> Optional[List[dict]]:
        for sheet_name in xls.sheet_names:
            if any(keyword.lower() in sheet_name.lower() for keyword in keywords):
                try:
                    df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str, engine='openpyxl')
                    df = self._sanitize_headers(df)
                    
                    records = []
                    for i, row in df.iterrows():
                        rec = {"index": i + 1}
                        for col in df.columns:
                            rec[col] = self._cell_to_value(row.get(col))
                        records.append(rec)
                    return records
                except Exception as e:
                    continue
        return None
    
    def _sanitize_headers(self, df: pd.DataFrame) -> pd.DataFrame:
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
    
    def _cell_to_value(self, text: Optional[str]):
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
    
    def _normalize_celebrate_data(self, data: List[dict], data_type: str) -> List[dict]:

        return self._normalize_generic_data(data, data_type)
    
    def _normalize_oxygen_data(self, data: List[dict], data_type: str) -> List[dict]:

        return self._normalize_generic_data(data, data_type)
    
    def _normalize_magnet_axiom_data(self, data: List[dict], data_type: str) -> List[dict]:
        normalized = []
        
        for record in data:
            normalized_record = {"index": record.get("index", 0)}
            
            if data_type == "contacts":
                normalized_record.update({
                    "Type": record.get("Source Account Type(s)"),
                    "Source": record.get("Source"),
                    "Contact": record.get("Display Name"),
                    "Messages": None,
                    "Phones & Emails": record.get("Phone Number(s)"),
                    "Internet": None,
                    "Other": f"Starred: {record.get('Starred')}, Deleted: {record.get('Deleted')}, Last Contacted: {record.get('Last Time Contacted Date/Time - UTC+00:00 (dd/MM/yyyy)')}, Times Contacted: {record.get('Number of Times Contacted')}"
                })
                
            elif data_type == "messages":
                message_text = record.get("DeepCommunication")
                if isinstance(message_text, list):
                    message_text = " ".join(message_text)
                
                normalized_record.update({
                    "Direction": record.get("Direction"),
                    "Source": record.get("Source"),
                    "Type": record.get("Type"),
                    "Time stamp (UTC 0)": record.get("Received Date/Time - UTC+00:00 (dd/MM/yyyy)"),
                    "Text": message_text,
                    "From": record.get("Sender"),
                    "To": record.get("Recipient(s)"),
                    "Details": f"Status: {record.get('Status')}, Original Transmit: {record.get('Original Transmit Date/Time - UTC+00:00 (dd/MM/yyyy)')}",
                    "Thread id": record.get("_ThreadID"),
                    "Attachment": None
                })
                
            elif data_type == "calls":
                normalized_record.update({
                    "Direction": record.get("Direction"),
                    "Source": record.get("Source"),
                    "Type": "Call",  # Default type
                    "Time stamp (UTC 0)": record.get("Call Date/Time - UTC+00:00 (dd/MM/yyyy)"),
                    "Duration": None,  # Not available in this data
                    "From": record.get("Local User"),
                    "To": record.get("Partner"),
                    "Details": f"Call Status: {record.get('Call Status')}, Partner Name: {record.get('Partner Name')}, Partner Location: {record.get('Partner Location')}, Country Code: {record.get('Service Provider Country Code')}"
                })
            
            for key, value in record.items():
                if key not in normalized_record:
                    normalized_record[key] = value
            
            normalized.append(normalized_record)
        
        return normalized
    
    def _normalize_generic_data(self, data: List[dict], data_type: str) -> List[dict]:
        normalized = []
        
        for record in data:
            normalized_record = {"index": record.get("index", 0)}
            
            field_mappings = {
                "contacts": {
                    "name": ["name", "contact", "display name", "first name", "last name"],
                    "phone": ["phone", "number", "mobile", "telephone"],
                    "email": ["email", "e-mail", "mail"]
                },
                "messages": {
                    "text": ["text", "message", "content", "body"],
                    "sender": ["sender", "from", "source"],
                    "receiver": ["receiver", "to", "destination"],
                    "timestamp": ["timestamp", "time", "date", "created"],
                    "direction": ["direction", "type", "incoming", "outgoing"]
                },
                "calls": {
                    "caller": ["caller", "from", "source"],
                    "receiver": ["receiver", "to", "destination"],
                    "timestamp": ["timestamp", "time", "date", "created"],
                    "duration": ["duration", "length", "call time"],
                    "direction": ["direction", "type", "incoming", "outgoing"]
                }
            }
            
            mappings = field_mappings.get(data_type, {})
            for target_field, source_fields in mappings.items():
                for source_field in source_fields:
                    if source_field in record:
                        normalized_record[target_field] = record[source_field]
                        break
            
            for key, value in record.items():
                if key not in normalized_record:
                    normalized_record[key] = value
            
            normalized.append(normalized_record)
        
        return normalized

tools_parser = ToolsParser()
