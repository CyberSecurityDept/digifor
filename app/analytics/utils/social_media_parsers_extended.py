import re
import pandas as pd  # type: ignore
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session  # type: ignore
from app.analytics.device_management.models import SocialMedia, ChatMessage

class SocialMediaParsersExtended:
    """Extended parsers untuk Axiom dan Cellebrite social media data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _clean(self, text: Any) -> Optional[str]:
        """Clean dan normalize text value"""
        if text is None or pd.isna(text):
            return None
        text = str(text).strip()
        if text.lower() in ["", "nan", "none", "null", "n/a", "none"]:
            return None
        return text
    
    def _check_existing_social_media(self, acc: Dict[str, Any]) -> bool:
        """Check apakah social media record sudah ada berdasarkan struktur baru"""
        file_id = acc.get("file_id")
        if not file_id:
            return False
        
        # Build query filter berdasarkan platform IDs yang ada
        query = self.db.query(SocialMedia).filter(SocialMedia.file_id == file_id)
        
        # Cek berdasarkan platform ID yang ada
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
        
        # Jika ada account_name, juga cek berdasarkan account_name
        if acc.get("account_name"):
            filters.append(SocialMedia.account_name == acc["account_name"])
        
        # Jika tidak ada filter, return False (tidak bisa check duplicate)
        if not filters:
            return False
        
        # Combine filters dengan OR - jika ada salah satu yang match, berarti duplicate
        from sqlalchemy import or_
        existing = query.filter(or_(*filters)).first()
        
        return existing is not None
    
    def _validate_social_media_data(self, acc: Dict[str, Any]) -> tuple[bool, str]:
        """Validasi data social media sebelum insert. Returns (is_valid, error_message)"""
        # Cek apakah menggunakan struktur lama, convert ke baru
        if "platform" in acc:
            acc = self._convert_old_to_new_structure(acc)
        
        # Gunakan validasi struktur baru
        return self._validate_social_media_data_new(acc)
    
    def _validate_social_media_data_new(self, acc: Dict[str, Any]) -> tuple[bool, str]:
        """Validasi data social media dengan struktur baru"""
        if not acc.get("file_id"):
            return False, "Missing file_id"
        
        # Cek apakah ada minimal satu platform ID atau account_name
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
                # Generate unique key berdasarkan struktur (lama atau baru)
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
            # Check if file is Excel format
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in ['.xlsx', '.xls']:
                return 0
            
            # Determine engine based on extension
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
                    # Skip sheets that can't be read
                    continue
            
            return total_count
            
        except Exception as e:
            # Silently return 0 for non-Excel files or parsing errors
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
            
            print(f"Successfully saved {saved_count} unique Cellebrite social media accounts to database")
            if skipped_count > 0:
                print(f"  ({skipped_count} records skipped - already exist)")
            if invalid_count > 0:
                print(f"  ({invalid_count} records skipped - invalid data)")
            
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
                                "source_tool": "Cellebrite",
                                "sheet_name": sheet_name,
                                "file_id": file_id
                            }
                            results.append(acc)
                    
                    # Check for WhatsApp mentions
                    elif 'whatsapp' in col_value_lower:
                        # Extract WhatsApp number
                        if '@s.whatsapp.net' in col_value:
                            whatsapp_match = re.search(r'(\+?[0-9]{10,15})@s\.whatsapp\.net', col_value)
                            if whatsapp_match:
                                phone_number = whatsapp_match.group(1)
                                col_value = col_value.replace('@s.whatsapp.net', '')
                        acc = {
                            "platform": "whatsapp",
                            "account_name": phone_number,
                            "account_id": phone_number,
                            "user_id": phone_number,
                            "full_name": phone_number,
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
                        entries = entries.replace('@s.whatsapp.net', '')
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
                                    line = line.replace('@s.whatsapp.net', '')
                                    acc = {
                                        "platform": "whatsapp",
                                        "account_name": phone_number,
                                        "account_id": phone_number,
                                        "user_id": phone_number,
                                        "full_name": phone_number,
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
                
                user_id_value = self._clean(row.get('User ID'))
                user_name_value = self._clean(row.get('User Name'))
                
                # account_id seharusnya menggunakan User ID (numeric) jika tersedia, bukan username
                # username bisa berubah, tapi User ID tetap unik
                account_id_value = user_id_value if user_id_value else user_name_value
                
                acc = {
                    "platform": "instagram",
                    "account_name": user_name_value,  # Username yang bisa berubah
                    "account_id": account_id_value,  # User ID (numeric) sebagai identifier unik
                    "user_id": user_id_value,  # User ID (numeric)
                    "full_name": self._clean(row.get('Name')),
                    "following": following_count,
                    "followers": followers_count,
                    "phone_number": self._clean(row.get('Phone Number')),
                    "source_tool": "Axiom",
                    "sheet_name": "Instagram Profiles",
                    "file_id": file_id,
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
                
                user_id_value = self._clean(row.get('ID'))
                user_name_value = self._clean(row.get('User Name'))
                
                # account_id seharusnya menggunakan ID (numeric) jika tersedia, bukan username
                account_id_value = user_id_value if user_id_value else user_name_value
                
                acc = {
                    "platform": "instagram",
                    "account_name": user_name_value,  # Username
                    "account_id": account_id_value,  # ID (numeric) sebagai identifier unik
                    "user_id": user_id_value,  # ID (numeric)
                    "full_name": self._clean(row.get('Full Name')),
                    "following": following_count,
                    "followers": None,
                    "phone_number": None,
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
                
                user_id_value = self._clean(row.get('ID'))
                user_name_value = self._clean(row.get('User Name'))
                
                # account_id seharusnya menggunakan ID (numeric) jika tersedia, bukan username
                account_id_value = user_id_value if user_id_value else user_name_value
                
                acc = {
                    "platform": "instagram",
                    "account_name": user_name_value,  # Username
                    "account_id": account_id_value,  # ID (numeric) sebagai identifier unik
                    "user_id": user_id_value,  # ID (numeric)
                    "full_name": self._clean(row.get('Full Name')),
                    "following": None,
                    "followers": None,
                    "phone_number": None,
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
                    "phone_number": self._clean(row.get('Phone Number(s)')),
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
                    
                user_id_value = self._clean(row.get('User ID'))
                screen_name_value = self._clean(row.get('Screen Name'))
                user_name_value = self._clean(row.get('User Name')) or screen_name_value
                
                # account_id seharusnya menggunakan User ID (numeric) jika tersedia, bukan username
                # untuk Twitter/X, Screen Name bisa berubah, tapi User ID tetap unik
                account_id_value = user_id_value if user_id_value else user_name_value
                    
                acc = {
                    "platform": "x",
                    "account_name": user_name_value or screen_name_value,  # Username/Screen Name
                    "account_id": account_id_value,  # User ID (numeric) sebagai identifier unik
                    "user_id": user_id_value,  # User ID (numeric)
                    "full_name": self._clean(row.get('Full Name')),
                    "following": self._safe_int(row.get('Following')),
                    "followers": self._safe_int(row.get('Followers')),
                    "source_tool": "Axiom",
                    "sheet_name": "Twitter Users",
                    "file_id": file_id,
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
                    "platform": "telegram",
                    "account_name": account_name_value,
                    "account_id": account_id_final,  # Account ID atau User ID sebagai identifier unik
                    "user_id": user_id_value,  # User ID (numeric)
                    "full_name": full_name,
                    "phone_number": self._clean(row.get('Phone Number')),
                    "source_tool": "Axiom",
                    "sheet_name": "Telegram Accounts",
                    "file_id": file_id,
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
                    "phone_number": self._clean(row.get('Phone Number')),
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
