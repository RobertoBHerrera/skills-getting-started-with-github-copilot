"""
Tests for the Mergington High School API

Uses pytest with FastAPI TestClient and follows the AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy

from src.app import app, activities


# Store original activities state for reset between tests
_original_activities = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test."""
    # Arrange - restore original state
    for activity_name in activities:
        activities[activity_name]["participants"] = deepcopy(
            _original_activities[activity_name]["participants"]
        )
    yield
    # Cleanup after test (restore again)
    for activity_name in activities:
        activities[activity_name]["participants"] = deepcopy(
            _original_activities[activity_name]["participants"]
        )


@pytest.fixture
def client():
    """Create a TestClient instance for testing."""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_index(self, client):
        """Test that root path redirects to the static index page."""
        # Arrange
        # (no special setup needed)

        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        assert "Mergington High School" in response.text


class TestGetActivities:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned."""
        # Arrange
        expected_activity_count = 9

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_activity_count

    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has the required fields."""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity_name, activity_data in data.items():
            assert required_fields.issubset(activity_data.keys()), \
                f"Activity '{activity_name}' missing required fields"


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        # Arrange
        activity_name = "Chess Club"
        test_email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert test_email in activities[activity_name]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404."""
        # Arrange
        invalid_activity = "Nonexistent Activity"
        test_email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_returns_error(self, client):
        """Test that signing up twice returns a 400 error."""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity."""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert existing_email not in activities[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404."""
        # Arrange
        invalid_activity = "Nonexistent Activity"
        test_email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/unregister",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up_returns_error(self, client):
        """Test unregistering when not signed up returns 400."""
        # Arrange
        activity_name = "Chess Club"
        non_participant_email = "notinclub@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": non_participant_email}
        )

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
