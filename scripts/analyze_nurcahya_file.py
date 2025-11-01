#!/usr/bin/env python3
"""
Script untuk menganalisis file Nurcahya Hikari dan melihat data yang di-skip
"""
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

file_path = 'sample_social_mediaa/iPhone Hikari/Oxygen/Nurcahya Hikari-Apple UFED file syst-22102025152543.xls'

def analyze_file():
    try:
        print("="*80)
        print("ANALYZING NURCAHYA HIKARI FILE")
        print("="*80)
        
        # Read Excel file
        xls = pd.ExcelFile(file_path, engine='xlrd')
        print(f"\n📊 Sheets available: {xls.sheet_names}")
        
        # Read Contacts sheet (note: sheet name has trailing space)
        df = pd.read_excel(file_path, sheet_name='Contacts ', engine='xlrd', dtype=str)
        print(f"\n📋 Contacts sheet: {len(df)} rows, {len(df.columns)} columns")
        print(f"Columns: {df.columns.tolist()}")
        
        # Analyze Instagram rows
        print("\n" + "="*80)
        print("INSTAGRAM ANALYSIS")
        print("="*80)
        instagram_rows = df[df['Source'].str.contains('Instagram', case=False, na=False)]
        print(f"Total Instagram rows: {len(instagram_rows)}")
        
        if len(instagram_rows) > 0:
            print("\nFirst 10 Instagram rows:")
            for idx, (row_idx, row) in enumerate(instagram_rows.head(10).iterrows(), 1):
                print(f"\n--- Row {row_idx} (Row #{idx}) ---")
                print(f"Type: {row.get('Type', 'N/A')}")
                print(f"Source: {row.get('Source', 'N/A')}")
                contact = str(row.get('Contact', '') or '')
                internet = str(row.get('Internet', '') or '')
                print(f"Contact: {contact[:100]}")
                print(f"Internet: {internet[:100]}")
                
                # Check if this row would be skipped
                account_name = None
                instagram_id = None
                
                # Simulate account_name extraction
                if contact:
                    contact_str = str(contact).strip()
                    if (contact_str and len(contact_str) > 1 and len(contact_str) < 50 and
                        '\n' not in contact_str and '@' not in contact_str and 
                        '/' not in contact_str and '\\' not in contact_str and
                        not contact_str.isdigit()):
                        account_name = contact_str
                
                # Simulate instagram_id extraction
                if internet:
                    if 'Instagram ID:' in internet:
                        parts = internet.split('Instagram ID:')
                        if len(parts) > 1:
                            instagram_id = parts[1].strip()
                    elif 'Group ID:' in internet or 'Group ID' in internet:
                        import re
                        group_id_match = re.search(r'Group\s+ID[:\s]+(\d+)', str(internet), re.IGNORECASE)
                        if group_id_match:
                            instagram_id = group_id_match.group(1).strip()
                
                if contact_str.isdigit() and len(contact_str) > 15:
                    instagram_id = contact_str
                
                print(f"Extracted account_name: {account_name}")
                print(f"Extracted instagram_id: {instagram_id}")
                
                if not account_name and not instagram_id:
                    print("⚠️  THIS ROW WOULD BE SKIPPED")
                else:
                    print("✓ This row would be processed")
        
        # Analyze Twitter/X rows
        print("\n" + "="*80)
        print("TWITTER/X ANALYSIS")
        print("="*80)
        twitter_rows = df[df['Source'].str.contains('Twitter|X', case=False, na=False)]
        print(f"Total Twitter/X rows: {len(twitter_rows)}")
        
        if len(twitter_rows) > 0:
            print("\nSample Twitter/X rows (first 20):")
            for idx, (row_idx, row) in enumerate(twitter_rows.head(20).iterrows(), 1):
                print(f"\n--- Row {row_idx} (Row #{idx}) ---")
                print(f"Type: {row.get('Type', 'N/A')}")
                print(f"Source: {row.get('Source', 'N/A')}")
                contact = str(row.get('Contact', '') or '')
                internet = str(row.get('Internet', '') or '')
                print(f"Contact: {contact[:100]}")
                print(f"Internet: {internet[:100]}")
                
                # Check if this row would be skipped
                type_field = str(row.get('Type', '') or '').lower().strip()
                is_account_type = type_field in ["account", "account(merged)", "account (merged)", "accounts"]
                is_contact_type = type_field in ["contact", "contact(merged)", "contact (merged)", "contacts"]
                
                if not (is_account_type or is_contact_type):
                    print("⚠️  SKIPPED: Type is not Account or Contact")
                    continue
                
                account_name = None
                x_id = None
                
                # Simulate account_name extraction (from _extract_nickname)
                if contact:
                    contact_str = str(contact).strip()
                    if 'Nickname:' in contact_str:
                        parts = contact_str.split('Nickname:')
                        if len(parts) > 1:
                            account_name = parts[1].strip()
                    elif (contact_str and len(contact_str) > 1 and len(contact_str) < 50 and
                          '\n' not in contact_str and 'nickname:' not in contact_str.lower() and
                          not contact_str.isdigit() and '@' not in contact_str and 
                          '/' not in contact_str and '\\' not in contact_str):
                        account_name = contact_str
                
                # Simulate x_id extraction
                if internet:
                    if 'X ID:' in internet:
                        parts = internet.split('X ID:')
                        if len(parts) > 1:
                            x_id = parts[1].strip()
                    elif 'Twitter ID:' in internet:
                        parts = internet.split('Twitter ID:')
                        if len(parts) > 1:
                            x_id = parts[1].strip()
                
                print(f"Extracted account_name: {account_name}")
                print(f"Extracted x_id: {x_id}")
                
                if not account_name and not x_id:
                    print("⚠️  THIS ROW WOULD BE SKIPPED (no account_name and no x_id)")
                else:
                    print("✓ This row would be processed")
            
            # Count Type distribution
            print("\n" + "-"*80)
            print("Type Distribution for Twitter/X rows:")
            type_dist = twitter_rows['Type'].value_counts()
            print(type_dist.to_string())
            
            # Count valid vs skipped
            valid_count = 0
            skipped_count = 0
            skipped_by_type = 0
            
            for _, row in twitter_rows.iterrows():
                type_field = str(row.get('Type', '') or '').lower().strip()
                is_account_type = type_field in ["account", "account(merged)", "account (merged)", "accounts"]
                is_contact_type = type_field in ["contact", "contact(merged)", "contact (merged)", "contacts"]
                
                if not (is_account_type or is_contact_type):
                    skipped_by_type += 1
                    continue
                
                contact_field = str(row.get('Contact', '') or '').strip()
                internet_field = str(row.get('Internet', '') or '').strip()
                
                account_name = None
                x_id = None
                
                # Extract account_name
                if contact_field:
                    if 'Nickname:' in contact_field:
                        parts = contact_field.split('Nickname:')
                        if len(parts) > 1:
                            account_name = parts[1].strip()
                    elif (contact_field and len(contact_field) > 1 and len(contact_field) < 50 and
                          '\n' not in contact_field and 'nickname:' not in contact_field.lower() and
                          not contact_field.isdigit() and '@' not in contact_field and 
                          '/' not in contact_field and '\\' not in contact_field):
                        account_name = contact_field
                
                # Extract x_id
                if internet_field:
                    if 'X ID:' in internet_field:
                        parts = internet_field.split('X ID:')
                        if len(parts) > 1:
                            x_id = parts[1].strip()
                    elif 'Twitter ID:' in internet_field:
                        parts = internet_field.split('Twitter ID:')
                        if len(parts) > 1:
                            x_id = parts[1].strip()
                
                if account_name or x_id:
                    valid_count += 1
                else:
                    skipped_count += 1
            
            print(f"\n📊 Summary:")
            print(f"  Total Twitter/X rows: {len(twitter_rows)}")
            print(f"  Skipped by Type filter: {skipped_by_type}")
            print(f"  Valid (has account_name or x_id): {valid_count}")
            print(f"  Skipped (no account_name and no x_id): {skipped_count}")
        
        # Check Instagram skipped row specifically
        print("\n" + "="*80)
        print("CHECKING SKIPPED INSTAGRAM ROW")
        print("="*80)
        print("Based on log: Contact=25130295109, Internet=None")
        skipped_instagram = instagram_rows[
            (instagram_rows['Contact'].astype(str).str.contains('25130295109', na=False)) |
            (instagram_rows['Internet'].astype(str).str.lower().str.contains('none|nan', na=False))
        ]
        
        if len(skipped_instagram) > 0:
            print(f"\nFound {len(skipped_instagram)} potential skipped Instagram rows:")
            for idx, (row_idx, row) in enumerate(skipped_instagram.iterrows(), 1):
                print(f"\n--- Row {row_idx} ---")
                for col in df.columns:
                    val = row.get(col)
                    if pd.notna(val) and str(val).strip() and str(val).lower() not in ['nan', 'none', 'null', '']:
                        print(f"{col}: {str(val)[:100]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_file()

