import re
import pandas as pd  # type: ignore
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session  # type: ignore
from app.analytics.device_management.models import SocialMedia, ChatMessage
from app.db.session import get_db
from .file_validator import file_validator
from .social_media_parsers_extended import SocialMediaParsersExtended

import warnings
import sys

warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', module='openpyxl')
warnings.filterwarnings('ignore', module='xlrd')
warnings.filterwarnings('ignore', message='.*OLE2.*')
warnings.filterwarnings('ignore', message='.*OLE2 inconsistency.*')
warnings.filterwarnings('ignore', message='.*file size.*not.*multiple of sector size.*')
warnings.filterwarnings('ignore', message='.*SSCS size is 0 but SSAT size is non-zero.*')
warnings.filterwarnings('ignore', message='.*WARNING \*\*\*.*')
# Suppress stderr for OLE2 warnings from xlrd/openpyxl
import io
class FilteredStderr(io.TextIOWrapper):
    def write(self, s):
        if isinstance(s, str):
            if 'OLE2 inconsistency' not in s and 'SSCS size is 0' not in s and 'WARNING ***' not in s:
                super().write(s)
        else:
            super().write(s)

try:
    if sys.stderr:
        original_stderr = sys.stderr
        def write_filtered(data):
            if isinstance(data, str):
                if 'OLE2 inconsistency' not in data and 'SSCS size is 0' not in data and 'WARNING ***' not in data:
                    original_stderr.write(data)
            else:
                original_stderr.write(data)
        
        class FilteredStderrWrapper:
            def write(self, data):
                write_filtered(data)
            def flush(self):
                original_stderr.flush()
            def __getattr__(self, name):
                return getattr(original_stderr, name)
        
        sys.stderr = FilteredStderrWrapper()
except:
    pass

SOCIAL_MEDIA_PLATFORMS = ["instagram", "facebook", "whatsapp", "telegram", "x", "tiktok"]

