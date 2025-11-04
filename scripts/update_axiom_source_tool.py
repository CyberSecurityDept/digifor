#!/usr/bin/env python3
"""
Script to update source_tool from 'axiom' to 'Magnet Axiom' in chat_messages table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.analytics.device_management.models import ChatMessage
from sqlalchemy import text

def update_source_tool():
    """Update source_tool from 'axiom' to 'Magnet Axiom'"""
    db = SessionLocal()
    
    try:
        # Count records that will be updated
        count_before = db.query(ChatMessage).filter(ChatMessage.source_tool == 'axiom').count()
        print(f"Found {count_before} records with source_tool='axiom'")
        
        if count_before == 0:
            print("No records to update. All source_tool values are already correct.")
            return
        
        # Update records
        updated = db.query(ChatMessage).filter(ChatMessage.source_tool == 'axiom').update({
            ChatMessage.source_tool: 'Magnet Axiom'
        })
        
        db.commit()
        
        print(f"Successfully updated {updated} records from 'axiom' to 'Magnet Axiom'")
        
        # Verify update
        count_after = db.query(ChatMessage).filter(ChatMessage.source_tool == 'axiom').count()
        count_new = db.query(ChatMessage).filter(ChatMessage.source_tool == 'Magnet Axiom').count()
        
        print(f"Verification:")
        print(f"  Records with source_tool='axiom': {count_after}")
        print(f"  Records with source_tool='Magnet Axiom': {count_new}")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating source_tool: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Updating source_tool from 'axiom' to 'Magnet Axiom' in chat_messages table...")
    update_source_tool()
    print("Done!")

