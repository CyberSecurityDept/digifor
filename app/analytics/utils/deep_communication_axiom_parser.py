import re
import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.analytics.shared.models import DeepCommunication


class DeepCommunicationParser:
    """
    Parser untuk membaca sheet Magnet Axiom (WhatsApp dan Telegram)
    dan menyimpan hasilnya ke tabel DeepCommunication.
    """

    VALID_SOURCES = {"Telegram", "WhatsApp Messenger"}

    def __init__(self, db: Session):
        self.db = db

    def parse_axiom_deep_communication(self, file_path: str, device_id: int, file_id: int):
        """
        Parse 2 sheet: 'Android WhatsApp Messages' dan 'Telegram Messages - Android'
        """
        results = []

        try:
            xls = pd.ExcelFile(file_path)
            sheets = xls.sheet_names

            # --- Telegram ---
            if "Telegram Messages - Android" in sheets:
                telegram_msgs = self._parse_telegram_sheet(xls, "Telegram Messages - Android", device_id, file_id)
                results.extend(telegram_msgs)

            # --- WhatsApp ---
            if "Android WhatsApp Messages" in sheets:
                whatsapp_msgs = self._parse_whatsapp_sheet(xls, "Android WhatsApp Messages", device_id, file_id)
                results.extend(whatsapp_msgs)

            # ✅ Pastikan hanya dua sumber valid (hindari leak mmssms.db dsb)
            results = [r for r in results if r.get("source") in self.VALID_SOURCES]

            # ✅ Simpan ke DB
            if results:
                self.db.bulk_insert_mappings(DeepCommunication, results)
                self.db.commit()
                print(f"✅ Inserted {len(results)} deep communication rows")

                # 🧹 Bersihkan entry yang gak valid (type NULL)
                deleted = (
                    self.db.query(DeepCommunication)
                    .filter(DeepCommunication.type.is_(None))
                    .delete(synchronize_session=False)
                )
                if deleted:
                    self.db.commit()
                    print(f"🧽 Cleaned up {deleted} invalid rows (type IS NULL)")

        except Exception as e:
            print(f"❌ Error parsing deep communication: {e}")

        return results

    # ===================================
    # 🔹 Telegram
    # ===================================
    def _parse_telegram_sheet(
        self, xls: pd.ExcelFile, sheet_name: str, device_id: int, file_id: int
    ) -> List[Dict[str, Any]]:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str, engine="openpyxl")
        data = []

        for _, row in df.iterrows():
            direction_raw = (row.get("Direction") or "").strip().lower()
            direction = None
            if "sent" in direction_raw:
                direction = "Outgoing"
            elif "received" in direction_raw:
                direction = "Incoming"

            entry = {
                "device_id": device_id,
                "file_id": file_id,
                "direction": direction,
                "source": "Telegram",  # 💬 Hardcode, biar gak ketimpa kolom "Source" dari Excel
                "type": "Telegram message",
                "timestamp": self._clean(row.get("Creation Date/Time - UTC+00:00 (dd/MM/yyyy)")),
                "text": self._clean(row.get("Message Body")),
                "sender": self._clean(row.get("Partner")),
                "receiver": self._clean(row.get("Partner")),
                "details": None,
                "thread_id": self._clean(row.get("_ChatId")),
            }

            if any(entry.values()):
                data.append(entry)

        return data

    # ===================================
    # 🔹 WhatsApp
    # ===================================
    def _parse_whatsapp_sheet(
        self, xls: pd.ExcelFile, sheet_name: str, device_id: int, file_id: int
    ) -> List[Dict[str, Any]]:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str, engine="openpyxl")
        data = []

        for _, row in df.iterrows():
            sender = self._clean(row.get("Sender"))
            receiver = self._clean(row.get("Receiver"))
            location = self._clean(row.get("Location"))

            # ✅ hanya proses baris yang punya "chat_list"
            if not location or "chat_list" not in location.lower():
                continue

            # Tentukan direction
            direction = "Incoming" if sender and re.search(r"\d{8,}", sender) else "Outgoing"

            # Ekstrak thread_id dari Location
            thread_id = None
            match = re.search(r"chat_list\(_id:\s*(\d+)\)", location or "", re.IGNORECASE)
            if match:
                thread_id = match.group(1).strip()

            if not thread_id:
                continue

            entry = {
                "device_id": device_id,
                "file_id": file_id,
                "direction": direction,
                "source": "WhatsApp Messenger",
                "type": "WhatsApp message",
                "timestamp": self._clean(row.get("Message Sent Date/Time - UTC+00:00 (dd/MM/yyyy)")),
                "text": self._clean(row.get("Message")),
                "sender": sender,
                "receiver": receiver,
                "details": None,
                "thread_id": thread_id,
            }

            if any(entry.values()):
                data.append(entry)

        return data

    # ===================================
    # 🔧 Utility
    # ===================================
    def _clean(self, value: Any) -> Optional[str]:
        """Membersihkan nilai kosong dan 'nan'"""
        if value is None or pd.isna(value):
            return None
        text = str(value).strip()
        if text.lower() in ["nan", "none", ""]:
            return None
        return text
