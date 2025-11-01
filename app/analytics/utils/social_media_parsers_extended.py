import re
import pandas as pd  # type: ignore
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session  # type: ignore
from app.analytics.device_management.models import SocialMedia, ChatMessage
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)

class SocialMediaParsersExtended:
    
    def __init__(self, db: Session):
        self.db = db
    
    def _clean(self, text: Any) -> Optional[str]:
        if text is None or pd.isna(text):
            return None
        text = str(text).strip()
        if text.lower() in ["", "nan", "none", "null", "n/a", "none"]:
            return None
        return text
    
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
            # Sudah struktur baru
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
        
        # Map platform dan account_id ke field yang sesuai
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
            
            print(f"📊 Total sheets available: {len(xls.sheet_names)}")
            print(f"📋 Sheet names: {xls.sheet_names}")
            
            if 'Contacts' in xls.sheet_names:
                print("🔍 Detected Contacts sheet - parsing Contacts only (skipping other sheets)")
                results.extend(self._parse_cellebrite_contacts_sheet(file_path, 'Contacts', file_id))
            
            elif 'Social Media' in xls.sheet_names:
                print("🔍 Detected Cellebrite format - parsing Social Media sheet")
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
                        # Extract Instagram username or ID
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
                    "account_name": user_name_value,  # Username
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
                
                # account_id seharusnya Account ID, jika tidak ada gunakan User ID
                # account_name bisa username atau full_name
                account_name_value = user_name or full_name or str(user_id_value) if user_id_value else None
                account_id_final = account_id_value if account_id_value else user_id_value
                
                acc = {
                    "file_id": file_id,
                    "source": "Telegram",
                    "account_name": account_name_value,
                    "full_name": full_name,
                    "phone_number": self._clean(row.get('Phone Number')),
                    "sheet_name": "Telegram Accounts",
                    "telegram_id": account_id_final,  # Account ID atau User ID sebagai identifier unik
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
                # Skip rows without ID
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
                
                # Parse berdasarkan tool
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
        results = []
        
        try:
            logger.info(f"[CELLEBRITE CHAT PARSER] Starting to parse chat messages from file_id={file_id}, file_path={file_path}")
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            logger.info(f"[CELLEBRITE CHAT PARSER] Total sheets found: {len(xls.sheet_names)}")
            logger.info(f"[CELLEBRITE CHAT PARSER] Available sheets: {', '.join(xls.sheet_names[:10])}...")
            
            # Parse Chats sheet for messages (supports multiple platforms)
            if 'Chats' in xls.sheet_names:
                logger.info(f"[CELLEBRITE CHAT PARSER] Found 'Chats' sheet, parsing...")
                chats_results = self._parse_cellebrite_chats_messages(file_path, 'Chats', file_id)
                results.extend(chats_results)
                logger.info(f"[CELLEBRITE CHAT PARSER] Chats sheet: Parsed {len(chats_results)} messages")
            else:
                logger.warning(f"[CELLEBRITE CHAT PARSER] 'Chats' sheet not found")
            
            logger.info(f"[CELLEBRITE CHAT PARSER] Total parsed messages: {len(results)}")
            
            # Log sample data for debugging
            if results:
                sample_msg = results[0]
                logger.debug(f"[CELLEBRITE CHAT PARSER] Sample message data: platform={sample_msg.get('platform')}, "
                           f"sheet_name={sample_msg.get('sheet_name')}, "
                           f"message_id={sample_msg.get('message_id')}, "
                           f"sender={sample_msg.get('sender_name')}, "
                           f"receiver={sample_msg.get('receiver_name')}, "
                           f"timestamp={sample_msg.get('timestamp')}")
            
            # Save to database
            saved_count = 0
            skipped_count = 0
            for msg in results:
                existing = (
                    self.db.query(ChatMessage)
                    .filter(
                        ChatMessage.platform == msg["platform"],
                        ChatMessage.message_id == msg["message_id"],
                                            )
                    .first()
                )
                if not existing:
                    self.db.add(ChatMessage(**msg))
                    saved_count += 1
                else:
                    skipped_count += 1
            
            self.db.commit()
            logger.info(f"[CELLEBRITE CHAT PARSER] Successfully saved {saved_count} chat messages to database (skipped {skipped_count} duplicates)")
            print(f"Successfully saved {saved_count} Cellebrite chat messages to database (skipped {skipped_count} duplicates)")
            
        except Exception as e:
            logger.error(f"[CELLEBRITE CHAT PARSER] Error parsing Cellebrite chat messages: {e}", exc_info=True)
            print(f"Error parsing Cellebrite chat messages: {e}")
            self.db.rollback()
            raise e
        
        return results

    def _parse_cellebrite_chats_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[CELLEBRITE CHATS PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            logger.debug(f"[CELLEBRITE CHATS PARSER] Sheet loaded: {len(df)} rows, columns: {list(df.columns)[:15]}")
            
            processed_count = 0
            skipped_count = 0
            platform_counts = {}
            
            skip_reasons = {
                'no_platform': 0,
                'no_message': 0,
                'header_row': 0
            }
            
            for idx, row in df.iterrows():
                first_col = self._clean(row.get(df.columns[0], ''))
                if first_col and first_col.lower() in ['identifier', 'record', 'name', 'platform', 'message', 'sender']:
                    skip_reasons['header_row'] += 1
                    continue
 
                platform = None
                
                # Check multiple possible columns for platform
                platform_columns_to_check = [
                    'Unnamed: 15',
                    df.columns[14] if len(df.columns) > 14 else None,
                    'Unnamed: 16',
                    df.columns[15] if len(df.columns) > 15 else None,
                    'Service',
                    'Platform',
                    'App'
                ]
                
                for col_name in platform_columns_to_check:
                    if not col_name:
                        continue
                    platform_val = self._clean(row.get(col_name, ''))
                    if platform_val:
                        platform_lower = platform_val.lower()
                        if 'telegram' in platform_lower:
                            platform = "telegram"
                            break
                        elif 'whatsapp' in platform_lower or 'wa ' in platform_lower:
                            platform = "whatsapp"
                            break
                        elif 'instagram' in platform_lower or 'ig ' in platform_lower:
                            platform = "instagram"
                            break
                        elif 'tiktok' in platform_lower:
                            platform = "tiktok"
                            break
                        elif 'twitter' in platform_lower or 'x ' in platform_lower:
                            platform = "x"
                            break
                        elif 'facebook' in platform_lower or 'messenger' in platform_lower:
                            platform = "facebook"
                            break
                
                if not platform:
                    skip_reasons['no_platform'] += 1
                    if skip_reasons['no_platform'] <= 3:
                        logger.debug(f"[CELLEBRITE CHATS PARSER] Row {idx} skipped - no platform detected. "
                                   f"Sample values: col15={row.get('Unnamed: 15', 'N/A')[:50]}, "
                                   f"col0={row.get(df.columns[0], 'N/A')[:50]}")
                    skipped_count += 1
                    continue
                
                # Track platform count
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                message_text = None
                message_columns_to_check = [
                    'Unnamed: 32',
                    df.columns[31] if len(df.columns) > 31 else None,
                    'Unnamed: 33',
                    df.columns[32] if len(df.columns) > 32 else None,
                    'Body',
                    'Message',
                    'Text',
                    'Content'
                ]
                
                for col_name in message_columns_to_check:
                    if not col_name:
                        continue
                    msg_val = self._clean(row.get(col_name, ''))
                    if msg_val and len(msg_val.strip()) > 0:
                        message_text = msg_val
                        break
                
                if not message_text:
                    for col_name in df.columns:
                        if col_name and col_name not in ['Unnamed: 15', 'Unnamed: 25', 'Unnamed: 24', 'Unnamed: 2']:
                            val = self._clean(row.get(col_name, ''))
                            if val and len(val.strip()) > 10:
                                if not val.replace(':', '').replace('-', '').replace('/', '').replace(' ', '').isdigit():
                                    message_text = val
                                    break
                
                if not message_text:
                    skip_reasons['no_message'] += 1
                    if skip_reasons['no_message'] <= 3:
                        logger.debug(f"[CELLEBRITE CHATS PARSER] Row {idx} skipped - no message text. "
                                   f"Platform: {platform}, "
                                   f"Message col 32: {str(row.get('Unnamed: 32', 'N/A'))[:50]}")
                    skipped_count += 1
                    continue
                
                # Extract sender info (usually Unnamed: 25)
                sender_info = self._clean(row.get('Unnamed: 25', '')) or \
                             self._clean(row.get('Sender', '')) or \
                             self._clean(row.get('From', ''))
                
                sender_name = ""
                sender_id = ""
                
                # Parse sender info (format: "ID Name" atau "Name")
                if sender_info:
                    parts = sender_info.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        sender_id = parts[0]
                        sender_name = ' '.join(parts[1:])
                    else:
                        sender_name = sender_info
                        # Try to extract ID from other columns
                        sender_id = self._clean(row.get('Unnamed: 26', '')) or \
                                   self._clean(row.get('Sender ID', ''))
                
                # Extract receiver info
                receiver_info = self._clean(row.get('Unnamed: 27', '')) or \
                               self._clean(row.get('Recipient', '')) or \
                               self._clean(row.get('To', ''))
                
                receiver_name = ""
                receiver_id = ""
                
                if receiver_info:
                    parts = receiver_info.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        receiver_id = parts[0]
                        receiver_name = ' '.join(parts[1:])
                    else:
                        receiver_name = receiver_info
                
                # Extract timestamp (usually Unnamed: 41)
                timestamp = self._clean(row.get('Unnamed: 41', '')) or \
                           self._clean(row.get('Timestamp: Time', '')) or \
                           self._clean(row.get('Timestamp', '')) or \
                           self._clean(row.get('Date/Time', ''))
                
                # Extract chat identifier (usually Unnamed: 2)
                chat_id = self._clean(row.get('Unnamed: 2', '')) or \
                         self._clean(row.get('Identifier', '')) or \
                         self._clean(row.get('Chat ID', ''))
                
                # Extract message ID (usually Unnamed: 24)
                message_id = self._clean(row.get('Unnamed: 24', '')) or \
                            self._clean(row.get('Instant Message #', '')) or \
                            self._clean(row.get('Message ID', ''))
                
                if not message_id or message_id.lower() in ['nan', 'none', '']:
                    if timestamp:
                        message_id = f"{platform}_{file_id}_{timestamp}_{idx}"
                    else:
                        message_id = f"{platform}_{file_id}_{idx}"
                
                direction = self._clean(row.get('Direction', '')) or \
                           self._clean(row.get('Unnamed: 28', ''))
                
                if not direction:
                    direction = "Outgoing" if sender_id else "Incoming"
                
                # Extract message type
                message_type = self._clean(row.get('Type', '')) or \
                              self._clean(row.get('Message Type', '')) or \
                              'text'
                
                message_data = {
                    "file_id": file_id,
                    "platform": platform,
                    "message_text": message_text,
                    "sender_name": sender_name,
                    "sender_id": sender_id,
                    "receiver_name": receiver_name,
                    "receiver_id": receiver_id,
                    "timestamp": timestamp,
                    "thread_id": chat_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "message_type": message_type,
                    "direction": direction,
                    "source_tool": "cellebrite",
                    "sheet_name": sheet_name
                }
                
                if platform_counts[platform] == 1:
                    logger.debug(f"[CELLEBRITE CHATS PARSER] First {platform} message sample: message_id={message_data['message_id']}, "
                               f"sender={message_data['sender_name']}, receiver={message_data['receiver_name']}, "
                               f"text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[CELLEBRITE CHATS PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            logger.info(f"[CELLEBRITE CHATS PARSER] Platform breakdown: {platform_counts}")
            logger.info(f"[CELLEBRITE CHATS PARSER] Skip reasons: {skip_reasons}")
            logger.debug(f"[CELLEBRITE CHATS PARSER] Total rows in sheet: {len(df)}, "
                        f"Processed: {processed_count}, Skipped: {skipped_count}, "
                        f"Coverage: {(processed_count/len(df)*100):.1f}%")
            
        except Exception as e:
            logger.error(f"[CELLEBRITE CHATS PARSER] Error parsing Cellebrite chats messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Cellebrite chats messages: {e}")
            import traceback
            traceback.print_exc()
        
        return results

    def parse_oxygen_chat_messages(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.info(f"[OXYGEN CHAT PARSER] Starting to parse chat messages from file_id={file_id}, file_path={file_path}")
            print(f"[OXYGEN CHAT PARSER] Starting to parse chat messages from file_id={file_id}, file_path={file_path}")
            
            # Determine engine based on file extension
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
            for sheet in xls.sheet_names:
                if sheet.lower() == 'messages' or sheet.lower() == 'message':
                    messages_sheet = sheet
                    break
            
            if messages_sheet:
                logger.info(f"[OXYGEN CHAT PARSER] Found '{messages_sheet}' sheet - will parse all platforms from this sheet")
                print(f"[OXYGEN CHAT PARSER] Found '{messages_sheet}' sheet - will parse all platforms from this sheet")
                
                messages_results = self._parse_oxygen_messages_sheet(file_path, messages_sheet, file_id, engine)
                results.extend(messages_results)
                logger.info(f"[OXYGEN CHAT PARSER] Messages sheet: Parsed {len(messages_results)} messages from all platforms")
                print(f"[OXYGEN CHAT PARSER] Messages sheet: Parsed {len(messages_results)} messages from all platforms")
            
            whatsapp_sheets = [s for s in xls.sheet_names if 'whatsapp' in s.lower() and ('message' in s.lower() or 'chat' in s.lower())]
            if not whatsapp_sheets:
                whatsapp_sheets = [s for s in xls.sheet_names if 'whatsapp messenger' in s.lower()]
            
            if 'Contacts' in xls.sheet_names or 'Contact' in xls.sheet_names:
                contacts_sheet = 'Contacts' if 'Contacts' in xls.sheet_names else 'Contact'
                if contacts_sheet not in whatsapp_sheets:
                    whatsapp_sheets.append(contacts_sheet)
                    logger.info(f"[OXYGEN CHAT PARSER] Adding Contacts sheet for WhatsApp message parsing")
                    print(f"[OXYGEN CHAT PARSER] Adding Contacts sheet for WhatsApp message parsing")
            
            if messages_sheet:
                if messages_sheet not in whatsapp_sheets:
                    whatsapp_sheets.append(messages_sheet)
            
            if not whatsapp_sheets:
                logger.warning(f"[OXYGEN CHAT PARSER] No WhatsApp sheets found!")
                print(f"[OXYGEN CHAT PARSER] WARNING: No WhatsApp sheets found!")
                print(f"[OXYGEN CHAT PARSER] Available sheets with 'whatsapp': {[s for s in xls.sheet_names if 'whatsapp' in s.lower()]}")
            else:
                print(f"[OXYGEN CHAT PARSER] Found {len(whatsapp_sheets)} WhatsApp sheet(s): {whatsapp_sheets}")
            
            for sheet in whatsapp_sheets:
                logger.info(f"[OXYGEN CHAT PARSER] Found WhatsApp sheet: {sheet}, parsing...")
                print(f"[OXYGEN CHAT PARSER] Found WhatsApp sheet: {sheet}, parsing...")
                try:
                    whatsapp_results = self._parse_oxygen_whatsapp_messages(file_path, sheet, file_id, engine)
                    results.extend(whatsapp_results)
                    logger.info(f"[OXYGEN CHAT PARSER] WhatsApp ({sheet}): Parsed {len(whatsapp_results)} messages")
                    print(f"[OXYGEN CHAT PARSER] WhatsApp ({sheet}): Parsed {len(whatsapp_results)} messages")
                except Exception as e:
                    logger.error(f"[OXYGEN CHAT PARSER] Error parsing WhatsApp sheet {sheet}: {e}", exc_info=True)
                    print(f"[OXYGEN CHAT PARSER] Error parsing WhatsApp sheet {sheet}: {e}")
                    continue
            
            # Parse Telegram Messages
            telegram_sheets = [s for s in xls.sheet_names if 'telegram' in s.lower() and ('message' in s.lower() or 'chat' in s.lower())]
            if not telegram_sheets:
                telegram_sheets = [s for s in xls.sheet_names if 'telegram ' in s.lower()]
            
            # If Messages sheet exists, add it to telegram sheets
            if messages_sheet and messages_sheet not in telegram_sheets:
                telegram_sheets.append(messages_sheet)
            
            for sheet in telegram_sheets:
                logger.info(f"[OXYGEN CHAT PARSER] Found Telegram sheet: {sheet}, parsing...")
                telegram_results = self._parse_oxygen_telegram_messages(file_path, sheet, file_id, engine)
                results.extend(telegram_results)
                logger.info(f"[OXYGEN CHAT PARSER] Telegram ({sheet}): Parsed {len(telegram_results)} messages")
            
            # Parse Instagram Messages
            instagram_sheets = [s for s in xls.sheet_names if 'instagram' in s.lower() and ('message' in s.lower() or 'dm' in s.lower() or 'direct' in s.lower())]
            if not instagram_sheets:
                instagram_sheets = [s for s in xls.sheet_names if 'instagram ' in s.lower()]
            
            if messages_sheet and messages_sheet not in instagram_sheets:
                instagram_sheets.append(messages_sheet)
            
            for sheet in instagram_sheets:
                logger.info(f"[OXYGEN CHAT PARSER] Found Instagram sheet: {sheet}, parsing...")
                instagram_results = self._parse_oxygen_instagram_messages(file_path, sheet, file_id, engine)
                results.extend(instagram_results)
                logger.info(f"[OXYGEN CHAT PARSER] Instagram ({sheet}): Parsed {len(instagram_results)} messages")
            
            twitter_sheets = [s for s in xls.sheet_names if ('twitter' in s.lower() or 'x ' in s.lower()) and ('message' in s.lower() or 'dm' in s.lower() or 'direct' in s.lower())]
            if not twitter_sheets:
                twitter_sheets = [s for s in xls.sheet_names if 'x (twitter) ' in s.lower()]
            
            if messages_sheet and messages_sheet not in twitter_sheets:
                twitter_sheets.append(messages_sheet)
            
            for sheet in twitter_sheets:
                logger.info(f"[OXYGEN CHAT PARSER] Found Twitter/X sheet: {sheet}, parsing...")
                twitter_results = self._parse_oxygen_twitter_messages(file_path, sheet, file_id, engine)
                results.extend(twitter_results)
                logger.info(f"[OXYGEN CHAT PARSER] Twitter/X ({sheet}): Parsed {len(twitter_results)} messages")
            
            tiktok_sheets = [s for s in xls.sheet_names if 'tiktok' in s.lower() and ('message' in s.lower() or 'chat' in s.lower())]
            
            if messages_sheet and messages_sheet not in tiktok_sheets:
                tiktok_sheets.append(messages_sheet)
            
            for sheet in tiktok_sheets:
                logger.info(f"[OXYGEN CHAT PARSER] Found TikTok sheet: {sheet}, parsing...")
                tiktok_results = self._parse_oxygen_tiktok_messages(file_path, sheet, file_id, engine)
                results.extend(tiktok_results)
                logger.info(f"[OXYGEN CHAT PARSER] TikTok ({sheet}): Parsed {len(tiktok_results)} messages")
            
            facebook_sheets = [s for s in xls.sheet_names if 'facebook' in s.lower() and ('message' in s.lower() or 'messenger' in s.lower() or 'chat' in s.lower())]
            
            # If Messages sheet exists, add it to facebook sheets
            if messages_sheet and messages_sheet not in facebook_sheets:
                facebook_sheets.append(messages_sheet)
            
            for sheet in facebook_sheets:
                logger.info(f"[OXYGEN CHAT PARSER] Found Facebook sheet: {sheet}, parsing...")
                facebook_results = self._parse_oxygen_facebook_messages(file_path, sheet, file_id, engine)
                results.extend(facebook_results)
                logger.info(f"[OXYGEN CHAT PARSER] Facebook ({sheet}): Parsed {len(facebook_results)} messages")
            
            logger.info(f"[OXYGEN CHAT PARSER] Total parsed messages: {len(results)}")
            print(f"[OXYGEN CHAT PARSER] Total parsed messages: {len(results)}")
            
            if results:
                sample_msg = results[0]
                logger.info(f"[OXYGEN CHAT PARSER] Sample message data: platform={sample_msg.get('platform')}, "
                           f"sheet_name={sample_msg.get('sheet_name')}, "
                           f"message_id={sample_msg.get('message_id')}, "
                           f"sender={sample_msg.get('sender_name')}, "
                           f"receiver={sample_msg.get('receiver_name')}, "
                           f"timestamp={sample_msg.get('timestamp')}")
                print(f"[OXYGEN CHAT PARSER] Sample message data: platform={sample_msg.get('platform')}, "
                      f"sheet_name={sample_msg.get('sheet_name')}, "
                      f"message_id={sample_msg.get('message_id')}, "
                      f"sender={sample_msg.get('sender_name')}")
            else:
                logger.warning(f"[OXYGEN CHAT PARSER] No messages found! Check if file contains chat messages.")
                print(f"[OXYGEN CHAT PARSER] WARNING: No messages found! Check if file contains chat messages.")
                print(f"[OXYGEN CHAT PARSER] All available sheets ({len(xls.sheet_names)}): {', '.join(xls.sheet_names[:20])}")
                if len(xls.sheet_names) > 20:
                    print(f"[OXYGEN CHAT PARSER] ... and {len(xls.sheet_names) - 20} more sheets")
                
                # Suggest which sheets might contain messages
                potential_sheets = []
                for sheet in xls.sheet_names:
                    sheet_lower = sheet.lower()
                    if any(kw in sheet_lower for kw in ['message', 'chat', 'im', 'whatsapp', 'telegram', 'instagram', 'contact']):
                        potential_sheets.append(sheet)
                
                if potential_sheets:
                    print(f"[OXYGEN CHAT PARSER] Potential message-containing sheets: {', '.join(potential_sheets[:10])}")
            
            # Save to database
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

    def _parse_oxygen_messages_sheet(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
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
            
            # Log all columns for debugging
            logger.info(f"[OXYGEN MESSAGES PARSER] Available columns: {list(df.columns)}")
            print(f"[OXYGEN MESSAGES PARSER] Available columns ({len(df.columns)}): {list(df.columns)}")
            
            for col in df.columns:
                col_str = str(col).strip()
                col_lower = col_str.lower()
                
                if col_str == 'Source' or col_lower == 'source':
                    source_col = col
                elif not source_col and ('source' in col_lower or 'service' in col_lower):
                    source_col = col
                
                # Message column
                if 'message' in col_lower and 'type' not in col_lower:
                    if not message_col or col_str == 'Message' or col_lower == 'message':
                        message_col = col
                
                # Timestamp column
                if 'timestamp' in col_lower or ('time' in col_lower and 'stamp' in col_lower) or 'date/time' in col_lower:
                    if not timestamp_col:
                        timestamp_col = col
                
                # Participant/Sender columns
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
                
                # Thread ID column
                if 'thread' in col_lower and 'id' in col_lower:
                    thread_id_col = col
                elif 'message id' in col_lower or 'msg id' in col_lower:
                    thread_id_col = col
            
            # Fallback: if source_col not found, try first column
            if not source_col and len(df.columns) > 0:
                first_col = df.columns[0]
                # Check if first column contains platform names
                if len(df) > 0:
                    sample_val = str(df.iloc[0][first_col]).lower() if pd.notna(df.iloc[0][first_col]) else ''
                    if any(platform in sample_val for platform in ['whatsapp', 'telegram', 'instagram', 'twitter', 'facebook', 'tiktok', 'x']):
                        source_col = first_col
                        logger.info(f"[OXYGEN MESSAGES PARSER] Using first column '{first_col}' as Source/Platform column")
                        print(f"[OXYGEN MESSAGES PARSER] Using first column '{first_col}' as Source/Platform column")
            
            # Fallback: if message_col not found, try common positions
            if not message_col:
                # Usually column 4 (index 3) or column with most text content
                for i in [3, 4, 5]:
                    if i < len(df.columns):
                        col = df.columns[i]
                        # Check if this column has message-like content
                        if len(df) > 0:
                            sample = str(df.iloc[0][col]) if pd.notna(df.iloc[0][col]) else ''
                            if len(sample) > 10 and any(c.isalpha() for c in sample[:50]):
                                message_col = col
                                logger.info(f"[OXYGEN MESSAGES PARSER] Using column {i} '{col}' as Message column")
                                print(f"[OXYGEN MESSAGES PARSER] Using column {i} '{col}' as Message column")
                                break
            
            # Fallback: if timestamp_col not found, try column 3 (index 2)
            if not timestamp_col and len(df.columns) > 2:
                col = df.columns[2]
                sample = str(df.iloc[0][col]) if len(df) > 0 and pd.notna(df.iloc[0][col]) else ''
                if '/' in sample and ':' in sample:  # Looks like date/time format
                    timestamp_col = col
                    logger.info(f"[OXYGEN MESSAGES PARSER] Using column 2 '{col}' as Timestamp column")
                    print(f"[OXYGEN MESSAGES PARSER] Using column 2 '{col}' as Timestamp column")
            
            logger.info(f"[OXYGEN MESSAGES PARSER] Found columns - Source: {source_col}, Message: {message_col}, Timestamp: {timestamp_col}, Sender: {sender_col}, Receiver: {receiver_col}, ThreadID: {thread_id_col}")
            print(f"[OXYGEN MESSAGES PARSER] Found columns:")
            print(f"  Source/Platform: {source_col}")
            print(f"  Message: {message_col}")
            print(f"  Timestamp: {timestamp_col}")
            print(f"  Sender: {sender_col}")
            print(f"  Receiver: {receiver_col}")
            print(f"  Thread ID: {thread_id_col}")
            
            if not source_col:
                logger.warning(f"[OXYGEN MESSAGES PARSER] No Source/Platform column found!")
                print(f"[OXYGEN MESSAGES PARSER] WARNING: No Source/Platform column found!")
            
            if not message_col:
                logger.warning(f"[OXYGEN MESSAGES PARSER] No Message column found!")
                print(f"[OXYGEN MESSAGES PARSER] WARNING: No Message column found!")
            
            for idx, row in df.iterrows():
                first_val = self._clean(row.get(df.columns[0], ''))
                if first_val and first_val.lower() in ['source', 'service', 'platform', 'application', 'message', 'timestamp']:
                    continue
                
                platform = None
                if source_col:
                    source = self._clean(row.get(source_col, ''))
                    if source:
                        source_lower = source.lower().strip()
                        
                        if 'whatsapp' in source_lower:
                            platform = "whatsapp"
                        # Check for Telegram
                        elif 'telegram' in source_lower:
                            platform = "telegram"
                        # Check for Instagram
                        elif 'instagram' in source_lower:
                            platform = "instagram"
                        elif 'twitter' in source_lower:
                            platform = "x"
                        elif source_lower == 'x' or source_lower.startswith('x '):
                            platform = "x"
                        # Check for TikTok
                        elif 'tiktok' in source_lower:
                            platform = "tiktok"
                        elif 'facebook' in source_lower or 'messenger' in source_lower:
                            platform = "facebook"
                
                if not platform:
                    skipped_count += 1
                    if skipped_count <= 10:
                        source_val = self._clean(row.get(source_col, '')) if source_col else 'N/A'
                        logger.debug(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - no platform detected. Source value: '{source_val}'")
                        print(f"[OXYGEN MESSAGES PARSER] Row {idx} skipped - no platform. Source: '{source_val}'")
                    continue
                
                if platform_counts.get(platform, 0) == 0:
                    source_val = self._clean(row.get(source_col, '')) if source_col else 'N/A'
                    logger.info(f"[OXYGEN MESSAGES PARSER] First {platform} message detected from Source: '{source_val}'")
                    print(f"[OXYGEN MESSAGES PARSER] First {platform} message detected from Source: '{source_val}'")
                
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                # Extract message text
                message_text = None
                if message_col:
                    message_text = self._clean(row.get(message_col))
                else:
                    # Scan columns for message content
                    for col in df.columns:
                        val = self._clean(row.get(col))
                        if val and len(val.strip()) > 10:
                            if not val.replace(':', '').replace('-', '').replace('/', '').replace(' ', '').isdigit():
                                if any(c.isalpha() for c in val[:50]):
                                    message_text = val
                                    break
                
                if not message_text:
                    skipped_count += 1
                    continue
                
                # Extract other fields
                timestamp = self._clean(row.get(timestamp_col)) if timestamp_col else None
                sender = self._clean(row.get(sender_col)) if sender_col else None
                
                # Extract thread/chat identifier
                thread_id = None
                if thread_id_col:
                    thread_id = self._clean(row.get(thread_id_col, ''))
                
                if not thread_id:
                    # Try common column names
                    thread_id = self._clean(row.get('Thread ID', '')) or \
                                  self._clean(row.get('Chat ID', '')) or \
                                  self._clean(row.get('Identifier', '')) or \
                                  self._clean(row.get('Message ID', ''))
                
                # Extract sender and receiver from participant columns
                sender_name = None
                sender_id = None
                receiver_name = None
                receiver_id = None
                
                if sender_col:
                    sender_data = self._clean(row.get(sender_col, ''))
                    if sender_data:
                        # Extract name and JID from format: "Name <+6281779323003@s.whatsapp.net>"
                        import re
                        name_match = re.search(r'^([^<]+)', sender_data)
                        jid_match = re.search(r'<([^>]+)>', sender_data)
                        if name_match:
                            sender_name = name_match.group(1).strip()
                        if jid_match:
                            sender_id = jid_match.group(1).strip()
                
                if receiver_col:
                    receiver_data = self._clean(row.get(receiver_col, ''))
                    if receiver_data:
                        # Extract name and JID from format: "Name <+6281779323003@s.whatsapp.net>"
                        import re
                        name_match = re.search(r'^([^<]+)', receiver_data)
                        jid_match = re.search(r'<([^>]+)>', receiver_data)
                        if name_match:
                            receiver_name = name_match.group(1).strip()
                        if jid_match:
                            receiver_id = jid_match.group(1).strip()
                
                # If sender/receiver not found from participant columns, try sender_col fallback
                if not sender_name and sender_col:
                    sender_name = self._clean(row.get(sender_col, ''))
                if not receiver_name and receiver_col:
                    receiver_name = self._clean(row.get(receiver_col, ''))
                
                message_id = self._generate_oxygen_message_id(platform, row, file_id, idx)
                
                message_data = {
                    "file_id": file_id,
                    "platform": platform,
                    "message_text": message_text,
                    "sender_name": sender_name or sender,
                    "sender_id": sender_id or self._clean(row.get('Sender ID', '')),
                    "receiver_name": receiver_name or self._clean(row.get('Recipient', '')) or self._clean(row.get('Receiver', '')),
                    "receiver_id": receiver_id or self._clean(row.get('Recipient ID', '')) or self._clean(row.get('Receiver ID', '')),
                    "timestamp": timestamp,
                    "thread_id": thread_id,
                    "chat_id": thread_id,
                    "message_id": message_id,
                    "message_type": self._clean(row.get('Message Type', '')) or self._clean(row.get('Message Status', '')) or 'text',
                    "direction": self._clean(row.get('Direction', '')),
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                if platform_counts[platform] == 1:
                    logger.debug(f"[OXYGEN MESSAGES PARSER] First {platform} message: message_id={message_data['message_id']}, "
                               f"sender={message_data['sender_name']}, text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN MESSAGES PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            logger.info(f"[OXYGEN MESSAGES PARSER] Platform breakdown: {platform_counts}")
            print(f"[OXYGEN MESSAGES PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            print(f"[OXYGEN MESSAGES PARSER] Platform breakdown: {platform_counts}")
            
        except Exception as e:
            logger.error(f"[OXYGEN MESSAGES PARSER] Error parsing Messages sheet: {e}", exc_info=True)
            print(f"[OXYGEN MESSAGES PARSER] Error parsing Messages sheet: {e}")
            import traceback
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
                                # Extract message after keyword
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
                        "platform": "whatsapp",
                        "message_text": message_text,
                        "sender_name": contact_name,
                        "sender_id": phone_number,
                        "receiver_name": None,
                        "receiver_id": None,
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
                                if any(c.isalpha() for c in val[:50]):  # Has alphabetic characters
                                    message_text = val
                                    break
                
                if not message_text:
                    skip_reasons['no_message'] += 1
                    skipped_count += 1
                    continue
                
                timestamp = self._clean(row.get(timestamp_col)) if timestamp_col else None
                if not timestamp:
                    for col in df.columns[:10]:
                        val = self._clean(row.get(col))
                        if val and ('/' in val or ':' in val) and len(val) > 8:
                            # Might be timestamp
                            if any(c.isdigit() for c in val):
                                timestamp = val
                                break
                
                sender = self._clean(row.get(sender_col)) if sender_col else None
                direction = self._clean(row.get(direction_col)) if direction_col else None

                thread_id = self._clean(row.get('Thread ID', '')) or \
                          self._clean(row.get('Chat ID', '')) or \
                          self._clean(row.get('Identifier', '')) or \
                          self._clean(row.get('Contact', ''))
                
                message_id = self._generate_oxygen_message_id("whatsapp", row, file_id, idx)
                
                message_data = {
                    "file_id": file_id,
                    "platform": "whatsapp",
                    "message_text": message_text,
                    "sender_name": sender,
                    "sender_id": None,
                    "receiver_name": None,
                    "receiver_id": None,
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
                               f"sender={message_data['sender_name']}, text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN WHATSAPP PARSER] Processed {processed_count} messages, skipped {skipped_count} rows, reasons: {skip_reasons}")
            
        except Exception as e:
            logger.error(f"[OXYGEN WHATSAPP PARSER] Error parsing WhatsApp messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Oxygen WhatsApp messages: {e}")
            import traceback
            traceback.print_exc()
        
        return results

    def _generate_oxygen_message_id(self, platform: str, row: pd.Series, file_id: int, index: int) -> str:
        # Try to get existing message_id from various columns
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
            logger.debug(f"[OXYGEN TELEGRAM PARSER] Sheet loaded: {len(df)} rows")
            
            processed_count = 0
            skipped_count = 0

            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', '')) or \
                              self._clean(row.get('Body', '')) or \
                              self._clean(row.get('Text', ''))
                
                if not message_text:
                    skipped_count += 1
                    continue
                
                timestamp = self._clean(row.get('Timestamp', '')) or \
                          self._clean(row.get('Date/Time', ''))
                sender = self._clean(row.get('Sender', '')) or \
                        self._clean(row.get('From', ''))
                
                message_data = {
                    "file_id": file_id,
                    "platform": "telegram",
                    "message_text": message_text,
                    "sender_name": sender,
                    "sender_id": self._clean(row.get('Sender ID', '')),
                    "receiver_name": None,
                    "receiver_id": None,
                    "timestamp": timestamp,
                    "thread_id": self._clean(row.get('Chat ID', '')),
                    "chat_id": self._clean(row.get('Chat ID', '')),
                    "message_id": self._generate_oxygen_message_id("telegram", row, file_id, idx),
                    "message_type": "text",
                    "direction": self._clean(row.get('Direction', '')),
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN TELEGRAM PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            
        except Exception as e:
            logger.error(f"[OXYGEN TELEGRAM PARSER] Error parsing Telegram messages from {sheet_name}: {e}", exc_info=True)
        
        return results

    def _parse_oxygen_instagram_messages(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[OXYGEN INSTAGRAM PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN INSTAGRAM PARSER] Sheet loaded: {len(df)} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Message', '')) or \
                              self._clean(row.get('Body', ''))
                
                if not message_text:
                    skipped_count += 1
                    continue
                
                message_data = {
                    "file_id": file_id,
                    "platform": "instagram",
                    "message_text": message_text,
                    "sender_name": self._clean(row.get('Sender', '')),
                    "sender_id": None,
                    "receiver_name": self._clean(row.get('Recipient', '')),
                    "receiver_id": None,
                    "timestamp": self._clean(row.get('Timestamp', '')),
                    "thread_id": self._clean(row.get('Thread ID', '')),
                    "chat_id": self._clean(row.get('Chat ID', '')),
                    "message_id": self._generate_oxygen_message_id("instagram", row, file_id, idx),
                    "message_type": "text",
                    "direction": self._clean(row.get('Direction', '')),
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN INSTAGRAM PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            
        except Exception as e:
            logger.error(f"[OXYGEN INSTAGRAM PARSER] Error parsing Instagram messages from {sheet_name}: {e}", exc_info=True)
        
        return results

    def _parse_oxygen_twitter_messages(self, file_path: str, sheet_name: str, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[OXYGEN TWITTER PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
            logger.debug(f"[OXYGEN TWITTER PARSER] Sheet loaded: {len(df)} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                message_text = self._clean(row.get('Text', '')) or \
                              self._clean(row.get('Message', ''))
                
                if not message_text:
                    skipped_count += 1
                    continue
                
                message_data = {
                    "file_id": file_id,
                    "platform": "x",
                    "message_text": message_text,
                    "sender_name": self._clean(row.get('Sender', '')),
                    "sender_id": self._clean(row.get('Sender ID', '')),
                    "receiver_name": self._clean(row.get('Recipient', '')),
                    "receiver_id": self._clean(row.get('Recipient ID', '')),
                    "timestamp": self._clean(row.get('Timestamp', '')),
                    "thread_id": self._clean(row.get('Thread ID', '')),
                    "chat_id": self._clean(row.get('Chat ID', '')),
                    "message_id": self._generate_oxygen_message_id("x", row, file_id, idx),
                    "message_type": "text",
                    "direction": self._clean(row.get('Direction', '')),
                    "source_tool": "oxygen",
                    "sheet_name": sheet_name
                }
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[OXYGEN TWITTER PARSER] Processed {processed_count} messages, skipped {skipped_count} rows")
            
        except Exception as e:
            logger.error(f"[OXYGEN TWITTER PARSER] Error parsing Twitter messages from {sheet_name}: {e}", exc_info=True)
        
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
                
                message_data = {
                    "file_id": file_id,
                    "platform": "tiktok",
                    "message_text": message_text,
                    "sender_name": self._clean(row.get('Sender', '')),
                    "sender_id": None,
                    "receiver_name": self._clean(row.get('Recipient', '')),
                    "receiver_id": None,
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
                
                message_data = {
                    "file_id": file_id,
                    "platform": "facebook",
                    "message_text": message_text,
                    "sender_name": self._clean(row.get('Sender', '')),
                    "sender_id": self._clean(row.get('Sender ID', '')),
                    "receiver_name": self._clean(row.get('Recipient', '')),
                    "receiver_id": self._clean(row.get('Recipient ID', '')),
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
            
            if 'Telegram Messages - iOS' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Telegram Messages sheet, parsing...")
                telegram_results = self._parse_telegram_messages(file_path, 'Telegram Messages - iOS', file_id)
                results.extend(telegram_results)
                logger.info(f"[CHAT PARSER] Telegram: Parsed {len(telegram_results)} messages")
            else:
                logger.warning(f"[CHAT PARSER] Telegram Messages - iOS sheet not found")
            
            if 'Instagram Direct Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Instagram Direct Messages sheet, parsing...")
                instagram_results = self._parse_instagram_messages(file_path, 'Instagram Direct Messages', file_id)
                results.extend(instagram_results)
                logger.info(f"[CHAT PARSER] Instagram: Parsed {len(instagram_results)} messages")
            else:
                logger.warning(f"[CHAT PARSER] Instagram Direct Messages sheet not found")
            
            if 'TikTok Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found TikTok Messages sheet, parsing...")
                tiktok_results = self._parse_tiktok_messages(file_path, 'TikTok Messages', file_id)
                results.extend(tiktok_results)
                logger.info(f"[CHAT PARSER] TikTok: Parsed {len(tiktok_results)} messages")
            else:
                logger.warning(f"[CHAT PARSER] TikTok Messages sheet not found")

            if 'Twitter Direct Messages' in xls.sheet_names:
                logger.info(f"[CHAT PARSER] Found Twitter Direct Messages sheet, parsing...")
                twitter_results = self._parse_twitter_messages(file_path, 'Twitter Direct Messages', file_id)
                results.extend(twitter_results)
                logger.info(f"[CHAT PARSER] Twitter/X: Parsed {len(twitter_results)} messages")
            else:
                logger.warning(f"[CHAT PARSER] Twitter Direct Messages sheet not found")
            
            logger.info(f"[CHAT PARSER] Total parsed messages: {len(results)}")

            if results:
                sample_msg = results[0]
                logger.debug(f"[CHAT PARSER] Sample message data: platform={sample_msg.get('platform')}, "
                           f"sheet_name={sample_msg.get('sheet_name')}, "
                           f"message_id={sample_msg.get('message_id')}, "
                           f"sender={sample_msg.get('sender_name')}, "
                           f"receiver={sample_msg.get('receiver_name')}, "
                           f"timestamp={sample_msg.get('timestamp')}")
            
            saved_count = 0
            skipped_count = 0
            for msg in results:
                existing = (
                    self.db.query(ChatMessage)
                    .filter(
                        ChatMessage.platform == msg["platform"],
                        ChatMessage.message_id == msg["message_id"],
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
            logger.debug(f"[TELEGRAM PARSER] Sheet loaded: {len(df)} rows, columns: {list(df.columns)[:10]}")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                if pd.isna(row.get('Message')) or not str(row.get('Message')).strip():
                    skipped_count += 1
                    continue
                
                message_data = {                    "file_id": file_id,
                    "platform": "telegram",
                    "message_text": str(row.get('Message', '')),
                    "sender_name": str(row.get('Sender Name', '')),
                    "sender_id": str(row.get('Sender ID', '')),
                    "receiver_name": str(row.get('Recipient Name', '')),
                    "receiver_id": str(row.get('Recipient ID', '')),
                    "timestamp": str(row.get('Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "thread_id": str(row.get('_ThreadID', '')),
                    "chat_id": str(row.get('Chat ID', '')),
                    "message_id": str(row.get('Message ID', '')),
                    "message_type": str(row.get('Type', 'text')),
                    "direction": str(row.get('Direction', '')),
                    "source_tool": "axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[TELEGRAM PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"sender={message_data['sender_name']}, receiver={message_data['receiver_name']}, "
                               f"text_preview={str(message_data['message_text'])[:50]}...")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[TELEGRAM PARSER] Processed {processed_count} messages, skipped {skipped_count} empty rows")
        
        except Exception as e:
            logger.error(f"[TELEGRAM PARSER] Error parsing Telegram messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Telegram messages: {e}")
        
        return results

    def _parse_instagram_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[INSTAGRAM PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            logger.debug(f"[INSTAGRAM PARSER] Sheet loaded: {len(df)} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                if pd.isna(row.get('Message')) or not str(row.get('Message')).strip():
                    skipped_count += 1
                    continue
                
                message_data = {                    
                    "file_id": file_id,
                    "platform": "instagram",
                    "message_text": str(row.get('Message', '')),
                    "sender_name": str(row.get('Sender', '')),
                    "sender_id": "",
                    "receiver_name": str(row.get('Recipient', '')),
                    "receiver_id": "",
                    "timestamp": str(row.get('Message Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "thread_id": str(row.get('_ThreadID', '')),
                    "chat_id": str(row.get('Chat ID', '')),
                    "message_id": str(row.get('Item ID', '')),
                    "message_type": str(row.get('Type', 'text')),
                    "direction": str(row.get('Direction', '')),
                    "source_tool": "axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[INSTAGRAM PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"sender={message_data['sender_name']}, receiver={message_data['receiver_name']}")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[INSTAGRAM PARSER] Processed {processed_count} messages, skipped {skipped_count} empty rows")
        
        except Exception as e:
            logger.error(f"[INSTAGRAM PARSER] Error parsing Instagram messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Instagram messages: {e}")
        
        return results

    def _parse_tiktok_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[TIKTOK PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            logger.debug(f"[TIKTOK PARSER] Sheet loaded: {len(df)} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                if pd.isna(row.get('Message')) or not str(row.get('Message')).strip():
                    skipped_count += 1
                    continue
                
                message_data = {                    "file_id": file_id,
                    "platform": "tiktok",
                    "message_text": str(row.get('Message', '')),
                    "sender_name": str(row.get('Sender', '')),
                    "sender_id": "",
                    "receiver_name": str(row.get('Recipient', '')),
                    "receiver_id": "",
                    "timestamp": str(row.get('Created Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "thread_id": str(row.get('_ThreadID', '')),
                    "chat_id": "",
                    "message_id": str(row.get('Item ID', '')),
                    "message_type": str(row.get('Message Type', 'text')),
                    "direction": "",
                    "source_tool": "axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[TIKTOK PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"sender={message_data['sender_name']}, receiver={message_data['receiver_name']}")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[TIKTOK PARSER] Processed {processed_count} messages, skipped {skipped_count} empty rows")
        
        except Exception as e:
            logger.error(f"[TIKTOK PARSER] Error parsing TikTok messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing TikTok messages: {e}")
        
        return results

    def _parse_twitter_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            logger.debug(f"[TWITTER/X PARSER] Reading sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            logger.debug(f"[TWITTER/X PARSER] Sheet loaded: {len(df)} rows")
            
            processed_count = 0
            skipped_count = 0
            
            for idx, row in df.iterrows():
                if pd.isna(row.get('Text')) or not str(row.get('Text')).strip():
                    skipped_count += 1
                    continue
                
                message_data = {                    "file_id": file_id,
                    "platform": "x",
                    "message_text": str(row.get('Text', '')),
                    "sender_name": str(row.get('Sender Name', '')),
                    "sender_id": str(row.get('Sender ID', '')),
                    "receiver_name": str(row.get('Recipient Name(s)', '')),
                    "receiver_id": str(row.get('Recipient ID(s)', '')),
                    "timestamp": str(row.get('Sent/Received Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "thread_id": str(row.get('_ThreadID', '')),
                    "chat_id": "",
                    "message_id": str(row.get('Item ID', '')),
                    "message_type": "text",
                    "direction": str(row.get('Direction', '')),
                    "source_tool": "axiom",
                    "sheet_name": sheet_name
                }
                
                if processed_count == 0:
                    logger.debug(f"[TWITTER/X PARSER] First message sample: message_id={message_data['message_id']}, "
                               f"sender={message_data['sender_name']}, receiver={message_data['receiver_name']}")
                
                results.append(message_data)
                processed_count += 1
            
            logger.info(f"[TWITTER/X PARSER] Processed {processed_count} messages, skipped {skipped_count} empty rows")
        
        except Exception as e:
            logger.error(f"[TWITTER/X PARSER] Error parsing Twitter messages from {sheet_name}: {e}", exc_info=True)
            print(f"Error parsing Twitter messages: {e}")
        
        return results

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
                        "platform": "whatsapp",
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
                        "platform": "whatsapp",
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
                        "platform": "whatsapp",
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
            
            # Fix column names if they are unnamed
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
                        "platform": "whatsapp",
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
                        "platform": "whatsapp",
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
                        "platform": "telegram",
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
                        "platform": "telegram",
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
                        "platform": "telegram",
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
            
            # Fix column names if they are unnamed
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
                        "platform": "telegram",
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
