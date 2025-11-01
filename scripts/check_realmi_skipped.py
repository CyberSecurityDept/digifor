#!/usr/bin/env python3
"""
Script untuk menganalisis data yang terskip dari file Realmi Hikari.xls
"""
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

file_path = 'sample_social_mediaa/Realmi Hikari/Oxygen/Realmi Hikari.xls'

def analyze_skipped_data():
    try:
        print("="*80)
        print("ANALYZING REALMI HIKARI FILE - SKIPPED DATA")
        print("="*80)
        
        # Read Excel file
        xls = pd.ExcelFile(file_path, engine='xlrd')
        print(f"\n📊 Sheets available: {len(xls.sheet_names)}")
        
        # Read Contacts sheet
        df = pd.read_excel(file_path, sheet_name='Contacts ', engine='xlrd', dtype=str)
        print(f"\n📋 Contacts sheet: {len(df)} total rows")
        
        # Analyze WhatsApp skipped rows
        print("\n" + "="*80)
        print("WHATSAPP ANALYSIS")
        print("="*80)
        whatsapp_rows = df[df['Source'].str.contains('WhatsApp Messenger', case=False, na=False)]
        print(f"Total WhatsApp rows: {len(whatsapp_rows)}")
        print(f"Expected valid: 9")
        print(f"Expected skipped: {len(whatsapp_rows) - 9}")
        
        skipped_whatsapp = []
        for idx, (row_idx, row) in enumerate(whatsapp_rows.iterrows(), 1):
            type_field = str(row.get('Type', '') or '').lower().strip()
            contact_field = str(row.get('Contact', '') or '').strip()
            internet_field = str(row.get('Internet', '') or '').strip()
            phones_emails_field = str(row.get('Phones & Emails', '') or '').strip()
            
            # Check if this would be skipped by type
            is_account_type = type_field in ["account", "account(merged)", "account (merged)", "accounts"]
            is_contact_type = type_field in ["contact", "contact(merged)", "contact (merged)", "contacts"]
            
            if not (is_account_type or is_contact_type):
                skipped_whatsapp.append({
                    'row': row_idx,
                    'type': row.get('Type'),
                    'reason': f"Type='{row.get('Type')}' (not Account/Contact)",
                    'contact': contact_field[:100],
                    'internet': internet_field[:100],
                    'phones': phones_emails_field[:100]
                })
                continue
            
            # Simulate extraction (simplified)
            whatsapp_id = None
            phone_number = None
            
            # Extract from Internet
            if internet_field and 'whatsapp id:' in internet_field.lower():
                import re
                match = re.search(r'WhatsApp\s+ID[:\s]+([^\s@]+@s\.whatsapp\.net)', internet_field, re.IGNORECASE)
                if match:
                    whatsapp_id = match.group(1).strip()
            
            # Extract from Phones & Emails
            if phones_emails_field:
                import re
                # Try phone number
                phone_match = re.search(r'Phone\s+number[:\s]+(\d+)', phones_emails_field, re.IGNORECASE)
                if phone_match:
                    phone_val = phone_match.group(1).strip()
                    # Validate phone number (min 8 digits)
                    if phone_val.isdigit() and len(phone_val) >= 8:
                        phone_number = phone_val
                
                # Try WhatsApp ID
                if not whatsapp_id:
                    wa_match = re.search(r'WhatsApp\s+ID[:\s]+([^\s@]+@s\.whatsapp\.net)', phones_emails_field, re.IGNORECASE)
                    if wa_match:
                        whatsapp_id = wa_match.group(1).strip()
            
            # Check if this would be skipped
            if not whatsapp_id and not phone_number:
                skipped_whatsapp.append({
                    'row': row_idx,
                    'type': row.get('Type'),
                    'reason': "No whatsapp_id or phone_number (or phone_number too short)",
                    'contact': contact_field[:100],
                    'internet': internet_field[:100],
                    'phones': phones_emails_field[:100],
                    'extracted_whatsapp_id': whatsapp_id,
                    'extracted_phone': phone_number
                })
        
        print(f"\n📊 WhatsApp skipped rows: {len(skipped_whatsapp)}")
        for skip in skipped_whatsapp:
            print(f"\n--- Row {skip['row']} ---")
            print(f"Type: {skip['type']}")
            print(f"Reason: {skip['reason']}")
            print(f"Contact: {skip['contact']}")
            print(f"Internet: {skip['internet']}")
            print(f"Phones & Emails: {skip['phones']}")
            if 'extracted_whatsapp_id' in skip:
                print(f"Extracted WhatsApp ID: {skip['extracted_whatsapp_id']}")
                print(f"Extracted Phone: {skip['extracted_phone']}")
        
        # Analyze Telegram skipped rows
        print("\n" + "="*80)
        print("TELEGRAM ANALYSIS")
        print("="*80)
        telegram_rows = df[df['Source'].str.contains('Telegram', case=False, na=False)]
        print(f"Total Telegram rows: {len(telegram_rows)}")
        print(f"Expected valid: 1094")
        print(f"Expected skipped: {len(telegram_rows) - 1094}")
        
        skipped_telegram = []
        for idx, (row_idx, row) in enumerate(telegram_rows.iterrows(), 1):
            type_field = str(row.get('Type', '') or '').lower().strip()
            contact_field = str(row.get('Contact', '') or '').strip()
            internet_field = str(row.get('Internet', '') or '').strip()
            
            # Check if this would be skipped by type
            is_account_type = type_field in ["account", "account(merged)", "account (merged)", "accounts"]
            is_contact_type = type_field in ["contact", "contact(merged)", "contact (merged)", "contacts"]
            is_group_type = type_field in ["group", "group(merged)", "group (merged)", "groups"]
            
            if not (is_account_type or is_contact_type or is_group_type):
                skipped_telegram.append({
                    'row': row_idx,
                    'type': row.get('Type'),
                    'reason': f"Type='{row.get('Type')}' (not Account/Contact/Group)",
                    'contact': contact_field[:100],
                    'internet': internet_field[:100]
                })
                continue
            
            # Simulate extraction
            account_name = None
            telegram_id = None
            
            # Extract account_name from nickname
            if contact_field and 'Nickname:' in contact_field:
                import re
                match = re.search(r"Nickname[:\s]+([^\n]+)", contact_field, re.IGNORECASE)
                if match:
                    account_name = match.group(1).strip()
            
            # If no nickname, try from contact directly
            if not account_name and contact_field:
                contact_str = str(contact_field).strip()
                if '\n' in contact_str:
                    contact_str = contact_str.split('\n')[0].strip()
                if contact_str.lower().startswith('contact:'):
                    contact_str = contact_str.split(':', 1)[1].strip()
                
                if (contact_str and len(contact_str) > 1 and len(contact_str) < 50 and
                    'nickname:' not in contact_str.lower() and
                    not contact_str.isdigit() and '@' not in contact_str and 
                    '/' not in contact_str and '\\' not in contact_str):
                    account_name = contact_str
            
            # Extract telegram_id
            if internet_field and internet_field.lower() not in ['nan', 'none', 'null', '']:
                import re
                if 'Telegram ID:' in internet_field:
                    parts = internet_field.split('Telegram ID:')
                    if len(parts) > 1:
                        telegram_id = parts[1].strip().split()[0]  # Take first part
            
            # Check validation (simplified)
            if account_name:
                # Check if account_name is invalid
                if len(account_name) <= 1:
                    # Invalid, but might have telegram_id
                    if not telegram_id:
                        skipped_telegram.append({
                            'row': row_idx,
                            'type': row.get('Type'),
                            'reason': f"account_name too short: '{account_name}' and no telegram_id",
                            'contact': contact_field[:100],
                            'internet': internet_field[:100],
                            'account_name': account_name,
                            'telegram_id': telegram_id
                        })
                        continue
                # Check header/metadata (simplified)
                invalid_chars = ['♣️', 'ㅤ', '🌘']
                if account_name in invalid_chars:
                    if not telegram_id:
                        skipped_telegram.append({
                            'row': row_idx,
                            'type': row.get('Type'),
                            'reason': f"account_name appears to be header/metadata: '{account_name}' and no telegram_id",
                            'contact': contact_field[:100],
                            'internet': internet_field[:100],
                            'account_name': account_name,
                            'telegram_id': telegram_id
                        })
                        continue
            
            # If no account_name and no telegram_id
            if not account_name and not telegram_id:
                skipped_telegram.append({
                    'row': row_idx,
                    'type': row.get('Type'),
                    'reason': "No account_name and no telegram_id",
                    'contact': contact_field[:100],
                    'internet': internet_field[:100]
                })
        
        print(f"\n📊 Telegram skipped rows: {len(skipped_telegram)}")
        for skip in skipped_telegram[:20]:  # Show first 20
            print(f"\n--- Row {skip['row']} ---")
            print(f"Type: {skip['type']}")
            print(f"Reason: {skip['reason']}")
            print(f"Contact: {skip['contact']}")
            print(f"Internet: {skip['internet']}")
            if 'account_name' in skip:
                print(f"Account Name: {skip['account_name']}")
            if 'telegram_id' in skip:
                print(f"Telegram ID: {skip['telegram_id']}")
        
        if len(skipped_telegram) > 20:
            print(f"\n... and {len(skipped_telegram) - 20} more skipped Telegram rows")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        total_found = len(whatsapp_rows) + len(telegram_rows)
        total_valid = 9 + 1094
        total_skipped = len(skipped_whatsapp) + len(skipped_telegram)
        print(f"Total rows found: {total_found} (WhatsApp: {len(whatsapp_rows)}, Telegram: {len(telegram_rows)})")
        print(f"Total valid: {total_valid} (WhatsApp: 9, Telegram: 1094)")
        print(f"Total skipped: {total_skipped} (WhatsApp: {len(skipped_whatsapp)}, Telegram: {len(skipped_telegram)})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_skipped_data()

