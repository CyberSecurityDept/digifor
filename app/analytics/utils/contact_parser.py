import pandas as pd
import warnings
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.analytics.device_management.models import Contact, Call

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class ContactParser:
    """Parser for contact and call data from various forensic tools"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def parse_axiom_contacts(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse contacts from Axiom file"""
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            contacts_sheet = None
            for sheet_name in xls.sheet_names:
                if 'contact' in sheet_name.lower():
                    contacts_sheet = sheet_name
                    break
            
            if not contacts_sheet:
                print("No contacts sheet found in Axiom file")
                return results
            
            df = pd.read_excel(file_path, sheet_name=contacts_sheet, engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                contact_data = {
                    "file_id": file_id,
                    "display_name": str(row.get('Display Name', '')),
                    "phone_number": str(row.get('Phone Number(s)', '')),
                    "email": str(row.get('Email Address(es)', '')),
                    "type": str(row.get('Source Account Type(s)', '')),
                    "last_time_contacted": str(row.get('Last Time Contacted Date/Time - UTC+00:00 (dd/MM/yyyy)', ''))
                }
                
                if contact_data["display_name"] and contact_data["display_name"] != 'nan':
                    results.append(contact_data)
            
            for contact in results:
                existing = (
                    self.db.query(Contact)
                    .filter(
                        Contact.display_name == contact["display_name"],
                        Contact.file_id == file_id,
                        Contact.phone_number == contact["phone_number"]
                    )
                    .first()
                )
                if not existing:
                    self.db.add(Contact(**contact))
            
            self.db.commit()
            print(f"Successfully saved {len(results)} contacts to database")
                    
        except Exception as e:
            print(f"Error parsing Axiom contacts: {e}")
            self.db.rollback()
            raise e
        
        return results
    
    def parse_axiom_calls(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse calls from Axiom file"""
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            calls_sheet = None
            for sheet_name in xls.sheet_names:
                if 'call' in sheet_name.lower():
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
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')

            if 'Contacts' not in xls.sheet_names:
                print("No Contacts sheet found in Cellebrite file")
                return results

            df = pd.read_excel(file_path, sheet_name='Contacts', engine='openpyxl', dtype=str)
            
            for _, row in df.iterrows():
                contact_data = {
                    "file_id": file_id,
                    "display_name": str(row.get('Contacts (40)', '')).strip(),
                    "phone_number": str(row.get('Unnamed: 8', '')).strip(),
                    "email": "",
                    "type": str(row.get('Unnamed: 20', '')).strip(),
                    "last_time_contacted": str(row.get('Unnamed: 16', '')).strip()
                }

                if contact_data["display_name"] and contact_data["display_name"].lower() != 'nan':
                    results.append(contact_data)

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
            print(f"Successfully saved {len(results)} Cellebrite contacts to database")
                    
        except Exception as e:
            print(f"Error parsing Cellebrite contacts: {e}")
            self.db.rollback()
            raise e

        return results

    
    def parse_cellebrite_calls(self, file_path: str, file_id: int) -> List[Dict[str, Any]]:
        """Parse calls from Cellebrite file"""
        results = []
        
        try:
            xls = pd.ExcelFile(file_path, engine='openpyxl')
            
            calls_sheet = None
            for sheet_name in xls.sheet_names:
                if 'call' in sheet_name.lower():
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
        """Parse contacts from Oxygen file"""
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
            for sheet_name in xls.sheet_names:
                if 'contact' in sheet_name.lower():
                    contacts_sheet = sheet_name
                    break
            
            if not contacts_sheet:
                print("No contacts sheet found in Oxygen file")
                return results
            
            df = pd.read_excel(file_path, sheet_name=contacts_sheet, dtype=str, engine=engine)
            
            for _, row in df.iterrows():
                contact_data = {
                    "file_id": file_id,
                    "display_name": str(row.get('Name', '')),
                    "phone_number": str(row.get('Phone', '')),
                    "email": str(row.get('Email', '')),
                    "type": str(row.get('Type', '')),
                    "last_time_contacted": str(row.get('Last Contacted', ''))
                }
                
                if contact_data["display_name"] and contact_data["display_name"] != 'nan':
                    results.append(contact_data)
            
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
            print(f"Successfully saved {len(results)} Oxygen contacts to database")
            
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
                if 'call' in sheet_name.lower():
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