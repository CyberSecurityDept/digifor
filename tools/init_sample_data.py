import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy.orm import Session
from app.db.session import get_db, init_db
from app.case_management.models import Agency, Case
from app.evidence_management.models import Evidence
from app.suspect_management.models import Suspect
from datetime import datetime, timedelta, timezone
import uuid


def create_sample_data():
    db = next(get_db())
    
    try:
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
        
        suspects = [
            Suspect(
                name="Rafi Ahmad",
                case_name="Buronan Maroko Interpol",
                investigator="Solehun",
                status="Suspect",
                is_unknown=False
            ),
            Suspect(
                name="Nathalie",
                case_name="Buronan Maroko Interpol",
                investigator="Solehun",
                status="Suspect",
                is_unknown=False
            ),
            Suspect(
                name="John Doe",
                case_name="Penyelundupan Ganja",
                investigator="Robert",
                status="Witness",
                is_unknown=False
            )
        ]
        
        for suspect in suspects:
            existing = db.query(Suspect).filter(Suspect.name == suspect.name).first()
            if not existing:
                db.add(suspect)
        
        db.commit()
        
        cases = [
            Case(
                case_number="CASE-2024-001",
                title="Buronan Maroko Interpol",
                description="International fugitive case involving drug trafficking",
                status="Open",
                main_investigator="Solehun",
                agency_id=agencies[0].id
            ),
            Case(
                case_number="CASE-2024-002", 
                title="Penyelundupan Ganja",
                description="Drug smuggling case with evidence ID 83863932",
                status="Open",
                main_investigator="Robert",
                agency_id=agencies[3].id
            )
        ]
        
        for case in cases:
            existing = db.query(Case).filter(Case.case_number == case.case_number).first()
            if not existing:
                db.add(case)
        
        db.commit()
        
        suspects[0].case_id = cases[0].id
        suspects[1].case_id = cases[0].id
        suspects[2].case_id = cases[1].id
        db.commit()
        
        evidence_items = [
            Evidence(
                evidence_number="EM001011",
                title="GPS Smartphone Samsung S21",
                description="GPS handphone suspect menyatakan posisi yang berada di TKP pada saat kejadian",
                file_path="/evidence/EM001011/phone_data.zip",
                file_size=2621440,
                file_type="application/zip",
                file_extension="zip",
                case_id=cases[0].id,
                investigator="Solehun",
                suspect_id=suspects[0].id,
                source="Mobile Phone",
                collected_date=datetime.now(timezone.utc)
            ),
            Evidence(
                evidence_number="EM001012",
                title="Dialog Recording",
                description="Terdapat dialog seputar pembakaran dengan suspect lain",
                file_path="/evidence/EM001012/recording.mp3",
                file_size=15938355,
                file_type="audio/mpeg",
                file_extension="mp3",
                case_id=cases[0].id,
                investigator="Solehun",
                suspect_id=suspects[1].id,
                source="Document",
                collected_date=datetime.now(timezone.utc)
            )
        ]
        
        for evidence in evidence_items:
            existing = db.query(Evidence).filter(Evidence.evidence_number == evidence.evidence_number).first()
            if not existing:
                db.add(evidence)
        
        db.commit()
        
        print("Sample data created successfully!")
        print(f"Created:")
        print(f" - {len(agencies)} Agencies")
        print(f" - {len(suspects)} Suspects")
        print(f" - {len(cases)} Cases")
        print(f" - {len(evidence_items)} Evidence items")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing sample data...")
    init_db()
    create_sample_data()
    print("Sample data initialization completed!")
