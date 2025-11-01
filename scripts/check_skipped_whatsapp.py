import pandas as pd
import re

file_path = 'sample_social_mediaa/Xiaomi Riko/Cellebrite/Xiaomi Redmi 9C_2025-10-21_Report.xlsx'

try:
    df = pd.read_excel(file_path, sheet_name='Contacts', engine='openpyxl', dtype=str)
    
    # Fix column names if they are unnamed
    if any('Unnamed' in str(col) for col in df.columns):
        df.columns = df.iloc[0]
        df = df.drop(df.index[0])
        df = df.reset_index(drop=True)
    
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}\n")
    
    # Check WhatsApp rows
    whatsapp_rows = []
    skipped_reasons = {
        'no_name': [],
        'no_phone': [],
        'no_whatsapp_id': [],
        'has_all': []
    }
    
    for idx, row in df.iterrows():
        source = str(row.get('Source', '')).strip() if pd.notna(row.get('Source', '')) else ''
        name = str(row.get('Name', '')).strip() if pd.notna(row.get('Name', '')) else ''
        entries = str(row.get('Entries', '')).strip() if pd.notna(row.get('Entries', '')) else ''
        
        if 'whatsapp' in source.lower():
            whatsapp_id = None
            phone_number = None
            
            # Check WhatsApp User Id
            whatsapp_user_id_match = re.search(r'User\s+ID-WhatsApp\s+User\s+Id[:\s]+([^\s\n\r]+)', entries, re.IGNORECASE)
            if whatsapp_user_id_match:
                whatsapp_user_id_full = whatsapp_user_id_match.group(1).strip()
                whatsapp_id = whatsapp_user_id_full.replace('@s.whatsapp.net', '').strip()
            
            # Check Phone patterns
            phone_patterns = [
                r'Phone-Mobile[:\s]+([^\s\n\r]+)',
                r'Phone[:\s]+([^\s\n\r]+)',
                r'Mobile[:\s]+([^\s\n\r]+)',
                r'Phone\s+Number[:\s]+([^\s\n\r]+)',
            ]
            for phone_pattern in phone_patterns:
                phone_match = re.search(phone_pattern, entries, re.IGNORECASE)
                if phone_match:
                    phone_number = phone_match.group(1).strip()
                    break
            
            if not phone_number and whatsapp_id:
                phone_number = whatsapp_id
            
            # Determine skip reason
            if not name or name.lower() in ['nan', 'none', 'null', '']:
                skipped_reasons['no_name'].append({
                    'row': idx + 2,  # +2 karena index 0-based dan header
                    'name': name,
                    'whatsapp_id': whatsapp_id,
                    'phone_number': phone_number,
                    'entries': entries[:200] if len(entries) > 200 else entries
                })
            elif not phone_number:
                skipped_reasons['no_phone'].append({
                    'row': idx + 2,
                    'name': name,
                    'whatsapp_id': whatsapp_id,
                    'entries': entries[:200] if len(entries) > 200 else entries
                })
            elif not whatsapp_id:
                skipped_reasons['no_whatsapp_id'].append({
                    'row': idx + 2,
                    'name': name,
                    'phone_number': phone_number,
                    'entries': entries[:200] if len(entries) > 200 else entries
                })
            else:
                skipped_reasons['has_all'].append({
                    'row': idx + 2,
                    'name': name,
                    'whatsapp_id': whatsapp_id,
                    'phone_number': phone_number
                })
    
    print("=" * 80)
    print("WHATSAPP ANALYSIS")
    print("=" * 80)
    print(f"\nTotal WhatsApp rows: {sum(len(v) for v in skipped_reasons.values())}")
    print(f"Rows with all fields (should be inserted): {len(skipped_reasons['has_all'])}")
    print(f"Rows skipped - no name: {len(skipped_reasons['no_name'])}")
    print(f"Rows skipped - no phone: {len(skipped_reasons['no_phone'])}")
    print(f"Rows skipped - no whatsapp_id: {len(skipped_reasons['no_whatsapp_id'])}")
    
    print("\n" + "=" * 80)
    print("SKIPPED: Missing NAME (first 10 examples)")
    print("=" * 80)
    for item in skipped_reasons['no_name'][:10]:
        print(f"Row {item['row']}: Name='{item['name']}', WhatsApp ID='{item['whatsapp_id']}', Phone='{item['phone_number']}'")
        print(f"  Entries preview: {item['entries'][:150]}...")
        print()
    
    print("\n" + "=" * 80)
    print("SKIPPED: Missing PHONE (first 5 examples)")
    print("=" * 80)
    for item in skipped_reasons['no_phone'][:5]:
        print(f"Row {item['row']}: Name='{item['name']}', WhatsApp ID='{item['whatsapp_id']}'")
        print(f"  Entries preview: {item['entries'][:150]}...")
        print()
    
    print("\n" + "=" * 80)
    print("SKIPPED: Missing WHATSAPP_ID (first 5 examples)")
    print("=" * 80)
    for item in skipped_reasons['no_whatsapp_id'][:5]:
        print(f"Row {item['row']}: Name='{item['name']}', Phone='{item['phone_number']}'")
        print(f"  Entries preview: {item['entries'][:150]}...")
        print()
    
    print("\n" + "=" * 80)
    print("SHOULD BE INSERTED (first 5 examples)")
    print("=" * 80)
    for item in skipped_reasons['has_all'][:5]:
        print(f"Row {item['row']}: Name='{item['name']}', WhatsApp ID='{item['whatsapp_id']}', Phone='{item['phone_number']}'")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

