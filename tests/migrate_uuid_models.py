#!/usr/bin/env python3
"""
Database Migration Script for UUID-based Case Management Models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging
import uuid

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    logger.info("🚀 UUID-based Case Management Model Migration")
    logger.info("==================================================")
    logger.info("🔄 Migrating to UUID-based models")
    logger.info("==================================================")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Drop existing tables
        logger.info("📝 Step 1: Dropping existing tables...")
        with engine.connect() as connection:
            # Drop tables in reverse dependency order
            connection.execute(text("DROP TABLE IF EXISTS case_persons CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS cases CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS work_units CASCADE"))
            connection.execute(text("DROP TABLE IF EXISTS agencies CASCADE"))
            connection.execute(text("DROP TYPE IF EXISTS casestatus CASCADE"))
            connection.commit()
        logger.info("✅ Existing tables dropped successfully")
        
        # Step 2: Create new tables
        logger.info("📝 Step 2: Creating new UUID-based tables...")
        from app.db.base import Base
        from app.case_management.models import Agency, WorkUnit, Case, CasePerson
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ New UUID-based tables created successfully")
        
        # Step 3: Insert sample data
        logger.info("📝 Step 3: Inserting sample data...")
        
        # Create agencies with UUID
        agencies_data = [
            {"name": "Police Department"},
            {"name": "FBI"},
            {"name": "Customs"},
            {"name": "Cyber Crime Unit"}
        ]
        
        agency_ids = []
        for agency_data in agencies_data:
            agency = Agency(**agency_data)
            db.add(agency)
        db.commit()
        
        # Get agency IDs
        agencies = db.query(Agency).all()
        agency_ids = [agency.id for agency in agencies]
        logger.info("✅ Agencies created with UUIDs")
        
        # Create work units with UUID
        work_units_data = [
            {"name": "Digital Forensics Unit", "agency_id": agency_ids[0]},
            {"name": "Cyber Investigation Unit", "agency_id": agency_ids[0]},
            {"name": "Financial Crimes Unit", "agency_id": agency_ids[1]},
            {"name": "Border Security Unit", "agency_id": agency_ids[2]}
        ]
        
        work_unit_ids = []
        for work_unit_data in work_units_data:
            work_unit = WorkUnit(**work_unit_data)
            db.add(work_unit)
        db.commit()
        
        # Get work unit IDs
        work_units = db.query(WorkUnit).all()
        work_unit_ids = [work_unit.id for work_unit in work_units]
        logger.info("✅ Work units created with UUIDs")
        
        # Create sample cases with UUID
        cases_data = [
            {
                "case_number": "CASE-2024-01-001",
                "title": "Cyber Fraud Investigation",
                "description": "Investigation of online fraud case",
                "main_investigator": "John Doe",
                "agency_id": agency_ids[0],
                "work_unit_id": work_unit_ids[0]
            },
            {
                "case_number": "CASE-2024-01-002", 
                "title": "Data Breach Analysis",
                "description": "Analysis of corporate data breach",
                "main_investigator": "Jane Smith",
                "agency_id": agency_ids[1],
                "work_unit_id": work_unit_ids[2]
            }
        ]
        
        case_ids = []
        for case_data in cases_data:
            case = Case(**case_data)
            db.add(case)
        db.commit()
        
        # Get case IDs
        cases = db.query(Case).all()
        case_ids = [case.id for case in cases]
        logger.info("✅ Sample cases created with UUIDs")
        
        # Step 4: Test the new models
        logger.info("📝 Step 4: Testing new UUID-based models...")
        
        # Test agencies
        agencies = db.query(Agency).all()
        logger.info(f"📊 Total agencies: {len(agencies)}")
        for agency in agencies:
            logger.info(f"  - Agency {agency.id}: {agency.name}")
        
        # Test work units
        work_units = db.query(WorkUnit).all()
        logger.info(f"📊 Total work units: {len(work_units)}")
        for work_unit in work_units:
            logger.info(f"  - Work Unit {work_unit.id}: {work_unit.name} (Agency: {work_unit.agency_id})")
        
        # Test cases
        cases = db.query(Case).all()
        logger.info(f"📊 Total cases: {len(cases)}")
        for case in cases:
            logger.info(f"  - Case {case.id}: {case.case_number} - {case.title}")
            logger.info(f"    Investigator: {case.main_investigator}")
            logger.info(f"    Agency ID: {case.agency_id}, Work Unit ID: {case.work_unit_id}")
            logger.info(f"    Status: {case.status}")
        
        # Test relationships
        logger.info("📝 Testing relationships...")
        for case in cases:
            if case.agency:
                logger.info(f"  - Case {case.case_number} belongs to Agency: {case.agency.name}")
            if case.work_unit:
                logger.info(f"  - Case {case.case_number} belongs to Work Unit: {case.work_unit.name}")
        
        logger.info("✅ Model testing completed successfully!")
        
        db.commit()
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()
    
    logger.info("\n🎉 UUID Migration completed successfully!")
    logger.info("✅ New UUID-based models created")
    logger.info("✅ Sample data inserted with UUIDs")
    logger.info("✅ Relationships tested")
    logger.info("✅ Database ready for use")

if __name__ == "__main__":
    run_migration()
