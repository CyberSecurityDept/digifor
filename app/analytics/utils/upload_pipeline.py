from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import UploadFile
from app.analytics.shared.models import File
from app.analytics.device_management.service import create_device
from app.analytics.utils.sdp_crypto import decrypt_from_sdp
from app.analytics.utils.tools_parser import tools_parser
from app.analytics.utils.performance_optimizer import performance_optimizer
from app.analytics.device_management.service import save_hashfiles_to_database
from app.db.session import get_db
from app.core.config import settings
from datetime import datetime
from app.analytics.utils.social_media_parser import SocialMediaParser
from app.analytics.device_management.models import SocialMedia, Contact, Call, HashFile, ChatMessage, Device
from app.utils.timezone import get_indonesia_time
from app.analytics.utils.contact_parser import ContactParser
from app.analytics.utils.hashfile_parser import HashFileParser
import pandas as pd
import traceback, time, os, asyncio

sm_db = next(get_db())
sm_parser = SocialMediaParser(db=sm_db)

BASE_DIR = os.getcwd()
UPLOAD_DIR = settings.UPLOAD_DIR
APK_DIR_BASE = settings.APK_DIR
DATA_DIR = os.path.join(UPLOAD_DIR, "data")
ENCRYPTED_DIR = os.path.join(UPLOAD_DIR, "encrypted")
KEY_DIR = os.path.join(BASE_DIR, "keys")

for d in [UPLOAD_DIR, DATA_DIR, ENCRYPTED_DIR, KEY_DIR]:
    os.makedirs(d, exist_ok=True)

def _load_existing_private_key() -> bytes:
    private_key_path = os.path.join(KEY_DIR, "private.key")
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(
            f"Private key not found at {private_key_path}. Please place your key in the 'keys' folder."
        )
    with open(private_key_path, "rb") as f:
        return f.read()

