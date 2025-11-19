import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.analytics.device_management.models import ChatMessage
from datetime import datetime
import pytz, traceback, logging, re

logger = logging.getLogger(__name__)

class ChatMessagesParserExtended:
    
    def _normalize_direction(self, direction_raw: str) -> str:
        if not direction_raw:
            return ''
        
        direction = str(direction_raw).strip()
        
        if '(not parsed)' in direction.lower():
            return ''
        
        direction_lower = direction.lower()
        if direction_lower == 'sent':
            return 'Outgoing'
        elif direction_lower == 'received':
            return 'Incoming'
        elif direction_lower in ['outgoing', 'incoming']:
            return direction.capitalize()
        
        if direction.isdigit() or re.match(r'^\d+\s*\(', direction):
            return ''
        
        return direction
    
    def __init__(self, db: Session):
        self.db = db
    
    def _is_na(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, (pd.Series, pd.DataFrame)):
            if value.empty:
                return True
            na_result = value.isna().all()
            return bool(na_result) if isinstance(na_result, (pd.Series, pd.DataFrame)) else bool(na_result)
        try:
            na_result = pd.isna(value)
            if isinstance(na_result, (pd.Series, pd.DataFrame)):
                return bool(na_result.all())
            return bool(na_result)
        except (TypeError, ValueError):
            return False
    
    def _not_na(self, value: Any) -> bool:
        return not self._is_na(value)

    def _normalize_platform_name(self, platform: str) -> str:
        if not platform:
            return platform
        
        platform_lower = platform.lower().strip()
        platform_map = {
            'whatsapp': 'WhatsApp',
            'telegram': 'Telegram',
            'instagram': 'Instagram',
            'facebook': 'Facebook',
            'tiktok': 'TikTok',
            'x': 'X',
            'twitter': 'X'
        }
        
        return platform_map.get(platform_lower, platform)
    
    def _is_whatsapp_system_message(self, message_text: str, sender_id: str = None, sender_name: str = None) -> bool:
        if not message_text:
            return False
        
        message_lower = message_text.lower()
        
        if sender_id:
            sender_id_clean = str(sender_id).strip().lower()
            if sender_id_clean == '0' or sender_id_clean == '0@s.whatsapp.net':
                if message_text.strip().startswith('*') or any(keyword in message_lower for keyword in [
                    'whatsapp can see', 'end-to-end', 'protecting your privacy', 'new:', 
                    'add more memories', 'status photo', 'tap the sticker'
                ]):
                    return True
        
        if message_text.strip().startswith('*'):
            promotional_keywords = [
                'not even whatsapp can see',
                'your personal messages',
                'protected with end-to-end',
                'protecting your privacy',
                'new:',
                'add more memories',
                'status photo stickers',
                'tap the sticker button',
                'when creating a status',
                'you never need to choose',
                'share all your favorite photos',
                'whatsapp update',
                'new feature',
                'try the new',
                'check out our'
            ]
            
            if any(keyword in message_lower for keyword in promotional_keywords):
                return True
        
        if any(pattern in message_lower for pattern in [
            'end-to-end encryption',
            'always committed to protecting',
            'share all your favorite photos to your status',
            'select photo when creating a status'
        ]):
            return True
        
        return False

    def parse_cellebrite_chat_messages(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.info(f"[CELLEBRITE CHAT PARSER] Starting to parse chat messages from file_id={file_id}, file_path={file_path}")
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            logger.info(f"[CELLEBRITE CHAT PARSER] Total sheets found: {len(xls.sheet_names)}")
            logger.info(f"[CELLEBRITE CHAT PARSER] Available sheets: {', '.join(xls.sheet_names[:10])}...")
            
            if 'Chats' in xls.sheet_names:
                logger.info(f"[CELLEBRITE CHAT PARSER] Found 'Chats' sheet, parsing...")
                chats_results = self._parse_cellebrite_chats_messages(file_path, 'Chats', file_id)
                results.extend(chats_results)
                logger.info(f"[CELLEBRITE CHAT PARSER] Chats sheet: Parsed {len(chats_results)} messages")
            else:
                logger.warning(f"[CELLEBRITE CHAT PARSER] 'Chats' sheet not found")
            
            logger.info(f"[CELLEBRITE CHAT PARSER] Total parsed messages: {len(results)}")
            
            if results:
                sample_msg = results[0]
                logger.debug(f"[CELLEBRITE CHAT PARSER] Sample message data: platform={sample_msg.get('platform')}, "
                            f"direction={sample_msg.get('direction')}, "
                            f"from={sample_msg.get('sender')}, "
                            f"to={sample_msg.get('receiver')}, "
                            f"timestamp={sample_msg.get('timestamp')}")
            
            saved_count = 0
            skipped_count = 0

            for msg in results:
                chat_message_data = {
                    "file_id": msg.get("file_id"),
                    "platform": msg.get("platform", "Unknown"),
                    "message_text": msg.get("message_text"),
                    "account_name": msg.get("account_name"),
                    "group_name": msg.get("group_name"),
                    "group_id": msg.get("group_id"),
                    "from_name": (msg.get("sender") or "").strip() or "Unknown",
                    "sender_number": (msg.get("sender_number") or "").strip() or None,
                    "to_name": (msg.get("receiver") or "").strip() or "Unknown",
                    "recipient_number": (msg.get("recipient_number") or "").strip() or None,
                    "timestamp": msg.get("timestamp"),
                    "thread_id": msg.get("thread_id"),
                    "chat_id": msg.get("chat_id") or msg.get("thread_id"),
                    "message_id": msg.get("message_id") or msg.get("thread_id"),
                    "message_type": msg.get("type", "Unknown"),
                    "chat_type": msg.get("chat_type"),
                    "status": msg.get("status"),
                    "direction": msg.get("direction"),
                    "source_tool": "Cellebrite",
                    "sheet_name": "Chats",
                }

                existing = (
                    self.db.query(ChatMessage)
                    .filter(
                        ChatMessage.file_id == chat_message_data["file_id"],
                        ChatMessage.platform == chat_message_data["platform"],
                        ChatMessage.message_id == chat_message_data["message_id"]
                    )
                    .first()
                )

                if not existing:
                    self.db.add(ChatMessage(**chat_message_data))
                    saved_count += 1
                else:
                    skipped_count += 1

            self.db.commit()
            logger.info(f"[CELLEBRITE CHAT PARSER] Saved {saved_count} messages (skipped {skipped_count} duplicates)")
            print(f"Saved {saved_count} Cellebrite chat messages (skipped {skipped_count} duplicates)")

        except Exception as e:
            logger.error(f"[CELLEBRITE CHAT PARSER] Error parsing Cellebrite chat messages: {e}", exc_info=True)
            print(f"Error parsing Cellebrite chat messages: {e}")
            self.db.rollback()
            raise e

        return results

    def _parse_cellebrite_chats_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        try:
            logger.debug(f"[CELLEBRITE CHATS PARSER] === Start parsing sheet '{sheet_name}' for file_id={file_id} ===")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl", dtype=str, header=1)
            df = df.fillna("")
            logger.debug(f"[CELLEBRITE CHATS PARSER] Loaded {len(df)} rows, columns: {list(df.columns)[:15]}")

            processed_count = 0
            skipped_count = 0
            skip_reasons = {
                "not_one_on_one": 0,
                "no_timestamp": 0,
                "no_sender_or_text": 0,
                "no_source_type": 0,
                "header_row": 0,
                "unsupported_platform": 0,
                "duplicate_system_message": 0,
            }

            allowed_platforms = ["whatsapp", "telegram", "instagram", "facebook", "tiktok", "x", "twitter", "x (twitter)"]
            for idx, row in df.iterrows():
                try:
                    first_col = self._clean(row.get(df.columns[0], "")) or ""
                    if first_col.lower() in ["#", "identifier", "record", "chat #", "name", "platform"]:
                        skip_reasons["header_row"] += 1
                        continue

                    participants_raw = str(row.get("Participants") or "")
                    participants_raw = re.sub(r"_x0{0,2}(0d|0a)_", "\n", participants_raw, flags=re.IGNORECASE)
                    participants_raw = participants_raw.replace("\r", "\n").replace("\xa0", " ")
                    participants_lines = [self._clean(p) for p in participants_raw.split("\n") if p and p.strip()]

                    owner_full, non_owner_full = None, None
                    for p in participants_lines:
                        if "(owner)" in (p or "").lower():
                            owner_full = p.replace("(owner)", "").strip()
                        else:
                            non_owner_full = p.strip()

                    if not owner_full and participants_lines:
                        owner_full = participants_lines[0]
                    if not non_owner_full and len(participants_lines) > 1:
                        non_owner_full = participants_lines[1]
                    if not non_owner_full:
                        non_owner_full = "Unknown"
                    
                    source = self._clean(row.get("Source"))
                    platform = self._clean(row.get("Platform"))
                    platform_lower = f"{source} {platform}".lower() if source and platform else ""
                    is_twitter = "x" in platform_lower or "twitter" in platform_lower
                    

                    group_name_value = self._clean(row.get("Name")) or self._clean(row.get("name"))
                    
                    from_field = (row.get("From") or "").strip()
                    
                    if from_field:
                        from_field_lower = from_field.lower().strip()
                        if "system message" in from_field_lower and from_field_lower.count("system message") > 1:
                            skip_reasons["duplicate_system_message"] += 1
                            skipped_count += 1
                            continue
                    
                    sender = from_field or owner_full or "Unknown"

                    if "system message" in from_field.lower():
                        direction = "Incoming"
                        sender = "System Message"
                        receiver = owner_full or "Unknown"
                        sender_number = None
                        from_name = "System Message"
                    else:
                        direction = "Incoming"
                        if owner_full and from_field:
                            if owner_full.split(" ")[0] in from_field or owner_full.lower() in from_field.lower():
                                direction = "Outgoing"
                            else:
                                direction = "Incoming"

                    receiver = non_owner_full if direction == "Outgoing" else owner_full

                    timestamp_clean = self._parse_timestamp(row.get("Timestamp: Time"))
                    if not timestamp_clean:
                        skip_reasons["no_timestamp"] += 1
                        skipped_count += 1
                        continue

                    if not source or not platform:
                        source = self._clean(row.get("Source"))
                        platform = self._clean(row.get("Platform"))
                        if not source or not platform:
                            skip_reasons["no_source_type"] += 1
                            skipped_count += 1
                            continue

                    platform_text = f"{source} {platform}".lower()
                    if not any(p in platform_text for p in allowed_platforms):
                        skip_reasons["unsupported_platform"] += 1
                        skipped_count += 1
                        continue
    
                    is_twitter = "x" in platform_text or "twitter" in platform_text

                    chat_type_raw = self._clean(row.get("Chat Type")) or self._clean(row.get("chat type")) or self._clean(row.get("Chat type"))
                    chat_type = None

                    status_value = self._clean(row.get("Status")) or self._clean(row.get("status"))
                    
                    if chat_type_raw:
                        chat_type_normalized = chat_type_raw.lower().strip().replace("-", " ").replace("_", " ")
                        if "one on one" in chat_type_normalized:
                            chat_type = "One On One"
                        elif "group" in chat_type_normalized:
                            chat_type = "Group"
                        elif "broadcast" in chat_type_normalized:
                            chat_type = "Broadcast"
                        else:
                            chat_type = chat_type_raw

                    platform_lower = (source or "").lower()
                    is_twitter = "x" in platform_lower or "twitter" in platform_lower
                    is_instagram = "instagram" in platform_lower
                    
                    if is_twitter:
                        username_part, name_part = self._split_twitter_username_name(from_field)
                        if username_part and name_part:
                            sender_number = username_part
                            from_name = self._safe_clean_name(name_part)
                        else:
                            id_part, name_part = self._split_twitter_id_name(from_field)
                            sender_number = id_part
                            from_name = self._safe_clean_name(name_part) if name_part else "Unknown"
                        
                        username_part, name_part = self._split_twitter_username_name(receiver)
                        if username_part and name_part:
                            recipient_number = username_part
                            to_name = self._safe_clean_name(name_part)
                        else:
                            id_part, name_part = self._split_twitter_id_name(receiver)
                            if id_part and name_part:
                                recipient_number = id_part
                                to_name = self._safe_clean_name(name_part)
                            else:
                                to_name = self._safe_clean_name(receiver)
                                recipient_number = None
                    elif is_instagram:
                        sender_number, from_name = self._split_twitter_username_name(from_field)
                        from_name = self._safe_clean_name(from_name)

                        username_part, name_part = self._split_twitter_username_name(receiver)
                        if username_part and name_part:
                            to_name = self._safe_clean_name(name_part)
                            recipient_number = username_part
                        else:
                            to_name = self._safe_clean_name(receiver)
                            recipient_number = None
                    else:
                        sender_number, from_name = self._split_name_number(from_field)
                        from_name = self._safe_clean_name(from_name)

                        recipient_number, to_name = self._split_name_number(receiver)
                        to_name = self._safe_clean_name(to_name)

                    body = self._clean(row.get("Body"))
                    if not sender or not body:
                        skip_reasons["no_sender_or_text"] += 1
                        skipped_count += 1
                        continue

                    thread_id = self._clean(row.get("Identifier"))

                    chat_id_value = None
                    for col_name in ["Chat #", "chat #", "Chat#", "chat#"]:
                        if col_name in row.index:
                            chat_id_value = self._clean(row.get(col_name))
                            if chat_id_value:
                                break
                    
                    instant_message_id = None
                    for col_name in ["Instant Message #", "instant message #", "Instant Message#", "instant message#"]:
                        if col_name in row.index:
                            instant_message_id = self._clean(row.get(col_name))
                            if instant_message_id:
                                break
                    
                    group_id_value = None
                    if chat_type and chat_type.lower() in ["group", "broadcast"]:
                        group_id_value = self._clean(row.get("Identifier"))

                    account_name = self._clean(row.get("Account")) or self._clean(row.get("account"))

                    entry = {
                        "file_id": file_id,
                        "direction": direction,
                        "platform": source,
                        "type": platform,
                        "timestamp": timestamp_clean,
                        "message_text": body,
                        "sender": from_name or "Unknown",
                        "receiver": to_name or "Unknown",
                        "sender_number": sender_number,
                        "recipient_number": recipient_number,
                        "details": None,
                        "thread_id": thread_id,
                        "chat_id": chat_id_value if chat_id_value else thread_id,
                        "message_id": instant_message_id if instant_message_id else None,
                        "chat_type": chat_type,
                        "status": status_value,
                        "account_name": account_name,
                        "group_name": group_name_value,
                        "group_id": group_id_value,
                    }

                    results.append(entry)
                    processed_count += 1

                    if processed_count <= 3:
                        logger.debug(f"[ROW {idx}] {direction} | {from_name} ({sender_number}) → {to_name} ({recipient_number}) | {body[:60]}...")

                except Exception as e:
                    skipped_count += 1
                    logger.warning(f"[ROW {idx}] Error parsing row: {e}", exc_info=False)

            logger.info(
                f"[CELLEBRITE CHATS PARSER] Processed {processed_count} valid rows, "
                f"Skipped {skipped_count}, Reasons: {skip_reasons}"
            )

        except Exception as e:
            logger.error(f"[CELLEBRITE CHATS PARSER] Error parsing Cellebrite chats ({sheet_name}): {e}", exc_info=True)

        return results

    def _safe_clean_name(self, text: Optional[str]) -> str:
        if not text:
            return "Unknown"

        cleaned = str(text)
        cleaned = re.sub(r'[\u200b\u200c\u200d\ufeff\xa0]', '', cleaned)
        cleaned = cleaned.strip()

        return cleaned if cleaned else "Unknown"

    def _split_name_number(self, raw_value: str) -> Tuple[Optional[str], str]:
        if not raw_value or not str(raw_value).strip():
            return None, "Unknown"

        val = str(raw_value).strip()

        val = re.sub(r'[\u200b\u200c\u200d\ufeff\xa0]', '', val)
        val = self._clean_whatsapp_format(val) or ""
        val = val.strip()

        parts = val.split(" ", 1)

        if len(parts) == 2:
            number_candidate, name_part = parts[0].strip(), parts[1].strip()
            number_candidate = self._clean_whatsapp_format(number_candidate) or number_candidate

            if re.match(r'^\+?\d+$', number_candidate):
                return number_candidate, self._safe_clean_name(name_part)
            else:
                sub_parts = val.split(" ")
                if len(sub_parts) >= 2:
                    possible_username = sub_parts[0].strip()
                    return None, self._safe_clean_name(possible_username)

        return None, self._safe_clean_name(val)

    def _split_twitter_id_name(self, raw_value: str) -> Tuple[Optional[str], str]:
        if not raw_value or not str(raw_value).strip():
            return None, "Unknown"
        
        val = str(raw_value).strip()
        val = re.sub(r'[\u200b\u200c\u200d\ufeff\xa0]', '', val)
        val = val.strip()
        
        parts = val.split(" ", 1)
        
        if len(parts) == 2:
            id_candidate = parts[0].strip()
            name = parts[1].strip()
            
            if id_candidate and name and re.match(r'^\d{10,}$', id_candidate):
                return id_candidate, name
        
        return None, val

    def _split_twitter_username_name(self, raw_value: str) -> Tuple[Optional[str], str]:
        if not raw_value or not str(raw_value).strip():
            return None, "Unknown"
        
        val = str(raw_value).strip()
        val = re.sub(r'[\u200b\u200c\u200d\ufeff\xa0]', '', val)
        val = val.strip()
        
        parts = val.split(" ", 1)
        
        if len(parts) == 2:
            username = parts[0].strip()
            name = parts[1].strip()
            
            if username and name:
                return username, name
        
        return None, val

    def _clean_whatsapp_format(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        
        text = str(value).strip()
        text = re.sub(r'@s\.whatsapp\.net', '', text, flags=re.IGNORECASE)
        text = re.sub(r'@[\w\.-]+', '', text)
        text = text.strip()
        
        return text if text else None

    def _clean(self, value: Any) -> Optional[str]:
        if value is None or self._is_na(value):
            return None
        
        text_str = str(value).strip()
        if text_str.lower() in ["", "nan", "none", "null", "n/a"]:
            return None

        text = str(value)
        text = re.sub(r"_x0{0,2}(0d|0a)_", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"[\x00-\x1F]+", " ", text)
        text = "".join(ch for ch in text if ch.isprintable())
        text = re.sub(r"\s+", " ", text).strip()
        
        text = self._clean_whatsapp_format(text)
        
        return text or None

    def _extract_name(self, text: str) -> Optional[str]:
        if not text or str(text).strip().lower() in ["", "nan", "none"]:
            return None
        cleaned = re.sub(r"\(owner\)", "", text)
        cleaned = re.sub(r"^\+?\d+\s*", "", cleaned).strip()
        cleaned = self._clean(cleaned)
        return cleaned or None

    def _parse_timestamp(self, raw: str) -> Optional[str]:
        if not raw:
            return None
        try:
            base = re.sub(r"\(UTC[+-]\d+\)", "", raw).strip()
            dt = datetime.strptime(base, "%d/%m/%Y %H:%M:%S")
            tz = pytz.timezone("Asia/Jakarta")
            localized = tz.localize(dt)
            return localized.isoformat()
        except Exception:
            return None

    def parse_oxygen_chat_messages(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.info(f"[OXYGEN CHAT PARSER] Starting to parse chat messages from file_id={file_id}, file_path={file_path}")
            print(f"[OXYGEN CHAT PARSER] Starting to parse chat messages from file_id={file_id}, file_path={file_path}")
            
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()
            if file_extension == '.xls':
                engine = "xlrd"
            else:
                engine = "openpyxl"
            
            logger.info(f"[OXYGEN CHAT PARSER] Using engine: {engine} for file extension: {file_extension}")
            print(f"[OXYGEN CHAT PARSER] Using engine: {engine} for file extension: {file_extension}")
            
            xls = pd.ExcelFile(file_path, engine=engine)
            logger.info(f"[OXYGEN CHAT PARSER] Total sheets found: {len(xls.sheet_names)}")
            print(f"[OXYGEN CHAT PARSER] Total sheets found: {len(xls.sheet_names)}")
            logger.info(f"[OXYGEN CHAT PARSER] Available sheets: {', '.join(xls.sheet_names[:10])}...")
            print(f"[OXYGEN CHAT PARSER] Available sheets: {', '.join(xls.sheet_names[:15])}...")
            
            messages_sheet = None
            logger.info(f"[OXYGEN CHAT PARSER] Searching for Messages sheet in {len(xls.sheet_names)} sheets")
            print(f"[OXYGEN CHAT PARSER] Searching for Messages sheet...")
            
            for sheet in xls.sheet_names:
                sheet_clean = str(sheet).strip().lower()
                logger.debug(f"[OXYGEN CHAT PARSER] Checking sheet: '{sheet}' -> cleaned: '{sheet_clean}'")
                
                if sheet_clean == 'messages' or sheet_clean == 'message':
                    messages_sheet = sheet
                    logger.info(f"[OXYGEN CHAT PARSER] Found Messages sheet: '{sheet}' (with exact match)")
                    print(f"[OXYGEN CHAT PARSER] Found Messages sheet: '{sheet}'")
                    break
            
            if not messages_sheet:
                for sheet in xls.sheet_names:
                    sheet_clean = str(sheet).strip().lower()
                    if sheet_clean in ['messages', 'message']:
                        messages_sheet = sheet
                        logger.info(f"[OXYGEN CHAT PARSER] Found Messages sheet (strip match): '{sheet}'")
                        print(f"[OXYGEN CHAT PARSER] Found Messages sheet: '{sheet}'")
                        break
            
            if not messages_sheet:
                for sheet in xls.sheet_names:
                    sheet_lower = str(sheet).lower()
                    if sheet_lower.startswith('message') and 'sheet' not in sheet_lower:
                        messages_sheet = sheet
                        logger.info(f"[OXYGEN CHAT PARSER] Found Messages sheet (prefix match): '{sheet}'")
                        print(f"[OXYGEN CHAT PARSER] Found Messages sheet: '{sheet}'")
                        break
            
            if not messages_sheet:
                print(f"[OXYGEN CHAT PARSER] DEBUG: All sheet names (detailed):")
                for idx, sheet in enumerate(xls.sheet_names):
                    sheet_repr = repr(sheet)
                    sheet_clean = str(sheet).strip().lower()
                    print(f"  [{idx}] Original: {sheet_repr} | Cleaned: '{sheet_clean}' | Length: {len(str(sheet))}")
                    logger.debug(f"Sheet {idx}: {sheet_repr} -> cleaned: '{sheet_clean}'")
                
                print(f"[OXYGEN CHAT PARSER] Searching for sheets containing 'message' (case-insensitive):")
                message_related_sheets = [s for s in xls.sheet_names if 'message' in str(s).lower()]
                for sheet in message_related_sheets:
                    print(f"  - '{sheet}' (repr: {repr(sheet)})")
                    logger.info(f"Found message-related sheet: '{sheet}' (repr: {repr(sheet)})")
                
                if message_related_sheets:
                    potential_sheet = message_related_sheets[0]
                    print(f"[OXYGEN CHAT PARSER] WARNING: No exact 'Messages' sheet found, but found '{potential_sheet}'")
                    print(f"[OXYGEN CHAT PARSER] Checking if '{potential_sheet}' contains multi-platform messages...")
                    logger.warning(f"[OXYGEN CHAT PARSER] No 'Messages' sheet found. Checking '{potential_sheet}' as potential messages sheet")
                    
                    try:
                        test_df = pd.read_excel(file_path, sheet_name=potential_sheet, engine=engine, dtype=str, nrows=5)
                        if len(test_df.columns) > 5:
                            has_source_col = any('source' in str(col).lower() or 'platform' in str(col).lower() for col in test_df.columns[:3])
                            has_text_col = any('text' in str(col).lower() or 'message' in str(col).lower() for col in test_df.columns)
                            
                            if has_source_col or has_text_col:
                                print(f"[OXYGEN CHAT PARSER] '{potential_sheet}' appears to be a multi-platform messages sheet!")
                                print(f"[OXYGEN CHAT PARSER] Using '{potential_sheet}' as Messages sheet")
                                messages_sheet = potential_sheet
                                logger.info(f"[OXYGEN CHAT PARSER] Using '{potential_sheet}' as Messages sheet (detected multi-platform structure)")
                    except Exception as e:
                        logger.debug(f"[OXYGEN CHAT PARSER] Could not test '{potential_sheet}': {e}")
            
            if messages_sheet:
                logger.info(f"[OXYGEN CHAT PARSER] Found '{messages_sheet}' sheet - will parse all platforms from this sheet ONLY")
                print(f"[OXYGEN CHAT PARSER] Found '{messages_sheet}' sheet - will parse all platforms from this sheet ONLY")
                print(f"[OXYGEN CHAT PARSER] Skipping ALL individual platform sheets (Telegram, Instagram, Twitter, WhatsApp, etc.)")
                
                try:
                    messages_results = self._parse_oxygen_messages_sheet(file_path, messages_sheet, file_id, engine)
                    results.extend(messages_results)
                    logger.info(f"[OXYGEN CHAT PARSER] Messages sheet: Parsed {len(messages_results)} messages from all platforms")
                    print(f"[OXYGEN CHAT PARSER] Messages sheet: Parsed {len(messages_results)} messages from all platforms")
                except Exception as e:
                    logger.error(f"[OXYGEN CHAT PARSER] Error parsing Messages sheet: {e}", exc_info=True)
                    print(f"[OXYGEN CHAT PARSER] ERROR parsing Messages sheet: {e}")
                    
                    traceback.print_exc()
            else:
                logger.warning(f"[OXYGEN CHAT PARSER] Messages sheet not found! Will NOT parse from individual platform sheets.")
                print(f"[OXYGEN CHAT PARSER] WARNING: Messages sheet not found!")
                print(f"[OXYGEN CHAT PARSER] Available sheets: {', '.join(xls.sheet_names[:20])}")
                print(f"[OXYGEN CHAT PARSER] Parser only accepts 'Messages' sheet. No data will be parsed.")
                logger.warning(f"[OXYGEN CHAT PARSER] Skipping all individual platform sheets as per requirement - only 'Messages' sheet is allowed.")
            
            logger.info(f"[OXYGEN CHAT PARSER] Total parsed messages: {len(results)}")
            print(f"[OXYGEN CHAT PARSER] Total parsed messages: {len(results)}")
            
            if results:
                sample_msg = results[0]
                logger.info(f"[OXYGEN CHAT PARSER] Sample message data: platform={sample_msg.get('platform')}, "
                           f"sheet_name={sample_msg.get('sheet_name')}, "
                           f"message_id={sample_msg.get('message_id')}, "
                           f"from={sample_msg.get('from_name')}, "
                           f"to={sample_msg.get('to_name')}, "
                           f"timestamp={sample_msg.get('timestamp')}")
                print(f"[OXYGEN CHAT PARSER] Sample message data: platform={sample_msg.get('platform')}, "
                      f"sheet_name={sample_msg.get('sheet_name')}, "
                      f"message_id={sample_msg.get('message_id')}, "
                      f"from={sample_msg.get('from_name')}")
            else:
                logger.warning(f"[OXYGEN CHAT PARSER] No messages found! Check if file contains chat messages.")
                print(f"[OXYGEN CHAT PARSER] WARNING: No messages found! Check if file contains chat messages.")
                print(f"[OXYGEN CHAT PARSER] All available sheets ({len(xls.sheet_names)}): {', '.join(xls.sheet_names[:20])}")
                if len(xls.sheet_names) > 20:
                    print(f"[OXYGEN CHAT PARSER] ... and {len(xls.sheet_names) - 20} more sheets")
                
                potential_sheets = []
                for sheet in xls.sheet_names:
                    sheet_lower = str(sheet).lower()
                    if any(kw in sheet_lower for kw in ['message', 'chat', 'im', 'whatsapp', 'telegram', 'instagram', 'contact']):
                        potential_sheets.append(sheet)
                
                if potential_sheets:
                    print(f"[OXYGEN CHAT PARSER] Potential message-containing sheets: {', '.join(potential_sheets[:10])}")
            
            saved_count = 0
            skipped_count = 0
            for msg in results:
                existing = (
                    self.db.query(ChatMessage)
                    .filter(
                        ChatMessage.file_id == msg["file_id"],
                        ChatMessage.platform == msg["platform"],
                        ChatMessage.message_id == msg["message_id"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(ChatMessage(**msg))
                    saved_count += 1
                else:
                    skipped_count += 1
            
            self.db.commit()
            logger.info(f"[OXYGEN CHAT PARSER] Successfully saved {saved_count} chat messages to database (skipped {skipped_count} duplicates)")
            print(f"[OXYGEN CHAT PARSER] Successfully saved {saved_count} chat messages to database (skipped {skipped_count} duplicates)")
            
            if saved_count == 0 and len(results) > 0:
                logger.warning(f"[OXYGEN CHAT PARSER] All {len(results)} messages were duplicates or failed to save!")
                print(f"[OXYGEN CHAT PARSER] WARNING: All {len(results)} messages were duplicates or failed to save!")
            
        except Exception as e:
            logger.error(f"[OXYGEN CHAT PARSER] Error parsing Oxygen chat messages: {e}", exc_info=True)
            print(f"Error parsing Oxygen chat messages: {e}")
            self.db.rollback()
            raise e
        
        return results

    def _parse_oxygen_messages_sheet(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:  # type: ignore[reportGeneralTypeIssues]
        results = []
        
        try:
            logger.debug(f"[OXYGEN MESSAGES PARSER] Reading sheet: {sheet_name}")
            print(f"[OXYGEN MESSAGES PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN MESSAGES PARSER] Sheet loaded: {len(df)} rows, columns: {list(df.columns)[:15]}")
            print(f"[OXYGEN MESSAGES PARSER] Sheet loaded: {len(df)} rows, {len(df.columns)} columns")
            
            processed_count = 0
            skipped_count = 0
            platform_counts = {}
            
            header_row_idx = None
            for idx in range(min(5, len(df))):
                first_val = str(df.iloc[idx, 0] if len(df.columns) > 0 else '').lower()
                if first_val in ['source', 'service', 'platform', 'application', 'app']:
                    header_row_idx = idx
                    break
            
            if header_row_idx and header_row_idx > 0:
                df.columns = df.iloc[header_row_idx]
                df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
                logger.debug(f"[OXYGEN MESSAGES PARSER] Found header at row {header_row_idx}")
            
            source_col = None
            message_col = None
            timestamp_col = None
            sender_col = None
            receiver_col = None
            thread_id_col = None
            details_col = None
            
            logger.info(f"[OXYGEN MESSAGES PARSER] Available columns: {list(df.columns)}")
            print(f"[OXYGEN MESSAGES PARSER] Available columns ({len(df.columns)}): {list(df.columns)}")
            
            for col_idx, col in enumerate(df.columns):
                col_str = str(col).strip()
                col_lower = col_str.lower()
                
                if col_idx == 0:
                    if len(df) > 0:
                        sample_val = str(df.iloc[0][col]).lower() if self._not_na(df.iloc[0][col]) else ''
                        if any(platform in sample_val for platform in ['whatsapp', 'telegram', 'instagram', 'twitter', 'facebook', 'tiktok', 'x']):
                            source_col = col
                            logger.info(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Source/Platform column")
                            print(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Source/Platform column")
                
                if col_str == 'Source' or col_lower == 'source':
                    source_col = col
                elif not source_col and ('source' in col_lower or 'service' in col_lower or col_lower == 'type'):
                    source_col = col
                
                if col_str == 'Text' or col_lower == 'text':
                    message_col = col
                    logger.info(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Text/Message column (PRIORITY)")
                    print(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Text/Message column (PRIORITY)")
                
                if col_idx == 3 and not message_col:
                    if len(df) > 0:
                        sample = str(df.iloc[0][col]) if self._not_na(df.iloc[0][col]) else ''
                        if len(sample) > 5 and any(c.isalpha() for c in sample[:50]):
                            message_col = col
                            logger.info(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Message column")
                            print(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Message column")
                
                if not message_col:
                    if 'message' in col_lower and 'type' not in col_lower and 'status' not in col_lower:
                        if col_str == 'Message' or col_lower == 'message':
                            message_col = col
                
                if col_idx == 2 and not timestamp_col:
                    sample = str(df.iloc[0][col]) if len(df) > 0 and self._not_na(df.iloc[0][col]) else ''
                    if '/' in sample and ':' in sample:
                        timestamp_col = col
                        logger.info(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Timestamp column")
                        print(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Timestamp column")
                
                if 'timestamp' in col_lower or ('time' in col_lower and 'stamp' in col_lower) or 'date/time' in col_lower:
                    if not timestamp_col:
                        timestamp_col = col
                
                if col_idx in [4, 5]:
                    sample = str(df.iloc[0][col]) if len(df) > 0 and self._not_na(df.iloc[0][col]) else ''
                    if '@' in sample and 's.whatsapp.net' in sample.lower():
                        if col_idx == 4 and not sender_col:
                            sender_col = col
                            logger.info(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Sender/Participant 1")
                            print(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Sender")
                        elif col_idx == 5 and not receiver_col:
                            receiver_col = col
                            logger.info(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Receiver/Participant 2")
                            print(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Receiver")
                
                if 'participant' in col_lower:
                    if '1' in col_lower or not sender_col:
                        sender_col = col
                    elif '2' in col_lower:
                        receiver_col = col
                elif 'sender' in col_lower or 'from' in col_lower:
                    if not sender_col:
                        sender_col = col
                elif 'receiver' in col_lower or 'recipient' in col_lower or 'to' in col_lower:
                    if not receiver_col:
                        receiver_col = col
                
                if col_idx == 7:
                    thread_id_col = col
                    logger.info(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Thread ID column")
                    print(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Thread ID")
                
                if 'thread' in col_lower and 'id' in col_lower:
                    thread_id_col = col
                elif 'message id' in col_lower or 'msg id' in col_lower:
                    thread_id_col = col
                
                if col_str == 'Details' or col_lower == 'details':
                    details_col = col
                    logger.info(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Details column")
                    print(f"[OXYGEN MESSAGES PARSER] Column {col_idx} ('{col}') detected as Details column")
            
            if not source_col and len(df.columns) > 0:
                first_col = df.columns[0]
                if len(df) > 0:
                    sample_val = str(df.iloc[0][first_col]).lower() if self._not_na(df.iloc[0][first_col]) else ''
                    if any(platform in sample_val for platform in ['whatsapp', 'telegram', 'instagram', 'twitter', 'facebook', 'tiktok', 'x']):
                        source_col = first_col
                        logger.info(f"[OXYGEN MESSAGES PARSER] Using first column '{first_col}' as Source/Platform column")
                        print(f"[OXYGEN MESSAGES PARSER] Using first column '{first_col}' as Source/Platform column")
            
            if not message_col:
                for i in [3, 4, 5]:
                    if i < len(df.columns):
                        col = df.columns[i]
                        if len(df) > 0:
                            sample = str(df.iloc[0][col]) if self._not_na(df.iloc[0][col]) else ''
                            if len(sample) > 10 and any(c.isalpha() for c in sample[:50]):
                                message_col = col
                                logger.info(f"[OXYGEN MESSAGES PARSER] Using column {i} '{col}' as Message column")
                                print(f"[OXYGEN MESSAGES PARSER] Using column {i} '{col}' as Message column")
                                break
            
            if not timestamp_col and len(df.columns) > 2:
                col = df.columns[2]
                sample = str(df.iloc[0][col]) if len(df) > 0 and self._not_na(df.iloc[0][col]) else ''
                if '/' in sample and ':' in sample:
                    timestamp_col = col
                    logger.info(f"[OXYGEN MESSAGES PARSER] Using column 2 '{col}' as Timestamp column")
                    print(f"[OXYGEN MESSAGES PARSER] Using column 2 '{col}' as Timestamp column")
            
            logger.info(f"[OXYGEN MESSAGES PARSER] Found columns - Source: {source_col}, Message: {message_col}, Timestamp: {timestamp_col}, Sender: {sender_col}, Receiver: {receiver_col}, ThreadID: {thread_id_col}, Details: {details_col}")
            print(f"[OXYGEN MESSAGES PARSER] Found columns:")
            print(f"Source/Platform: {source_col}")
            print(f"Message: {message_col}")
            print(f"Timestamp: {timestamp_col}")
            print(f"Sender: {sender_col}")
            print(f"Receiver: {receiver_col}")
            print(f"Thread ID: {thread_id_col}")
            print(f"Details: {details_col}")
            
            if not source_col:
                logger.warning(f"[OXYGEN MESSAGES PARSER] No Source/Platform column found!")
                print(f"[OXYGEN MESSAGES PARSER] WARNING: No Source/Platform column found!")
            
            if not message_col:
                logger.warning(f"[OXYGEN MESSAGES PARSER] No Message column found!")
                print(f"[OXYGEN MESSAGES PARSER] WARNING: No Message column found!")
            
            for idx, row in df.iterrows():
                if all(self._is_na(row[col] if col in row.index else None) or not str(self._clean(row[col] if col in row.index else None) or '').strip() for col in df.columns[:3]):
                    continue
                
                first_col = df.columns[0] if len(df.columns) > 0 else None
                if first_col:
                    first_val = self._clean(row[first_col] if first_col in row.index else None)
                else:
                    first_val = None
                    
                if first_val and first_val.lower() in ['source', 'service', 'platform', 'application', 'message', 'timestamp', 'type']:
                    logger.debug(f"[OXYGEN MESSAGES PARSER] Skipping header row {idx}: first_val='{first_val}'")
                    continue
                
                platform = None
                if source_col:
                    source = self._clean(row[source_col] if source_col in row.index else None)
                    if source:
                        source_lower = source.lower().strip()
                        
                        if 'whatsapp' in source_lower:
                            platform = "whatsapp"
                        elif 'telegram' in source_lower:
                            platform = "telegram"
                        elif 'instagram' in source_lower:
                            platform = "instagram"
                        elif 'twitter' in source_lower:
                            platform = "x"
                        elif source_lower == 'x' or source_lower.startswith('x '):
                            platform = "x"
                        elif 'tiktok' in source_lower:
                            platform = "tiktok"
                        elif 'facebook' in source_lower or 'messenger' in source_lower:
                            platform = "facebook"
                        
                        if platform:
                            platform = self._normalize_platform_name(platform)
                        
                        if platform and platform_counts.get(platform, 0) == 0:
                            logger.info(f"[OXYGEN MESSAGES PARSER] Detected platform '{platform}' from Source: '{source}'")
                            print(f"[OXYGEN MESSAGES PARSER] Detected platform '{platform}' from Source: '{source}'")
                
                if not platform:
                    skipped_count += 1
                    if skipped_count <= 10:
                        source_val = self._clean(row[source_col] if source_col and source_col in row.index else None) if source_col else 'N/A'
                        logger.debug(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - no platform detected. Source value: '{source_val}'")
                        print(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - no platform. Source: '{source_val}'")
                    continue
                
                if platform_counts.get(platform, 0) == 0:
                    source_val = self._clean(row[source_col] if source_col and source_col in row.index else None) if source_col else 'N/A'
                    logger.info(f"[OXYGEN MESSAGES PARSER] First {platform} message detected from Source: '{source_val}'")
                    print(f"[OXYGEN MESSAGES PARSER] First {platform} message detected from Source: '{source_val}'")
                
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                message_text = None
                if message_col:
                    message_text = self._clean(row[message_col] if message_col in row.index else None)
                    if message_text and (message_text.upper() == 'N/A' or message_text.lower() == 'na'):
                        message_text = None
                else:
                    for col in df.columns:
                        if str(col).strip().lower() == 'text':
                            message_text = self._clean(row[col] if col in row.index else None)
                            if message_text and message_text.upper() != 'N/A':
                                message_col = col
                                break
                    
                    if not message_text:
                        for col in df.columns:
                            if 'message' in str(col).lower() and 'type' not in str(col).lower() and 'status' not in str(col).lower():
                                message_text = self._clean(row[col] if col in row.index else None)
                                if message_text and message_text.upper() != 'N/A':
                                    message_col = col
                                    break

                    if not message_text:
                        for col_idx in [3, 4, 5, 2]:
                            if col_idx < len(df.columns):
                                col = df.columns[col_idx]
                                val = self._clean(row[col] if col in row.index else None)
                                if val and len(val.strip()) > 5 and val.upper() != 'N/A':
                                    cleaned_val = val.replace(':', '').replace('-', '').replace('/', '').replace(' ', '').replace('@', '').replace('.', '')
                                    if not cleaned_val.isdigit() or len(val.strip()) > 20:
                                        if any(c.isalpha() for c in val[:50]) or len(val.strip()) > 20:
                                            message_text = val
                                            logger.debug(f"[OXYGEN MESSAGES PARSER] Found message in column {col_idx} ({col}): {val[:50]}...")
                                            break
                
                if not message_text:
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - no message text. Platform: {platform}, Source: {source if source_col else 'N/A'}")
                        sample_vals = [str(self._clean(row[col] if col in row.index else None) or '')[:30] for col in df.columns[:6]]
                        print(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - no message. Platform: {platform}, Sample: {sample_vals}")
                    continue
                
                if platform == "WhatsApp":
                    sender_temp = self._clean(row[sender_col] if sender_col and sender_col in row.index else None) if sender_col else None
                    sender_id_temp = None
                    
                    if sender_temp:
                        if '@s.whatsapp.net' in sender_temp:
                            parts = sender_temp.split('@')
                            sender_id_temp = parts[0].strip()
                        elif sender_temp.strip() == '0':
                            sender_id_temp = '0'
                    
                    if self._is_whatsapp_system_message(message_text, sender_id_temp, sender_temp):
                        skipped_count += 1
                        if skipped_count <= 10:
                            logger.debug(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - WhatsApp system/promotional message: {message_text[:80]}...")
                            print(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - WhatsApp system message")
                        continue
                
                timestamp = self._clean(row[timestamp_col] if timestamp_col and timestamp_col in row.index else None) if timestamp_col else None
                sender = self._clean(row[sender_col] if sender_col and sender_col in row.index else None) if sender_col else None
                
                thread_id = None
                if thread_id_col:
                    thread_id = self._clean(row[thread_id_col] if thread_id_col in row.index else None)
                
                if not thread_id:
                    thread_id = self._clean(row['Thread ID'] if 'Thread ID' in row.index else None) or \
                                  self._clean(row['Chat ID'] if 'Chat ID' in row.index else None) or \
                                  self._clean(row['Identifier'] if 'Identifier' in row.index else None) or \
                                  self._clean(row['Message ID'] if 'Message ID' in row.index else None)
                
                sender_name = None
                sender_id = None
                receiver_name = None
                receiver_id = None
                
                from_col = None
                to_col = None
                
                for col in df.columns:
                    col_str = str(col).strip()
                    col_lower = col_str.lower()
                    if col_lower == 'from':
                        from_col = col
                    elif col_lower == 'to':
                        to_col = col
                
                if from_col:
                    from_data = self._clean(row[from_col] if from_col in row.index else None)
                    if from_data:
                        name_match = re.search(r'^([^<]+)', from_data)
                        id_match = re.search(r'<([^>]+)>', from_data)
                        if name_match:
                            sender_name = name_match.group(1).strip()
                        if id_match:
                            id_value = id_match.group(1).strip()
                            sender_id = id_value
                            
                            if '@s.whatsapp.net' in id_value:
                                phone_match = re.search(r'(\d+)', id_value)
                                if phone_match:
                                    sender_id = phone_match.group(1).strip()
                                    if processed_count == 0:
                                        logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted phone from From column: '{sender_id}'")
                                        print(f"[OXYGEN MESSAGES PARSER] Extracted phone from From: '{sender_id}'")
                            else:
                                sender_id = id_value
                                if processed_count == 0:
                                    logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted ID/number from From column: '{sender_id}'")
                                    print(f"[OXYGEN MESSAGES PARSER] Extracted ID/number from From: '{sender_id}'")
                        else:
                            if not sender_name:
                                if from_data.upper() != 'N/A':
                                    sender_name = from_data
                                else:
                                    sender_name = None
                            sender_id = None
                
                if to_col:
                    to_data = self._clean(row[to_col] if to_col in row.index else None)
                    if to_data:
                        name_match = re.search(r'^([^<]+)', to_data)
                        id_match = re.search(r'<([^>]+)>', to_data)
                        if name_match:
                            receiver_name = name_match.group(1).strip()
                        if id_match:
                            id_value = id_match.group(1).strip()
                            receiver_id = id_value
                            
                            if '@s.whatsapp.net' in id_value:
                                phone_match = re.search(r'(\d+)', id_value)
                                if phone_match:
                                    receiver_id = phone_match.group(1).strip()
                                    if processed_count == 0:
                                        logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted phone from To column: '{receiver_id}'")
                                        print(f"[OXYGEN MESSAGES PARSER] Extracted phone from To: '{receiver_id}'")
                            else:
                                receiver_id = id_value
                                if processed_count == 0:
                                    logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted ID/number from To column: '{receiver_id}'")
                                    print(f"[OXYGEN MESSAGES PARSER] Extracted ID/number from To: '{receiver_id}'")
                        else:
                            if not receiver_name:
                                if to_data.upper() != 'N/A':
                                    receiver_name = to_data
                                else:
                                    receiver_name = None
                            receiver_id = None
                
                if sender_col:
                    sender_data = self._clean(row[sender_col] if sender_col in row.index else None)
                    if sender_data:
                        name_match = re.search(r'^([^<]+)', sender_data)
                        id_match = re.search(r'<([^>]+)>', sender_data)
                        if name_match and not sender_name:
                            sender_name = name_match.group(1).strip()
                        if id_match and not sender_id:
                            id_value = id_match.group(1).strip()
                            sender_id = id_value
                            
                            if '@s.whatsapp.net' in id_value:
                                phone_match = re.search(r'(\d+)', id_value)
                                if phone_match:
                                    sender_id = phone_match.group(1).strip()
                            else:
                                sender_id = id_value
                
                if receiver_col:
                    receiver_data = self._clean(row[receiver_col] if receiver_col in row.index else None)
                    if receiver_data:
                        name_match = re.search(r'^([^<]+)', receiver_data)
                        id_match = re.search(r'<([^>]+)>', receiver_data)
                        if name_match and not receiver_name:
                            receiver_name = name_match.group(1).strip()
                        if id_match and not receiver_id:
                            id_value = id_match.group(1).strip()
                            receiver_id = id_value
                            
                            if '@s.whatsapp.net' in id_value:
                                phone_match = re.search(r'(\d+)', id_value)
                                if phone_match:
                                    receiver_id = phone_match.group(1).strip()
                            else:
                                receiver_id = id_value
                
                if not sender_name and sender_col:
                    sender_name = self._clean(row[sender_col] if sender_col in row.index else None)
                if not receiver_name and receiver_col:
                    receiver_name = self._clean(row[receiver_col] if receiver_col in row.index else None)
                
                message_id = None
                chat_id_from_details = None
                if details_col:
                    details = self._clean(row[details_col] if details_col in row.index else None)
                    if details:
                        msg_id_match = re.search(r'Message ID:\s*([^\s\n\r]+)', details, re.IGNORECASE)
                        if msg_id_match:
                            message_id = msg_id_match.group(1).strip()
                            if message_id and len(message_id) > 0:
                                logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted Message ID from Details: '{message_id}'")
                                if processed_count == 0:
                                    print(f"[OXYGEN MESSAGES PARSER] Extracted Message ID from Details: '{message_id}'")
                            else:
                                message_id = None
                        
                        chat_id_match = re.search(r'Chat ID:\s*([^\s\n\r]+)', details, re.IGNORECASE)
                        if chat_id_match:
                            chat_id_from_details = chat_id_match.group(1).strip()
                            if chat_id_from_details and len(chat_id_from_details) > 0:
                                logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted Chat ID from Details: '{chat_id_from_details}'")
                                if processed_count == 0:
                                    print(f"[OXYGEN MESSAGES PARSER] Extracted Chat ID from Details: '{chat_id_from_details}'")
                            else:
                                chat_id_from_details = None
                        
                        if not receiver_id:
                            remote_phone_match = re.search(r'Remote party phone number:\s*([^\s\n\r]+)', details, re.IGNORECASE)
                            if remote_phone_match:
                                receiver_id = remote_phone_match.group(1).strip()
                                if receiver_id and len(receiver_id) > 0:
                                    logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted Remote party phone number from Details: '{receiver_id}'")
                                    if processed_count == 0:
                                        print(f"[OXYGEN MESSAGES PARSER] Extracted Remote party phone number from Details: '{receiver_id}'")
                        
                        if not receiver_id:
                            remote_party_match = re.search(r'Remote party ID:\s*([^\s\n\r]+)', details, re.IGNORECASE)
                            if remote_party_match:
                                receiver_id = remote_party_match.group(1).strip()
                                if receiver_id and len(receiver_id) > 0:
                                    logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted Remote party ID from Details: '{receiver_id}'")
                                    if processed_count == 0:
                                        print(f"[OXYGEN MESSAGES PARSER] Extracted Remote party ID from Details: '{receiver_id}'")
                        
                        if not receiver_name:
                            remote_party_name_match = re.search(r'Remote party:\s*([^\n\r]+)', details, re.IGNORECASE)
                            if remote_party_name_match:
                                remote_party_name = remote_party_name_match.group(1).strip()
                                if remote_party_name and len(remote_party_name) > 0 and remote_party_name.upper() != 'N/A':
                                    receiver_name = remote_party_name
                                    logger.debug(f"[OXYGEN MESSAGES PARSER] Extracted Remote party name from Details: '{receiver_name}'")
                                    if processed_count == 0:
                                        print(f"[OXYGEN MESSAGES PARSER] Extracted Remote party name from Details: '{receiver_name}'")
                
                if not message_id:
                    message_id = self._generate_oxygen_message_id(platform, row, file_id, idx)
                    logger.debug(f"[OXYGEN MESSAGES PARSER] Generated Message ID (not found in Details): {message_id}")
                    if processed_count == 0:
                        print(f"[OXYGEN MESSAGES PARSER] Generated Message ID (not found in Details): {message_id}")
                
                sender_id_val = sender_id if sender_id else self._clean(row['Sender ID'] if 'Sender ID' in row.index else None)
                recipient_val = self._clean(row['Recipient'] if 'Recipient' in row.index else None) or self._clean(row['Receiver'] if 'Receiver' in row.index else None)
                recipient_id_val = receiver_id if receiver_id else self._clean(row['Recipient ID'] if 'Recipient ID' in row.index else None) or self._clean(row['Receiver ID'] if 'Receiver ID' in row.index else None)
                message_type_val = self._clean(row['Message Type'] if 'Message Type' in row.index else None) or self._clean(row['Message Status'] if 'Message Status' in row.index else None) or 'text'
                direction_val = self._clean(row['Direction'] if 'Direction' in row.index else None)
                
                if platform == "WhatsApp":
                    if self._is_whatsapp_system_message(message_text, sender_id_val, sender_name or sender):
                        skipped_count += 1
                        if skipped_count <= 10:
                            logger.debug(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - WhatsApp system/promotional message (final check): {message_text[:80]}...")
                            print(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - WhatsApp system message (final check)")
                        continue
                
                final_chat_id = chat_id_from_details if chat_id_from_details else thread_id
                
                message_data = {
                    "file_id": file_id,
                    "platform": platform,
                    "message_text": message_text,
                    "from_name": sender_name or sender,
                    "sender_number": sender_id_val,
                    "to_name": receiver_name or recipient_val,
                    "recipient_number": receiver_id or recipient_id_val,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": final_chat_id,
                    "message_id": message_id,
                    "message_type": message_type_val,
                    "direction": direction_val,
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                if platform_counts[platform] == 1:
                    logger.debug(f"[OXYGEN MESSAGES PARSER] First {platform} message: message_id={message_data['message_id']}, "
                               f"from={message_data['from_name']}, text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN MESSAGES PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            logger.info(f"[OXYGEN MESSAGES PARSER] Platform breakdown: {platform_counts}")
            print(f"[OXYGEN MESSAGES PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            print(f"[OXYGEN MESSAGES PARSER] Platform breakdown: {platform_counts}")
            
        except Exception as e:
            logger.error(f"[OXYGEN MESSAGES PARSER] Error parsing Messages sheet: {e}", exc_info=True)
            print(f"[OXYGEN MESSAGES PARSER] Error parsing Messages sheet: {e}")
            
            traceback.print_exc()
        
        return results


    def _parse_oxygen_whatsapp_messages(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[OXYGEN WHATSAPP PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN WHATSAPP PARSER] Sheet loaded: {len(df)} rows, columns: {list(df.columns)[:15]}")
            
            processed_count = 0
            skipped_count = 0
            skip_reasons = {'no_message': 0, 'header_row': 0, 'invalid_format': 0}
            
            if 'Contacts' in sheet_name or 'Contact' in sheet_name:
                for idx, row in df.iterrows():
                    source = self._clean(row.get('Source', ''))
                    
                    if not source or 'whatsapp' not in source.lower():
                        continue
                    
                    message_text = None
                    message_fields = ['Other', 'Internet', 'Phones & Emails']
                    
                    for field in message_fields:
                        val = self._clean(row.get(field, ''))
                        if val and len(val.strip()) > 5:
                            if any(keyword in val.lower() for keyword in ['message:', 'text:', 'chat:']):
                                for keyword in ['message:', 'text:', 'chat:']:
                                    if keyword in val.lower():
                                        parts = val.split(':')
                                        if len(parts) > 1:
                                            message_text = ':'.join(parts[1:]).strip()
                                            break
                            elif len(val.strip()) > 20 and not val.replace(':', '').replace('-', '').replace('/', '').isdigit():
                                message_text = val
                    
                    if not message_text:
                        skip_reasons['no_message'] += 1
                        continue
                    
                    contact_name = self._clean(row.get('Contact', ''))
                    phones_emails = self._clean(row.get('Phones & Emails', ''))
                    phone_number = None
                    if phones_emails:
                        import re
                        phone_matches = re.findall(r'(\+?[0-9]{10,15})', phones_emails)
                        if phone_matches:
                            phone_number = max(phone_matches, key=len)
                    
                    timestamp = None
                    other_field = self._clean(row.get('Other', ''))
                    if other_field and ('/' in other_field or ':' in other_field):
                        import re
                        timestamp_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}[\s:]+\d{1,2}:\d{2})', other_field)
                        if timestamp_match:
                            timestamp = timestamp_match.group(1)
                    
                    message_data = {
                        "file_id": file_id,
                        "platform": "WhatsApp",
                        "message_text": message_text,
                        "from_name": contact_name,
                        "sender_number": phone_number,
                        "to_name": None,
                        "recipient_number": None,
                        "timestamp": timestamp,
                        "thread_id": phone_number or contact_name,
                        "chat_id": phone_number or contact_name,
                        "message_id": self._generate_oxygen_message_id("whatsapp", row, file_id, idx),
                        "message_type": "text",
                        "direction": None,
                        "source_tool": "oxygen",
                        "sheet_name": sheet_name
                    }
                    
                    results.append(message_data)
                    processed_count += 1
                
                logger.info(f"[OXYGEN WHATSAPP PARSER] Processed {processed_count} messages from Contacts sheet, skipped {skipped_count} rows")
                return results
            
            header_row_idx = None
            for idx in range(min(20, len(df))):
                row_text = ' '.join([str(df.iloc[idx, col_idx]) if col_idx < len(df.columns) else '' 
                                   for col_idx in range(min(20, len(df.columns)))]).lower()
                
                if any(kw in row_text for kw in ['message', 'timestamp', 'direction', 'sender', 'from', 'time stamp']):
                    if any(kw in row_text for kw in ['time stamp', 'date/time', 'date', 'received', 'sent', 'direction']):
                        header_row_idx = idx
                        logger.debug(f"[OXYGEN WHATSAPP PARSER] Potential header at row {idx}: {row_text[:100]}")
                        break
            
            if header_row_idx is not None:
                try:
                    df.columns = df.iloc[header_row_idx]
                    df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
                    logger.debug(f"[OXYGEN WHATSAPP PARSER] Using row {header_row_idx} as header")
                except:
                    logger.debug(f"[OXYGEN WHATSAPP PARSER] Could not use row {header_row_idx} as header, using original columns")
            
            message_col = None
            timestamp_col = None
            sender_col = None
            direction_col = None
            
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'message' in col_lower and not message_col and 'type' not in col_lower:
                    message_col = col
                elif ('timestamp' in col_lower or ('time' in col_lower and 'stamp' in col_lower) or 'date/time' in col_lower) and not timestamp_col:
                    timestamp_col = col
                elif ('sender' in col_lower or 'from' in col_lower) and not sender_col:
                    sender_col = col
                elif 'direction' in col_lower and not direction_col:
                    direction_col = col
            
            skip_keywords = [
                'source', 'status', 'received', 'delivered', 'seen', 'categories',
                'direction', 'time stamp', 'timestamp', 'deleted', 'chats\\', 'calls\\',
                'at the server', 'failed call', 'outgoing', 'incoming', 'message', 'call',
                'user name', 'user id', 'full name', 'phone number', 'user picture'
            ]
            
            for idx, row in df.iterrows():
                first_col = df.columns[0] if len(df.columns) > 0 else None
                if first_col:
                    first_val = self._clean(row[first_col] if first_col in row.index else None)
                else:
                    first_val = None
                    
                if first_val and first_val.lower() in skip_keywords:
                    skip_reasons['header_row'] += 1
                    continue
                
                row_text_lower = ' '.join([str(self._clean(row[col] if col in row.index else None) or '').lower() for col in df.columns[:10]]).lower()
                if '\\chats\\' in row_text_lower or '\\calls\\' in row_text_lower:
                    skip_reasons['invalid_format'] += 1
                    continue
                
                message_text = None
                if message_col:
                    message_text = self._clean(row[message_col] if message_col in row.index else None)
                else:
                    for col in df.columns:
                        val = self._clean(row[col] if col in row.index else None)
                        if val and len(val.strip()) > 10:
                            if not val.replace(':', '').replace('-', '').replace('/', '').replace(' ', '').isdigit():
                                if any(c.isalpha() for c in val[:50]):
                                    message_text = val
                                    break
                
                if not message_text:
                    skip_reasons['no_message'] += 1
                    skipped_count += 1
                    continue
                
                timestamp = self._clean(row[timestamp_col] if timestamp_col and timestamp_col in row.index else None) if timestamp_col else None
                if not timestamp:
                    for col in df.columns[:10]:
                        val = self._clean(row[col] if col in row.index else None)
                        if val and ('/' in val or ':' in val) and len(val) > 8:
                            if any(c.isdigit() for c in val):
                                timestamp = val
                                break
                
                sender = self._clean(row[sender_col] if sender_col and sender_col in row.index else None) if sender_col else None
                direction = self._clean(row[direction_col] if direction_col and direction_col in row.index else None) if direction_col else None

                thread_id = self._clean(row['Thread ID'] if 'Thread ID' in row.index else None) or \
                          self._clean(row['Chat ID'] if 'Chat ID' in row.index else None) or \
                          self._clean(row['Identifier'] if 'Identifier' in row.index else None) or \
                          self._clean(row['Contact'] if 'Contact' in row.index else None)
                
                message_id = self._generate_oxygen_message_id("whatsapp", row, file_id, idx)
                
                message_data = {
                    "file_id": file_id,
                    "platform": "WhatsApp",
                    "message_text": message_text,
                    "from_name": sender,
                    "sender_number": None,
                    "to_name": None,
                    "recipient_number": None,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": thread_id,
                    "message_id": message_id,
                    "message_type": "text",
                    "direction": direction,
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[OXYGEN WHATSAPP PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"from={message_data['from_name']}, text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN WHATSAPP PARSER] Processed {processed_count} messages, skipped {skipped_count} rows, reasons: {skip_reasons}")
            
        except Exception as e:
            logger.error(f"[OXYGEN WHATSAPP PARSER] Error parsing WhatsApp messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Oxygen WhatsApp messages: {e}")
            
            traceback.print_exc()
        
        return results

    def _generate_oxygen_message_id(self, platform: str, row: pd.Series, file_id: int, index: int) -> str:
        message_id_fields = ['Message ID', 'Item ID', 'Record', 'message_id', 'id', 'Instant Message #']
        for field in message_id_fields:
            if hasattr(row, 'index') and field in row.index:
                msg_id = self._clean(row.get(field))
                if msg_id and msg_id.lower() not in ['nan', 'none', '']:
                    return f"{platform}_{file_id}_{msg_id}"
        
        timestamp = self._clean(row.get('timestamp', '')) or self._clean(row.get('Timestamp', ''))
        if timestamp:
            clean_timestamp = str(timestamp).replace('/', '').replace(':', '').replace('-', '').replace(' ', '')[:15]
            return f"{platform}_{file_id}_{clean_timestamp}_{index}"
        
        return f"{platform}_{file_id}_{index}"

    def _parse_oxygen_telegram_messages(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[OXYGEN TELEGRAM PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN TELEGRAM PARSER] Sheet loaded: {len(df)} rows, columns: {list(df.columns)[:15]}")
            print(f"[OXYGEN TELEGRAM PARSER] Sheet loaded: {len(df)} rows, columns ({len(df.columns)}): {list(df.columns)[:10]}")
            
            processed_count = 0
            skipped_count = 0
            skip_reasons = {'no_message': 0, 'header_row': 0, 'invalid_format': 0}
            
            header_row_idx = None
            for idx in range(min(20, len(df))):
                row_text = ' '.join([str(df.iloc[idx, col_idx]) if col_idx < len(df.columns) else '' 
                                   for col_idx in range(min(20, len(df.columns)))]).lower()
                
                if any(kw in row_text for kw in ['message', 'timestamp', 'direction', 'sender', 'from', 'time stamp']):
                    if any(kw in row_text for kw in ['time stamp', 'date/time', 'date', 'received', 'sent', 'direction']):
                        header_row_idx = idx
                        logger.debug(f"[OXYGEN TELEGRAM PARSER] Potential header at row {idx}")
                        break
            
            if header_row_idx is not None:
                try:
                    df.columns = df.iloc[header_row_idx]
                    df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
                    logger.debug(f"[OXYGEN TELEGRAM PARSER] Using row {header_row_idx} as header")
                    print(f"[OXYGEN TELEGRAM PARSER] Found header at row {header_row_idx}, columns: {list(df.columns)[:10]}")
                except:
                    logger.debug(f"[OXYGEN TELEGRAM PARSER] Could not use row {header_row_idx} as header, using original columns")
            
            message_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if col_lower == 'text':
                    message_col = col
                    break
                elif 'message' in col_lower and not message_col and 'type' not in col_lower:
                    message_col = col
                elif 'body' in col_lower and not message_col:
                    message_col = col
            
            timestamp_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if ('timestamp' in col_lower or ('time' in col_lower and 'stamp' in col_lower) or 
                    'date/time' in col_lower or 'date' in col_lower and 'time' in col_lower):
                    timestamp_col = col
                    break
            
            sender_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if col_lower == 'from':
                    sender_col = col
                    break
                elif 'sender' in col_lower and not sender_col:
                    sender_col = col
            
            recipient_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if col_lower == 'to':
                    recipient_col = col
                    break
                elif 'recipient' in col_lower:
                    recipient_col = col
                    break
            
            chat_id_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'thread id' in col_lower or col_lower == 'thread id':
                    chat_id_col = col
                    break
                elif 'chat id' in col_lower or 'identifier' in col_lower:
                    chat_id_col = col
                    break
            
            source_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if col_lower == 'source':
                    source_col = col
                    break
            
            logger.info(f"[OXYGEN TELEGRAM PARSER] Detected columns - Message/Text: {message_col}, Timestamp: {timestamp_col}, Sender/From: {sender_col}, Recipient/To: {recipient_col}, Thread ID: {chat_id_col}, Source: {source_col}")
            print(f"[OXYGEN TELEGRAM PARSER] Detected columns - Message/Text: {message_col}, Timestamp: {timestamp_col}, Sender/From: {sender_col}, Recipient/To: {recipient_col}")
            
            skip_keywords = [
                'source', 'status', 'received', 'delivered', 'seen', 'categories',
                'direction', 'time stamp', 'timestamp', 'deleted', 'chats\\', 'calls\\',
                'at the server', 'failed call', 'outgoing', 'incoming', 'message', 'call',
                'user name', 'user id', 'full name', 'phone number', 'user picture'
            ]

            for idx, row in df.iterrows():
                first_col = df.columns[0] if len(df.columns) > 0 else None
                if first_col:
                    first_val = self._clean(row[first_col] if first_col in row.index else None)
                else:
                    first_val = None
                    
                if first_val and first_val.lower() in skip_keywords:
                    skip_reasons['header_row'] += 1
                    continue
                
                if source_col:
                    source_val = self._clean(row[source_col] if source_col in row.index else None)
                    if source_val and source_val.lower() in ['source', 'type', 'direction']:
                        skip_reasons['header_row'] += 1
                        continue
                    if source_val and ('\\' in source_val or '**' in source_val or '/' in source_val):
                        if not any(c.isalpha() for c in source_val.replace('\\', '').replace('/', '').replace('**', '').replace('*', '').replace('-', '').replace('_', '')[:20]):
                            skip_reasons['invalid_format'] += 1
                            continue
                
                row_text_lower = ' '.join([str(self._clean(row[col] if col in row.index else None) or '').lower() for col in df.columns[:10]]).lower()
                if '\\chats\\' in row_text_lower or '\\calls\\' in row_text_lower:
                    skip_reasons['invalid_format'] += 1
                    continue
                
                message_text = None
                if message_col:
                    message_text = self._clean(row[message_col] if message_col in row.index else None)
                    
                    if not message_text:
                        skip_reasons['no_message'] += 1
                        skipped_count += 1
                        continue
                    
                    if message_text.upper() == 'N/A' or message_text.lower() == 'na':
                        skip_reasons['no_message'] += 1
                        skipped_count += 1
                        continue
                    
                    if message_text:
                        if '\\' in message_text or message_text.count('/') > 2:
                            if not any(c.isalpha() for c in message_text.replace('\\', '').replace('/', '').replace(' ', '')[:30]):
                                skip_reasons['invalid_format'] += 1
                                continue
                        if '**' in message_text or message_text.startswith('org.') or message_text.count('.') > 3:
                            if ' ' not in message_text[:30]:
                                skip_reasons['invalid_format'] += 1
                                continue
                
                if not message_text:
                    skip_reasons['no_message'] += 1
                    skipped_count += 1
                    continue
                
                timestamp = None
                if timestamp_col:
                    timestamp = self._clean(row[timestamp_col] if timestamp_col in row.index else None)
                else:
                    for col in df.columns[:10]:
                        val = self._clean(row[col] if col in row.index else None)
                        if val and ('/' in val or ':' in val) and len(val) > 8:
                            if any(c.isdigit() for c in val):
                                timestamp = val
                                break
                
                sender_name = None
                sender_id = None
                if sender_col:
                    sender_raw = self._clean(row[sender_col] if sender_col in row.index else None)
                    if sender_raw:
                        name_match = re.search(r'^([^<]+)', sender_raw)
                        id_match = re.search(r'<([^>]+)>', sender_raw)
                        if name_match:
                            sender_name = name_match.group(1).strip()
                        if id_match:
                            id_value = id_match.group(1).strip()
                            if '@s.whatsapp.net' in id_value:
                                phone_match = re.search(r'(\d+)', id_value)
                                if phone_match:
                                    sender_id = phone_match.group(1).strip()
                            else:
                                sender_id = id_value
                        if not sender_name:
                            sender_name = sender_raw
                
                receiver_name = None
                receiver_id = None
                if recipient_col:
                    receiver_raw = self._clean(row[recipient_col] if recipient_col in row.index else None)
                    if receiver_raw:
                        name_match = re.search(r'^([^<]+)', receiver_raw)
                        id_match = re.search(r'<([^>]+)>', receiver_raw)
                        if name_match:
                            receiver_name = name_match.group(1).strip()
                        if id_match:
                            id_value = id_match.group(1).strip()
                            if '@s.whatsapp.net' in id_value:
                                phone_match = re.search(r'(\d+)', id_value)
                                if phone_match:
                                    receiver_id = phone_match.group(1).strip()
                            else:
                                receiver_id = id_value
                        if not receiver_name:
                            receiver_name = receiver_raw
                
                details_col = None
                for col in df.columns:
                    if str(col).lower().strip() == 'details':
                        details_col = col
                        break
                
                if not sender_id and details_col:
                    details = self._clean(row[details_col] if details_col in row.index else None)
                    if details:
                        remote_party_match = re.search(r'Remote party ID:\s*(\d+)', details, re.IGNORECASE)
                        if remote_party_match:
                            sender_id = remote_party_match.group(1)
                
                
                thread_id = None
                if chat_id_col:
                    thread_id = self._clean(row[chat_id_col] if chat_id_col in row.index else None)
                else:
                    thread_id = self._clean(row['Chat ID'] if 'Chat ID' in row.index else None) or \
                              self._clean(row['Thread ID'] if 'Thread ID' in row.index else None) or \
                              self._clean(row['Identifier'] if 'Identifier' in row.index else None)
                
                message_id_from_details = None
                if details_col:
                    details = self._clean(row[details_col] if details_col in row.index else None)
                    if details:
                        msg_id_match = re.search(r'Message ID:\s*(\d+)', details, re.IGNORECASE)
                        if msg_id_match:
                            message_id_from_details = msg_id_match.group(1)
                
                if message_id_from_details:
                    final_message_id = f"telegram_{file_id}_{message_id_from_details}"
                else:
                    final_message_id = self._generate_oxygen_message_id("telegram", row, file_id, idx)
                
                direction_val = self._clean(row['Direction'] if 'Direction' in row.index else None)
                
                message_data = {
                    "file_id": file_id,
                    "platform": "Telegram",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": receiver_name,
                    "recipient_number": receiver_id,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": thread_id,
                    "message_id": final_message_id,
                    "message_type": "text",
                    "direction": direction_val,
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN TELEGRAM PARSER] Processed {processed_count} messages, skipped {skipped_count} rows, reasons: {skip_reasons}")
            print(f"[OXYGEN TELEGRAM PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            
        except Exception as e:
            logger.error(f"[OXYGEN TELEGRAM PARSER] Error parsing Telegram messages from {sheet_name}: {e}", exc_info=True)
            print(f"[OXYGEN TELEGRAM PARSER] Error: {e}")
            
            traceback.print_exc()
        
        return results

    def _parse_oxygen_instagram_messages(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[OXYGEN INSTAGRAM PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN INSTAGRAM PARSER] Sheet loaded: {len(df)} rows, columns: {list(df.columns)[:15]}")
            print(f"[OXYGEN INSTAGRAM PARSER] Sheet loaded: {len(df)} rows, columns ({len(df.columns)}): {list(df.columns)[:10]}")
            
            processed_count = 0
            skipped_count = 0
            skip_reasons = {'no_message': 0, 'header_row': 0, 'invalid_format': 0}
            
            header_row_idx = None
            for idx in range(min(20, len(df))):
                row_text = ' '.join([str(df.iloc[idx, col_idx]) if col_idx < len(df.columns) else '' 
                                   for col_idx in range(min(20, len(df.columns)))]).lower()
                
                if any(kw in row_text for kw in ['message', 'timestamp', 'direction', 'sender', 'recipient', 'time stamp']):
                    if any(kw in row_text for kw in ['time stamp', 'date/time', 'date', 'received', 'sent', 'direction']):
                        header_row_idx = idx
                        logger.debug(f"[OXYGEN INSTAGRAM PARSER] Potential header at row {idx}")
                        break
            
            if header_row_idx is not None:
                try:
                    df.columns = df.iloc[header_row_idx]
                    df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
                    logger.debug(f"[OXYGEN INSTAGRAM PARSER] Using row {header_row_idx} as header")
                    print(f"[OXYGEN INSTAGRAM PARSER] Found header at row {header_row_idx}, columns: {list(df.columns)[:10]}")
                except:
                    logger.debug(f"[OXYGEN INSTAGRAM PARSER] Could not use row {header_row_idx} as header, using original columns")
            
            message_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'message' in col_lower and not message_col and 'type' not in col_lower:
                    message_col = col
                elif 'body' in col_lower and not message_col:
                    message_col = col
            
            timestamp_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if ('timestamp' in col_lower or ('time' in col_lower and 'stamp' in col_lower) or 
                    'date/time' in col_lower or ('date' in col_lower and 'time' in col_lower)):
                    timestamp_col = col
                    break
            
            sender_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if ('sender' in col_lower or 'from' in col_lower) and not sender_col:
                    sender_col = col
            
            recipient_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'recipient' in col_lower or 'to' in col_lower:
                    recipient_col = col
                    break
            
            chat_id_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'chat id' in col_lower or 'thread id' in col_lower or 'identifier' in col_lower:
                    chat_id_col = col
                    break
            
            logger.info(f"[OXYGEN INSTAGRAM PARSER] Detected columns - Message: {message_col}, Timestamp: {timestamp_col}, Sender: {sender_col}, Recipient: {recipient_col}")
            print(f"[OXYGEN INSTAGRAM PARSER] Detected columns - Message: {message_col}, Timestamp: {timestamp_col}, Sender: {sender_col}")
            
            skip_keywords = [
                'source', 'status', 'received', 'delivered', 'seen', 'categories',
                'direction', 'time stamp', 'timestamp', 'deleted', 'chats\\', 'calls\\',
                'at the server', 'failed call', 'outgoing', 'incoming', 'message', 'call',
                'user name', 'user id', 'full name', 'phone number', 'user picture'
            ]
            
            for idx, row in df.iterrows():
                first_val = self._clean(row.get(df.columns[0], ''))
                if first_val and first_val.lower() in skip_keywords:
                    skip_reasons['header_row'] += 1
                    continue
                
                row_text_lower = ' '.join([str(row.get(col, '')).lower() for col in df.columns[:10]]).lower()
                if '\\chats\\' in row_text_lower or '\\calls\\' in row_text_lower:
                    skip_reasons['invalid_format'] += 1
                    continue
                
                message_text = None
                if message_col:
                    message_text = self._clean(row.get(message_col))
                else:
                    for col in df.columns:
                        val = self._clean(row.get(col))
                        if val and len(val.strip()) > 10:
                            if not val.replace(':', '').replace('-', '').replace('/', '').replace(' ', '').isdigit():
                                if any(c.isalpha() for c in val[:50]):
                                    message_text = val
                                    break
                
                if not message_text:
                    skip_reasons['no_message'] += 1
                    skipped_count += 1
                    continue
                
                timestamp = None
                if timestamp_col:
                    timestamp = self._clean(row.get(timestamp_col))
                else:
                    for col in df.columns[:10]:
                        val = self._clean(row.get(col))
                        if val and ('/' in val or ':' in val) and len(val) > 8:
                            if any(c.isdigit() for c in val):
                                timestamp = val
                                break
                
                sender_name = None
                sender_id = None
                if sender_col:
                    sender_raw = self._clean(row.get(sender_col))
                    if sender_raw:
                        name_match = re.search(r'^([^<]+)', sender_raw)
                        id_match = re.search(r'<([^>]+)>', sender_raw)
                        if name_match:
                            sender_name = name_match.group(1).strip()
                        if id_match:
                            id_value = id_match.group(1).strip()
                            if '@s.whatsapp.net' in id_value:
                                phone_match = re.search(r'(\d+)', id_value)
                                if phone_match:
                                    sender_id = phone_match.group(1).strip()
                            else:
                                sender_id = id_value
                        if not sender_name:
                            sender_name = sender_raw
                
                receiver_name = None
                receiver_id = None
                if recipient_col:
                    receiver_raw = self._clean(row.get(recipient_col))
                    if receiver_raw:
                        name_match = re.search(r'^([^<]+)', receiver_raw)
                        id_match = re.search(r'<([^>]+)>', receiver_raw)
                        if name_match:
                            receiver_name = name_match.group(1).strip()
                        if id_match:
                            id_value = id_match.group(1).strip()
                            if '@s.whatsapp.net' in id_value:
                                phone_match = re.search(r'(\d+)', id_value)
                                if phone_match:
                                    receiver_id = phone_match.group(1).strip()
                            else:
                                receiver_id = id_value
                        if not receiver_name:
                            receiver_name = receiver_raw
                
                thread_id = None
                if chat_id_col:
                    thread_id = self._clean(row.get(chat_id_col))
                else:
                    thread_id = self._clean(row.get('Thread ID', '')) or \
                              self._clean(row.get('Chat ID', '')) or \
                              self._clean(row.get('Identifier', ''))
                
                message_data = {
                    "file_id": file_id,
                    "platform": "Instagram",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": receiver_name,
                    "recipient_number": receiver_id,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": thread_id,
                    "message_id": self._generate_oxygen_message_id("instagram", row, file_id, idx),
                    "message_type": "text",
                    "direction": self._clean(row.get('Direction', '')),
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN INSTAGRAM PARSER] Processed {processed_count} messages, skipped {skipped_count} rows, reasons: {skip_reasons}")
            print(f"[OXYGEN INSTAGRAM PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            
        except Exception as e:
            logger.error(f"[OXYGEN INSTAGRAM PARSER] Error parsing Instagram messages from {sheet_name}: {e}", exc_info=True)
            print(f"[OXYGEN INSTAGRAM PARSER] Error: {e}")
            
            traceback.print_exc()
        
        return results

    def _parse_oxygen_twitter_messages(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[OXYGEN TWITTER PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN TWITTER PARSER] Sheet loaded: {len(df)} rows, columns: {list(df.columns)[:15]}")
            print(f"[OXYGEN TWITTER PARSER] Sheet loaded: {len(df)} rows, columns ({len(df.columns)}): {list(df.columns)[:10]}")
            
            processed_count = 0
            skipped_count = 0
            skip_reasons = {'no_message': 0, 'header_row': 0, 'invalid_format': 0}
            
            header_row_idx = None
            for idx in range(min(20, len(df))):
                row_text = ' '.join([str(df.iloc[idx, col_idx]) if col_idx < len(df.columns) else '' 
                                   for col_idx in range(min(20, len(df.columns)))]).lower()
                
                if any(kw in row_text for kw in ['message', 'text', 'timestamp', 'direction', 'sender', 'recipient', 'time stamp']):
                    if any(kw in row_text for kw in ['time stamp', 'date/time', 'date', 'received', 'sent', 'direction']):
                        header_row_idx = idx
                        logger.debug(f"[OXYGEN TWITTER PARSER] Potential header at row {idx}")
                        break
            
            if header_row_idx is not None:
                try:
                    df.columns = df.iloc[header_row_idx]
                    df = df.iloc[header_row_idx + 1:].reset_index(drop=True)
                    logger.debug(f"[OXYGEN TWITTER PARSER] Using row {header_row_idx} as header")
                    print(f"[OXYGEN TWITTER PARSER] Found header at row {header_row_idx}, columns: {list(df.columns)[:10]}")
                except:
                    logger.debug(f"[OXYGEN TWITTER PARSER] Could not use row {header_row_idx} as header, using original columns")
            
            message_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'text' in col_lower and not message_col:
                    message_col = col
                elif 'message' in col_lower and not message_col and 'type' not in col_lower:
                    message_col = col
            
            timestamp_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if ('timestamp' in col_lower or ('time' in col_lower and 'stamp' in col_lower) or 
                    'date/time' in col_lower or ('date' in col_lower and 'time' in col_lower)):
                    timestamp_col = col
                    break
            
            sender_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if ('sender' in col_lower or 'from' in col_lower) and not sender_col:
                    sender_col = col
            
            recipient_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'recipient' in col_lower or 'to' in col_lower:
                    recipient_col = col
                    break
            
            chat_id_col = None
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if 'chat id' in col_lower or 'thread id' in col_lower or 'identifier' in col_lower:
                    chat_id_col = col
                    break
            
            logger.info(f"[OXYGEN TWITTER PARSER] Detected columns - Message/Text: {message_col}, Timestamp: {timestamp_col}, Sender: {sender_col}, Recipient: {recipient_col}")
            print(f"[OXYGEN TWITTER PARSER] Detected columns - Message/Text: {message_col}, Timestamp: {timestamp_col}, Sender: {sender_col}")
            
            skip_keywords = [
                'source', 'status', 'received', 'delivered', 'seen', 'categories',
                'direction', 'time stamp', 'timestamp', 'deleted', 'chats\\', 'calls\\',
                'at the server', 'failed call', 'outgoing', 'incoming', 'message', 'call',
                'user name', 'user id', 'full name', 'phone number', 'user picture'
            ]
            
            for idx, row in df.iterrows():
                first_val = self._clean(row.get(df.columns[0], ''))
                if first_val and first_val.lower() in skip_keywords:
                    skip_reasons['header_row'] += 1
                    continue
                
                row_text_lower = ' '.join([str(row.get(col, '')).lower() for col in df.columns[:10]]).lower()
                if '\\chats\\' in row_text_lower or '\\calls\\' in row_text_lower:
                    skip_reasons['invalid_format'] += 1
                    continue
                
                message_text = None
                if message_col:
                    message_text = self._clean(row.get(message_col))
                else:
                    for col in df.columns:
                        val = self._clean(row.get(col))
                        if val and len(val.strip()) > 10:
                            if not val.replace(':', '').replace('-', '').replace('/', '').replace(' ', '').isdigit():
                                if any(c.isalpha() for c in val[:50]):
                                    message_text = val
                                    break
                
                if not message_text:
                    skip_reasons['no_message'] += 1
                    skipped_count += 1
                    continue
                
                timestamp = None
                if timestamp_col:
                    timestamp = self._clean(row.get(timestamp_col))
                else:
                    for col in df.columns[:10]:
                        val = self._clean(row.get(col))
                        if val and ('/' in val or ':' in val) and len(val) > 8:
                            if any(c.isdigit() for c in val):
                                timestamp = val
                                break
                
                sender = None
                if sender_col:
                    sender = self._clean(row.get(sender_col))
                
                sender_id = None
                sender_id_col = None
                for col in df.columns:
                    col_lower = str(col).lower().strip()
                    if 'sender id' in col_lower:
                        sender_id_col = col
                        break
                if sender_id_col:
                    sender_id = self._clean(row.get(sender_id_col))
                
                recipient = None
                if recipient_col:
                    recipient = self._clean(row.get(recipient_col))
                
                recipient_id = None
                recipient_id_col = None
                for col in df.columns:
                    col_lower = str(col).lower().strip()
                    if 'recipient id' in col_lower:
                        recipient_id_col = col
                        break
                if recipient_id_col:
                    recipient_id = self._clean(row.get(recipient_id_col))
                
                thread_id = None
                if chat_id_col:
                    thread_id = self._clean(row.get(chat_id_col))
                else:
                    thread_id = self._clean(row.get('Thread ID', '')) or \
                              self._clean(row.get('Chat ID', '')) or \
                              self._clean(row.get('Identifier', ''))
                
                message_data = {
                    "file_id": file_id,
                    "platform": "X",
                    "message_text": message_text,
                    "from_name": sender,
                    "sender_number": sender_id,
                    "to_name": recipient,
                    "recipient_number": recipient_id,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": thread_id,
                    "message_id": self._generate_oxygen_message_id("x", row, file_id, idx),
                    "message_type": "text",
                    "direction": self._clean(row.get('Direction', '')),
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN TWITTER PARSER] Processed {processed_count} messages, skipped {skipped_count} rows, reasons: {skip_reasons}")
            print(f"[OXYGEN TWITTER PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            
        except Exception as e:
            logger.error(f"[OXYGEN TWITTER PARSER] Error parsing Twitter messages from {sheet_name}: {e}", exc_info=True)
            print(f"[OXYGEN TWITTER PARSER] Error: {e}")
            
            traceback.print_exc()
        
        return results

    def _parse_oxygen_tiktok_messages(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[OXYGEN TIKTOK PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN TIKTOK PARSER] Sheet loaded: {len(df)} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', ''))
                
                if not message_text:
                    skipped_count += 1
                    continue
                
                sender_name = None
                sender_id = None
                sender_raw = self._clean(row.get('Sender', ''))
                if sender_raw:
                    name_match = re.search(r'^([^<]+)', sender_raw)
                    id_match = re.search(r'<([^>]+)>', sender_raw)
                    if name_match:
                        sender_name = name_match.group(1).strip()
                    if id_match:
                        id_value = id_match.group(1).strip()
                        if '@s.whatsapp.net' in id_value:
                            phone_match = re.search(r'(\d+)', id_value)
                            if phone_match:
                                sender_id = phone_match.group(1).strip()
                        else:
                            sender_id = id_value
                    if not sender_name:
                        sender_name = sender_raw
                
                receiver_name = None
                receiver_id = None
                receiver_raw = self._clean(row.get('Recipient', ''))
                if receiver_raw:
                    name_match = re.search(r'^([^<]+)', receiver_raw)
                    id_match = re.search(r'<([^>]+)>', receiver_raw)
                    if name_match:
                        receiver_name = name_match.group(1).strip()
                    if id_match:
                        id_value = id_match.group(1).strip()
                        if '@s.whatsapp.net' in id_value:
                            phone_match = re.search(r'(\d+)', id_value)
                            if phone_match:
                                receiver_id = phone_match.group(1).strip()
                        else:
                            receiver_id = id_value
                    if not receiver_name:
                        receiver_name = receiver_raw
                
                message_data = {
                    "file_id": file_id,
                    "platform": "TikTok",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": receiver_name,
                    "recipient_number": receiver_id,
                    "timestamp": self._clean(row.get('Timestamp', '')),
                    "thread_id": self._clean(row.get('Thread ID', '')),
                    "chat_id": None,
                    "message_id": self._generate_oxygen_message_id("tiktok", row, file_id, idx),
                    "message_type": self._clean(row.get('Message Type', '')) or 'text',
                    "direction": None,
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN TIKTOK PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            
        except Exception as e:
            logger.error(f"[OXYGEN TIKTOK PARSER] Error parsing TikTok messages from {sheet_name}: {e}", exc_info=True)
        
        return results

    def _parse_oxygen_facebook_messages(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[OXYGEN FACEBOOK PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN FACEBOOK PARSER] Sheet loaded: {len(df)} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', '')) or \
                              self._clean(row.get('Content', ''))
                
                if not message_text:
                    skipped_count += 1
                    continue
                
                sender_name = None
                sender_id = None
                sender_raw = self._clean(row.get('Sender', ''))
                if sender_raw:
                    name_match = re.search(r'^([^<]+)', sender_raw)
                    id_match = re.search(r'<([^>]+)>', sender_raw)
                    if name_match:
                        sender_name = name_match.group(1).strip()
                    if id_match:
                        id_value = id_match.group(1).strip()
                        if '@s.whatsapp.net' in id_value:
                            phone_match = re.search(r'(\d+)', id_value)
                            if phone_match:
                                sender_id = phone_match.group(1).strip()
                        else:
                            sender_id = id_value
                    if not sender_name:
                        sender_name = sender_raw
                
                if not sender_id:
                    sender_id = self._clean(row.get('Sender ID', ''))
                
                receiver_name = None
                receiver_id = None
                receiver_raw = self._clean(row.get('Recipient', ''))
                if receiver_raw:
                    name_match = re.search(r'^([^<]+)', receiver_raw)
                    id_match = re.search(r'<([^>]+)>', receiver_raw)
                    if name_match:
                        receiver_name = name_match.group(1).strip()
                    if id_match:
                        id_value = id_match.group(1).strip()
                        if '@s.whatsapp.net' in id_value:
                            phone_match = re.search(r'(\d+)', id_value)
                            if phone_match:
                                receiver_id = phone_match.group(1).strip()
                        else:
                            receiver_id = id_value
                    if not receiver_name:
                        receiver_name = receiver_raw
                
                if not receiver_id:
                    receiver_id = self._clean(row.get('Recipient ID', ''))
                
                message_data = {
                    "file_id": file_id,
                    "platform": "Facebook",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": receiver_name,
                    "recipient_number": receiver_id,
                    "timestamp": self._clean(row.get('Timestamp', '')),
                    "thread_id": self._clean(row.get('Thread ID', '')),
                    "chat_id": self._clean(row.get('Chat ID', '')),
                    "message_id": self._generate_oxygen_message_id("facebook", row, file_id, idx),
                    "message_type": "text",
                    "direction": self._clean(row.get('Direction', '')),
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN FACEBOOK PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            
        except Exception as e:
            logger.error(f"[OXYGEN FACEBOOK PARSER] Error parsing Facebook messages from {sheet_name}: {e}", exc_info=True)
        
        return results

    def parse_axiom_chat_messages(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.info(f"[CHAT PARSER] Starting to parse chat messages from file_id={file_id}, file_path={file_path}")
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            logger.info(f"[CHAT PARSER] Total sheets found: {len(xls.sheet_names)}")
            logger.info(f"[CHAT PARSER] Available sheets: {', '.join(xls.sheet_names[:10])}...")
            
            platform_counts = {}
            
            if 'Telegram Messages - iOS' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Telegram Messages - iOS sheet, parsing...")
                telegram_results = self._parse_telegram_messages(file_path, 'Telegram Messages - iOS', file_id)
                results.extend(telegram_results)
                platform_counts['Telegram'] = platform_counts.get('Telegram', 0) + len(telegram_results)
                logger.info(f"[CHAT PARSER] Telegram Messages - iOS: Parsed {len(telegram_results)} messages")
            else:
                logger.debug(f"[CHAT PARSER] Telegram Messages - iOS sheet not found")

            if 'Telegram Messages - Android' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Telegram Messages - Android sheet, parsing...")
                telegram_android_results = self._parse_telegram_messages(file_path, 'Telegram Messages - Android', file_id)
                results.extend(telegram_android_results)
                platform_counts['Telegram'] = platform_counts.get('Telegram', 0) + len(telegram_android_results)
                logger.info(f"[CHAT PARSER] Telegram Messages - Android: Parsed {len(telegram_android_results)} messages")
            else:
                logger.debug(f"[CHAT PARSER] Telegram Messages - Android sheet not found")
            
            if 'Instagram Direct Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Instagram Direct Messages sheet, parsing...")
                instagram_results = self._parse_instagram_messages(file_path, 'Instagram Direct Messages', file_id)
                results.extend(instagram_results)
                platform_counts['Instagram'] = len(instagram_results)
                logger.info(f"[CHAT PARSER] Instagram: Parsed {len(instagram_results)} messages")
            else:
                logger.warning(f"[CHAT PARSER] Instagram Direct Messages sheet not found")
            
            if 'TikTok Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found TikTok Messages sheet, parsing...")
                tiktok_results = self._parse_tiktok_messages(file_path, 'TikTok Messages', file_id)
                results.extend(tiktok_results)
                platform_counts['TikTok'] = len(tiktok_results)
                logger.info(f"[CHAT PARSER] TikTok: Parsed {len(tiktok_results)} messages")
            else:
                logger.warning(f"[CHAT PARSER] TikTok Messages sheet not found")

            if 'Twitter Direct Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Twitter Direct Messages sheet, parsing...")
                twitter_results = self._parse_twitter_messages(file_path, 'Twitter Direct Messages', file_id)
                results.extend(twitter_results)
                platform_counts['Twitter/X'] = len(twitter_results)
                logger.info(f"[CHAT PARSER] Twitter/X: Parsed {len(twitter_results)} messages")
            else:
                logger.warning(f"[CHAT PARSER] Twitter Direct Messages sheet not found")
            
            if 'Facebook Messenger Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Facebook Messenger Messages sheet, parsing...")
                facebook_results = self._parse_facebook_messages(file_path, 'Facebook Messenger Messages', file_id)
                results.extend(facebook_results)
                platform_counts['Facebook'] = len(facebook_results)
                logger.info(f"[CHAT PARSER] Facebook Messenger Messages: Parsed {len(facebook_results)} messages")
            else:
                logger.debug(f"[CHAT PARSER] Facebook Messenger Messages sheet not found")
            
            if 'WhatsApp Messages - Android' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found WhatsApp Messages - Android sheet, parsing...")
                whatsapp_android_results = self._parse_whatsapp_messages(file_path, 'WhatsApp Messages - Android', file_id)
                results.extend(whatsapp_android_results)
                platform_counts['WhatsApp'] = platform_counts.get('WhatsApp', 0) + len(whatsapp_android_results)
                logger.info(f"[CHAT PARSER] WhatsApp Messages - Android: Parsed {len(whatsapp_android_results)} messages")
            else:
                logger.debug(f"[CHAT PARSER] WhatsApp Messages - Android sheet not found")
            
            if 'WhatsApp Messages - iOS' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found WhatsApp Messages - iOS sheet, parsing...")
                whatsapp_ios_results = self._parse_whatsapp_messages(file_path, 'WhatsApp Messages - iOS', file_id)
                results.extend(whatsapp_ios_results)
                platform_counts['WhatsApp'] = platform_counts.get('WhatsApp', 0) + len(whatsapp_ios_results)
                logger.info(f"[CHAT PARSER] WhatsApp Messages - iOS: Parsed {len(whatsapp_ios_results)} messages")
            else:
                logger.debug(f"[CHAT PARSER] WhatsApp Messages - iOS sheet not found")
            
            if 'Android WhatsApp Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Android WhatsApp Messages sheet, parsing...")
                android_whatsapp_results = self._parse_whatsapp_messages(file_path, 'Android WhatsApp Messages', file_id)
                results.extend(android_whatsapp_results)
                platform_counts['WhatsApp'] = platform_counts.get('WhatsApp', 0) + len(android_whatsapp_results)
                logger.info(f"[CHAT PARSER] Android WhatsApp Messages: Parsed {len(android_whatsapp_results)} messages")
            else:
                logger.debug(f"[CHAT PARSER] Android WhatsApp Messages sheet not found")
            
            if 'iOS WhatsApp Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found iOS WhatsApp Messages sheet, parsing...")
                ios_whatsapp_results = self._parse_whatsapp_messages(file_path, 'iOS WhatsApp Messages', file_id)
                results.extend(ios_whatsapp_results)
                platform_counts['WhatsApp'] = platform_counts.get('WhatsApp', 0) + len(ios_whatsapp_results)
                logger.info(f"[CHAT PARSER] iOS WhatsApp Messages: Parsed {len(ios_whatsapp_results)} messages")
            else:
                logger.debug(f"[CHAT PARSER] iOS WhatsApp Messages sheet not found")
            
            logger.info(f"[CHAT PARSER] Total parsed messages: {len(results)}")
            if platform_counts:
                platform_summary = ", ".join([f"{platform}: {count}" for platform, count in platform_counts.items()])
                logger.info(f"[CHAT PARSER] Breakdown by platform: {platform_summary}")

            if results:
                sample_msg = results[0]
                logger.debug(f"[CHAT PARSER] Sample message data: platform={sample_msg.get('platform')}, "
                           f"sheet_name={sample_msg.get('sheet_name')}, "
                           f"message_id={sample_msg.get('message_id')}, "
                           f"from={sample_msg.get('from_name')}, "
                           f"to={sample_msg.get('to_name')}, "
                           f"timestamp={sample_msg.get('timestamp')}")
            
            saved_count = 0
            skipped_count = 0
            for msg in results:
                existing = (
                    self.db.query(ChatMessage)
                    .filter(
                        ChatMessage.file_id == msg["file_id"],
                        ChatMessage.platform == msg["platform"],
                        ChatMessage.message_id == msg["message_id"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(ChatMessage(**msg))
                    saved_count += 1
                else:
                    skipped_count += 1
            
            self.db.commit()
            logger.info(f"[CHAT PARSER] Successfully saved {saved_count} chat messages to database (skipped {skipped_count} duplicates)")
            print(f"Successfully saved {saved_count} chat messages to database (skipped {skipped_count} duplicates)")
            
        except Exception as e:
            logger.error(f"[CHAT PARSER] Error parsing Axiom chat messages: {e}", exc_info=True)
            print(f"Error parsing Axiom chat messages: {e}")
            self.db.rollback()
            raise e
        
        return results

    def _parse_telegram_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[TELEGRAM PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            total_rows = len(df)
            logger.debug(f"[TELEGRAM PARSER] Sheet loaded: {total_rows} rows, columns: {list(df.columns)[:10]}")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                if sheet_name == 'Telegram Messages - Android' and 'Message Body' in df.columns:
                    message_text = str(row.get('Message Body', '')).strip() if self._not_na(row.get('Message Body')) else ''
                else:
                    message_text = str(row.get('Message', '')).strip() if self._not_na(row.get('Message')) else ''
                
                if sheet_name == 'Telegram Messages - Android':
                    message_id = str(row.get('Item ID', '')).strip() if self._not_na(row.get('Item ID')) else ''
                    message_type = str(row.get('Type', 'text')).strip() if self._not_na(row.get('Type')) else 'text'
                else:
                    message_type = str(row.get('Type', '')).strip().lower() if self._not_na(row.get('Type')) else ''
                    message_id = str(row.get('Message ID', '')).strip() if self._not_na(row.get('Message ID')) else ''
                
                if not message_text:
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[TELEGRAM PARSER] Row {idx} skipped: No message text")
                    continue
                
                if sheet_name == 'Telegram Messages - Android':
                    direction_raw = str(row.get('Direction', '')).strip() if self._not_na(row.get('Direction')) else ''
                    direction = self._normalize_direction(direction_raw)
                    
                    chat_id = str(row.get('_ChatId', '')).strip() if self._not_na(row.get('_ChatId')) else ''
                    
                    thread_id = chat_id
                    if not thread_id:
                        sender_id = str(row.get('Sender ID', '')).strip() if self._not_na(row.get('Sender ID')) else ''
                        recipient_id = str(row.get('Recipient ID', '')).strip() if self._not_na(row.get('Recipient ID')) else ''
                        if sender_id and recipient_id:
                            participants = sorted([sender_id, recipient_id])
                            thread_id = "_".join(participants)
                            if not chat_id:
                                chat_id = thread_id
                        elif sender_id or recipient_id:
                            thread_id = sender_id or recipient_id
                            if not chat_id:
                                chat_id = thread_id
                    
                    message_data = {
                        "file_id": file_id,
                        "platform": "Telegram",
                        "message_text": message_text,
                        "from_name": str(row.get('Sender', '')).strip() if self._not_na(row.get('Sender')) else '',
                        "sender_number": str(row.get('Sender ID', '')).strip() if self._not_na(row.get('Sender ID')) else '',
                        "to_name": str(row.get('Recipient', '')).strip() if self._not_na(row.get('Recipient')) else '',
                        "recipient_number": str(row.get('Recipient ID', '')).strip() if self._not_na(row.get('Recipient ID')) else '',
                        "timestamp": str(row.get('Created Date/Time - UTC+00:00 (dd/MM/yyyy)', '')).strip() if self._not_na(row.get('Created Date/Time - UTC+00:00 (dd/MM/yyyy)')) else str(row.get('Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)', '')).strip() if self._not_na(row.get('Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)')) else '',
                        "thread_id": thread_id,
                        "chat_id": chat_id,
                        "message_id": message_id or f"telegram_{file_id}_{idx}",
                        "message_type": message_type,
                        "direction": direction,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name
                    }
                else:
                    message_status = str(row.get('Message Status', '')).strip()
                    direction = ''
                    if message_status.lower() == 'received':
                        direction = 'Incoming'
                    elif message_status.lower() == 'sent':
                        direction = 'Outgoing'
                    else:
                        direction_raw = str(row.get('Direction', '')).strip() if self._not_na(row.get('Direction')) else ''
                        direction = self._normalize_direction(direction_raw)
                    
                    message_data = {
                        "file_id": file_id,
                        "platform": "Telegram",
                        "message_text": message_text,
                        "from_name": str(row.get('Sender Name', '')),
                        "sender_number": str(row.get('Sender ID', '')),
                        "to_name": str(row.get('Recipient Name', '')),
                        "recipient_number": str(row.get('Recipient ID', '')),
                        "timestamp": str(row.get('Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                        "thread_id": str(row.get('_ThreadID', '')),
                        "chat_id": str(row.get('Chat ID', '')),
                        "message_id": message_id or f"telegram_{file_id}_{idx}",
                        "message_type": str(row.get('Type', 'text')),
                        "direction": direction,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name
                    }
                
                if processed_count == 0:
                    logger.debug(f"[TELEGRAM PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"from={message_data['from_name']}, to={message_data['to_name']}, "
                               f"text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[TELEGRAM PARSER] Total rows in sheet: {total_rows}, Processed: {processed_count}, Skipped: {skipped_count}")
        
        except Exception as e:
            logger.error(f"[TELEGRAM PARSER] Error parsing Telegram messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Telegram messages: {e}")
        
        return results

    def _parse_instagram_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[INSTAGRAM PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            total_rows = len(df)
            logger.debug(f"[INSTAGRAM PARSER] Sheet loaded: {total_rows} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = str(row.get('Message', '')).strip() if self._not_na(row.get('Message')) else ''
                
                if not message_text:
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[INSTAGRAM PARSER] Row {idx} skipped: No message text")
                    continue
                
                timestamp = ''
                timestamp_columns = [
                    'Message Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Created Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Timestamp',
                    'Date/Time'
                ]
                for col in timestamp_columns:
                    if col in df.columns:
                        timestamp = str(row.get(col, '')).strip() if self._not_na(row.get(col)) else ''
                        if timestamp:
                            break
                
                sender_name = str(row.get('Sender', '')).strip() if self._not_na(row.get('Sender')) else ''
                recipient_name = str(row.get('Recipient', '')).strip() if self._not_na(row.get('Recipient')) else ''
                
                direction = str(row.get('Direction', '')).strip() if self._not_na(row.get('Direction')) else ''
                
                thread_id = str(row.get('_ThreadID', '')).strip() if self._not_na(row.get('_ThreadID')) else ''

                chat_id = str(row.get('Chat ID', '')).strip() if self._not_na(row.get('Chat ID')) else ''
                
                if not thread_id and not chat_id:
                    participants = sorted([p for p in [sender_name, recipient_name] if p])
                    if len(participants) >= 2:
                        chat_id = "_".join(participants)
                        thread_id = chat_id
                    elif participants:
                        chat_id = participants[0]
                        thread_id = chat_id
                
                if not chat_id and thread_id:
                    chat_id = thread_id
                
                if not thread_id and chat_id:
                    thread_id = chat_id
                
                item_id = str(row.get('Item ID', '')).strip() if self._not_na(row.get('Item ID')) else ''
                message_id = item_id or f"instagram_{file_id}_{idx}"
                
                message_type = str(row.get('Type', 'text')).strip() if self._not_na(row.get('Type')) else 'text'
                
                message_data = {
                    "file_id": file_id,
                    "platform": "Instagram",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": "",
                    "to_name": recipient_name,
                    "recipient_number": "",
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "message_type": message_type,
                    "direction": direction,
                    "source_tool": "Magnet Axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[INSTAGRAM PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"from={message_data['from_name']}, to={message_data['to_name']}")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[INSTAGRAM PARSER] Total rows in sheet: {total_rows}, Processed: {processed_count}, Skipped: {skipped_count}")
        
        except Exception as e:
            logger.error(f"[INSTAGRAM PARSER] Error parsing Instagram messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Instagram messages: {e}")
        
        return results

    def _parse_tiktok_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[TIKTOK PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            total_rows = len(df)
            logger.debug(f"[TIKTOK PARSER] Sheet loaded: {total_rows} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = str(row.get('Message', '')).strip() if self._not_na(row.get('Message')) else ''
                message_type = str(row.get('Message Type', '')).strip().lower() if self._not_na(row.get('Message Type')) else ''
                item_id = str(row.get('Item ID', '')).strip() if self._not_na(row.get('Item ID')) else ''
                
                if not message_text:
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[TIKTOK PARSER] Row {idx} skipped: No message text")
                    continue
                
                timestamp = ''
                timestamp_columns = [
                    'Created Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Message Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Timestamp',
                    'Date/Time'
                ]
                for col in timestamp_columns:
                    if col in df.columns:
                        timestamp = str(row.get(col, '')).strip() if self._not_na(row.get(col)) else ''
                        if timestamp:
                            break
                
                direction_raw = str(row.get('Direction', '')).strip() if self._not_na(row.get('Direction')) else ''
                direction = self._normalize_direction(direction_raw)
                
                message_data = {
                    "file_id": file_id,
                    "platform": "TikTok",
                    "message_text": message_text,
                    "from_name": str(row.get('Sender', '')).strip() if self._not_na(row.get('Sender')) else '',
                    "sender_number": "",
                    "to_name": str(row.get('Recipient', '')).strip() if self._not_na(row.get('Recipient')) else '',
                    "recipient_number": "",
                    "timestamp": timestamp,
                    "thread_id": str(row.get('_ThreadID', '')).strip() if self._not_na(row.get('_ThreadID')) else '',
                    "chat_id": "",
                    "message_id": item_id or f"tiktok_{file_id}_{idx}",
                    "message_type": str(row.get('Message Type', 'text')).strip() if self._not_na(row.get('Message Type')) else 'text',
                    "direction": direction,
                    "source_tool": "Magnet Axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[TIKTOK PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"from={message_data['from_name']}, to={message_data['to_name']}")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[TIKTOK PARSER] Total rows in sheet: {total_rows}, Processed: {processed_count}, Skipped: {skipped_count}")
        
        except Exception as e:
            logger.error(f"[TIKTOK PARSER] Error parsing TikTok messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing TikTok messages: {e}")
        
        return results

    def _parse_twitter_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[TWITTER/X PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            total_rows = len(df)
            logger.debug(f"[TWITTER/X PARSER] Sheet loaded: {total_rows} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = str(row.get('Text', '')).strip() if self._not_na(row.get('Text')) else ''
                
                if not message_text:
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[TWITTER/X PARSER] Row {idx} skipped: No message text")
                    continue
                
                timestamp = ''
                timestamp_columns = [
                    'Sent/Received Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Message Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Created Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Timestamp',
                    'Date/Time'
                ]
                for col in timestamp_columns:
                    if col in df.columns:
                        timestamp = str(row.get(col, '')).strip() if self._not_na(row.get(col)) else ''
                        if timestamp:
                            break
                
                sender_id = str(row.get('Sender ID', '')).strip() if self._not_na(row.get('Sender ID')) else ''
                sender_name = str(row.get('Sender Name', '')).strip() if self._not_na(row.get('Sender Name')) else ''
                
                recipient_id = str(row.get('Recipient ID(s)', '')).strip() if self._not_na(row.get('Recipient ID(s)')) else ''
                recipient_name = str(row.get('Recipient Name(s)', '')).strip() if self._not_na(row.get('Recipient Name(s)')) else ''
                
                direction_raw = str(row.get('Direction', '')).strip() if self._not_na(row.get('Direction')) else ''
                direction = self._normalize_direction(direction_raw)
                
                thread_id = str(row.get('_ThreadID', '')).strip() if self._not_na(row.get('_ThreadID')) else ''
                
                chat_id = thread_id
                if not chat_id:
                    participants = sorted([p for p in [sender_id, recipient_id] if p])
                    if len(participants) >= 2:
                        chat_id = "_".join(participants)
                        thread_id = chat_id
                    elif participants:
                        chat_id = participants[0]
                        thread_id = chat_id
                
                item_id = str(row.get('Item ID', '')).strip() if self._not_na(row.get('Item ID')) else ''
                message_id = item_id or f"twitter_{file_id}_{idx}"
                
                message_data = {
                    "file_id": file_id,
                    "platform": "X",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": recipient_name,
                    "recipient_number": recipient_id,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "message_type": "text",
                    "direction": direction,
                    "source_tool": "Magnet Axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[TWITTER/X PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"from={message_data['from_name']}, to={message_data['to_name']}")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[TWITTER/X PARSER] Total rows in sheet: {total_rows}, Processed: {processed_count}, Skipped: {skipped_count}")
        
        except Exception as e:
            logger.error(f"[TWITTER/X PARSER] Error parsing Twitter messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Twitter messages: {e}")
        
        return results

    def _parse_facebook_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[FACEBOOK PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            total_rows = len(df)
            logger.debug(f"[FACEBOOK PARSER] Sheet loaded: {total_rows} rows, columns: {list(df.columns)[:10]}")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = str(row.get('Text', '')).strip() if self._not_na(row.get('Text')) else ''
                
                if not message_text:
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[FACEBOOK PARSER] Row {idx} skipped: No message text")
                    continue
                
                message_type = str(row.get('Message Type', '')).strip() if self._not_na(row.get('Message Type')) else ''
                if message_type.lower() == 'system':
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[FACEBOOK PARSER] Row {idx} skipped: System message")
                    continue
                
                timestamp = ''
                timestamp_columns = [
                    'Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Deleted Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Created Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Timestamp',
                    'Date/Time'
                ]
                for col in timestamp_columns:
                    if col in df.columns:
                        timestamp = str(row.get(col, '')).strip() if self._not_na(row.get(col)) else ''
                        if timestamp:
                            break
                
                sender_name = str(row.get('Sender Name', '')).strip() if self._not_na(row.get('Sender Name')) else ''
                sender_id_raw = str(row.get('Sender ID', '')).strip() if self._not_na(row.get('Sender ID')) else ''
                
                sender_id = sender_id_raw
                if sender_id and sender_id.startswith('FACEBOOK:'):
                    sender_id = sender_id.replace('FACEBOOK:', '', 1).strip()
                
                receiver_name = str(row.get('Receiver Name', '')).strip() if self._not_na(row.get('Receiver Name')) else ''
                receiver_id_raw = str(row.get('Receiver ID', '')).strip() if self._not_na(row.get('Receiver ID')) else ''
                
                receiver_id = receiver_id_raw
                if receiver_id and receiver_id.startswith('FACEBOOK:'):
                    receiver_id = receiver_id.replace('FACEBOOK:', '', 1).strip()
                
                direction = ''
                
                send_state = str(row.get('Send State', '')).strip() if self._not_na(row.get('Send State')) else ''
                if send_state:
                    send_state_lower = send_state.lower()
                    if 'sent' in send_state_lower:
                        direction = 'Outgoing'
                    elif 'received' in send_state_lower or 'incoming' in send_state_lower:
                        direction = 'Incoming'
                
                if not direction and 'Direction' in df.columns:
                    direction_raw = str(row.get('Direction', '')).strip() if self._not_na(row.get('Direction')) else ''
                    direction = self._normalize_direction(direction_raw)
                
                thread_id_raw = str(row.get('Thread ID', '')).strip() if self._not_na(row.get('Thread ID')) else ''
                
                thread_id = thread_id_raw
                if thread_id and thread_id.startswith('ONE_TO_ONE:'):
                    thread_id = thread_id.replace('ONE_TO_ONE:', '', 1).strip()
                
                chat_id = thread_id
                if not chat_id:
                    participants = sorted([p for p in [sender_id, receiver_id] if p])
                    if len(participants) >= 2:
                        chat_id = "_".join(participants)
                        thread_id = chat_id
                    elif participants:
                        chat_id = participants[0]
                        thread_id = chat_id
                    elif sender_name and receiver_name:
                        participants = sorted([sender_name, receiver_name])
                        if len(participants) >= 2:
                            chat_id = "_".join(participants)
                            thread_id = chat_id
                
                message_id = str(row.get('Message ID', '')).strip() if self._not_na(row.get('Message ID')) else ''
                item_id = str(row.get('Item ID', '')).strip() if self._not_na(row.get('Item ID')) else ''
                
                if not message_id:
                    message_id = item_id or f"facebook_{file_id}_{idx}"
                
                if not message_type:
                    message_type = 'text'
                
                message_data = {
                    "file_id": file_id,
                    "platform": "Facebook",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_id,
                    "to_name": receiver_name,
                    "recipient_number": receiver_id,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "message_type": message_type,
                    "direction": direction,
                    "source_tool": "Magnet Axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[FACEBOOK PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"from={message_data['from_name']}, to={message_data['to_name']}, "
                               f"text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[FACEBOOK PARSER] Total rows in sheet: {total_rows}, Processed: {processed_count}, Skipped: {skipped_count}")
        
        except Exception as e:
            logger.error(f"[FACEBOOK PARSER] Error parsing Facebook messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Facebook messages: {e}")
        
        return results

    def _parse_whatsapp_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[WHATSAPP PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            total_rows = len(df)
            logger.debug(f"[WHATSAPP PARSER] Sheet loaded: {total_rows} rows, columns: {list(df.columns)[:10]}")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = ''
                if 'Message' in df.columns:
                    message_text = str(row.get('Message', '')).strip() if self._not_na(row.get('Message')) else ''
                elif 'Text' in df.columns:
                    message_text = str(row.get('Text', '')).strip() if self._not_na(row.get('Text')) else ''
                
                if not message_text:
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[WHATSAPP PARSER] Row {idx} skipped: No message text")
                    continue
                
                if self._is_whatsapp_system_message(message_text):
                    skipped_count += 1
                    if skipped_count <= 5:
                        logger.debug(f"[WHATSAPP PARSER] Row {idx} skipped: WhatsApp system message")
                    continue
                
                if sheet_name == 'WhatsApp Messages - Android':
                    sender_name = ''
                    if 'Sender Nickname' in df.columns:
                        sender_name = str(row.get('Sender Nickname', '')).strip() if self._not_na(row.get('Sender Nickname')) else ''
                    
                    sender_number = ''
                    sender_raw = str(row.get('Sender', '')) if self._not_na(row.get('Sender')) else ''
                    if '@s.whatsapp.net' in sender_raw:
                        phone_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', sender_raw)
                        if phone_match:
                            sender_number = phone_match.group(1)
                    else:
                        phone_match = re.search(r'(\+?[0-9]{10,15})', sender_raw)
                        if phone_match:
                            sender_number = phone_match.group(1)
                    
                    recipient_name = ''
                    if 'Recipient Nickname' in df.columns:
                        recipient_name = str(row.get('Recipient Nickname', '')).strip() if self._not_na(row.get('Recipient Nickname')) else ''
                    
                    recipient_number = ''
                    recipient_raw = str(row.get('Recipient', '')) if self._not_na(row.get('Recipient')) else ''
                    if '@s.whatsapp.net' in recipient_raw:
                        phone_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', recipient_raw)
                        if phone_match:
                            recipient_number = phone_match.group(1)
                    else:
                        phone_match = re.search(r'(\+?[0-9]{10,15})', recipient_raw)
                        if phone_match:
                            recipient_number = phone_match.group(1)
                else:
                    sender_raw = str(row.get('Sender', '')) if self._not_na(row.get('Sender')) else ''
                    sender_name = ''
                    sender_number = ''
                    
                    if '@s.whatsapp.net' in sender_raw:
                        phone_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', sender_raw)
                        if phone_match:
                            sender_number = phone_match.group(1)
                            sender_name = sender_number
                        else:
                            sender_name = sender_raw.replace('@s.whatsapp.net', '').strip()
                    else:
                        sender_name = sender_raw.strip()
                        phone_match = re.search(r'(\+?[0-9]{10,15})', sender_name)
                        if phone_match:
                            sender_number = phone_match.group(1)
                    
                    recipient_raw = str(row.get('Recipient', '')) if self._not_na(row.get('Recipient')) else ''
                    recipient_name = ''
                    recipient_number = ''
                    
                    if '@s.whatsapp.net' in recipient_raw:
                        phone_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', recipient_raw)
                        if phone_match:
                            recipient_number = phone_match.group(1)
                            recipient_name = recipient_number
                        else:
                            recipient_name = recipient_raw.replace('@s.whatsapp.net', '').strip()
                    else:
                        recipient_name = recipient_raw.strip()
                        phone_match = re.search(r'(\+?[0-9]{10,15})', recipient_name)
                        if phone_match:
                            recipient_number = phone_match.group(1)
                
                timestamp = ''
                timestamp_columns = [
                    'Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Message Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Created Date/Time - UTC+00:00 (dd/MM/yyyy)',
                    'Timestamp',
                    'Date/Time',
                    'Time stamp (UTC 0)'
                ]
                for col in timestamp_columns:
                    if col in df.columns:
                        timestamp = str(row.get(col, '')).strip() if self._not_na(row.get(col)) else ''
                        if timestamp:
                            break
                
                direction_raw = str(row.get('Direction', '')).strip() if self._not_na(row.get('Direction')) else ''
                direction = self._normalize_direction(direction_raw)
                
                if not direction and 'Message Status' in df.columns:
                    status = str(row.get('Message Status', '')).strip().lower() if self._not_na(row.get('Message Status')) else ''
                    if 'received' in status:
                        direction = 'Incoming'
                    elif 'sent' in status:
                        direction = 'Outgoing'
                
                message_id = ''
                id_columns = ['Message ID', 'Item ID', 'ID']
                for col in id_columns:
                    if col in df.columns:
                        message_id = str(row.get(col, '')).strip() if self._not_na(row.get(col)) else ''
                        if message_id:
                            break
                
                if not message_id:
                    message_id = f"whatsapp_{file_id}_{idx}"
                
                if sheet_name == 'WhatsApp Messages - Android':
                    thread_id = ''
                    chat_id = ''
                    
                    participants = []
                    if sender_number:
                        participants.append(sender_number)
                    elif sender_name:
                        participants.append(sender_name)
                    
                    if recipient_number:
                        participants.append(recipient_number)
                    elif recipient_name:
                        participants.append(recipient_name)
                    
                    if len(participants) >= 2:
                        participants_sorted = sorted(set(participants))
                        thread_id = "_".join(participants_sorted)
                        chat_id = thread_id
                    elif len(participants) == 1:
                        thread_id = participants[0]
                        chat_id = thread_id
                    else:
                        thread_id = message_id or f"whatsapp_{file_id}_{idx}"
                        chat_id = thread_id
                else:
                    thread_id = str(row.get('_ThreadID', '')).strip() if self._not_na(row.get('_ThreadID')) else ''
                    chat_id = str(row.get('Chat ID', '')).strip() if self._not_na(row.get('Chat ID')) else ''
                    
                    if not thread_id and not chat_id:
                        participants = sorted([p for p in [sender_number or sender_name, recipient_number or recipient_name] if p])
                        if len(participants) >= 2:
                            chat_id = "_".join(participants[:2])
                            thread_id = chat_id
                        elif sender_number or recipient_number:
                            chat_id = sender_number or recipient_number
                            thread_id = chat_id
                
                message_type = str(row.get('Type', 'text')).strip() if self._not_na(row.get('Type')) else 'text'
                
                message_data = {
                    "file_id": file_id,
                    "platform": "WhatsApp",
                    "message_text": message_text,
                    "from_name": sender_name,
                    "sender_number": sender_number,
                    "to_name": recipient_name,
                    "recipient_number": recipient_number,
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "message_type": message_type,
                    "direction": direction,
                    "source_tool": "Magnet Axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[WHATSAPP PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"from={message_data['from_name']}, to={message_data['to_name']}, "
                               f"text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[WHATSAPP PARSER] Total rows in sheet: {total_rows}, Processed: {processed_count}, Skipped: {skipped_count}")
        
        except Exception as e:
            logger.error(f"[WHATSAPP PARSER] Error parsing WhatsApp messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing WhatsApp messages: {e}")
        
        return results

