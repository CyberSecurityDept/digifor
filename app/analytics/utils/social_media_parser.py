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

    def _to_int_safe(self, value: Optional[str], max_value: int = 2147483647) -> Optional[int]:
        if value is None:
            return None
        text = str(value).strip()
        if text == "" or text.lower() == "nan":
            return None
        # Keep leading '-' if present; strip non-digits
        sign = -1 if text.startswith('-') else 1
        digits = ''.join(ch for ch in text if ch.isdigit())
        if digits == "":
            return None
        try:
            num = sign * int(digits)
            if -max_value <= num <= max_value:
                return num
            # Out of 32-bit integer range -> treat as invalid
            return None
        except Exception:
            return None

    def parse_oxygen_ufed_social_media(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []

        try:
            xls = pd.ExcelFile(file_path, engine='xlrd')
            
            if 'Contacts ' in xls.sheet_names:
                contacts_df = pd.read_excel(file_path, sheet_name='Contacts ', dtype=str, engine='xlrd')
                
                social_platforms = ['X (Twitter)', 'Instagram', 'Telegram Messenger', 'Facebook', 'WhatsApp', 'TikTok']
                social_accounts = contacts_df[contacts_df['Source'].isin(social_platforms)]
                
                for _, row in social_accounts.iterrows():
                    source = self._clean(row.get('Source', ''))
                    contact = self._clean(row.get('Contact', ''))
                    phones_emails = self._clean(row.get('Phones & Emails', ''))
                    internet = self._clean(row.get('Internet', ''))
                    
                    if not source or not contact:
                        continue
                    
                    platform = self._determine_platform_from_source(source)
                    if not platform:
                        continue
                    
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
        
        contact = contact.replace('\\r\\n', '').strip()
        
        if platform == 'instagram':
            if 'Instagram ID:' in contact:
                parts = contact.split('Instagram ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            return contact.split('\\n')[0].strip()
        
        elif platform == 'x':
            if 'Nickname:' in contact:
                parts = contact.split('Nickname:')
                if len(parts) > 1:
                    return parts[1].strip()

            return contact.split('\\n')[0].strip()
        
        elif platform == 'telegram':
            return contact.split('\\n')[0].strip()
        
        return contact.split('\\n')[0].strip()
    
    def _extract_account_id(self, contact: str, platform: str) -> str:
        return self._extract_account_name(contact, platform)
    
    def _extract_account_id_from_contact(self, contact: str, platform: str) -> str:
        if not contact:
            return None
        
        contact = contact.replace('\\r\\n', '').strip()
        
        if platform == 'instagram':
            # Look for Instagram ID pattern
            if 'Instagram ID:' in contact:
                parts = contact.split('Instagram ID:')
                if len(parts) > 1:
                    return parts[1].strip()

            return contact.split('\\n')[0].strip()
        
        elif platform == 'x':
            if 'X ID:' in contact:
                parts = contact.split('X ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            if 'Nickname:' in contact:
                parts = contact.split('Nickname:')
                if len(parts) > 1:
                    return parts[1].strip()
            return contact.split('\\n')[0].strip()
        
        elif platform == 'telegram':
            if 'Telegram ID:' in contact:
                parts = contact.split('Telegram ID:')
                if len(parts) > 1:
                    return parts[1].strip()
            return contact.split('\\n')[0].strip()
        
        return contact.split('\\n')[0].strip()
    
    def _extract_user_id_from_contact(self, contact: str, platform: str) -> str:
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
                
                file_path_obj = Path(file_path)
                file_extension = file_path_obj.suffix.lower()
                if file_extension == '.xls':
                    engine = "xlrd"
                else:
                    engine = "openpyxl"
                
                xls = pd.ExcelFile(file_path, engine=engine)
                
                print(f"Total sheets available: {len(xls.sheet_names)}")
                
                # Parse multiple sheets for social media data
                results.extend(self._parse_oxygen_instagram_sheets(file_path, xls, file_id, engine))
                results.extend(self._parse_oxygen_twitter_sheets(file_path, xls, file_id, engine))
                results.extend(self._parse_oxygen_telegram_sheets(file_path, xls, file_id, engine))
                results.extend(self._parse_oxygen_whatsapp_sheets(file_path, xls, file_id, engine))
                results.extend(self._parse_oxygen_contacts_sheet(file_path, xls, file_id, engine))
                results.extend(self._parse_oxygen_tiktok_facebook_sheets(file_path, xls, file_id, engine))

            # Remove duplicates before saving
            unique_results = []
            seen_accounts = set()
            
            for acc in results:
                account_key = f"{acc['platform']}_{acc['account_id']}_{acc['account_name']}"
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
            
            print(f"Successfully saved {saved_count} unique Oxygen social media accounts to database")

        except Exception as e:
            print(f"Error parsing social media Oxygen: {e}")
            self.db.rollback()
            raise e

        return unique_results

    def _parse_oxygen_instagram_sheets(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            # Parse Users-Following sheet
            if 'Users-Following ' in xls.sheet_names:
                print("Parsing Instagram Users-Following sheet...")
                df = pd.read_excel(file_path, sheet_name='Users-Following ', engine=engine, dtype=str)
                
                for _, row in df.iterrows():
                    user_name = self._clean(row.get('User name'))
                    full_name = self._clean(row.get('Full name'))
                    user_id = self._clean(row.get('User ID'))
                    profile_picture_url = self._clean(row.get('User picture URL'))
                    is_private = self._clean(row.get('Private'))
                    is_verified = self._clean(row.get('Verified'))
                    
                    if user_name and user_id:
                        acc = {
                            "platform": "instagram",
                            "account_name": user_name,
                            "account_id": user_id,
                            "user_id": user_id,
                            "full_name": full_name,
                            "following": None,
                            "followers": None,
                            "friends": None,
                            "statuses": None,
                            "phone_number": None,
                            "email": None,
                            "biography": None,
                            "profile_picture_url": profile_picture_url,
                            "is_private": is_private == 'Yes' if is_private else None,
                            "is_local_user": None,
                            "chat_content": None,
                            "last_message": None,
                            "other_info": f"Verified: {is_verified}" if is_verified else None,
                            "source_tool": "Oxygen",
                            "sheet_name": "Users-Following",
                            "file_id": file_id,
                        }
                        results.append(acc)
            
            # Parse Users-Followers sheet
            if 'Users-Followers ' in xls.sheet_names:
                print("Parsing Instagram Users-Followers sheet...")
                df = pd.read_excel(file_path, sheet_name='Users-Followers ', engine=engine, dtype=str)
                
                for _, row in df.iterrows():
                    user_name = self._clean(row.get('User name'))
                    full_name = self._clean(row.get('Full name'))
                    user_id = self._clean(row.get('UID'))
                    profile_picture_url = self._clean(row.get('User picture URL'))
                    description = self._clean(row.get('Description'))
                    followers_count = self._clean(row.get('Followers'))
                    following_count = self._clean(row.get('Following'))
                    is_verified = self._clean(row.get('Verified'))
                    
                    if user_name and user_id:
                        acc = {
                            "platform": "instagram",
                            "account_name": user_name,
                            "account_id": user_id,
                            "user_id": user_id,
                            "full_name": full_name,
                            "following": int(following_count) if following_count and following_count.isdigit() else None,
                            "followers": int(followers_count) if followers_count and followers_count.isdigit() else None,
                            "friends": None,
                            "statuses": None,
                            "phone_number": None,
                            "email": None,
                            "biography": description,
                            "profile_picture_url": profile_picture_url,
                            "is_private": None,
                            "is_local_user": None,
                            "chat_content": None,
                            "last_message": None,
                            "other_info": f"Verified: {is_verified}" if is_verified else None,
                            "source_tool": "Oxygen",
                            "sheet_name": "Users-Followers",
                            "file_id": file_id,
                        }
                        results.append(acc)
        
        except Exception as e:
            print(f"Error parsing Instagram sheets: {e}")
        
        return results

    def _parse_oxygen_twitter_sheets(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            # Parse Users-Followers sheet for Twitter data
            if 'Users-Followers ' in xls.sheet_names:
                print("Parsing X (Twitter) Users-Followers sheet...")
                df = pd.read_excel(file_path, sheet_name='Users-Followers ', engine=engine, dtype=str)
                
                for _, row in df.iterrows():
                    source = self._clean(row.get('Source'))
                    if source and 'twitter' in source.lower():
                        user_name = self._clean(row.get('User name'))
                        full_name = self._clean(row.get('Full name'))
                        user_id = self._clean(row.get('UID'))
                        profile_picture_url = self._clean(row.get('User picture URL'))
                        description = self._clean(row.get('Description'))
                        followers_count = self._clean(row.get('Followers'))
                        following_count = self._clean(row.get('Following'))
                        is_verified = self._clean(row.get('Verified'))
                        
                        if user_name and user_id:
                            acc = {
                                "platform": "x",
                                "account_name": user_name,
                                "account_id": user_id,
                                "user_id": user_id,
                                "full_name": full_name,
                                "following": int(following_count) if following_count and following_count.isdigit() else None,
                                "followers": int(followers_count) if followers_count and followers_count.isdigit() else None,
                                "friends": None,
                                "statuses": None,
                                "phone_number": None,
                                "email": None,
                                "biography": description,
                                "profile_picture_url": profile_picture_url,
                                "is_private": None,
                                "is_local_user": None,
                                "chat_content": None,
                                "last_message": None,
                                "other_info": f"Verified: {is_verified}" if is_verified else None,
                                "source_tool": "Oxygen",
                                "sheet_name": "Users-Followers",
                                "file_id": file_id,
                            }
                            results.append(acc)
            
            # Parse Tweets-Following sheet
            if 'Tweets-Following ' in xls.sheet_names:
                print("Parsing X (Twitter) Tweets-Following sheet...")
                df = pd.read_excel(file_path, sheet_name='Tweets-Following ', engine=engine, dtype=str)
                
                for _, row in df.iterrows():
                    user_name = self._clean(row.get('User name'))
                    full_name = self._clean(row.get('Full name'))
                    user_id = self._clean(row.get('User ID'))
                    tweet_text = self._clean(row.get('Tweet text'))
                    
                    if user_name and user_id:
                        acc = {
                            "platform": "x",
                            "account_name": user_name,
                            "account_id": user_id,
                            "user_id": user_id,
                            "full_name": full_name,
                            "following": None,
                            "followers": None,
                            "friends": None,
                            "statuses": None,
                            "phone_number": None,
                            "email": None,
                            "biography": None,
                            "profile_picture_url": None,
                            "is_private": None,
                            "is_local_user": None,
                            "chat_content": tweet_text,
                            "last_message": tweet_text,
                            "other_info": None,
                            "source_tool": "Oxygen",
                            "sheet_name": "Tweets-Following",
                            "file_id": file_id,
                        }
                        results.append(acc)
            
            # Parse Tweets-Other sheet
            if 'Tweets-Other ' in xls.sheet_names:
                print("Parsing X (Twitter) Tweets-Other sheet...")
                df = pd.read_excel(file_path, sheet_name='Tweets-Other ', engine=engine, dtype=str)
                
                for _, row in df.iterrows():
                    user_name = self._clean(row.get('User name'))
                    full_name = self._clean(row.get('Full name'))
                    user_id = self._clean(row.get('User ID'))
                    tweet_text = self._clean(row.get('Tweet text'))
                    
                    if user_name and user_id:
                        acc = {
                            "platform": "x",
                            "account_name": user_name,
                            "account_id": user_id,
                            "user_id": user_id,
                            "full_name": full_name,
                            "following": None,
                            "followers": None,
                            "friends": None,
                            "statuses": None,
                            "phone_number": None,
                            "email": None,
                            "biography": None,
                            "profile_picture_url": None,
                            "is_private": None,
                            "is_local_user": None,
                            "chat_content": tweet_text,
                            "last_message": tweet_text,
                            "other_info": None,
                            "source_tool": "Oxygen",
                            "sheet_name": "Tweets-Other",
                            "file_id": file_id,
                        }
                        results.append(acc)
        
        except Exception as e:
            print(f"Error parsing Twitter sheets: {e}")
        
        return results

    def _parse_oxygen_telegram_sheets(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            # Parse Telegram sheet
            if 'Telegram ' in xls.sheet_names:
                print("Parsing Telegram sheet...")
                df = pd.read_excel(file_path, sheet_name='Telegram ', engine=engine, dtype=str)
                
                if len(df) >= 2:
                    user_data_count = self._clean(df.iloc[1, 2])
                    if user_data_count and user_data_count.isdigit():
                        print(f"Telegram user data count: {user_data_count}")
            
            # Parse Contacts sheet for Telegram data
            if 'Contacts ' in xls.sheet_names:
                print("Parsing Telegram data from Contacts sheet...")
                df = pd.read_excel(file_path, sheet_name='Contacts ', engine=engine, dtype=str)
                
                for _, row in df.iterrows():
                    source_field = self._clean(row.get("Source"))
                    internet_field = self._clean(row.get("Internet"))
                    contact_field = self._clean(row.get("Contact"))
                    phones_emails_field = self._clean(row.get("Phones & Emails"))
                    
                    if source_field and 'telegram' in source_field.lower():
                        telegram_id = None
                        if internet_field and 'telegram id:' in internet_field.lower():
                            match = re.search(r'telegram id:\s*(\d+)', internet_field.lower())
                            if match:
                                telegram_id = match.group(1)
                        
                        account_name = self._extract_name(contact_field)
                        if not account_name and telegram_id:
                            account_name = telegram_id
                        
                        if telegram_id:
                            acc = {
                                "platform": "telegram",
                                "account_name": account_name,
                                "account_id": telegram_id,
                                "user_id": telegram_id,
                                "full_name": self._extract_full_name(contact_field),
                                "following": None,
                                "followers": None,
                                "friends": None,
                                "statuses": None,
                                "phone_number": self._extract_phone_number(phones_emails_field),
                                "email": self._extract_email(phones_emails_field),
                                "biography": None,
                                "profile_picture_url": None,
                                "is_private": None,
                                "is_local_user": None,
                                "chat_content": None,
                                "last_message": None,
                                "other_info": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "Contacts",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing Telegram sheets: {e}")
        
        return results

    def _parse_oxygen_whatsapp_sheets(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            # Parse WhatsApp Messenger sheet
            if 'WhatsApp Messenger ' in xls.sheet_names:
                print("Parsing WhatsApp Messenger sheet...")
                df = pd.read_excel(file_path, sheet_name='WhatsApp Messenger ', engine=engine, dtype=str)
                
                if len(df) >= 2:
                    user_data_count = self._clean(df.iloc[1, 2])  # Third column, second row
                    if user_data_count and user_data_count.isdigit():
                        print(f"WhatsApp user data count: {user_data_count}")
            
            # Parse Contacts sheet for WhatsApp data
            if 'Contacts ' in xls.sheet_names:
                print("Parsing WhatsApp data from Contacts sheet...")
                df = pd.read_excel(file_path, sheet_name='Contacts ', engine=engine, dtype=str)
                
                for _, row in df.iterrows():
                    source_field = self._clean(row.get("Source"))
                    internet_field = self._clean(row.get("Internet"))
                    contact_field = self._clean(row.get("Contact"))
                    phones_emails_field = self._clean(row.get("Phones & Emails"))
                    other_field = self._clean(row.get("Other"))
                    
                    if source_field and 'whatsapp' in source_field.lower():
                        whatsapp_id = None
                        if internet_field and 'whatsapp id:' in internet_field.lower():
                            match = re.search(r'whatsapp id:\s*(\d+)', internet_field.lower())
                            if match:
                                whatsapp_id = match.group(1)
                        
                        account_name = self._extract_name(contact_field)
                        if not account_name and whatsapp_id:
                            account_name = whatsapp_id
                        
                        phone_number = self._extract_phone_number(phones_emails_field)
                        if not phone_number and whatsapp_id:
                            phone_number = whatsapp_id
                        
                        if whatsapp_id:
                            acc = {
                                "platform": "whatsapp",
                                "account_name": account_name,
                                "account_id": whatsapp_id,
                                "user_id": whatsapp_id,
                                "full_name": self._extract_full_name(contact_field),
                                "following": None,
                                "followers": None,
                                "friends": None,
                                "statuses": None,
                                "phone_number": phone_number,
                                "email": self._extract_email(phones_emails_field),
                                "biography": None,
                                "profile_picture_url": None,
                                "is_private": None,
                                "is_local_user": None,
                                "chat_content": other_field,
                                "last_message": other_field,
                                "other_info": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "Contacts",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing WhatsApp sheets: {e}")
        
        return results

    def _parse_oxygen_contacts_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            sheet_name = file_validator._find_contacts_sheet(xls.sheet_names)
            if not sheet_name:
                return results

            print(f"Parsing Contacts sheet: {sheet_name}")
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
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)

        except Exception as e:
            print(f"Error parsing Contacts sheet: {e}")
        
        return results

    def _parse_oxygen_facebook_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if 'Facebook ' in xls.sheet_names:
                print("Parsing Facebook sheet...")
                df = pd.read_excel(file_path, sheet_name='Facebook ', engine=engine, dtype=str)
                
                if any('Unnamed' in str(col) for col in df.columns):
                    df.columns = df.iloc[0]
                    df = df.drop(df.index[0])
                    df = df.reset_index(drop=True)
                
                if len(df) > 3:
                    data_df = df.iloc[3:].copy()
                    data_df = data_df.reset_index(drop=True)
                    
                    for _, row in data_df.iterrows():
                        if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() in ['Categories', 'Identifier']:
                            continue
                        
                        full_name = self._clean(row.iloc[2]) if len(row) > 2 else None
                        user_name = self._clean(row.iloc[3]) if len(row) > 3 else None
                        email = self._clean(row.iloc[4]) if len(row) > 4 else None
                        phone_number = self._clean(row.iloc[5]) if len(row) > 5 else None
                        profile_picture_url = self._clean(row.iloc[6]) if len(row) > 6 else None
                        user_id = self._clean(row.iloc[14]) if len(row) > 14 else None
                        
                        if user_name and user_name not in ['Accounts', 'Source', 'Categories'] and user_id and user_id.isdigit():
                            acc = {
                                "platform": "facebook",
                                "account_name": user_name,
                                "account_id": user_id,
                                "user_id": user_id,
                                "full_name": full_name,
                                "following": None,
                                "followers": None,
                                "friends": None,
                                "statuses": None,
                                "phone_number": phone_number,
                                "email": email,
                                "biography": None,
                                "profile_picture_url": profile_picture_url,
                                "is_private": None,
                                "is_local_user": None,
                                "chat_content": None,
                                "last_message": None,
                                "other_info": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "Facebook",
                                "file_id": file_id,
                            }
                            results.append(acc)

        except Exception as e:
            print(f"Error parsing Facebook sheet: {e}")

        return results

    def _parse_oxygen_instagram_dedicated_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if 'Instagram ' in xls.sheet_names:
                print("Parsing Instagram dedicated sheet...")
                df = pd.read_excel(file_path, sheet_name='Instagram ', engine=engine, dtype=str)
                
                if any('Unnamed' in str(col) for col in df.columns):
                    df.columns = df.iloc[0]
                    df = df.drop(df.index[0])
                    df = df.reset_index(drop=True)
                
                if len(df) > 3:
                    data_df = df.iloc[3:].copy()
                    data_df = data_df.reset_index(drop=True)
                    
                    for _, row in data_df.iterrows():
                        if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() in ['Categories', 'Identifier']:
                            continue
                        
                        full_name = self._clean(row.iloc[2]) if len(row) > 2 else None
                        user_name = self._clean(row.iloc[3]) if len(row) > 3 else None
                        biography = self._clean(row.iloc[5]) if len(row) > 5 else None
                        profile_picture_url = self._clean(row.iloc[6]) if len(row) > 6 else None
                        followers_count = self._clean(row.iloc[7]) if len(row) > 7 else None
                        following_count = self._clean(row.iloc[8]) if len(row) > 8 else None
                        user_id = self._clean(row.iloc[19]) if len(row) > 19 else None
                        
                        if user_name and user_name not in ['Accounts', 'Source', 'Categories'] and user_id and user_id.isdigit():
                            acc = {
                                "platform": "instagram",
                                "account_name": user_name,
                                "account_id": user_id,
                                "user_id": user_id,
                                "full_name": full_name,
                                "following": self._to_int_safe(following_count),
                                "followers": self._to_int_safe(followers_count),
                                "friends": None,
                                "statuses": None,
                                "phone_number": None,
                                "email": None,
                                "biography": biography,
                                "profile_picture_url": profile_picture_url,
                                "is_private": None,
                                "is_local_user": None,
                                "chat_content": None,
                                "last_message": None,
                                "other_info": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "Instagram",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing Instagram dedicated sheet: {e}")
        
        return results

    def _parse_oxygen_whatsapp_dedicated_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if 'WhatsApp Messenger ' in xls.sheet_names:
                print("Parsing WhatsApp Messenger dedicated sheet...")
                df = pd.read_excel(file_path, sheet_name='WhatsApp Messenger ', engine=engine, dtype=str)
                
                if any('Unnamed' in str(col) for col in df.columns):
                    df.columns = df.iloc[0]
                    df = df.drop(df.index[0])
                    df = df.reset_index(drop=True)
                
                if len(df) > 3:
                    data_df = df.iloc[3:].copy()
                    data_df = data_df.reset_index(drop=True)
                    
                    for _, row in data_df.iterrows():
                        full_name = self._clean(row.iloc[1]) if len(row) > 1 else None
                        user_name = self._clean(row.iloc[2]) if len(row) > 2 else None
                        phone_number = self._clean(row.iloc[3]) if len(row) > 3 else None
                        profile_picture_url = self._clean(row.iloc[4]) if len(row) > 4 else None
                        user_id = self._clean(row.iloc[5]) if len(row) > 5 else None
                        
                        if user_name and user_id:
                            acc = {
                                "platform": "whatsapp",
                                "account_name": user_name,
                                "account_id": user_id,
                                "user_id": user_id,
                                "full_name": full_name,
                                "following": None,
                                "followers": None,
                                "friends": None,
                                "statuses": None,
                                "phone_number": phone_number,
                                "email": None,
                                "biography": None,
                                "profile_picture_url": profile_picture_url,
                                "is_private": None,
                                "is_local_user": None,
                                "chat_content": None,
                                "last_message": None,
                                "other_info": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "WhatsApp Messenger",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing WhatsApp Messenger dedicated sheet: {e}")
        
        return results

    def _parse_oxygen_telegram_dedicated_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if 'Telegram ' in xls.sheet_names:
                print("Parsing Telegram dedicated sheet...")
                df = pd.read_excel(file_path, sheet_name='Telegram ', engine=engine, dtype=str)
                
                if any('Unnamed' in str(col) for col in df.columns):
                    df.columns = df.iloc[0]
                    df = df.drop(df.index[0])
                    df = df.reset_index(drop=True)
                
                if len(df) > 3:
                    data_df = df.iloc[3:].copy()
                    data_df = data_df.reset_index(drop=True)
                    
                    for _, row in data_df.iterrows():
                        full_name = self._clean(row.iloc[1]) if len(row) > 1 else None
                        user_name = self._clean(row.iloc[2]) if len(row) > 2 else None
                        phone_number = self._clean(row.iloc[3]) if len(row) > 3 else None
                        profile_picture_url = self._clean(row.iloc[4]) if len(row) > 4 else None
                        user_id = self._clean(row.iloc[5]) if len(row) > 5 else None
                        
                        if user_name and user_id:
                            acc = {
                                "platform": "telegram",
                                "account_name": user_name,
                                "account_id": user_id,
                                "user_id": user_id,
                                "full_name": full_name,
                                "following": None,
                                "followers": None,
                                "friends": None,
                                "statuses": None,
                                "phone_number": phone_number,
                                "email": None,
                                "biography": None,
                                "profile_picture_url": profile_picture_url,
                                "is_private": None,
                                "is_local_user": None,
                                "chat_content": None,
                                "last_message": None,
                                "other_info": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "Telegram",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing Telegram dedicated sheet: {e}")
        
        return results

    def _parse_oxygen_twitter_dedicated_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if 'X (Twitter) ' in xls.sheet_names:
                print("Parsing X (Twitter) dedicated sheet...")
                df = pd.read_excel(file_path, sheet_name='X (Twitter) ', engine=engine, dtype=str)
                
                if any('Unnamed' in str(col) for col in df.columns):
                    df.columns = df.iloc[0]
                    df = df.drop(df.index[0])
                    df = df.reset_index(drop=True)
                
                if len(df) > 3:
                    data_df = df.iloc[3:].copy()
                    data_df = data_df.reset_index(drop=True)
                    
                    for _, row in data_df.iterrows():
                        full_name = self._clean(row.iloc[1]) if len(row) > 1 else None
                        user_name = self._clean(row.iloc[2]) if len(row) > 2 else None
                        biography = self._clean(row.iloc[3]) if len(row) > 3 else None
                        profile_picture_url = self._clean(row.iloc[4]) if len(row) > 4 else None
                        followers_count = self._clean(row.iloc[5]) if len(row) > 5 else None
                        following_count = self._clean(row.iloc[6]) if len(row) > 6 else None
                        user_id = self._clean(row.iloc[7]) if len(row) > 7 else None
                        
                        if user_name and user_id:
                            acc = {
                                "platform": "x",
                                "account_name": user_name,
                                "account_id": user_id,
                                "user_id": user_id,
                                "full_name": full_name,
                                "following": self._to_int_safe(following_count),
                                "followers": self._to_int_safe(followers_count),
                                "friends": None,
                                "statuses": None,
                                "phone_number": None,
                                "email": None,
                                "biography": biography,
                                "profile_picture_url": profile_picture_url,
                                "is_private": None,
                                "is_local_user": None,
                                "chat_content": None,
                                "last_message": None,
                                "other_info": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "X (Twitter)",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing X (Twitter) dedicated sheet: {e}")
        
        return results

    def _parse_oxygen_tiktok_mentions(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                    
                    for col in df.columns:
                        if df[col].dtype == "object":
                            for _, row in df.iterrows():
                                cell_value = self._clean(row.get(col))
                                if cell_value and 'tiktok' in cell_value.lower():
                                    tiktok_match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', cell_value)
                                    if tiktok_match:
                                        username = tiktok_match.group(1)
                                        acc = {
                                            "platform": "tiktok",
                                            "account_name": username,
                                            "account_id": username,
                                            "user_id": username,
                                            "full_name": username,
                                            "following": None,
                                            "followers": None,
                                            "friends": None,
                                            "statuses": None,
                                            "phone_number": None,
                                            "email": None,
                                            "biography": cell_value,
                                            "profile_picture_url": None,
                                            "is_private": None,
                                            "is_local_user": None,
                                            "chat_content": cell_value,
                                            "last_message": cell_value,
                                            "other_info": None,
                                            "source_tool": "Oxygen",
                                            "sheet_name": sheet_name,
                                            "file_id": file_id,
                                        }
                                        results.append(acc)
                
                except Exception as e:
                    print(f"Error reading sheet {sheet_name} for TikTok mentions: {e}")
                    continue
        
        except Exception as e:
            print(f"Error parsing TikTok mentions: {e}")
        
        return results

    def _parse_oxygen_tiktok_facebook_sheets(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            results.extend(self._parse_oxygen_facebook_sheet(file_path, xls, file_id, engine))
            
            results.extend(self._parse_oxygen_instagram_dedicated_sheet(file_path, xls, file_id, engine))
            
            results.extend(self._parse_oxygen_whatsapp_dedicated_sheet(file_path, xls, file_id, engine))
            
            results.extend(self._parse_oxygen_telegram_dedicated_sheet(file_path, xls, file_id, engine))
            
            results.extend(self._parse_oxygen_twitter_dedicated_sheet(file_path, xls, file_id, engine))

            results.extend(self._parse_oxygen_tiktok_mentions(file_path, xls, file_id, engine))
        
        except Exception as e:
            print(f"Error parsing enhanced social media sheets: {e}")
        
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
                account_key = f"{acc['platform']}_{acc['account_id']}_{acc['account_name']}"
                if account_key not in seen_accounts:
                    seen_accounts.add(account_key)
                    unique_results.append(acc)
            
            print(f"Removed {len(results) - len(unique_results)} duplicate records")
            print(f"Unique social media accounts: {len(unique_results)}")
            
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
            
            print(f"Successfully saved {saved_count} unique Axiom social media accounts to database")
            
        except Exception as e:
            print(f"Error parsing Axiom social media: {e}")
            self.db.rollback()
            raise e
        
        return unique_results
    
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
            if file_path.endswith('.xlsx'):
                engine = 'openpyxl'
            elif file_path.endswith('.xls'):
                engine = 'xlrd'
            else:
                engine = 'openpyxl'
            
            xls = pd.ExcelFile(file_path, engine=engine)
            
            print(f"📊 Total sheets available: {len(xls.sheet_names)}")
            print(f"📋 Sheet names: {xls.sheet_names}")
            
            if 'Social Media' in xls.sheet_names:
                print("🔍 Detected Cellebrite format - parsing Social Media sheet")
                # Parse all sheets with enhanced detection
                for sheet_name in xls.sheet_names:
                    print(f"Processing sheet: {sheet_name}")
                    
                    if sheet_name == 'Social Media':
                        results.extend(self._parse_cellebrite_social_media_sheet(file_path, sheet_name, file_id))
                    elif sheet_name == 'User Accounts':
                        results.extend(self._parse_cellebrite_user_accounts_sheet(file_path, sheet_name, file_id))
                    elif sheet_name == 'Contacts':
                        results.extend(self._parse_cellebrite_contacts_sheet(file_path, sheet_name, file_id))
                    elif sheet_name == 'Chats':
                        results.extend(self._parse_cellebrite_chats_sheet(file_path, sheet_name, file_id))
                    else:
                        # Check other sheets for social media data
                        results.extend(self._parse_cellebrite_generic_sheet(file_path, sheet_name, file_id))
            
            elif any(keyword in ' '.join(xls.sheet_names).lower() for keyword in ['instagram', 'facebook', 'twitter', 'whatsapp', 'telegram', 'tiktok']):
                print("🔍 Detected Oxygen format - parsing dedicated social media sheets")
                # Use Oxygen parser for dedicated social media sheets
                results.extend(self.parse_oxygen_social_media(file_path, file_id))
            
            else:
                print("🔍 Unknown format - attempting generic parsing")
                # Try generic parsing for unknown formats
                for sheet_name in xls.sheet_names:
                    print(f"Processing sheet: {sheet_name}")
                    results.extend(self._parse_cellebrite_generic_sheet(file_path, sheet_name, file_id))
            
            # Remove duplicates before saving
            unique_results = []
            seen_accounts = set()
            
            for acc in results:
                account_key = f"{acc['platform']}_{acc['account_id']}_{acc['account_name']}_{acc['file_id']}"
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
            
            # Fix column names if they are unnamed
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
                            "platform": "instagram",
                            "account_name": account_name,
                            "account_id": user_id,
                            "user_id": user_id,
                            "full_name": account_name,
                            "biography": body,
                            "profile_picture_url": url,
                            "source_tool": "Cellebrite",
                            "sheet_name": sheet_name,
                            "file_id": file_id
                        }
                        results.append(acc)
                
                elif source and source.lower() == 'facebook':
                    if author and account:
                        parts = author.split()
                        user_id = parts[0] if parts else account
                        account_name = ' '.join(parts[1:]) if len(parts) > 1 else account
                        
                        acc = {
                            "platform": "facebook",
                            "account_name": account_name,
                            "account_id": user_id,
                            "user_id": user_id,
                            "full_name": account_name,
                            "biography": body,
                            "profile_picture_url": url,
                            "source_tool": "Cellebrite",
                            "sheet_name": sheet_name,
                            "file_id": file_id
                        }
                        results.append(acc)
                
                elif source and source.lower() == 'twitter':
                    if author and account:
                        parts = author.split()
                        user_id = parts[0] if parts else account
                        account_name = ' '.join(parts[1:]) if len(parts) > 1 else account
                        
                        acc = {
                            "platform": "x",
                            "account_name": account_name,
                            "account_id": user_id,
                            "user_id": user_id,
                            "full_name": account_name,
                            "biography": body,
                            "profile_picture_url": url,
                            "source_tool": "Cellebrite",
                            "sheet_name": sheet_name,
                            "file_id": file_id
                        }
                        results.append(acc)
            
            print(f"Found {len(results)} social media accounts in {sheet_name} sheet")
            
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results
    
    def _parse_cellebrite_generic_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse generic sheets for social media data"""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            # Fix column names if they are unnamed
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            # Check all text columns for social media mentions
            for _, row in df.iterrows():
                for col_name, col_value in row.items():
                    if pd.isna(col_value) or not isinstance(col_value, str):
                        continue
                    
                    col_value_lower = col_value.lower()
                    
                    # Check for TikTok mentions
                    if 'tiktok' in col_value_lower:
                        # Extract TikTok username or ID
                        tiktok_match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', col_value)
                        if tiktok_match:
                            username = tiktok_match.group(1)
                            acc = {
                                "platform": "tiktok",
                                "account_name": username,
                                "account_id": username,
                                "user_id": username,
                                "full_name": username,
                                "biography": col_value,
                                "source_tool": "Cellebrite",
                                "sheet_name": sheet_name,
                                "file_id": file_id
                            }
                            results.append(acc)
                    
                    # Check for Instagram mentions
                    elif 'instagram' in col_value_lower:
                        # Extract Instagram username or ID
                        instagram_match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', col_value)
                        if instagram_match:
                            username = instagram_match.group(1)
                            acc = {
                                "platform": "instagram",
                                "account_name": username,
                                "account_id": username,
                                "user_id": username,
                                "full_name": username,
                                "biography": col_value,
                                "source_tool": "Cellebrite",
                                "sheet_name": sheet_name,
                                "file_id": file_id
                            }
                            results.append(acc)
                    
                    # Check for WhatsApp mentions
                    elif 'whatsapp' in col_value_lower:
                        # Extract WhatsApp number
                        whatsapp_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', col_value)
                        if whatsapp_match:
                            phone_number = whatsapp_match.group(1)
                            acc = {
                                "platform": "whatsapp",
                                "account_name": phone_number,
                                "account_id": phone_number,
                                "user_id": phone_number,
                                "full_name": phone_number,
                                "biography": col_value,
                                "source_tool": "Cellebrite",
                                "sheet_name": sheet_name,
                                "file_id": file_id
                            }
                            results.append(acc)
                    
                    # Check for Telegram mentions
                    elif 'telegram' in col_value_lower:
                        # Extract Telegram username
                        telegram_match = re.search(r'@([a-zA-Z0-9_]+)', col_value)
                        if telegram_match:
                            username = telegram_match.group(1)
                            acc = {
                                "platform": "telegram",
                                "account_name": username,
                                "account_id": username,
                                "user_id": username,
                                "full_name": username,
                                "biography": col_value,
                                "source_tool": "Cellebrite",
                                "sheet_name": sheet_name,
                                "file_id": file_id
                            }
                            results.append(acc)
                    
                    # Check for X/Twitter mentions
                    elif 'twitter' in col_value_lower or 'x.com' in col_value_lower:
                        # Extract Twitter/X username
                        twitter_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', col_value)
                        if twitter_match:
                            username = twitter_match.group(1)
                            acc = {
                                "platform": "x",
                                "account_name": username,
                                "account_id": username,
                                "user_id": username,
                                "full_name": username,
                                "biography": col_value,
                                "source_tool": "Cellebrite",
                                "sheet_name": sheet_name,
                                "file_id": file_id
                            }
                            results.append(acc)
                    
                    # Check for Facebook mentions
                    elif 'facebook' in col_value_lower:
                        # Extract Facebook ID or username
                        facebook_match = re.search(r'facebook\.com/([a-zA-Z0-9_.]+)', col_value)
                        if facebook_match:
                            username = facebook_match.group(1)
                            acc = {
                                "platform": "facebook",
                                "account_name": username,
                                "account_id": username,
                                "user_id": username,
                                "full_name": username,
                                "biography": col_value,
                                "source_tool": "Cellebrite",
                                "sheet_name": sheet_name,
                                "file_id": file_id
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
            
            # Fix column names if they are unnamed
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
                
                # Skip if no username
                if not username or username.lower() == 'n/a':
                    continue
                
                # Determine platform based on service type and source
                platform = None
                if 'instagram' in service_type.lower() or 'instagram' in source.lower():
                    platform = 'instagram'
                elif 'twitter' in service_type.lower() or 'twitter' in source.lower():
                    platform = 'x'
                elif 'telegram' in service_type.lower() or 'telegram' in source.lower():
                    platform = 'telegram'
                elif 'whatsapp' in service_type.lower() or 'whatsapp' in source.lower():
                    platform = 'whatsapp'
                elif 'facebook' in service_type.lower() or 'facebook' in source.lower():
                    platform = 'facebook'
                elif 'tiktok' in service_type.lower() or 'tiktok' in source.lower():
                    platform = 'tiktok'
                
                if platform:
                    phone_number = None
                    email = None
                    profile_picture_url = None
                    user_id = None
                    
                    if entries and entries.lower() != 'n/a':
                        # Extract phone number
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
                        
                        # Extract email
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
                        
                        # Extract profile picture URL
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
                        
                        # Extract user ID
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
                        'platform': platform,
                        'account_name': username,
                        'account_id': user_id or username,
                        'user_id': user_id or username,
                        'full_name': account_name if account_name and account_name.lower() != 'n/a' else username,
                        'phone_number': phone_number,
                        'email': email,
                        'profile_picture_url': profile_picture_url,
                        'source_tool': 'Cellebrite',
                        'sheet_name': sheet_name,
                        'file_id': file_id,
                    }
                    results.append(acc)
            
            print(f"Found {len(results)} social media accounts in {sheet_name} sheet")
            
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results
    
    def _parse_cellebrite_contacts_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            # Fix column names if they are unnamed
            if any('Unnamed' in str(col) for col in df.columns):
                df.columns = df.iloc[0]
                df = df.drop(df.index[0])
                df = df.reset_index(drop=True)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('#', '')) or str(row.get('#', '')).strip() == '#':
                    continue
                
                name = self._clean(row.get('Name', ''))
                entries = self._clean(row.get('Entries', ''))
                source = self._clean(row.get('Source', ''))
                
                if not name or name.lower() == 'n/a':
                    continue
                
                # Check for WhatsApp contacts
                if '@s.whatsapp.net' in entries:
                    whatsapp_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', entries)
                    if whatsapp_match:
                        phone_number = whatsapp_match.group(1)
                        acc = {
                            'platform': 'whatsapp',
                            'account_name': phone_number,
                            'account_id': phone_number,
                            'user_id': phone_number,
                            'full_name': name,
                            'phone_number': phone_number,
                            'source_tool': 'Cellebrite',
                            'sheet_name': sheet_name,
                            'file_id': file_id,
                        }
                        results.append(acc)
                
                # Check for Instagram contacts
                elif 'instagram' in entries.lower() or source.lower() == 'instagram':
                    instagram_match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', entries)
                    if instagram_match:
                        username = instagram_match.group(1)
                        acc = {
                            'platform': 'instagram',
                            'account_name': username,
                            'account_id': username,
                            'user_id': username,
                            'full_name': name,
                            'source_tool': 'Cellebrite',
                            'sheet_name': sheet_name,
                            'file_id': file_id,
                        }
                        results.append(acc)
                
                # Check for Facebook contacts
                elif 'facebook' in entries.lower() or source.lower() == 'facebook':
                    facebook_match = re.search(r'Facebook Id: ([0-9]+)', entries)
                    if facebook_match:
                        facebook_id = facebook_match.group(1)
                        acc = {
                            'platform': 'facebook',
                            'account_name': facebook_id,
                            'account_id': facebook_id,
                            'user_id': facebook_id,
                            'full_name': name,
                            'source_tool': 'Cellebrite',
                            'sheet_name': sheet_name,
                            'file_id': file_id,
                        }
                        results.append(acc)
                
                # Check for Twitter contacts
                elif 'twitter' in entries.lower() or source.lower() == 'twitter':
                    twitter_match = re.search(r'twitter\.com/([a-zA-Z0-9_]+)', entries)
                    if twitter_match:
                        username = twitter_match.group(1)
                        acc = {
                            'platform': 'x',
                            'account_name': username,
                            'account_id': username,
                            'user_id': username,
                            'full_name': name,
                            'source_tool': 'Cellebrite',
                            'sheet_name': sheet_name,
                            'file_id': file_id,
                        }
                        results.append(acc)
                
                # Check for TikTok contacts
                elif 'tiktok' in entries.lower():
                    tiktok_match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', entries)
                    if tiktok_match:
                        username = tiktok_match.group(1)
                        acc = {
                            'platform': 'tiktok',
                            'account_name': username,
                            'account_id': username,
                            'user_id': username,
                            'full_name': name,
                            'source_tool': 'Cellebrite',
                            'sheet_name': sheet_name,
                            'file_id': file_id,
                        }
                        results.append(acc)
                
                # Check for Telegram contacts
                elif 'telegram' in entries.lower() or source.lower() == 'telegram':
                    telegram_match = re.search(r'@([a-zA-Z0-9_]+)', entries)
                    if telegram_match:
                        username = telegram_match.group(1)
                        acc = {
                            'platform': 'telegram',
                            'account_name': username,
                            'account_id': username,
                            'user_id': username,
                            'full_name': name,
                            'source_tool': 'Cellebrite',
                            'sheet_name': sheet_name,
                            'file_id': file_id,
                        }
                        results.append(acc)
            
            print(f"Found {len(results)} social media accounts in {sheet_name} sheet")
            
        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")
        
        return results
    
    def _parse_cellebrite_chats_sheet(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            # Fix column names if they are unnamed
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
                                        "platform": "instagram",
                                        "account_name": username,
                                        "account_id": user_id,
                                        "user_id": user_id,
                                        "full_name": username,
                                        "biography": body,
                                        "source_tool": "Cellebrite",
                                        "sheet_name": sheet_name,
                                        "file_id": file_id,
                                    }
                                    results.append(acc)
                
                # Check for WhatsApp chats
                elif source and source.lower() == 'whatsapp':
                    if participants:
                        participant_lines = participants.split('_x000d_')
                        for line in participant_lines:
                            line = line.strip()
                            if line and '@s.whatsapp.net' in line:
                                whatsapp_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', line)
                                if whatsapp_match:
                                    phone_number = whatsapp_match.group(1)
                                    acc = {
                                        "platform": "whatsapp",
                                        "account_name": phone_number,
                                        "account_id": phone_number,
                                        "user_id": phone_number,
                                        "full_name": phone_number,
                                        "biography": body,
                                        "source_tool": "Cellebrite",
                                        "sheet_name": sheet_name,
                                        "file_id": file_id,
                                    }
                                    results.append(acc)
                
                # Check for Telegram chats
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
                                        "platform": "telegram",
                                        "account_name": username,
                                        "account_id": user_id,
                                        "user_id": user_id,
                                        "full_name": username,
                                        "biography": body,
                                        "source_tool": "Cellebrite",
                                        "sheet_name": sheet_name,
                                        "file_id": file_id,
                                    }
                                    results.append(acc)
                
                # Check for TikTok mentions in chat content
                elif body and 'tiktok' in body.lower():
                    tiktok_match = re.search(r'tiktok\.com/@([a-zA-Z0-9_.]+)', body)
                    if tiktok_match:
                        username = tiktok_match.group(1)
                        acc = {
                            "platform": "tiktok",
                            "account_name": username,
                            "account_id": username,
                            "user_id": username,
                            "full_name": username,
                            "biography": body,
                            "source_tool": "Cellebrite",
                            "sheet_name": sheet_name,
                            "file_id": file_id,
                        }
                        results.append(acc)
                
                # Check for Facebook mentions in chat content
                elif body and 'facebook' in body.lower():
                    facebook_match = re.search(r'facebook\.com/([a-zA-Z0-9_.]+)', body)
                    if facebook_match:
                        username = facebook_match.group(1)
                        acc = {
                            "platform": "facebook",
                            "account_name": username,
                            "account_id": username,
                            "user_id": username,
                            "full_name": username,
                            "biography": body,
                            "source_tool": "Cellebrite",
                            "sheet_name": sheet_name,
                            "file_id": file_id,
                        }
                        results.append(acc)
                
                # Check for X/Twitter mentions in chat content
                elif body and ('twitter' in body.lower() or 'x.com' in body.lower()):
                    twitter_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', body)
                    if twitter_match:
                        username = twitter_match.group(1)
                        acc = {
                            "platform": "x",
                            "account_name": username,
                            "account_id": username,
                            "user_id": username,
                            "full_name": username,
                            "biography": body,
                            "source_tool": "Cellebrite",
                            "sheet_name": sheet_name,
                            "file_id": file_id,
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

    def _parse_axiom_instagram_following(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User Name')):
                    continue
                
                # Extract following status
                following_value = self._clean(row.get('Status'))
                following_count = 1 if following_value and following_value.lower() == 'following' else None
                
                acc = {
                    "platform": "instagram",
                    "account_name": self._clean(row.get('User Name')),
                    "account_id": self._clean(row.get('User Name')),
                    "user_id": self._clean(row.get('ID')),
                    "full_name": self._clean(row.get('Full Name')),
                    "following": following_count,
                    "followers": None,
                    "biography": self._clean(row.get('Biography')),
                    "profile_picture_url": self._clean(row.get('Profile Picture URL')),
                    "is_private": self._safe_bool(row.get('Account Type') == 'Private'),
                    "source_tool": "Axiom",
                    "sheet_name": "Android Instagram Following",
                    "file_id": file_id,
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
                
                acc = {
                    "platform": "instagram",
                    "account_name": self._clean(row.get('User Name')),
                    "account_id": self._clean(row.get('User Name')),
                    "user_id": self._clean(row.get('ID')),
                    "full_name": self._clean(row.get('Full Name')),
                    "following": None,
                    "followers": None,
                    "biography": None,
                    "profile_picture_url": self._clean(row.get('Profile Picture URL')),
                    "is_private": None,
                    "source_tool": "Axiom",
                    "sheet_name": "Android Instagram Users",
                    "file_id": file_id,
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
                
                # Only process Telegram-related accounts
                if not service_name or 'telegram' not in service_name.lower():
                    continue
                
                if not user_name and not user_id:
                    continue
                
                acc = {
                    "platform": "telegram",
                    "account_name": user_name or user_id,
                    "account_id": user_id or user_name,
                    "user_id": user_id,
                    "full_name": user_name,
                    "following": None,
                    "followers": None,
                    "biography": None,
                    "profile_picture_url": self._clean(row.get('Profile Image URL')),
                    "phone_number": self._clean(row.get('Phone Number(s)')),
                    "email": self._clean(row.get('Email Address(es)')),
                    "source_tool": "Axiom",
                    "sheet_name": "User Accounts",
                    "file_id": file_id,
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
                    "platform": "whatsapp",
                    "account_name": whatsapp_name or phone_number,
                    "account_id": phone_number or whatsapp_name,
                    "user_id": phone_number,
                    "full_name": whatsapp_name,
                    "following": None,
                    "followers": None,
                    "biography": None,
                    "profile_picture_url": None,
                    "phone_number": phone_number,
                    "source_tool": "Axiom",
                    "sheet_name": "WhatsApp Accounts Information",
                    "file_id": file_id,
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
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl", dtype=str)
            
            for _, row in df.iterrows():
                # Skip rows without ID
                if pd.isna(row.get("ID")):
                    continue
                
                # Prioritize Nickname over User Name for account_name
                nickname = self._clean(row.get("Nickname"))
                user_name = self._clean(row.get("User Name"))
                account_name = nickname or user_name
                
                acc = {
                    "platform": "tiktok",
                    "account_name": account_name,
                    "account_id": self._clean(row.get("ID")),
                    "user_id": self._clean(row.get("ID")),
                    "full_name": nickname or user_name,
                    "following": None,
                    "followers": None,
                    "biography": None,
                    "profile_picture_url": self._clean(row.get("Profile Picture URL")),
                    "source_tool": "Axiom",
                    "sheet_name": "TikTok Contacts",
                    "file_id": file_id,
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
                    "source_tool": "Axiom",                    
                    "file_id": file_id,
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
                    "source_tool": "Axiom",                    
                    "file_id": file_id,
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
                    "source_tool": "Axiom",                    
                    "file_id": file_id,
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
                    "source_tool": "Axiom",                    
                    "file_id": file_id,
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
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('Message')) or not str(row.get('Message')).strip():
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
                    "source_tool": "axiom"
                }
                
                results.append(message_data)
            
        except Exception as e:
            print(f"Error parsing Instagram messages: {e}")
        
        return results

    def _parse_tiktok_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
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

    # Magnet Axiom specific parsers for sample_data format
    def _parse_axiom_whatsapp_accounts_info(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
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
            
            # Fix column names if they are unnamed
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
            
            # Fix column names if they are unnamed
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
            
            # Fix column names if they are unnamed
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
            
            # Fix column names if they are unnamed
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

    def _parse_axiom_telegram_messages(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
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