def format_bytes(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i, x = 0, float(n)
    while x >= 1024 and i < len(units) - 1:
        x /= 1024.0
        i += 1
    return f"{int(x)} {units[i]}" if i == 0 else f"{x:.2f} {units[i]}"

class UploadService:
    def __init__(self):
        self._progress: Dict[str, Dict[str, Any]] = {}
    
    def _normalize_tool_name(self, tools: str = None) -> Optional[str]:
        if not tools:
            return None
        
        tools_lower = tools.lower()
        if "cellebrite" in tools_lower or "celebrate" in tools_lower:
            return "Cellebrite"
        elif "oxygen" in tools_lower:
            return "Oxygen"
        elif "magnet" in tools_lower and "axiom" in tools_lower:
            return "Magnet Axiom"
        elif "encase" in tools_lower:
            return "Encase"
        return None

    def _init_state(self, upload_id: str):
        self._progress[upload_id] = {
            "percent": 0,
            "progress_size": "0 B",
            "total_size": None,
            "cancel": False,
            "message": "Starting upload...",
            "done": False,
        }

    def _is_canceled(self, upload_id: str) -> bool:
        data = self._progress.get(upload_id)
        if not data or not isinstance(data, dict):
            return True
        return data.get("cancel", False)

    def _detect_tool_from_sheets(self, file_path: str, method: str = None) -> str:
        try:
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in ['.xlsx', '.xls']:
                return "Unknown"
            
            try:
                xls = pd.ExcelFile(file_path, engine='openpyxl')
                sheet_names_lower = [str(s).lower() for s in xls.sheet_names]
                sheet_names_str = ' '.join(sheet_names_lower)
                
                print(f"[TOOL DETECTION] Analyzing sheets: {', '.join(xls.sheet_names[:10])}...")
                if method:
                    print(f"[TOOL DETECTION] Method: {method}")
                
                if method == "Deep Communication Analytics":
                    if 'messages' in sheet_names_lower or 'message' in sheet_names_lower:
                        oxygen_ios_indicators = [
                            'telegram messages - ios', 'telegram chats - ios',
                            'telegram groups - ios', 'telegram users - ios',
                            'telegram accounts', 'instagram direct messages',
                            'instagram media', 'instagram profiles',
                            'ios messages preferences', 'ip addresses - audio-video call'
                        ]
                        for indicator in oxygen_ios_indicators:
                            if indicator in sheet_names_str:
                                print(f"[TOOL DETECTION] Detected Oxygen (Deep Communication) based on: {indicator}")
                                return "Oxygen"
                        
                        for sheet in sheet_names_lower:
                            if 'telegram' in sheet and 'ios' in sheet:
                                print(f"[TOOL DETECTION] Detected Oxygen (Deep Communication) based on: {sheet}")
                                return "Oxygen"
                            if 'instagram' in sheet and ('direct' in sheet or 'media' in sheet or 'profiles' in sheet):
                                print(f"[TOOL DETECTION] Detected Oxygen (Deep Communication) based on: {sheet}")
                                return "Oxygen"
                            if 'ip addresses' in sheet and ('audio' in sheet or 'video' in sheet or 'call' in sheet):
                                print(f"[TOOL DETECTION] Detected Oxygen (Deep Communication) based on: {sheet}")
                                return "Oxygen"
                        
                        print(f"[TOOL DETECTION] Detected Oxygen (Deep Communication) based on Messages sheet")
                        return "Oxygen"
                    
                    if 'chats' in sheet_names_lower:
                        print(f"[TOOL DETECTION] Detected Cellebrite (Deep Communication) based on 'Chats' sheet")
                        return "Cellebrite"
                    
                    axiom_indicators = [
                        'android whatsapp messages', 'android whatsapp chats',
                        'telegram messages - android', 'telegram chats - android',
                        'android instagram', 'android telegram',
                        'telegram messages - ios', 'instagram direct messages'
                    ]
                    for indicator in axiom_indicators:
                        if indicator in sheet_names_str:
                            print(f"[TOOL DETECTION] Detected Magnet Axiom (Deep Communication) based on: {indicator}")
                            return "Magnet Axiom"
                    
                    for sheet in sheet_names_lower:
                        if 'android' in sheet and ('whatsapp' in sheet or 'telegram' in sheet):
                            print(f"[TOOL DETECTION] Detected Magnet Axiom (Deep Communication) based on: {sheet}")
                            return "Magnet Axiom"
                
                elif method == "Contact Correlation":
                    if 'contacts' in sheet_names_lower:
                        if 'social media' in sheet_names_str:
                            print(f"[TOOL DETECTION] Detected Cellebrite (Contact Correlation) based on Contacts + Social Media")
                            return "Cellebrite"
                        
                        oxygen_indicators = ['telegram', 'instagram', 'ios messages', 'ip addresses']
                        if any(ind in sheet_names_str for ind in oxygen_indicators):
                            print(f"[TOOL DETECTION] Detected Oxygen (Contact Correlation) based on Contacts + iOS indicators")
                            return "Oxygen"
                        
                        if any('android' in sheet for sheet in sheet_names_lower):
                            print(f"[TOOL DETECTION] Detected Magnet Axiom (Contact Correlation) based on Contacts + Android")
                            return "Magnet Axiom"
                        
                        print(f"[TOOL DETECTION] Detected Cellebrite (Contact Correlation) based on Contacts sheet")
                        return "Cellebrite"
                
                elif method == "Social Media Correlation":
                    oxygen_ios_indicators = [
                        'telegram messages - ios', 'telegram chats - ios',
                        'telegram groups - ios', 'telegram users - ios',
                        'telegram accounts', 'instagram direct messages',
                        'instagram media', 'instagram profiles',
                        'ios messages preferences'
                    ]
                    for indicator in oxygen_ios_indicators:
                        if indicator in sheet_names_str:
                            print(f"[TOOL DETECTION] Detected Oxygen (Social Media) based on: {indicator}")
                            return "Oxygen"
                    
                    for sheet in sheet_names_lower:
                        if 'telegram' in sheet and 'ios' in sheet:
                            print(f"[TOOL DETECTION] Detected Oxygen (Social Media) based on: {sheet}")
                            return "Oxygen"
                        if 'instagram' in sheet and ('direct' in sheet or 'media' in sheet or 'profiles' in sheet):
                            print(f"[TOOL DETECTION] Detected Oxygen (Social Media) based on: {sheet}")
                            return "Oxygen"
                    
                    if 'social media' in sheet_names_str:
                        print(f"[TOOL DETECTION] Detected Cellebrite (Social Media) based on 'Social Media' sheet")
                        return "Cellebrite"
                    
                    axiom_indicators = [
                        'android whatsapp messages', 'android whatsapp chats',
                        'telegram messages - android', 'telegram chats - android',
                        'android instagram', 'android telegram'
                    ]
                    for indicator in axiom_indicators:
                        if indicator in sheet_names_str:
                            print(f"[TOOL DETECTION] Detected Magnet Axiom (Social Media) based on: {indicator}")
                            return "Magnet Axiom"
                    
                    for sheet in sheet_names_lower:
                        if 'android' in sheet and ('whatsapp' in sheet or 'telegram' in sheet):
                            print(f"[TOOL DETECTION] Detected Magnet Axiom (Social Media) based on: {sheet}")
                            return "Magnet Axiom"
                
                elif method == "Hashfile Analytics":
                    structure_detected = self._detect_hashfile_tool_from_structure(file_path)
                    if structure_detected and structure_detected != "Unknown":
                        return structure_detected
                    
                    hash_indicators = ['hash', 'md5', 'sha1', 'sha256']
                    if any(ind in sheet_names_str for ind in hash_indicators):
                        if any('telegram' in sheet and 'ios' in sheet for sheet in sheet_names_lower):
                            print(f"[TOOL DETECTION] Detected Oxygen (Hashfile) based on hash + iOS indicators")
                            return "Oxygen"
                        if 'social media' in sheet_names_str:
                            print(f"[TOOL DETECTION] Detected Cellebrite (Hashfile) based on hash + Social Media")
                            return "Cellebrite"
                        if any('android' in sheet for sheet in sheet_names_lower):
                            print(f"[TOOL DETECTION] Detected Magnet Axiom (Hashfile) based on hash + Android")
                            return "Magnet Axiom"
                
                else:
                    oxygen_ios_indicators = [
                        'telegram messages - ios', 'telegram chats - ios',
                        'telegram groups - ios', 'telegram users - ios',
                        'telegram accounts', 'instagram direct messages',
                        'instagram media', 'instagram profiles',
                        'ios messages preferences', 'ip addresses - audio-video call'
                    ]
                    for indicator in oxygen_ios_indicators:
                        if indicator in sheet_names_str:
                            print(f"[TOOL DETECTION] Detected Oxygen based on: {indicator}")
                            return "Oxygen"
                    
                    for sheet in sheet_names_lower:
                        if 'telegram' in sheet and 'ios' in sheet:
                            print(f"[TOOL DETECTION] Detected Oxygen based on: {sheet}")
                            return "Oxygen"
                        if 'instagram' in sheet and ('direct' in sheet or 'media' in sheet or 'profiles' in sheet):
                            print(f"[TOOL DETECTION] Detected Oxygen based on: {sheet}")
                            return "Oxygen"
                        if 'ip addresses' in sheet and ('audio' in sheet or 'video' in sheet or 'call' in sheet):
                            print(f"[TOOL DETECTION] Detected Oxygen based on: {sheet}")
                            return "Oxygen"
                    
                    if 'chats' in sheet_names_lower:
                        print(f"[TOOL DETECTION] Detected Cellebrite based on 'Chats' sheet")
                        return "Cellebrite"
                    if 'social media' in sheet_names_str:
                        print(f"[TOOL DETECTION] Detected Cellebrite based on 'Social Media' sheet")
                        return "Cellebrite"
                    
                    axiom_indicators = [
                        'android whatsapp messages', 'android whatsapp chats',
                        'telegram messages - android', 'telegram chats - android',
                        'android instagram', 'android telegram'
                    ]
                    for indicator in axiom_indicators:
                        if indicator in sheet_names_str:
                            print(f"[TOOL DETECTION] Detected Magnet Axiom based on: {indicator}")
                            return "Magnet Axiom"
                    
                    for sheet in sheet_names_lower:
                        if 'android' in sheet and ('whatsapp' in sheet or 'telegram' in sheet):
                            print(f"[TOOL DETECTION] Detected Magnet Axiom based on: {sheet}")
                            return "Magnet Axiom"
                
            except Exception as e:
                print(f"[TOOL DETECTION] Error reading Excel file: {e}")
                return "Unknown"
        except Exception as e:
            print(f"[TOOL DETECTION] Error detecting tool: {e}")
            return "Unknown"
        
        return "Unknown"

    def _detect_hashfile_tool_from_structure(self, file_path: str) -> str:
        try:
            file_ext = Path(file_path).suffix.lower()
            
    
            if file_ext == '.txt':
                try:
                    encoding = 'utf-8'
                    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                        first_lines = [f.readline() for _ in range(5)]
                
                    for line in first_lines:
                        if line and '\t' in line:
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                lower_parts = [p.lower().strip() for p in parts[:3]]
                                if any('name' in p for p in lower_parts) and \
                                   any('md5' in p for p in lower_parts) and \
                                   any('sha1' in p for p in lower_parts):
                                    print(f"[TOOL DETECTION] Detected EnCase (Hashfile) based on .txt tab-separated structure")
                                    return "Encase"

                                if len(parts) >= 3:
                                    potential_md5 = parts[1].strip() if len(parts) > 1 else ""
                                    potential_sha1 = parts[2].strip() if len(parts) > 2 else ""
                                    if (len(potential_md5) == 32 and all(c in '0123456789abcdefABCDEF' for c in potential_md5)) or \
                                       (len(potential_sha1) == 40 and all(c in '0123456789abcdefABCDEF' for c in potential_sha1)):
                                        print(f"[TOOL DETECTION] Detected EnCase (Hashfile) based on .txt hash structure")
                                        return "Encase"
                except:
                    pass
            
            if file_ext in ['.xlsx', '.xls']:
                try:
                    engine = "xlrd" if file_ext == '.xls' else "openpyxl"
                    xls = pd.ExcelFile(file_path, engine=engine)
                    sheet_names = xls.sheet_names
                    sheet_names_lower = [str(s).lower() for s in sheet_names]
                    sheet_names_str = ' '.join(sheet_names_lower)
                    
                    md5_sheet = None
                    sha1_sheet = None
                    for sheet in sheet_names:
                        sheet_upper = str(sheet).upper().strip()
                        if sheet_upper == 'MD5':
                            md5_sheet = sheet
                        elif sheet_upper in ['SHA1', 'SHA-1']:
                            sha1_sheet = sheet
                    
                    if md5_sheet or sha1_sheet:
                        test_sheet = md5_sheet if md5_sheet else sha1_sheet
                        print(f"[TOOL DETECTION] Found MD5/SHA1 sheet: {test_sheet}, checking for Cellebrite structure...")
                        for header_row in [0, 1, 2]:
                            try:
                                df_test = pd.read_excel(file_path, sheet_name=test_sheet, engine=engine, dtype=str, header=header_row, nrows=5)
                                columns_lower = [str(col).lower().strip() for col in df_test.columns]
                                print(f"[TOOL DETECTION] Sheet '{test_sheet}' header row {header_row} columns: {columns_lower[:10]}...")
                                
                                has_name = 'name' in columns_lower or any('name' in col for col in columns_lower)
                                has_md5 = 'md5' in columns_lower or any('md5' in col for col in columns_lower)
                                has_sha1 = 'sha1' in columns_lower or 'sha-1' in columns_lower or any('sha1' in col or 'sha-1' in col for col in columns_lower)
                                
                                has_hash_md5 = any('hash(md5)' in col for col in columns_lower)
                                has_hash_sha1 = any('hash(sha1)' in col or 'hash(sha-1)' in col for col in columns_lower)
                                
                                print(f"[TOOL DETECTION] has_name={has_name}, has_md5={has_md5}, has_sha1={has_sha1}, has_hash_md5={has_hash_md5}, has_hash_sha1={has_hash_sha1}")
                                
                                if has_name and (has_md5 or has_sha1) and not (has_hash_md5 or has_hash_sha1):
                                    print(f"[TOOL DETECTION] Detected Cellebrite (Hashfile) based on MD5/SHA1 sheet structure (header row {header_row})")
                                    return "Cellebrite"
                            except Exception as e:
                                print(f"[TOOL DETECTION] Error reading sheet '{test_sheet}' header row {header_row}: {e}")
                                continue
                    
                    if not md5_sheet and not sha1_sheet:
                        hashfile_sheets = [s for s in sheet_names if isinstance(s, str) and str(s).lower() not in ['table of contents']]
                        for sheet_name in hashfile_sheets[:3]:
                            try:
                                df_test = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine, nrows=3)
                                columns_lower = [str(col).lower().strip() for col in df_test.columns]
                                
                                has_name = any('name' in col for col in columns_lower)
                                has_md5 = any('hash(md5)' in col for col in columns_lower)
                                has_sha1 = any('hash(sha1)' in col or 'hash(sha-1)' in col for col in columns_lower)
                                
                                if has_name and (has_md5 or has_sha1):
                                    print(f"[TOOL DETECTION] Detected Oxygen (Hashfile) based on Name/Hash(MD5)/Hash(SHA1) structure")
                                    return "Oxygen"
                            except:
                                continue
                    
                    for sheet_name in sheet_names[:3]:
                        try:
                            df_test = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine, nrows=3)
                            columns_lower = [str(col).lower().strip() for col in df_test.columns]
                            
                            if 'name' in columns_lower and 'md5' in columns_lower and 'sha1' in columns_lower:
                                print(f"[TOOL DETECTION] Detected EnCase (Hashfile) based on Name/MD5/SHA1 Excel structure")
                                return "Encase"
                        except:
                            continue
                    
                except Exception as e:
                    print(f"[TOOL DETECTION] Error detecting hashfile tool from structure: {e}")
                    return "Unknown"
            
            if file_ext == '.csv':
                try:
                    df_test = pd.read_csv(file_path, dtype=str, nrows=3)
                    columns_lower = [str(col).lower().strip() for col in df_test.columns]
                    if 'name' in columns_lower and ('md5' in columns_lower or 'sha1' in columns_lower):
                        print(f"[TOOL DETECTION] Detected Magnet Axiom (Hashfile) based on CSV structure")
                        return "Magnet Axiom"
                except:
                    pass
            
        except Exception as e:
            print(f"[TOOL DETECTION] Error in _detect_hashfile_tool_from_structure: {e}")
            return "Unknown"
        
        return "Unknown"

    def _detect_social_media_correlation_tool_from_structure(self, file_path: str) -> str:
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext not in ['.xlsx', '.xls']:
                return "Unknown"
            
            try:
                engine = "xlrd" if file_ext == '.xls' else "openpyxl"
                xls = pd.ExcelFile(file_path, engine=engine)
                sheet_names = [str(s) for s in xls.sheet_names]
                
                print(f"[TOOL DETECTION] Analyzing Social Media Correlation columns from {len(sheet_names)} sheets (column-based detection only)...")

                axiom_key_columns = [
                    'user name', 'user id',
                    'account id', 'first name', 'last name',
                    'whatsapp name',
                    'profile id', 'display name',
                    'record'
                ]
                
                axiom_column_combinations = [
                    ['user name', 'user id'],
                    ['user name', 'id', 'full name'],
                    ['account id', 'user id', 'first name', 'last name'],
                    ['whatsapp name', 'phone number'],
                    ['profile id', 'display name', 'first name', 'last name'],
                    ['record', 'user name'],
                    ['record', 'whatsapp name'],
                    ['record', 'account id']
                ]
                
                cellebrite_key_columns = [
                    'source', 'author', 'body', 'url', 'account',
                    'type', 'contact', 'internet', 'addresses',
                    'username', 'service type', 'account name', 'entries'
                ]
                
                cellebrite_column_combinations = [
                    ['source', 'author', 'body', 'url', 'account'],
                    ['type', 'contact', 'internet', 'addresses', 'source', 'name', 'entries'],
                    ['username', 'service type', 'account name', 'entries', 'source']
                ]
                
                oxygen_key_columns = [
                    'uid', 'username', 'full name', 'followers', 'following',
                    'user name', 'user id', 'user picture',
                    'source', 'service', 'platform', 'application', 'app'
                ]
                
                oxygen_column_combinations = [
                    ['uid', 'username', 'full name', 'followers', 'following'],
                    ['user name', 'user id', 'full name', 'phone number', 'user picture'],
                    ['source', 'service', 'platform']
                ]
                
                tool_scores = {
                    'Magnet Axiom': 0,
                    'Cellebrite': 0,
                    'Oxygen': 0
                }
                
                for sheet_name in sheet_names:
                    try:
                        for header_row in [0, 1, 2]:
                            try:
                                df_test = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str, header=header_row, nrows=3)
                                columns_lower = [str(col).lower().strip() for col in df_test.columns]
                                columns_set = set(columns_lower)
                                
                                axiom_key_matches = sum(1 for col in axiom_key_columns if col in columns_set)
                                for combo in axiom_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        tool_scores['Magnet Axiom'] += len(combo)
                                        print(f"[TOOL DETECTION] Found Magnet Axiom column combination in sheet '{sheet_name}': {combo}")
                                if axiom_key_matches > 0:
                                    tool_scores['Magnet Axiom'] += axiom_key_matches
                                
                                cellebrite_key_matches = sum(1 for col in cellebrite_key_columns if col in columns_set)
                                for combo in cellebrite_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        tool_scores['Cellebrite'] += len(combo)
                                        print(f"[TOOL DETECTION] Found Cellebrite column combination in sheet '{sheet_name}': {combo}")
                                if cellebrite_key_matches > 0:
                                    tool_scores['Cellebrite'] += cellebrite_key_matches
                                
                                oxygen_key_matches = sum(1 for col in oxygen_key_columns if col in columns_set)
                                for combo in oxygen_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        tool_scores['Oxygen'] += len(combo)
                                        print(f"[TOOL DETECTION] Found Oxygen column combination in sheet '{sheet_name}': {combo}")
                                if oxygen_key_matches > 0:
                                    tool_scores['Oxygen'] += oxygen_key_matches
                                
                                if tool_scores['Magnet Axiom'] >= 5 or tool_scores['Cellebrite'] >= 5 or tool_scores['Oxygen'] >= 5:
                                    break
                                    
                            except Exception as e:
                                continue
                                
                    except Exception as e:
                        print(f"[TOOL DETECTION] Error reading sheet '{sheet_name}': {e}")
                        continue

                max_score = max(tool_scores.values())
                if max_score > 0:
                    detected_tool = max(tool_scores, key=tool_scores.get)
                    print(f"[TOOL DETECTION] Tool scores: {tool_scores}")
                    print(f"[TOOL DETECTION] Detected {detected_tool} (Social Media Correlation) based on column structure (score: {max_score})")
                    return detected_tool
                
            except Exception as e:
                print(f"[TOOL DETECTION] Error detecting Social Media Correlation tool from structure: {e}")
                traceback.print_exc()
                return "Unknown"
            
        except Exception as e:
            print(f"[TOOL DETECTION] Error in _detect_social_media_correlation_tool_from_structure: {e}")
            traceback.print_exc()
            return "Unknown"
        
        print(f"[TOOL DETECTION] Could not detect Social Media Correlation tool from column structure")
        return "Unknown"

    def _detect_contact_correlation_tool_from_structure(self, file_path: str) -> str:
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext not in ['.xlsx', '.xls']:
                return "Unknown"
            
            try:
                engine = "xlrd" if file_ext == '.xls' else "openpyxl"
                xls = pd.ExcelFile(file_path, engine=engine)
                sheet_names = [str(s) for s in xls.sheet_names]
                
                print(f"[TOOL DETECTION] Analyzing Contact Correlation columns from {len(sheet_names)} sheets (column-based detection only)...")
                
                axiom_contacts_columns = [
                    'display name', 'phone number(s)', 'source account type(s)'
                ]
                
                axiom_calls_columns = [
                    'direction', 'source', 'type', 'received date/time', 'duration', 'caller', 'recipient(s)', 'status'
                ]
                
                axiom_column_combinations = [
                    ['display name', 'phone number(s)', 'source account type(s)'],
                    ['direction', 'source', 'type', 'received date/time', 'duration', 'caller', 'recipient(s)'],
                    ['display name', 'phone number(s)'],
                    ['direction', 'caller', 'recipient(s)']
                ]
                
                cellebrite_contacts_columns = [
                    'type', 'contact', 'internet', 'addresses', 'source', 'name', 'entries', 'interaction statuses'
                ]
                
                cellebrite_column_combinations = [
                    ['type', 'contact', 'internet', 'addresses', 'source', 'name', 'entries'],
                    ['type', 'contact', 'internet', 'addresses'],
                    ['name', 'entries', 'interaction statuses']
                ]
                
                oxygen_contacts_columns = [
                    'source', 'type', 'contact', 'internet', 'addresses'
                ]
                
                oxygen_column_combinations = [
                    ['source', 'type', 'contact', 'internet', 'addresses']
                ]
                
                tool_scores = {
                    'Magnet Axiom': 0,
                    'Cellebrite': 0,
                    'Oxygen': 0
                }
                
                for sheet_name in sheet_names:
                    try:
                        for header_row in [0, 1, 2]:
                            try:
                                df_test = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str, header=header_row, nrows=3)
                                columns_lower = [str(col).lower().strip() for col in df_test.columns]
                                columns_set = set(columns_lower)
                                sheet_lower = sheet_name.lower()
                                
                                for combo in axiom_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        score = len(combo) * 2 if len(combo) >= 3 else len(combo)
                                        tool_scores['Magnet Axiom'] += score
                                        print(f"[TOOL DETECTION] Found Magnet Axiom column combination in sheet '{sheet_name}': {combo} (score: {score})")
                                
                                if 'contact' in sheet_lower or 'call' in sheet_lower:
                                    contacts_match = sum(1 for col in axiom_contacts_columns if col in columns_set)
                                    calls_match = sum(1 for col in axiom_calls_columns if col in columns_set)
                                    if contacts_match >= 2 or calls_match >= 3:
                                        tool_scores['Magnet Axiom'] += (contacts_match + calls_match)
                                        print(f"[TOOL DETECTION] Bonus score for contacts/calls sheet '{sheet_name}': contacts={contacts_match}, calls={calls_match}")
                                
                                for combo in cellebrite_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        score = len(combo) * 2 if len(combo) >= 4 else len(combo)
                                        tool_scores['Cellebrite'] += score
                                        print(f"[TOOL DETECTION] Found Cellebrite column combination in sheet '{sheet_name}': {combo} (score: {score})")
                                
                                if sheet_lower == 'contacts':
                                    contacts_match = sum(1 for col in cellebrite_contacts_columns if col in columns_set)
                                    if contacts_match >= 4:
                                        tool_scores['Cellebrite'] += contacts_match
                                        print(f"[TOOL DETECTION] Bonus score for Cellebrite Contacts sheet: {contacts_match} columns matched")
                                
                                for combo in oxygen_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        score = len(combo) * 3
                                        tool_scores['Oxygen'] += score
                                        print(f"[TOOL DETECTION] Found Oxygen column combination in sheet '{sheet_name}': {combo} (score: {score})")
                                
                                if 'contact' in sheet_lower:
                                    contacts_match = sum(1 for col in oxygen_contacts_columns if col in columns_set)
                                    if contacts_match >= 3:
                                        tool_scores['Oxygen'] += contacts_match * 2
                                        print(f"[TOOL DETECTION] Bonus score for Oxygen contacts sheet '{sheet_name}': {contacts_match} columns matched")
                                
                                if tool_scores['Magnet Axiom'] >= 5 or tool_scores['Cellebrite'] >= 5 or tool_scores['Oxygen'] >= 5:
                                    break
                                    
                            except Exception as e:
                                continue
                                
                    except Exception as e:
                        print(f"[TOOL DETECTION] Error reading sheet '{sheet_name}': {e}")
                        continue
                
                max_score = max(tool_scores.values())
                if max_score > 0:
                    detected_tool = max(tool_scores, key=tool_scores.get)
                    print(f"[TOOL DETECTION] Tool scores: {tool_scores}")
                    print(f"[TOOL DETECTION] Detected {detected_tool} (Contact Correlation) based on column structure (score: {max_score})")
                    return detected_tool
                
            except Exception as e:
                print(f"[TOOL DETECTION] Error detecting Contact Correlation tool from structure: {e}")
                traceback.print_exc()
                return "Unknown"
            
        except Exception as e:
            print(f"[TOOL DETECTION] Error in _detect_contact_correlation_tool_from_structure: {e}")
            traceback.print_exc()
            return "Unknown"
        
        print(f"[TOOL DETECTION] Could not detect Contact Correlation tool from column structure")
        return "Unknown"

    def _detect_deep_communication_analytics_tool_from_structure(self, file_path: str) -> str:
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext not in ['.xlsx', '.xls']:
                return "Unknown"
            
            try:
                engine = "xlrd" if file_ext == '.xls' else "openpyxl"
                xls = pd.ExcelFile(file_path, engine=engine)
                sheet_names = [str(s) for s in xls.sheet_names]
                
                print(f"[TOOL DETECTION] Analyzing Deep Communication Analytics columns from {len(sheet_names)} sheets (column-based detection only)...")
                
                axiom_key_columns = [
                    'record', 'sender', 'message', 'timestamp', 'thread id', 'thread_id',
                    'recipient', 'receiver'
                ]
                
                axiom_column_combinations = [
                    ['record', 'sender', 'message'],
                    ['record', 'sender', 'timestamp'],
                    ['record', 'thread id', 'message'],
                    ['sender', 'message', 'timestamp']
                ]

                cellebrite_key_columns = [
                    'source', 'author', 'body', 'url', 'account'
                ]
                
                cellebrite_column_combinations = [
                    ['source', 'author', 'body', 'url', 'account']
                ]
                
                oxygen_key_columns = [
                    'source', 'service', 'platform', 'application', 'app',
                    'text', 'message', 'timestamp', 'sender', 'receiver', 'participant'
                ]
                
                oxygen_column_combinations = [
                    ['source', 'service', 'platform'],
                    ['source', 'text', 'timestamp'],
                    ['source', 'message', 'timestamp'],
                    ['service', 'platform', 'application']
                ]
                
                tool_scores = {
                    'Magnet Axiom': 0,
                    'Cellebrite': 0,
                    'Oxygen': 0
                }
                
                for sheet_name in sheet_names:
                    try:
                        for header_row in [0, 1, 2]:
                            try:
                                df_test = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str, header=header_row, nrows=3)
                                columns_lower = [str(col).lower().strip() for col in df_test.columns]
                                columns_set = set(columns_lower)
                                
                                axiom_key_matches = sum(1 for col in axiom_key_columns if col in columns_set)
                                for combo in axiom_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        tool_scores['Magnet Axiom'] += len(combo)
                                        print(f"[TOOL DETECTION] Found Magnet Axiom column combination in sheet '{sheet_name}': {combo}")
                                if axiom_key_matches > 0:
                                    tool_scores['Magnet Axiom'] += axiom_key_matches
                                
                                cellebrite_key_matches = sum(1 for col in cellebrite_key_columns if col in columns_set)
                                for combo in cellebrite_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        tool_scores['Cellebrite'] += len(combo)
                                        print(f"[TOOL DETECTION] Found Cellebrite column combination in sheet '{sheet_name}': {combo}")
                                if cellebrite_key_matches > 0:
                                    tool_scores['Cellebrite'] += cellebrite_key_matches
                                
                                oxygen_key_matches = sum(1 for col in oxygen_key_columns if col in columns_set)
                                for combo in oxygen_column_combinations:
                                    if all(col in columns_set for col in combo):
                                        tool_scores['Oxygen'] += len(combo)
                                        print(f"[TOOL DETECTION] Found Oxygen column combination in sheet '{sheet_name}': {combo}")
                                if oxygen_key_matches > 0:
                                    tool_scores['Oxygen'] += oxygen_key_matches
                                
                                if tool_scores['Magnet Axiom'] >= 5 or tool_scores['Cellebrite'] >= 5 or tool_scores['Oxygen'] >= 5:
                                    break
                                    
                            except Exception as e:
                                continue
                                
                    except Exception as e:
                        print(f"[TOOL DETECTION] Error reading sheet '{sheet_name}': {e}")
                        continue
                
                max_score = max(tool_scores.values())
                if max_score > 0:
                    detected_tool = max(tool_scores, key=tool_scores.get)
                    print(f"[TOOL DETECTION] Tool scores: {tool_scores}")
                    print(f"[TOOL DETECTION] Detected {detected_tool} (Deep Communication Analytics) based on column structure (score: {max_score})")
                    return detected_tool
                
            except Exception as e:
                print(f"[TOOL DETECTION] Error detecting Deep Communication Analytics tool from structure: {e}")
                traceback.print_exc()
                return "Unknown"
            
        except Exception as e:
            print(f"[TOOL DETECTION] Error in _detect_deep_communication_analytics_tool_from_structure: {e}")
            traceback.print_exc()
            return "Unknown"
        
        print(f"[TOOL DETECTION] Could not detect Deep Communication Analytics tool from column structure")
        return "Unknown"

    def _validate_file_format(self, file_path: str, tools: str, method: str) -> Dict[str, Any]:
        try:
            file_ext = Path(file_path).suffix.lower()
            
            hashfile_tool = self._detect_hashfile_tool_from_structure(file_path)
            is_hashfile = hashfile_tool and hashfile_tool != "Unknown"
            
            if method == "Hashfile Analytics":
                if is_hashfile:
                    detected_tool = hashfile_tool
                    normalized_user_tool = self._normalize_tool_name(tools)
                    if normalized_user_tool != detected_tool:
                        print(f"[VALIDATION] File format mismatch: User selected '{tools}' but file is '{detected_tool}' format")
                        return {
                            "is_valid": False,
                            "detected_tool": detected_tool,
                            "detected_method": method
                        }
                else:
                    print(f"[VALIDATION] Could not detect tool from file structure, proceeding with user selection")
                    return {"is_valid": True, "detected_tool": None, "detected_method": method}
            
            elif method == "Deep Communication Analytics":
                if is_hashfile:
                    print(f"[VALIDATION] File is actually a hashfile (detected: {hashfile_tool}), but user selected Deep Communication Analytics")
                    return {
                        "is_valid": False,
                        "detected_tool": hashfile_tool,
                        "detected_method": "Hashfile Analytics"
                    }
                
                # Use column-based detection for Deep Communication Analytics
                detected_tool = self._detect_deep_communication_analytics_tool_from_structure(file_path)
                if detected_tool and detected_tool != "Unknown":
                    normalized_user_tool = self._normalize_tool_name(tools)
                    if normalized_user_tool != detected_tool:
                        print(f"[VALIDATION] File format mismatch: User selected '{tools}' but file is '{detected_tool}' format")
                        return {
                            "is_valid": False,
                            "detected_tool": detected_tool,
                            "detected_method": method
                        }
                else:
                    if file_ext in ['.xlsx', '.xls']:
                        try:
                            xls = pd.ExcelFile(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')
                            sheet_names_lower = [str(s).lower() for s in xls.sheet_names]
                            has_messages = any('message' in s or 'chat' in s or 'text' in s for s in sheet_names_lower)
                            if not has_messages:
                                print(f"[VALIDATION] File does not contain required sheets for Deep Communication Analytics")
                                normalized_user_tool = self._normalize_tool_name(tools)
                                return {
                                    "is_valid": False,
                                    "detected_tool": normalized_user_tool or "Unknown",
                                    "detected_method": method
                                }
                        except:
                            pass
                    return {"is_valid": True, "detected_tool": None, "detected_method": method}
            
            elif method == "Social Media Correlation":
                if is_hashfile:
                    print(f"[VALIDATION] File is actually a hashfile (detected: {hashfile_tool}), but user selected Social Media Correlation")
                    return {
                        "is_valid": False,
                        "detected_tool": hashfile_tool,
                        "detected_method": "Hashfile Analytics"
                    }
                
                detected_tool = self._detect_social_media_correlation_tool_from_structure(file_path)
                if detected_tool and detected_tool != "Unknown":
                    normalized_user_tool = self._normalize_tool_name(tools)
                    if normalized_user_tool != detected_tool:
                        print(f"[VALIDATION] File format mismatch: User selected '{tools}' but file is '{detected_tool}' format")
                        return {
                            "is_valid": False,
                            "detected_tool": detected_tool,
                            "detected_method": method
                        }
                else:
                    if file_ext in ['.xlsx', '.xls']:
                        try:
                            xls = pd.ExcelFile(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')
                            sheet_names_lower = [str(s).lower() for s in xls.sheet_names]
                            has_social_media = any('social' in s or 'instagram' in s or 'facebook' in s or 'whatsapp' in s or 'telegram' in s for s in sheet_names_lower)
                            if not has_social_media:
                                print(f"[VALIDATION] File does not contain required sheets for Social Media Correlation")
                                normalized_user_tool = self._normalize_tool_name(tools)
                                return {
                                    "is_valid": False,
                                    "detected_tool": normalized_user_tool or "Unknown",
                                    "detected_method": method
                                }
                        except:
                            pass
                    return {"is_valid": True, "detected_tool": None, "detected_method": method}
            
            elif method == "Contact Correlation":
                if is_hashfile:
                    print(f"[VALIDATION] File is actually a hashfile (detected: {hashfile_tool}), but user selected Contact Correlation")
                    return {
                        "is_valid": False,
                        "detected_tool": hashfile_tool,
                        "detected_method": "Hashfile Analytics"
                    }
                
                # Use column-based detection for Contact Correlation
                detected_tool = self._detect_contact_correlation_tool_from_structure(file_path)
                if detected_tool and detected_tool != "Unknown":
                    normalized_user_tool = self._normalize_tool_name(tools)
                    if normalized_user_tool != detected_tool:
                        print(f"[VALIDATION] File format mismatch: User selected '{tools}' but file is '{detected_tool}' format")
                        return {
                            "is_valid": False,
                            "detected_tool": detected_tool,
                            "detected_method": method
                        }
                else:
                    if file_ext in ['.xlsx', '.xls']:
                        try:
                            xls = pd.ExcelFile(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')
                            sheet_names_lower = [str(s).lower() for s in xls.sheet_names]
                            has_contacts = any('contact' in s for s in sheet_names_lower)
                            if not has_contacts:
                                print(f"[VALIDATION] File does not contain required sheets for Contact Correlation")
                                normalized_user_tool = self._normalize_tool_name(tools)
                                return {
                                    "is_valid": False,
                                    "detected_tool": normalized_user_tool or "Unknown",
                                    "detected_method": method
                                }
                        except:
                            pass
                    return {"is_valid": True, "detected_tool": None, "detected_method": method}
            
            return {"is_valid": True, "detected_tool": None, "detected_method": method}
            
        except Exception as e:
            print(f"[VALIDATION] Error validating file format: {e}")
            traceback.print_exc()
            return {"is_valid": True, "detected_tool": None, "detected_method": method}

    def _mark_done(self, upload_id: str, message: str, is_error: bool = False, detected_tool: str = None, method: str = None, tools: str = None, detected_method: str = None):
        data = self._progress.get(upload_id)
        update_data = {
            "message": message, 
            "done": True,
            "error": is_error,
            "detected_tool": detected_tool
        }
        
        if method:
            update_data["method"] = method
        if detected_method:
            update_data["detected_method"] = detected_method
        if tools:
            update_data["tools"] = tools
        
        if not data:
            self._progress[upload_id] = update_data
        else:
            data.update(update_data)

    def _cleanup_failed_upload(self, file_id: int = None, file_path: str = None):
        try:
            db = next(get_db())
            
            if file_id:
                file_record = db.query(File).filter(File.id == file_id).first()
                if file_record:
                    db.query(SocialMedia).filter(SocialMedia.file_id == file_id).delete()
                    db.query(Contact).filter(Contact.file_id == file_id).delete()
                    db.query(Call).filter(Call.file_id == file_id).delete()
                    db.query(HashFile).filter(HashFile.file_id == file_id).delete()
                    db.query(ChatMessage).filter(ChatMessage.file_id == file_id).delete()
                    db.delete(file_record)
                    db.commit()
                    print(f"[CLEANUP] Deleted file record {file_id} and related data from database")
            
            if file_path:
                try:
                    full_path = os.path.join(BASE_DIR, file_path) if not os.path.isabs(file_path) else file_path
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f"[CLEANUP] Deleted physical file: {full_path}")
                except Exception as e:
                    print(f"[CLEANUP] Error deleting physical file {file_path}: {str(e)}")
                    
        except Exception as e:
            print(f"[CLEANUP] Error during cleanup: {str(e)}")
            traceback.print_exc()

    def get_progress(self, upload_id: str):
        data = self._progress.get(upload_id)
        if not data:
            return {"status": 404, "message": "Upload ID not found", "data": None}, 404
        
        message = data.get("message", "")
        method = data.get("method")
        
        if method == "Hashfile Analytics" and "File upload failed. Please upload this file using Tools" in message and "with method" not in message:
            tool_match = message.split("Tools ")[1].split()[0] if "Tools " in message else None
            if tool_match:
                message = f"File upload failed. Please upload this file using Tools {tool_match} with method {method}"
        
        return {
            "status": 200,
            "message": message,
            "data": {
                "percent": data.get("percent", 0),
                "progress_size": data.get("progress_size", "0 B"),
                "total_size": data.get("total_size"),
                "done": data.get("done", False),
                "error": data.get("error", False),
                "file_id": data.get("file_id"),
                "detected_tool": data.get("detected_tool"),
                "method": method,
                "tools": data.get("tools"),
            },
        }, 200

    def cancel(self, upload_id: str):
        if upload_id not in self._progress:
            return {"status": 404, "message": "Upload ID not found", "data": None}, 404
        self._progress[upload_id]["cancel"] = True
        self._progress[upload_id]["message"] = "Canceling..."

    def _serialize_contacts_for_json(self, contacts: list) -> list:
        serialized_contacts = []
        for contact in contacts:
            serialized_contact = contact.copy()
            if 'last_time_contacted' in serialized_contact and serialized_contact['last_time_contacted']:
                if isinstance(serialized_contact['last_time_contacted'], datetime):
                    serialized_contact['last_time_contacted'] = serialized_contact['last_time_contacted'].isoformat()
            serialized_contacts.append(serialized_contact)
        return serialized_contacts

    async def start_file_upload(
        self,
        upload_id: str,
        file: UploadFile,
        file_name: str,
        notes: str | None,
        created_by: str | None = None,
        type: str = None,
        tools: str = None,
        file_bytes: bytes = None,
        method: str | None = None,
    ):
        start_time = time.time()
        if upload_id in self._progress and not self._progress[upload_id].get("done"):
            return {"status": 400, "message": "Upload ID sedang berjalan", "data": None}
            
        self._init_state(upload_id)
        self._progress[upload_id]["_processing"] = True

        file_record_inserted = False
        file_id = None
        rel_path = None
        
        try:
            original_filename = file.filename
            if not original_filename:
                self._mark_done(upload_id, "Filename is required", is_error=True)
                return {"status": 400, "message": "Filename is required", "data": None}
            
            total_size = len(file_bytes)
            self._progress[upload_id].update(
                {
                    "total_size": format_bytes(total_size), 
                    "message": "Memulai upload...",
                    "method": method,
                    "tools": tools,
                }
            )

            file_ext = Path(original_filename).suffix.lower()
            CHUNK = 1024 * 512
            written = 0
            if file_ext == ".sdp":
                encrypted_path_abs = os.path.join(ENCRYPTED_DIR, original_filename)
                with open(encrypted_path_abs, "wb") as f:
                    for i in range(0, total_size, CHUNK):
                        if self._is_canceled(upload_id):
                            self._mark_done(upload_id, "Upload canceled")
                            return {"status": 200, "message": "Upload canceled", "data": {"done": True}}
                        chunk = file_bytes[i:i + CHUNK]
                        f.write(chunk)
                        written += len(chunk)

                        percent = (written / total_size) * 60
                        progress_bytes = int((percent / 100) * total_size)
                        self._progress[upload_id].update({
                            "percent": round(percent, 2),
                            "progress_size": format_bytes(progress_bytes),
                            "message": f"Uploading... ({percent:.2f}%)",
                        })
                        await asyncio.sleep(0.02)

                try:
                    self._progress[upload_id].update({"message": "Decrypting file...", "percent": 75})
                    priv_key = _load_existing_private_key()
                    
                    loop = asyncio.get_event_loop()
                    try:
                        decrypted_path_abs = await asyncio.wait_for(
                            loop.run_in_executor(None, decrypt_from_sdp, priv_key, encrypted_path_abs, DATA_DIR),
                            timeout=300.0
                        )
                    except asyncio.TimeoutError:
                        detected_tool_for_error = self._normalize_tool_name(tools) if tools else "Unknown"
                        error_message = f"Upload hash data not found in file with {method or 'Unknown'} method and {detected_tool_for_error} tools."
                        self._mark_done(upload_id, error_message, is_error=True, detected_tool=detected_tool_for_error, method=method, tools=tools)
                        return {"status": 500, "message": error_message, "data": None, "detected_tool": detected_tool_for_error}
                    except Exception as e:
                        detected_tool_for_error = self._normalize_tool_name(tools) if tools else "Unknown"
                        error_message = f"Upload hash data not found in file with {method or 'Unknown'} method and {detected_tool_for_error} tools."
                        self._mark_done(upload_id, error_message, is_error=True, detected_tool=detected_tool_for_error, method=method, tools=tools)
                        return {"status": 500, "message": error_message, "data": None, "detected_tool": detected_tool_for_error}
                    
                    self._progress[upload_id].update({"message": "Decryption completed", "percent": 80})
                    
                    expected_name = os.path.splitext(original_filename)[0]
                    expected_abs = os.path.join(DATA_DIR, expected_name)
                    if os.path.abspath(decrypted_path_abs) != os.path.abspath(expected_abs):
                        
                        if os.path.exists(expected_abs):
                            try:
                                os.remove(expected_abs)
                            except Exception:
                                pass
                        try:
                            os.replace(decrypted_path_abs, expected_abs)
                            decrypted_path_abs = expected_abs
                        except Exception:
                            pass
                except Exception as e:
                    detected_tool_for_error = self._normalize_tool_name(tools) if tools else "Unknown"
                    error_message = f"Upload hash data not found in file with {method or 'Unknown'} method and {detected_tool_for_error} tools."
                    self._mark_done(upload_id, error_message, is_error=True, detected_tool=detected_tool_for_error, method=method, tools=tools)
                    return {"status": 500, "message": error_message, "data": None, "detected_tool": detected_tool_for_error}

                original_path_abs = decrypted_path_abs
                original_filename = Path(decrypted_path_abs).name
            else:
                original_path_abs = os.path.join(DATA_DIR, original_filename)
                with open(original_path_abs, "wb") as f:
                    for i in range(0, total_size, CHUNK):
                        if self._is_canceled(upload_id):
                            self._mark_done(upload_id, "Upload canceled")
                            return {"status": 200, "message": "Upload canceled", "data": {"done": True}}
                        chunk = file_bytes[i:i + CHUNK]
                        f.write(chunk)
                        written += len(chunk)

                        percent = (written / total_size) * 60
                        progress_bytes = int((percent / 100) * total_size)
                        self._progress[upload_id].update({
                            "percent": round(percent, 2),
                            "progress_size": format_bytes(progress_bytes),
                            "message": f"Uploading... ({percent:.2f}%)",
                        })
                        await asyncio.sleep(0.02)

            current_percent = self._progress[upload_id].get("percent", 60)
            start_percent = max(60, int(current_percent))
            
            for i in range(start_percent, 95):
                if self._is_canceled(upload_id):
                    self._mark_done(upload_id, "Processing canceled")
                    return {"status": 200, "message": "Processing canceled", "data": {"done": True}}

                phase_ratio = (i - 60) / 35 if i >= 60 else 0
                current_bytes = int(0.6 * total_size + phase_ratio * 0.4 * total_size)
                self._progress[upload_id].update({
                    "percent": i,
                    "progress_size": format_bytes(current_bytes),
                    "message": f"Preparing... ({i}%)"
                })
                await asyncio.sleep(0.03)

            self._progress[upload_id].update({
                "message": "Validating file format...",
                "percent": 94
            })
            
            validation_result = self._validate_file_format(original_path_abs, tools, method)

            validation_passed = validation_result.get("is_valid", False)
            validated_tool = validation_result.get("detected_tool")
            validated_method = validation_result.get("detected_method", method)
            
            if not validation_result["is_valid"]:
                detected_tool = validation_result.get("detected_tool")
                detected_method = validation_result.get("detected_method", method)
                
                if not detected_tool or detected_tool == "Unknown":
                    detected_tool = self._normalize_tool_name(tools) or tools or "Unknown"
                
                error_message = f"Upload hash data not found in file with {detected_method} method and {detected_tool} tools."
                size_message = f"File upload failed. Please upload this file using Tools {detected_tool} with method {detected_method}"
                
                self._mark_done(upload_id, error_message, is_error=True, detected_tool=detected_tool, method=detected_method, tools=tools, detected_method=detected_method)
                try:
                    if os.path.exists(original_path_abs):
                        os.remove(original_path_abs)
                        print(f"[CLEANUP] Deleted file due to format mismatch: {original_path_abs}")
                except Exception as cleanup_error:
                    print(f"[CLEANUP] Error deleting file: {str(cleanup_error)}")
                
                return {
                    "status": 400,
                    "message": error_message,
                    "data": None,
                    "detected_tool": detected_tool,
                    "detected_method": detected_method
                }
            
            self._progress[upload_id].update({
                "message": "Starting data parsing...",
                "percent": 95
            })
            
            rel_path = os.path.relpath(original_path_abs, BASE_DIR)
            db = next(get_db())
            file_record = File(
                file_name=file_name,
                file_path=rel_path,
                notes=notes,
                created_by=created_by,
                type=type,
                tools=tools,
                method=method,
                total_size=total_size,
                amount_of_data=0,
            )
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            file_id = int(file_record.id)
            file_record_inserted = True
            
            parsing_result = {
                "tool_used": tools,
                "contacts_count": 0,
                "messages_count": 0,
                "calls_count": 0,
                "hashfiles_count": 0,
                "social_media_count": 0,
                "chat_messages_count": 0,
                "parsing_success": True
            }
            
            if method == "Social Media Correlation":
                try:
                    self._progress[upload_id].update({
                        "message": "Parsing social media data...",
                        "percent": 97.5
                    })
                    if tools == "Magnet Axiom":
                        social_media_result = sm_parser.parse_axiom_social_media(original_path_abs, file_id)
                    elif tools == "Cellebrite":
                        social_media_result = sm_parser.parse_cellebrite_social_media(original_path_abs, file_id)
                    elif tools == "Oxygen":
                        try:
                            xls = pd.ExcelFile(original_path_abs, engine='xlrd')
                            
                            social_media_sheets = ['Instagram ', 'Telegram ', 'WhatsApp Messenger ', 'X (Twitter) ', 'Users-Following ', 'Users-Followers ']
                            has_social_media_sheets = any(sheet in xls.sheet_names for sheet in social_media_sheets)
                            
                            if has_social_media_sheets:
                                
                                social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, file_id)
                            else:
                                
                                social_media_result = sm_parser.parse_oxygen_ufed_social_media(original_path_abs, file_id)
                        except Exception as e:
                            print(f"Error determining Oxygen format: {e}")
                            social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, file_id)
                    else:
                            social_media_result = sm_parser.parse_oxygen_social_media(original_path_abs, file_id)
                    
                    if social_media_result:
                        parsing_result["social_media_count"] = len(social_media_result)
                    else:
                        parsing_result["social_media_count"] = 0
                        if validation_passed:
                            parsing_result["social_media_error"] = f"Social Media Correlation data not found in file. The file format is correct ({tools} with {method} method), but no social media data exists in this file."
                            print(f"[WARNING] No social media data found in file for method '{method}' with tools '{tools}'. Tools/method are correct, but data doesn't exist.")
                        else:
                            detected_tool_for_error = validated_tool
                            if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                                try:
                                    if os.path.exists(original_path_abs):
                                        detected_tool_for_error = self._detect_social_media_correlation_tool_from_structure(original_path_abs)
                                        if detected_tool_for_error and detected_tool_for_error != "Unknown":
                                            print(f"[TOOL DETECTION] Detected correct tool for Social Media Correlation: {detected_tool_for_error}")
                                except:
                                    pass
                            
                            if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                                detected_tool_for_error = self._normalize_tool_name(tools) or tools or "Unknown"
                            
                            parsing_result["social_media_error"] = f"Upload hash data not found in file with {method} method and {detected_tool_for_error} tools."
                            print(f"[WARNING] No social media data found in file for method '{method}' with tools '{tools}'. Possible tool/method mismatch.")
                    self._progress[upload_id].update({
                        "message": "Inserting social media data to database...",
                        "percent": 98.5
                    })
                except Exception as e:
                    print(f"Error parsing social media: {e}")
                    parsing_result["social_media_error"] = str(e)
            
            elif method == "Deep Communication Analytics":
                try:
                    self._progress[upload_id].update({
                        "message": "Parsing chat messages data...",
                        "percent": 97.5
                    })
                    if tools == "Magnet Axiom":
                        chat_messages_result = sm_parser.parse_axiom_chat_messages(original_path_abs, file_id)
                    elif tools == "Cellebrite":
                        chat_messages_result = sm_parser.parse_cellebrite_chat_messages(original_path_abs, file_id)
                    elif tools == "Oxygen":
                        print(f"Calling parse_oxygen_chat_messages for file_id={file_id}")
                        chat_messages_result = sm_parser.parse_oxygen_chat_messages(original_path_abs, file_id)
                        print(f"parse_oxygen_chat_messages returned {len(chat_messages_result) if chat_messages_result else 0} messages")
                    else:
                        chat_messages_result = []
                    
                    if chat_messages_result:
                        parsing_result["chat_messages_count"] = len(chat_messages_result)
                        print(f"Set chat_messages_count to {len(chat_messages_result)}")
                    else:
                        parsing_result["chat_messages_count"] = 0
                        
                        if validation_passed:
                            parsing_result["chat_messages_error"] = f"Deep Communication Analytics data not found in file. The file format is correct ({tools} with {method} method), but no chat messages data exists in this file."
                            print(f"[WARNING] No chat messages data found in file for method '{method}' with tools '{tools}'. Tools/method are correct, but data doesn't exist.")
                        else:
                            hashfile_tool = self._detect_hashfile_tool_from_structure(original_path_abs)
                            if hashfile_tool and hashfile_tool != "Unknown":
                                detected_tool = hashfile_tool
                                detected_method = "Hashfile Analytics"
                                parsing_result["detected_tool"] = detected_tool
                                print(f"[DETECTION] File is actually a hashfile ({hashfile_tool}), redirecting to Hashfile Analytics")
                            else:
                                detected_tool = validated_tool
                                if not detected_tool or detected_tool == "Unknown":
                                    try:
                                        detected_tool = self._detect_deep_communication_analytics_tool_from_structure(original_path_abs)
                                        if not detected_tool or detected_tool == "Unknown":
                                            detected_tool = self._normalize_tool_name(tools) or tools or "Unknown"
                                    except:
                                        detected_tool = self._normalize_tool_name(tools) or tools or "Unknown"
                                detected_method = method
                                parsing_result["detected_tool"] = detected_tool
                            
                            parsing_result["chat_messages_error"] = f"Upload hash data not found in file with {detected_method} method and {detected_tool} tools."
                            print(f"[WARNING] No chat messages data found in file for method '{method}' with tools '{tools}'. Possible tool/method mismatch. Detected tool: {detected_tool}, method: {detected_method}")
                    self._progress[upload_id].update({
                        "message": "Inserting chat messages data to database...",
                        "percent": 98.5
                    })
                except Exception as e:
                    print(f"Error parsing chat messages: {e}")
                    hashfile_tool = self._detect_hashfile_tool_from_structure(original_path_abs)
                    if hashfile_tool and hashfile_tool != "Unknown":
                        detected_tool = hashfile_tool
                        detected_method = "Hashfile Analytics"
                        parsing_result["detected_tool"] = detected_tool
                        print(f"[DETECTION] File is actually a hashfile ({hashfile_tool}), redirecting to Hashfile Analytics")
                    else:
                        detected_tool = self._detect_tool_from_sheets(original_path_abs, method)
                        detected_method = method or "Deep Communication Analytics"
                        parsing_result["detected_tool"] = detected_tool
                        if not detected_tool or detected_tool == "Unknown":
                            try:
                                detected_tool = self._detect_tool_from_sheets(original_path_abs, method)
                                parsing_result["detected_tool"] = detected_tool
                            except:
                                pass
                        
                        if not detected_tool or detected_tool == "Unknown":
                            detected_tool = self._normalize_tool_name(tools) or tools or "Unknown"
                            if detected_tool:
                                parsing_result["detected_tool"] = detected_tool

                    parsing_result["chat_messages_error"] = f"Upload hash data not found in file with {detected_method} method and {detected_tool} tools."
            
            elif method == "Contact Correlation":
                try:
                    self._progress[upload_id].update({
                        "message": "Parsing contacts and calls data...",
                        "percent": 97.5
                    })
                    contact_parser = ContactParser(db=sm_db)
                    
                    if tools == "Magnet Axiom":
                        contacts_result = contact_parser.parse_axiom_contacts(original_path_abs, file_id)
                        calls_result = contact_parser.parse_axiom_calls(original_path_abs, file_id)
                    elif tools == "Cellebrite":
                        contacts_result = contact_parser.parse_cellebrite_contacts(original_path_abs, file_id)
                        calls_result = contact_parser.parse_cellebrite_calls(original_path_abs, file_id)
                    elif tools == "Oxygen":
                        contacts_result = contact_parser.parse_oxygen_contacts(original_path_abs, file_id)
                        calls_result = contact_parser.parse_oxygen_calls(original_path_abs, file_id)
                    else:
                        contacts_result = contact_parser.parse_oxygen_contacts(original_path_abs, file_id)
                        calls_result = contact_parser.parse_oxygen_calls(original_path_abs, file_id)
                    
                    if contacts_result:
                        parsing_result["contacts_count"] = len(contacts_result)
                    else:
                        parsing_result["contacts_count"] = 0
                    if calls_result:
                        parsing_result["calls_count"] = len(calls_result)
                    else:
                        parsing_result["calls_count"] = 0

                    if not contacts_result and not calls_result:
                        if validation_passed:
                            parsing_result["contacts_calls_error"] = f"Contact Correlation data not found in file. The file format is correct ({tools} with {method} method), but no contact or call data exists in this file."
                            print(f"[WARNING] No contacts or calls data found in file for method '{method}' with tools '{tools}'. Tools/method are correct, but data doesn't exist.")
                        else:
                            detected_tool_for_error = validated_tool
                            if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                                try:
                                    if os.path.exists(original_path_abs):
                                        detected_tool_for_error = self._detect_contact_correlation_tool_from_structure(original_path_abs)
                                        if detected_tool_for_error and detected_tool_for_error != "Unknown":
                                            print(f"[TOOL DETECTION] Detected correct tool for Contact Correlation: {detected_tool_for_error}")
                                except:
                                    pass
                            
                            if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                                detected_tool_for_error = self._normalize_tool_name(tools) or tools or "Unknown"
                            
                            parsing_result["contacts_calls_error"] = f"Contacts and calls data not found in file with {method} method and {detected_tool_for_error} tools."
                            print(f"[WARNING] No contacts or calls data found in file for method '{method}' with tools '{tools}'. Possible tool/method mismatch.")
                    
                    self._progress[upload_id].update({
                        "message": "Inserting contacts and calls data to database...",
                        "percent": 98.5
                    })
                except Exception as e:
                    print(f"Error parsing contacts/calls: {e}")
                    parsing_result["contacts_calls_error"] = str(e)
            
            elif method == "Hashfile Analytics":
                detected_tool_from_file = None
                try:
                    self._progress[upload_id].update({
                        "message": "Preparing hashfile parsing...",
                        "percent": 97.0
                    })
                    
                    try:
                        if os.path.exists(original_path_abs):
                            detected_tool_from_file = self._detect_hashfile_tool_from_structure(original_path_abs)
                            print(f"[TOOL DETECTION] Pre-parsing detection: Detected tool '{detected_tool_from_file}' from file structure")
                            if detected_tool_from_file and detected_tool_from_file != "Unknown" and detected_tool_from_file != tools:
                                print(f"[TOOL DETECTION] Detected tool '{detected_tool_from_file}' differs from user selection '{tools}'. Will use detected tool for error messages.")
                    except Exception as e:
                        print(f"[TOOL DETECTION] Error in pre-parsing tool detection: {e}")
                        pass
                    
                    hashfile_parser_instance = HashFileParser(db=db)
                    
                    is_sample_file = any(pattern in original_filename.lower() for pattern in [
                        'oxygen', 'cellebrite', 'magnet axiom', 'encase', 'hashfile'
                    ])
                    
                    if is_sample_file:
                        if original_filename:
                            original_file_path = os.path.abspath(os.path.join(os.getcwd(), 'sample_hashfile', original_filename))
                        else:
                            original_file_path = original_path_abs
                    else:
                        original_file_path = original_path_abs
                    
                    def update_hashfile_progress(upload_id: str, progress_info: dict):
                        self._progress[upload_id].update({
                            "message": progress_info.get("message", "Processing hashfiles..."),
                            "percent": progress_info.get("percent", 97.5),
                            "amount_of_data": progress_info.get("amount_of_data", 0)
                        })
                    
                    try:
                        hashfiles_result = hashfile_parser_instance.parse_hashfile(
                            original_path_abs, 
                            file_id, 
                            tools, 
                            original_file_path,
                            upload_id=upload_id,
                            progress_callback=update_hashfile_progress
                        )
                        
                        if hashfiles_result:
                            if isinstance(hashfiles_result, int):
                                parsing_result["hashfiles_count"] = hashfiles_result
                            else:
                                parsing_result["hashfiles_count"] = len(hashfiles_result)
                        else:
                            parsing_result["hashfiles_count"] = 0
                    except ValueError as ve:
                        error_str = str(ve)
                        if "Upload hash data not found" in error_str or "hash data not found" in error_str.lower():
                            print(f"[HASHFILE PARSING] ValueError caught: {error_str}")
                            parsing_result["hashfiles_count"] = 0
                            
                            detected_tool_for_error = detected_tool_from_file
                            
                            if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                                try:
                                    if os.path.exists(original_path_abs):
                                        detected_tool_for_error = self._detect_hashfile_tool_from_structure(original_path_abs)
                                        print(f"[TOOL DETECTION] Detected tool from file structure (ValueError): {detected_tool_for_error}")
                                except Exception as e:
                                    print(f"[TOOL DETECTION] Error detecting tool from structure: {e}")
                                    pass
                            
                            if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                                try:
                                    if os.path.exists(original_path_abs):
                                        detected_tool_for_error = self._detect_tool_from_sheets(original_path_abs, method)
                                        if detected_tool_for_error and detected_tool_for_error != "Unknown":
                                            print(f"[TOOL DETECTION] Detected tool from all sheets (ValueError): {detected_tool_for_error}")
                                except Exception as e:
                                    print(f"[TOOL DETECTION] Error detecting tool from all sheets: {e}")
                                    pass
                            
                            if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                                print(f"[TOOL DETECTION] WARNING: Could not detect tool from file structure (ValueError). Falling back to user selection '{tools}' (this may be incorrect).")
                                detected_tool_for_error = self._normalize_tool_name(tools) or tools or "Unknown"
                            
                            print(f"[TOOL DETECTION] Using tool '{detected_tool_for_error}' for error message (ValueError).")
                            if detected_tool_for_error != tools:
                                print(f"[TOOL DETECTION] Detected tool '{detected_tool_for_error}' differs from user selection '{tools}'. Using detected tool.")
                            
                            parsing_result["hashfiles_error"] = f"Upload hash data not found in file with {method or 'Hashfile Analytics'} method and {detected_tool_for_error} tools."
                            parsing_result["detected_tool"] = detected_tool_for_error
                        else:
                            raise
                    
                    if parsing_result.get("hashfiles_count", 0) == 0:
                        detected_tool_for_error = detected_tool_from_file
                        
                        if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                            try:
                                if os.path.exists(original_path_abs):
                                    detected_tool_for_error = self._detect_hashfile_tool_from_structure(original_path_abs)
                                    print(f"[TOOL DETECTION] Detected tool from file structure: {detected_tool_for_error}")
                            except Exception as e:
                                print(f"[TOOL DETECTION] Error detecting tool from structure: {e}")
                                pass
                        
                        if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                            try:
                                if os.path.exists(original_path_abs):
                                    detected_tool_for_error = self._detect_tool_from_sheets(original_path_abs, method)
                                    if detected_tool_for_error and detected_tool_for_error != "Unknown":
                                        print(f"[TOOL DETECTION] Detected tool from all sheets: {detected_tool_for_error}")
                            except Exception as e:
                                print(f"[TOOL DETECTION] Error detecting tool from all sheets: {e}")
                                pass
                        
                        if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                            print(f"[TOOL DETECTION] WARNING: Could not detect tool from file structure. Falling back to user selection '{tools}' (this may be incorrect).")
                            detected_tool_for_error = self._normalize_tool_name(tools) or tools or "Unknown"
                        
                        print(f"[TOOL DETECTION] Using tool '{detected_tool_for_error}' for error message.")
                        if detected_tool_for_error != tools:
                            print(f"[TOOL DETECTION] Detected tool '{detected_tool_for_error}' differs from user selection '{tools}'. Using detected tool.")
                        
                        parsing_result["hashfiles_error"] = f"Upload hash data not found in file with {method} method and {detected_tool_for_error} tools."
                        parsing_result["detected_tool"] = detected_tool_for_error
                        print(f"[WARNING] No hashfile data found in file for method '{method}' with tools '{tools}'. Detected tool: {detected_tool_for_error}")
                    
                    self._progress[upload_id].update({
                        "message": f"Hashfile parsing completed ({parsing_result['hashfiles_count']:,} records)...",
                        "percent": 99.0,
                        "amount_of_data": parsing_result["hashfiles_count"]
                    })
                except Exception as e:
                    print(f"Error parsing hashfiles: {e}")
                    traceback.print_exc()
                    
                    parsing_result["hashfiles_count"] = 0
 
                    error_str = str(e)
                    
                    detected_tool_for_error = detected_tool_from_file
                    
                    if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                        try:
                            if os.path.exists(original_path_abs):
                                detected_tool_for_error = self._detect_hashfile_tool_from_structure(original_path_abs)
                                print(f"[TOOL DETECTION] Detected tool from file structure (exception): {detected_tool_for_error}")
                        except Exception as e:
                            print(f"[TOOL DETECTION] Error detecting tool from structure: {e}")
                            pass
                    
                    if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                        try:
                            if os.path.exists(original_path_abs):
                                detected_tool_for_error = self._detect_tool_from_sheets(original_path_abs, method)
                                if detected_tool_for_error and detected_tool_for_error != "Unknown":
                                    print(f"[TOOL DETECTION] Detected tool from all sheets (exception): {detected_tool_for_error}")
                        except Exception as e:
                            print(f"[TOOL DETECTION] Error detecting tool from all sheets: {e}")
                            pass
                    
                    if not detected_tool_for_error or detected_tool_for_error == "Unknown":
                        print(f"[TOOL DETECTION] WARNING: Could not detect tool from file structure (exception). Falling back to user selection '{tools}' (this may be incorrect).")
                        detected_tool_for_error = self._normalize_tool_name(tools) or tools or "Unknown"
                    
                    print(f"[TOOL DETECTION] Using tool '{detected_tool_for_error}' for error message (exception).")
                    if detected_tool_for_error != tools:
                        print(f"[TOOL DETECTION] Detected tool '{detected_tool_for_error}' differs from user selection '{tools}'. Using detected tool.")
                    
                    parsing_result["hashfiles_error"] = f"Upload hash data not found in file with {method or 'Hashfile Analytics'} method and {detected_tool_for_error} tools."
                    parsing_result["detected_tool"] = detected_tool_for_error
            
            self._progress[upload_id].update({
                "message": "Finalizing database records...",
                "percent": 99
            })
            
            actual_social_media_count = db.query(SocialMedia).filter(SocialMedia.file_id == file_record.id).count()
            actual_contacts_count = db.query(Contact).filter(Contact.file_id == file_record.id).count()
            actual_calls_count = db.query(Call).filter(Call.file_id == file_record.id).count()
            actual_hashfiles_count = db.query(HashFile).filter(HashFile.file_id == file_record.id).count()
            actual_chat_messages_count = db.query(ChatMessage).filter(ChatMessage.file_id == file_record.id).count()
            
            actual_amount_of_data = actual_social_media_count + actual_contacts_count + actual_calls_count + actual_hashfiles_count + actual_chat_messages_count
            if actual_amount_of_data == 0:
                
                has_parsing_error = (
                    "error" in parsing_result or 
                    "parsing_error" in parsing_result or parsing_result.get("parsing_success") == False or
                    "chat_messages_error" in parsing_result or
                    "social_media_error" in parsing_result or
                    "contacts_calls_error" in parsing_result or
                    "hashfiles_error" in parsing_result
                )
                
                detected_tool = parsing_result.get("detected_tool", None)
                
                if has_parsing_error:
                    error_msg = (
                        parsing_result.get("hashfiles_error") or
                        parsing_result.get("chat_messages_error") or
                        parsing_result.get("social_media_error") or
                        parsing_result.get("contacts_calls_error") or
                        parsing_result.get("parsing_error") or 
                        parsing_result.get("error") or 
                        "Tools tidak sesuai dengan format file"
                    )
                    print(f"[ERROR] No data inserted. Parsing error detected: {error_msg}")
                    print(f"[ERROR] Detected tool from parsing_result: {detected_tool}")
                    print(f"[ERROR] Method from user selection: {method}")
                    
                    if method != "Hashfile Analytics" and ("Upload hash data not found" in error_msg or "not found" in error_msg.lower()):
                        try:
                            if os.path.exists(original_path_abs):
                                print(f"[ERROR HANDLING] Attempting to re-detect hashfile for method '{method}'...")
                                hashfile_tool_check = self._detect_hashfile_tool_from_structure(original_path_abs)
                                if hashfile_tool_check and hashfile_tool_check != "Unknown":
                                    print(f"[ERROR HANDLING] ✓ Re-detected hashfile tool: {hashfile_tool_check}")
                                    print(f"[ERROR HANDLING] Updating error message from '{method}' to 'Hashfile Analytics'")
                                    detected_tool = hashfile_tool_check
                                    error_msg = f"Upload hash data not found in file with Hashfile Analytics method and {hashfile_tool_check} tools."
                                    parsing_result["detected_tool"] = hashfile_tool_check
                                    print(f"[ERROR HANDLING] Updated error message: {error_msg}")
                                else:
                                    print(f"[ERROR HANDLING] ✗ Could not re-detect hashfile tool (result: {hashfile_tool_check})")
                        except Exception as e:
                            print(f"[ERROR HANDLING] Exception during hashfile re-detection: {e}")
                            traceback.print_exc()
                    
                    detected_method_from_error = None
                    detected_tool_from_error = None
                    if " with " in error_msg and " method" in error_msg and " and " in error_msg and " tools." in error_msg:
                        try:
                            method_part = error_msg.split(" with ")[1].split(" method")[0].strip()
                            tool_part = error_msg.split(" and ")[-1].replace(" tools.", "").strip()
                            if method_part:
                                detected_method_from_error = method_part
                            if tool_part and tool_part != "Unknown":
                                detected_tool_from_error = tool_part
                            print(f"[ERROR HANDLING] Extracted from error_msg - method: {detected_method_from_error}, tool: {detected_tool_from_error}")
                        except Exception as e:
                            print(f"[ERROR HANDLING] Error extracting method/tool from error_msg: {e}")

                    if detected_method_from_error and detected_tool_from_error and detected_tool_from_error != "Unknown":
                        print(f"[ERROR HANDLING] Using detected values from error_msg: method={detected_method_from_error}, tool={detected_tool_from_error}")
                        detected_tool = detected_tool_from_error
                        error_msg = f"Upload hash data not found in file with {detected_method_from_error} method and {detected_tool_from_error} tools."
                    elif detected_method_from_error:
                        print(f"[ERROR HANDLING] Using detected method from error_msg: {detected_method_from_error}")
                        error_msg = f"Upload hash data not found in file with {detected_method_from_error} method and {detected_tool} tools."

                    if not detected_tool or detected_tool == "Unknown" or (method == "Hashfile Analytics" and "Upload hash data not found" in error_msg):
                        if method == "Hashfile Analytics":
                            try:
                                if os.path.exists(original_path_abs):
                                    detected_tool = self._detect_hashfile_tool_from_structure(original_path_abs)
                                    print(f"[TOOL DETECTION] Detected tool from file structure (fallback): {detected_tool}")
                                    
                                    if detected_tool and detected_tool != "Unknown" and "Upload hash data not found" in error_msg:
                                        
                                        method_from_error = method
                                        if " with " in error_msg and " method" in error_msg:
                                            try:
                                                method_part = error_msg.split(" with ")[1].split(" method")[0].strip()
                                                if method_part:
                                                    method_from_error = method_part
                                            except:
                                                pass
                                        error_msg = f"Upload hash data not found in file with {method_from_error or 'Hashfile Analytics'} method and {detected_tool} tools."
                                        print(f"[TOOL DETECTION] Updated error message with detected tool: {error_msg}")
                            except:
                                pass
                        
                        if not detected_tool or detected_tool == "Unknown":
                            try:
                                if os.path.exists(original_path_abs):
                                    if method == "Social Media Correlation":
                                        detected_tool = self._detect_social_media_correlation_tool_from_structure(original_path_abs)
                                        print(f"[TOOL DETECTION] Detected tool from columns (fallback for Social Media Correlation): {detected_tool}")
                                    elif method == "Contact Correlation":
                                        detected_tool = self._detect_contact_correlation_tool_from_structure(original_path_abs)
                                        print(f"[TOOL DETECTION] Detected tool from columns (fallback for Contact Correlation): {detected_tool}")
                                    elif method == "Deep Communication Analytics":
                                        detected_tool = self._detect_deep_communication_analytics_tool_from_structure(original_path_abs)
                                        print(f"[TOOL DETECTION] Detected tool from columns (fallback for Deep Communication Analytics): {detected_tool}")
                                    else:
                                        detected_tool = self._detect_tool_from_sheets(original_path_abs, method)
                                        print(f"[TOOL DETECTION] Detected tool from sheets (fallback): {detected_tool}")
                            except:
                                pass
                        
                        if not detected_tool or detected_tool == "Unknown":
                            detected_tool = self._normalize_tool_name(tools)
                else:
                    if not detected_tool:
                        try:
                            if os.path.exists(original_path_abs):
                                if method == "Social Media Correlation":
                                    detected_tool = self._detect_social_media_correlation_tool_from_structure(original_path_abs)
                                elif method == "Contact Correlation":
                                    detected_tool = self._detect_contact_correlation_tool_from_structure(original_path_abs)
                                elif method == "Deep Communication Analytics":
                                    detected_tool = self._detect_deep_communication_analytics_tool_from_structure(original_path_abs)
                                else:
                                    detected_tool = self._detect_tool_from_sheets(original_path_abs, method)
                        except:
                            pass
                    
                    if not detected_tool:
                        try:
                            if method == "Social Media Correlation":
                                detected_tool = self._detect_social_media_correlation_tool_from_structure(original_path_abs)
                            elif method == "Contact Correlation":
                                detected_tool = self._detect_contact_correlation_tool_from_structure(original_path_abs)
                            elif method == "Deep Communication Analytics":
                                detected_tool = self._detect_deep_communication_analytics_tool_from_structure(original_path_abs)
                            else:
                                detected_tool = self._detect_tool_from_sheets(original_path_abs, method)
                        except:
                            pass
                    
                    if not detected_tool or detected_tool == "Unknown":
                        detected_tool = self._normalize_tool_name(tools) or tools or "Unknown"

                    error_msg = f"Upload hash data not found in file with {method or 'Hashfile Analytics'} method and {detected_tool} tools."
                    print(f"[ERROR] No data inserted. No parsing error but also no data found.")
                
                self._cleanup_failed_upload(file_id=file_id, file_path=rel_path)
                
                if not detected_tool or detected_tool == "Unknown":
                    detected_tool = self._normalize_tool_name(tools) or tools or "Unknown"
                
                detected_method_from_error = None
                detected_tool_from_error = None
                if " with " in error_msg and " method" in error_msg and " and " in error_msg and " tools." in error_msg:
                    try:
                        method_part = error_msg.split(" with ")[1].split(" method")[0].strip()
                        tool_part = error_msg.split(" and ")[-1].replace(" tools.", "").strip()
                        if method_part:
                            detected_method_from_error = method_part
                        if tool_part and tool_part != "Unknown":
                            detected_tool_from_error = tool_part
                        print(f"[ERROR HANDLING] Extracted from error_msg - method: {detected_method_from_error}, tool: {detected_tool_from_error}")
                    except Exception as e:
                        print(f"[ERROR HANDLING] Error extracting method/tool from error_msg: {e}")
                
                is_no_data_error = (
                    "Contact Correlation data not found in file. The file format is correct" in error_msg or
                    "Social Media Correlation data not found in file. The file format is correct" in error_msg or
                    "Deep Communication Analytics data not found in file. The file format is correct" in error_msg
                )
                
                if is_no_data_error:
                    print(f"[ERROR HANDLING] Tools and method are correct, but no data found in file")
                    final_error_msg = error_msg
                    final_method = method or detected_method_from_error or "Hashfile Analytics"
                    detected_tool = self._normalize_tool_name(tools) or tools or detected_tool_from_error or "Unknown"
                elif detected_method_from_error and detected_tool_from_error and detected_tool_from_error != "Unknown":
                    print(f"[ERROR HANDLING] Using detected values from error_msg: method={detected_method_from_error}, tool={detected_tool_from_error}")
                    final_error_msg = error_msg
                    final_method = detected_method_from_error
                    detected_tool = detected_tool_from_error
                else:
                    final_method = detected_method_from_error if detected_method_from_error else (method or "Hashfile Analytics")
                    
                    if method != "Hashfile Analytics" and ("Upload hash data not found" in error_msg or "not found" in error_msg.lower()):
                        try:
                            if os.path.exists(original_path_abs):
                                print(f"[ERROR HANDLING] Final check: Re-detecting hashfile for method '{method}'...")
                                hashfile_tool_final = self._detect_hashfile_tool_from_structure(original_path_abs)
                                if hashfile_tool_final and hashfile_tool_final != "Unknown":
                                    print(f"[ERROR HANDLING] ✓ Final re-detection successful: {hashfile_tool_final}")
                                    detected_tool = hashfile_tool_final
                                    final_method = "Hashfile Analytics"
                                    final_error_msg = f"Upload hash data not found in file with Hashfile Analytics method and {hashfile_tool_final} tools."
                                    print(f"[ERROR HANDLING] Final error message: {final_error_msg}")
                                else:
                                    print(f"[ERROR HANDLING] ✗ Final re-detection failed (result: {hashfile_tool_final})")
                                    if "Upload hash data not found" in error_msg or "hash data not found" in error_msg.lower():
                                        final_error_msg = f"Upload hash data not found in file with {final_method} method and {detected_tool} tools."
                                    elif "Contacts and calls data not found" in error_msg:
                                        final_error_msg = f"Contacts and calls data not found in file with {final_method} method and {detected_tool} tools."
                                    elif "not found" in error_msg.lower():
                                        final_error_msg = f"Upload hash data not found in file with {final_method} method and {detected_tool} tools."
                                    else:
                                        final_error_msg = error_msg
                        except Exception as e:
                            print(f"[ERROR HANDLING] Exception during final hashfile re-detection: {e}")
                            traceback.print_exc()
                            if "Upload hash data not found" in error_msg or "hash data not found" in error_msg.lower():
                                final_error_msg = f"Upload hash data not found in file with {final_method} method and {detected_tool} tools."
                            elif "Contacts and calls data not found" in error_msg:
                                final_error_msg = f"Contacts and calls data not found in file with {final_method} method and {detected_tool} tools."
                            elif "not found" in error_msg.lower():
                                final_error_msg = f"Upload hash data not found in file with {final_method} method and {detected_tool} tools."
                            else:
                                final_error_msg = error_msg
                    else:
                        if "Upload hash data not found" in error_msg or "hash data not found" in error_msg.lower():
                            final_error_msg = f"Upload hash data not found in file with {final_method} method and {detected_tool} tools."
                        elif "Contacts and calls data not found" in error_msg:
                            final_error_msg = f"Contacts and calls data not found in file with {final_method} method and {detected_tool} tools."
                        elif "not found" in error_msg.lower():
                            final_error_msg = f"Upload hash data not found in file with {final_method} method and {detected_tool} tools."
                        else:
                            final_error_msg = error_msg
                
                self._mark_done(upload_id, final_error_msg, is_error=True, detected_tool=detected_tool, method=final_method, tools=tools, detected_method=final_method)
                return {"status": 400, "message": final_error_msg, "data": None, "detected_tool": detected_tool}
            
            setattr(file_record, 'amount_of_data', actual_amount_of_data)
            db.commit()
            
            print(f"Updated amount_of_data to {actual_amount_of_data} (Social Media: {actual_social_media_count}, Contacts: {actual_contacts_count}, Calls: {actual_calls_count}, Hash Files: {actual_hashfiles_count}, Chat Messages: {actual_chat_messages_count})")
            
            amount_of_data_count = (
                parsing_result.get("contacts_count", 0) +
                parsing_result.get("messages_count", 0) +
                parsing_result.get("calls_count", 0) +
                parsing_result.get("hashfiles_count", 0) +
                parsing_result.get("social_media_count", 0) +
                parsing_result.get("chat_messages_count", 0)
            )
            
            if method == "Social Media Correlation":
                cleaned_parsing_result = {
                    "tool_used": parsing_result.get("tool_used"),
                    "social_media_count": actual_social_media_count,
                    "parsing_success": parsing_result.get("parsing_success", True),
                    "amount_of_data_count": actual_social_media_count
                }
                if "social_media_error" in parsing_result:
                    cleaned_parsing_result["parsing_error"] = parsing_result["social_media_error"]
            elif method == "Contact Correlation":
                cleaned_parsing_result = {
                    "tool_used": parsing_result.get("tool_used"),
                    "contacts_count": actual_contacts_count,
                    "calls_count": actual_calls_count,
                    "parsing_success": parsing_result.get("parsing_success", True),
                    "amount_of_data_count": actual_contacts_count + actual_calls_count
                }
                if "contacts_calls_error" in parsing_result:
                    cleaned_parsing_result["parsing_error"] = parsing_result["contacts_calls_error"]
            elif method == "Hashfile Analytics":
                cleaned_parsing_result = {
                    "tool_used": parsing_result.get("tool_used"),
                    "hashfiles_count": actual_hashfiles_count,
                    "parsing_success": parsing_result.get("parsing_success", True),
                    "amount_of_data_count": actual_hashfiles_count
                }
                if "hashfiles_error" in parsing_result:
                    cleaned_parsing_result["parsing_error"] = parsing_result["hashfiles_error"]
            elif method == "Deep Communication Analytics":
                cleaned_parsing_result = {
                    "tool_used": parsing_result.get("tool_used"),
                    "chat_messages_count": actual_chat_messages_count,
                    "parsing_success": parsing_result.get("parsing_success", True),
                    "amount_of_data_count": actual_chat_messages_count
                }
                if "chat_messages_error" in parsing_result:
                    cleaned_parsing_result["parsing_error"] = parsing_result["chat_messages_error"]
            else:
                cleaned_parsing_result = parsing_result.copy()
                cleaned_parsing_result["amount_of_data_count"] = amount_of_data_count
            
            parsing_result = cleaned_parsing_result

            self._progress[upload_id].update({
                "percent": 100,
                "progress_size": format_bytes(total_size),
                "message": "Upload, parsing & database insertion complete",
                "done": True,
                "file_id": file_record.id,
            })

            total_records = (
                parsing_result.get("contacts_count", 0) +
                parsing_result.get("messages_count", 0) +
                parsing_result.get("calls_count", 0) +
                parsing_result.get("hashfiles_count", 0) +
                parsing_result.get("social_media_count", 0) +
                parsing_result.get("chat_messages_count", 0)
            )
            
            if total_records > 5000:
                response_data = performance_optimizer.create_summary_response(
                    total_records=total_records,
                    file_size=total_size,
                    processing_time=time.time() - start_time
                )
                response_data["data"].update({
                    "file_id": file_record.id,
                    "upload_id": upload_id,
                    "percentage": 100,
                    "progress_size": format_bytes(total_size),
                    "total_size": format_bytes(total_size),
                    "done": True,
                    "file_path": rel_path,
                    "parsing_result": parsing_result
                })
            else:
                response_data = {
                    "status": 200,
                    "message": "File uploaded, encrypted & parsed successfully",
                    "data": {
                        "file_id": file_record.id,
                        "upload_id": upload_id,
                        "percentage": 100,
                        "progress_size": format_bytes(total_size),
                        "total_size": format_bytes(total_size),
                        "done": True,
                        "file_path": rel_path,
                        "parsing_result": parsing_result
                    },
                }
            return response_data

        except Exception as e:
            if file_record_inserted and file_id:
                self._cleanup_failed_upload(file_id=file_id, file_path=rel_path)
            self._mark_done(upload_id, f"Upload error: {str(e)}", is_error=True)
            return {"status": 500, "message": f"Unexpected upload error: {str(e)}", "data": None}

    async def start_device_processing(
        self,
        upload_id: str,
        file_id: int,
        owner_name: str,
        phone_number: str,
        tools: str,
        device_id: int | None = None
    ) -> Dict[str, Any]:
        try:
            db = next(get_db())
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return {"status": 404, "message": "File not found", "data": None}
            
            self._init_state(upload_id)
            self._progress[upload_id].update({
                "message": f"Processing with {tools} parser...",
                "percent": 10
            })
            
            file_path = Path(file_record.file_path)
            if not file_path.exists():
                return {"status": 404, "message": "File not found on disk", "data": None}
            
            self._progress[upload_id].update({
                "message": f"Parsing {tools} format...",
                "percent": 30
            })
            
            parsed_data = tools_parser.parse_file(file_path, tools)
            
            if "error" in parsed_data:
                self._progress[upload_id].update({
                    "message": f"Parser error: {parsed_data['error']}",
                    "percent": 50
                })

                parsed_data = parsed_data.get("fallback", {})
            
            self._progress[upload_id].update({
                "message": "Creating device record...",
                "percent": 70
            })
            
            if device_id:
                device_data = {
                    "owner_name": owner_name,
                    "phone_number": phone_number,
                    "file_id": file_id
                }
                
                file_id_from_data = device_data.get("file_id")
                if file_id_from_data is None:
                    return {"status": 400, "message": "file_id is required", "data": None}
                
                device = Device(
                    owner_name=device_data.get("owner_name"),
                    phone_number=device_data.get("phone_number"),
                    file_id=int(file_id_from_data),
                    created_at=get_indonesia_time(),
                )
                
                sm_db.add(device)
                sm_db.commit()
                sm_db.refresh(device)
                device_id = device.id
                
                print(f"Created device ID {device_id} in same session as parser")
            else:
                device_data = {
                    "owner_name": owner_name,
                    "phone_number": phone_number,
                    "file_id": file_id
                }
                
                device_id = create_device(
                    device_data=device_data,
                    contacts=parsed_data.get("contacts", []),
                    messages=parsed_data.get("messages", []),
                    calls=parsed_data.get("calls", [])
                )
            
            self._progress[upload_id].update({
                "message": "Device processing complete",
                "percent": 100,
                "done": True,
                "device_id": device_id,
                "parsed_data": {
                    "tool": parsed_data.get("tool", "Forensic Tool"),
                    "contacts_count": len(parsed_data.get("contacts", [])),
                    "messages_count": len(parsed_data.get("messages", [])),
                    "calls_count": len(parsed_data.get("calls", []))
                }
            })
            
            return {
                "status": 200,
                "message": "Device processing completed successfully",
                "data": {
                    "device_id": device_id,
                    "tool_used": parsed_data.get("tool", "Forensic Tool"),
                    "parsed_data": {
                        "contacts_count": len(parsed_data.get("contacts", [])),
                        "messages_count": len(parsed_data.get("messages", [])),
                        "calls_count": len(parsed_data.get("calls", []))
                    }
                }
            }
            
        except Exception as e:
            self._mark_done(upload_id, f"Device processing error: {str(e)}", is_error=True)
            return {"status": 500, "message": f"Device processing error: {str(e)}", "data": None}

    async def start_upload_and_process(
        self,
        file_id: int,
        owner_name: str,
        phone_number: str,
        device_id: int | None = None
    ) -> Dict[str, Any]:
        try:
            db = next(get_db())
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return {"status": 404, "message": "File not found", "data": None}
            
            upload_id = f"process_{file_id}_{int(time.time())}"
            
            return await self.start_device_processing(
                upload_id=upload_id,
                file_id=file_id,
                owner_name=owner_name,
                phone_number=phone_number,
                tools=file_record.tools,
                device_id=device_id
            )
            
        except Exception as e:
            return {"status": 500, "message": f"Processing error: {str(e)}", "data": None}

    async def start_app_upload(self, upload_id: str, file: UploadFile, file_name: str, file_bytes: bytes):
        try:
            APK_DIR = os.path.join(APK_DIR_BASE, "apk")
            os.makedirs(APK_DIR, exist_ok=True)
            print(f"[DEBUG] APK_DIR ready: {APK_DIR}")

            safe_filename = Path(file.filename).name
            target_path = os.path.join(APK_DIR, safe_filename)
            total_size = len(file_bytes)
            print(f"[DEBUG] Start writing file: {target_path} ({format_bytes(total_size)})")

            self._init_state(upload_id)

            chunk_size = 1024 * 512
            written = 0
            with open(target_path, "wb") as f:
                for i in range(0, total_size, chunk_size):
                    chunk = file_bytes[i:i + chunk_size]
                    f.write(chunk)
                    written += len(chunk)
                    percent = (written / total_size) * 100
                    self._progress[upload_id].update({
                        "percent": round(percent, 2),
                        "progress_size": format_bytes(written),
                        "message": f"Uploading app... ({percent:.2f}%)",
                    })
                    await asyncio.sleep(0.02)
            print(f"[DEBUG] File write completed ({written} bytes)")
            
            rel_path = os.path.relpath(target_path, BASE_DIR)
            print(f"[DEBUG] Relative path for DB: {rel_path}")

            db = next(get_db())
            print("[DEBUG] Database session started")

            file_record = File(
                file_name=file_name,
                file_path=rel_path,
                notes=None,
                type="Handphone",
                tools=None,
                total_size=total_size,
                method="APK Analytics",
            )

            db.add(file_record)
            print("[DEBUG] File record added to DB session")

            db.commit()
            print("[DEBUG] DB commit successful")

            db.refresh(file_record)
            print(f"[DEBUG] File record refreshed (ID: {file_record.id})")

            self._progress[upload_id].update({
                "percent": 100,
                "progress_size": format_bytes(total_size),
                "message": "App upload complete",
                "done": True,
                "file_id": file_record.id,
            })

            print(f"[DEBUG] Upload process complete for {file_name} (upload_id={upload_id})")

            return {
                "status": 200,
                "message": "Application uploaded successfully",
                "data": {
                    "percent": 100,
                    "progress_size": format_bytes(total_size),
                    "total_size": format_bytes(total_size),
                    "done": True,
                    "file_id": file_record.id,
                    "file_path": rel_path,
                },
            }

        except Exception as e:
            print(f"[ERROR] start_app_upload error: {str(e)}")
            traceback.print_exc()
            self._mark_done(upload_id, f"App upload error: {str(e)}", is_error=True)
            return {"status": 500, "message": f"Unexpected app upload error: {str(e)}", "data": None}

upload_service = UploadService()