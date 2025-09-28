#!/usr/bin/env python3
"""
Database migration script to add case management improvements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models.case import Case, CasePerson, EvidencePersonAssociation

def add_case_management_fields():
    """Add new fields to cases table"""
    db = SessionLocal()
    try:
        # Add new columns to cases table
        db.execute(text("""
            ALTER TABLE cases 
            ADD COLUMN IF NOT EXISTS agency VARCHAR(200),
            ADD COLUMN IF NOT EXISTS jurisdiction_level VARCHAR(50),
            ADD COLUMN IF NOT EXISTS case_classification VARCHAR(50);
        """))
        
        # Update existing cases with default values
        db.execute(text("""
            UPDATE cases 
            SET agency = jurisdiction,
                jurisdiction_level = 'Local',
                case_classification = 'Public'
            WHERE agency IS NULL;
        """))
        
        db.commit()
        print("✅ Added new fields to cases table")
        
    except Exception as e:
        print(f"❌ Error adding case fields: {e}")
        db.rollback()
    finally:
        db.close()

def create_evidence_person_associations_table():
    """Create evidence_person_associations table"""
    db = SessionLocal()
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS evidence_person_associations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                evidence_id UUID NOT NULL REFERENCES evidence_items(id),
                person_id UUID NOT NULL REFERENCES case_persons(id),
                association_type VARCHAR(50) DEFAULT 'related',
                association_notes TEXT,
                confidence_level VARCHAR(20) DEFAULT 'medium',
                created_by UUID NOT NULL REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE,
                UNIQUE(evidence_id, person_id)
            );
        """))
        
        # Create indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_evidence_person_associations_evidence_id 
            ON evidence_person_associations(evidence_id);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_evidence_person_associations_person_id 
            ON evidence_person_associations(person_id);
        """))
        
        db.commit()
        print("✅ Created evidence_person_associations table")
        
    except Exception as e:
        print(f"❌ Error creating evidence_person_associations table: {e}")
        db.rollback()
    finally:
        db.close()

def migrate_existing_associations():
    """Migrate existing evidence-person associations from descriptions"""
    db = SessionLocal()
    try:
        from app.models.evidence import EvidenceItem
        
        # Get all evidence items with person names in descriptions
        evidence_items = db.query(EvidenceItem).all()
        associations_created = 0
        
        for evidence in evidence_items:
            if not evidence.description:
                continue
                
            # Look for person names in evidence descriptions
            persons = db.query(CasePerson).filter(
                CasePerson.case_id == evidence.case_id
            ).all()
            
            for person in persons:
                if person.full_name.lower() in evidence.description.lower():
                    # Check if association already exists
                    existing = db.query(EvidencePersonAssociation).filter(
                        EvidencePersonAssociation.evidence_id == evidence.id,
                        EvidencePersonAssociation.person_id == person.id
                    ).first()
                    
                    if not existing:
                        association = EvidencePersonAssociation(
                            evidence_id=evidence.id,
                            person_id=person.id,
                            association_type="legacy",
                            confidence_level="medium",
                            association_notes="Migrated from evidence description",
                            created_by=evidence.created_by
                        )
                        db.add(association)
                        associations_created += 1
        
        db.commit()
        print(f"✅ Migrated {associations_created} existing evidence-person associations")
        
    except Exception as e:
        print(f"❌ Error migrating associations: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Run all migrations"""
    print("🚀 Starting case management database improvements...")
    
    print("\n1. Adding new fields to cases table...")
    add_case_management_fields()
    
    print("\n2. Creating evidence_person_associations table...")
    create_evidence_person_associations_table()
    
    print("\n3. Migrating existing associations...")
    migrate_existing_associations()
    
    print("\n✅ Case management database improvements completed!")

if __name__ == "__main__":
    main()
