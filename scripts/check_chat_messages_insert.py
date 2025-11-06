#!/usr/bin/env python3
"""
Script to check why only 211 chat messages were inserted instead of 350
for file_id=1 (Magnet Axiom file)
"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.analytics.device_management.models import ChatMessage, File

def analyze_chat_messages():
    """Analyze chat messages for file_id=1"""
    db = SessionLocal()
    
    try:
        # Get file info
        file_record = db.query(File).filter(File.id == 1).first()
        if not file_record:
            print("File with id=1 not found!")
            return
        
        print(f"File Info:")
        print(f"  ID: {file_record.id}")
        print(f"  Name: {file_record.file_name}")
        print(f"  Path: {file_record.file_path}")
        print(f"  Tools: {file_record.tools}")
        print(f"  Method: {file_record.method}")
        print(f"  amount_of_data: {file_record.amount_of_data}")
        print(f"  chat_messages_count: {file_record.chat_messages_count}")
        print()
        
        # Count actual chat messages in database
        total_chat_messages = db.query(ChatMessage).filter(ChatMessage.file_id == 1).count()
        print(f"Total chat_messages in database for file_id=1: {total_chat_messages}")
        
        # Count by platform
        platforms = db.query(ChatMessage.platform).filter(ChatMessage.file_id == 1).distinct().all()
        print(f"\nPlatform breakdown:")
        for (platform,) in platforms:
            count = db.query(ChatMessage).filter(
                ChatMessage.file_id == 1,
                ChatMessage.platform == platform
            ).count()
            print(f"  {platform}: {count}")
        
        # Check for duplicates
        from sqlalchemy import func
        duplicate_query = db.query(
            ChatMessage.platform,
            ChatMessage.message_id,
            func.count(ChatMessage.id).label('count')
        ).filter(
            ChatMessage.file_id == 1
        ).group_by(
            ChatMessage.platform,
            ChatMessage.message_id
        ).having(func.count(ChatMessage.id) > 1).all()
        
        if duplicate_query:
            print(f"\n⚠️ Found {len(duplicate_query)} duplicate message_id combinations!")
            for platform, msg_id, count in duplicate_query[:5]:
                print(f"  Platform: {platform}, Message ID: {msg_id}, Count: {count}")
        else:
            print(f"\n✓ No duplicates found")
        
        # Check messages with missing required fields
        messages_without_text = db.query(ChatMessage).filter(
            ChatMessage.file_id == 1,
            (ChatMessage.message_text == None) | (ChatMessage.message_text == '')
        ).count()
        
        messages_without_platform = db.query(ChatMessage).filter(
            ChatMessage.file_id == 1,
            (ChatMessage.platform == None) | (ChatMessage.platform == '')
        ).count()
        
        messages_without_message_id = db.query(ChatMessage).filter(
            ChatMessage.file_id == 1,
            (ChatMessage.message_id == None) | (ChatMessage.message_id == '')
        ).count()
        
        print(f"\nMessages with missing data:")
        print(f"  Without message_text: {messages_without_text}")
        print(f"  Without platform: {messages_without_platform}")
        print(f"  Without message_id: {messages_without_message_id}")
        
        # Analyze Excel file directly
        file_path = file_record.file_path
        if os.path.exists(file_path):
            print(f"\n=== Analyzing Excel file directly ===")
            print(f"File: {file_path}")
            
            try:
                xls = pd.ExcelFile(file_path, engine='openpyxl')
                print(f"Total sheets: {len(xls.sheet_names)}")
                print(f"Sheets: {', '.join(xls.sheet_names[:10])}")
                
                # Check Telegram Messages sheet
                if 'Telegram Messages - iOS' in xls.sheet_names:
                    df = pd.read_excel(file_path, sheet_name='Telegram Messages - iOS', engine='openpyxl', dtype=str)
                    print(f"\n'Telegram Messages - iOS' sheet:")
                    print(f"  Total rows: {len(df)}")
                    
                    # Count rows with Message
                    messages_with_content = df[df['Message'].notna() & (df['Message'].astype(str).str.strip() != '')].shape[0]
                    print(f"  Rows with Message content: {messages_with_content}")
                    
                    # Check Message Status
                    if 'Message Status' in df.columns:
                        status_counts = df['Message Status'].value_counts()
                        print(f"  Message Status breakdown:")
                        for status, count in status_counts.items():
                            print(f"    {status}: {count}")
                    
                    # Check for duplicates in Excel
                    if 'Message ID' in df.columns:
                        unique_ids = df['Message ID'].nunique()
                        total_ids = df['Message ID'].notna().sum()
                        print(f"  Unique Message IDs: {unique_ids} (out of {total_ids} with Message ID)")
                        
                        if unique_ids < total_ids:
                            duplicates_in_excel = total_ids - unique_ids
                            print(f"  ⚠️ Potential duplicates in Excel: {duplicates_in_excel}")
                
                # Check other message sheets
                message_sheets = [s for s in xls.sheet_names if 'message' in s.lower() or 'chat' in s.lower()]
                print(f"\nOther message-related sheets:")
                for sheet in message_sheets:
                    if sheet != 'Telegram Messages - iOS':
                        df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl', dtype=str, nrows=5)
                        print(f"  {sheet}: {len(df)} rows (showing first 5)")
                
            except Exception as e:
                print(f"Error reading Excel file: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n⚠️ File not found at: {file_path}")
        
        # Expected vs Actual
        expected = file_record.amount_of_data or 0
        actual = total_chat_messages
        difference = expected - actual
        
        print(f"\n=== Summary ===")
        print(f"Expected (amount_of_data): {expected}")
        print(f"Actual in database: {actual}")
        print(f"Difference: {difference}")
        
        if difference > 0:
            print(f"\n⚠️ Missing {difference} records!")
            print(f"Possible reasons:")
            print(f"  1. Duplicate checking skipped {difference} records")
            print(f"  2. Validation failed (missing message_text, platform, or message_id)")
            print(f"  3. Parsing errors or skipped rows")
            print(f"  4. amount_of_data includes data from other sources (not just chat_messages)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("Analyzing chat messages for file_id=1...")
    print("=" * 60)
    analyze_chat_messages()
    print("=" * 60)

