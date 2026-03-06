"""
Tests for the Mergington High School API

Uses pytest with FastAPI TestClient and follows the AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from copy import deepcopy

from src.app import app, activities, reviews


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


@pytest.fixture(autouse=True)
def reset_reviews():
    """Reset reviews to empty state before each test."""
    for activity_name in reviews:
        reviews[activity_name] = []
    yield
    for activity_name in reviews:
        reviews[activity_name] = []


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


class TestCreateReview:
    """Tests for the POST /activities/{activity_name}/reviews endpoint."""

    def test_create_review_success(self, client):
        """Test successful review creation."""
        # Arrange
        activity_name = "Chess Club"
        review_data = {
            "email": "michael@mergington.edu",
            "rating": 5,
            "comment": "Great club, very challenging!"
        }

        # Act
        response = client.post(
            f"/activities/{activity_name}/reviews",
            json=review_data
        )

        # Assert
        assert response.status_code == 200
        assert "Review added" in response.json()["message"]
        assert len(reviews[activity_name]) == 1
        assert reviews[activity_name][0]["email"] == "michael@mergington.edu"

    def test_create_review_activity_not_found(self, client):
        """Test review for non-existent activity returns 404."""
        # Arrange
        review_data = {"email": "test@mergington.edu", "rating": 5, "comment": "Great!"}

        # Act
        response = client.post("/activities/Nonexistent/reviews", json=review_data)

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_create_review_not_participant(self, client):
        """Test non-participant cannot leave review (403)."""
        # Arrange
        review_data = {
            "email": "stranger@mergington.edu",
            "rating": 4,
            "comment": "I wish I was here"
        }

        # Act
        response = client.post("/activities/Chess Club/reviews", json=review_data)

        # Assert
        assert response.status_code == 403
        assert "Only participants" in response.json()["detail"]

    def test_create_review_duplicate(self, client):
        """Test duplicate review from same email returns 400."""
        # Arrange
        review_data = {
            "email": "michael@mergington.edu",
            "rating": 5,
            "comment": "Great club!"
        }
        client.post("/activities/Chess Club/reviews", json=review_data)

        # Act
        response = client.post("/activities/Chess Club/reviews", json=review_data)

        # Assert
        assert response.status_code == 400
        assert "already reviewed" in response.json()["detail"]

    def test_create_review_invalid_rating_low(self, client):
        """Test rating below 1 returns 422."""
        # Arrange
        review_data = {
            "email": "michael@mergington.edu",
            "rating": 0,
            "comment": "Bad"
        }

        # Act
        response = client.post("/activities/Chess Club/reviews", json=review_data)

        # Assert
        assert response.status_code == 422

    def test_create_review_invalid_rating_high(self, client):
        """Test rating above 5 returns 422."""
        # Arrange
        review_data = {
            "email": "michael@mergington.edu",
            "rating": 6,
            "comment": "Too good"
        }

        # Act
        response = client.post("/activities/Chess Club/reviews", json=review_data)

        # Assert
        assert response.status_code == 422

    def test_create_review_empty_comment(self, client):
        """Test empty comment returns 400."""
        # Arrange
        review_data = {
            "email": "michael@mergington.edu",
            "rating": 4,
            "comment": "   "
        }

        # Act
        response = client.post("/activities/Chess Club/reviews", json=review_data)

        # Assert
        assert response.status_code == 400
        assert "Comment cannot be empty" in response.json()["detail"]

    def test_create_review_comment_too_long(self, client):
        """Test comment over 500 chars returns 400."""
        # Arrange
        review_data = {
            "email": "michael@mergington.edu",
            "rating": 4,
            "comment": "A" * 501
        }

        # Act
        response = client.post("/activities/Chess Club/reviews", json=review_data)

        # Assert
        assert response.status_code == 400
        assert "500 characters" in response.json()["detail"]


class TestGetReviews:
    """Tests for the GET /activities/{activity_name}/reviews endpoint."""

    def test_get_reviews_with_reviews(self, client):
        """Test getting reviews with calculated average."""
        # Arrange
        client.post("/activities/Chess Club/reviews", json={
            "email": "michael@mergington.edu", "rating": 5, "comment": "Excellent!"
        })
        client.post("/activities/Chess Club/reviews", json={
            "email": "daniel@mergington.edu", "rating": 3, "comment": "OK"
        })

        # Act
        response = client.get("/activities/Chess Club/reviews")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["review_count"] == 2
        assert data["average_rating"] == 4.0
        assert len(data["reviews"]) == 2

    def test_get_reviews_empty(self, client):
        """Test getting reviews for activity with no reviews."""
        # Arrange
        # (no reviews created)

        # Act
        response = client.get("/activities/Chess Club/reviews")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["review_count"] == 0
        assert data["average_rating"] is None
        assert data["reviews"] == []

    def test_get_reviews_activity_not_found(self, client):
        """Test getting reviews for non-existent activity returns 404."""
        # Act
        response = client.get("/activities/Nonexistent/reviews")

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestDeleteReview:
    """Tests for the DELETE /activities/{activity_name}/reviews endpoint."""

    def test_delete_review_success(self, client):
        """Test successful review deletion."""
        # Arrange
        client.post("/activities/Chess Club/reviews", json={
            "email": "michael@mergington.edu", "rating": 5, "comment": "Great!"
        })

        # Act
        response = client.delete(
            "/activities/Chess Club/reviews",
            params={"email": "michael@mergington.edu"}
        )

        # Assert
        assert response.status_code == 200
        assert "Review deleted" in response.json()["message"]
        assert len(reviews["Chess Club"]) == 0

    def test_delete_review_not_found(self, client):
        """Test deleting non-existent review returns 404."""
        # Act
        response = client.delete(
            "/activities/Chess Club/reviews",
            params={"email": "nobody@mergington.edu"}
        )

        # Assert
        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]

    def test_delete_review_activity_not_found(self, client):
        """Test deleting review from non-existent activity returns 404."""
        # Act
        response = client.delete(
            "/activities/Nonexistent/reviews",
            params={"email": "test@mergington.edu"}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestActivitiesWithRatings:
    """Tests for GET /activities with review rating fields and sorting."""

    def test_activities_include_rating_fields(self, client):
        """Test that activities include average_rating and review_count."""
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        for name, activity in data.items():
            assert "average_rating" in activity
            assert "review_count" in activity
            assert activity["review_count"] == 0
            assert activity["average_rating"] is None

    def test_activities_sort_by_rating_desc(self, client):
        """Test sorting activities by rating descending."""
        # Arrange - add reviews to give different ratings
        client.post("/activities/Chess Club/reviews", json={
            "email": "michael@mergington.edu", "rating": 5, "comment": "Best!"
        })
        client.post("/activities/Programming Class/reviews", json={
            "email": "emma@mergington.edu", "rating": 3, "comment": "Good"
        })

        # Act
        response = client.get("/activities", params={"sort_by": "rating_desc"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        keys = list(data.keys())
        # Chess Club (5.0) should come before Programming Class (3.0)
        assert keys.index("Chess Club") < keys.index("Programming Class")
        # Unrated activities should be at the end
        unrated_start = None
        for i, name in enumerate(keys):
            if data[name]["average_rating"] is None:
                unrated_start = i
                break
        if unrated_start is not None:
            for name in keys[unrated_start:]:
                assert data[name]["average_rating"] is None

    def test_activities_sort_by_rating_asc(self, client):
        """Test sorting activities by rating ascending."""
        # Arrange
        client.post("/activities/Chess Club/reviews", json={
            "email": "michael@mergington.edu", "rating": 2, "comment": "Meh"
        })
        client.post("/activities/Programming Class/reviews", json={
            "email": "emma@mergington.edu", "rating": 5, "comment": "Amazing!"
        })

        # Act
        response = client.get("/activities", params={"sort_by": "rating_asc"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        keys = list(data.keys())
        # Chess Club (2.0) should come before Programming Class (5.0)
        assert keys.index("Chess Club") < keys.index("Programming Class")
