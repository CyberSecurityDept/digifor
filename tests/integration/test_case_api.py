import pytest
from fastapi.testclient import TestClient


class TestCaseAPI:
    def test_create_case(self, client: TestClient, sample_case_data: dict):
        response = client.post("/api/v1/cases/", json=sample_case_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["status"] == 201
        assert data["message"] == "Case created successfully"
        assert data["data"]["case_number"] == sample_case_data["case_number"]
    
    def test_get_case(self, client: TestClient, sample_case_data: dict):
        create_response = client.post("/api/v1/cases/", json=sample_case_data)
        case_id = create_response.json()["data"]["id"]
        
        response = client.get(f"/api/v1/cases/{case_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == 200
        assert data["data"]["id"] == case_id
    
    def test_get_cases_list(self, client: TestClient, sample_case_data: dict):
        for i in range(3):
            case_data = {**sample_case_data, "case_number": f"CASE-{i}"}
            client.post("/api/v1/cases/", json=case_data)
        
        response = client.get("/api/v1/cases/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == 200
        assert len(data["data"]) == 3
    
    def test_update_case(self, client: TestClient, sample_case_data: dict):
        create_response = client.post("/api/v1/cases/", json=sample_case_data)
        case_id = create_response.json()["data"]["id"]
        
        update_data = {"title": "Updated Title", "status": "closed"}
        response = client.put(f"/api/v1/cases/{case_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["title"] == "Updated Title"
        assert data["data"]["status"] == "closed"
    
    def test_delete_case(self, client: TestClient, sample_case_data: dict):
        create_response = client.post("/api/v1/cases/", json=sample_case_data)
        case_id = create_response.json()["data"]["id"]
        
        response = client.delete(f"/api/v1/cases/{case_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == 200
        assert data["message"] == "Case deleted successfully"
    
    def test_close_case(self, client: TestClient, sample_case_data: dict):
        create_response = client.post("/api/v1/cases/", json=sample_case_data)
        case_id = create_response.json()["data"]["id"]
        
        response = client.post(f"/api/v1/cases/{case_id}/close", params={"reason": "Test closure"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["status"] == "closed"
    
    def test_reopen_case(self, client: TestClient, sample_case_data: dict):
        create_response = client.post("/api/v1/cases/", json=sample_case_data)
        case_id = create_response.json()["data"]["id"]
        
        client.post(f"/api/v1/cases/{case_id}/close", params={"reason": "Test closure"})
        
        response = client.post(f"/api/v1/cases/{case_id}/reopen", params={"reason": "Test reopening"})
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["status"] == "reopened"
    
    def test_get_case_statistics(self, client: TestClient, sample_case_data: dict):
        for i in range(3):
            case_data = {**sample_case_data, "case_number": f"CASE-{i}"}
            client.post("/api/v1/cases/", json=case_data)
        
        response = client.get("/api/v1/cases/statistics/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == 200
        assert data["data"]["total_cases"] == 3
