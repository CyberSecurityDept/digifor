#!/usr/bin/env python3
import pandas as pd
import sys
from pathlib import Path

def analyze_excel_file(file_path: str):
    print(f"=== ANALYZING EXCEL FILE ===\n")
    print(f"File: {file_path}\n")
    
    try:
        xls = pd.ExcelFile(file_path, engine='xlrd')
        
        print(f"Total Sheets: {len(xls.sheet_names)}\n")
        print(f"Sheet Names:")
        for idx, sheet in enumerate(xls.sheet_names, 1):
            print(f"  {idx}. {sheet}")
        
        print("\n" + "="*80)
        print("ANALYZING SOCIAL MEDIA SHEETS")
        print("="*80 + "\n")
        
        social_media_keywords = {
            'whatsapp': ['whatsapp'],
            'instagram': ['instagram'],
            'telegram': ['telegram'],
            'x': ['twitter', 'x (twitter)', 'x(', 'twitter'],
            'facebook': ['facebook'],
            'tiktok': ['tiktok']
        }
        
        for sheet_name in xls.sheet_names:
            sheet_lower = sheet_name.lower().strip()
            
            # Detect platform
            detected_platform = None
            for platform, keywords in social_media_keywords.items():
                if any(keyword in sheet_lower for keyword in keywords):
                    detected_platform = platform
                    break
            
            # Also check Contacts sheet
            if 'contact' in sheet_lower:
                detected_platform = 'contacts'
            
            if detected_platform or 'contact' in sheet_lower:
                print(f"\n{'='*80}")
                print(f"SHEET: {sheet_name}")
                print(f"Platform: {detected_platform or 'Contacts (multiple platforms)'}")
                print(f"{'='*80}\n")
                
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='xlrd', dtype=str, nrows=20)
                    
                    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
                    print(f"\nColumns:")
                    for idx, col in enumerate(df.columns):
                        print(f"  [{idx}] {col}")
                    
                    print(f"\nFirst 5 rows (sample data):")
                    print(df.head(5).to_string(max_cols=15))
                    
                    # Analyze column mapping
                    print(f"\n--- Column Mapping Analysis ---")
                    col_mapping = analyze_column_mapping(df, detected_platform)
                    print("Detected mappings:")
                    for key, value in col_mapping.items():
                        print(f"  {key}: Column '{value}'")
                    
                    print(f"\n--- Data Sample (First Valid Row) ---")
                    sample_data = extract_sample_data(df, detected_platform)
                    for key, value in sample_data.items():
                        if value:
                            print(f"  {key}: {value[:100]}")  # Limit to 100 chars
                    
                except Exception as e:
                    print(f"Error reading sheet: {e}")
                    import traceback
                    traceback.print_exc()
        
    except Exception as e:
        print(f"Error opening file: {e}")
        import traceback
        traceback.print_exc()

def analyze_column_mapping(df: pd.DataFrame, platform: str) -> dict:
    """Analyze and map columns for the given platform"""
    
    col_mapping = {}
    
    for col in df.columns:
        col_str = str(col).lower().strip()
        
        # Common mappings
        if 'full name' in col_str:
            col_mapping['full_name'] = col
        elif 'user name' in col_str and 'user id' not in col_str:
            col_mapping['account_name'] = col
        elif 'user id' in col_str or 'userid' in col_str:
            col_mapping['user_id'] = col
        elif 'account id' in col_str or 'accountid' in col_str:
            col_mapping['account_id'] = col
        elif 'phone number' in col_str or 'phone' in col_str:
            col_mapping['phone_number'] = col
        elif 'user picture' in col_str or 'profile picture' in col_str:
            col_mapping['profile_picture_url'] = col
        elif 'following' in col_str:
            col_mapping['following'] = col
        elif 'followers' in col_str:
            col_mapping['followers'] = col
    
    # Platform-specific mappings
    if platform == 'whatsapp':
        # WhatsApp specific
        pass
    
    return col_mapping

def extract_sample_data(df: pd.DataFrame, platform: str) -> dict:
    """Extract sample data from first valid row"""
    
    sample = {}
    
    # Find first non-empty row
    for idx, row in df.iterrows():
        row_values = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() not in ['', 'nan', 'None']]
        if len(row_values) > 0:
            # Extract values
            if len(row) > 0:
                sample['row_index'] = idx
                for i, val in enumerate(row.values[:10]):  # First 10 columns
                    if pd.notna(val) and str(val).strip() not in ['', 'nan', 'None']:
                        sample[f'col_{i}'] = str(val)[:100]
            break
    
    return sample

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_excel_structure.py <excel_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    analyze_excel_file(file_path)

