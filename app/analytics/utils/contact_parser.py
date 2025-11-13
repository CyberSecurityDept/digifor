import pandas as pd
import warnings
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.analytics.device_management.models import Contact, Call
import re

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class ContactParser:
    
    def __init__(self, db: Session):
        self.db = db
    
    def parse_axiom_contacts(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        seen_numbers = set()

        try:
            print("📘 Reading Axiom Excel file...")
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            print(f"LIST SHEET NAME: {xls.sheet_names}")
            contacts_sheet = None
            for sheet_name in xls.sheet_names:
                sheet_clean = str(sheet_name).strip().lower()
                if 'android contacts' in sheet_clean:
                    contacts_sheet = sheet_name
                    break
            print(f"[SHEET NAME : {contacts_sheet}]")
                            
            if not contacts_sheet:
                print("No contacts sheet found in Axiom file")
                return results
            
            df = pd.read_excel(file_path, sheet_name=contacts_sheet, engine='openpyxl', dtype=str)
            print(f"Found {len(df)} rows in '{contacts_sheet}' — starting parse...")

            for idx, row in df.iterrows():
                name = str(row.get('Display Name', '')).strip()
                phone_field = str(row.get('Phone Number(s)', '')).strip()
                acc_type = str(row.get('Source Account Type(s)', '')).strip()

                phone_number = ""

                if phone_field and phone_field.lower() != 'nan':
                    parts = re.split(r'[\n,;]+', phone_field)
                    cleaned_candidates = []

                    for part in parts:
                        part_clean = part.strip()
                        match = re.search(r'(\+?\d[\d\s\-().]*)', part_clean)
                        if match:
                            num = re.sub(r'[^\d+]', '', match.group(1))
                            if 7 <= len(num) <= 15:
                                normalized = num.lstrip('+').replace(' ', '').replace('-', '')
                                cleaned_candidates.append((num, normalized))
                    
                    for original, normalized in cleaned_candidates:
                        if normalized not in seen_numbers:
                            phone_number = original
                            seen_numbers.add(normalized)
                            break

                    if not phone_number and cleaned_candidates:
                        print(f"All numbers in row {int(idx)+1} are duplicates or invalid: {cleaned_candidates}")

                if not name or name.lower() == 'nan':
                    name = "Unknown"

                idx_int = int(idx)
                if idx_int % 10 == 0 or idx_int == len(df) - 1:
                    print(f"Row {idx_int+1}/{len(df)} → Name='{name}', Phone='{phone_number}', Account='{acc_type}'")

                if phone_number:
                    contact_data = {
                        "file_id": file_id,
                        "display_name": name.strip(),
                        "phone_number": phone_number.strip(),
                        "type": acc_type.strip(),
                    }
                    results.append(contact_data)
                else:
                    print(f"Skipped row {int(idx)+1} — no valid phone number found")

            print(f"Finished parsing Axiom contacts — valid unique entries: {len(results)}")

            for contact in results:
                existing = (
                    self.db.query(Contact)
                    .filter(
                        Contact.phone_number == contact["phone_number"],
                        Contact.file_id == file_id
                    )
                    .first()
                )
                if not existing:
                    self.db.add(Contact(**contact))
                else:
                    print(f"Skipped DB insert — duplicate number in DB: {contact['phone_number']}")

            self.db.commit()
            print(f"Successfully saved {len(results)} Axiom contacts (unique & valid numbers only)")

        except Exception as e:
            print(f"Error parsing Axiom contacts: {e}")
            self.db.rollback()
            raise e
        
        return results
    
    def parse_axiom_calls(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            calls_sheet = None
            for sheet_name in xls.sheet_names:
                if isinstance(sheet_name, str) and 'call' in str(sheet_name).lower():
                    calls_sheet = sheet_name
                    break
            
            if not calls_sheet:
                print("No calls sheet found in Axiom file")
                return results
            
            df = pd.read_excel(file_path, sheet_name=calls_sheet, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                call_data = {
                    "file_id": file_id,
                    "direction": str(row.get('Direction', '')),
                    "source": str(row.get('Source', '')),
                    "type": str(row.get('Type', '')),
                    "timestamp": str(row.get('Received Date/Time - UTC+00:00 (dd/MM/yyyy)', '')),
                    "duration": str(row.get('Duration', '')),
                    "caller": str(row.get('Caller', '')),
                    "receiver": str(row.get('Recipient(s)', '')),
                    "details": str(row.get('Status', '')),
                    "thread_id": str(row.get('_ThreadID', ''))
                }
                
                if call_data["caller"] and call_data["caller"] != 'nan':
                    results.append(call_data)
            
            for call in results:
                existing = (
                    self.db.query(Call)
                    .filter(
                        Call.caller == call["caller"],
                        Call.file_id == file_id,
                        Call.timestamp == call["timestamp"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(Call(**call))
            
            self.db.commit()
            print(f"Successfully saved {len(results)} calls to database")
                
        except Exception as e:
            print(f"Error parsing Axiom calls: {e}")
            self.db.rollback()
            raise e
        
        return results
    
    def parse_cellebrite_contacts(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        seen_numbers = set()

        try:
            print("📘 Reading Cellebrite Excel file...")
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            print(f"LIST SHEET NAME: {xls.sheet_names}")

            if 'Contacts' not in xls.sheet_names:
                print("No Contacts sheet found in Cellebrite file")
                return results

            print("[SHEET NAME DETECTED: Contacts]")

            df = pd.read_excel(file_path, sheet_name='Contacts', engine='openpyxl', dtype=str, header=1)
            print(f"Found {len(df)} rows in 'Contacts' sheet — starting parse...")
            print(f"Columns detected: {list(df.columns)}")

            if str(df.columns[0]).startswith('#'):
                df = df.drop(df.columns[0], axis=1)
                print("Dropped first column (#) — not part of contact data")

            for idx, row in df.iterrows():
                name = str(row.get('Name', '')).strip()
                entries_raw = str(row.get('Entries', '')).strip()
                status = str(row.get('Interaction Statuses', '')).strip()

                phone_number = ""
                display_name = name

                if entries_raw and entries_raw.lower() != 'nan':
                    parts = re.split(r'[\n,;]+', entries_raw)
                    for part in parts:
                        part_clean = part.strip()
                        lower = part_clean.lower()

                        if any(kw in lower for kw in ["@newsletter", "@bot", "@system", "@broadcast", "@business"]):
                            print(f"Skipped system/bot entry: {part_clean}")
                            continue

                        if "whatsapp" in lower:
                            match = re.search(r'(\d+)(?=@)', part_clean)
                            if match:
                                candidate = match.group(1)
                                if 7 <= len(candidate) <= 15:
                                    phone_number = candidate
                                    print(f"📞 Found WhatsApp number: {phone_number}")
                                    break
                                else:
                                    print(f"Skipped invalid WhatsApp number (length {len(candidate)}): {candidate}")

                        elif lower.startswith("phone-mobile:"):
                            content = part_clean.split(":", 1)[1].strip()
                            digits = re.sub(r'[^\d+]', '', content)
                            if re.search(r'\d{7,}', digits) and 7 <= len(digits) <= 15:
                                phone_number = digits
                                print(f"📱 Found mobile number: {phone_number}")
                                break
                            else:
                                print(f"Skipped Phone-Mobile invalid or non-numeric: {content}")

                        elif lower.startswith("phone-:"):
                            content = part_clean.split(":", 1)[1].strip()
                            digits = re.sub(r'[^\d+]', '', content)
                            if re.search(r'\d{7,}', digits) and 7 <= len(digits) <= 15:
                                phone_number = digits
                                print(f"Found phone number: {phone_number}")
                                break
                            else:
                                print(f"Skipped invalid Phone- number: {content}")

                if not display_name or display_name.lower() == 'nan':
                    display_name = "Unknown"

                idx_int = int(idx)
                if idx_int % 10 == 0 or idx_int == len(df) - 1:
                    print(f"Row {idx_int+1}/{len(df)} → Name='{display_name}', Phone='{phone_number}', Status='{status}'")

                if phone_number:
                    if phone_number in seen_numbers:
                        print(f"Duplicate number detected, skipped: {phone_number}")
                        continue

                    seen_numbers.add(phone_number)
                    contact_data = {
                        "file_id": file_id,
                        "display_name": display_name.strip(),
                        "phone_number": phone_number.strip(),
                        "type": status.strip()
                    }
                    results.append(contact_data)
                else:
                    idx_int = int(idx)
                    print(f"Skipped row {idx_int+1} — no valid number found in Entries")

            print(f"Finished parsing Cellebrite contacts — valid unique entries: {len(results)}")

            for contact in results:
                existing = (
                    self.db.query(Contact)
                    .filter(
                        Contact.phone_number == contact["phone_number"],
                        Contact.file_id == file_id
                    )
                    .first()
                )
                if not existing:
                    self.db.add(Contact(**contact))
                else:
                    print(f"Skipped DB insert — duplicate in database: {contact['phone_number']}")

            self.db.commit()
            print(f"Successfully saved {len(results)} Cellebrite contacts (unique & valid numbers only)")

        except Exception as e:
            print(f"Error parsing Cellebrite contacts: {e}")
            self.db.rollback()
            raise e

        return results

    def parse_cellebrite_calls(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            calls_sheet = None
            for sheet_name in xls.sheet_names:
                if isinstance(sheet_name, str) and 'call' in str(sheet_name).lower():
                    calls_sheet = sheet_name
                    break
            
            if not calls_sheet:
                print("No calls sheet found in Cellebrite file")
                return results
            
            df = pd.read_excel(file_path, sheet_name=calls_sheet, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                call_data = {
                    "file_id": file_id,
                    "direction": str(row.get('Direction', '')),
                    "source": str(row.get('Source', '')),
                    "type": str(row.get('Type', '')),
                    "timestamp": str(row.get('Timestamp', '')),
                    "duration": str(row.get('Duration', '')),
                    "caller": str(row.get('Caller', '')),
                    "receiver": str(row.get('Receiver', '')),
                    "details": str(row.get('Details', '')),
                    "thread_id": str(row.get('Thread ID', ''))
                }
                
                if call_data["caller"] and call_data["caller"] != 'nan':
                    results.append(call_data)
            
            for call in results:
                existing = (
                    self.db.query(Call)
                    .filter(
                        Call.caller == call["caller"],
                        Call.file_id == file_id,
                        Call.timestamp == call["timestamp"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(Call(**call))
            
            self.db.commit()
            print(f"Successfully saved {len(results)} Cellebrite calls to database")
            
        except Exception as e:
            print(f"Error parsing Cellebrite calls: {e}")
            self.db.rollback()
            raise e
        
        return results
    
    def parse_oxygen_contacts(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()
            if file_extension == '.xls':
                engine = "xlrd"
            else:
                engine = "openpyxl"
            
            xls = pd.ExcelFile(file_path, engine=engine)
            
            contacts_sheet = None
            print(f"LIST SHEET NAME {xls.sheet_names}")
            for sheet_name in xls.sheet_names:
                sheet_clean = str(sheet_name).strip().lower()
                if 'contacts' in sheet_clean:
                    contacts_sheet = sheet_name
                    break
            print(f"[SHEET NAME : {sheet_name}]")
            
            if not contacts_sheet:
                print("No contacts sheet found in Oxygen file")
                return results
            
            df = pd.read_excel(file_path, sheet_name=contacts_sheet, dtype=str, engine=engine)
            
            print(f"Found {len(df)} rows in '{contacts_sheet}' sheet — starting parse...")

            for idx, row in df.iterrows():
                raw_name_field = str(row.get('Contact', '')).strip()
                display_name = ""
                if raw_name_field and raw_name_field.lower() != 'nan':
                    name_lines = [ln.strip() for ln in re.split(r'[\n,;]+', raw_name_field) if ln.strip()]
                    if name_lines:
                        first_line = name_lines[0]
                        if not re.match(r'^(nickname|fullname|first name|last name)\s*:', first_line.lower()):
                            display_name = first_line
                        else:
                            for ln in name_lines:
                                lower_ln = ln.lower()
                                if lower_ln.startswith("fullname:"):
                                    display_name = ln.split(":", 1)[1].strip()
                                    break
                                elif lower_ln.startswith("first name:"):
                                    display_name = ln.split(":", 1)[1].strip()
                                    break
                                elif lower_ln.startswith("last name:"):
                                    display_name = ln.split(":", 1)[1].strip()
                                    break
                            if not display_name:
                                for ln in name_lines:
                                    if not ln.lower().startswith("nickname:"):
                                        display_name = ln.strip()
                                        break

                raw_phone_field = str(row.get('Phones & Emails', '')).strip()
                phone_number = ""
                if raw_phone_field and raw_phone_field.lower() != 'nan':
                    lower_field = raw_phone_field.lower()
                    if any(k in lower_field for k in ["phone number", "mobile", "cell", "tel", "telephone"]):
                        parts = re.split(r'[\n,;]+', raw_phone_field)
                        for part in parts:
                            part_clean = part.strip()
                            match = re.search(r'(\+?\d[\d\s\-().]*)', part_clean)
                            if match:
                                num = re.sub(r'[^\d+]', '', match.group(1))
                                if len(num) >= 7:
                                    phone_number = num
                                    break

                contact_data = {
                    "file_id": file_id,
                    "display_name": display_name,
                    "phone_number": phone_number,
                    "type": str(row.get('Type', '')).strip(),
                }

                idx_int = int(idx)
                if idx_int % 10 == 0 or idx_int == len(df) - 1:
                    print(f"Parsing contact [{idx_int + 1}/{len(df)}]: "
                        f"Name='{contact_data['display_name']}', "
                        f"Phone='{contact_data['phone_number']}'")

                if (
                    contact_data["display_name"]
                    and contact_data["display_name"].lower() != 'nan'
                    and contact_data["phone_number"]
                    and any(k in raw_phone_field.lower() for k in ["phone number", "mobile", "cell", "tel", "telephone"])
                ):
                    results.append(contact_data)
                else:
                    print(f"Skipped contact '{display_name}' — invalid or missing phone")

            print(f"Finished parsing Oxygen contacts — valid entries: {len(results)}")

            for contact in results:
                existing = (
                    self.db.query(Contact)
                    .filter(
                        Contact.display_name == contact["display_name"],
                        Contact.file_id == file_id
                    )
                    .first()
                )
                if not existing:
                    self.db.add(Contact(**contact))
            
            self.db.commit()
            print(f"Successfully saved {len(results)} Oxygen contacts to database (phone entries only)")
        
        except Exception as e:
            print(f"Error parsing Oxygen contacts: {e}")
            self.db.rollback()
            raise e
        
        return results

    def parse_oxygen_calls(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        results = []
        
        try:
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()
            if file_extension == '.xls':
                engine = "xlrd"
            else:
                engine = "openpyxl"
            
            xls = pd.ExcelFile(file_path, engine=engine)
            
            calls_sheet = None
            for sheet_name in xls.sheet_names:
                if isinstance(sheet_name, str) and 'call' in str(sheet_name).lower():
                    calls_sheet = sheet_name
                    break
            
            if not calls_sheet:
                print("No calls sheet found in Oxygen file")
                return results
            
            df = pd.read_excel(file_path, sheet_name=calls_sheet, dtype=str, engine=engine)
            
            for _, row in df.iterrows():
                call_data = {
                    "file_id": file_id,
                    "direction": str(row.get('Direction', '')),
                    "source": str(row.get('Source', '')),
                    "type": str(row.get('Type', '')),
                    "timestamp": str(row.get('Timestamp', '')),
                    "duration": str(row.get('Duration', '')),
                    "caller": str(row.get('Caller', '')),
                    "receiver": str(row.get('Receiver', '')),
                    "details": str(row.get('Details', '')),
                    "thread_id": str(row.get('Thread ID', ''))
                }
                
                if call_data["caller"] and call_data["caller"] != 'nan':
                    results.append(call_data)
            
            for call in results:
                existing = (
                    self.db.query(Call)
                    .filter(
                        Call.caller == call["caller"],
                        Call.file_id == file_id,
                        Call.timestamp == call["timestamp"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(Call(**call))
            
            self.db.commit()
            print(f"Successfully saved {len(results)} Oxygen calls to database")
            
        except Exception as e:
            print(f"Error parsing Oxygen calls: {e}")
            self.db.rollback()
            raise e
        
        return results