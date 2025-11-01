#!/usr/bin/env python3
"""Quick test script"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
sys.stdout.write("Starting test...\n")
sys.stdout.flush()

try:
    from app.db.session import get_db
    sys.stdout.write("Imported get_db\n")
    sys.stdout.flush()
    
    db = next(get_db())
    sys.stdout.write("Got database connection\n")
    sys.stdout.flush()
    
    from app.analytics.device_management.models import SocialMedia
    sys.stdout.write("Imported SocialMedia model\n")
    sys.stdout.flush()
    
    count = db.query(SocialMedia).count()
    sys.stdout.write(f"Total records in social_media: {count}\n")
    sys.stdout.flush()
    
    # Test cleanup functions
    from scripts.cleanup_invalid_social_media import is_header_or_metadata, is_system_path
    
    test_cases = [
        ("Source", True),
        ("/", True),
        ("4,00 KB", True),
        ("Cache\\Links", True),
        ("testuser", False),
        ("@username", False),
    ]
    
    sys.stdout.write("\nTesting validation functions:\n")
    sys.stdout.flush()
    
    for value, expected in test_cases:
        result1 = is_header_or_metadata(value)
        result2 = is_system_path(value)
        result = result1 or result2
        status = "✓" if result == expected else "✗"
        sys.stdout.write(f"  {status} '{value}' -> {result} (expected {expected})\n")
        sys.stdout.flush()
    
    sys.stdout.write("\nTest completed!\n")
    sys.stdout.flush()
    
except Exception as e:
    sys.stdout.write(f"ERROR: {e}\n")
    sys.stdout.flush()
    import traceback
    traceback.print_exc()

