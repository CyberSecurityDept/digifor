"""
Pytest Configuration
Test fixtures and configuration
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_case_data():
    return {
        "case_number": "CASE-2024-001",
        "title": "Test Case",
        "description": "Test case description",
        "case_type": "criminal",
        "status": "open",
        "priority": "medium",
        "case_officer": "John Doe",
        "work_unit": "Test Unit"
    }


@pytest.fixture
def sample_evidence_data():
    return {
        "evidence_number": "EVID-2024-001",
        "title": "Test Evidence",
        "description": "Test evidence description",
        "case_id": "00000000-0000-0000-0000-000000000001",
        "status": "collected",
        "collected_by": "Jane Doe",
        "collected_location": "Test Location"
    }


@pytest.fixture
def sample_person_data():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "nationality": "US",
        "phone": "123-456-7890",
        "email": "john.doe@example.com",
        "status": "active",
        "is_primary_suspect": False,
        "risk_level": "medium"
    }
