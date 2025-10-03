from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Disable SQLAlchemy logging completely
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.db.base import Base
    # Import models to register them with SQLAlchemy
    from app.case_management.models import Case, CasePerson
    from app.evidence_management.models import Evidence, EvidenceType
    from app.suspect_management.models import Person
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
