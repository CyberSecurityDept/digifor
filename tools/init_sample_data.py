"""
Initialize sample data for the case management system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import get_db, init_db
from app.models.agency import Agency
from app.models.investigator import Investigator
from app.models.person import Person, PersonRole
from app.models.evidence_type import EvidenceType
from app.models.case import Case, CasePerson
from app.models.evidence_new import Evidence, EvidenceStatus
from datetime import datetime, timedelta
import uuid


def create_sample_data():
    """Create sample data for testing"""
    db = next(get_db())
    
    try:
        # Create agencies
        agencies = [
            Agency(name="Interpol", description="International Criminal Police Organization"),
            Agency(name="Trikora Agency", description="Local law enforcement agency"),
            Agency(name="Dirjen Imigrasi", description="Directorate General of Immigration"),
            Agency(name="Bareskrim", description="Criminal Investigation Agency")
        ]
        
        for agency in agencies:
            existing = db.query(Agency).filter(Agency.name == agency.name).first()
            if not existing:
                db.add(agency)
        
        db.commit()
        
        # Create investigators
        investigators = [
            Investigator(
                name="Solehun",
                badge_number="INV001",
                email="solehun@interpol.gov",
                phone="+62-123-456-7890",
                rank="Senior Investigator",
                specialization="International Crimes",
                agency_id=agencies[0].id
            ),
            Investigator(
                name="Robert",
                badge_number="INV002", 
                email="robert@trikora.gov",
                phone="+62-123-456-7891",
                rank="Investigator",
                specialization="Drug Enforcement",
                agency_id=agencies[1].id
            ),
            Investigator(
                name="John Doe",
                badge_number="INV003",
                email="john@imigrasi.gov", 
                phone="+62-123-456-7892",
                rank="Senior Investigator",
                specialization="Immigration Crimes",
                agency_id=agencies[2].id
            )
        ]
        
        for investigator in investigators:
            existing = db.query(Investigator).filter(Investigator.badge_number == investigator.badge_number).first()
            if not existing:
                db.add(investigator)
        
        db.commit()
        
        # Create evidence types
        evidence_types = [
            EvidenceType(name="Mobile Phone", category="Digital", description="Smartphone evidence"),
            EvidenceType(name="Document", category="Physical", description="Paper documents"),
            EvidenceType(name="DNA Sample", category="Biological", description="Biological evidence"),
            EvidenceType(name="Computer", category="Digital", description="Computer evidence"),
            EvidenceType(name="Vehicle", category="Physical", description="Vehicle evidence")
        ]
        
        for evidence_type in evidence_types:
            existing = db.query(EvidenceType).filter(EvidenceType.name == evidence_type.name).first()
            if not existing:
                db.add(evidence_type)
        
        db.commit()
        
        # Create persons
        persons = [
            Person(
                name="Rafi Ahmad",
                alias="Rafi",
                date_of_birth=datetime(1985, 5, 15),
                nationality="Indonesian",
                address="Jakarta, Indonesia",
                phone="+62-812-345-6789",
                role=PersonRole.SUSPECT,
                description="Primary suspect in drug trafficking case",
                physical_description="Male, 35 years old, 170cm tall"
            ),
            Person(
                name="Nathalie",
                alias="Nat",
                date_of_birth=datetime(1990, 8, 22),
                nationality="Indonesian", 
                address="Bandung, Indonesia",
                phone="+62-813-456-7890",
                role=PersonRole.SUSPECT,
                description="Secondary suspect",
                physical_description="Female, 30 years old, 165cm tall"
            ),
            Person(
                name="John Doe",
                alias="JD",
                date_of_birth=datetime(1988, 3, 10),
                nationality="American",
                address="New York, USA",
                phone="+1-555-123-4567",
                role=PersonRole.WITNESS,
                description="Witness to the crime",
                physical_description="Male, 32 years old, 175cm tall"
            )
        ]
        
        for person in persons:
            existing = db.query(Person).filter(Person.name == person.name).first()
            if not existing:
                db.add(person)
        
        db.commit()
        
        # Create cases
        cases = [
            Case(
                case_number="CASE-2024-001",
                title="Buronan Maroko Interpol",
                description="International fugitive case involving drug trafficking",
                case_type="criminal",
                status="open",
                priority="high",
                incident_date=datetime(2024, 1, 15),
                reported_date=datetime(2024, 1, 16),
                jurisdiction="International",
                work_unit="Dirjen imigrasi 1",
                main_investigator_id=investigators[0].id,
                agency_id=agencies[0].id,
                evidence_count=3,
                analysis_progress=75
            ),
            Case(
                case_number="CASE-2024-002", 
                title="Penyelundupan Ganja",
                description="Drug smuggling case with evidence ID 83863932",
                case_type="criminal",
                status="open",
                priority="medium",
                incident_date=datetime(2024, 2, 10),
                reported_date=datetime(2024, 2, 11),
                jurisdiction="National",
                work_unit="Bareskrim Unit 1",
                main_investigator_id=investigators[1].id,
                agency_id=agencies[3].id,
                evidence_count=2,
                analysis_progress=50
            )
        ]
        
        for case in cases:
            existing = db.query(Case).filter(Case.case_number == case.case_number).first()
            if not existing:
                db.add(case)
        
        db.commit()
        
        # Create case-person associations
        case_persons = [
            CasePerson(
                case_id=cases[0].id,
                person_id=persons[0].id,
                person_type="suspect",
                is_primary=True,
                notes="Primary suspect in international drug trafficking"
            ),
            CasePerson(
                case_id=cases[0].id,
                person_id=persons[1].id,
                person_type="suspect",
                is_primary=False,
                notes="Secondary suspect, possible accomplice"
            ),
            CasePerson(
                case_id=cases[1].id,
                person_id=persons[2].id,
                person_type="witness",
                is_primary=False,
                notes="Witness to drug smuggling activities"
            )
        ]
        
        for case_person in case_persons:
            existing = db.query(CasePerson).filter(
                CasePerson.case_id == case_person.case_id,
                CasePerson.person_id == case_person.person_id
            ).first()
            if not existing:
                db.add(case_person)
        
        db.commit()
        
        # Create evidence
        evidence_items = [
            Evidence(
                evidence_id="EM001011",
                name="GPS Smartphone Samsung S21",
                description="GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian",
                source="Crime scene",
                summary="Mobile phone found at crime scene with GPS data",
                file_path="/evidence/EM001011/phone_data.zip",
                file_name="phone_data.zip",
                file_size="2.5MB",
                file_type="ZIP",
                case_id=cases[0].id,
                investigator_id=investigators[0].id,
                person_involved_id=persons[0].id,
                evidence_type_id=evidence_types[0].id,
                status=EvidenceStatus.ACTIVE
            ),
            Evidence(
                evidence_id="EM001012",
                name="Dialog Recording",
                description="Terdapat dialog seputar pembakaran dengan suspect lain",
                source="Wiretap",
                summary="Recorded conversation about arson with another suspect",
                file_path="/evidence/EM001012/recording.mp3",
                file_name="recording.mp3",
                file_size="15.2MB",
                file_type="MP3",
                case_id=cases[0].id,
                investigator_id=investigators[0].id,
                person_involved_id=persons[1].id,
                evidence_type_id=evidence_types[1].id,
                status=EvidenceStatus.ACTIVE
            )
        ]
        
        for evidence in evidence_items:
            existing = db.query(Evidence).filter(Evidence.evidence_id == evidence.evidence_id).first()
            if not existing:
                db.add(evidence)
        
        db.commit()
        
        print("✅ Sample data created successfully!")
        print(f"📊 Created:")
        print(f"  - {len(agencies)} Agencies")
        print(f"  - {len(investigators)} Investigators") 
        print(f"  - {len(evidence_types)} Evidence Types")
        print(f"  - {len(persons)} Persons")
        print(f"  - {len(cases)} Cases")
        print(f"  - {len(case_persons)} Case-Person associations")
        print(f"  - {len(evidence_items)} Evidence items")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Initializing sample data...")
    init_db()
    create_sample_data()
    print("✅ Sample data initialization completed!")
