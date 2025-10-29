import re
import pandas as pd  # type: ignore
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session  # type: ignore
from app.analytics.device_management.models import SocialMedia, ChatMessage
from app.db.session import get_db
from .file_validator import file_validator

import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', message='.*OLE2 inconsistency.*')
warnings.filterwarnings('ignore', message='.*file size.*not.*multiple of sector size.*')
warnings.filterwarnings('ignore', message='.*SSCS size is 0 but SSAT size is non-zero.*')
warnings.filterwarnings('ignore', message='.*WARNING \*\*\*.*')

SOCIAL_MEDIA_PLATFORMS = ["instagram", "facebook", "whatsapp", "telegram", "x", "tiktok"]

class SocialMediaParser:

    def __init__(self, db: Session):
        self.db = db

    def parse_oxygen_ufed_social_media(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []

        try:
            # Read Excel file
            xls = pd.ExcelFile(file_path, engine='xlrd')
            
            # Parse Contacts sheet for social media accounts
            if 'Contacts ' in xls.sheet_names:
                contacts_df = pd.read_excel(file_path, sheet_name='Contacts ', dtype=str, engine='xlrd')
                
                # Filter for ALL social media records (Account, Group, Contact)
                social_platforms = ['X (Twitter)', 'Instagram', 'Telegram Messenger', 'Facebook', 'WhatsApp', 'TikTok']
                social_accounts = contacts_df[contacts_df['Source'].isin(social_platforms)]
                
                for _, row in social_accounts.iterrows():
                    source = self._clean(row.get('Source', ''))
                    contact = self._clean(row.get('Contact', ''))
                    phones_emails = self._clean(row.get('Phones & Emails', ''))
                    internet = self._clean(row.get('Internet', ''))
                    
                    if not source or not contact:
                        continue
                    
                    # Determine platform based on source
                    platform = self._determine_platform_from_source(source)
                    if not platform:
                        continue
                    
                    # Extract account information with enhanced parsing
                    account_name = self._extract_account_name_enhanced(contact, platform, phones_emails, internet)
                    account_id = self._extract_account_id_enhanced(contact, platform, phones_emails, internet)
                    user_id = self._extract_user_id_enhanced(contact, platform, phones_emails, internet)
                    
                    if account_name:
                        acc = {
                            "platform": platform,
                            "account_name": account_name,
                            "account_id": account_id,
                            "user_id": user_id,
                            "full_name": account_name,
                            "source_tool": "Oxygen",
                            "sheet_name": "Contacts",
                            "file_id": file_id,
                        }
                        results.append(acc)
            
            # Save to database in batches using the same session
            batch_size = 50
            saved_count = 0
            
            for i in range(0, len(results), batch_size):
                batch = results[i:i + batch_size]
                
                try:
                    for acc in batch:
                        existing = (
                            self.db.query(SocialMedia)
                            .filter(
                                SocialMedia.account_name == acc["account_name"],
                                SocialMedia.platform == acc["platform"],
                                SocialMedia.file_id == file_id,
                            )
                            .first()
                        )
                        if not existing:
                            self.db.add(SocialMedia(**acc))
                    
                    self.db.commit()
                    saved_count += len(batch)
                    print(f"Saved batch {i//batch_size + 1}: {len(batch)} records (Total: {saved_count})")
                    
                except Exception as batch_error:
                    print(f"Error saving batch {i//batch_size + 1}: {batch_error}")
                    self.db.rollback()
                    raise batch_error
            
            print(f"Successfully saved {saved_count} Oxygen UFED social media accounts to database")

        except Exception as e:
            print(f"Error parsing Oxygen UFED social media: {e}")
            self.db.rollback()
            # Get a fresh session for retry
            self.db = next(get_db())
            raise e
        
        return results
    
    def _determine_platform_from_source(self, source: str) -> str:
        source_lower = source.lower()
        
        if 'instagram' in source_lower:
            return 'instagram'
        elif 'twitter' in source_lower or 'x (' in source_lower:
            return 'x'
        elif 'telegram' in source_lower:
            return 'telegram'
        elif 'facebook' in source_lower:
            return 'facebook'
        elif 'whatsapp' in source_lower:
            return 'whatsapp'
        elif 'tiktok' in source_lower:
            return 'tiktok'
        
        return None
    
    def _extract_account_name(self, contact: str, platform: str) -> str:
        if not contact:
            return None
        
        # Remove common suffixes
        contact = contact.replace('\\r\\n', '').strip()
        
        # For different platforms, extract differently
        if platform == 'instagram':
            # Look for Instagram ID pattern first
            if 'Instagram ID:' in contact:
                parts = contact.split('Instagram ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        elif platform == 'x':
            # Look for nickname pattern
            if 'Nickname:' in contact:
                parts = contact.split('Nickname:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        elif platform == 'telegram':
            # Return the first line (usually the name)
            return contact.split('\\n')[0].strip()
        
        # Default: return first line
        return contact.split('\\n')[0].strip()
    
    def _extract_account_id(self, contact: str, platform: str) -> str:
        # For most platforms, account ID is same as account name
        return self._extract_account_name(contact, platform)
    
    def _extract_account_id_from_contact(self, contact: str, platform: str) -> str:
        if not contact:
            return None
        
        # Remove common suffixes and clean up
        contact = contact.replace('\\r\\n', '').strip()
        
        # Look for specific patterns based on platform
        if platform == 'instagram':
            # Look for Instagram ID pattern
            if 'Instagram ID:' in contact:
                parts = contact.split('Instagram ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        elif platform == 'x':
            # Look for X ID pattern
            if 'X ID:' in contact:
                parts = contact.split('X ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Look for nickname pattern
            if 'Nickname:' in contact:
                parts = contact.split('Nickname:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        elif platform == 'telegram':
            # Look for Telegram ID pattern
            if 'Telegram ID:' in contact:
                parts = contact.split('Telegram ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        # Default: return first line
        return contact.split('\\n')[0].strip()
    
    def _extract_user_id_from_contact(self, contact: str, platform: str) -> str:
        # For most cases, user ID is same as account ID
        return self._extract_account_id_from_contact(contact, platform)
    
    def _extract_account_name_enhanced(self, contact: str, platform: str, phones_emails: str, internet: str) -> str:
        if not contact:
            return None
        
        # Remove common suffixes and clean up
        contact = contact.replace('\\r\\n', '').strip()
        phones_emails = phones_emails or ''
        internet = internet or ''
        
        # For different platforms, extract differently
        if platform == 'instagram':
            # Look for Instagram ID pattern first
            if 'Instagram ID:' in internet:
                parts = internet.split('Instagram ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        elif platform == 'x':
            # Look for nickname pattern first
            if 'Nickname:' in contact:
                parts = contact.split('Nickname:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        elif platform == 'telegram':
            # Return the first line (usually the name)
            return contact.split('\\n')[0].strip()
        
        # Default: return first line
        return contact.split('\\n')[0].strip()
    
    def _extract_account_id_enhanced(self, contact: str, platform: str, phones_emails: str, internet: str) -> str:
        if not contact:
            return None
        
        # Remove common suffixes and clean up
        contact = contact.replace('\\r\\n', '').strip()
        phones_emails = phones_emails or ''
        internet = internet or ''
        
        # Look for specific patterns based on platform
        if platform == 'instagram':
            # Look for Instagram ID pattern
            if 'Instagram ID:' in internet:
                parts = internet.split('Instagram ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        elif platform == 'x':
            # Look for X ID pattern
            if 'X ID:' in phones_emails:
                parts = phones_emails.split('X ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Look for nickname pattern
            if 'Nickname:' in contact:
                parts = contact.split('Nickname:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        elif platform == 'telegram':
            # Look for Telegram ID pattern
            if 'Telegram ID:' in internet:
                parts = internet.split('Telegram ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            # Otherwise return the first line
            return contact.split('\\n')[0].strip()
        
        # Default: return first line
        return contact.split('\\n')[0].strip()
    
    def _extract_user_id_enhanced(self, contact: str, platform: str, phones_emails: str, internet: str) -> str:
        # For most cases, user ID is same as account ID
        return self._extract_account_id_enhanced(contact, platform, phones_emails, internet)
    
    def _parse_oxygen_instagram_sheet(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name='Instagram ', dtype=str, engine='xlrd')
            
            # Skip header rows and look for actual user data
            skip_keywords = ['identifier', 'user data', 'version', 'container type', 'container', 
                           'purchase date', 'apple id', 'genre', 'copyright', 'passwords', 'accounts', 
                           'categories', 'following', 'feed', 'stories', 'messages', 'media', 'contacts',
                           'chats', 'group', 'event log', 'cache', 'images', 'others', 'private', 'info']
            
            for _, row in df.iterrows():
                instagram_col = self._clean(row.get('Instagram', ''))
                
                if instagram_col and instagram_col.lower() not in skip_keywords:
                    # Check if this looks like a real username (not too long, contains alphanumeric, no backslashes)
                    if (len(instagram_col) <= 30 and 
                        any(c.isalnum() for c in instagram_col) and 
                        '\\' not in instagram_col and
                        '/' not in instagram_col):
                        acc = {
                            "platform": "instagram",
                            "account_name": instagram_col,
                            "account_id": instagram_col,
                            "user_id": instagram_col,
                            "full_name": instagram_col,
                            "source_tool": "Oxygen",
                            "sheet_name": "Instagram",                            "file_id": file_id,
                        }
                        results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing Instagram sheet: {e}")
        
        return results
    
    def _parse_oxygen_telegram_sheet(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name='Telegram Messenger ', dtype=str, engine='xlrd')
            
            # Skip header rows and look for actual user data
            skip_keywords = ['identifier', 'user data', 'version', 'container type', 'container', 
                           'purchase date', 'apple id', 'genre', 'copyright', 'passwords', 'accounts', 
                           'categories', 'following', 'feed', 'stories', 'messages', 'media', 'contacts',
                           'chats', 'group', 'event log', 'cache', 'images', 'others', 'private', 'info']
            
            for _, row in df.iterrows():
                telegram_col = self._clean(row.get('Telegram Messenger', ''))
                
                if telegram_col and telegram_col.lower() not in skip_keywords:
                    # Check if this looks like a real username (not too long, contains alphanumeric, no backslashes)
                    if (len(telegram_col) <= 30 and 
                        any(c.isalnum() for c in telegram_col) and 
                        '\\' not in telegram_col and
                        '/' not in telegram_col):
                        acc = {
                            "platform": "telegram",
                            "account_name": telegram_col,
                            "account_id": telegram_col,
                            "user_id": telegram_col,
                            "full_name": telegram_col,
                            "source_tool": "Oxygen",
                            "sheet_name": "Telegram Messenger",                            "file_id": file_id,
                        }
                        results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing Telegram sheet: {e}")
        
        return results
    
    def _parse_oxygen_twitter_sheet(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name='X (Twitter) ', dtype=str, engine='xlrd')
            
            # Skip header rows and look for actual user data
            skip_keywords = ['identifier', 'user data', 'version', 'container type', 'container', 
                           'purchase date', 'apple id', 'genre', 'copyright', 'passwords', 'accounts', 
                           'categories', 'following', 'feed', 'stories', 'messages', 'media', 'contacts',
                           'chats', 'group', 'event log', 'cache', 'images', 'others', 'private', 'info']
            
            for _, row in df.iterrows():
                twitter_col = self._clean(row.get('X (Twitter)', ''))
                
                if twitter_col and twitter_col.lower() not in skip_keywords:
                    # Check if this looks like a real username (not too long, contains alphanumeric, no backslashes)
                    if (len(twitter_col) <= 30 and 
                        any(c.isalnum() for c in twitter_col) and 
                        '\\' not in twitter_col and
                        '/' not in twitter_col):
                        acc = {
                            "platform": "x",
                            "account_name": twitter_col,
                            "account_id": twitter_col,
                            "user_id": twitter_col,
                            "full_name": twitter_col,
                            "source_tool": "Oxygen",
                            "sheet_name": "X (Twitter)",                            "file_id": file_id,
                        }
                        results.append(acc)
                    
        except Exception as e:
            print(f"Error parsing X (Twitter) sheet: {e}")
        
        return results

    def parse_oxygen_social_media(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []

        validation = file_validator.validate_excel_file(Path(file_path))
        file_validator.print_validation_summary(validation)

        if not validation["is_valid"]:
            print(f"File validation failed: {validation['errors']}")
            if validation["warnings"]:
                print(f"Warnings: {validation['warnings']}")

        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                # Determine engine based on file extension
                file_path_obj = Path(file_path)
                file_extension = file_path_obj.suffix.lower()
                if file_extension == '.xls':
                    engine = "xlrd"
                else:
                    engine = "openpyxl"
                
                xls = pd.ExcelFile(file_path, engine=engine)
                sheet_name = file_validator._find_contacts_sheet(xls.sheet_names)

            if not sheet_name:
                return results

            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine)

            for _, row in df.iterrows():
                type_field = self._clean(row.get("Type"))
                if not type_field:
                    continue

                if type_field.lower() not in ["contact", "contact (merged)"]:
                    continue

                contact_field = self._clean(row.get("Contact"))
                internet_field = self._clean(row.get("Internet"))
                phones_emails_field = self._clean(row.get("Phones & Emails"))
                source_field = self._clean(row.get("Source"))

                if not source_field:
                    continue

                detected_platforms = self._extract_multiple_platforms(source_field)
                if not detected_platforms:
                    continue

                account_name = self._extract_name(contact_field)

                following = self._extract_following_count(contact_field, internet_field, phones_emails_field)
                followers = self._extract_followers_count(contact_field, internet_field, phones_emails_field)
                friends = self._extract_friends_count(contact_field, internet_field, phones_emails_field)
                statuses = self._extract_statuses_count(contact_field, internet_field, phones_emails_field)
                phone_number = self._extract_phone_number(phones_emails_field)
                email = self._extract_email(phones_emails_field)
                biography = self._extract_biography(contact_field, internet_field, phones_emails_field)
                profile_picture_url = self._extract_profile_picture_url(internet_field)
                is_private = self._extract_is_private(contact_field, internet_field, phones_emails_field)
                is_local_user = self._extract_is_local_user(contact_field, internet_field, phones_emails_field)
                chat_content = self._extract_chat_content(contact_field, internet_field, phones_emails_field)
                last_message = self._extract_last_message(contact_field, internet_field, phones_emails_field)
                other_info = self._extract_other_info(contact_field, internet_field, phones_emails_field)

                for platform in detected_platforms:
                    account_id = self._extract_account_id(internet_field, platform)
                    if not account_id:
                        account_id = self._extract_account_id(phones_emails_field, platform)
                    
                    user_id = self._extract_user_id(internet_field, phones_emails_field, platform)
                    full_name = self._extract_full_name(contact_field)

                    if not account_id and not account_name:
                        continue

                    acc = {
                        "platform": platform,
                        "account_name": account_name,
                        "account_id": account_id,
                        "user_id": user_id,
                        "full_name": full_name,
                        "following": following,
                        "followers": followers,
                        "friends": friends,
                        "statuses": statuses,
                        "phone_number": phone_number,
                        "email": email,
                        "biography": biography,
                        "profile_picture_url": profile_picture_url,
                        "is_private": is_private,
                        "is_local_user": is_local_user,
                        "chat_content": chat_content,
                        "last_message": last_message,
                        "other_info": other_info,
                        "source_tool": "Oxygen",
                        "sheet_name": sheet_name,                        "file_id": file_id,
                    }
                    results.append(acc)

                    # Note: Database saving will be done in batches after parsing all data
                    pass

            # Save to database in batches with fresh sessions
            batch_size = 50
            saved_count = 0
            
            for i in range(0, len(results), batch_size):
                batch = results[i:i + batch_size]
                
                try:
                    for acc in batch:
                        existing = (
                            self.db.query(SocialMedia)
                            .filter(
                                SocialMedia.platform == acc["platform"],
                                SocialMedia.account_id == acc["account_id"],
                            )
                            .first()
                        )
                        if not existing:
                            self.db.add(SocialMedia(**acc))
                    
                    self.db.commit()
                    saved_count += len(batch)
                    print(f"Saved batch {i//batch_size + 1}: {len(batch)} records (Total: {saved_count})")
                    
                except Exception as batch_error:
                    print(f"Error saving batch {i//batch_size + 1}: {batch_error}")
                    self.db.rollback()
                    raise batch_error
            
            print(f"Successfully saved {saved_count} Oxygen social media accounts to database")

        except Exception as e:
            print(f"Error parsing social media Oxygen: {e}")

        return results

    def _extract_multiple_platforms(self, text: str) -> List[str]:
        if not text:
            return []

        text_lower = text.lower()

        text_lower = text_lower.replace("whatsapp messenger backup", "")

        found = []
        for platform in SOCIAL_MEDIA_PLATFORMS:
            if platform in text_lower:
                found.append(platform)
        if "twitter" in text_lower:
            found.append("x")

        return list(set(found))

    def _extract_name(self, contact_field: Optional[str]) -> Optional[str]:
        if not contact_field:
            return None
        lines = [l.strip() for l in contact_field.split("\n") if l.strip()]
        if not lines:
            return None

        for line in lines:
            if line.lower().startswith("nickname:"):
                return line.split(":", 1)[1].strip()
            if line.lower().startswith("full name:"):
                return line.split(":", 1)[1].strip()
        return lines[0]

    def _extract_account_id(self, text: Optional[str], platform: str) -> Optional[str]:
        if not text:
            return None

        patterns = {
            "instagram": r"Instagram ID:\s*(\S+)",
            "facebook": r"Facebook ID:\s*(\S+)",
            "telegram": r"Telegram ID:\s*(\S+)",
            "tiktok": r"TikTok ID:\s*(\S+)",
            "x": r"Account name:\s*(\S+)",
            "whatsapp": r"(WhatsApp|Phone)\s*(ID|number):\s*([+\d\s\-\(\)]+)",
        }

        pattern = patterns.get(platform)
        if not pattern:
            return None

        matches = re.findall(pattern, text, re.IGNORECASE)
        if not matches:
            return None

        match = matches[-1]
        if isinstance(match, tuple):
            value = match[-1].strip()
        else:
            value = match.strip()

        if platform == "whatsapp":
            return self._normalize_phone(value)
        return value

    def _normalize_phone(self, phone: str) -> str:
        if not phone:
            return phone
        phone = re.sub(r"[^\d+]", "", phone)
        if phone.startswith("+62"):
            return phone
        elif phone.startswith("62"):
            return f"+{phone}"
        elif phone.startswith("0"):
            return f"+62{phone[1:]}"
        return phone


    def _clean(self, text: Any) -> Optional[str]:
        if text is None or pd.isna(text):
            return None
        text = str(text).strip()
        if text.lower() in ["", "nan", "none"]:
            return None
        return text

    def _extract_following_count(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[int]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            # Pattern untuk following count
            patterns = [
                r'following[:\s]*(\d+)',
                r'following\s+(\d+)',
                r'follows[:\s]*(\d+)',
                r'following\s+count[:\s]*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        continue
        
        return None

    def _extract_followers_count(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[int]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            # Pattern untuk followers count
            patterns = [
                r'followers[:\s]*(\d+)',
                r'follower[:\s]*(\d+)',
                r'followers\s+count[:\s]*(\d+)',
                r'followed\s+by[:\s]*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        continue
        
        return None

    def _extract_chat_content(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[str]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            # Pattern untuk chat content
            patterns = [
                r'chat[:\s]*(.+?)(?:\n|$)',
                r'message[:\s]*(.+?)(?:\n|$)',
                r'conversation[:\s]*(.+?)(?:\n|$)',
                r'last\s+message[:\s]*(.+?)(?:\n|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    content = match.group(1).strip()
                    if content and len(content) > 3:
                        return content
        
        return None

    def _extract_friends_count(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[int]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            # Pattern untuk friends count
            patterns = [
                r'friends[:\s]*(\d+)',
                r'friend[:\s]*(\d+)',
                r'friends\s+count[:\s]*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        continue
        
        return None

    def _extract_statuses_count(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[int]:
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            # Pattern untuk statuses count
            patterns = [
                r'statuses[:\s]*(\d+)',
                r'posts[:\s]*(\d+)',
                r'tweets[:\s]*(\d+)',
                r'statuses\s+count[:\s]*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, field.lower())
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        continue
        
        return None

    def _extract_phone_number(self, phones_emails_field: Optional[str]) -> Optional[str]:
        if not phones_emails_field:
            return None
            
        # Pattern untuk phone number
        patterns = [
            r'phone\s+number[:\s]*(\+?\d{10,15})',
            r'mobile[:\s]*(\+?\d{10,15})',
            r'tel[:\s]*(\+?\d{10,15})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, phones_emails_field.lower())
            if match:
                return match.group(1)
        
        return None

    def _extract_email(self, phones_emails_field: Optional[str]) -> Optional[str]:
        if not phones_emails_field:
            return None
            
        # Pattern untuk email
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
                
            # Pattern untuk biography
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
            
        # Pattern untuk URL
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
                
            # Pattern untuk last message
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
                
            # Pattern untuk other info
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
                
            # Pattern untuk user ID berdasarkan platform
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
            
        # Pattern untuk full name
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
            # Baca file dengan engine openpyxl untuk .xlsx
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            # Parse setiap sheet khusus platform
            for sheet_name in xls.sheet_names:
                if 'Instagram Profiles' in sheet_name:
                    results.extend(self._parse_axiom_instagram_profiles(file_path, sheet_name, file_id))
                elif 'Twitter Users' in sheet_name:
                    results.extend(self._parse_axiom_twitter_users(file_path, sheet_name, file_id))
                elif 'Telegram Accounts' in sheet_name:
                    results.extend(self._parse_axiom_telegram_accounts(file_path, sheet_name, file_id))
                elif 'TikTok Contacts' in sheet_name:
                    results.extend(self._parse_axiom_tiktok_contacts(file_path, sheet_name, file_id))
                elif 'Facebook Contacts' in sheet_name:
                    results.extend(self._parse_axiom_facebook_contacts(file_path, sheet_name, file_id))
                elif 'Facebook User-Friends' in sheet_name:
                    results.extend(self._parse_axiom_facebook_users(file_path, sheet_name, file_id))
                elif 'WhatsApp Contacts' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_contacts(file_path, sheet_name, file_id))
                elif 'WhatsApp User Profiles' in sheet_name:
                    results.extend(self._parse_axiom_whatsapp_users(file_path, sheet_name, file_id))
            
            # Save to database in batches with fresh sessions
            batch_size = 50
            saved_count = 0
            
            for i in range(0, len(results), batch_size):
                batch = results[i:i + batch_size]
                
                try:
                    for acc in batch:
                        existing = (
                            self.db.query(SocialMedia)
                            .filter(
                                SocialMedia.platform == acc["platform"],
                                SocialMedia.account_id == acc["account_id"],
                                SocialMedia.file_id == acc["file_id"]
                            )
                            .first()
                        )
                        if not existing:
                            self.db.add(SocialMedia(**acc))
                    
                    self.db.commit()
                    saved_count += len(batch)
                    print(f"Saved batch {i//batch_size + 1}: {len(batch)} records (Total: {saved_count})")
                    
                except Exception as batch_error:
                    print(f"Error saving batch {i//batch_size + 1}: {batch_error}")
                    self.db.rollback()
                    raise batch_error
            
            print(f"Successfully saved {saved_count} Axiom social media accounts to database")
            
        except Exception as e:
            print(f"Error parsing Axiom social media: {e}")
            self.db.rollback()
            raise e
        
        return results
    
    def count_axiom_social_media(self, file_path: str) -> int:
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            total_count = 0
            
            for sheet_name in xls.sheet_names:
                if 'Instagram Profiles' in sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    total_count += len(df[df['User ID'].notna()])
                elif 'Twitter Users' in sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    total_count += len(df[df['User ID'].notna()])
                elif 'Telegram Accounts' in sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    total_count += len(df[df['Account ID'].notna()])
                elif 'TikTok Contacts' in sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    total_count += len(df[df['ID'].notna()])
                elif 'Facebook Contacts' in sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    total_count += len(df[df['Profile ID'].notna()])
                elif 'Facebook User-Friends' in sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    total_count += len(df[df['User ID'].notna()])
                elif 'WhatsApp Contacts' in sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    total_count += len(df[df['ID'].notna()])
                elif 'WhatsApp User Profiles' in sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
                    total_count += len(df[df['Phone Number'].notna()])
            
            return total_count
            
        except Exception as e:
            print(f"Error counting Axiom social media: {e}")
            return 0
    
    def parse_cellebrite_social_media(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            # Parse all sheets
            if 'Social Media' in xls.sheet_names:
                results.extend(self._parse_cellebrite_social_media_sheet(file_path, 'Social Media', file_id))
            
            if 'Contacts' in xls.sheet_names:
                results.extend(self._parse_cellebrite_contacts_sheet(file_path, 'Contacts', file_id))
            
            if 'Chats' in xls.sheet_names:
                results.extend(self._parse_cellebrite_chats_sheet(file_path, 'Chats', file_id))
            
            # Remove duplicates before saving
            unique_results = []
            seen_accounts = set()
            
            for acc in results:
                account_key = f"{acc['platform']}_{acc['account_id']}"
                if account_key not in seen_accounts:
                    seen_accounts.add(account_key)
                    unique_results.append(acc)
            
            print(f"Removed {len(results) - len(unique_results)} duplicate records")
            print(f"Unique social media accounts: {len(unique_results)}")
            
            # Save to database in batches
            batch_size = 50
            saved_count = 0
            
            for i in range(0, len(unique_results), batch_size):
                batch = unique_results[i:i + batch_size]
                
                try:
                    for acc in batch:
                        existing = (
                            self.db.query(SocialMedia)
                            .filter(
                                SocialMedia.platform == acc["platform"],
                                SocialMedia.account_id == acc["account_id"],
                                SocialMedia.file_id == acc["file_id"]
                            )
                            .first()
                        )
                        if not existing:
                            self.db.add(SocialMedia(**acc))
                    
                    self.db.commit()
                    saved_count += len(batch)
                    print(f"Saved batch {i//batch_size + 1}: {len(batch)} records (Total: {saved_count})")
                    
                except Exception as batch_error:
                    print(f"Error saving batch {i//batch_size + 1}: {batch_error}")
                    self.db.rollback()
                    raise batch_error
            
            print(f"Successfully saved {saved_count} unique Cellebrite social media accounts to database")
            
        except Exception as e:
            print(f"Error parsing Cellebrite social media: {e}")
            self.db.rollback()
            raise e
        
        return unique_results
    
    def _parse_cellebrite_social_media_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Unnamed: 0')) or row.get('Unnamed: 0') == '#':
                    continue
                
                if row.get('Unnamed: 8') == 'Instagram': 
                    author = self._clean(row.get('Unnamed: 2'))
                    title = self._clean(row.get('Unnamed: 4'))
                    body = self._clean(row.get('Unnamed: 3'))
                    created = self._clean(row.get('Unnamed: 5'))
                    url = self._clean(row.get('Unnamed: 17')) 
                    account = self._clean(row.get('Unnamed: 18'))
                    
                    if author and account:
                        user_id = author.split()[0] if author.split() else None
                        account_name = author.split()[1] if len(author.split()) > 1 else account
                        
                        acc = {
                            "platform": "instagram",
                            "account_name": account_name,
                            "account_id": user_id,
                            "user_id": user_id,
                            "full_name": account_name,
                            "biography": body,
                            "profile_picture_url": url,
                            "source_tool": "Cellebrite",
                            "sheet_name": "Social Media",                            "file_id": file_id,
                        }
                        results.append(acc)
            
        except Exception as e:
            print(f"Error parsing Cellebrite Social Media sheet: {e}")
        
        return results
    
    def _parse_cellebrite_contacts_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Unnamed: 0')) or row.get('Unnamed: 0') == '#':
                    continue
                
                if row.get('Unnamed: 20') == 'Telegram':
                    entries = self._clean(row.get('Unnamed: 8'))
                    
                    if entries and 'User ID-Username:' in entries:
                        username = entries.split('User ID-Username: ')[1].strip() if 'User ID-Username: ' in entries else None
                        
                        if username:
                            acc = {
                                "platform": "telegram",
                                "account_name": username,
                                "account_id": username,
                                "user_id": username,
                                "full_name": username,
                                "source_tool": "Cellebrite",
                                "sheet_name": "Contacts",                                "file_id": file_id,
                            }
                            results.append(acc)
                    
                    elif entries and 'User ID-User ID:' in entries:
                        user_id = entries.split('User ID-User ID: ')[1].strip() if 'User ID-User ID: ' in entries else None
                        
                        if user_id:
                            acc = {
                                "platform": "telegram",
                                "account_name": user_id,
                                "account_id": user_id,
                                "user_id": user_id,
                                "full_name": user_id,
                                "source_tool": "Cellebrite",
                                "sheet_name": "Contacts",                                "file_id": file_id,
                            }
                            results.append(acc)
            
        except Exception as e:
            print(f"Error parsing Cellebrite Contacts sheet: {e}")
        
        return results
    
    def _parse_cellebrite_chats_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Unnamed: 0')) or row.get('Unnamed: 0') == '#':
                    continue
                
                # Check if it's Telegram chat
                if row.get('Unnamed: 15') == 'Telegram':
                    participants = self._clean(row.get('Unnamed: 13'))
                    chat_id = self._clean(row.get('Unnamed: 2'))
                    
                    if participants and chat_id:
                        participant_lines = participants.split('_x000d_')
                        
                        for line in participant_lines:
                            line = line.strip()
                            if line and not line.startswith('777000'):
                                parts = line.split()
                                if len(parts) >= 2:
                                    user_id = parts[0]
                                    username = ' '.join(parts[1:]).replace('(owner)', '').strip()
                                    
                                    acc = {
                                        "platform": "telegram",
                                        "account_name": username,
                                        "account_id": user_id,
                                        "user_id": user_id,
                                        "full_name": username,
                                        "chat_content": f"Chat ID: {chat_id}",
                                        "source_tool": "Cellebrite",
                                        "sheet_name": "Chats",                                        "file_id": file_id,
                                    }
                                    results.append(acc)
            
        except Exception as e:
            print(f"Error parsing Cellebrite Chats sheet: {e}")
        
        return results
    
    def count_cellebrite_social_media(self, file_path: str) -> int:
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            total_count = 0
            
            # Count Social Media sheet
            if 'Social Media' in xls.sheet_names:
                df = pd.read_excel(file_path, sheet_name='Social Media', engine='openpyxl', dtype=str)
                instagram_count = len(df[df['Unnamed: 8'] == 'Instagram'])
                total_count += instagram_count
            
            # Count Contacts sheet
            if 'Contacts' in xls.sheet_names:
                df = pd.read_excel(file_path, sheet_name='Contacts', engine='openpyxl', dtype=str)
                telegram_contacts = df[df['Unnamed: 20'] == 'Telegram']
                telegram_count = len(telegram_contacts[telegram_contacts['Unnamed: 8'].notna()])
                total_count += telegram_count
            
            # Count Chats sheet
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
                    
                # Handle following/followers as Yes/No strings
                following_value = self._clean(row.get('Following'))
                followers_value = self._clean(row.get('Is Followed By'))
                
                # Convert Yes/No to boolean, then to 1/0 for counting
                following_count = 1 if following_value and following_value.lower() == 'yes' else None
                followers_count = 1 if followers_value and followers_value.lower() == 'yes' else None
                
                acc = {
                    "platform": "instagram",
                    "account_name": self._clean(row.get('User Name')),
                    "account_id": self._clean(row.get('User Name')),  # Username sebagai account_id
                    "user_id": self._clean(row.get('User ID')),
                    "full_name": self._clean(row.get('Name')),
                    "following": following_count,
                    "followers": followers_count,
                    "biography": self._clean(row.get('Biography')),
                    "profile_picture_url": self._clean(row.get('Profile Picture URL')),
                    "is_private": self._safe_bool(row.get('Is Private')),
                    "is_local_user": self._safe_bool(row.get('Local User')),
                    "email": self._clean(row.get('Email')),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "source_tool": "Axiom",
                    "sheet_name": "Instagram Profiles",                    "file_id": file_id,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Instagram Profiles: {e}")
        
        return results

    def _parse_axiom_twitter_users(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User Name')):
                    continue
                    
                acc = {
                    "platform": "x",
                    "account_name": self._clean(row.get('User Name')),
                    "account_id": self._clean(row.get('User Name')),  # Username sebagai account_id
                    "user_id": self._clean(row.get('User ID')),
                    "full_name": self._clean(row.get('Full Name')),
                    "following": self._safe_int(row.get('Following')),
                    "followers": self._safe_int(row.get('Followers')),
                    "friends": self._safe_int(row.get('Friends')),
                    "statuses": self._safe_int(row.get('Statuses')),
                    "biography": self._clean(row.get('Description')),
                    "profile_picture_url": self._clean(row.get('Image URL')),
                    "is_private": self._safe_bool(row.get('Protected')),
                    "source_tool": "Axiom",
                    "sheet_name": "Twitter Users",                    "file_id": file_id,
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
                
                acc = {
                    "platform": "telegram",
                    "account_name": user_name or full_name or str(self._clean(row.get('User ID'))),
                    "account_id": self._clean(row.get('Account ID')),
                    "user_id": self._clean(row.get('User ID')),
                    "full_name": full_name,
                    "phone_number": self._clean(row.get('Phone Number')),
                    "is_local_user": self._safe_bool(row.get('Active Account')),
                    "source_tool": "Axiom",
                    "sheet_name": "Telegram Accounts",                    "file_id": file_id,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Telegram Accounts: {e}")
        
        return results

    def _parse_axiom_tiktok_contacts(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('ID')):
                    continue
                    
                acc = {
                    "platform": "tiktok",
                    "account_name": self._clean(row.get('Nickname')) or self._clean(row.get('User Name')),
                    "account_id": self._clean(row.get('ID')),
                    "user_id": self._clean(row.get('ID')),
                    "full_name": self._clean(row.get('Nickname')),
                    "profile_picture_url": self._clean(row.get('Profile Picture URL')),
                    "source_tool": "Axiom",
                    "sheet_name": "TikTok Contacts",                    "file_id": file_id,
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
                    "platform": "facebook",
                    "account_name": self._clean(row.get('Display Name')),
                    "account_id": self._clean(row.get('Profile ID')),
                    "user_id": self._clean(row.get('Profile ID')),
                    "full_name": f"{self._clean(row.get('First Name'))} {self._clean(row.get('Last Name'))}".strip(),
                    "profile_picture_url": self._clean(row.get('Picture URL')),
                    "phone_number": self._clean(row.get('Phone Numbers')),
                    "source_tool": "Axiom",                    "file_id": file_id,
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
                    "platform": "facebook",
                    "account_name": self._clean(row.get('Display Name')),
                    "account_id": self._clean(row.get('User ID')),
                    "user_id": self._clean(row.get('User ID')),
                    "full_name": f"{self._clean(row.get('First Name'))} {self._clean(row.get('Last Name'))}".strip(),
                    "profile_picture_url": self._clean(row.get('User Image URL')),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "email": self._clean(row.get('Email(s)')),
                    "source_tool": "Axiom",                    "file_id": file_id,
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
                    "platform": "whatsapp",
                    "account_name": self._clean(row.get('WhatsApp Name')),
                    "account_id": self._clean(row.get('ID')),
                    "user_id": self._clean(row.get('ID')),
                    "full_name": f"{self._clean(row.get('Given Name'))} {self._clean(row.get('Family Name'))}".strip(),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "source_tool": "Axiom",                    "file_id": file_id,
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
                    "platform": "whatsapp",
                    "account_name": self._clean(row.get('WhatsApp Name')),
                    "account_id": self._clean(row.get('Phone Number')),
                    "user_id": self._clean(row.get('Phone Number')),
                    "full_name": self._clean(row.get('WhatsApp Name')),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "source_tool": "Axiom",                    "file_id": file_id,
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
            
            # Cek setiap tool folder (Axiom, Cellebrite, Oxygen)
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
        
        # Cari file Excel
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
        
        # Cari file Excel
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
        
        # Cari file Excel
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
        """Parse chat messages from Cellebrite file."""
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            # Parse Chats sheet for Telegram messages
            if 'Chats' in xls.sheet_names:
                results.extend(self._parse_cellebrite_chats_messages(file_path, 'Chats', file_id))
            
            # Save to database
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
            
            self.db.commit()
            print(f"Successfully saved {len(results)} Cellebrite chat messages to database")
            
        except Exception as e:
            print(f"Error parsing Cellebrite chat messages: {e}")
            self.db.rollback()
            raise e
        
        return results

    def _parse_cellebrite_chats_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse Telegram chat messages from Cellebrite Chats sheet."""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                # Cek apakah ini adalah pesan Telegram
                if pd.isna(row.get('Unnamed: 15')) or str(row.get('Unnamed: 15')).strip() != 'Telegram':
                    continue
                
                # Ekstrak data pesan dari kolom Body (Unnamed: 32)
                message_text = str(row.get('Unnamed: 32', ''))
                if not message_text or message_text.strip() == 'nan':
                    continue
                
                # Ekstrak informasi pengirim dari kolom From (Unnamed: 25)
                sender_info = str(row.get('Unnamed: 25', ''))
                sender_name = ""
                sender_id = ""
                
                # Parse sender info (format: "ID Name" atau "Name")
                if sender_info and sender_info != 'nan':
                    parts = sender_info.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        sender_id = parts[0]
                        sender_name = ' '.join(parts[1:])
                    else:
                        sender_name = sender_info
                
                # Ekstrak timestamp dari kolom Timestamp: Time (Unnamed: 41)
                timestamp = str(row.get('Unnamed: 41', ''))
                
                # Ekstrak chat identifier dari kolom Identifier (Unnamed: 2)
                chat_id = str(row.get('Unnamed: 2', ''))
                
                # Ekstrak instant message number dari kolom Instant Message # (Unnamed: 24)
                message_id = str(row.get('Unnamed: 24', ''))
                
                # Determine direction based on sender
                direction = "Outgoing" if sender_id == "8229898490" else "Incoming"
                
                message_data = {                    "file_id": file_id,
                    "platform": "telegram",
                    "message_text": message_text,
                    "sender_name": sender_name,
                    "sender_id": sender_id,
                    "receiver_name": "",
                    "receiver_id": "",
                    "timestamp": timestamp,
                    "thread_id": chat_id,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "message_type": "text",
                    "direction": direction,
                    "source_tool": "cellebrite"
                }
                
                results.append(message_data)
            
        except Exception as e:
            print(f"Error parsing Cellebrite chats messages: {e}")
        
        return results

    def parse_axiom_chat_messages(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse chat messages from Axiom file."""
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            # Parse Telegram Messages
            if 'Telegram Messages - iOS' in xls.sheet_names:
                results.extend(self._parse_telegram_messages(file_path, 'Telegram Messages - iOS', file_id))
            
            # Parse Instagram Direct Messages
            if 'Instagram Direct Messages' in xls.sheet_names:
                results.extend(self._parse_instagram_messages(file_path, 'Instagram Direct Messages', file_id))
            
            # Parse TikTok Messages
            if 'TikTok Messages' in xls.sheet_names:
                results.extend(self._parse_tiktok_messages(file_path, 'TikTok Messages', file_id))
            
            # Parse Twitter Direct Messages
            if 'Twitter Direct Messages' in xls.sheet_names:
                results.extend(self._parse_twitter_messages(file_path, 'Twitter Direct Messages', file_id))
            
            # Save to database
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
            
            self.db.commit()
            print(f"Successfully saved {len(results)} chat messages to database")
            
        except Exception as e:
            print(f"Error parsing Axiom chat messages: {e}")
            self.db.rollback()
            raise e
        
        return results

    def _parse_telegram_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse Telegram messages from Axiom file."""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Message')) or not str(row.get('Message')).strip():
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
                    "source_tool": "axiom"
                }
                
                results.append(message_data)
            
        except Exception as e:
            print(f"Error parsing Telegram messages: {e}")
        
        return results

    def _parse_instagram_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse Instagram direct messages from Axiom file."""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Message')) or not str(row.get('Message')).strip():
                    continue
                
                message_data = {                    "file_id": file_id,
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
                    "source_tool": "axiom"
                }
                
                results.append(message_data)
            
        except Exception as e:
            print(f"Error parsing Instagram messages: {e}")
        
        return results

    def _parse_tiktok_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse TikTok messages from Axiom file."""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Message')) or not str(row.get('Message')).strip():
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
                    "source_tool": "axiom"
                }
                
                results.append(message_data)
            
        except Exception as e:
            print(f"Error parsing TikTok messages: {e}")
        
        return results

    def _parse_twitter_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse Twitter direct messages from Axiom file."""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Text')) or not str(row.get('Text')).strip():
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
                    "source_tool": "axiom"
                }
                
                results.append(message_data)
            
        except Exception as e:
            print(f"Error parsing Twitter messages: {e}")
        
        return results
