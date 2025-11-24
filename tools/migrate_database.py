import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.base import Base
from app.db.session import engine, init_db
from app.core.config import settings
from app.case_management.models import Agency, Case, CaseLog, WorkUnit
from app.evidence_management.models import Evidence, EvidenceType, CustodyLog, CustodyReport
from app.suspect_management.models import Suspect
from app.auth.models import User
try:
    from app.analytics.analytics_management.models import Analytic
    from app.analytics.device_management.models import Device, File, HashFile, Contact, Call, SocialMedia, ChatMessage
except ImportError:
    pass

def migrate_database():
    try:
        print("Starting database migration...")
        print(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else '***'}")
        Base.metadata.create_all(bind=engine)
        print("Database migration completed successfully!")
        print("Created tables:")
        print("- agencies")
        print("- work_units")
        print("- cases")
        print("- case_logs")
        print("- suspects")
        print("- evidence_types")
        print("- evidence")
        print("- custody_logs")
        print("- custody_reports")
        print("- users")
        
        try:
            print("  - analytics")
            print("  - devices")
            print("  - files")
            print("  - hash_files")
            print("  - contacts")
            print("  - calls")
            print("  - social_media")
            print("  - chat_messages")
        except ImportError:
            pass
        
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        raise
    
if __name__ == "__main__":
    migrate_database()
