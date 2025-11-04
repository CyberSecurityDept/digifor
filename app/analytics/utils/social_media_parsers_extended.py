import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.analytics.device_management.models import SocialMedia, ChatMessage
from sqlalchemy import or_
from app.analytics.utils.chat_messages_parser_extended import ChatMessagesParserExtended
import logging

logger = logging.getLogger(__name__)

class SocialMediaParsersExtended:
    
    def __init__(self, db: Session):
        self.db = db
        self._chat_messages_parser = ChatMessagesParserExtended(db)
    
    def _clean(self, text: Any) -> Optional[str]:
        if text is None or pd.isna(text):
            return None
        text = str(text).strip()
        if text.lower() in ["", "nan", "none", "null", "n/a", "none"]:
            return None
        return text
    
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
            'twitter': 'X'  # Twitter is now X
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
    
    def _check_existing_social_media(self, acc: Dict[str, Any]) -> bool:
        file_id = acc.get("file_id")
        if not file_id:
            return False
        
        query = self.db.query(SocialMedia).filter(SocialMedia.file_id == file_id)
        
        filters = []
        
        if acc.get("instagram_id"):
            filters.append(SocialMedia.instagram_id == acc["instagram_id"])
        if acc.get("facebook_id"):
            filters.append(SocialMedia.facebook_id == acc["facebook_id"])
        if acc.get("whatsapp_id"):
            filters.append(SocialMedia.whatsapp_id == acc["whatsapp_id"])
        if acc.get("telegram_id"):
            filters.append(SocialMedia.telegram_id == acc["telegram_id"])
        if acc.get("X_id"):
            filters.append(SocialMedia.X_id == acc["X_id"])
        if acc.get("tiktok_id"):
            filters.append(SocialMedia.tiktok_id == acc["tiktok_id"])
        
        if acc.get("account_name"):
            filters.append(SocialMedia.account_name == acc["account_name"])
        
        if not filters:
            return False
        
        existing = query.filter(or_(*filters)).first()
        
        return existing is not None
    
    def _validate_social_media_data(self, acc: Dict[str, Any]) -> tuple[bool, str]:
        return self._validate_social_media_data_new(acc)
    
    def _validate_social_media_data_new(self, acc: Dict[str, Any]) -> tuple[bool, str]:
        if not acc.get("file_id"):
            return False, "Missing file_id"
        
        has_identifier = (
            acc.get("instagram_id") or
            acc.get("facebook_id") or
            acc.get("whatsapp_id") or
            acc.get("telegram_id") or
            acc.get("X_id") or
            acc.get("tiktok_id") or
            acc.get("account_name")
        )
        
        if not has_identifier:
            return False, "Missing platform identifier or account_name"
        
        return True, ""
    
    def _convert_old_to_new_structure(self, acc: Dict[str, Any]) -> Dict[str, Any]:
        if "platform" not in acc:
            return acc
        
        new_acc = {
            "file_id": acc.get("file_id"),
            "source": acc.get("source") or acc.get("source_tool"),
            "phone_number": acc.get("phone_number"),
            "full_name": acc.get("full_name"),
            "account_name": acc.get("account_name"),
            "whatsapp_id": None,
            "telegram_id": None,
            "instagram_id": None,
            "X_id": None,
            "facebook_id": None,
            "tiktok_id": None,
            "sheet_name": acc.get("sheet_name"),
        }
        
        platform = acc.get("platform", "").lower()
        account_id = acc.get("account_id") or acc.get("user_id")
        
        if platform == "instagram":
            new_acc["instagram_id"] = account_id
        elif platform == "facebook":
            new_acc["facebook_id"] = account_id
        elif platform == "whatsapp":
            new_acc["whatsapp_id"] = account_id
        elif platform in ["x", "twitter"]:
            new_acc["X_id"] = account_id
        elif platform == "telegram":
            new_acc["telegram_id"] = account_id
        elif platform == "tiktok":
            new_acc["tiktok_id"] = account_id
        
        return new_acc

    def _extract_email(self, phones_emails_field: Optional[str]) -> Optional[str]:
        if not phones_emails_field:
            return None
            
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, phones_emails_field)
        if match:
            return match.group(0)
        
        return None

    def _extract_biography(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[str]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            patterns = [
                r'biography[:\s]*(.+?)(?:\n|$)',
                r'bio[:\s]*(.+?)(?:\n|$)',
                r'description[:\s]*(.+?)(?:\n|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    bio = match.group(1).strip()
                    if bio and len(bio) > 3:
                        return bio
        
        return None

    def _extract_profile_picture_url(self, internet_field: Optional[str]) -> Optional[str]:
        if not internet_field:
            return None
        
        url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif)'
        match = re.search(url_pattern, internet_field)
        if match:
            return match.group(0)
        
        return None

    def _extract_is_private(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[bool]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            if 'private' in field.lower():
                return True
            elif 'public' in field.lower():
                return False
        
        return None

    def _extract_is_local_user(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[bool]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            if 'local user' in field.lower():
                return True
        
        return None

    def _extract_last_message(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[str]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            patterns = [
                r'last\s+message[:\s]*(.+?)(?:\n|$)',
                r'last\s+msg[:\s]*(.+?)(?:\n|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    message = match.group(1).strip()
                    if message and len(message) > 3:
                        return message
        
        return None

    def _extract_other_info(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[str]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            patterns = [
                r'birthday[:\s]*(.+?)(?:\n|$)',
                r'age[:\s]*(.+?)(?:\n|$)',
                r'location[:\s]*(.+?)(?:\n|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    info = match.group(1).strip()
                    if info and len(info) > 1:
                        return info
        
        return None

    def _extract_user_id(self, internet_field: Optional[str], phones_emails_field: Optional[str], platform: str) -> Optional[str]:
        fields = [internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            patterns = []
            if platform.lower() == 'x' or platform.lower() == 'twitter':
                patterns = [r'x\s+id[:\s]*(\d+)', r'twitter\s+id[:\s]*(\d+)']
            elif platform.lower() == 'instagram':
                patterns = [r'instagram\s+id[:\s]*(\d+)']
            elif platform.lower() == 'telegram':
                patterns = [r'telegram\s+id[:\s]*(\d+)']
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    return match.group(1)
        
        return None

    def _extract_full_name(self, contact_field: Optional[str]) -> Optional[str]:
        if not contact_field:
            return None
            
        patterns = [
            r'full\s+name[:\s]*(.+?)(?:\n|$)',
            r'name[:\s]*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, contact_field.lower())
            if match:
                name = match.group(1).strip()
                if name and len(name) > 1:
                    return name
        
        return None

    def parse_axiom_social_media(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            print(f" Total sheets available: {len(xls.sheet_names)}")
            
            for sheet_name in xls.sheet_names:
                print(f"Processing sheet: {sheet_name}")
                
                if 'Instagram Profiles' in sheet_name:
                    results.extend(self._parse_axiom_instagram_profiles(file_path, sheet_name, file_id))
                elif 'Android Instagram Following' in sheet_name:
                    results.extend(self._parse_axiom_instagram_following(file_path, sheet_name, file_id))
                elif 'Android Instagram Users' in sheet_name:
                    results.extend(self._parse_axiom_instagram_users(file_path, sheet_name, file_id))
                
                elif 'Twitter Users' in sheet_name:
                    results.extend(self._parse_axiom_twitter_users(file_path, sheet_name, file_id))
                
                elif 'Telegram Accounts' in sheet_name:
                    results.extend(self._parse_axiom_telegram_accounts(file_path, sheet_name, file_id))
                elif 'User Accounts' in sheet_name:
                    results.extend(self._parse_axiom_user_accounts(file_path, sheet_name, file_id))
                
                elif 'TikTok Contacts' in sheet_name:
                    results.extend(self._parse_axiom_tiktok_contacts(file_path, sheet_name, file_id))
                
                elif 'Facebook Contacts' in sheet_name:
                    results.extend(self._parse_axiom_facebook_contacts(file_path, sheet_name, file_id))
                elif 'Facebook User-Friends' in sheet_name:
                    results.extend(self._parse_axiom_facebook_users(file_path, sheet_name, file_id))
                
                elif 'WhatsApp Contacts - Android' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_contacts(file_path, sheet_name, file_id))
                elif 'WhatsApp User Profiles - Androi' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_users(file_path, sheet_name, file_id))
                elif 'WhatsApp Accounts Information' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_accounts(file_path, sheet_name, file_id))
                
                elif 'Android WhatsApp Accounts Infor' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_accounts_info(file_path, sheet_name, file_id))
                elif 'Android WhatsApp Chats' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_chats(file_path, sheet_name, file_id))
                elif 'Android WhatsApp Contacts' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_contacts_android(file_path, sheet_name, file_id))
                elif 'Android WhatsApp Messages' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_messages(file_path, sheet_name, file_id))
                elif 'Android WhatsApp User Profiles' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_user_profiles(file_path, sheet_name, file_id))
                elif 'Telegram Chats - Android' in sheet_name:
                    results.extend(self._parse_axiom_telegram_chats(file_path, sheet_name, file_id))
                elif 'Telegram Contacts - Android' in sheet_name:
                    results.extend(self._parse_axiom_telegram_contacts_android(file_path, sheet_name, file_id))
                elif 'Telegram Messages - Android' in sheet_name:
                    results.extend(self._parse_axiom_telegram_messages(file_path, sheet_name, file_id))
                elif 'Telegram Users - Android' in sheet_name:
                    results.extend(self._parse_axiom_telegram_users_android(file_path, sheet_name, file_id))

            unique_results = []
            seen_accounts = set()
            
            for acc in results:
                platform_ids = []
                if acc.get('instagram_id'):
                    platform_ids.append(f"ig:{acc['instagram_id']}")
                if acc.get('facebook_id'):
                    platform_ids.append(f"fb:{acc['facebook_id']}")
                if acc.get('whatsapp_id'):
                    platform_ids.append(f"wa:{acc['whatsapp_id']}")
                if acc.get('telegram_id'):
                    platform_ids.append(f"tg:{acc['telegram_id']}")
                if acc.get('X_id'):
                    platform_ids.append(f"x:{acc['X_id']}")
                if acc.get('tiktok_id'):
                    platform_ids.append(f"tt:{acc['tiktok_id']}")
                account_key = f"{acc.get('account_name', '')}_{'_'.join(platform_ids)}"
                
                if account_key not in seen_accounts:
                    seen_accounts.add(account_key)
                    unique_results.append(acc)
            
            print(f"Removed {len(results) - len(unique_results)} duplicate records")
            print(f"Unique social media accounts: {len(unique_results)}")
            
            batch_size = 50
            saved_count = 0
            skipped_count = 0
            invalid_count = 0
            
            for i in range(0, len(unique_results), batch_size):
                batch = unique_results[i:i + batch_size]
                batch_saved = 0
                
                try:
                    for acc in batch:
                        if "platform" in acc:
                            acc = self._convert_old_to_new_structure(acc)
                        
                        is_valid, error_msg = self._validate_social_media_data(acc)
                        if not is_valid:
                            invalid_count += 1
                            if invalid_count <= 10:
                                platform_info = []
                                if acc.get('instagram_id'):
                                    platform_info.append(f"IG:{acc['instagram_id']}")
                                if acc.get('facebook_id'):
                                    platform_info.append(f"FB:{acc['facebook_id']}")
                                if acc.get('whatsapp_id'):
                                    platform_info.append(f"WA:{acc['whatsapp_id']}")
                                if acc.get('telegram_id'):
                                    platform_info.append(f"TG:{acc['telegram_id']}")
                                if acc.get('X_id'):
                                    platform_info.append(f"X:{acc['X_id']}")
                                if acc.get('tiktok_id'):
                                    platform_info.append(f"TT:{acc['tiktok_id']}")
                                platform_str = ', '.join(platform_info) if platform_info else 'Unknown'
                                print(f"⚠️  Skipping invalid record: {error_msg} - Platform IDs: {platform_str}, Account: {acc.get('account_name', 'N/A')}")
                            continue
                        
                        if self._check_existing_social_media(acc):
                            skipped_count += 1
                            continue
                        
                        self.db.add(SocialMedia(**acc))
                        batch_saved += 1
                    
                    self.db.commit()
                    saved_count += batch_saved
                    print(f"Saved batch {i//batch_size + 1}: {batch_saved}/{len(batch)} records inserted (Total saved: {saved_count}, Skipped: {skipped_count})")
                    
                except Exception as batch_error:
                    print(f"Error saving batch {i//batch_size + 1}: {batch_error}")
                    import traceback
                    traceback.print_exc()
                    self.db.rollback()
                    raise batch_error
            
            print(f"Successfully saved {saved_count} unique Axiom social media accounts to database")
            if skipped_count > 0:
                print(f"  ({skipped_count} records skipped - already exist)")
            if invalid_count > 0:
                print(f"  ({invalid_count} records skipped - invalid data)")
            
        except Exception as e:
            print(f"Error parsing Axiom social media: {e}")
            self.db.rollback()
            raise e
        
        return unique_results
    
    def count_axiom_social_media(self, file_path: str) -> int:
        try:
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in ['.xlsx', '.xls']:
                return 0
            
            if file_ext == '.xls':
                engine = 'xlrd'
            else:
                engine = 'openpyxl'
            
            xls = pd.ExcelFile(file_path, engine=engine)
            total_count = 0
            
            for sheet_name in xls.sheet_names:
                try:
                    if 'Instagram Profiles' in sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'User ID' in df.columns:
                            total_count += len(df[df['User ID'].notna()])
                    elif 'Twitter Users' in sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'User ID' in df.columns:
                            total_count += len(df[df['User ID'].notna()])
                    elif 'Telegram Accounts' in sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'Account ID' in df.columns:
                            total_count += len(df[df['Account ID'].notna()])
                    elif 'TikTok Contacts' in sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'ID' in df.columns:
                            total_count += len(df[df['ID'].notna()])
                    elif 'Facebook Contacts' in sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'Profile ID' in df.columns:
                            total_count += len(df[df['Profile ID'].notna()])
                    elif 'Facebook User-Friends' in sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'User ID' in df.columns:
                            total_count += len(df[df['User ID'].notna()])
                    elif 'WhatsApp Contacts' in sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'ID' in df.columns:
                            total_count += len(df[df['ID'].notna()])
                    elif 'WhatsApp User Profiles' in sheet_name:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'Phone Number' in df.columns:
                            total_count += len(df[df['Phone Number'].notna()])
                except Exception:
                    continue
            
            return total_count
            
        except Exception as e:
            return 0
    
    def parse_cellebrite_social_media(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if file_path.endswith('.xlsx'):
                engine = 'openpyxl'
            elif file_path.endswith('.xls'):
                engine = 'xlrd'
            else:
                engine = 'openpyxl'
            
            xls = pd.ExcelFile(file_path, engine=engine)
            
            print(f"Total sheets available: {len(xls.sheet_names)}")
            print(f"Sheet names: {xls.sheet_names}")
            
            if 'Contacts' in xls.sheet_names:
                print("Detected Contacts sheet - parsing Contacts only (skipping other sheets)")
                results.extend(self._parse_cellebrite_contacts_sheet(file_path, 'Contacts', file_id))
            
            elif 'Social Media' in xls.sheet_names:
                print("Detected Cellebrite format - parsing Social Media sheet")
                for sheet_name in xls.sheet_names:
                    print(f"Processing sheet: {sheet_name}")
                    
                    if sheet_name == 'Social Media':
                        results.extend(self._parse_cellebrite_social_media_sheet(file_path, sheet_name, file_id))
                    elif sheet_name == 'User Accounts':
                        results.extend(self._parse_cellebrite_user_accounts_sheet(file_path, sheet_name, file_id))
                    elif sheet_name == 'Chats':
                        results.extend(self._parse_cellebrite_chats_sheet(file_path, sheet_name, file_id))
                    else:
                        results.extend(self._parse_cellebrite_generic_sheet(file_path, sheet_name, file_id))
            
            elif any(keyword in ' '.join(xls.sheet_names).lower() for keyword in ['instagram', 'facebook', 'twitter', 'whatsapp', 'telegram', 'tiktok']):
                print("Detected Oxygen format - parsing dedicated social media sheets")
                results.extend(self.parse_oxygen_social_media(file_path, file_id))
            
            else:
                print("Unknown format - attempting generic parsing")
                for sheet_name in xls.sheet_names:
                    print(f"Processing sheet: {sheet_name}")
                    results.extend(self._parse_cellebrite_generic_sheet(file_path, sheet_name, file_id))
            
            unique_results = []
            seen_accounts = set()
            
            for acc in results:
                platform_ids = []
                if acc.get('instagram_id'):
                    platform_ids.append(f"ig:{acc['instagram_id']}")
                if acc.get('facebook_id'):
                    platform_ids.append(f"fb:{acc['facebook_id']}")
                if acc.get('whatsapp_id'):
                    platform_ids.append(f"wa:{acc['whatsapp_id']}")
                if acc.get('telegram_id'):
                    platform_ids.append(f"tg:{acc['telegram_id']}")
                if acc.get('X_id'):
                    platform_ids.append(f"x:{acc['X_id']}")
                if acc.get('tiktok_id'):
                    platform_ids.append(f"tt:{acc['tiktok_id']}")
                platform_str = '_'.join(platform_ids) if platform_ids else 'unknown'
                account_key = f"{platform_str}_{acc.get('account_name', '')}_{acc.get('file_id', '')}"
                
                if account_key not in seen_accounts:
                    seen_accounts.add(account_key)
                    unique_results.append(acc)
            
            print(f"Removed {len(results) - len(unique_results)} duplicate records")
            print(f"Unique social media accounts: {len(unique_results)}")
            
            batch_size = 50
            saved_count = 0
            skipped_count = 0
            invalid_count = 0
            
            for i in range(0, len(unique_results), batch_size):
                batch = unique_results[i:i + batch_size]
                batch_saved = 0
                
                try:
                    for acc in batch:
                        
                        is_valid, error_msg = self._validate_social_media_data(acc)
                        if not is_valid:
                            invalid_count += 1
                            if invalid_count <= 10:
                                
                                platform_info = []
                                if acc.get('instagram_id'):
                                    platform_info.append(f"IG:{acc['instagram_id']}")
                                if acc.get('facebook_id'):
                                    platform_info.append(f"FB:{acc['facebook_id']}")
                                if acc.get('whatsapp_id'):
                                    platform_info.append(f"WA:{acc['whatsapp_id']}")
                                if acc.get('telegram_id'):
                                    platform_info.append(f"TG:{acc['telegram_id']}")
                                if acc.get('X_id'):
                                    platform_info.append(f"X:{acc['X_id']}")
                                if acc.get('tiktok_id'):
                                    platform_info.append(f"TT:{acc['tiktok_id']}")
                                platform_str = ', '.join(platform_info) if platform_info else 'Unknown'
                                print(f"⚠️  Skipping invalid record: {error_msg} - Platform IDs: {platform_str}, Account: {acc.get('account_name', 'N/A')}")
                            continue
                        
                        if self._check_existing_social_media(acc):
                            skipped_count += 1
                            continue
                        
                        self.db.add(SocialMedia(**acc))
                        batch_saved += 1
                    
                    self.db.commit()
                    saved_count += batch_saved
                    print(f"Saved batch {i//batch_size + 1}: {batch_saved}/{len(batch)} records inserted (Total saved: {saved_count}, Skipped: {skipped_count})")
                    
                except Exception as batch_error:
                    print(f"Error saving batch {i//batch_size + 1}: {batch_error}")
                    import traceback
                    traceback.print_exc()
                    self.db.rollback()
                    raise batch_error
            
            print(f"Successfully saved {saved_count} unique Cellebrite social media accounts to database")
            if skipped_count > 0:
                print(f"  ({skipped_count} records skipped - already exist)")
            if invalid_count > 0:
                print(f"  ({invalid_count} records skipped - invalid data)")
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error parsing Cellebrite social media: {e}")
            self.db.rollback()
            raise e
        
        return unique_results
    
    def _parse_cellebrite_social_media_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('#', '')) or str(row.get('#', '')).strip() == '#':
                    continue
                
                source = self._clean(row.get('Source', ''))
                author = self._clean(row.get('Author', ''))
                body = self._clean(row.get('Body', ''))
                url = self._clean(row.get('URL', ''))
                account = self._clean(row.get('Account', ''))
                
                if source and source.lower() == 'instagram':
                    if author and account:
                        parts = author.split()
                        user_id = parts[0] if parts else account
                        account_name = ' '.join(parts[1:]) if len(parts) > 1 else account
                        
                        acc = {
                            "file_id": file_id,
                            "source": source,
                            "account_name": account_name,
                            "full_name": account_name,
                            "instagram_id": user_id,
                            "whatsapp_id": None,
                            "telegram_id": None,
                            "X_id": None,
                            "facebook_id": None,
                            "tiktok_id": None,
                            "sheet_name": sheet_name,
                        }
                        results.append(acc)
                
                elif source and source.lower() == 'facebook':
                    if author and account:
                        parts = author.split()
                        user_id = parts[0] if parts else account
                        account_name = ' '.join(parts[1:]) if len(parts) > 1 else account
                        
                        acc = {
                            "file_id": file_id,
                            "source": source,
                            "account_name": account_name,
                            "full_name": account_name,
                            "facebook_id": user_id,
                            "whatsapp_id": None,
                            "telegram_id": None,
                            "instagram_id": None,
                            "X_id": None,
                            "tiktok_id": None,
                            "sheet_name": sheet_name,
                        }
                        results.append(acc)
                
                elif source and source.lower() == 'twitter':
                    if author and account:
                        parts = author.split()
                        user_id = parts[0] if parts else account
                        account_name = ' '.join(parts[1:]) if len(parts) > 1 else account
                        
                        acc = {
                            "file_id": file_id,
                            "source": source,
                            "account_name": account_name,
                            "full_name": account_name,
                            "X_id": user_id,
                            "whatsapp_id": None,
                            "telegram_id": None,
                            "instagram_id": None,
                            "facebook_id": None,
                            "tiktok_id": None,
                            "sheet_name": sheet_name,
                        }
                        results.append(acc)
            
            print(f"Found {len(results)} social media accounts in {sheet_name} sheet")
            
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results
    
    def _parse_cellebrite_generic_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                for col_name, col_value in row.items():
                    if pd.isna(col_value) or not isinstance(col_value, str):
                        continue
                    
                    col_value_lower = col_value.lower()
                    
                    if 'tiktok' in col_value_lower:
                        tiktok_match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', col_value)
                        if tiktok_match:
                            username = tiktok_match.group(1)
                            acc = {
                                "file_id": file_id,
                                "source": "TikTok",
                                "account_name": username,
                                "full_name": username,
                                "tiktok_id": username,
                                "whatsapp_id": None,
                                "telegram_id": None,
                                "instagram_id": None,
                                "X_id": None,
                                "facebook_id": None,
                                "sheet_name": sheet_name,
                            }
                            results.append(acc)
                    
                    elif 'instagram' in col_value_lower:
                        instagram_match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', col_value)
                        if instagram_match:
                            username = instagram_match.group(1)
                            acc = {
                                "file_id": file_id,
                                "source": "Instagram",
                                "account_name": username,
                                "full_name": username,
                                "instagram_id": username,
                                "whatsapp_id": None,
                                "telegram_id": None,
                                "X_id": None,
                                "facebook_id": None,
                                "tiktok_id": None,
                                "sheet_name": sheet_name,
                            }
                            results.append(acc)
                    
                    elif 'whatsapp' in col_value_lower:
                        phone_number = None
                        if '@s.whatsapp.net' in col_value:
                            whatsapp_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', col_value)
                            if whatsapp_match:
                                phone_number = whatsapp_match.group(1)
                        if phone_number:
                            acc = {
                                "file_id": file_id,
                                "source": "WhatsApp",
                                "account_name": phone_number,
                                "full_name": phone_number,
                                "whatsapp_id": phone_number,
                                "phone_number": phone_number,
                                "telegram_id": None,
                                "instagram_id": None,
                                "X_id": None,
                                "facebook_id": None,
                                "tiktok_id": None,
                                "sheet_name": sheet_name,
                            }
                            results.append(acc)
                    
                    elif 'telegram' in col_value_lower:
                        telegram_match = re.search(r'@([a-zA-Z0-9_]+)', col_value)
                        if telegram_match:
                            username = telegram_match.group(1)
                            acc = {
                                "file_id": file_id,
                                "source": "Telegram",
                                "account_name": username,
                                "full_name": username,
                                "telegram_id": username,
                                "whatsapp_id": None,
                                "instagram_id": None,
                                "X_id": None,
                                "facebook_id": None,
                                "tiktok_id": None,
                                "sheet_name": sheet_name,
                            }
                            results.append(acc)
                    
                    elif 'twitter' in col_value_lower or 'x.com' in col_value_lower:
                        twitter_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', col_value)
                        if twitter_match:
                            username = twitter_match.group(1)
                            acc = {
                                "file_id": file_id,
                                "source": "X (Twitter)",
                                "account_name": username,
                                "full_name": username,
                                "X_id": username,
                                "whatsapp_id": None,
                                "telegram_id": None,
                                "instagram_id": None,
                                "facebook_id": None,
                                "tiktok_id": None,
                                "sheet_name": sheet_name,
                            }
                            results.append(acc)
                    
                    elif 'facebook' in col_value_lower:
                        facebook_match = re.search(r'facebook\.com/([a-zA-Z0-9_.]+)', col_value)
                        if facebook_match:
                            username = facebook_match.group(1)
                            acc = {
                                "file_id": file_id,
                                "source": "Facebook",
                                "account_name": username,
                                "full_name": username,
                                "facebook_id": username,
                                "whatsapp_id": None,
                                "telegram_id": None,
                                "instagram_id": None,
                                "X_id": None,
                                "tiktok_id": None,
                                "sheet_name": sheet_name,
                            }
                            results.append(acc)
            
            if results:
                print(f"Found {len(results)} social media accounts in {sheet_name} sheet")
            
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results
    
    def _parse_cellebrite_user_accounts_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('#', '')) or str(row.get('#', '')).strip() == '#':
                    continue
                
                username = self._clean(row.get('Username', ''))
                service_type = self._clean(row.get('Service Type', ''))
                account_name = self._clean(row.get('Account Name', ''))
                entries = self._clean(row.get('Entries', ''))
                source = self._clean(row.get('Source', ''))
                
                if not username or username.lower() == 'n/a':
                    continue

                platform = None
                service_type_lower = (service_type or '').lower()
                source_lower = (source or '').lower()
                
                if 'instagram' in service_type_lower or 'instagram' in source_lower:
                    platform = 'instagram'
                elif 'twitter' in service_type_lower or 'twitter' in source_lower or 'x' in service_type_lower or 'x' in source_lower:
                    platform = 'x'
                elif 'telegram' in service_type_lower or 'telegram' in source_lower:
                    platform = 'telegram'
                elif 'whatsapp' in service_type_lower or 'whatsapp' in source_lower:
                    platform = 'whatsapp'
                elif 'facebook' in service_type_lower or 'facebook' in source_lower:
                    platform = 'facebook'
                elif 'tiktok' in service_type_lower or 'tiktok' in source_lower:
                    platform = 'tiktok'
                
                if platform:
                    phone_number = None
                    email = None
                    profile_picture_url = None
                    user_id = None
                    
                    if entries and entries.lower() != 'n/a':
                        phone_patterns = [
                            r'Phone-([^\\n]+)',
                            r'Mobile: ([^\\n]+)',
                            r'Main: ([^\\n]+)',
                            r'Phone Number: ([^\\n]+)'
                        ]
                        for pattern in phone_patterns:
                            match = re.search(pattern, entries)
                            if match:
                                phone_number = match.group(1).strip()
                                break
                        
                        email_patterns = [
                            r'Email-([^\\n]+)',
                            r'Email: ([^\\n]+)',
                            r'Google Drive Account: ([^\\n]+)'
                        ]
                        for pattern in email_patterns:
                            match = re.search(pattern, entries)
                            if match:
                                email = match.group(1).strip()
                                break
                        
                        pic_patterns = [
                            r'Profile Picture-([^\\n]+)',
                            r'Profile Picture Url: ([^\\n]+)',
                            r'Pic Square: ([^\\n]+)',
                            r'profile_picture_url: ([^\\n]+)'
                        ]
                        for pattern in pic_patterns:
                            match = re.search(pattern, entries)
                            if match:
                                profile_picture_url = match.group(1).strip()
                                break
                        
                        id_patterns = [
                            r'User ID-([^\\n]+)',
                            r'User Id: ([^\\n]+)',
                            r'WhatsApp User Id: ([^\\n]+)',
                            r'Facebook Id: ([^\\n]+)'
                        ]
                        for pattern in id_patterns:
                            match = re.search(pattern, entries)
                            if match:
                                user_id = match.group(1).strip()
                                break

                    acc = {
                        "file_id": file_id,
                        "source": source or service_type,
                        "account_name": username,
                        "full_name": account_name if account_name and account_name.lower() != 'n/a' else username,
                        "phone_number": phone_number,
                        "sheet_name": sheet_name,
                        "whatsapp_id": None,
                        "telegram_id": None,
                        "instagram_id": None,
                        "X_id": None,
                        "facebook_id": None,
                        "tiktok_id": None,
                    }
                    
                    if platform == 'instagram':
                        acc['instagram_id'] = user_id or username
                    elif platform == 'facebook':
                        acc['facebook_id'] = user_id or username
                    elif platform == 'whatsapp':
                        acc['whatsapp_id'] = user_id or username
                    elif platform == 'x':
                        acc['X_id'] = user_id or username
                    elif platform == 'telegram':
                        acc['telegram_id'] = user_id or username
                    elif platform == 'tiktok':
                        acc['tiktok_id'] = user_id or username
                    
                    results.append(acc)
            
            print(f"Found {len(results)} social media accounts in {sheet_name} sheet")
            
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results
    
    def _parse_cellebrite_contacts_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            required_columns = ['Source', 'Entries']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"  Missing required columns in Contacts sheet: {missing_columns}")
                return results
            
            social_media_keywords = ['Instagram', 'WhatsApp', 'Twitter', 'Facebook', 'Telegram', 'Tiktok', 'X']
            
            for _, row in df.iterrows():
                if pd.isna(row.get('#', '')) or str(row.get('#', '')).strip() == '#':
                    continue
                
                source = self._clean(row.get('Source', ''))
                name = self._clean(row.get('Name', ''))
                entries = self._clean(row.get('Entries', ''))
                
                if not source:
                    continue
                
                source_lower = (source or '').lower()
                platform = None
                platform_id_field = None
                
                if 'instagram' in source_lower:
                    platform = 'instagram'
                    platform_id_field = 'instagram_id'
                elif 'whatsapp' in source_lower:
                    platform = 'whatsapp'
                    platform_id_field = 'whatsapp_id'
                elif 'twitter' in source_lower or 'x' in source_lower:
                    platform = 'x'
                    platform_id_field = 'X_id'
                elif 'facebook' in source_lower:
                    platform = 'facebook'
                    platform_id_field = 'facebook_id'
                elif 'telegram' in source_lower:
                    platform = 'telegram'
                    platform_id_field = 'telegram_id'
                elif 'tiktok' in source_lower:
                    platform = 'tiktok'
                    platform_id_field = 'tiktok_id'
                
                if not platform:
                    continue
                
                account_name = None
                platform_id = None
                phone_number = None
                
                if entries:
                    username_match = re.search(r'User\s+ID-Username[:\s]+([^\s\n\r]+)', entries, re.IGNORECASE)
                    if username_match:
                        account_name = username_match.group(1).strip()
                        print(f"  Found account_name from Entries: {account_name}")
                    
                    if platform == 'whatsapp':
                        whatsapp_user_id_match = re.search(r'User\s+ID-WhatsApp\s+User\s+Id[:\s]+([^\s\n\r]+)', entries, re.IGNORECASE)
                        if whatsapp_user_id_match:
                            whatsapp_user_id_full = whatsapp_user_id_match.group(1).strip()

                            if '@g.us' in whatsapp_user_id_full or '-' in whatsapp_user_id_full.replace('@s.whatsapp.net', ''):
                                print(f"  Skipping WhatsApp Group ID: {whatsapp_user_id_full} (not individual user)")
                                platform_id = None
                            else:
                                whatsapp_id_clean = whatsapp_user_id_full.replace('@s.whatsapp.net', '').strip()
                                platform_id = whatsapp_id_clean
                                print(f"  Found WhatsApp User Id from Entries: {platform_id}")
                        
                        phone_patterns = [
                            r'Phone-Mobile[:\s]+([^\s\n\r]+)',
                            r'Phone[:\s]+([^\s\n\r]+)',
                            r'Mobile[:\s]+([^\s\n\r]+)',
                            r'Phone\s+Number[:\s]+([^\s\n\r]+)',
                        ]
                        for phone_pattern in phone_patterns:
                            phone_match = re.search(phone_pattern, entries, re.IGNORECASE)
                            if phone_match:
                                phone_number = phone_match.group(1).strip()
                                print(f"  Found phone_number from Entries: {phone_number}")
                                break
                        
                        if not phone_number and platform_id:
                            phone_number = platform_id
                            print(f"  Using WhatsApp User Id as phone_number: {phone_number}")
                    
                    elif platform == 'facebook':
                        facebook_id_match = re.search(r'User\s+ID-Facebook\s+Id[:\s]+([^\s\n\r]+)', entries, re.IGNORECASE)
                        if facebook_id_match:
                            platform_id = facebook_id_match.group(1).strip()
                            print(f"  Found Facebook Id from Entries: {platform_id}")
                    
                    else:
                        user_id_match = re.search(r'User\s+ID-User\s+ID[:\s]+([^\s\n\r]+)', entries, re.IGNORECASE)
                        if not user_id_match:
                            user_id_match = re.search(r'User\s+ID-(?!Username|WhatsApp|Facebook)[:\s]+(\d+)', entries, re.IGNORECASE)
                        
                        if user_id_match:
                            platform_id = user_id_match.group(1).strip()
                            print(f"  Found platform_id from Entries: {platform_id} (platform: {platform})")
                            if not account_name:
                                print(f"  Note: account_name will be null (only User ID found, no User ID-Username)")
                
                full_name = name if name and name.lower() not in ['nan', 'none', 'null', ''] else None
                
                if platform == 'whatsapp':
                    phone_number_valid = False
                    if phone_number:
                        phone_clean = phone_number.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').strip()
                        if phone_clean and phone_clean != '0' and len(phone_clean) >= 10:
                            phone_number_valid = True

                    if not phone_number_valid or not platform_id:
                        missing_fields = []
                        if not phone_number_valid:
                            if phone_number:
                                missing_fields.append(f"phone_number (invalid: '{phone_number}' - too short or '0')")
                            else:
                                missing_fields.append("phone_number")
                        if not platform_id:
                            missing_fields.append("whatsapp_id")
                        print(f"  Skipping WhatsApp row: Missing required fields: {', '.join(missing_fields)}")
                        continue
                    
                if platform != 'whatsapp' and not account_name and not platform_id:
                    print(f"  Skipping row: No account_name and no platform_id found in Entries")
                    continue
                
                acc = {
                    "file_id": file_id,
                    "source": source,
                    "full_name": full_name,
                    "account_name": account_name,
                    "phone_number": phone_number,
                    "sheet_name": sheet_name,
                    "whatsapp_id": None,
                    "telegram_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }

                if platform_id:
                    acc[platform_id_field] = platform_id
                    print(f"  Inserting record: account_name={account_name}, {platform_id_field}={platform_id}, phone_number={phone_number}")
                else:
                    print(f"  Inserting record: account_name={account_name}, phone_number={phone_number}")
                
                results.append(acc)
            
            if results:
                print(f"Found {len(results)} social media accounts in {sheet_name} sheet")
            
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def _parse_cellebrite_chats_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('#', '')) or str(row.get('#', '')).strip() == '#':
                    continue
                
                source = self._clean(row.get('Source', ''))
                participants = self._clean(row.get('Participants', ''))
                from_user = self._clean(row.get('From', ''))
                to_user = self._clean(row.get('To', ''))
                body = self._clean(row.get('Body', ''))
                account = self._clean(row.get('Account', ''))
                
                if source and source.lower() == 'instagram':
                    if participants:
                        participant_lines = participants.split('_x000d_')
                        for line in participant_lines:
                            line = line.strip()
                            if line and not line.startswith('777000'):
                                parts = line.split()
                                if len(parts) >= 2:
                                    user_id = parts[0]
                                    username = ' '.join(parts[1:]).replace('(owner)', '').strip()
                                    
                                    acc = {
                                        "file_id": file_id,
                                        "source": source,
                                        "account_name": username,
                                        "full_name": username,
                                        "instagram_id": user_id,
                                        "whatsapp_id": None,
                                        "telegram_id": None,
                                        "X_id": None,
                                        "facebook_id": None,
                                        "tiktok_id": None,
                                        "sheet_name": sheet_name,
                                    }
                                    results.append(acc)
                
                elif source and source.lower() == 'whatsapp':
                    if participants:
                        participant_lines = participants.split('_x000d_')
                        for line in participant_lines:
                            line = line.strip()
                            if line and '@s.whatsapp.net' in line:
                                whatsapp_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', line)
                                if whatsapp_match:
                                    phone_number = whatsapp_match.group(1)
                                    line = line.replace('@s.whatsapp.net', '')
                                    acc = {
                                        "file_id": file_id,
                                        "source": source,
                                        "account_name": phone_number,
                                        "full_name": phone_number,
                                        "whatsapp_id": phone_number,
                                        "phone_number": phone_number,
                                        "telegram_id": None,
                                        "instagram_id": None,
                                        "X_id": None,
                                        "facebook_id": None,
                                        "tiktok_id": None,
                                        "sheet_name": sheet_name,
                                    }
                                    results.append(acc)
                
                elif source and source.lower() == 'telegram':
                    if participants:
                        participant_lines = participants.split('_x000d_')
                        for line in participant_lines:
                            line = line.strip()
                            if line and not line.startswith('777000'):
                                parts = line.split()
                                if len(parts) >= 2:
                                    user_id = parts[0]
                                    username = ' '.join(parts[1:]).replace('(owner)', '').strip()
                                    
                                    acc = {
                                        "file_id": file_id,
                                        "source": source,
                                        "account_name": username,
                                        "full_name": username,
                                        "telegram_id": user_id,
                                        "whatsapp_id": None,
                                        "instagram_id": None,
                                        "X_id": None,
                                        "facebook_id": None,
                                        "tiktok_id": None,
                                        "sheet_name": sheet_name,
                                    }
                                    results.append(acc)
                
                elif body and 'tiktok' in body.lower():
                    tiktok_match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', body)
                    if tiktok_match:
                        username = tiktok_match.group(1)
                        acc = {
                            "file_id": file_id,
                            "source": "TikTok",
                            "account_name": username,
                            "full_name": username,
                            "tiktok_id": username,
                            "whatsapp_id": None,
                            "telegram_id": None,
                            "instagram_id": None,
                            "X_id": None,
                            "facebook_id": None,
                            "sheet_name": sheet_name,
                        }
                        results.append(acc)
                
                elif body and 'facebook' in body.lower():
                    facebook_match = re.search(r'facebook\.com/([a-zA-Z0-9_.]+)', body)
                    if facebook_match:
                        username = facebook_match.group(1)
                        acc = {
                            "file_id": file_id,
                            "source": "Facebook",
                            "account_name": username,
                            "full_name": username,
                            "facebook_id": username,
                            "whatsapp_id": None,
                            "telegram_id": None,
                            "instagram_id": None,
                            "X_id": None,
                            "tiktok_id": None,
                            "sheet_name": sheet_name,
                        }
                        results.append(acc)
                
                elif body and ('twitter' in body.lower() or 'x.com' in body.lower()):
                    twitter_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', body)
                    if twitter_match:
                        username = twitter_match.group(1)
                        acc = {
                            "file_id": file_id,
                            "source": "X (Twitter)",
                            "account_name": username,
                            "full_name": username,
                            "X_id": username,
                            "whatsapp_id": None,
                            "telegram_id": None,
                            "instagram_id": None,
                            "facebook_id": None,
                            "tiktok_id": None,
                            "sheet_name": sheet_name,
                        }
                        results.append(acc)
            
            print(f"Found {len(results)} social media accounts in {sheet_name} sheet")
            
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results
    
    def count_cellebrite_social_media(self, file_path: str) -> int:
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            total_count = 0
           
            if 'Social Media' in xls.sheet_names:
                df = pd.read_excel(file_path, sheet_name='Social Media', engine='openpyxl', dtype=str)
                instagram_count = len(df[df['Unnamed: 8'] == 'Instagram'])
                total_count += instagram_count
            
            if 'Contacts' in xls.sheet_names:
                df = pd.read_excel(file_path, sheet_name='Contacts', engine='openpyxl', dtype=str)
                telegram_contacts = df[df['Unnamed: 20'] == 'Telegram']
                telegram_count = len(telegram_contacts[telegram_contacts['Unnamed: 8'].notna()])
                total_count += telegram_count
            
            if 'Chats' in xls.sheet_names:
                df = pd.read_excel(file_path, sheet_name='Chats', engine='openpyxl', dtype=str)
                telegram_chats = df[df['Unnamed: 15'] == 'Telegram']
                chat_count = len(telegram_chats[telegram_chats['Unnamed: 13'].notna()])
                total_count += chat_count
            
            return total_count
            
        except Exception as e:
            print(f"Error counting Cellebrite social media: {e}")
            return 0

    def _parse_axiom_instagram_profiles(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User Name')):
                    continue
                    
                following_value = self._clean(row.get('Following'))
                followers_value = self._clean(row.get('Is Followed By'))
                
                following_count = 1 if following_value and following_value.lower() == 'yes' else None
                followers_count = 1 if followers_value and followers_value.lower() == 'yes' else None
                
                user_id_value = self._clean(row.get('User ID'))
                user_name_value = self._clean(row.get('User Name'))
                
                account_id_value = user_id_value if user_id_value else user_name_value
                
                acc = {
                    "file_id": file_id,
                    "source": "Instagram",
                    "account_name": user_name_value,
                    "full_name": self._clean(row.get('Name')),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "sheet_name": "Instagram Profiles",
                    "instagram_id": account_id_value, 
                    "whatsapp_id": None,
                    "telegram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Instagram Profiles: {e}")
        
        return results

    def _parse_axiom_instagram_following(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User Name')):
                    continue
                
                following_value = self._clean(row.get('Status'))
                following_count = 1 if following_value and following_value.lower() == 'following' else None
                
                user_id_value = self._clean(row.get('ID'))
                user_name_value = self._clean(row.get('User Name'))
                
                account_id_value = user_id_value if user_id_value else user_name_value
                
                acc = {
                    "file_id": file_id,
                    "source": "Instagram",
                    "account_name": user_name_value,
                    "full_name": self._clean(row.get('Full Name')),
                    "sheet_name": "Android Instagram Following",
                    "instagram_id": account_id_value,
                    "whatsapp_id": None,
                    "telegram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Android Instagram Following: {e}")
        
        return results

    def _parse_axiom_instagram_users(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User Name')):
                    continue
                
                user_id_value = self._clean(row.get('ID'))
                user_name_value = self._clean(row.get('User Name'))
                
                account_id_value = user_id_value if user_id_value else user_name_value
                
                acc = {
                    "file_id": file_id,
                    "source": "Instagram",
                    "account_name": user_name_value,
                    "full_name": self._clean(row.get('Full Name')),
                    "sheet_name": "Android Instagram Users",
                    "instagram_id": account_id_value,
                    "whatsapp_id": None,
                    "telegram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Android Instagram Users: {e}")
        
        return results

    def _parse_axiom_user_accounts(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                service_name = self._clean(row.get('Service Name', ''))
                user_name = self._clean(row.get('User Name', ''))
                user_id = self._clean(row.get('User ID', ''))
                
                if not service_name or 'telegram' not in service_name.lower():
                    continue
                
                if not user_name and not user_id:
                    continue
                
                acc = {
                    "file_id": file_id,
                    "source": "Telegram",
                    "account_name": user_name or user_id,
                    "full_name": user_name,
                    "phone_number": self._clean(row.get('Phone Number(s)')),
                    "sheet_name": "User Accounts",
                    "telegram_id": user_id or user_name,
                    "whatsapp_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing User Accounts: {e}")
        
        return results

    def _parse_axiom_whatsapp_accounts(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                whatsapp_name = self._clean(row.get('WhatsApp Name'))
                phone_number = self._clean(row.get('Phone Number'))
                
                if not whatsapp_name and not phone_number:
                    continue
                
                acc = {
                    "file_id": file_id,
                    "source": "WhatsApp",
                    "account_name": whatsapp_name or phone_number,
                    "full_name": whatsapp_name,
                    "phone_number": phone_number,
                    "sheet_name": "WhatsApp Accounts Information",
                    "whatsapp_id": phone_number or whatsapp_name,
                    "telegram_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing WhatsApp Accounts Information: {e}")
        
        return results

    def _parse_axiom_twitter_users(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User Name')):
                    continue
                    
                user_id_value = self._clean(row.get('User ID'))
                screen_name_value = self._clean(row.get('Screen Name'))
                user_name_value = self._clean(row.get('User Name')) or screen_name_value
                
                account_id_value = user_id_value if user_id_value else user_name_value
                    
                acc = {
                    "file_id": file_id,
                    "source": "X (Twitter)",
                    "account_name": user_name_value or screen_name_value,
                    "full_name": self._clean(row.get('Full Name')),
                    "sheet_name": "Twitter Users",
                    "X_id": account_id_value,
                    "whatsapp_id": None,
                    "telegram_id": None,
                    "instagram_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Twitter Users: {e}")
        
        return results

    def _parse_axiom_telegram_accounts(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User ID')):
                    continue
                    
                first_name = self._clean(row.get('First Name', ''))
                last_name = self._clean(row.get('Last Name', ''))
                full_name = f"{first_name} {last_name}".strip()
                user_name = self._clean(row.get('User Name'))
                
                account_id_value = self._clean(row.get('Account ID'))
                user_id_value = self._clean(row.get('User ID'))
                
                account_name_value = user_name or full_name or str(user_id_value) if user_id_value else None
                account_id_final = account_id_value if account_id_value else user_id_value
                
                acc = {
                    "file_id": file_id,
                    "source": "Telegram",
                    "account_name": account_name_value,
                    "full_name": full_name,
                    "phone_number": self._clean(row.get('Phone Number')),
                    "sheet_name": "Telegram Accounts",
                    "telegram_id": account_id_final,
                    "whatsapp_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Telegram Accounts: {e}")
        
        return results

    def _parse_axiom_tiktok_contacts(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl", dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get("ID")):
                    continue
                
                nickname = self._clean(row.get("Nickname"))
                user_name = self._clean(row.get("User Name"))
                account_name = nickname or user_name
                
                acc = {
                    "file_id": file_id,
                    "source": "TikTok",
                    "account_name": account_name,
                    "full_name": nickname or user_name,
                    "sheet_name": "TikTok Contacts",
                    "tiktok_id": self._clean(row.get("ID")),
                    "whatsapp_id": None,
                    "telegram_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                }
                
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing TikTok Contacts: {e}")
        
        return results

    def _parse_axiom_facebook_contacts(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Profile ID')):
                    continue
                    
                acc = {
                    "file_id": file_id,
                    "source": "Facebook",
                    "account_name": self._clean(row.get('Display Name')),
                    "full_name": f"{self._clean(row.get('First Name'))} {self._clean(row.get('Last Name'))}".strip(),
                    "phone_number": self._clean(row.get('Phone Numbers')),
                    "sheet_name": sheet_name,
                    "facebook_id": self._clean(row.get('Profile ID')),
                    "whatsapp_id": None,
                    "telegram_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Facebook Contacts: {e}")
        
        return results

    def _parse_axiom_facebook_users(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User ID')):
                    continue
                    
                acc = {
                    "file_id": file_id,
                    "source": "Facebook",
                    "account_name": self._clean(row.get('Display Name')),
                    "full_name": f"{self._clean(row.get('First Name'))} {self._clean(row.get('Last Name'))}".strip(),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "sheet_name": sheet_name,
                    "facebook_id": self._clean(row.get('User ID')),
                    "whatsapp_id": None,
                    "telegram_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Facebook Users: {e}")
        
        return results

    def _parse_axiom_whatsapp_contacts(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('ID')):
                    continue
                    
                acc = {
                    "file_id": file_id,
                    "source": "WhatsApp",
                    "account_name": self._clean(row.get('WhatsApp Name')),
                    "full_name": f"{self._clean(row.get('Given Name'))} {self._clean(row.get('Family Name'))}".strip(),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "sheet_name": sheet_name,
                    "whatsapp_id": self._clean(row.get('ID')),
                    "telegram_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing WhatsApp Contacts: {e}")
        
        return results

    def _parse_axiom_whatsapp_users(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Phone Number')):
                    continue
                    
                acc = {
                    "file_id": file_id,
                    "source": "WhatsApp",
                    "account_name": self._clean(row.get('WhatsApp Name')),
                    "full_name": self._clean(row.get('WhatsApp Name')),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "sheet_name": sheet_name,
                    "whatsapp_id": self._clean(row.get('Phone Number')),
                    "telegram_id": None,
                    "instagram_id": None,
                    "X_id": None,
                    "facebook_id": None,
                    "tiktok_id": None,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing WhatsApp Users: {e}")
        
        return results

    def _safe_int(self, value) -> Optional[int]:
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None

    def _safe_bool(self, value) -> Optional[bool]:
        if pd.isna(value) or value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'y']
        return bool(value)

    def parse_social_media_from_sample_folder(self, sample_folder_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        sample_path = Path(sample_folder_path)
        
        if not sample_path.exists():
            print(f"Sample folder tidak ditemukan: {sample_folder_path}")
            return results
        
        for device_folder in sample_path.iterdir():
            if not device_folder.is_dir():
                continue
                
            print(f"Processing device folder: {device_folder.name}")
            
            for tool_folder in device_folder.iterdir():
                if not tool_folder.is_dir():
                    continue
                    
                print(f"Processing tool folder: {tool_folder.name}")
                
                if tool_folder.name.lower() == "axiom":
                    tool_results = self._parse_axiom_social_media(tool_folder, file_id)
                elif tool_folder.name.lower() == "cellebrite":
                    tool_results = self._parse_cellebrite_social_media(tool_folder, file_id)
                elif tool_folder.name.lower() == "oxygen":
                    tool_results = self._parse_oxygen_folder_social_media(tool_folder, file_id)
                else:
                    continue
                    
                results.extend(tool_results)
        
        return results

    def _parse_axiom_social_media(self, tool_folder: Path, file_id: int) -> List[Dict[str, Any]]:
        results = []

        excel_files = list(tool_folder.glob("*.xlsx")) + list(tool_folder.glob("*.xls"))
        
        for excel_file in excel_files:
            print(f"Parsing Axiom file: {excel_file.name}")
            try:
                file_results = self.parse_oxygen_social_media(excel_file, file_id)
                results.extend(file_results)
            except Exception as e:
                print(f"Error parsing Axiom file {excel_file.name}: {e}")
        
        return results

    def _parse_cellebrite_social_media(self, tool_folder: Path, file_id: int) -> List[Dict[str, Any]]:
    
        results = []
        
        excel_files = list(tool_folder.glob("*.xlsx")) + list(tool_folder.glob("*.xls"))
        
        for excel_file in excel_files:
            print(f"Parsing Cellebrite file: {excel_file.name}")
            try:
                file_results = self.parse_oxygen_social_media(excel_file, file_id)
                results.extend(file_results)
            except Exception as e:
                print(f"Error parsing Cellebrite file {excel_file.name}: {e}")
        
        return results

    def _parse_oxygen_folder_social_media(self, tool_folder: Path, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        excel_files = list(tool_folder.glob("*.xlsx")) + list(tool_folder.glob("*.xls"))
        
        for excel_file in excel_files:
            print(f"Parsing Oxygen file: {excel_file.name}")
            try:
                file_results = self.parse_oxygen_social_media(excel_file, file_id)
                results.extend(file_results)
            except Exception as e:
                print(f"Error parsing Oxygen file {excel_file.name}: {e}")
        
        return results

    def parse_cellebrite_chat_messages(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        return self._chat_messages_parser.parse_cellebrite_chat_messages(file_path, file_id)

    def parse_oxygen_chat_messages(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        return self._chat_messages_parser.parse_oxygen_chat_messages(file_path, file_id)

    def parse_axiom_chat_messages(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        return self._chat_messages_parser.parse_axiom_chat_messages(file_path, file_id)

    def _parse_axiom_whatsapp_accounts_info(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                whatsapp_name = self._clean(row.get('WhatsApp Name', ''))
                phone_number = self._clean(row.get('Phone Number', ''))
                
                if whatsapp_name and phone_number:
                    acc = {
                        "platform": "WhatsApp",
                        "account_name": whatsapp_name,
                        "account_id": phone_number,
                        "user_id": phone_number,
                        "full_name": whatsapp_name,
                        "phone_number": phone_number,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results

    def _parse_axiom_whatsapp_chats(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                individual_chat_name = self._clean(row.get('Individual Chat Name', ''))
                group_chat_name = self._clean(row.get('Group Chat Name', ''))
                chat_id = self._clean(row.get('Chat ID', ''))
                
                phone_number = None
                if chat_id and '@s.whatsapp.net' in chat_id:
                    phone_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', chat_id)
                    if phone_match:
                        phone_number = phone_match.group(1)
                        chat_id = chat_id.replace('@s.whatsapp.net', '')
                
                account_name = individual_chat_name or group_chat_name
                
                if account_name and phone_number:
                    acc = {
                        "platform": "WhatsApp",
                        "account_name": account_name,
                        "account_id": phone_number,
                        "user_id": phone_number,
                        "full_name": account_name,
                        "phone_number": phone_number,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results

    def _parse_axiom_whatsapp_contacts_android(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                contact_id = self._clean(row.get('ID', ''))
                name = self._clean(row.get('Name', ''))
                
                phone_number = None
                if contact_id and '@s.whatsapp.net' in contact_id:
                    phone_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', contact_id)
                    if phone_match:
                        phone_number = phone_match.group(1)
                        contact_id = contact_id.replace('@s.whatsapp.net', '')
                
                if phone_number:
                    acc = {
                        "platform": "WhatsApp",
                        "account_name": name or phone_number,
                        "account_id": phone_number,
                        "user_id": phone_number,
                        "full_name": name,
                        "phone_number": phone_number,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results

    def _parse_axiom_whatsapp_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            seen_accounts = set()
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                sender = self._clean(row.get('Sender', ''))
                
                phone_number = None
                if sender and '@s.whatsapp.net' in sender:
                    phone_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', sender)
                    if phone_match:
                        phone_number = phone_match.group(1)
                        sender = sender.replace('@s.whatsapp.net', '')
                
                if phone_number and phone_number not in seen_accounts:
                    seen_accounts.add(phone_number)
                    acc = {
                        "platform": "WhatsApp",
                        "account_name": phone_number,
                        "account_id": phone_number,
                        "user_id": phone_number,
                        "full_name": phone_number,
                        "phone_number": phone_number,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results

    def _parse_axiom_whatsapp_user_profiles(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                whatsapp_name = self._clean(row.get('WhatsApp Name', ''))
                phone_number = self._clean(row.get('Phone Number', ''))
                
                if whatsapp_name and phone_number:
                    acc = {
                        "platform": "WhatsApp",
                        "account_name": whatsapp_name,
                        "account_id": phone_number,
                        "user_id": phone_number,
                        "full_name": whatsapp_name,
                        "phone_number": phone_number,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results

    def _parse_axiom_telegram_chats(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                chat_name = self._clean(row.get('Chat Name', ''))
                chat_id = self._clean(row.get('Chat ID', ''))
                chat_type = self._clean(row.get('Chat Type', ''))
                
                if chat_name and chat_id:
                    acc = {
                        "platform": "Telegram",
                        "account_name": chat_name,
                        "account_id": chat_id,
                        "user_id": chat_id,
                        "full_name": chat_name,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results

    def _parse_axiom_telegram_contacts_android(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                user_id = self._clean(row.get('User ID', ''))
                first_name = self._clean(row.get('First Name', ''))
                last_name = self._clean(row.get('Last Name', ''))
                username = self._clean(row.get('Username', ''))
                
                if user_id and (first_name or last_name or username):
                    full_name = f"{first_name} {last_name}".strip() if first_name or last_name else username
                    account_name = username or full_name
                    
                    acc = {
                        "platform": "Telegram",
                        "account_name": account_name,
                        "account_id": user_id,
                        "user_id": user_id,
                        "full_name": full_name,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results

    def _parse_axiom_telegram_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            seen_accounts = set()
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                partner = self._clean(row.get('Partner', ''))
                
                if partner and partner not in seen_accounts:
                    seen_accounts.add(partner)
                    acc = {
                        "platform": "Telegram",
                        "account_name": partner,
                        "account_id": partner,
                        "user_id": partner,
                        "full_name": partner,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results

    def _parse_axiom_telegram_users_android(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
            
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue
                
                user_id = self._clean(row.get('User ID', ''))
                first_name = self._clean(row.get('First Name', ''))
                last_name = self._clean(row.get('Last Name', ''))
                username = self._clean(row.get('Username', ''))
                
                if user_id and (first_name or last_name or username):
                    full_name = f"{first_name} {last_name}".strip() if first_name or last_name else username
                    account_name = username or full_name
                    
                    acc = {
                        "platform": "Telegram",
                        "account_name": account_name,
                        "account_id": user_id,
                        "user_id": user_id,
                        "full_name": full_name,
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results


