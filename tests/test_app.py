"""
Backend tests for the Mergington High School Activities API.

All tests follow the AAA (Arrange-Act-Assert) pattern.
"""

import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    """Provide a test client with a fresh copy of the activities database."""
    # Arrange: snapshot the in-memory database and restore it after each test
    original = copy.deepcopy(activities)
    yield TestClient(app)
    activities.clear()
    activities.update(original)


class TestRoot:
    def test_root_redirects_to_static_index(self, client):
        # Arrange
        url = "/"

        # Act
        response = client.get(url, follow_redirects=False)

        # Assert
        assert response.status_code in (302, 307)
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    def test_get_activities_returns_ok(self, client):
        # Arrange
        url = "/activities"

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200

    def test_get_activities_contains_expected_activity(self, client):
        # Arrange
        url = "/activities"

        # Act
        data = client.get(url).json()

        # Assert
        assert "Chess Club" in data
        assert data["Chess Club"]["max_participants"] == 12

    def test_activities_have_required_fields(self, client):
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        data = client.get("/activities").json()

        # Assert
        for name, details in data.items():
            assert required_fields.issubset(details.keys()), f"{name} is missing fields"


class TestSignupForActivity:
    def test_signup_succeeds_for_new_student(self, client):
        # Arrange
        activity = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        assert response.status_code == 200
        assert email in activities[activity]["participants"]
        assert response.json()["message"] == f"Signed up {email} for {activity}"

    def test_signup_fails_for_unknown_activity(self, client):
        # Arrange
        activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_fails_for_duplicate_registration(self, client):
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"  # already registered in sample data

        # Act
        response = client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is already signed up"

    def test_duplicate_signup_does_not_add_participant_twice(self, client):
        # Arrange
        activity = "Chess Club"
        email = "michael@mergington.edu"
        count_before = activities[activity]["participants"].count(email)

        # Act
        client.post(f"/activities/{activity}/signup", params={"email": email})

        # Assert
        assert activities[activity]["participants"].count(email) == count_before == 1
