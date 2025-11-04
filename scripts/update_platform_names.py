#!/usr/bin/env python3
"""
Script to update platform names from lowercase to proper capitalized format in chat_messages table
Updates: whatsapp -> WhatsApp, telegram -> Telegram, instagram -> Instagram, 
         facebook -> Facebook, tiktok -> TikTok, x -> X
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.analytics.device_management.models import ChatMessage

def update_platform_names():
    """Update platform names to proper capitalized format"""
    db = SessionLocal()
    
    try:
        platform_mappings = {
            'whatsapp': 'WhatsApp',
            'telegram': 'Telegram',
            'instagram': 'Instagram',
            'facebook': 'Facebook',
            'tiktok': 'TikTok',
            'x': 'X',
            'twitter': 'X'  # Twitter is now X
        }
        
        total_updated = 0
        
        for old_name, new_name in platform_mappings.items():
            # Count records
            count_before = db.query(ChatMessage).filter(ChatMessage.platform == old_name).count()
            print(f"Found {count_before} records with platform='{old_name}'")
            
            if count_before > 0:
                # Update records
                updated = db.query(ChatMessage).filter(ChatMessage.platform == old_name).update({
                    ChatMessage.platform: new_name
                })
                db.commit()
                total_updated += updated
                print(f"  Updated {updated} records from '{old_name}' to '{new_name}'")
        
        print(f"\nTotal records updated: {total_updated}")
        
        # Verify updates
        print("\nVerification (current platform counts):")
        for new_name in platform_mappings.values():
            count = db.query(ChatMessage).filter(ChatMessage.platform == new_name).count()
            if count > 0:
                print(f"  {new_name}: {count}")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating platform names: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Updating platform names to proper capitalized format in chat_messages table...")
    print("=" * 60)
    update_platform_names()
    print("=" * 60)
    print("Done!")
