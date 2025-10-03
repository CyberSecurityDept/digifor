"""
Database Migration Script
Creates all tables for the case management system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import get_db, init_db
from app.config import settings
from app.models.agency import Agency
from app.models.investigator import Investigator
from app.models.person import Person
from app.models.evidence_type import EvidenceType
from app.models.case import Case, CasePerson
from app.models.evidence_new import Evidence, ChainOfCustody, EvidenceMetadata
from app.database import Base, engine


def migrate_database():
    """Create all database tables"""
    try:
        print("🚀 Starting database migration...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database migration completed successfully!")
        print("📊 Created tables:")
        print("  - agencies")
        print("  - investigators") 
        print("  - persons")
        print("  - evidence_types")
        print("  - cases")
        print("  - case_persons")
        print("  - evidence")
        print("  - chain_of_custody")
        print("  - evidence_metadata")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        raise


if __name__ == "__main__":
    migrate_database()
