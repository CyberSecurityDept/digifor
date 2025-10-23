import re
import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.analytics.device_management.models import SocialMedia

SOCIAL_MEDIA_PLATFORMS = ["instagram", "facebook", "whatsapp", "telegram", "x", "tiktok"]

class SocialMediaParser:
    """
    Parser untuk mengekstrak data sosial media dari Oxygen sheet 'Contacts'.
    """

    def __init__(self, db: Session):
        self.db = db

    def parse_oxygen_social_media(self, file_path: str, device_id: int, file_id: int) -> List[Dict[str, Any]]:
        """
        Parse sheet Contacts dari Oxygen dan simpan akun sosial media ke tabel SocialMedia.
        - Hanya Type == 'Contact' atau 'Contact (merged)'
        - Platform diambil dari kolom Source (bisa multiple)
        - WhatsApp Messenger Backup di-skip
        - account_name dari kolom Contact
        - account_id dari Internet, fallback ke Phones & Emails
        """
        results = []

        try:
            xls = pd.ExcelFile(file_path)
            sheet_name = None
            if "Contacts " in xls.sheet_names:
                sheet_name = "Contacts "
            elif "Contacts" in xls.sheet_names:
                sheet_name = "Contacts"

            if not sheet_name:
                print("⚠️ No 'Contacts' sheet found in Oxygen file.")
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
            print(f"❌ Error parsing social media Oxygen: {e}")

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
