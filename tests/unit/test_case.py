"""
Case Management Unit Tests
Test case management functionality
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.case_management.service import case_service
from app.case_management.schemas import CaseCreate, CaseUpdate


class TestCaseService:
    """Test case service functionality"""
    
    def test_create_case(self, db_session: Session, sample_case_data: dict):
        """Test case creation"""
        case_data = CaseCreate(**sample_case_data)
        case = case_service.create_case(db_session, case_data)
        
        assert case.case_number == sample_case_data["case_number"]
        assert case.title == sample_case_data["title"]
        assert case.status == "open"
    
    def test_get_case(self, db_session: Session, sample_case_data: dict):
        """Test case retrieval"""
        case_data = CaseCreate(**sample_case_data)
        case = case_service.create_case(db_session, case_data)
        
        retrieved_case = case_service.get_case(db_session, case.id)
        assert retrieved_case.id == case.id
        assert retrieved_case.case_number == case.case_number
    
    def test_update_case(self, db_session: Session, sample_case_data: dict):
        """Test case update"""
        case_data = CaseCreate(**sample_case_data)
        case = case_service.create_case(db_session, case_data)
        
        update_data = CaseUpdate(title="Updated Title", status="closed")
        updated_case = case_service.update_case(db_session, case.id, update_data)
        
        assert updated_case.title == "Updated Title"
        assert updated_case.status == "closed"
    
    def test_delete_case(self, db_session: Session, sample_case_data: dict):
        """Test case deletion"""
        case_data = CaseCreate(**sample_case_data)
        case = case_service.create_case(db_session, case_data)
        
        success = case_service.delete_case(db_session, case.id)
        assert success is True
    
    def test_close_case(self, db_session: Session, sample_case_data: dict):
        """Test case closure"""
        case_data = CaseCreate(**sample_case_data)
        case = case_service.create_case(db_session, case_data)
        
        closed_case = case_service.close_case(db_session, case.id, "Test closure reason")
        assert closed_case.status == "closed"
        assert closed_case.status_change_reason == "Test closure reason"
    
    def test_reopen_case(self, db_session: Session, sample_case_data: dict):
        """Test case reopening"""
        case_data = CaseCreate(**sample_case_data)
        case = case_service.create_case(db_session, case_data)
        
        # First close the case
        case_service.close_case(db_session, case.id, "Test closure")
        
        # Then reopen it
        reopened_case = case_service.reopen_case(db_session, case.id, "Test reopening")
        assert reopened_case.status == "reopened"
        assert reopened_case.reopened_count == 1
    
    def test_get_case_statistics(self, db_session: Session, sample_case_data: dict):
        """Test case statistics"""
        # Create multiple cases
        for i in range(3):
            case_data = CaseCreate(**{**sample_case_data, "case_number": f"CASE-{i}"})
            case_service.create_case(db_session, case_data)
        
        stats = case_service.get_case_statistics(db_session)
        assert stats["total_cases"] == 3
        assert stats["open_cases"] == 3
        assert stats["closed_cases"] == 0
