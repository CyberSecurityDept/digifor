import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.analytics.device_management.models import SocialMedia, ChatMessage
from app.db.session import get_db
from .file_validator import file_validator
from pathlib import Path
import re, traceback, logging, warnings

logger = logging.getLogger(__name__)

class AxiomParser:
    
    def __init__(self, db: Session):
        self.db = db
    
    def _clean(self, text: Any) -> Optional[str]:
        if text is None:
            return None
        if isinstance(text, float) and pd.isna(text):
            return None
        text_str = str(text).strip()
        if text_str.lower() in ['nan', 'none', 'null', '', 'n/a']:
            return None
        return text_str
    
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
    
    def _validate_social_media_data(self, acc: Dict[str, Any]) -> tuple[bool, str]:
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
    
    def _check_existing_social_media(self, acc: Dict[str, Any]) -> bool:
        query = self.db.query(SocialMedia).filter(
            SocialMedia.file_id == acc.get("file_id")
        )
        
        if acc.get("instagram_id"):
            query = query.filter(SocialMedia.instagram_id == acc.get("instagram_id"))
        elif acc.get("facebook_id"):
            query = query.filter(SocialMedia.facebook_id == acc.get("facebook_id"))
        elif acc.get("whatsapp_id"):
            query = query.filter(SocialMedia.whatsapp_id == acc.get("whatsapp_id"))
        elif acc.get("telegram_id"):
            query = query.filter(SocialMedia.telegram_id == acc.get("telegram_id"))
        elif acc.get("X_id"):
            query = query.filter(SocialMedia.X_id == acc.get("X_id"))
        elif acc.get("tiktok_id"):
            query = query.filter(SocialMedia.tiktok_id == acc.get("tiktok_id"))
        elif acc.get("account_name"):
            query = query.filter(SocialMedia.account_name == acc.get("account_name"))
        else:
            return False
        
        return query.first() is not None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        try:
            if isinstance(value, str):
                value = value.strip()
                if value.lower() in ['nan', 'none', 'null', '', 'n/a']:
                    return None
                return int(float(value))
            return int(value)
        except (ValueError, TypeError):
            return None

    def parse_axiom_social_media(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []

        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')

            print(f" Total sheets available: {len(xls.sheet_names)}")

            for sheet_name in xls.sheet_names:
                sheet_name_str = str(sheet_name)
                print(f"Processing sheet: {sheet_name_str}")

                if 'Instagram Profiles' in sheet_name_str:
                    results.extend(self._parse_axiom_instagram_profiles(file_path, sheet_name, file_id))
                elif 'Android Instagram Following' in sheet_name_str:
                    results.extend(self._parse_axiom_instagram_following(file_path, sheet_name, file_id))
                elif 'Android Instagram Users' in sheet_name_str:
                    results.extend(self._parse_axiom_instagram_users(file_path, sheet_name, file_id))

                elif 'Twitter Users' in sheet_name_str:
                    results.extend(self._parse_axiom_twitter_users(file_path, sheet_name, file_id))

                elif 'Telegram Accounts' in sheet_name_str:
                    results.extend(self._parse_axiom_telegram_accounts(file_path, sheet_name, file_id))
                elif 'User Accounts' in sheet_name_str:
                    results.extend(self._parse_axiom_user_accounts(file_path, sheet_name, file_id))

                elif 'TikTok Contacts' in sheet_name_str:
                    results.extend(self._parse_axiom_tiktok_contacts(file_path, sheet_name, file_id))

                elif 'Facebook Contacts' in sheet_name_str:
                    results.extend(self._parse_axiom_facebook_contacts(file_path, sheet_name, file_id))
                elif 'Facebook User-Friends' in sheet_name_str:
                    results.extend(self._parse_axiom_facebook_users(file_path, sheet_name, file_id))

                elif 'WhatsApp Contacts - Android' in sheet_name_str:
                    results.extend(self._parse_axiom_whatsapp_contacts(file_path, sheet_name, file_id))
                elif 'WhatsApp User Profiles - Androi' in sheet_name_str:
                    results.extend(self._parse_axiom_whatsapp_users(file_path, sheet_name, file_id))
                elif 'WhatsApp Accounts Information' in sheet_name_str:
                    results.extend(self._parse_axiom_whatsapp_accounts(file_path, sheet_name, file_id))

                elif 'Android WhatsApp Accounts Infor' in sheet_name_str:
                    results.extend(self._parse_axiom_whatsapp_accounts_info(file_path, sheet_name, file_id))
                elif 'Android WhatsApp Chats' in sheet_name_str:
                    results.extend(self._parse_axiom_whatsapp_chats(file_path, sheet_name, file_id))
                elif 'Android WhatsApp Contacts' in sheet_name_str:
                    results.extend(self._parse_axiom_whatsapp_contacts_android(file_path, sheet_name, file_id))
                elif 'Android WhatsApp Messages' in sheet_name_str:
                    results.extend(self._parse_axiom_whatsapp_messages(file_path, sheet_name, file_id))
                elif 'Android WhatsApp User Profiles' in sheet_name_str:
                    results.extend(self._parse_axiom_whatsapp_user_profiles(file_path, sheet_name, file_id))
                elif 'Telegram Chats - Android' in sheet_name_str:
                    results.extend(self._parse_axiom_telegram_chats(file_path, sheet_name, file_id))
                elif 'Telegram Contacts - Android' in sheet_name_str:
                    results.extend(self._parse_axiom_telegram_contacts_android(file_path, sheet_name, file_id))
                elif 'Telegram Messages - Android' in sheet_name_str:
                    results.extend(self._parse_axiom_telegram_messages(file_path, sheet_name, file_id))
                elif 'Telegram Users - Android' in sheet_name_str:
                    results.extend(self._parse_axiom_telegram_users_android(file_path, sheet_name, file_id))

            unique_results = []
            seen_accounts = set()

            for acc in results:
                if "platform" in acc:
                    account_key = f"{acc.get('platform', '')}_{acc.get('account_id', '')}_{acc.get('account_name', '')}"
                else:
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
                                print(f" Skipping invalid record: {error_msg} - Platform IDs: {platform_str}, Account: {log_acc.get('account_name', 'N/A')}")
                            continue

                        if "platform" in acc:
                            acc = self._convert_old_to_new_structure(acc)

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
                    sheet_name_str = str(sheet_name)
                    if 'Instagram Profiles' in sheet_name_str:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'User ID' in df.columns:
                            total_count += len(df[df['User ID'].notna()])
                    elif 'Twitter Users' in sheet_name_str:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'User ID' in df.columns:
                            total_count += len(df[df['User ID'].notna()])
                    elif 'Telegram Accounts' in sheet_name_str:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'Account ID' in df.columns:
                            total_count += len(df[df['Account ID'].notna()])
                    elif 'TikTok Contacts' in sheet_name_str:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'ID' in df.columns:
                            total_count += len(df[df['ID'].notna()])
                    elif 'Facebook Contacts' in sheet_name_str:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'Profile ID' in df.columns:
                            total_count += len(df[df['Profile ID'].notna()])
                    elif 'Facebook User-Friends' in sheet_name_str:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'User ID' in df.columns:
                            total_count += len(df[df['User ID'].notna()])
                    elif 'WhatsApp Contacts' in sheet_name_str:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'ID' in df.columns:
                            total_count += len(df[df['ID'].notna()])
                    elif 'WhatsApp User Profiles' in sheet_name_str:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine, dtype=str)
                        if 'Phone Number' in df.columns:
                            total_count += len(df[df['Phone Number'].notna()])
                except Exception:
                    continue

            return total_count

        except Exception as e:
            return 0

    def _parse_axiom_instagram_profiles(self, file_path: str, sheet_name: str, file_id: int) -> List[Dict[str, Any]]:
        results = []

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl', dtype=str)

            for _, row in df.iterrows():
                if self._is_na(row.get('User Name')):
                    continue

                following_value = self._clean(row.get('Following'))
                followers_value = self._clean(row.get('Is Followed By'))

                following_count = 1 if following_value and following_value.lower() == 'yes' else None
                followers_count = 1 if followers_value and followers_value.lower() == 'yes' else None

                user_id_value = self._clean(row.get('User ID'))
                user_name_value = self._clean(row.get('User Name'))

                account_id_value = user_id_value if user_id_value else user_name_value

                acc = {
                    "platform": "Instagram",
                    "account_name": user_name_value,
                    "account_id": account_id_value,
                    "user_id": user_id_value,
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
                if self._is_na(row.get('User Name')):
                    continue

                following_value = self._clean(row.get('Status'))
                following_count = 1 if following_value and following_value.lower() == 'following' else None

                user_id_value = self._clean(row.get('ID'))
                user_name_value = self._clean(row.get('User Name'))

                account_id_value = user_id_value if user_id_value else user_name_value

                acc = {
                    "platform": "Instagram",
                    "account_name": user_name_value,
                    "account_id": account_id_value,
                    "user_id": user_id_value,
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
                if self._is_na(row.get('User Name')):
                    continue

                user_id_value = self._clean(row.get('ID'))
                user_name_value = self._clean(row.get('User Name'))
                account_id_value = user_id_value if user_id_value else user_name_value
                acc = {
                    "platform": "Instagram",
                    "account_name": user_name_value,
                    "account_id": account_id_value,
                    "user_id": user_id_value,
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
                if not service_name or 'telegram' not in service_name.lower():
                    continue
                if not user_name and not user_id:
                    continue

                acc = {
                    "platform": "Telegram",
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
                    "platform": "WhatsApp",
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
                if self._is_na(row.get('User Name')):
                    continue

                user_id_value = self._clean(row.get('User ID'))
                screen_name_value = self._clean(row.get('Screen Name'))
                user_name_value = self._clean(row.get('User Name')) or screen_name_value

                account_id_value = user_id_value if user_id_value else user_name_value

                acc = {
                    "platform": "X",
                    "account_name": user_name_value or screen_name_value,
                    "account_id": account_id_value,
                    "user_id": user_id_value,
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
                if self._is_na(row.get('User ID')):
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
                    "platform": "Telegram",
                    "account_name": account_name_value,
                    "account_id": account_id_final,
                    "user_id": user_id_value,
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
                if self._is_na(row.get("ID")):
                    continue
                nickname = self._clean(row.get("Nickname"))
                user_name = self._clean(row.get("User Name"))
                account_name = nickname or user_name

                acc = {
                    "platform": "TikTok",
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
                if self._is_na(row.get('Profile ID')):
                    continue
                acc = {
                    "platform": "Facebook",
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
                if self._is_na(row.get('User ID')):
                    continue
                acc = {
                    "platform": "Facebook",
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
                if self._is_na(row.get('ID')):
                    continue
                acc = {
                    "platform": "WhatsApp",
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
                if self._is_na(row.get('Phone Number')):
                    continue

                acc = {
                    "platform": "WhatsApp",
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

    def _parse_axiom_social_media(self, tool_folder: Path, file_id: int) -> List[Dict[str, Any]]:
        results = []
        excel_files = list(tool_folder.glob("*.xlsx")) + list(tool_folder.glob("*.xls"))
        for excel_file in excel_files:
            print(f"Parsing Axiom file: {excel_file.name}")
            try:
                file_results = self.parse_axiom_social_media(str(excel_file), file_id)
                results.extend(file_results)
            except Exception as e:
                print(f"Error parsing Axiom file {excel_file.name}: {e}")
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
            logger.debug(f"[TELEGRAM PARSER] Sheet loaded: {len(df)} rows, columns: {list(df.columns)[:10]}")
            processed_count = 0
            skipped_count = 0
            for idx, row in df.iterrows():
                if self._is_na(row.get('Message')) or not str(row.get('Message')).strip():
                    skipped_count += 1
                    continue

                message_status = str(row.get('Message Status', '')).strip()
                direction = ''
                if message_status.lower() == 'received':
                    direction = 'Incoming'
                elif message_status.lower() == 'sent':
                    direction = 'Outgoing'
                else:
                    direction = str(row.get('Direction', '')).strip()

                message_data = {                    
                    "file_id": file_id,
                    "platform": "Telegram",
                    "message_text": str(row.get('Message', '')),
                    "from_name": str(row.get('Sender Name', '')),
                    "sender_number": str(row.get('Sender ID', '')),
                    "to_name": str(row.get('Recipient Name', '')),
                    "recipient_number": str(row.get('Recipient ID', '')),
                    "timestamp": str(row.get('Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "thread_id": str(row.get('_ThreadID', '')),
                    "chat_id": str(row.get('Chat ID', '')),
                    "message_id": str(row.get('Message ID', '')),
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
                if self._is_na(row.get('Message')) or not str(row.get('Message')).strip():
                    skipped_count += 1
                    continue

                message_data = {
                    "file_id": file_id,
                    "platform": "Instagram",
                    "message_text": str(row.get('Message', '')),
                    "from_name": str(row.get('Sender', '')),
                    "sender_number": "",
                    "to_name": str(row.get('Recipient', '')),
                    "recipient_number": "",
                    "timestamp": str(row.get('Message Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "thread_id": str(row.get('_ThreadID', '')),
                    "chat_id": str(row.get('Chat ID', '')),
                    "message_id": str(row.get('Item ID', '')),
                    "message_type": str(row.get('Type', 'text')),
                    "direction": str(row.get('Direction', '')),
                    "source_tool": "Magnet Axiom",
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
                if self._is_na(row.get('Message')) or not str(row.get('Message')).strip():
                    skipped_count += 1
                    continue

                message_data = {                    
                    "file_id": file_id,
                    "platform": "TikTok",
                    "message_text": str(row.get('Message', '')),
                    "from_name": str(row.get('Sender', '')),
                    "sender_number": "",
                    "to_name": str(row.get('Recipient', '')),
                    "recipient_number": "",
                    "timestamp": str(row.get('Created Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "thread_id": str(row.get('_ThreadID', '')),
                    "chat_id": "",
                    "message_id": str(row.get('Item ID', '')),
                    "message_type": str(row.get('Message Type', 'text')),
                    "direction": "",
                    "source_tool": "Magnet Axiom",
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
                if self._is_na(row.get('Text')) or not str(row.get('Text')).strip():
                    skipped_count += 1
                    continue

                message_data = {                    
                    "file_id": file_id,
                    "platform": "X",
                    "message_text": str(row.get('Text', '')),
                    "from_name": str(row.get('Sender Name', '')),
                    "sender_number": str(row.get('Sender ID', '')),
                    "to_name": str(row.get('Recipient Name(s)', '')),
                    "recipient_number": str(row.get('Recipient ID(s)', '')),
                    "timestamp": str(row.get('Sent/Received Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "thread_id": str(row.get('_ThreadID', '')),
                    "chat_id": "",
                    "message_id": str(row.get('Item ID', '')),
                    "message_type": "text",
                    "direction": str(row.get('Direction', '')),
                    "source_tool": "Magnet Axiom",
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
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
                if self._is_na(row.get('Record', '')) or str(row.get('Record', '')).strip() == 'Record':
                    continue

                user_id = self._clean(row.get('User ID', ''))
                first_name = self._clean(row.get('First Name', ''))
                last_name = self._clean(row.get('Last Name', ''))
                username = self._clean(row.get('Username', ''))
                source_col = self._clean(row.get('Source', ''))
                
                source = None
                if source_col and 'org.telegram.messenger' in source_col:
                    source = "Telegram"

                if user_id and (first_name or last_name or username):
                    full_name = f"{first_name} {last_name}".strip() if first_name or last_name else username
                    account_name = username or full_name

                    acc = {
                        "platform": "Telegram",
                        "account_name": account_name,
                        "account_id": user_id,
                        "user_id": user_id,
                        "full_name": full_name,
                        "source": source or "Telegram",
                        "source_tool": "Magnet Axiom",
                        "sheet_name": sheet_name,
                        "file_id": file_id,
                    }
                    results.append(acc)

        except Exception as e:
            print(f"Error parsing {sheet_name} sheet: {e}")

        return results

