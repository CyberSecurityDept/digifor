#!/usr/bin/env python3
"""
Script untuk menganalisis data yang terskip dari parsing
"""
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

file_path = 'sample_social_mediaa/iPhone Hikari/Oxygen/Nurcahya Hikari-Apple UFED file syst-22102025152543.xls'

def analyze_skipped_data():
    try:
        print("="*80)
        print("ANALYZING SKIPPED DATA")
        print("="*80)
        
        # Read Excel file
        xls = pd.ExcelFile(file_path, engine='xlrd')
        
        # Read Contacts sheet
        df = pd.read_excel(file_path, sheet_name='Contacts ', engine='xlrd', dtype=str)
        print(f"\n📋 Contacts sheet: {len(df)} total rows")
        
        # Analyze Telegram skipped rows
        print("\n" + "="*80)
        print("TELEGRAM ANALYSIS")
        print("="*80)
        telegram_rows = df[df['Source'].str.contains('Telegram', case=False, na=False)]
        print(f"Total Telegram rows: {len(telegram_rows)}")
        print(f"Expected valid: 33")
        print(f"Expected skipped: {len(telegram_rows) - 33}")
        
        skipped_telegram = []
        for idx, (row_idx, row) in enumerate(telegram_rows.iterrows(), 1):
            type_field = str(row.get('Type', '') or '').lower().strip()
            contact_field = str(row.get('Contact', '') or '').strip()
            internet_field = str(row.get('Internet', '') or '').strip()
            
            # Check if this would be skipped
            is_account_type = type_field in ["account", "account(merged)", "account (merged)", "accounts"]
            is_contact_type = type_field in ["contact", "contact(merged)", "contact (merged)", "contacts"]
            
            if not (is_account_type or is_contact_type):
                skipped_telegram.append({
                    'row': row_idx,
                    'type': row.get('Type'),
                    'reason': f"Type='{row.get('Type')}' (not Account/Contact)",
                    'contact': contact_field[:100],
                    'internet': internet_field[:100]
                })
                continue
            
            # Simulate extraction
            account_name = None
            telegram_id = None
            
            # Extract account_name
            if contact_field:
                if 'Telegram ID:' in contact_field:
                    parts = contact_field.split('Telegram ID:')
                    if len(parts) > 1:
                        account_name = parts[0].strip()
                else:
                    account_name = contact_field.split('\n')[0].strip()
                
                # Check if account_name is invalid
                if account_name:
                    # Check if it's header/metadata
                    if len(account_name) <= 1 or account_name in ['♣️', 'ㅤㅤ']:
                        skipped_telegram.append({
                            'row': row_idx,
                            'type': row.get('Type'),
                            'reason': f"account_name appears to be header/metadata: '{account_name}'",
                            'contact': contact_field[:100],
                            'internet': internet_field[:100]
                        })
                        continue
            
            # Extract telegram_id
            if internet_field and internet_field.lower() not in ['nan', 'none', 'null', '']:
                if 'Telegram ID:' in internet_field:
                    parts = internet_field.split('Telegram ID:')
                    if len(parts) > 1:
                        telegram_id = parts[1].strip()
            
            if not account_name and not telegram_id:
                skipped_telegram.append({
                    'row': row_idx,
                    'type': row.get('Type'),
                    'reason': "No account_name and no telegram_id",
                    'contact': contact_field[:100],
                    'internet': internet_field[:100]
                })
        
        print(f"\n📊 Telegram skipped rows: {len(skipped_telegram)}")
        for skip in skipped_telegram:
            print(f"\n--- Row {skip['row']} ---")
            print(f"Type: {skip['type']}")
            print(f"Reason: {skip['reason']}")
            print(f"Contact: {skip['contact']}")
            print(f"Internet: {skip['internet']}")
        
        # Analyze Twitter/X skipped rows
        print("\n" + "="*80)
        print("TWITTER/X ANALYSIS")
        print("="*80)
        twitter_rows = df[df['Source'].str.contains('Twitter|X', case=False, na=False)]
        print(f"Total Twitter/X rows: {len(twitter_rows)}")
        print(f"Expected valid: 150")
        print(f"Expected skipped: {len(twitter_rows) - 150}")
        
        skipped_twitter = []
        for idx, (row_idx, row) in enumerate(twitter_rows.iterrows(), 1):
            type_field = str(row.get('Type', '') or '').lower().strip()
            contact_field = str(row.get('Contact', '') or '').strip()
            internet_field = str(row.get('Internet', '') or '').strip()
            
            # Check if this would be skipped
            is_account_type = type_field in ["account", "account(merged)", "account (merged)", "accounts"]
            is_contact_type = type_field in ["contact", "contact(merged)", "contact (merged)", "contacts"]
            is_group_type = type_field in ["group", "group(merged)", "group (merged)", "groups"]
            
            if not (is_account_type or is_contact_type or is_group_type):
                skipped_twitter.append({
                    'row': row_idx,
                    'type': row.get('Type'),
                    'reason': f"Type='{row.get('Type')}' (not Account/Contact/Group)",
                    'contact': contact_field[:100],
                    'internet': internet_field[:100]
                })
                continue
            
            # Simulate extraction
            account_name = None
            x_id = None
            
            # Extract account_name from nickname
            if contact_field and 'Nickname:' in contact_field:
                import re
                match = re.search(r"Nickname[:\s]+([^\n]+)", contact_field, re.IGNORECASE)
                if match:
                    account_name = match.group(1).strip()
            
            # If no nickname, try from contact directly
            if not account_name and contact_field:
                contact_str = str(contact_field).strip()
                # Jika multiline, ambil baris pertama saja
                if '\n' in contact_str:
                    contact_str = contact_str.split('\n')[0].strip()
                # Hapus prefix "Contact:" jika ada
                if contact_str.lower().startswith('contact:'):
                    contact_str = contact_str.split(':', 1)[1].strip()
                # Hapus "@" di awal jika ada
                if contact_str.startswith('@'):
                    contact_str = contact_str[1:].strip()
                
                if (contact_str and len(contact_str) > 1 and len(contact_str) < 50 and
                    'nickname:' not in contact_str.lower() and
                    not contact_str.isdigit() and '@' not in contact_str and 
                    '/' not in contact_str and '\\' not in contact_str):
                    account_name = contact_str
            
            # Extract x_id
            if internet_field and internet_field.lower() not in ['nan', 'none', 'null', '']:
                import re
                match = re.search(r'(?:Twitter|X)\s+ID[:\s]+([a-zA-Z0-9_]+)', internet_field, re.IGNORECASE)
                if match:
                    x_id = match.group(1).strip()
            
            if not account_name and not x_id:
                skipped_twitter.append({
                    'row': row_idx,
                    'type': row.get('Type'),
                    'reason': "No account_name and no x_id",
                    'contact': contact_field[:100],
                    'internet': internet_field[:100]
                })
        
        print(f"\n📊 Twitter/X skipped rows: {len(skipped_twitter)}")
        for skip in skipped_twitter:
            print(f"\n--- Row {skip['row']} ---")
            print(f"Type: {skip['type']}")
            print(f"Reason: {skip['reason']}")
            print(f"Contact: {skip['contact']}")
            print(f"Internet: {skip['internet']}")
            # Show all columns for debugging
            for col in df.columns:
                val = row.get(col)
                if pd.notna(val) and str(val).strip() and str(val).lower() not in ['nan', 'none', 'null', '']:
                    print(f"  {col}: {str(val)[:100]}")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        total_found = len(telegram_rows) + len(twitter_rows)
        total_valid = 33 + 150
        total_skipped = len(skipped_telegram) + len(skipped_twitter)
        print(f"Total rows found: {total_found} (Telegram: {len(telegram_rows)}, Twitter/X: {len(twitter_rows)})")
        print(f"Total valid: {total_valid} (Telegram: 33, Twitter/X: 150)")
        print(f"Total skipped: {total_skipped} (Telegram: {len(skipped_telegram)}, Twitter/X: {len(skipped_twitter)})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_skipped_data()