class SocialMediaParser(SocialMediaParsersExtended):

    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db

    def _to_int_safe(self, value: Optional[str], max_value: int = 2147483647) -> Optional[int]:
        if value is None:
            return None
        text = str(value).strip()
        if text == "" or text.lower() == "nan":
            return None
        sign = -1 if text.startswith('-') else 1
        digits = ''.join(ch for ch in text if ch.isdigit())
        if digits == "":
            return None
        try:
            num = sign * int(digits)
            if -max_value <= num <= max_value:
                return num
            return None
        except Exception:
            return None

    def parse_oxygen_ufed_social_media(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []

        try:
            xls = pd.ExcelFile(file_path, engine='xlrd')
            
            if 'Contacts ' in xls.sheet_names:
                contacts_df = pd.read_excel(file_path, sheet_name='Contacts ', dtype=str, engine='xlrd')
                
                print("=" * 60)
                print("FOCUS: Parsing Instagram only from Contacts sheet")
                print("=" * 60)

                if 'Source' not in contacts_df.columns:
                    print("  Column 'Source' not found in Contacts sheet")
                    return results

                instagram_rows = contacts_df[contacts_df['Source'].str.contains('Instagram', case=False, na=False)]
                print(f"  Found {len(instagram_rows)} rows with Source containing 'Instagram'")

                if len(instagram_rows) == 0:
                    print("  No Instagram rows found")
                    return results

                for _, row in instagram_rows.iterrows():
                    source = self._clean(row.get('Source', ''))
                    type_field = self._clean(row.get('Type', ''))
                    contact = self._clean(row.get('Contact', ''))
                    internet = self._clean(row.get('Internet', ''))
                    addresses = self._clean(row.get('Addresses', ''))
                    
                    if not source or self._is_header_or_metadata(source):
                        continue

                    full_name = self._extract_full_name_from_contact(contact)
                    account_name = self._extract_nickname(contact)
                    instagram_id = self._extract_platform_id(internet, "instagram")
                    location = self._extract_location(addresses)

                    if account_name or instagram_id:
                        acc = {
                            "file_id": file_id,
                            "type": type_field,
                            "source": source.strip(),
                            "phone_number": None,
                            "full_name": full_name,
                            "account_name": account_name,
                            "instagram_id": instagram_id,
                            "location": location,
                            "whatsapp_id": None,
                            "telegram_id": None,
                            "X_id": None,
                            "facebook_id": None,
                            "tiktok_id": None,
                            "sheet_name": "Contacts",
                        }

                        is_valid, error_msg = self._validate_social_media_data_new(acc)
                        if is_valid:
                            results.append(acc)
                        else:
                            if len(results) < 5:
                                print(f"⚠️  Skipping invalid record: {error_msg}")
            
            batch_size = 50
            saved_count = 0
            skipped_count = 0
            invalid_count = 0
            
            for i in range(0, len(results), batch_size):
                batch = results[i:i + batch_size]
                batch_saved = 0
                
                try:
                    for acc in batch:
                        is_valid, error_msg = self._validate_social_media_data(acc)
                        if not is_valid:
                            invalid_count += 1
                            if invalid_count <= 5:
                                log_acc = self._convert_old_to_new_structure(acc) if "platform" in acc else acc
                                platform_info = []
                                if log_acc.get('instagram_id'):
                                    platform_info.append(f"IG:{log_acc['instagram_id']}")
                                if log_acc.get('facebook_id'):
                                    platform_info.append(f"FB:{log_acc['facebook_id']}")
                                if log_acc.get('whatsapp_id'):
                                    platform_info.append(f"WA:{log_acc['whatsapp_id']}")
                                if log_acc.get('X_id'):
                                    platform_info.append(f"X:{log_acc['X_id']}")
                                platform_str = ', '.join(platform_info) if platform_info else 'Unknown'
                                print(f"⚠️  Skipping invalid record: {error_msg} - Platform IDs: {platform_str}, Account: {log_acc.get('account_name', 'N/A')}")
                            continue

                        if "platform" in acc:
                            acc = self._convert_old_to_new_structure(acc)

                        if self._check_existing_social_media(acc):
                            skipped_count += 1
                            continue

                        # Simpan ke DB
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
            
            print(f"Successfully saved {saved_count} Oxygen UFED social media accounts to database")
            if skipped_count > 0:
                print(f"  ({skipped_count} records skipped - already exist)")
            if invalid_count > 0:
                print(f"  ({invalid_count} records skipped - invalid data)")

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
                
                # FOKUS PARSING INSTAGRAM SAJA - Skip platform lain untuk sementara
                print("=" * 60)
                print("FOCUS: Parsing Instagram only (other platforms disabled)")
                print("=" * 60)
                
                # Parse Instagram sheets dan Contacts sheet (Instagram only)
                results.extend(self._parse_oxygen_instagram_sheets(file_path, xls, file_id, engine))
                results.extend(self._parse_oxygen_contacts_sheet(file_path, xls, file_id, engine))

            unique_results = []
            seen_accounts = set()
            
            for acc in results:
                if "platform" in acc:
                    account_key = f"{acc.get('platform', '')}_{acc.get('account_id', '')}_{acc.get('account_name', '')}"
                else:
                    # Struktur baru - gunakan platform IDs
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
            
            # Save to database in batches
            batch_size = 50
            saved_count = 0
            skipped_count = 0
            invalid_count = 0
            
            for i in range(0, len(unique_results), batch_size):
                batch = unique_results[i:i + batch_size]
                batch_saved = 0
                
                try:
                    for acc in batch:
                        # Validasi data sebelum insert
                        is_valid, error_msg = self._validate_social_media_data(acc)
                        if not is_valid:
                            invalid_count += 1
                            if invalid_count <= 5:  # Log first 5 invalid records
                                # Convert untuk logging
                                log_acc = self._convert_old_to_new_structure(acc) if "platform" in acc else acc
                                platform_info = []
                                if log_acc.get('instagram_id'):
                                    platform_info.append(f"IG:{log_acc['instagram_id']}")
                                if log_acc.get('facebook_id'):
                                    platform_info.append(f"FB:{log_acc['facebook_id']}")
                                if log_acc.get('whatsapp_id'):
                                    platform_info.append(f"WA:{log_acc['whatsapp_id']}")
                                if log_acc.get('X_id'):
                                    platform_info.append(f"X:{log_acc['X_id']}")
                                platform_str = ', '.join(platform_info) if platform_info else 'Unknown'
                                print(f"⚠️  Skipping invalid record: {error_msg} - Platform IDs: {platform_str}, Account: {log_acc.get('account_name', 'N/A')}")
                            continue
                        
                        # Convert ke struktur baru jika perlu
                        if "platform" in acc:
                            acc = self._convert_old_to_new_structure(acc)
                        
                        # Check duplicate menggunakan struktur baru
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
            
            print(f"Successfully saved {saved_count} unique Oxygen social media accounts to database")
            if skipped_count > 0:
                print(f"  ({skipped_count} records skipped - already exist)")
            if invalid_count > 0:
                print(f"  ({invalid_count} records skipped - invalid data)")

        except Exception as e:
            print(f"Error parsing social media Oxygen: {e}")
            self.db.rollback()
            raise e

        return unique_results

    def _parse_oxygen_instagram_sheets(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        print("Note: Instagram dedicated sheets skipped - only parsing from Contacts sheet")
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
                                "phone_number": None,
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
                            "phone_number": None,
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
                            "phone_number": None,
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
                    
                    # Skip jika source_field adalah header
                    if source_field and self._is_header_or_metadata(source_field):
                        continue
                    
                    if source_field and 'telegram' in source_field.lower():
                        telegram_id = None
                        if internet_field and 'telegram id:' in internet_field.lower():
                            match = re.search(r'telegram id:\s*(\d+)', internet_field.lower())
                            if match:
                                telegram_id = match.group(1)
                        
                        account_name = self._extract_name(contact_field)
                        if not account_name and telegram_id:
                            account_name = telegram_id
                        
                        # Skip jika account_name adalah header/metadata
                        if account_name and self._is_header_or_metadata(account_name):
                            continue
                        
                        if telegram_id:
                            acc = {
                                "platform": "telegram",
                                "account_name": account_name,
                                "account_id": telegram_id,
                                "user_id": telegram_id,
                                "full_name": self._extract_full_name(contact_field),
                                "following": None,
                                "followers": None,
                                "phone_number": self._extract_phone_number(phones_emails_field),
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
                
                # Skip header row jika terdeteksi
                for _, row in df.iterrows():
                    source_field = self._clean(row.get("Source"))
                    internet_field = self._clean(row.get("Internet"))
                    contact_field = self._clean(row.get("Contact"))
                    phones_emails_field = self._clean(row.get("Phones & Emails"))
                    other_field = self._clean(row.get("Other"))
                    
                    # Skip jika source_field adalah header
                    if source_field and self._is_header_or_metadata(source_field):
                        continue
                    
                    if source_field and 'whatsapp' in source_field.lower():
                        whatsapp_id = None
                        if internet_field and 'whatsapp id:' in internet_field.lower():
                            match = re.search(r'whatsapp id:\s*(\d+)', internet_field.lower())
                            if match:
                                whatsapp_id = match.group(1)
                        
                        account_name = self._extract_name(contact_field)
                        if not account_name and whatsapp_id:
                            account_name = whatsapp_id
                        
                        # Skip jika account_name adalah header/metadata
                        if account_name and self._is_header_or_metadata(account_name):
                            continue
                        
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
                                "phone_number": phone_number,
                                "source_tool": "Oxygen",
                                "sheet_name": "Contacts",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing WhatsApp sheets: {e}")
        
        return results

    def _extract_platform_id(self, text: str, platform: str) -> Optional[str]:
        """Extract platform ID dari text berdasarkan platform"""
        if not text:
            return None
        
        text_str = str(text)
        platform_lower = platform.lower()
        
        patterns = {
            "instagram": r"Instagram\s+ID[:\s]*(\d+)",
            "facebook": r"Facebook\s+ID[:\s]*(\d+)",
            "whatsapp": r"WhatsApp\s+ID[:\s]*([\+\d\s\-\(\)]+)|Phone\s+number[:\s]*([\+\d\s\-\(\)]+)",
            "telegram": r"Telegram\s+ID[:\s]*(\d+)",
            "x": r"(?:X|Twitter)\s+ID[:\s]*(\d+)",
            "twitter": r"(?:X|Twitter)\s+ID[:\s]*(\d+)",
            "tiktok": r"TikTok\s+ID[:\s]*(\d+)",
        }
        
        pattern = patterns.get(platform_lower)
        if pattern:
            match = re.search(pattern, text_str, re.IGNORECASE)
            if match:
                # Ambil group pertama yang tidak None
                for group in match.groups():
                    if group:
                        return group.strip()
        return None
    
    def _extract_nickname(self, text: str) -> Optional[str]:
        """Extract nickname dari Contact field"""
        if not text:
            return None
        
        text_str = str(text)
        # Cari "Nickname: username"
        match = re.search(r"Nickname[:\s]+([^\n]+)", text_str, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location dari Addresses field"""
        if not text:
            return None
        
        text_str = str(text)
        # Cari "Location: Bandung, Indonesia"
        match = re.search(r"Location[:\s]+([^\n]+)", text_str, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_phone_number_from_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        text_str = str(text)
        
        match = re.search(r"Phone\s+number[:\s]+([\+\d\s\-\(\)@\.]+)", text_str, re.IGNORECASE)
        if match:
            phone = match.group(1).strip()
            # Clean @s.whatsapp.net jika ada
            phone = phone.replace('@s.whatsapp.net', '')
            # Clean whitespace dan karakter non-digit (kecuali + di awal)
            phone = re.sub(r'\s+', '', phone)
            # Hapus karakter selain digit dan + (di awal saja)
            if phone.startswith('+'):
                phone = '+' + re.sub(r'[^\d]', '', phone[1:])
            else:
                phone = re.sub(r'[^\d]', '', phone)
            # Skip phone_number yang hanya "0" atau terlalu pendek
            if phone and len(phone) >= 8 and phone not in ['0', '+0']:
                return phone
        
        
        phone_match = re.search(r"(?:Home|Mobile|Work|Cell|Phone|Office)[:\s]+([\+\d\s\-\(\)]+)", text_str, re.IGNORECASE)
        if phone_match:
            phone = phone_match.group(1).strip()
            # Clean @s.whatsapp.net jika ada
            phone = phone.replace('@s.whatsapp.net', '')
            # Clean whitespace
            phone = re.sub(r'\s+', '', phone)
            # Hapus karakter selain digit dan + (di awal saja)
            if phone.startswith('+'):
                phone = '+' + re.sub(r'[^\d]', '', phone[1:])
            else:
                phone = re.sub(r'[^\d]', '', phone)
            # Skip phone_number yang hanya "0" atau terlalu pendek
            if phone and len(phone) >= 8 and phone not in ['0', '+0']:
                return phone
        
        return None
    
    def _extract_full_name_from_contact(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        text_str = str(text)
        lines = [line.strip() for line in text_str.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # Ambil line pertama yang tidak dimulai dengan "Nickname:"
        for line in lines:
            if not line.lower().startswith('nickname:'):
                full_name = line.strip()
                if '@s.whatsapp.net' in full_name:
                    full_name = full_name.replace('@s.whatsapp.net', '').strip()
                    # Jika hanya tersisa angka, gunakan sebagai full_name
                    if full_name and full_name.isdigit():
                        return full_name
                return full_name
        
        return None

    def _extract_whatsapp_id_from_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        text_str = str(text)
        match = re.search(r'WhatsApp\s+ID[:\s]+([^\n\r]+)', text_str, re.IGNORECASE)
        if match:
            whatsapp_id_raw = match.group(1).strip()
            
            if '@s.whatsapp.net' in whatsapp_id_raw:
                number_part = whatsapp_id_raw.split('@s.whatsapp.net')[0].strip()
                # Clean dari karakter non-digit di awal/akhir
                number_part = re.sub(r'^[^\d]+', '', number_part)
                number_part = re.sub(r'[^\d]+$', '', number_part)
                
                if number_part and number_part.isdigit() and len(number_part) >= 11 and number_part.startswith('8'):
                    number_part = number_part[1:]  # Hapus digit pertama "8"
                
                if number_part and number_part.isdigit() and len(number_part) >= 8:
                    # Return dengan format @s.whatsapp.net
                    return f"{number_part}@s.whatsapp.net"
            else:
                whatsapp_id = whatsapp_id_raw
                whatsapp_id = re.sub(r'^[^\d]+', '', whatsapp_id)
                whatsapp_id = re.sub(r'[^\d]+$', '', whatsapp_id)
                
                # Jika nomor dimulai dengan "8" dan panjang >= 11 digit, hapus digit pertama "8"
                if whatsapp_id and whatsapp_id.isdigit() and len(whatsapp_id) >= 11 and whatsapp_id.startswith('8'):
                    whatsapp_id = whatsapp_id[1:]
                
                if whatsapp_id and whatsapp_id.isdigit() and len(whatsapp_id) >= 8:
                    return whatsapp_id
        
        return None
    
    def _extract_telegram_id_from_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        text_str = str(text)
        
        # Cari "Telegram ID: 123456789"
        match = re.search(r'Telegram\s+ID[:\s]+(\d+)', text_str, re.IGNORECASE)
        if match:
            telegram_id = match.group(1).strip()
            if telegram_id and telegram_id.isdigit():
                return telegram_id
        
        # Cari "Username: @username" atau "Telegram: @username"
        username_match = re.search(r'(?:Telegram|Username)[:\s]+@?([a-zA-Z0-9_]+)', text_str, re.IGNORECASE)
        if username_match:
            username = username_match.group(1).strip()
            if username and len(username) > 0:
                return username
        
        return None
    
    def _extract_tiktok_id_from_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        text_str = str(text)
        
        # Cari "TikTok ID: 123456789" atau "TikTok: @username"
        match = re.search(r'TikTok\s+(?:ID|Username)[:\s]+@?([a-zA-Z0-9_\.]+)', text_str, re.IGNORECASE)
        if match:
            tiktok_id = match.group(1).strip()
            if tiktok_id:
                return tiktok_id
        
        # Cari "TikTok: username" atau "@username"
        username_match = re.search(r'TikTok[:\s]+@?([a-zA-Z0-9_\.]+)', text_str, re.IGNORECASE)
        if username_match:
            username = username_match.group(1).strip()
            if username:
                return username
        
        return None
    
    def _extract_x_id_from_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        text_str = str(text)
        
        match = re.search(r'(?:Twitter|X)\s+ID[:\s]+([a-zA-Z0-9_]+)', text_str, re.IGNORECASE)
        if match:
            x_id = match.group(1).strip()
            if x_id and len(x_id) > 0:
                return x_id
        
        # Cari "Twitter: @username" atau "X: @username" (format lama untuk backward compatibility)
        username_match = re.search(r'(?:Twitter|X)[:\s]+@?([a-zA-Z0-9_]+)', text_str, re.IGNORECASE)
        if username_match:
            username = username_match.group(1).strip()
            if username:
                return username
        
        return None
    
    def _extract_facebook_id_from_text(self, text: str) -> Optional[str]:
        if not text:
            return None
        
        text_str = str(text)
        
        # Cari "Facebook ID: 123456789"
        match = re.search(r'Facebook\s+ID[:\s]+(\d+)', text_str, re.IGNORECASE)
        if match:
            facebook_id = match.group(1).strip()
            if facebook_id and facebook_id.isdigit():
                return facebook_id
        
        # Cari "Facebook: profile/username" atau "Facebook: username"
        username_match = re.search(r'Facebook[:\s]+(?:profile/)?([a-zA-Z0-9_\.]+)', text_str, re.IGNORECASE)
        if username_match:
            username = username_match.group(1).strip()
            if username and len(username) > 0:
                return username
        
        return None
    
    def _extract_whatsapp_account_name_from_contact(self, contact_field: str) -> Optional[str]:
        if not contact_field:
            return None
        
        contact_str = str(contact_field).strip()
        
        # Skip jika kosong atau nan
        if contact_str.lower() in ['nan', 'none', 'null', '']:
            return None
        
        if '@s.whatsapp.net' in contact_str:
            account_name = contact_str.split('@s.whatsapp.net')[0].strip()
            # Clean dari karakter non-digit di awal/akhir
            account_name = re.sub(r'^[^\d]+', '', account_name)
            account_name = re.sub(r'[^\d]+$', '', account_name)
            if account_name and account_name.isdigit() and len(account_name) >= 8:  # Minimal 8 digit
                return account_name
        
        if '\n' in contact_str or 'nickname:' in contact_str.lower():
            nickname = self._extract_nickname(contact_str)
            if nickname:
                nickname = self._clean_whatsapp_suffix(nickname)
                if nickname and nickname.isdigit() and len(nickname) >= 8:
                    return nickname
                # Jika bukan angka atau angka pendek, tetap return jika valid
                if nickname and len(nickname) > 1 and not nickname.isdigit():
                    return nickname
        
       
        contact_clean = contact_str.strip()
        if contact_clean.isdigit() and len(contact_clean) >= 8:
            return contact_clean
        
        # Jika berisi format lain, coba clean dan return jika valid
        contact_clean = self._clean_whatsapp_suffix(contact_str)
        if contact_clean and len(contact_clean) > 1:
            # Skip jika terlihat seperti header/metadata
            if not self._is_header_or_metadata(contact_clean):
                return contact_clean
        
        return None

    def _parse_oxygen_contacts_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            sheet_name = file_validator._find_contacts_sheet(xls.sheet_names)
            if not sheet_name:
                print("  Contacts sheet not found")
                return results

            print(f"Parsing Contacts sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine)

            required_columns = ['Source', 'Type', 'Contact', 'Internet', 'Addresses']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"  Missing required columns: {missing_columns}")
                return results

            instagram_rows = df[df['Source'].str.contains('Instagram', case=False, na=False)]
            
            print(f"  Found {len(instagram_rows)} rows with Source containing 'Instagram'")
            
            if len(instagram_rows) > 0:
                print(f"  Parsing {len(instagram_rows)} Instagram rows from Contacts sheet...")

            for _, row in instagram_rows.iterrows():
                source_field = self._clean(row.get("Source"))
                if not source_field or self._is_header_or_metadata(source_field):
                    continue
                
                # Ambil data dari kolom yang diperlukan
                type_field = self._clean(row.get("Type"))
                source_clean = source_field.strip()
                contact_field = self._clean(row.get("Contact"))
                internet_field = self._clean(row.get("Internet"))
                addresses_field = self._clean(row.get("Addresses"))
                
                # Extract data dari Contact field
                full_name = self._extract_full_name_from_contact(contact_field)
                account_name = self._extract_nickname(contact_field)
                
                if not account_name and contact_field:
                    contact_str = str(contact_field).strip()
                    # Skip jika ini pure numeric panjang (kemungkinan Group ID, bukan username)
                    if contact_str.isdigit() and len(contact_str) > 15:
                        # Ini mungkin Group ID, akan ditangani nanti di extract instagram_id
                        pass
                    elif ('\n' not in contact_str and 'nickname:' not in contact_str.lower() and 
                        len(contact_str) > 1 and len(contact_str) < 50 and  # Panjang wajar untuk username
                        not contact_str.isdigit() and  # Bukan pure number
                        '@' not in contact_str and '/' not in contact_str and '\\' not in contact_str):
                        # Kemungkinan ini langsung username
                        account_name = contact_str
                        full_name = None  # Jika langsung username, full_name = None
                
                if not account_name:
                    # Cek kolom dengan nama yang mungkin berisi Instagram username
                    possible_columns = ['Instagram', 'instagram', 'Account Name', 'account_name', 'Username', 'username']
                    for col_name in possible_columns:
                        if col_name in df.columns:
                            col_value = self._clean(row.get(col_name))
                            if col_value and not self._is_header_or_metadata(col_value):
                                # Jika kolom berisi username/handle Instagram (bukan ID, bukan path, bukan email)
                                col_str = str(col_value).strip()
                                if (col_str.lower() not in ['nan', 'n/a', 'none', 'null', ''] and 
                                    '@' not in col_str and '/' not in col_str and 
                                    '\\' not in col_str and len(col_str) > 1 and 
                                    not col_str.isdigit()):  # Bukan pure numeric (mungkin ID)
                                    account_name = col_str
                                    print(f"  Found account_name in column '{col_name}': {account_name}")
                                    break
                    
                    if not account_name:
                        # Cek semua kolom (kecuali yang sudah dicek)
                        excluded_cols = ['Source', 'Type', 'Contact', 'Internet', 'Addresses', 'Photo', 'Deleted', 'Calls', 'Messages']
                        for col_name in df.columns:
                            if col_name in excluded_cols:
                                continue
                            col_value = self._clean(row.get(col_name))
                            if col_value and not self._is_header_or_metadata(col_value):
                                col_str = str(col_value).strip()
                                # Validasi: bukan null/nan, bukan email, bukan path, bukan pure number, minimal 2 karakter
                                if (col_str.lower() not in ['nan', 'n/a', 'none', 'null', ''] and 
                                    '@' not in col_str and '/' not in col_str and 
                                    '\\' not in col_str and len(col_str) > 1 and 
                                    not col_str.isdigit() and
                                    not col_str.lower().startswith('http')):
                                    account_name = col_str
                                    print(f"  Found account_name in column '{col_name}': {account_name}")
                                    break
                
                # Extract location dari Addresses field
                location = self._extract_location(addresses_field)
                
                # Extract Instagram ID dari Internet field
                instagram_id = self._extract_platform_id(internet_field, "instagram")
                
                if not instagram_id and internet_field:
                    group_id_match = re.search(r'Group\s+ID[:\s]+(\d+)', str(internet_field), re.IGNORECASE)
                    if group_id_match:
                        instagram_id = group_id_match.group(1).strip()
                        print(f"  Found Group ID as instagram_id: {instagram_id}")
                
                if not instagram_id and contact_field:
                    contact_str = str(contact_field).strip()
                    # Jika Contact field adalah pure numeric panjang (>15 digits), gunakan sebagai instagram_id
                    if contact_str.isdigit() and len(contact_str) > 15:
                        instagram_id = contact_str
                        print(f"  Found Group ID from Contact field (pure numeric): {instagram_id}")
                    # Atau jika Type=Group dan Contact field numeric
                    elif type_field and 'group' in type_field.lower() and contact_str.isdigit():
                        instagram_id = contact_str
                        print(f"  Found Group ID from Contact field (Type=Group): {instagram_id}")
                    # Atau jika Type=Contact dan Contact field numeric >=10 digits (mungkin Instagram user ID)
                    elif type_field and 'contact' in type_field.lower() and contact_str.isdigit() and len(contact_str) >= 10:
                        instagram_id = contact_str
                        print(f"  Found Instagram ID from Contact field (Type=Contact, numeric >=10 digits): {instagram_id}")
                
                # Extract phone_number dari Internet field jika ada (optional)
                phone_number = None
                phone_from_internet = self._extract_phone_number_from_text(internet_field)
                if phone_from_internet:
                    phone_number = self._clean_whatsapp_suffix(phone_from_internet)
                
                acc = {
                    "file_id": file_id,
                    "type": type_field, 
                    "source": source_clean,
                    "phone_number": phone_number,
                    "full_name": full_name,
                    "account_name": account_name,
                    "instagram_id": instagram_id,
                    "location": location,  # dari kolom Addresses
                    "whatsapp_id": None,  # tidak diisi (hanya Instagram)
                    "telegram_id": None,  # tidak diisi (hanya Instagram)
                    "X_id": None,  # tidak diisi (hanya Instagram)
                    "facebook_id": None,  # tidak diisi (hanya Instagram)
                    "tiktok_id": None,  # tidak diisi (hanya Instagram)
                    "sheet_name": sheet_name,
                }
  
                if account_name or instagram_id:
                    # Validasi data sebelum append
                    is_valid, error_msg = self._validate_social_media_data_new(acc)
                    if is_valid:
                        results.append(acc)
                    else:
                        print(f"⚠️  Skipping invalid Instagram record: {error_msg}")
                        print(f"   Details: account_name={account_name}, instagram_id={instagram_id}, full_name={full_name}, type={type_field}")
                else:
                    # Log rows yang tidak punya account_name maupun instagram_id
                    print(f"⚠️  Skipping row: No account_name and no instagram_id")
                    print(f"   Details: Type={type_field}, Source={source_clean}, Contact={contact_field[:50] if contact_field else 'None'}, Internet={internet_field[:50] if internet_field else 'None'}")
                    # Cek semua kolom untuk debugging
                    for col in df.columns:
                        col_val = self._clean(row.get(col))
                        if col_val and col_val.lower() not in ['nan', 'none', 'null', ''] and len(col_val) > 1:
                            print(f"   Column '{col}': {col_val[:50]}")
            
            # Save to database
            if results:
                print(f"  Found {len(results)} valid Instagram records from Contacts sheet")
                batch_size = 50
                saved_count = 0
                skipped_count = 0
                
                for i in range(0, len(results), batch_size):
                    batch = results[i:i + batch_size]
                    batch_saved = 0
                    
                    try:
                        for acc in batch:
                            # Check duplicate menggunakan struktur baru
                            if self._check_existing_social_media(acc):
                                skipped_count += 1
                                continue
                            
                            self.db.add(SocialMedia(**acc))
                            batch_saved += 1
                        
                        self.db.commit()
                        saved_count += batch_saved
                        print(f"Saved contacts batch {i//batch_size + 1}: {batch_saved}/{len(batch)} records inserted (Total saved: {saved_count}, Skipped: {skipped_count})")
                        
                    except Exception as batch_error:
                        print(f"Error saving contacts batch {i//batch_size + 1}: {batch_error}")
                        import traceback
                        traceback.print_exc()
                        self.db.rollback()
                
                print(f"Successfully saved {saved_count} Instagram records from Contacts sheet")
            
            whatsapp_rows = df[
                (df['Source'].str.contains('WhatsApp Messenger', case=False, na=False))
            ]
            
            print(f"  Found {len(whatsapp_rows)} rows with Source containing 'WhatsApp Messenger' or 'WhatsApp Messenger backup'")
            
            # Show Source distribution untuk debugging
            if len(whatsapp_rows) > 0:
                source_dist = whatsapp_rows['Source'].value_counts()
                print(f"  WhatsApp Source distribution: {dict(source_dist)}")
                
                # Breakdown per Source
                whatsapp_messenger_only = df[
                    df['Source'].str.contains('WhatsApp Messenger', case=False, na=False) &
                    ~df['Source'].str.contains('backup', case=False, na=False)
                ]
                whatsapp_backup_only = df[
                    df['Source'].str.contains('WhatsApp Messenger backup', case=False, na=False)
                ]
                print(f"  Breakdown:")
                print(f"    - WhatsApp Messenger (no backup): {len(whatsapp_messenger_only)} rows")
                print(f"    - WhatsApp Messenger backup: {len(whatsapp_backup_only)} rows")
            
            if len(whatsapp_rows) > 0:
                print(f"  Parsing {len(whatsapp_rows)} WhatsApp rows from Contacts sheet...")
                
                whatsapp_results = []
                
                # Count Type distribution untuk logging
                whatsapp_type_dist = whatsapp_rows['Type'].value_counts()
                print(f"  WhatsApp Type distribution: {dict(whatsapp_type_dist)}")
                
                # Count rows dengan Type=Account atau Account(merged)
                account_whatsapp = whatsapp_rows[
                    whatsapp_rows['Type'].str.contains('Account', case=False, na=False)
                ]
                print(f"  WhatsApp rows with Type containing 'Account': {len(account_whatsapp)}")
                
                # Show sample data untuk verification
                if len(account_whatsapp) > 0:
                    print(f"\n  Sample WhatsApp Account records (first 3):")
                    for idx, (row_idx, row) in enumerate(account_whatsapp.head(3).iterrows(), 1):
                        print(f"    Record {idx} (Row {row_idx}):")
                        print(f"      Source: {row.get('Source')}")
                        print(f"      Type: {row.get('Type')}")
                        contact = str(row.get('Contact', '') or '')[:100]
                        internet = str(row.get('Internet', '') or '')[:100]
                        phones = str(row.get('Phones & Emails', '') or '')[:100]
                        print(f"      Contact: {contact}")
                        print(f"      Internet: {internet}")
                        print(f"      Phones & Emails: {phones}")
                        print()
                
                # Parse semua rows dengan Source=WhatsApp Messenger atau WhatsApp Messenger backup
                skipped_by_type = 0
                skipped_by_source = 0
                
                for row_idx, row in whatsapp_rows.iterrows():
                    # Skip jika Source adalah header/metadata
                    source_field = self._clean(row.get("Source"))
                    if not source_field or self._is_header_or_metadata(source_field):
                        skipped_by_source += 1
                        if skipped_by_source <= 3:  # Log first 3 skipped rows
                            print(f"  ⚠️  Skipping WhatsApp row {row_idx} by Source filter: '{source_field}'")
                        continue
                    
                    source_clean = "WhatsApp"
                    
                    type_field = self._clean(row.get("Type"))
                    if not type_field:
                        skipped_by_type += 1
                        continue

                    type_lower = type_field.lower().strip()
                    
                    is_account_type = type_lower in ["account", "account(merged)", "account (merged)", "accounts"]
                    is_contact_type = type_lower in ["contact", "contact(merged)", "contact (merged)", "contacts"]
                    
                    if not (is_account_type or is_contact_type):
                        skipped_by_type += 1
                        if skipped_by_type <= 3:  # Log first 3 skipped rows
                            print(f"  ⚠️  Skipping WhatsApp row {row_idx} by Type filter: Type='{type_field}' (not Account/Contact)")
                        continue

                    contact_field = self._clean(row.get("Contact"))
                    internet_field = self._clean(row.get("Internet"))
                    addresses_field = self._clean(row.get("Addresses"))
                    phones_emails_field = self._clean(row.get("Phones & Emails"))
                    
                    print(f"\nProcessing WhatsApp Row {row_idx}:")
                    print(f"   Type: {type_field}")
                    print(f"   Source: {source_field}")
                    print(f"   Contact: {contact_field[:80] if contact_field else 'None'}")
                    print(f"   Internet: {internet_field[:80] if internet_field else 'None'}")
                    print(f"   Phones & Emails: {phones_emails_field[:80] if phones_emails_field else 'None'}")
                    
                    account_name = None
                    
                    full_name = self._extract_full_name_from_contact(contact_field)
                    if full_name and '@s.whatsapp.net' in full_name:

                        full_name = full_name.replace('@s.whatsapp.net', '').strip()
                        if full_name:
                            print(f"  ✓ Cleaned full_name (removed @s.whatsapp.net): {full_name}")
                    
                    location = self._extract_location(addresses_field)

                    phone_number = None
                    if internet_field:
                        phone_from_internet = self._extract_phone_number_from_text(internet_field)
                        if phone_from_internet:
                            phone_number = self._clean_whatsapp_suffix(phone_from_internet)
                            if phone_number:
                                print(f"  ✓ Extracted phone_number from Internet: {phone_number}")
                    
                    if not phone_number and phones_emails_field:
                        phone_from_phones = self._extract_phone_number_from_text(phones_emails_field)
                        if phone_from_phones:
                            phone_number = self._clean_whatsapp_suffix(phone_from_phones)
                            if phone_number:
                                print(f"  ✓ Extracted phone_number from Phones & Emails: {phone_number}")

                    # Extract whatsapp_id dari Internet field
                    whatsapp_id = self._extract_whatsapp_id_from_text(internet_field)
                    if whatsapp_id:
                        print(f"  ✓ Extracted whatsapp_id from Internet: {whatsapp_id}")
                    
                    # Jika whatsapp_id belum ada, coba dari Contact field jika berisi @s.whatsapp.net
                    # Contoh: "84927223310@s.whatsapp.net" -> "4927223310@s.whatsapp.net"
                    # Contoh: "6281275907774@s.whatsapp.net" -> "6281275907774@s.whatsapp.net"
                    if not whatsapp_id and contact_field:
                        contact_str = str(contact_field).strip()
                        if '@s.whatsapp.net' in contact_str:
                            # Extract nomor sebelum @s.whatsapp.net
                            number_part = contact_str.split('@s.whatsapp.net')[0].strip()
                            # Clean dari karakter non-digit di awal/akhir
                            number_part = re.sub(r'^[^\d]+', '', number_part)
                            number_part = re.sub(r'[^\d]+$', '', number_part)
                            
                            # Jika nomor dimulai dengan "8" dan panjang >= 11 digit, hapus digit pertama "8"
                            # Contoh: "84927223310" -> "4927223310"
                            if number_part and number_part.isdigit() and len(number_part) >= 11 and number_part.startswith('8'):
                                number_part = number_part[1:]  # Hapus digit pertama "8"
                            
                            if number_part and number_part.isdigit() and len(number_part) >= 8:
                                # Simpan dengan format @s.whatsapp.net
                                whatsapp_id = f"{number_part}@s.whatsapp.net"
                                print(f"  ✓ Extracted whatsapp_id from Contact field: {whatsapp_id}")
                    
                    # Jika whatsapp_id masih belum ada, coba dari Phones & Emails field
                    if not whatsapp_id and phones_emails_field:
                        whatsapp_id_from_phones = self._extract_whatsapp_id_from_text(phones_emails_field)
                        if whatsapp_id_from_phones:
                            whatsapp_id = whatsapp_id_from_phones
                            print(f"  ✓ Extracted whatsapp_id from Phones & Emails: {whatsapp_id}")
                    
                    # Jika whatsapp_id masih belum ada tapi phone_number ada, gunakan phone_number sebagai whatsapp_id
                    if not whatsapp_id and phone_number:
                        # Clean phone_number dari karakter non-digit
                        phone_clean = re.sub(r'[^\d]', '', str(phone_number))
                        # Skip phone_number yang hanya "0" atau terlalu pendek
                        if phone_clean and phone_clean.isdigit() and len(phone_clean) >= 8 and phone_clean != '0':
                            whatsapp_id = phone_clean
                            print(f"  ✓ Using phone_number as whatsapp_id: {whatsapp_id}")
                    
                    acc = {
                        "file_id": file_id,
                        "type": type_field,
                        "source": source_clean,  # Normalisasi menjadi "WhatsApp"
                        "phone_number": phone_number,  # dari Internet atau Phones & Emails
                        "full_name": full_name,  # dari Contact (bisa null)
                        "account_name": None,  # Untuk WhatsApp, account_name tidak diisi
                        "whatsapp_id": whatsapp_id,  # dari Internet (6281356150918 dari WhatsApp ID: 6281356150918@s.whatsapp.net)
                        "location": location,  # dari Addresses
                        "instagram_id": None,  # tidak diisi (hanya WhatsApp)
                        "telegram_id": None,  # tidak diisi (hanya WhatsApp)
                        "X_id": None,
                        "facebook_id": None,  # tidak diisi (hanya WhatsApp)
                        "tiktok_id": None,  # tidak diisi (hanya WhatsApp)
                        "sheet_name": sheet_name,
                    }
                    
                    # KONDISI: Ambil data jika ada whatsapp_id atau phone_number (account_name tidak diperlukan untuk WhatsApp)
                    if whatsapp_id or phone_number:
                        # Validasi data sebelum append
                        is_valid, error_msg = self._validate_social_media_data_new(acc)
                        if is_valid:
                            whatsapp_results.append(acc)
                        else:
                            print(f"⚠️  Skipping invalid WhatsApp record: {error_msg}")
                            print(f"   Details: whatsapp_id={whatsapp_id}, phone_number={phone_number}, type={type_field}")
                    else:
                        print(f"⚠️  Skipping WhatsApp row: No whatsapp_id or phone_number")
                        print(f"   Details: Type={type_field}, Source={source_field}")
                        print(f"   Contact: {contact_field[:80] if contact_field else 'None'}")
                        print(f"   Internet: {internet_field[:80] if internet_field else 'None'}")
                        print(f"   Phones & Emails: {phones_emails_field[:80] if phones_emails_field else 'None'}")
                        # Debug: tampilkan hasil ekstraksi
                        print(f"   Extracted - whatsapp_id: {whatsapp_id}, phone_number: {phone_number}")
                
                # Log summary dengan detail lengkap
                print(f"\n  WhatsApp parsing summary:")
                print(f"    - Total WhatsApp rows found: {len(whatsapp_rows)}")
                print(f"    - Skipped by Source (header/metadata): {skipped_by_source}")
                print(f"    - Skipped by Type (not Account): {skipped_by_type}")
                print(f"    - Valid Account rows processed: {len(whatsapp_results)} records")
                
                # Show sample of processed records
                if len(whatsapp_results) > 0:
                    print(f"\n  Sample WhatsApp records that will be saved (first 5):")
                    for idx, acc in enumerate(whatsapp_results[:5], 1):
                        print(f"    Record {idx}:")
                        print(f"      whatsapp_id: {acc.get('whatsapp_id')}")
                        print(f"      phone_number: {acc.get('phone_number')}")
                        print(f"      full_name: {acc.get('full_name')}")
                        print(f"      source: {acc.get('source')}")
                        print(f"      type: {acc.get('type')}")
                        print(f"      account_name: {acc.get('account_name')} (None for WhatsApp)")
                        print()
                    if len(whatsapp_results) > 5:
                        print(f"    ... and {len(whatsapp_results) - 5} more records")
                
                # Save WhatsApp results to database
                if whatsapp_results:
                    print(f"  Found {len(whatsapp_results)} valid WhatsApp records from Contacts sheet")
                    batch_size = 50
                    whatsapp_saved_count = 0
                    whatsapp_skipped_count = 0
                    
                    for i in range(0, len(whatsapp_results), batch_size):
                        batch = whatsapp_results[i:i + batch_size]
                        batch_saved = 0
                        
                        try:
                            for acc in batch:
                                # Check duplicate menggunakan struktur baru
                                if self._check_existing_social_media(acc):
                                    whatsapp_skipped_count += 1
                                    continue
                                
                                self.db.add(SocialMedia(**acc))
                                batch_saved += 1
                            
                            self.db.commit()
                            whatsapp_saved_count += batch_saved
                            print(f"Saved WhatsApp batch {i//batch_size + 1}: {batch_saved}/{len(batch)} records inserted (Total saved: {whatsapp_saved_count}, Skipped: {whatsapp_skipped_count})")
                            
                        except Exception as batch_error:
                            print(f"Error saving WhatsApp batch {i//batch_size + 1}: {batch_error}")
                            import traceback
                            traceback.print_exc()
                            self.db.rollback()
                    
                    print(f"Successfully saved {whatsapp_saved_count} WhatsApp records from Contacts sheet")
                    # Tambahkan WhatsApp results ke results utama
                    results.extend(whatsapp_results)
                else:
                    print(f"  No valid WhatsApp records found to save from Contacts sheet")
            
            # Parse TikTok data
            tiktok_rows = df[df['Source'].str.contains('TikTok', case=False, na=False)]
            print(f"  Found {len(tiktok_rows)} rows with Source containing 'TikTok'")
            
            tiktok_results = []
            if len(tiktok_rows) > 0:
                print(f"  Parsing {len(tiktok_rows)} TikTok rows from Contacts sheet...")
                
                for _, row in tiktok_rows.iterrows():
                    source_field = self._clean(row.get("Source"))
                    if not source_field or self._is_header_or_metadata(source_field):
                        continue
                    
                    type_field = self._clean(row.get("Type"))
                    type_lower = (type_field or "").lower().strip()
                    
                    # Filter untuk Type Account atau Account(merged) atau Contact/Contact(merged)
                    is_account_type = type_lower in ["account", "account(merged)", "account (merged)", "accounts"]
                    is_contact_type = type_lower in ["contact", "contact(merged)", "contact (merged)", "contacts"]
                    
                    if not (is_account_type or is_contact_type):
                        continue
                    
                    contact_field = self._clean(row.get("Contact"))
                    internet_field = self._clean(row.get("Internet"))
                    addresses_field = self._clean(row.get("Addresses"))
                    
                    # Extract data
                    full_name = self._extract_full_name_from_contact(contact_field)
                    account_name = self._extract_nickname(contact_field)
                    
                    # Jika account_name tidak ditemukan, coba dari Contact field langsung
                    if not account_name and contact_field:
                        contact_str = str(contact_field).strip()
                        if (contact_str and len(contact_str) > 1 and len(contact_str) < 50 and
                            '\n' not in contact_str and 'nickname:' not in contact_str.lower() and
                            not contact_str.isdigit() and '@' not in contact_str and 
                            '/' not in contact_str and '\\' not in contact_str):
                            account_name = contact_str
                    
                    # Extract TikTok ID dari Internet field
                    tiktok_id = self._extract_tiktok_id_from_text(internet_field) if internet_field else None
                    
                    # Extract location
                    location = self._extract_location(addresses_field)
                    
                    acc = {
                        "file_id": file_id,
                        "type": type_field,
                        "source": "TikTok",
                        "full_name": full_name,
                        "account_name": account_name,
                        "tiktok_id": tiktok_id,
                        "location": location,
                        "whatsapp_id": None,
                        "telegram_id": None,
                        "instagram_id": None,
                        "X_id": None,
                        "facebook_id": None,
                        "phone_number": None,
                        "sheet_name": sheet_name,
                    }
                    
                    if account_name or tiktok_id:
                        is_valid, error_msg = self._validate_social_media_data_new(acc)
                        if is_valid:
                            tiktok_results.append(acc)
                        else:
                            print(f"⚠️  Skipping invalid TikTok record: {error_msg}")
            
            # Save TikTok records
            if tiktok_results:
                print(f"  Found {len(tiktok_results)} valid TikTok records from Contacts sheet")
                batch_size = 50
                tiktok_saved_count = 0
                for i in range(0, len(tiktok_results), batch_size):
                    batch = tiktok_results[i:i+batch_size]
                    try:
                        for acc in batch:
                            self.db.add(SocialMedia(**acc))
                        self.db.commit()
                        tiktok_saved_count += len(batch)
                        print(f"  Saved TikTok batch {i//batch_size + 1}: {len(batch)}/{len(batch)} records inserted (Total saved: {tiktok_saved_count}, Skipped: 0)")
                    except Exception as batch_error:
                        print(f"  Error saving TikTok batch {i//batch_size + 1}: {batch_error}")
                        import traceback
                        traceback.print_exc()
                        self.db.rollback()
                
                print(f"Successfully saved {tiktok_saved_count} TikTok records from Contacts sheet")
                results.extend(tiktok_results)
            
            # Parse Telegram data
            telegram_rows = df[df['Source'].str.contains('Telegram', case=False, na=False)]
            print(f"  Found {len(telegram_rows)} rows with Source containing 'Telegram'")
            
            telegram_results = []
            if len(telegram_rows) > 0:
                print(f"  Parsing {len(telegram_rows)} Telegram rows from Contacts sheet...")
                
                for _, row in telegram_rows.iterrows():
                    source_field = self._clean(row.get("Source"))
                    if not source_field or self._is_header_or_metadata(source_field):
                        continue
                    
                    type_field = self._clean(row.get("Type"))
                    type_lower = (type_field or "").lower().strip()
                    
                    # Filter untuk Type Account atau Account(merged) atau Contact/Contact(merged) atau Group
                    is_account_type = type_lower in ["account", "account(merged)", "account (merged)", "accounts"]
                    is_contact_type = type_lower in ["contact", "contact(merged)", "contact (merged)", "contacts"]
                    is_group_type = type_lower in ["group", "group(merged)", "group (merged)", "groups"]
                    
                    # Process Group type rows for Telegram as they often contain valid account information
                    if not (is_account_type or is_contact_type or is_group_type):
                        if len(telegram_results) < 5:  # Log first 5 skipped by type
                            print(f"⚠️  Skipping Telegram row {row.name}: Type='{type_field}' (not Account/Contact/Group)")
                        continue
                    
                    contact_field = self._clean(row.get("Contact"))
                    internet_field = self._clean(row.get("Internet"))
                    addresses_field = self._clean(row.get("Addresses"))
                    
                    # Extract data
                    full_name = self._extract_full_name_from_contact(contact_field)
                    account_name = self._extract_nickname(contact_field)
                    
                    # Jika account_name tidak ditemukan, coba dari Contact field langsung
                    # Untuk Group type, prioritaskan Contact field sebagai account_name
                    if not account_name and contact_field:
                        contact_str = str(contact_field).strip()
                        # Jika multiline, ambil baris pertama saja (sebelum \n)
                        if '\n' in contact_str:
                            contact_str = contact_str.split('\n')[0].strip()
                        # Hapus prefix "Contact:" jika ada
                        if contact_str.lower().startswith('contact:'):
                            contact_str = contact_str.split(':', 1)[1].strip()
                        
                        # Untuk Group type, lebih longgar validasinya (boleh karakter unicode/emoji)
                        if is_group_type:
                            if (contact_str and len(contact_str) > 1 and len(contact_str) < 200 and
                                'nickname:' not in contact_str.lower() and
                                '@' not in contact_str and 
                                '/' not in contact_str and '\\' not in contact_str and
                                not contact_str.lower() in ["nan", "none", "null", "", "n/a", "undefined"]):
                                account_name = contact_str
                        else:
                            if (contact_str and len(contact_str) > 1 and len(contact_str) < 50 and
                                'nickname:' not in contact_str.lower() and
                                not contact_str.isdigit() and '@' not in contact_str and 
                                '/' not in contact_str and '\\' not in contact_str):
                                account_name = contact_str
                    
                    # Extract Telegram ID dari Internet field
                    telegram_id = self._extract_telegram_id_from_text(internet_field) if internet_field else None
                    
                    # Untuk Group type, coba extract Group ID dari Internet field jika telegram_id belum ada
                    if is_group_type and not telegram_id and internet_field:
                        group_id_match = re.search(r'Group\s+ID[:\s]+(\d+)', str(internet_field), re.IGNORECASE)
                        if group_id_match:
                            telegram_id = group_id_match.group(1).strip()
                            print(f"  Found Group ID as telegram_id: {telegram_id}")
                    
                    # Jika account_name tidak valid tapi ada telegram_id, gunakan telegram_id sebagai account_name
                    if account_name:
                        # Cek apakah account_name valid
                        if (self._is_header_or_metadata(account_name) or 
                            len(account_name) <= 1 or
                            account_name.lower() in ["nan", "none", "null", "", "n/a", "undefined"]):
                            # Account name tidak valid, gunakan telegram_id jika ada
                            if telegram_id:
                                account_name = f"Telegram_{telegram_id}"
                            else:
                                account_name = None
                    
                    # Jika Group type dan ada telegram_id tapi tidak ada account_name, gunakan Contact field atau telegram_id
                    if is_group_type and telegram_id and not account_name:
                        # Coba gunakan Contact field sebagai account_name jika valid
                        # Untuk Group, lebih longgar validasinya karena bisa berisi unicode/emoji
                        if contact_field:
                            contact_str = str(contact_field).strip()
                            # Untuk Group, hanya skip jika benar-benar invalid (header keywords, terlalu pendek, atau null)
                            is_valid_contact = (
                                contact_str and 
                                len(contact_str) > 1 and 
                                len(contact_str) < 200 and
                                contact_str.lower() not in ["nan", "none", "null", "", "n/a", "undefined"] and
                                # Skip hanya jika benar-benar header keyword (bukan unicode/emoji yang valid)
                                not (len(contact_str) <= 3 and contact_str.lower() in ["source", "type", "contact", "account", "group"])
                            )
                            if is_valid_contact:
                                account_name = contact_str
                            else:
                                account_name = f"Telegram_{telegram_id}"
                        else:
                            account_name = f"Telegram_{telegram_id}"
                    
                    # Extract location
                    location = self._extract_location(addresses_field)
                    
                    acc = {
                        "file_id": file_id,
                        "type": type_field,
                        "source": "Telegram",
                        "full_name": full_name,
                        "account_name": account_name,
                        "telegram_id": telegram_id,
                        "location": location,
                        "whatsapp_id": None,
                        "instagram_id": None,
                        "X_id": None,
                        "facebook_id": None,
                        "tiktok_id": None,
                        "phone_number": None,
                        "sheet_name": sheet_name,
                    }
                    
                    if account_name or telegram_id:
                        is_valid, error_msg = self._validate_social_media_data_new(acc)
                        if is_valid:
                            telegram_results.append(acc)
                        else:
                            print(f"⚠️  Skipping invalid Telegram record: {error_msg}")
                            print(f"   Details: Type={type_field}, account_name={account_name}, telegram_id={telegram_id}, Contact={contact_field[:80] if contact_field else 'None'}")
                    else:
                        # Log rows yang tidak punya account_name maupun telegram_id
                        print(f"⚠️  Skipping Telegram row: No account_name and no telegram_id")
                        print(f"   Details: Type={type_field}, Source={source_field}, Contact={contact_field[:80] if contact_field else 'None'}, Internet={internet_field[:80] if internet_field else 'None'}")
            
            # Save Telegram records
            if telegram_results:
                print(f"  Found {len(telegram_results)} valid Telegram records from Contacts sheet")
                batch_size = 50
                telegram_saved_count = 0
                for i in range(0, len(telegram_results), batch_size):
                    batch = telegram_results[i:i+batch_size]
                    try:
                        for acc in batch:
                            self.db.add(SocialMedia(**acc))
                        self.db.commit()
                        telegram_saved_count += len(batch)
                        print(f"  Saved Telegram batch {i//batch_size + 1}: {len(batch)}/{len(batch)} records inserted (Total saved: {telegram_saved_count}, Skipped: 0)")
                    except Exception as batch_error:
                        print(f"  Error saving Telegram batch {i//batch_size + 1}: {batch_error}")
                        import traceback
                        traceback.print_exc()
                        self.db.rollback()
                
                print(f"Successfully saved {telegram_saved_count} Telegram records from Contacts sheet")
                results.extend(telegram_results)
            
            # Parse X (Twitter) data
            # Mencari Source yang mengandung "Twitter" atau "X" (bisa sebagai kata terpisah)
            twitter_rows = df[df['Source'].str.contains('Twitter', case=False, na=False) | 
                             df['Source'].str.contains(r'\bX\b', case=False, na=False, regex=True)]
            print(f"  Found {len(twitter_rows)} rows with Source containing 'Twitter' or 'X'")
            
            twitter_results = []
            if len(twitter_rows) > 0:
                print(f"  Parsing {len(twitter_rows)} X (Twitter) rows from Contacts sheet...")
                
                for _, row in twitter_rows.iterrows():
                    source_field = self._clean(row.get("Source"))
                    if not source_field or self._is_header_or_metadata(source_field):
                        continue
                    
                    type_field = self._clean(row.get("Type"))
                    type_lower = (type_field or "").lower().strip()
                    
                    # Filter untuk Type Account atau Account(merged) atau Contact/Contact(merged) atau Group
                    is_account_type = type_lower in ["account", "account(merged)", "account (merged)", "accounts"]
                    is_contact_type = type_lower in ["contact", "contact(merged)", "contact (merged)", "contacts"]
                    is_group_type = type_lower in ["group", "group(merged)", "group (merged)", "groups"]
                    
                    # Process Group type rows for Twitter/X as they often contain valid account information (Nickname field)
                    if not (is_account_type or is_contact_type or is_group_type):
                        continue
                    
                    contact_field = self._clean(row.get("Contact"))
                    internet_field = self._clean(row.get("Internet"))
                    addresses_field = self._clean(row.get("Addresses"))
                    phones_emails_field = self._clean(row.get("Phones & Emails"))
                    
                    # Extract data
                    full_name = self._extract_full_name_from_contact(contact_field)
                    account_name = self._extract_nickname(contact_field)
                    
                    # Jika account_name tidak ditemukan, coba dari Contact field langsung
                    if not account_name and contact_field:
                        contact_str = str(contact_field).strip()
                        # Jika multiline, ambil baris pertama saja (sebelum \n)
                        if '\n' in contact_str:
                            contact_str = contact_str.split('\n')[0].strip()
                        # Hapus prefix "Contact:" jika ada
                        if contact_str.lower().startswith('contact:'):
                            contact_str = contact_str.split(':', 1)[1].strip()
                        # Hapus "@" di awal jika ada
                        if contact_str.startswith('@'):
                            contact_str = contact_str[1:].strip()
                        
                        if (contact_str and len(contact_str) > 1 and len(contact_str) < 50 and
                            'nickname:' not in contact_str.lower() and
                            not contact_str.isdigit() and '@' not in contact_str and 
                            '/' not in contact_str and '\\' not in contact_str):
                            account_name = contact_str
                    
                    # Extract X (Twitter) ID dari Internet field
                    x_id = self._extract_x_id_from_text(internet_field) if internet_field else None
                    
                    # Jika x_id tidak ditemukan di Internet, coba dari Phones & Emails field
                    if not x_id and phones_emails_field:
                        x_id = self._extract_x_id_from_text(phones_emails_field)
                    
                    # Jika Group type dan ada x_id tapi tidak ada account_name, gunakan x_id sebagai account_name
                    if is_group_type and x_id and not account_name:
                        account_name = f"X_{x_id}"
                    
                    # Extract location
                    location = self._extract_location(addresses_field)
                    
                    acc = {
                        "file_id": file_id,
                        "type": type_field,
                        "source": "X (Twitter)",
                        "full_name": full_name,
                        "account_name": account_name,
                        "X_id": x_id,
                        "location": location,
                        "whatsapp_id": None,
                        "telegram_id": None,
                        "instagram_id": None,
                        "facebook_id": None,
                        "tiktok_id": None,
                        "phone_number": None,
                        "sheet_name": sheet_name,
                    }
                    
                    if account_name or x_id:
                        is_valid, error_msg = self._validate_social_media_data_new(acc)
                        if is_valid:
                            twitter_results.append(acc)
                        else:
                            print(f"⚠️  Skipping invalid X (Twitter) record: {error_msg}")
            
            # Save X (Twitter) records
            if twitter_results:
                print(f"  Found {len(twitter_results)} valid X (Twitter) records from Contacts sheet")
                batch_size = 50
                twitter_saved_count = 0
                for i in range(0, len(twitter_results), batch_size):
                    batch = twitter_results[i:i+batch_size]
                    try:
                        for acc in batch:
                            self.db.add(SocialMedia(**acc))
                        self.db.commit()
                        twitter_saved_count += len(batch)
                        print(f"  Saved X (Twitter) batch {i//batch_size + 1}: {len(batch)}/{len(batch)} records inserted (Total saved: {twitter_saved_count}, Skipped: 0)")
                    except Exception as batch_error:
                        print(f"  Error saving X (Twitter) batch {i//batch_size + 1}: {batch_error}")
                        import traceback
                        traceback.print_exc()
                        self.db.rollback()
                
                print(f"Successfully saved {twitter_saved_count} X (Twitter) records from Contacts sheet")
                results.extend(twitter_results)
            
            # Parse Facebook data
            facebook_rows = df[df['Source'].str.contains('Facebook', case=False, na=False)]
            print(f"  Found {len(facebook_rows)} rows with Source containing 'Facebook'")
            
            facebook_results = []
            if len(facebook_rows) > 0:
                print(f"  Parsing {len(facebook_rows)} Facebook rows from Contacts sheet...")
                
                for _, row in facebook_rows.iterrows():
                    source_field = self._clean(row.get("Source"))
                    if not source_field or self._is_header_or_metadata(source_field):
                        continue
                    
                    type_field = self._clean(row.get("Type"))
                    type_lower = (type_field or "").lower().strip()
                    
                    # Filter untuk Type Account atau Account(merged) atau Contact/Contact(merged)
                    is_account_type = type_lower in ["account", "account(merged)", "account (merged)", "accounts"]
                    is_contact_type = type_lower in ["contact", "contact(merged)", "contact (merged)", "contacts"]
                    
                    if not (is_account_type or is_contact_type):
                        continue
                    
                    contact_field = self._clean(row.get("Contact"))
                    internet_field = self._clean(row.get("Internet"))
                    addresses_field = self._clean(row.get("Addresses"))
                    
                    # Extract data
                    full_name = self._extract_full_name_from_contact(contact_field)
                    account_name = self._extract_nickname(contact_field)
                    
                    # Jika account_name tidak ditemukan, coba dari Contact field langsung
                    if not account_name and contact_field:
                        contact_str = str(contact_field).strip()
                        if (contact_str and len(contact_str) > 1 and len(contact_str) < 50 and
                            '\n' not in contact_str and 'nickname:' not in contact_str.lower() and
                            not contact_str.isdigit() and '@' not in contact_str and 
                            '/' not in contact_str and '\\' not in contact_str):
                            account_name = contact_str
                    
                    # Extract Facebook ID dari Internet field
                    facebook_id = self._extract_facebook_id_from_text(internet_field) if internet_field else None
                    
                    # Extract location
                    location = self._extract_location(addresses_field)
                    
                    acc = {
                        "file_id": file_id,
                        "type": type_field,
                        "source": "Facebook",
                        "full_name": full_name,
                        "account_name": account_name,
                        "facebook_id": facebook_id,
                        "location": location,
                        "whatsapp_id": None,
                        "telegram_id": None,
                        "instagram_id": None,
                        "X_id": None,
                        "tiktok_id": None,
                        "phone_number": None,
                        "sheet_name": sheet_name,
                    }
                    
                    if account_name or facebook_id:
                        is_valid, error_msg = self._validate_social_media_data_new(acc)
                        if is_valid:
                            facebook_results.append(acc)
                        else:
                            print(f"⚠️  Skipping invalid Facebook record: {error_msg}")
            
            # Save Facebook records
            if facebook_results:
                print(f"  Found {len(facebook_results)} valid Facebook records from Contacts sheet")
                batch_size = 50
                facebook_saved_count = 0
                for i in range(0, len(facebook_results), batch_size):
                    batch = facebook_results[i:i+batch_size]
                    try:
                        for acc in batch:
                            self.db.add(SocialMedia(**acc))
                        self.db.commit()
                        facebook_saved_count += len(batch)
                        print(f"  Saved Facebook batch {i//batch_size + 1}: {len(batch)}/{len(batch)} records inserted (Total saved: {facebook_saved_count}, Skipped: 0)")
                    except Exception as batch_error:
                        print(f"  Error saving Facebook batch {i//batch_size + 1}: {batch_error}")
                        import traceback
                        traceback.print_exc()
                        self.db.rollback()
                
                print(f"Successfully saved {facebook_saved_count} Facebook records from Contacts sheet")
                results.extend(facebook_results)

        except Exception as e:
            print(f"Error parsing Contacts sheet: {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def _check_existing_social_media(self, acc: Dict[str, Any]) -> bool:
        file_id = acc.get("file_id")
        if not file_id:
            return False
        
        # Build query filter berdasarkan platform IDs yang ada
        query = self.db.query(SocialMedia).filter(SocialMedia.file_id == file_id)
        
        # Strategy: Cek duplicate berdasarkan platform_id spesifik jika ada
        # Jika ada platform_id (instagram_id, facebook_id, dll), cek duplicate hanya berdasarkan platform_id tersebut
        # Jika tidak ada platform_id tapi ada account_name, cek berdasarkan account_name
        
        platform_ids = {
            'instagram_id': acc.get("instagram_id"),
            'facebook_id': acc.get("facebook_id"),
            'whatsapp_id': acc.get("whatsapp_id"),
            'telegram_id': acc.get("telegram_id"),
            'X_id': acc.get("X_id"),
            'tiktok_id': acc.get("tiktok_id"),
        }
        
        # Cek apakah ada platform_id yang valid
        has_platform_id = any(v for v in platform_ids.values() if v)
        
        if has_platform_id:
            # Jika ada platform_id, cek duplicate berdasarkan platform_id spesifik
            # Platform ID adalah unique identifier, jadi cek apakah platform_id yang sama sudah ada
            from sqlalchemy import or_
            platform_filters = []
            platform_info = []
            
            if platform_ids['instagram_id']:
                platform_filters.append(SocialMedia.instagram_id == platform_ids['instagram_id'])
                platform_info.append(f"IG:{platform_ids['instagram_id']}")
            if platform_ids['facebook_id']:
                platform_filters.append(SocialMedia.facebook_id == platform_ids['facebook_id'])
                platform_info.append(f"FB:{platform_ids['facebook_id']}")
            if platform_ids['whatsapp_id']:
                platform_filters.append(SocialMedia.whatsapp_id == platform_ids['whatsapp_id'])
                platform_info.append(f"WA:{platform_ids['whatsapp_id']}")
            if platform_ids['telegram_id']:
                platform_filters.append(SocialMedia.telegram_id == platform_ids['telegram_id'])
                platform_info.append(f"TG:{platform_ids['telegram_id']}")
            if platform_ids['X_id']:
                platform_filters.append(SocialMedia.X_id == platform_ids['X_id'])
                platform_info.append(f"X:{platform_ids['X_id']}")
            if platform_ids['tiktok_id']:
                platform_filters.append(SocialMedia.tiktok_id == platform_ids['tiktok_id'])
                platform_info.append(f"TT:{platform_ids['tiktok_id']}")
            
            if platform_filters:
                existing = query.filter(or_(*platform_filters)).first()
                if existing:
                    # Log untuk debugging (hanya log beberapa pertama)
                    import sys
                    if not hasattr(self, '_dup_log_count'):
                        self._dup_log_count = 0
                    if self._dup_log_count < 5:
                        existing_info = []
                        if existing.telegram_id:
                            existing_info.append(f"TG:{existing.telegram_id}")
                        if existing.instagram_id:
                            existing_info.append(f"IG:{existing.instagram_id}")
                        if existing.whatsapp_id:
                            existing_info.append(f"WA:{existing.whatsapp_id}")
                        if existing.X_id:
                            existing_info.append(f"X:{existing.X_id}")
                        if existing.tiktok_id:
                            existing_info.append(f"TT:{existing.tiktok_id}")
                        existing_str = ', '.join(existing_info) if existing_info else 'N/A'
                        print(f"⚠️  Duplicate detected: Platform IDs: {', '.join(platform_info)}, Account: {acc.get('account_name', 'N/A')}")
                        print(f"    → Already exists in DB: {existing_str}, Account: {existing.account_name or 'N/A'}, Sheet: {existing.sheet_name or 'N/A'}")
                        self._dup_log_count += 1
                return existing is not None
        elif acc.get("account_name"):
            # Jika tidak ada platform_id tapi ada account_name, cek berdasarkan account_name
            existing = query.filter(SocialMedia.account_name == acc["account_name"]).first()
            if existing:
                import sys
                if not hasattr(self, '_dup_log_count'):
                    self._dup_log_count = 0
                if self._dup_log_count < 5:
                    print(f"⚠️  Duplicate detected: Account name: {acc['account_name']} (no platform ID)")
                    self._dup_log_count += 1
            return existing is not None
        
        # Jika tidak ada identifier sama sekali, tidak bisa check duplicate
        return False
    
    def _validate_social_media_data_new(self, acc: Dict[str, Any]) -> tuple[bool, str]:
        # file_id wajib ada
        if not acc.get("file_id"):
            return False, "file_id is required"
        
        # Minimal harus ada account_name atau salah satu platform ID
        has_data = (
            acc.get("account_name") or
            acc.get("instagram_id") or
            acc.get("facebook_id") or
            acc.get("whatsapp_id") or
            acc.get("telegram_id") or
            acc.get("X_id") or
            acc.get("tiktok_id")
        )
        
        if not has_data:
            return False, "account_name or at least one platform ID is required"
        
        # Clean invalid values
        invalid_values = ["nan", "none", "null", "", "n/a", "undefined"]
        
        # Validasi account_name
        if acc.get("account_name"):
            account_name_str = str(acc["account_name"]).strip()
            if account_name_str.lower() in invalid_values:
                return False, "account_name is invalid"
            
            # Untuk TikTok dan Telegram: jika ada platform_id yang valid, account_name dengan emoji/unicode dianggap valid
            # TikTok dan Telegram sering menggunakan emoji/unicode characters yang tidak mengandung a-zA-Z0-9
            is_tiktok_with_id = (
                acc.get("tiktok_id") and 
                (
                    (acc.get("source") and "tiktok" in str(acc.get("source", "")).lower()) or
                    (acc.get("sheet_name") and "tiktok" in str(acc.get("sheet_name", "")).lower())
                )
            )
            
            is_telegram_with_id = (
                acc.get("telegram_id") and 
                (
                    (acc.get("source") and "telegram" in str(acc.get("source", "")).lower()) or
                    (acc.get("sheet_name") and "telegram" in str(acc.get("sheet_name", "")).lower())
                )
            )
            
            if not is_tiktok_with_id and not is_telegram_with_id:
                # Validasi header/metadata hanya untuk non-TikTok/Telegram atau tanpa ID
                if self._is_header_or_metadata(account_name_str):
                    return False, f"account_name appears to be header/metadata: '{account_name_str}'"
        
        
        return True, ""

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
                                "phone_number": phone_number,
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
                
                if len(df) < 4:
                    print("  Instagram sheet too short, skipping")
                    return results
                
                # Parse account owner (row 4, index 4)
                # Format: Col[4]=Full name, Col[5]=User name, Col[9]=Followers
                if len(df) > 4:
                    owner_row = df.iloc[4]
                    owner_full_name = self._clean(owner_row.iloc[4]) if len(owner_row) > 4 else None
                    owner_user_name = self._clean(owner_row.iloc[5]) if len(owner_row) > 5 else None
                    owner_followers = self._clean(owner_row.iloc[9]) if len(owner_row) > 9 else None
                    
                    if owner_user_name and owner_user_name.lower() not in ['nan', 'accounts', 'source', 'categories']:
                        # Try to extract user_id from other columns
                        owner_user_id = None
                        # Check all columns for user ID (Instagram IDs are usually 9-15 digits)
                        for col_idx in range(len(owner_row)):
                            val = self._clean(owner_row.iloc[col_idx])
                            if val and val.isdigit() and 8 <= len(val) <= 15:  # Instagram IDs are usually 9-15 digits
                                # Additional check: skip very small numbers that might be flags/counts
                                if int(val) > 1000000:  # Skip numbers that are too small
                                    owner_user_id = val
                                    break
                        
                        if owner_user_id:
                            acc = {
                                "platform": "instagram",
                                "account_name": owner_user_name,
                                "account_id": owner_user_id,
                                "user_id": owner_user_id,
                                "full_name": owner_full_name,
                                "following": None,
                                "followers": self._to_int_safe(owner_followers),
                                "phone_number": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "Instagram",
                                "file_id": file_id,
                            }
                            results.append(acc)
                            print(f"  Found account owner: {owner_user_name}")
                
                if len(df) > 8:
                    following_count = 0
                    for idx in range(8, len(df)):
                        row = df.iloc[idx]
                        
                        # Skip empty rows
                        if len(row) < 6:
                            continue
                        
                        full_name = self._clean(row.iloc[4]) if len(row) > 4 else None
                        user_name = self._clean(row.iloc[5]) if len(row) > 5 else None
                        source_path = self._clean(row.iloc[2]) if len(row) > 2 else None
                        
                        # Skip header rows or invalid rows
                        if not user_name or user_name.lower() in ['nan', 'user name', 'accounts', 'source', 'categories', 'deleted', '']:
                            continue
                        
                        # Skip if source_path contains path-like structure (metadata)
                        if source_path and ('\\' in str(source_path) or '/' in str(source_path)):
                            # This might be a path, but continue if user_name is valid
                            pass
                        
                        # Extract user_id if available (check all columns for Instagram ID)
                        user_id = None
                        for col_idx in range(len(row)):
                            val = self._clean(row.iloc[col_idx])
                            if val and val.isdigit() and 8 <= len(val) <= 15:  # Instagram IDs are usually 9-15 digits
                                # Additional check: skip very small numbers that might be flags/counts
                                if int(val) > 1000000:  # Skip numbers that are too small
                                    user_id = val
                                    break
                        
                        # If no user_id found, skip this row
                        if not user_id:
                            continue
                        
                        if user_name and user_id:
                            acc = {
                                "platform": "instagram",
                                "account_name": user_name,
                                "account_id": user_id,
                                "user_id": user_id,
                                "full_name": full_name,
                                "following": None,
                                "followers": None,
                                "phone_number": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "Instagram",
                                "file_id": file_id,
                            }
                            results.append(acc)
                            following_count += 1
                    
                    if following_count > 0:
                        print(f"  Found {following_count} following accounts from Instagram sheet")
        
        except Exception as e:
            print(f"Error parsing Instagram dedicated sheet: {e}")
            import traceback
            traceback.print_exc()
        
        return results

    def _parse_oxygen_whatsapp_dedicated_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if 'WhatsApp Messenger ' in xls.sheet_names:
                print("Parsing WhatsApp Messenger dedicated sheet...")
                df = pd.read_excel(file_path, sheet_name='WhatsApp Messenger ', engine=engine, dtype=str)
                
                # Cari header row yang berisi "Full name", "User name", "User picture URL", "User ID", "Phone number"
                header_row_idx = None
                for idx in range(min(10, len(df))):  # Check first 10 rows
                    row_text = ' '.join([str(df.iloc[idx, col_idx]) if col_idx < len(df.columns) else '' 
                                        for col_idx in range(min(10, len(df.columns)))])
                    row_text_lower = row_text.lower()
                    
                    # Cari row yang berisi kolom header untuk account data
                    # Minimal harus ada "User name" atau "User ID" dan salah satu: "Full name", "Phone number", atau "User picture"
                    if ('user name' in row_text_lower or 'user id' in row_text_lower) and \
                       ('full name' in row_text_lower or 'phone number' in row_text_lower or 'phone' in row_text_lower or 'user picture' in row_text_lower):
                        header_row_idx = idx
                        break
                
                if header_row_idx is None:
                    print("Warning: Could not find header row for WhatsApp account data")
                    return results
                
                # Set columns dari header row
                df.columns = df.iloc[header_row_idx]
                df = df.drop(df.index[0:header_row_idx+1])
                df = df.reset_index(drop=True)
                
                # Cari kolom yang tepat
                col_mapping = {}
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'full name' in col_lower:
                        col_mapping['full_name'] = col
                    elif 'user name' in col_lower and 'user id' not in col_lower:
                        col_mapping['user_name'] = col
                    elif 'user picture' in col_lower or 'profile picture' in col_lower:
                        col_mapping['profile_picture_url'] = col
                    elif 'user id' in col_lower:
                        col_mapping['user_id'] = col
                    elif 'phone number' in col_lower or 'phone' in col_lower:
                        col_mapping['phone_number'] = col
                
                # Skip keywords yang menandakan row bukan account data
                skip_keywords = [
                    'source', 'status', 'received', 'delivered', 'seen', 'categories',
                    'direction', 'time stamp', 'timestamp', 'deleted', 'chats\\', 'calls\\',
                    'at the server', 'failed call', 'outgoing', 'incoming', 'message', 'call',
                    'riko suloyo\\chats', 'riko suloyo\\calls'
                ]
                
                for _, row in df.iterrows():
                    # Skip jika row kosong atau hanya whitespace
                    row_values = [str(row.get(col, '')).strip() for col in df.columns]
                    if not any(val and val.lower() not in ['nan', 'none', ''] for val in row_values):
                        continue
                    
                    # Skip jika row berisi skip keywords (header/metadata chat/call)
                    row_text = ' '.join(row_values).lower()
                    if any(keyword in row_text for keyword in skip_keywords):
                        continue
                    
                    # Skip jika row berisi path chat (misal: "Riko Suloyo\Chats\Private\...")
                    if '\\chats\\' in row_text or '\\calls\\' in row_text:
                        continue
                    
                    # Ambil data dari kolom yang tepat
                    full_name = None
                    user_name = None
                    profile_picture_url = None
                    user_id = None
                    phone_number = None
                    
                    if 'full_name' in col_mapping:
                        full_name = self._clean(row.get(col_mapping['full_name']))
                    if 'user_name' in col_mapping:
                        user_name = self._clean(row.get(col_mapping['user_name']))
                    if 'profile_picture_url' in col_mapping:
                        profile_picture_url = self._clean(row.get(col_mapping['profile_picture_url']))
                    if 'user_id' in col_mapping:
                        user_id = self._clean(row.get(col_mapping['user_id']))
                    if 'phone_number' in col_mapping:
                        phone_number = self._clean(row.get(col_mapping['phone_number']))
                    
                    # Jika kolom tidak ditemukan, coba ambil dari index (fallback)
                    # Order: Full name (1), User name (2), Phone number (3), User picture URL (4), User ID (5)
                    if not full_name and len(row) > 1:
                        full_name = self._clean(row.iloc[1] if isinstance(row, pd.Series) else row.get(1))
                    if not user_name and len(row) > 2:
                        user_name = self._clean(row.iloc[2] if isinstance(row, pd.Series) else row.get(2))
                    if not phone_number and len(row) > 3:
                        phone_number = self._clean(row.iloc[3] if isinstance(row, pd.Series) else row.get(3))
                    if not profile_picture_url and len(row) > 4:
                        profile_picture_url = self._clean(row.iloc[4] if isinstance(row, pd.Series) else row.get(4))
                    if not user_id and len(row) > 5:
                        user_id = self._clean(row.iloc[5] if isinstance(row, pd.Series) else row.get(5))
                    
                    # Validasi: harus ada user_id yang valid (numeric atau phone number format)
                    if not user_id:
                        continue
                    
                    # Validasi user_id bukan keyword invalid
                    user_id_str = str(user_id).strip().lower()
                    if user_id_str in skip_keywords or len(user_id_str) < 3:
                        continue
                    
                    # Prioritaskan phone_number dari kolom jika ada, jika tidak gunakan user_id
                    phone_to_use = phone_number if phone_number else user_id
                    
                    if not phone_to_use:
                        continue
                    
                    phone_to_use_str = str(phone_to_use).strip().lower()
                    
                    # Validasi: harus numeric atau phone number format
                    phone_clean = phone_to_use_str.replace('+', '').replace('-', '').replace('@s.whatsapp.net', '').replace('@', '')
                    
                    if not phone_clean.isdigit():
                        # Bisa jadi bukan account data valid
                        continue
                    
                    # Normalize phone number untuk account_id
                    account_id = self._normalize_phone(phone_to_use)
                    
                    # Validasi panjang phone number (minimal 10 digit)
                    account_id_clean = str(account_id).replace('+', '').replace('-', '')
                    if len(account_id_clean) < 10:
                        continue
                    
                    # Normalize phone_number field juga
                    if phone_number:
                        phone_number = self._normalize_phone(phone_number)
                    else:
                        # Jika tidak ada phone_number di kolom, gunakan account_id
                        phone_number = account_id
                    
                    # Jika tidak ada user_name, gunakan full_name atau account_id
                    if not user_name:
                        user_name = full_name if full_name else account_id
                    
                    acc = {
                        "platform": "whatsapp",
                        "account_name": user_name if user_name else (full_name if full_name else phone_number),
                        "account_id": account_id,  # Phone number sebagai identifier unik
                        "user_id": user_id if user_id and user_id != account_id else account_id,  # User ID atau phone number
                        "full_name": full_name,  # Required field untuk WhatsApp
                        "following": None,  # Tidak ada di WhatsApp
                        "followers": None,  # Tidak ada di WhatsApp
                        "phone_number": phone_number,  # Phone number yang sudah dinormalisasi (Required untuk WhatsApp)
                        "source_tool": "Oxygen",
                        "sheet_name": "WhatsApp Messenger",
                        "file_id": file_id,
                    }
                    results.append(acc)
        
        except Exception as e:
            print(f"Error parsing WhatsApp Messenger dedicated sheet: {e}")
            import traceback
            traceback.print_exc()
        
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
                                "phone_number": phone_number,
                                "source_tool": "Oxygen",
                                "sheet_name": "Telegram",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing Telegram dedicated sheet: {e}")
        
        return results

    def _clean_whatsapp_suffix(self, value: str) -> str:
        if not value:
            return value
        value_str = str(value)
        return value_str.replace('@s.whatsapp.net', '').strip()

    def _parse_oxygen_twitter_dedicated_sheet(self, file_path: str, xls: pd.ExcelFile, file_id: int, engine: str) -> List[Dict[str, Any]]:
        results = []
        
        try:
            if 'X (Twitter) ' in xls.sheet_names:
                print("Parsing X (Twitter) dedicated sheet...")
                df = pd.read_excel(file_path, sheet_name='X (Twitter) ', engine=engine, dtype=str)
                
                # Normalize column names
                df.columns = [str(col).strip() for col in df.columns]
                
                # Handle case where first row might be headers
                if any('Unnamed' in str(col) for col in df.columns):
                    # Try to use first row as column names
                    potential_header_row = None
                    for idx in range(min(3, len(df))):
                        row_values = [str(val).strip().lower() for val in df.iloc[idx].values]
                        if any(col in row_values for col in ['uid', 'username', 'full name']):
                            potential_header_row = idx
                            break
                    
                    if potential_header_row is not None:
                        df.columns = df.iloc[potential_header_row]
                        df = df.drop(df.index[:potential_header_row + 1])
                        df = df.reset_index(drop=True)
                        df.columns = [str(col).strip() for col in df.columns]
                
                # Cek apakah kolom yang diperlukan ada
                required_columns = ['UID', 'Username', 'Full name', 'Followers', 'Following']
                column_mapping = {}
                
                for req_col in required_columns:
                    # Cari kolom yang cocok (case insensitive)
                    for col in df.columns:
                        if req_col.lower() == str(col).lower().strip():
                            column_mapping[req_col] = col
                            break
                        # Juga cek variasi nama
                        if req_col.lower() in ['uid'] and 'uid' in str(col).lower():
                            column_mapping[req_col] = col
                            break
                        elif req_col.lower() in ['username'] and 'username' in str(col).lower():
                            column_mapping[req_col] = col
                            break
                        elif req_col.lower() in ['full name'] and ('full name' in str(col).lower() or 'fullname' in str(col).lower()):
                            column_mapping[req_col] = col
                            break
                        elif req_col.lower() in ['followers'] and 'followers' in str(col).lower():
                            column_mapping[req_col] = col
                            break
                        elif req_col.lower() in ['following'] and 'following' in str(col).lower():
                            column_mapping[req_col] = col
                            break
                
                # Cek kolom yang harus di-skip
                skip_columns = ['category', 'source', 'delete']
                skip_column_names = []
                for skip_col in skip_columns:
                    for col in df.columns:
                        if skip_col.lower() == str(col).lower().strip():
                            skip_column_names.append(col)
                
                print(f"  Found columns: UID={column_mapping.get('UID')}, Username={column_mapping.get('Username')}, "
                      f"Full name={column_mapping.get('Full name')}, Followers={column_mapping.get('Followers')}, "
                      f"Following={column_mapping.get('Following')}")
                if skip_column_names:
                    print(f"  Skip columns detected: {skip_column_names}")
                
                # Parse data
                for _, row in df.iterrows():
                    # Skip row jika ada nilai di kolom category, source, atau delete
                    should_skip = False
                    for skip_col in skip_column_names:
                        skip_value = self._clean(row.get(skip_col, ''))
                        if skip_value and str(skip_value).strip().lower() not in ['', 'nan', 'none', 'null']:
                            should_skip = True
                            break
                    
                    if should_skip:
                        continue
                    
                    # Ambil data hanya dari kolom yang diperlukan
                    user_id_col = column_mapping.get('UID')
                    username_col = column_mapping.get('Username')
                    full_name_col = column_mapping.get('Full name')
                    followers_col = column_mapping.get('Followers')
                    following_col = column_mapping.get('Following')
                    
                    user_id = self._clean(row.get(user_id_col, '')) if user_id_col else None
                    username = self._clean(row.get(username_col, '')) if username_col else None
                    full_name = self._clean(row.get(full_name_col, '')) if full_name_col else None
                    followers_count = self._clean(row.get(followers_col, '')) if followers_col else None
                    following_count = self._clean(row.get(following_col, '')) if following_col else None
                    
                    # Clean data dari @s.whatsapp.net jika ada
                    if user_id:
                        user_id = self._clean_whatsapp_suffix(user_id)
                    if username:
                        username = self._clean_whatsapp_suffix(username)
                    if full_name:
                        full_name = self._clean_whatsapp_suffix(full_name)
                    
                    # Hanya insert jika ada minimal UID atau Username
                    if user_id or username:
                        account_name = username or user_id
                        
                        # Skip jika account_name adalah header/metadata
                        if account_name and self._is_header_or_metadata(account_name):
                            continue
                        
                            acc = {
                                "platform": "x",
                            "account_name": account_name,
                            "account_id": user_id or username,
                                "user_id": user_id,
                                "full_name": full_name,
                                "following": self._to_int_safe(following_count),
                                "followers": self._to_int_safe(followers_count),
                                "phone_number": None,
                                "source_tool": "Oxygen",
                                "sheet_name": "X (Twitter)",
                                "file_id": file_id,
                            }
                            results.append(acc)
        
        except Exception as e:
            print(f"Error parsing X (Twitter) dedicated sheet: {e}")
            import traceback
            traceback.print_exc()
        
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
                                            "phone_number": None,
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
        if text.lower() in ["", "nan", "none", "null", "n/a", "none"]:
            return None
        return text
    
    def _is_header_or_metadata(self, value: str) -> bool:
        """Cek apakah value adalah header kolom atau metadata sistem"""
        if not value:
            return False
        
        value_str = str(value).strip()
        value_lower = value_str.lower()
        
        # Header kolom yang umum ditemukan di Excel (exact match)
        exact_header_keywords = [
            "source", "file name", "file size", "source file", "source table",
            "source file size", "source table", "path", "/", 
            "user picture url", "thumbnail url", "tweet url", "remote party name"
        ]
        
        if value_lower in exact_header_keywords:
            return True
        
        # Cek apakah value adalah ukuran file (berisi angka + KB/MB/GB)
        if re.search(r'^\d+[,\s\.]?\d*\s*(kb|mb|gb)$', value_lower):
            return True
        
        # Cek apakah value terlalu pendek (kecuali untuk username yang sangat pendek yang valid)
        if len(value_str) <= 1:
            # Single character bisa valid untuk beberapa platform, tapi "/" jelas tidak valid
            if value_str == "/":
                return True
            # Skip single character yang bukan alphanumeric
            if not value_str.isalnum():
                return True
        
        # Cek apakah value adalah hanya simbol tanpa karakter valid
        if not re.search(r'[a-zA-Z0-9]', value_str):
            return True
        
        return False
    
    def _is_system_path(self, value: str) -> bool:
        """Cek apakah value terlihat seperti system path yang bukan social media account"""
        if not value:
            return False
        
        value_str = str(value).strip()
        
        # Cek apakah mengandung backslash (Windows path)
        if '\\' in value_str:
            path_parts = value_str.split('\\')
            if len(path_parts) >= 2:
                first_part = path_parts[0].lower()
                # Cek bagian pertama yang umum untuk system paths
                if first_part in ["cache", "cookies", "source", "users"]:
                    # Cek apakah bagian berikutnya juga terlihat seperti path sistem
                    if any(part.lower() in ["links", "cache", "cookies"] for part in path_parts[1:]):
                        return True
                    # Jika account_name adalah path tapi account_id juga invalid, kemungkinan besar system path
                    return False  # Akan dicek di validasi bersama dengan account_id
        
        # Cek pattern seperti "Cache\Links" atau "Source" yang jelas bukan account
        suspicious_patterns = [
            r'^cache\\links?$',
            r'^cookies$',
            r'^source$',
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, value_str.lower()):
                return True
        
        return False
    
    def _convert_old_to_new_structure(self, acc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert struktur lama ke struktur baru"""
        if "platform" not in acc:
            # Sudah struktur baru
            return acc
        
        new_acc = {
            "file_id": acc.get("file_id"),
            "type": acc.get("type"),
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
            "location": acc.get("location"),
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
    
    def _validate_social_media_data(self, acc: Dict[str, Any]) -> tuple[bool, str]:
        if "platform" in acc:
            acc = self._convert_old_to_new_structure(acc)
    
        return self._validate_social_media_data_new(acc)

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
        
        
        phones_found = []
        
        mobile_pattern = r'mobile[:\s]+(\+?\d+)'
        mobile_matches = re.findall(mobile_pattern, phones_emails_field.lower())
        for match in mobile_matches:
            phone_clean = match.replace('+', '').replace('-', '').replace(' ', '')
            if phone_clean and phone_clean.isdigit() and len(phone_clean) >= 3:  # Minimal 3 digit
                phones_found.append((len(phone_clean), match))  # Simpan dengan length untuk sorting
        
        if not phones_found:
            phone_number_pattern = r'phone\s+number[:\s]+(\+?\d+)'
            phone_matches = re.findall(phone_number_pattern, phones_emails_field.lower())
            for match in phone_matches:
                phone_clean = match.replace('+', '').replace('-', '').replace(' ', '')
                if phone_clean and phone_clean.isdigit() and len(phone_clean) >= 3:
                    phones_found.append((len(phone_clean), match))
                    break
        
        if not phones_found:
            direct_mobile_pattern = r'mobile[:\s]+(\+?\d{3,15})'
            match = re.search(direct_mobile_pattern, phones_emails_field.lower())
            if match:
                phone_clean = match.group(1).replace('+', '').replace('-', '').replace(' ', '')
                if phone_clean.isdigit():
                    phones_found.append((len(phone_clean), match.group(1)))
        
        if not phones_found:
            tel_pattern = r'(?:tel|phone)[:\s]+(\+?\d{10,15})'
            match = re.search(tel_pattern, phones_emails_field.lower())
            if match:
                phone_clean = match.group(1).replace('+', '').replace('-', '').replace(' ', '')
                if phone_clean.isdigit():
                    phones_found.append((len(phone_clean), match.group(1)))
        
        phones_found.sort(key=lambda x: x[0], reverse=True)
        
        for length, phone in phones_found:
            phone_normalized = self._normalize_phone(phone)
            if phone_normalized:
                phone_digits = phone_normalized.replace('+', '').replace('-', '').replace(' ', '')
                if len(phone_digits) >= 10:
                    return phone_normalized
        
        if phones_found:
            length, phone = phones_found[0]
            phone_normalized = self._normalize_phone(phone)
            if phone_normalized:
                phone_digits = phone_normalized.replace('+', '').replace('-', '').replace(' ', '')
                if len(phone_digits) >= 3:
                    return phone_normalized
        return None
