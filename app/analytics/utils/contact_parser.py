import pandas as pd  # type: ignore
import re
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .file_validator import file_validator

# Suppress all OLE2 warnings globally
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
warnings.filterwarnings('ignore', message='.*OLE2 inconsistency.*')
warnings.filterwarnings('ignore', message='.*file size.*not.*multiple of sector size.*')
warnings.filterwarnings('ignore', message='.*SSCS size is 0 but SSAT size is non-zero.*')
warnings.filterwarnings('ignore', message='.*WARNING \*\*\*.*')

class ContactParser:
    
    def __init__(self):
        self.phone_pattern = re.compile(r'(\+?62|0)(\d{8,13})')
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_only_pattern = re.compile(r'^[\+\d\s\-\(\)]+$')
    
    def parse_contacts_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Validasi file terlebih dahulu
        validation = file_validator.validate_excel_file(file_path)
        file_validator.print_validation_summary(validation)
        
        if not validation["is_valid"]:
            print(f"File validation failed: {validation['errors']}")
            if validation["warnings"]:
                print(f"Warnings: {validation['warnings']}")
        
        file_name = file_path.name.lower()
        
        if 'magnet' in file_name or 'axiom' in file_name:
            return self._parse_magnet_axiom_contacts(file_path)
        elif 'oxygen' in file_name:
            return self._parse_oxygen_contacts(file_path)
        else:
            return self._parse_generic_contacts(file_path)
    
    def _parse_magnet_axiom_contacts(self, file_path: Path) -> List[Dict[str, Any]]:
        contacts = []
        
        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                xls = pd.ExcelFile(file_path)
                
                if 'Android Contacts' in xls.sheet_names:
                    contacts.extend(self._parse_magnet_android_contacts(file_path, 'Android Contacts'))
                
                if 'Android WhatsApp Contacts' in xls.sheet_names:
                    contacts.extend(self._parse_magnet_whatsapp_contacts(file_path, 'Android WhatsApp Contacts'))
                
                if 'Telegram Contacts - Android' in xls.sheet_names:
                    contacts.extend(self._parse_magnet_telegram_contacts(file_path, 'Telegram Contacts - Android'))
                    
        except Exception as e:
            print(f"Error parsing Magnet Axiom file: {e}")
        
        return contacts
    
    def _parse_magnet_android_contacts(self, file_path: Path, sheet_name: str) -> List[Dict[str, Any]]:
        contacts = []
        
        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine='openpyxl')
                
                for _, row in df.iterrows():
                    contact = self._extract_magnet_contact_data(row)
                    if contact:
                        contacts.append(contact)
                        
        except Exception as e:
            print(f"Error parsing Android Contacts sheet '{sheet_name}': {e}")
        
        return contacts
    
    def _parse_magnet_whatsapp_contacts(self, file_path: Path, sheet_name: str) -> List[Dict[str, Any]]:
        contacts = []
        
        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine='openpyxl')
                
                for _, row in df.iterrows():
                    contact = self._extract_whatsapp_contact_data(row)
                    if contact:
                        contacts.append(contact)
                        
        except Exception as e:
            print(f"Error parsing WhatsApp Contacts sheet '{sheet_name}': {e}")
        
        return contacts
    
    def _parse_magnet_telegram_contacts(self, file_path: Path, sheet_name: str) -> List[Dict[str, Any]]:
        contacts = []
        
        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine='openpyxl')
                
                for _, row in df.iterrows():
                    contact = self._extract_telegram_contact_data(row)
                    if contact:
                        contacts.append(contact)
                        
        except Exception as e:
            print(f"Error parsing Telegram Contacts sheet '{sheet_name}': {e}")
        
        return contacts
    
    def _parse_oxygen_contacts(self, file_path: Path) -> List[Dict[str, Any]]:
        contacts = []
        
        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                xls = pd.ExcelFile(file_path)
                sheet_name = file_validator._find_contacts_sheet(xls.sheet_names)
                
                if not sheet_name:
                    return contacts
                
                contacts.extend(self._parse_oxygen_contacts_sheet(file_path, sheet_name))
                
        except Exception as e:
            print(f"Error parsing Oxygen file: {e}")
        
        return contacts
    
    def _parse_oxygen_contacts_sheet(self, file_path: Path, sheet_name: str) -> List[Dict[str, Any]]:
        contacts = []
        
        try:
            # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine='openpyxl')
                
                for _, row in df.iterrows():
                    contact_list = self._extract_oxygen_contact_data(row)
                    if contact_list:
                        contacts.extend(contact_list)
                    
        except Exception as e:
            print(f"Error parsing Oxygen Contacts sheet '{sheet_name}': {e}")
        
        return contacts
    
    def _parse_generic_contacts(self, file_path: Path) -> List[Dict[str, Any]]:
        contacts = []
        
        try:
            file_extension = file_path.suffix.lower()
            
            if file_extension == '.csv':
                # Handle CSV files
                df = pd.read_csv(file_path, dtype=str)
                
                for _, row in df.iterrows():
                    contact = self._extract_generic_contact_data(row)
                    if contact:
                        contacts.append(contact)
            elif file_extension == '.txt':
                # Handle TXT files - try different delimiters
                try:
                    # First try comma-separated
                    df = pd.read_csv(file_path, dtype=str, sep=',')
                    if len(df.columns) > 1:
                        for _, row in df.iterrows():
                            contact = self._extract_generic_contact_data(row)
                            if contact:
                                contacts.append(contact)
                    else:
                        # Try tab-separated
                        df = pd.read_csv(file_path, dtype=str, sep='\t')
                        if len(df.columns) > 1:
                            for _, row in df.iterrows():
                                contact = self._extract_generic_contact_data(row)
                                if contact:
                                    contacts.append(contact)
                        else:
                            # Try space-separated
                            df = pd.read_csv(file_path, dtype=str, sep=' ')
                            if len(df.columns) > 1:
                                for _, row in df.iterrows():
                                    contact = self._extract_generic_contact_data(row)
                                    if contact:
                                        contacts.append(contact)
                except Exception as e:
                    print(f"Error parsing TXT file: {e}")
            else:
                # Handle Excel files
                # Suppress OLE2 warnings untuk file Excel yang mungkin memiliki struktur tidak konsisten
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
                    warnings.filterwarnings("ignore", message=".*OLE2 inconsistency.*")
                    warnings.filterwarnings("ignore", message=".*file size.*not.*multiple of sector size.*")
                    
                    xls = pd.ExcelFile(file_path)
                    
                    contact_sheets = [s for s in xls.sheet_names if 'contact' in s.lower()]
                    
                    for sheet_name in contact_sheets:
                        df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, engine='openpyxl')
                        
                        for _, row in df.iterrows():
                            contact = self._extract_generic_contact_data(row)
                            if contact:
                                contacts.append(contact)
                        
        except Exception as e:
            print(f"Error parsing generic file: {e}")
        
        return contacts
    
    def _extract_magnet_contact_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        try:
            display_name = self._clean_text(row.get('Display Name'))
            phone_field = self._clean_text(row.get('Phone Number(s)', ''))
            contact_type = self._clean_text(row.get('Source Account Type(s)', 'Contact'))
            last_contacted = self._parse_timestamp(row.get('Last Time Contacted Date/Time - UTC+00:00 (dd/MM/yyyy)'))
            
            phone_numbers = self._extract_magnet_phone_numbers(phone_field)
            
            if not display_name and not phone_numbers:
                return None
            
            best_phone = self._select_best_phone_number(phone_numbers)
            
            return {
                'display_name': display_name,
                'phone_number': best_phone,
                'type': contact_type or 'Contact',
                'last_time_contacted': last_contacted
            }
        except Exception as e:
            print(f"Error extracting Magnet contact data: {e}")
            return None
    
    def _extract_whatsapp_contact_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        try:
            display_name = self._clean_text(row.get('Display Name'))
            phone_number = self._clean_text(row.get('Phone Number'))
            whatsapp_name = self._clean_text(row.get('WhatsApp Name'))
            contact_type = 'WhatsApp Contact'
            last_contacted = self._parse_timestamp(row.get('Status Updated Date/Time - UTC+00:00 (dd/MM/yyyy)'))
            
            final_name = whatsapp_name or display_name
            
            if not final_name and not phone_number:
                return None
            
            return {
                'display_name': final_name,
                'phone_number': phone_number,
                'type': contact_type,
                'last_time_contacted': last_contacted
            }
        except Exception as e:
            print(f"Error extracting WhatsApp contact data: {e}")
            return None
    
    def _extract_telegram_contact_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        try:
            first_name = self._clean_text(row.get('First Name'))
            last_name = self._clean_text(row.get('Last Name'))
            phone_number = self._clean_text(row.get('Phone Number'))
            contact_type = 'Telegram Contact'
            
            display_name = f"{first_name} {last_name}".strip() if first_name or last_name else None
            
            if not display_name and not phone_number:
                return None
            
            return {
                'display_name': display_name,
                'phone_number': phone_number,
                'type': contact_type,
                'last_time_contacted': None
            }
        except Exception as e:
            print(f"Error extracting Telegram contact data: {e}")
            return None
    
    def _extract_oxygen_contact_data(self, row: pd.Series) -> List[Dict[str, Any]]:
        try:
            contact_field = self._clean_text(row.get('Contact'))
            phones_emails = self._clean_text(row.get('Phones & Emails'))
            contact_type = self._clean_text(row.get('Type', 'Contact'))
            source = self._clean_text(row.get('Source'))
            other_data = self._clean_text(row.get('Other'))
            
            last_time_contacted = self._extract_last_time_contacted_from_other(other_data)
            
            contacts = []
            
            multiple_contacts = self._extract_multiple_contacts_from_phones_emails(phones_emails, contact_type, last_time_contacted)
            
            main_phone_pattern = re.compile(r'Phone number:\s*([+\d\s\-\(\)]+)', re.IGNORECASE)
            main_phone_match = main_phone_pattern.search(phones_emails) if phones_emails else None
            
            if main_phone_match:
                main_phone = main_phone_match.group(1).strip()
                if main_phone and self._is_indonesian_phone_number(main_phone):
                    display_name = self._extract_clean_display_name(contact_field)
                    phone_number = self._normalize_phone_number(main_phone)
                    
                    # Handle generic or missing display names
                    if not display_name or self._is_generic_contact_name(display_name):
                        display_name = "Unknown"
                    
                    if phone_number:
                        contacts.append({
                            'display_name': display_name,
                            'phone_number': phone_number,
                            'type': contact_type or 'Contact',
                            'last_time_contacted': last_time_contacted
                        })
            elif multiple_contacts:
                # Try to get the main contact name from Contact field first
                main_display_name = self._extract_clean_display_name(contact_field)
                
                # If we have a valid main display name, use it for the first contact
                if main_display_name and not self._is_generic_contact_name(main_display_name):
                    # Update the first contact with the main display name
                    if multiple_contacts:
                        multiple_contacts[0]['display_name'] = main_display_name
                
                contacts.extend(multiple_contacts)
                
                contact_from_field = self._extract_contact_from_contact_field(contact_field, contact_type, last_time_contacted)
                if contact_from_field:
                    is_duplicate = False
                    for existing_contact in contacts:
                        if (existing_contact.get('display_name') == contact_from_field.get('display_name') and
                            existing_contact.get('phone_number') == contact_from_field.get('phone_number')):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        contacts.append(contact_from_field)
            else:
                display_name = self._extract_clean_display_name(contact_field)
                phone_number = self._extract_clean_phone_number(phones_emails)
                
                if not display_name or (display_name and (self._is_phone_number_only(display_name) or self._is_generic_contact_name(display_name))):
                    if phone_number:
                        display_name = "Unknown"
                    else:
                        return contacts  # Return empty list
                
                # Jika phone_number kosong, coba ambil dari display_name
                if not phone_number and display_name:
                    phone_from_name = self._extract_phone_numbers(display_name)
                    if phone_from_name:
                        phone_number = phone_from_name[0]
                        display_name = "Unknown"
                
                # Only add contact if it has a phone number (skip NULL phone numbers)
                if phone_number:
                    contacts.append({
                        'display_name': display_name,
                        'phone_number': phone_number,
                        'type': contact_type or 'Contact',
                        'last_time_contacted': last_time_contacted
                    })
            
            return contacts
        except Exception as e:
            print(f"Error extracting Oxygen contact data: {e}")
            return []
    
    def _extract_generic_contact_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        try:
            # Try to find common field names
            display_name = None
            phone_number = None
            contact_type = 'Contact'
            
            for col in row.index:
                col_lower = col.lower()
                if 'name' in col_lower and not display_name:
                    display_name = self._clean_text(row.get(col))
                elif 'phone' in col_lower and not phone_number:
                    phone_number = self._clean_text(row.get(col))
                elif 'type' in col_lower:
                    contact_type = self._clean_text(row.get(col)) or 'Contact'
            
            if not display_name and not phone_number:
                return None
            
            return {
                'display_name': display_name,
                'phone_number': phone_number,
                'type': contact_type,
                'last_time_contacted': None
            }
        except Exception as e:
            print(f"Error extracting generic contact data: {e}")
            return None
    


    def _clean_text(self, text: Any) -> Optional[str]:
        if pd.isna(text) or text is None:
            return None
        
        text = str(text).strip()
        if text.lower() in ['nan', 'none', '']:
            return None
        
        return text
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        if not text or pd.isna(text) or text is None:
            return []
        
        text = str(text)
        phone_numbers = []
        
        matches = self.phone_pattern.findall(text)
        for match in matches:
            country_code, number = match
            if country_code == '+62':
                phone_numbers.append(f"+62{number}")
            elif country_code == '62':
                phone_numbers.append(f"+62{number}")
            elif country_code == '0':
                phone_numbers.append(f"+62{number}")
            # Skip non-Indonesian phone numbers
        
        spaced_patterns = [
            r'(\+?62\s*\d{2,3}\s*\d{3,4}\s*\d{3,4})',
            r'(0\d{2,3}\s*\d{3,4}\s*\d{3,4})',
            r'(\+?62\s*\d{2,3}[-]\d{3,4}[-]\d{3,4})',
            r'(0\d{2,3}[-]\d{3,4}[-]\d{3,4})',
        ]
        
        for pattern in spaced_patterns:
            spaced_numbers = re.findall(pattern, text)
            for num in spaced_numbers:
                
                clean_num = re.sub(r'[\s\-]+', '', num) if num else ''
                if clean_num.startswith('+62'):
                    phone_numbers.append(clean_num)
                elif clean_num.startswith('62'):
                    phone_numbers.append(f"+{clean_num}")
                elif clean_num.startswith('0'):
                    phone_numbers.append(f"+62{clean_num[1:]}")
        
        
        partial_pattern = r'(\d{3,4})\s+(\d{3,4})'
        partial_matches = re.findall(partial_pattern, text)
        for part1, part2 in partial_matches:
            combined = part1 + part2
            if len(combined) >= 10:
                if part1.startswith('0'):
                    phone_numbers.append(f"+62{combined[1:]}")
                elif part1.startswith('62'):
                    phone_numbers.append(f"+{combined}")
                else:
                    phone_numbers.append(f"+62{combined}")
        
        simple_numbers = re.findall(r'\b\d{8,13}\b', text)
        for num in simple_numbers:
            if len(num) >= 10:
                if num.startswith('0'):
                    phone_numbers.append(f"+62{num[1:]}")
                elif num.startswith('62'):
                    
                    phone_numbers.append(f"+62{num}")
                
        
        short_numbers = re.findall(r'\b\d{3,7}\b', text)
        for num in short_numbers:
            if len(num) >= 3:
                phone_numbers.append(num)
        
        return list(set(phone_numbers))
    
    def _extract_emails(self, text: str) -> List[str]:
        if not text:
            return []
        
        emails = self.email_pattern.findall(text)
        return list(set(emails))
    
    def _extract_primary_name(self, contact_field: str) -> Optional[str]:
        if not contact_field:
            return None
        
        lines = contact_field.split('\n')
        primary_name = lines[0].strip()
        
        prefixes_to_remove = ['Nickname:', 'First name:', 'Last name:']
        for prefix in prefixes_to_remove:
            if primary_name.startswith(prefix):
                primary_name = primary_name[len(prefix):].strip()
        
        return primary_name if primary_name else None
    
    def _extract_clean_display_name(self, contact_field: str) -> Optional[str]:
        if not contact_field or pd.isna(contact_field) or contact_field is None:
            return None
        
        lines = contact_field.split('\n')
        primary_name = lines[0].strip()
        
        prefixes_to_remove = ['Nickname:', 'First name:', 'Last name:']
        for prefix in prefixes_to_remove:
            if primary_name.startswith(prefix):
                primary_name = primary_name[len(prefix):].strip()
        
        if self._is_generic_contact_name(primary_name) or self._is_phone_number_only(primary_name):
            for line in lines[1:]:
                line = line.strip()
                if line and not self._is_phone_number_only(line) and not self._is_generic_contact_name(line):
                    # Remove prefixes
                    for prefix in prefixes_to_remove:
                        if line.startswith(prefix):
                            line = line[len(prefix):].strip()
                            break
                    if line and not self._is_phone_number_only(line) and not self._is_generic_contact_name(line):
                        return line
            return None
        
        return primary_name if primary_name else None
    
    def _extract_clean_phone_number(self, phones_emails: str) -> Optional[str]:
        if not phones_emails or pd.isna(phones_emails) or phones_emails is None:
            return None
        
        phone_patterns = [
            re.compile(r'Phone number:\s*([+\d\s\-\(\)]+)', re.IGNORECASE),
            re.compile(r'Mobile:\s*([+\d\s\-\(\)]+)', re.IGNORECASE),
            re.compile(r'Phone:\s*([+\d\s\-\(\)]+)', re.IGNORECASE),
        ]
        
        for phone_pattern in phone_patterns:
            match = phone_pattern.search(phones_emails) if phones_emails else None
            if match:
                phone = match.group(1).strip()
                if phone and self._is_indonesian_phone_number(phone):
                    return self._normalize_phone_number(phone)
        
        phone_numbers = self._extract_phone_numbers(phones_emails)
        
        if not phone_numbers:
            return None
        
        valid_phones = []
        for phone in phone_numbers:
            if phone and len(phone.replace('+', '').replace('-', '').replace(' ', '') if phone else '') >= 3 and self._is_indonesian_phone_number(phone):
                valid_phones.append(phone)
        
        if not valid_phones:
            return None
        
        def phone_priority(phone):
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '') if phone else ''
            if clean_phone.startswith('62') and len(clean_phone) >= 10:
                return (1, len(clean_phone))
            elif clean_phone.startswith('08') and len(clean_phone) >= 10:
                return (2, len(clean_phone))  # Local format
            elif clean_phone.isdigit() and 3 <= len(clean_phone) <= 7:
                return (3, len(clean_phone))
            else:
                return (4, len(clean_phone))
        
        valid_phones.sort(key=phone_priority)
        return valid_phones[0]
    
    def _is_indonesian_phone_number(self, phone_number: str) -> bool:
        if not phone_number or pd.isna(phone_number) or phone_number is None:
            return False
        
        phone_number = str(phone_number).strip()
        
        if self._is_social_media_id(phone_number):
            return False
        
        phone_clean = phone_number.replace('+', '').replace('-', '').replace(' ', '') if phone_number else ''
        
        if phone_clean.startswith('62') or phone_clean.startswith('08'):
            return True
        
        if phone_clean.isdigit() and 3 <= len(phone_clean) <= 7:
            return True
        
        return False
    
    def _extract_multiple_contacts_from_phones_emails(self, phones_emails: str, contact_type: str, last_time_contacted: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if not phones_emails or pd.isna(phones_emails) or phones_emails is None:
            return []
        
        contacts = []
        
        lines = phones_emails.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    name_part = parts[0].strip()
                    phone_part = parts[1].strip()
                    
                    phone_numbers = self._extract_phone_numbers(phone_part) if phone_part else []
                    
                    if phone_numbers:
                        valid_phones = []
                        for phone in phone_numbers:
                            if phone and len(phone.replace('+', '').replace('-', '').replace(' ', '') if phone else '') >= 3 and self._is_indonesian_phone_number(phone):
                                valid_phones.append(phone)
                        
                        if not valid_phones:
                            continue
                        
                        def phone_priority(phone):
                            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '') if phone else ''
                            if clean_phone.startswith('62') and len(clean_phone) >= 10:
                                return (1, len(clean_phone))
                            elif clean_phone.startswith('08') and len(clean_phone) >= 10:
                                return (2, len(clean_phone))
                            elif clean_phone.isdigit() and 3 <= len(clean_phone) <= 7:
                                return (3, len(clean_phone))
                            else:
                                return (4, len(clean_phone))
                        
                        valid_phones.sort(key=phone_priority)
                        phone_number = valid_phones[0]
                        
                        display_name = name_part
                        
                        if (self._is_social_media_id(line) or 
                            name_part.lower() in ['mobile', 'phone number', 'email', 'phone'] or
                            'id' in name_part.lower()):
                            continue
                        
                        if self._is_phone_number_only(display_name):
                            display_name = "Unknown"
                        
                        if phone_number:
                            contacts.append({
                                'display_name': display_name,
                                'phone_number': phone_number,
                                'type': contact_type or 'Contact',
                                'last_time_contacted': last_time_contacted
                            })
        
        return contacts
    
    def _extract_contact_from_contact_field(self, contact_field: str, contact_type: str, last_time_contacted: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        if not contact_field or pd.isna(contact_field) or contact_field is None:
            return None
        
        lines = contact_field.split('\n')
        if not lines:
            return None
        
        first_line = lines[0].strip()
        
        phone_numbers = self._extract_phone_numbers(first_line) if first_line else []
        if not phone_numbers:
            return None
        
        valid_phones = []
        for phone in phone_numbers:
            if phone and len(phone.replace('+', '').replace('-', '').replace(' ', '') if phone else '') >= 3 and self._is_indonesian_phone_number(phone):
                valid_phones.append(phone)
        
        if not valid_phones:
            return None
        
        def phone_priority(phone):
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '') if phone else ''
            if clean_phone.startswith('62') and len(clean_phone) >= 10:
                return (1, len(clean_phone))  # Full Indonesian numbers
            elif clean_phone.startswith('08') and len(clean_phone) >= 10:
                return (2, len(clean_phone))  # Local format
            elif clean_phone.isdigit() and 3 <= len(clean_phone) <= 7:
                return (3, len(clean_phone))  # Service numbers
            else:
                return (4, len(clean_phone))  # Others
        
        valid_phones.sort(key=phone_priority)
        phone_number = valid_phones[0]
        
        display_name = None
        for line in lines[1:]:
            line = line.strip()
            if line.startswith('First name:'):
                display_name = line.replace('First name:', '').strip() if line else ''
                break
            elif line and not self._is_phone_number_only(line):
                display_name = line
                break
        
        if not display_name:
            display_name = "Unknown"
        
        if phone_number:
            return {
                'display_name': display_name,
                'phone_number': phone_number,
                'type': contact_type or 'Contact',
                'last_time_contacted': last_time_contacted
            }
        
        return None
    
    def _extract_last_time_contacted_from_other(self, other_data: str) -> Optional[datetime]:
        if not other_data or pd.isna(other_data) or other_data is None:
            return None
        
        other_data = str(other_data)
        
        created_pattern = r'Created:\s*(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})'
        match = re.search(created_pattern, other_data) if other_data else None
        
        if match:
            created_str = match.group(1)
            try:
                # Parse DD/MM/YYYY HH:MM:SS format
                return datetime.strptime(created_str, '%d/%m/%Y %H:%M:%S')
            except ValueError:
                # Try alternative formats if needed
                try:
                    return datetime.strptime(created_str, '%d/%m/%Y %H:%M:%S')
                except ValueError:
                    return None
        
        return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        if not timestamp_str or pd.isna(timestamp_str):
            return None
        
        try:
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(timestamp_str), fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def normalize_contacts(self, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        seen_phones = set()
        
        normalized_contacts = []
        for contact in contacts:
            if not contact.get('phone_number'):
                continue
                
            if contact.get('phone_number'):
                contact['phone_number'] = self._normalize_phone_number(contact['phone_number'])
            
            if contact.get('display_name'):
                contact['display_name'] = self._normalize_display_name(contact['display_name'])
            
            phone = contact.get('phone_number', '')
            if not phone:
                continue
                
            normalized_contacts.append(contact)
        
        for contact in normalized_contacts:
            phone = contact.get('phone_number', '')
            
            if phone in seen_phones:
                existing_contact = next((c for c in normalized if c.get('phone_number') == phone), None)
                if existing_contact:
                    if self._is_better_contact(contact, existing_contact):
                        normalized.remove(existing_contact)
                        normalized.append(contact)
                continue
            
            seen_phones.add(phone)
            normalized.append(contact)
        
        return normalized
    
    def _is_better_contact(self, new_contact: Dict[str, Any], existing_contact: Dict[str, Any]) -> bool:
        type_priority = {
            'WhatsApp Contact': 1,
            'Contact': 2,
            'com.whatsapp': 3,
            'com.lge.sync': 4,
            'com.android.contacts.sim': 5,
            'Telegram Contact': 6
        }
        
        new_type = new_contact.get('type', '')
        existing_type = existing_contact.get('type', '')
        
        new_priority = type_priority.get(new_type, 999)
        existing_priority = type_priority.get(existing_type, 999)
        
        if new_priority < existing_priority:
            return True
        elif new_priority > existing_priority:
            return False
        
        new_last_contacted = new_contact.get('last_time_contacted')
        existing_last_contacted = existing_contact.get('last_time_contacted')
        
        if new_last_contacted and not existing_last_contacted:
            return True
        elif not new_last_contacted and existing_last_contacted:
            return False
        
        new_name = new_contact.get('display_name', '')
        existing_name = existing_contact.get('display_name', '')
        
        return len(new_name) > len(existing_name)
    
    def _normalize_phone_number(self, phone: str) -> str:
        if not phone or pd.isna(phone) or phone is None:
            return phone
        
        cleaned = re.sub(r'[^\d+]', '', phone) if phone else ''
        
        if cleaned.startswith('+62'):
            return cleaned
        elif cleaned.startswith('62'):
            return f"+{cleaned}"
        elif cleaned.startswith('0'):
            return f"+62{cleaned[1:]}"
        else:
            return cleaned
    
    def _normalize_display_name(self, name: str) -> str:
        if not name or pd.isna(name) or name is None:
            return name
        
        name = re.sub(r'\s+', ' ', name.strip()) if name else ''

        if self._is_phone_number_only(name):
            return "Unknown"
        
        return ' '.join(word.capitalize() for word in name.split())
    
    def _is_phone_number_only(self, text: str) -> bool:
        if not text or pd.isna(text) or text is None:
            return False
        
        cleaned_text = text.strip()
        
        if cleaned_text and self.phone_only_pattern.match(cleaned_text):
            digit_count = sum(1 for c in cleaned_text if c.isdigit())
            total_chars = len(cleaned_text.replace(' ', '')) if cleaned_text else 0
            
            if total_chars > 0 and (digit_count / total_chars) > 0.7:
                return True
        
        return False
    
    def _is_generic_contact_name(self, name: str) -> bool:
        if not name or pd.isna(name) or name is None:
            return True
        
        name = str(name).strip().lower()
        
        generic_names = [
            'contact', 'unknown', 'n/a', 'na', 'phone', 'mobile', 'telephone',
            'call', 'message', 'chat', 'conversation', 'user', 'person',
            'friend', 'family', 'work', 'home', 'office', 'business', 'client',
            'customer', 'member', 'guest', 'visitor', 'anonymous', 'private',
            'public', 'group', 'team', 'department', 'company', 'organization',
            'institution', 'service', 'support', 'help', 'info', 'admin',
            'administrator', 'system', 'default', 'test', 'sample', 'example',
            'dummy', 'placeholder', 'temp', 'temporary', 'new', 'old', 'deleted',
            'removed', 'blocked', 'spam', 'junk', 'trash', 'archive', 'backup'
        ]
        
        return name in generic_names
    
    def _is_social_media_id(self, text: str) -> bool:
        if not text or pd.isna(text) or text is None:
            return False
        
        text = str(text).strip()
        
        social_media_patterns = [
            r'Telegram ID:\s*\w+',
            r'Instagram ID:\s*\w+',
            r'WhatsApp ID:\s*\w+',
            r'Facebook ID:\s*\w+',
            r'Google ID:\s*\w+',
            r'Twitter ID:\s*\w+',
            r'LinkedIn ID:\s*\w+',
            r'Snapchat ID:\s*\w+',
            r'TikTok ID:\s*\w+',
            r'Discord ID:\s*\w+',
            r'Skype ID:\s*\w+',
            r'Viber ID:\s*\w+',
            r'Line ID:\s*\w+',
            r'WeChat ID:\s*\w+',
            r'Signal ID:\s*\w+',
            r'Telegram\s+ID',
            r'Instagram\s+ID',
            r'WhatsApp\s+ID',
            r'Facebook\s+ID',
            r'Google\s+ID',
            r'Twitter\s+ID',
            r'LinkedIn\s+ID',
            r'Snapchat\s+ID',
            r'TikTok\s+ID',
            r'Discord\s+ID',
            r'Skype\s+ID',
            r'Viber\s+ID',
            r'Line\s+ID',
            r'WeChat\s+ID',
            r'Signal\s+ID',
        ]
        
        for pattern in social_media_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_magnet_phone_numbers(self, phone_field: str) -> List[str]:
        if not phone_field or pd.isna(phone_field) or phone_field is None:
            return []
        
        phone_field = str(phone_field).strip()
        phone_numbers = []
        
        parts = phone_field.split(',')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            if ':' in part:
                part = part.split(':', 1)[1].strip()
            
            numbers = self._extract_phone_numbers(part)
            phone_numbers.extend(numbers)
        
        return phone_numbers
    
    def _select_best_phone_number(self, phone_numbers: List[str]) -> Optional[str]:
        if not phone_numbers:
            return None
        
        valid_phones = []
        for phone in phone_numbers:
            if phone and len(phone.replace('+', '').replace('-', '').replace(' ', '') if phone else '') >= 3:
                valid_phones.append(phone)
        
        if not valid_phones:
            return None
        
        def phone_priority(phone):
            clean_phone = phone.replace('+', '').replace('-', '').replace(' ', '') if phone else ''
            if clean_phone.startswith('62') and len(clean_phone) >= 10:
                return (1, len(clean_phone))
            elif clean_phone.startswith('08') and len(clean_phone) >= 10:
                return (2, len(clean_phone))
            elif clean_phone.isdigit() and 3 <= len(clean_phone) <= 7:
                return (3, len(clean_phone))
            else:
                return (4, len(clean_phone))
        
        valid_phones.sort(key=phone_priority)
        return valid_phones[0]

contact_parser = ContactParser()
