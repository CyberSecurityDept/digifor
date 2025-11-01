#!/usr/bin/env python3
"""
Script untuk cek Row 129 yang terskip
"""
import pandas as pd

file_path = 'sample_social_mediaa/iPhone Hikari/Oxygen/Nurcahya Hikari-Apple UFED file syst-22102025152543.xls'

df = pd.read_excel(file_path, sheet_name='Contacts ', engine='xlrd', dtype=str)
row = df.iloc[129]

print('Row 129:')
print(f"Type: {row.get('Type')}")
print(f"Source: {row.get('Source')}")
print(f"Contact: {row.get('Contact')}")
print(f"Internet: {row.get('Internet')}")
print(f"Phones & Emails: {row.get('Phones & Emails')}")
print(f"\nAll columns:")
for col in df.columns:
    val = row.get(col)
    if pd.notna(val) and str(val).strip() and str(val).lower() not in ['nan', 'none', 'null', '']:
        print(f"  {col}: {str(val)[:150]}")

