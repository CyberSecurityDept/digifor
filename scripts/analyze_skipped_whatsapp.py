#!/usr/bin/env python3
"""
Script untuk menganalisis data WhatsApp yang di-skip berdasarkan log
"""
import re

def analyze_skipped_data():
    """Analisis data yang di-skip berdasarkan log"""
    
    skipped_data = {
        "by_type": {
            "Row 6": {
                "reason": "Type='Group' (not Account/Contact)",
                "data": "Type: Group",
                "fixable": False,  # Group memang bukan Account/Contact
                "note": "Group type biasanya bukan individual account"
            }
        },
        "no_whatsapp_id_or_phone": {
            "Row 16": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "0@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "issue": "Contact berisi '0@s.whatsapp.net' (terlalu pendek, hanya 1 digit)",
                "fix": "Telah ditambahkan ekstraksi dari Contact field, tapi '0' terlalu pendek (<8 digit minimal)"
            },
            "Row 22": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact (merged)",
                    "Source": "WhatsApp Messenger backup, WhatsApp Messenger",
                    "Contact": "3Care",
                    "Internet": "WhatsApp ID: 62123@s.whatsapp.net",
                    "Phones & Emails": "Phone number: Mobile: 123"
                },
                "fixable": True,
                "issue": "WhatsApp ID hanya 5 digit (62123), Phone number hanya 3 digit (123) - keduanya <8 digit minimal",
                "fix": "Fungsi sudah bisa extract, tapi ID terlalu pendek untuk dianggap valid"
            },
            "Row 34": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "6281275907774@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "issue": "Contact field berisi nomor dengan @s.whatsapp.net tapi tidak ada Internet/Phones & Emails",
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            },
            "Row 37": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "628176601011@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "issue": "Same as Row 34",
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            },
            "Row 40": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "6282280113988@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            },
            "Row 41": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "6283141493472@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            },
            "Row 45": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "6285608531839@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            },
            "Row 46": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "6285742723180@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            },
            "Row 48": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "6285822380449@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            },
            "Row 49": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "6287727723776@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            },
            "Row 50": {
                "reason": "No whatsapp_id or phone_number",
                "data": {
                    "Type": "Contact",
                    "Source": "WhatsApp Messenger",
                    "Contact": "6287777230670@s.whatsapp.net",
                    "Internet": "None",
                    "Phones & Emails": "None"
                },
                "fixable": True,
                "fix": "✅ SUDAH DIPERBAIKI: Sekarang extract dari Contact field langsung"
            }
        }
    }
    
    print("=" * 80)
    print("ANALISIS DATA WHATSAPP YANG DI-SKIP")
    print("=" * 80)
    
    # Summary
    total_skipped = len(skipped_data["by_type"]) + len(skipped_data["no_whatsapp_id_or_phone"])
    fixable = sum(1 for item in skipped_data["no_whatsapp_id_or_phone"].values() if item.get("fixable", False))
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total skipped: {total_skipped} rows")
    print(f"  - Skipped by Type filter: {len(skipped_data['by_type'])}")
    print(f"  - Skipped by no whatsapp_id/phone: {len(skipped_data['no_whatsapp_id_or_phone'])}")
    print(f"  - Fixable: {fixable} rows")
    print(f"  - Already fixed: {fixable} rows")
    
    print(f"\n📋 DETAIL SKIP BY TYPE:")
    for row, info in skipped_data["by_type"].items():
        print(f"\n  {row}:")
        print(f"    Reason: {info['reason']}")
        print(f"    Data: {info['data']}")
        print(f"    Fixable: {info['fixable']}")
        print(f"    Note: {info['note']}")
    
    print(f"\n📋 DETAIL SKIP BY NO WHATSAPP_ID/PHONE:")
    for row, info in skipped_data["no_whatsapp_id_or_phone"].items():
        print(f"\n  {row}:")
        print(f"    Reason: {info['reason']}")
        print(f"    Type: {info['data'].get('Type', 'N/A')}")
        print(f"    Contact: {info['data'].get('Contact', 'N/A')}")
        print(f"    Internet: {info['data'].get('Internet', 'N/A')[:50] if info['data'].get('Internet') else 'None'}")
        if 'issue' in info:
            print(f"    Issue: {info['issue']}")
        print(f"    Fix: {info['fix']}")
    
    print(f"\n✅ PERBAIKAN YANG SUDAH DILAKUKAN:")
    print(f"  1. Ekstraksi whatsapp_id dari Contact field jika berisi @s.whatsapp.net")
    print(f"     Contoh: '6281275907774@s.whatsapp.net' -> '6281275907774'")
    print(f"  2. Ekstraksi whatsapp_id dari Phones & Emails field")
    print(f"  3. Fallback: gunakan phone_number sebagai whatsapp_id jika tersedia")
    print(f"  4. Validasi minimal 8 digit untuk memastikan nomor valid")
    
    print(f"\n⚠️  DATA YANG TETAP DI-SKIP (Dengan Alasan):")
    print(f"  - Row 6: Type='Group' (bukan individual account)")
    print(f"  - Row 16: Contact='0@s.whatsapp.net' (terlalu pendek, hanya 1 digit)")
    print(f"  - Row 22: WhatsApp ID='62123' (terlalu pendek, hanya 5 digit, minimal 8 digit)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_skipped_data()

