#!/usr/bin/env python3
"""
Script to query chat_messages by thread_id and file_id
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from sqlalchemy import text

def query_chat_messages_by_thread(thread_id: str, file_id: int):
    """Query chat_messages by thread_id and file_id"""
    db = SessionLocal()
    
    try:
        query = text("""
            SELECT *
            FROM chat_messages
            WHERE thread_id = :thread_id AND file_id = :file_id
            ORDER BY timestamp
        """)
        
        result = db.execute(query, {"thread_id": thread_id, "file_id": file_id})
        rows = result.fetchall()
        
        print(f"=== Chat Messages Query ===")
        print(f"Thread ID: {thread_id}")
        print(f"File ID: {file_id}")
        print(f"Total messages: {len(rows)}")
        print()
        
        if rows:
            # Get column names
            columns = result.keys()
            print("Messages:")
            print("-" * 100)
            
            for idx, row in enumerate(rows, 1):
                print(f"\nMessage #{idx}:")
                row_dict = dict(zip(columns, row))
                
                print(f"  ID: {row_dict.get('id')}")
                print(f"  Platform: {row_dict.get('platform')}")
                print(f"  From: {row_dict.get('from_name')} ({row_dict.get('sender_number')})")
                print(f"  To: {row_dict.get('to_name')} ({row_dict.get('recipient_number')})")
                print(f"  Timestamp: {row_dict.get('timestamp')}")
                print(f"  Thread ID: {row_dict.get('thread_id')}")
                print(f"  Chat ID: {row_dict.get('chat_id')}")
                print(f"  Direction: {row_dict.get('direction')}")
                print(f"  Message Text: {(row_dict.get('message_text') or '')[:100]}...")
        else:
            print("No messages found for this thread_id and file_id")
        
    except Exception as e:
        print(f"Error executing query: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Example usage
    thread_id = "707651c78965f2c17cf01ec7b25b14f0"
    file_id = 1
    
    if len(sys.argv) > 1:
        thread_id = sys.argv[1]
    if len(sys.argv) > 2:
        file_id = int(sys.argv[2])
    
    query_chat_messages_by_thread(thread_id, file_id)

