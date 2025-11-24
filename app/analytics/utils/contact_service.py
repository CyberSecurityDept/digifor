#!/usr/bin/env python3
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.analytics.device_management.models import Contact, Device
from app.analytics.utils.contact_parser import ContactParser
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ContactService:
    
    def __init__(self):
        self.parser = None  # type: ignore
    
    def parse_and_save_contacts(self, file_path: Path, device_id: int) -> Dict[str, Any]:  # type: ignore[reportAttributeAccessIssue]
        try:
            contacts = self.parser.parse_contacts_from_file(file_path)  # type: ignore[reportAttributeAccessIssue]
            
            if not contacts:
                return {
                    "success": False,
                    "message": "No contacts found in file",
                    "contacts_parsed": 0,
                    "contacts_saved": 0
                }
            
            normalized_contacts = self.parser.normalize_contacts(contacts)  # type: ignore[reportAttributeAccessIssue]
            
            result = self._save_contacts_to_db(normalized_contacts, device_id)
            saved_count = result.get('saved_count', 0)
            skipped_count = result.get('skipped_count', 0)
            
            return {
                "success": True,
                "message": f"Successfully parsed and saved {saved_count} contacts, skipped {skipped_count} duplicates",
                "contacts_parsed": len(contacts),
                "contacts_saved": saved_count,
                "contacts_skipped": skipped_count,
                "contacts_normalized": len(normalized_contacts)
            }
            
        except Exception as e:
            logger.error(f"Error parsing and saving contacts: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "contacts_parsed": 0,
                "contacts_saved": 0
            }
    
    def _save_contacts_to_db(self, contacts: List[Dict[str, Any]], device_id: int) -> Dict[str, int]:
        db: Session = SessionLocal()
        saved_count = 0
        skipped_count = 0
        
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                raise ValueError(f"Device with ID {device_id} not found")
            
            for contact_data in contacts:
                try:
                    phone_number = contact_data.get('phone_number')
                    display_name = contact_data.get('display_name')
                    contact_type = contact_data.get('type', 'Contact')
                    
                    if not phone_number:
                        logger.warning(f"Skipping contact '{display_name}' - no phone number")
                        skipped_count += 1
                        continue
                    
                    existing_contact = db.query(Contact).filter(
                        Contact.file_id == device.file_id,
                        Contact.phone_number == phone_number
                    ).first()
                    
                    if existing_contact:
                        logger.info(f"Skipping duplicate contact: {display_name} ({phone_number}) - already exists")
                        skipped_count += 1
                        continue
                    
                    contact = Contact(
                        file_id=device.file_id,
                        display_name=display_name,
                        phone_number=phone_number,
                        type=contact_type,
                        last_time_contacted=contact_data.get('last_time_contacted')
                    )
                    
                    db.add(contact)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving contact {contact_data.get('display_name', 'Unknown')}: {e}")
                    skipped_count += 1
                    continue
            
            db.commit()
            logger.info(f"Successfully saved {saved_count} contacts to database, skipped {skipped_count} duplicates")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving contacts to database: {e}")
            raise
        finally:
            db.close()
        
        return {
            "saved_count": saved_count,
            "skipped_count": skipped_count
        }
    
    def get_contacts_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        db: Session = SessionLocal()
        
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return []
            
            contacts = db.query(Contact).filter(Contact.file_id == device.file_id).all()
            
            result = []
            for contact in contacts:
                result.append({
                    "id": contact.id,
                    "file_id": contact.file_id,
                    "display_name": contact.display_name,
                    "phone_number": contact.phone_number,
                    "type": contact.type,
                    "last_time_contacted": contact.last_time_contacted,
                    "created_at": contact.created_at,
                    "updated_at": contact.updated_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting contacts by device: {e}")
            return []
        finally:
            db.close()
    
    def get_contact_statistics(self, device_id: int) -> Dict[str, Any]:
        db: Session = SessionLocal()
        
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                return {
                    "total_contacts": 0,
                    "unique_phone_numbers": 0,
                    "contacts_with_names": 0
                }
            
            contacts = db.query(Contact).filter(Contact.file_id == device.file_id).all()
            
            total_contacts = len(contacts)
            
            type_counts = {}
            for contact in contacts:
                contact_type = contact.type or 'Unknown'
                type_counts[contact_type] = type_counts.get(contact_type, 0) + 1
            
            contacts_with_phone = sum(1 for c in contacts if c.phone_number is not None)
            
            contacts_with_last_contacted = sum(1 for c in contacts if c.last_time_contacted is not None)
            
            return {
                "total_contacts": total_contacts,
                "contacts_with_phone": contacts_with_phone,
                "contacts_with_last_contacted": contacts_with_last_contacted,
                "type_distribution": type_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting contact statistics: {e}")
            return {
                "total_contacts": 0,
                "contacts_with_phone": 0,
                "contacts_with_last_contacted": 0,
                "type_distribution": {}
            }
        finally:
            db.close()

contact_service = ContactService()
