import re
import pandas as pd  # type: ignore
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session  # type: ignore
from app.analytics.device_management.models import SocialMedia
from .file_validator import file_validator

# Suppress all OLE2 warnings globally
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', message='.*OLE2 inconsistency.*')
warnings.filterwarnings('ignore', message='.*file size.*not.*multiple of sector size.*')
warnings.filterwarnings('ignore', message='.*SSCS size is 0 but SSAT size is non-zero.*')
warnings.filterwarnings('ignore', message='.*WARNING \*\*\*.*')

SOCIAL_MEDIA_PLATFORMS = ["instagram", "facebook", "whatsapp", "telegram", "x", "tiktok"]

class SocialMediaParser:
    """
    Parser untuk mengekstrak data sosial media dari Oxygen sheet 'Contacts'.
    """

    def __init__(self, db: Session):
        self.db = db

    def parse_oxygen_social_media(self, file_path: str, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        results = []

        # Validasi file terlebih dahulu
        validation = file_validator.validate_excel_file(Path(file_path))
        file_validator.print_validation_summary(validation)
        
        if not validation["is_valid"]:
            print(f"File validation failed: {validation['errors']}")
            if validation["warnings"]:
                print(f"Warnings: {validation['warnings']}")

        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
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

                # Determine engine based on file extension
                file_path_obj = Path(file_path)
                file_extension = file_path_obj.suffix.lower()
                if file_extension == '.xls':
                    engine = "xlrd"
                else:
                    engine = "openpyxl"
                
                df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine=engine)

            for _, row in df.iterrows():
                # --- Filter hanya contact / contact (merged) ---
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

                # --- ambil semua platform yang valid ---
                detected_platforms = self._extract_multiple_platforms(source_field)
                if not detected_platforms:
                    continue

                # --- ambil nama kontak ---
                account_name = self._extract_name(contact_field)

                # --- ekstrak data tambahan ---
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

                # --- iterasi tiap platform ---
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
                        "device_id": device_id,
                        "file_id": file_id,
                    }
                    results.append(acc)

                    # --- Cegah duplikat ---
                    existing = (
                        self.db.query(SocialMedia)
                        .filter(
                            SocialMedia.platform == platform,
                            SocialMedia.account_id == account_id,
                            SocialMedia.device_id == device_id,
                        )
                        .first()
                    )
                    if not existing:
                        self.db.add(SocialMedia(**acc))

            self.db.commit()

        except Exception as e:
            print(f"Error parsing social media Oxygen: {e}")

        return results


    # -----------------------------
    # 🔧 Helper Functions
    # -----------------------------

    def _extract_multiple_platforms(self, text: str) -> List[str]:
        if not text:
            return []

        text_lower = text.lower()

        # Hapus backup agar tidak dihitung
        text_lower = text_lower.replace("whatsapp messenger backup", "")

        found = []
        for platform in SOCIAL_MEDIA_PLATFORMS:
            if platform in text_lower:
                found.append(platform)
        if "twitter" in text_lower:
            found.append("x")

        return list(set(found))  # hilangkan duplikat

    def _extract_name(self, contact_field: Optional[str]) -> Optional[str]:
        """Ambil nama dari field Contact."""
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
        """Ambil account ID dari field Internet / Phones & Emails."""
        if not text:
            return None

        # Pola umum (boleh lebih dari satu ID dalam satu teks)
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

        # ambil hasil terakhir (jika ada beberapa)
        match = matches[-1]
        if isinstance(match, tuple):
            value = match[-1].strip()
        else:
            value = match.strip()

        if platform == "whatsapp":
            return self._normalize_phone(value)
        return value

    def _normalize_phone(self, phone: str) -> str:
        """Normalisasi nomor telepon WhatsApp jadi format +62."""
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
        """Ekstrak jumlah followers dari berbagai field."""
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
                    if content and len(content) > 3:  # Minimal 3 karakter
                        return content
        
        return None

    def _extract_friends_count(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[int]:
        """Ekstrak jumlah friends dari berbagai field."""
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
        """Ekstrak jumlah statuses/posts dari berbagai field."""
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
        """Ekstrak nomor telepon dari field Phones & Emails."""
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
        """Ekstrak email dari field Phones & Emails."""
        if not phones_emails_field:
            return None
            
        # Pattern untuk email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, phones_emails_field)
        if match:
            return match.group(0)
        
        return None

    def _extract_biography(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[str]:
        """Ekstrak biography/description dari berbagai field."""
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
        """Ekstrak profile picture URL dari field Internet."""
        if not internet_field:
            return None
            
        # Pattern untuk URL
        url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif)'
        match = re.search(url_pattern, internet_field)
        if match:
            return match.group(0)
        
        return None

    def _extract_is_private(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[bool]:
        """Ekstrak status private account."""
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
        """Ekstrak status local user."""
        fields = [contact_field, internet_field, phones_emails_field]
        
        for field in fields:
            if not field:
                continue
                
            if 'local user' in field.lower():
                return True
        
        return None

    def _extract_last_message(self, contact_field: Optional[str], internet_field: Optional[str], phones_emails_field: Optional[str]) -> Optional[str]:
        """Ekstrak last message content."""
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
        """Ekstrak other information."""
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
        """Ekstrak numeric user ID."""
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
        """Ekstrak full name dari field Contact."""
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

    def parse_axiom_social_media(self, file_path: str, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            # Baca file dengan engine openpyxl untuk .xlsx
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            # Parse setiap sheet khusus platform
            for sheet_name in xls.sheet_names:
                if 'Instagram Profiles' in sheet_name:
                    results.extend(self._parse_axiom_instagram_profiles(file_path, sheet_name, device_id, file_id))
                elif 'Twitter Users' in sheet_name:
                    results.extend(self._parse_axiom_twitter_users(file_path, sheet_name, device_id, file_id))
                elif 'Telegram Accounts' in sheet_name:
                    results.extend(self._parse_axiom_telegram_accounts(file_path, sheet_name, device_id, file_id))
                elif 'TikTok Contacts' in sheet_name:
                    results.extend(self._parse_axiom_tiktok_contacts(file_path, sheet_name, device_id, file_id))
            
            # Simpan ke database
            for acc in results:
                existing = (
                    self.db.query(SocialMedia)
                    .filter(
                        SocialMedia.platform == acc["platform"],
                        SocialMedia.account_id == acc["account_id"],
                        SocialMedia.device_id == device_id,
                    )
                    .first()
                )
                if not existing:
                    self.db.add(SocialMedia(**acc))
            
            self.db.commit()
            
        except Exception as e:
            print(f"Error parsing Axiom social media: {e}")
        
        return results

    def _parse_axiom_instagram_profiles(self, file_path: str, sheet_name: str, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        """Parse Instagram Profiles sheet dari Axiom."""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User Name')):
                    continue
                    
                acc = {
                    "platform": "instagram",
                    "account_name": self._clean(row.get('User Name')),
                    "account_id": self._clean(row.get('User Name')),  # Username sebagai account_id
                    "user_id": self._clean(row.get('User ID')),
                    "full_name": self._clean(row.get('Name')),
                    "following": self._safe_int(row.get('Following')),
                    "followers": self._safe_int(row.get('Is Followed By')),
                    "biography": self._clean(row.get('Biography')),
                    "profile_picture_url": self._clean(row.get('Profile Picture URL')),
                    "is_private": self._safe_bool(row.get('Is Private')),
                    "is_local_user": self._safe_bool(row.get('Local User')),
                    "email": self._clean(row.get('Email')),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "source_tool": "Axiom",
                    "device_id": device_id,
                    "file_id": file_id,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Instagram Profiles: {e}")
        
        return results

    def _parse_axiom_twitter_users(self, file_path: str, sheet_name: str, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        """Parse Twitter Users sheet dari Axiom."""
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
                    "device_id": device_id,
                    "file_id": file_id,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Twitter Users: {e}")
        
        return results

    def _parse_axiom_telegram_accounts(self, file_path: str, sheet_name: str, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        """Parse Telegram Accounts sheet dari Axiom."""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('User ID')):
                    continue
                    
                acc = {
                    "platform": "telegram",
                    "account_name": self._clean(row.get('User Name')),
                    "account_id": self._clean(row.get('Account ID')),
                    "user_id": self._clean(row.get('User ID')),
                    "full_name": f"{self._clean(row.get('First Name', ''))} {self._clean(row.get('Last Name', ''))}".strip(),
                    "phone_number": self._clean(row.get('Phone Number')),
                    "is_local_user": self._safe_bool(row.get('Active Account')),
                    "source_tool": "Axiom",
                    "device_id": device_id,
                    "file_id": file_id,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing Telegram Accounts: {e}")
        
        return results

    def _parse_axiom_tiktok_contacts(self, file_path: str, sheet_name: str, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        """Parse TikTok Contacts sheet dari Axiom."""
        results = []
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                if pd.isna(row.get('ID')):
                    continue
                    
                acc = {
                    "platform": "tiktok",
                    "account_name": self._clean(row.get('User Name')),
                    "account_id": self._clean(row.get('ID')),
                    "user_id": self._clean(row.get('ID')),
                    "full_name": self._clean(row.get('Nickname')),
                    "profile_picture_url": self._clean(row.get('Profile Picture URL')),
                    "source_tool": "Axiom",
                    "device_id": device_id,
                    "file_id": file_id,
                }
                results.append(acc)
                
        except Exception as e:
            print(f"Error parsing TikTok Contacts: {e}")
        
        return results

    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int."""
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None

    def _safe_bool(self, value) -> Optional[bool]:
        """Safely convert value to bool."""
        if pd.isna(value) or value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', 'yes', '1', 'y']
        return bool(value)

    def parse_social_media_from_sample_folder(self, sample_folder_path: str, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        results = []
        sample_path = Path(sample_folder_path)
        
        if not sample_path.exists():
            print(f"Sample folder tidak ditemukan: {sample_folder_path}")
            return results
        
        # Iterasi setiap device folder (iPhone Hikari, Realmi Hikari, Xiaomi Riko)
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
                    tool_results = self._parse_axiom_social_media(tool_folder, device_id, file_id)
                elif tool_folder.name.lower() == "cellebrite":
                    tool_results = self._parse_cellebrite_social_media(tool_folder, device_id, file_id)
                elif tool_folder.name.lower() == "oxygen":
                    tool_results = self._parse_oxygen_folder_social_media(tool_folder, device_id, file_id)
                else:
                    continue
                    
                results.extend(tool_results)
        
        return results

    def _parse_axiom_social_media(self, tool_folder: Path, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        # Cari file Excel
        excel_files = list(tool_folder.glob("*.xlsx")) + list(tool_folder.glob("*.xls"))
        
        for excel_file in excel_files:
            print(f"Parsing Axiom file: {excel_file.name}")
            try:
                file_results = self.parse_oxygen_social_media(excel_file, device_id, file_id)
                results.extend(file_results)
            except Exception as e:
                print(f"Error parsing Axiom file {excel_file.name}: {e}")
        
        return results

    def _parse_cellebrite_social_media(self, tool_folder: Path, device_id: int, file_id: int) -> List[Dict[str, Any]]:
    
        results = []
        
        # Cari file Excel
        excel_files = list(tool_folder.glob("*.xlsx")) + list(tool_folder.glob("*.xls"))
        
        for excel_file in excel_files:
            print(f"Parsing Cellebrite file: {excel_file.name}")
            try:
                file_results = self.parse_oxygen_social_media(excel_file, device_id, file_id)
                results.extend(file_results)
            except Exception as e:
                print(f"Error parsing Cellebrite file {excel_file.name}: {e}")
        
        return results

    def _parse_oxygen_folder_social_media(self, tool_folder: Path, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        # Cari file Excel
        excel_files = list(tool_folder.glob("*.xlsx")) + list(tool_folder.glob("*.xls"))
        
        for excel_file in excel_files:
            print(f"Parsing Oxygen file: {excel_file.name}")
            try:
                file_results = self.parse_oxygen_social_media(excel_file, device_id, file_id)
                results.extend(file_results)
            except Exception as e:
                print(f"Error parsing Oxygen file {excel_file.name}: {e}")
        
        return results
