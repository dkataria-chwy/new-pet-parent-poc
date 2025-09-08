import pytest
from fastapi.testclient import TestClient
from main import app
from database import db
import os

# Use a test database
TEST_DB_PATH = "test_chewy_journey.db"

@pytest.fixture(scope="function")
def client():
    # Use test database
    db.db_path = TEST_DB_PATH
    db.init_db()
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up test database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_pet(client):
    pet_data = {
        "name": "Max",
        "species": "dog",
        "breed": "Golden Retriever",
        "ageMonths": 24,
        "allergies": "None",
        "about": "Very energetic and friendly"
    }
    
    response = client.post("/profile", json=pet_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Max"
    assert data["species"] == "dog"
    assert data["breed"] == "Golden Retriever"
    assert data["ageMonths"] == 24
    assert "id" in data

def test_initialize_journey(client):
    # First create a pet
    pet_data = {
        "name": "Max",
        "species": "dog",
        "breed": "Golden Retriever",
        "ageMonths": 24
    }
    
    pet_response = client.post("/profile", json=pet_data)
    pet_id = pet_response.json()["id"]
    
    # Initialize journey
    journey_data = {
        "petId": pet_id,
        "months": 15
    }
    
    response = client.post("/journey", json=journey_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["petId"] == pet_id
    assert data["current"] == 0
    assert data["totalMonths"] == 15
    assert data["decisions"] == {}
    assert "id" in data

def test_update_journey_state_decision(client):
    # Setup pet and journey
    pet_data = {"name": "Max", "species": "dog", "breed": "Golden Retriever", "ageMonths": 24}
    pet_response = client.post("/profile", json=pet_data)
    pet_id = pet_response.json()["id"]
    
    journey_data = {"petId": pet_id, "months": 15}
    journey_response = client.post("/journey", json=journey_data)
    journey_id = journey_response.json()["id"]
    
    # Make a decision
    decision_data = {
        "action": "setDecision",
        "journeyId": journey_id,
        "monthIdx": 0,
        "section": "subscriptions",
        "value": True
    }
    
    response = client.patch("/journey/state", json=decision_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["decisions"]["0"]["subscriptions"] == True

def test_get_recommendations(client):
    # Setup pet and journey
    pet_data = {"name": "Max", "species": "dog", "breed": "Golden Retriever", "ageMonths": 24}
    pet_response = client.post("/profile", json=pet_data)
    pet_id = pet_response.json()["id"]
    
    journey_data = {"petId": pet_id, "months": 15}
    journey_response = client.post("/journey", json=journey_data)
    journey_id = journey_response.json()["id"]
    
    # Get recommendations
    response = client.get(f"/recommendations?journeyId={journey_id}&monthIdx=0")
    assert response.status_code == 200
    
    data = response.json()
    assert "summaryWhy" in data
    assert "subscriptions" in data
    assert "bundles" in data
    assert "singles" in data

def test_ai_recommendations(client):
    # Setup pet and journey
    pet_data = {"name": "Max", "species": "dog", "breed": "Golden Retriever", "ageMonths": 24}
    pet_response = client.post("/profile", json=pet_data)
    pet_id = pet_response.json()["id"]
    
    journey_data = {"petId": pet_id, "months": 15}
    journey_response = client.post("/journey", json=journey_data)
    journey_id = journey_response.json()["id"]
    
    # Get AI recommendations
    ai_data = {
        "journeyId": journey_id,
        "monthIdx": 0,
        "note": "Max has been teething a lot lately"
    }
    
    response = client.post("/ai/recs", json=ai_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "summary" in data
    assert "items" in data
    assert len(data["items"]) > 0

def test_log_event(client):
    event_data = {
        "type": "test_event",
        "journeyId": "test-journey-id",
        "meta": {"test": "data"}
    }
    
    response = client.post("/events", json=event_data)
    assert response.status_code == 200
    assert response.json() == {"status": "logged"}

def test_complete_month_flow(client):
    # Setup pet and journey
    pet_data = {"name": "Max", "species": "dog", "breed": "Golden Retriever", "ageMonths": 24}
    pet_response = client.post("/profile", json=pet_data)
    pet_id = pet_response.json()["id"]
    
    journey_data = {"petId": pet_id, "months": 15}
    journey_response = client.post("/journey", json=journey_data)
    journey_id = journey_response.json()["id"]
    
    # Make decisions for all sections
    sections = ["subscriptions", "bundles", "singles"]
    for section in sections:
        decision_data = {
            "action": "setDecision",
            "journeyId": journey_id,
            "monthIdx": 0,
            "section": section,
            "value": True
        }
        client.patch("/journey/state", json=decision_data)
    
    # Complete the month
    complete_data = {
        "action": "completeMonth",
        "journeyId": journey_id,
        "monthIdx": 0
    }
    
    response = client.patch("/journey/state", json=complete_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["current"] == 1  # Should advance to next month
