from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base

from app.analytics.shared.models import *
from app.case_management.models import *
from app.evidence_management.models import *
from app.suspect_management.models import *
from app.auth.models import *


def init_db():
    Base.metadata.create_all(bind=engine)
