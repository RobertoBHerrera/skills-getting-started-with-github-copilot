"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""
""" Framework que convierte las funciones de python en endpoints http """
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from datetime import datetime
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")


# Pydantic model for review requests
class ReviewRequest(BaseModel):
    email: str
    rating: int = Field(ge=1, le=5)
    comment: str

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    # Sports related activities
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Wednesdays, 4:00 PM - 6:00 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly games",
        "schedule": "Mondays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ethan@mergington.edu", "ava@mergington.edu"]
    },
    # Artistic activities
    "Art Workshop": {
        "description": "Explore painting, drawing, and sculpture techniques",
        "schedule": "Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 16,
        "participants": ["isabella@mergington.edu", "liam@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce school plays and performances",
        "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": ["noah@mergington.edu", "amelia@mergington.edu"]
    },
    # Intellectual activities
    "Math Olympiad": {
        "description": "Prepare for math competitions and solve challenging problems",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 10,
        "participants": ["oliver@mergington.edu", "charlotte@mergington.edu"]
    },
    "Science Club": {
        "description": "Conduct experiments and explore scientific concepts",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 14,
        "participants": ["benjamin@mergington.edu", "ella@mergington.edu"]
    }
}


# In-memory reviews database
reviews = {activity_name: [] for activity_name in activities}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(sort_by: str = None):
    """Get all activities with review stats"""
    result = {}
    for name, data in activities.items():
        activity_reviews = reviews.get(name, [])
        review_count = len(activity_reviews)
        average_rating = None
        if review_count > 0:
            average_rating = round(sum(r["rating"] for r in activity_reviews) / review_count, 1)
        result[name] = {**data, "average_rating": average_rating, "review_count": review_count}

    if sort_by in ("rating_desc", "rating_asc"):
        reverse = sort_by == "rating_desc"
        sorted_items = sorted(
            result.items(),
            key=lambda x: (x[1]["average_rating"] is None, x[1]["average_rating"] or 0),
            reverse=reverse,
        )
        # When descending, nulls should be at the end (not reversed to top)
        if reverse:
            rated = [(k, v) for k, v in sorted_items if v["average_rating"] is not None]
            unrated = [(k, v) for k, v in sorted_items if v["average_rating"] is None]
            sorted_items = rated + unrated
        result = dict(sorted_items)

    return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/activities/{activity_name}/reviews")
def create_review(activity_name: str, review: ReviewRequest):
    """Create a review for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate reviewer is a participant
    if review.email not in activities[activity_name]["participants"]:
        raise HTTPException(status_code=403, detail="Only participants can leave reviews")

    # Validate no duplicate review
    for existing in reviews[activity_name]:
        if existing["email"] == review.email:
            raise HTTPException(status_code=400, detail="You have already reviewed this activity")

    # Validate comment is not empty/whitespace
    if not review.comment.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    # Validate comment length
    if len(review.comment) > 500:
        raise HTTPException(status_code=400, detail="Comment must be 500 characters or less")

    # Create review entry
    review_entry = {
        "email": review.email,
        "rating": review.rating,
        "comment": review.comment.strip(),
        "timestamp": datetime.now().isoformat()
    }
    reviews[activity_name].append(review_entry)
    return {"message": f"Review added for {activity_name}"}


@app.get("/activities/{activity_name}/reviews")
def get_reviews(activity_name: str):
    """Get all reviews for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity_reviews = reviews[activity_name]
    review_count = len(activity_reviews)
    average_rating = None
    if review_count > 0:
        average_rating = round(sum(r["rating"] for r in activity_reviews) / review_count, 1)

    return {
        "reviews": activity_reviews,
        "average_rating": average_rating,
        "review_count": review_count
    }


@app.delete("/activities/{activity_name}/reviews")
def delete_review(activity_name: str, email: str):
    """Delete a review from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Find and remove the review
    for i, review in enumerate(reviews[activity_name]):
        if review["email"] == email:
            reviews[activity_name].pop(i)
            return {"message": f"Review deleted from {activity_name}"}

    raise HTTPException(status_code=404, detail="Review not found")
