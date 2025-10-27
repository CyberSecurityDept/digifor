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
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                xls = pd.ExcelFile(file_path)
                sheet_name = file_validator._find_contacts_sheet(xls.sheet_names)

                if not sheet_name:
                    return results

                df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine="openpyxl")

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

                # --- iterasi tiap platform ---
                for platform in detected_platforms:
                    account_id = self._extract_account_id(internet_field, platform)
                    if not account_id:
                        account_id = self._extract_account_id(phones_emails_field, platform)

                    if not account_id and not account_name:
                        continue

                    acc = {
                        "platform": platform,
                        "account_name": account_name,
                        "account_id": account_id,
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
        """
        Deteksi multiple platform dalam satu kolom Source.
        Contoh: "WhatsApp Messenger, Telegram" -> ["whatsapp", "telegram"]
        Abaikan 'WhatsApp Messenger Backup'
        """
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
        """Utility untuk membersihkan teks kosong / NaN."""
        if text is None or pd.isna(text):
            return None
        text = str(text).strip()
        if text.lower() in ["", "nan", "none"]:
            return None
        return text

    def parse_axiom_deep_communication() :
        
        return None
