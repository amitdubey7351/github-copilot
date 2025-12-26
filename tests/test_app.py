import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of activities"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_activities_have_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        for activity_name, activity_details in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_details, dict)
            assert required_fields.issubset(activity_details.keys())
            assert isinstance(activity_details["participants"], list)
            assert isinstance(activity_details["max_participants"], int)
    
    def test_activities_not_empty(self, client):
        """Test that activities list is not empty"""
        response = client.get("/activities")
        activities = response.json()
        assert len(activities) > 0


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@example.com" in data["message"]
    
    def test_signup_to_nonexistent_activity(self, client):
        """Test signup to a nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonExistent/signup?email=test@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_email(self, client):
        """Test that duplicate signups are rejected"""
        email = "duplicate@example.com"
        activity = "Tennis%20Club"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "unregister@example.com"
        activity = "Art%20Studio"
        
        # First signup
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister",
            json={"email": email}
        )
        assert unregister_response.status_code == 200
        data = unregister_response.json()
        assert "Removed" in data["message"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """Test unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonExistent/unregister",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 404
    
    def test_unregister_nonexistent_participant(self, client):
        """Test unregister of nonexistent participant returns 404"""
        response = client.post(
            "/activities/Music%20Band/unregister",
            json={"email": "nonexistent@example.com"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_unregister_actually_removes_participant(self, client):
        """Test that unregister actually removes the participant from the list"""
        email = "verify@example.com"
        activity = "Programming%20Class"
        
        # Signup
        client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Verify participant is in list
        response1 = client.get("/activities")
        activities1 = response1.json()
        assert email in activities1["Programming Class"]["participants"]
        
        # Unregister
        client.post(
            f"/activities/{activity}/unregister",
            json={"email": email}
        )
        
        # Verify participant is removed
        response2 = client.get("/activities")
        activities2 = response2.json()
        assert email not in activities2["Programming Class"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "static/index.html" in response.headers["location"]
