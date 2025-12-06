from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from typing import Generator
from app.core.config import settings
from app.db.base import Base
from app.case_management.models import Case
from app.evidence_management.models import Evidence
from app.suspect_management.models import Suspect


DB_TIMEZONE = "Asia/Jakarta"

if not all(c.isalnum() or c in ['/', '_', '-'] for c in DB_TIMEZONE):
    raise ValueError(f"Invalid timezone value: {DB_TIMEZONE}")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
    connect_args={"options": f"-c timezone={DB_TIMEZONE}"}
)

@event.listens_for(engine, "connect")
def set_timezone(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute(f"SET timezone = '{DB_TIMEZONE}'")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
