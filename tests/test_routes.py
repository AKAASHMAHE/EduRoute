from datetime import date, timedelta
import pytest
from app import create_app
from app.models import db, Journey
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client


def test_index_route(client):
    """Test landing page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Never Miss Your Train Booking Opening Date" in response.data


def test_dashboard_empty_route(client):
    """Test dashboard page loads with empty state."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"No Journeys Found" in response.data


def test_add_journey_route(client):
    """Test adding a journey via form submission."""
    future_date = (date.today() + timedelta(days=45)).strftime("%Y-%m-%d")

    # GET request
    get_res = client.get("/journey/add")
    assert get_res.status_code == 200

    # POST request
    post_res = client.post(
        "/journey/add",
        data={
            "trip_name": "Diwali Vacation",
            "source": "Chennai",
            "destination": "Coimbatore",
            "train_name": "Cheran Express",
            "journey_date": future_date,
            "reminder_enabled": "true",
        },
        follow_redirects=True,
    )
    assert post_res.status_code == 200
    assert b"Diwali Vacation" in post_res.data
    assert b"Chennai" in post_res.data


def test_journey_detail_and_edit_and_delete(client):
    """Test journey detail, edit, and deletion cycle."""
    future_date = (date.today() + timedelta(days=50)).strftime("%Y-%m-%d")

    # Add journey directly
    with client.application.app_context():
        j = Journey(
            trip_name="Original Name",
            source="Mumbai",
            destination="Pune",
            journey_date=date.today() + timedelta(days=50),
        )
        db.session.add(j)
        db.session.commit()
        j_id = j.id

    # View details
    detail_res = client.get(f"/journey/{j_id}")
    assert detail_res.status_code == 200
    assert b"Original Name" in detail_res.data

    # Edit journey
    new_future_date = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")
    edit_res = client.post(
        f"/journey/{j_id}/edit",
        data={
            "trip_name": "Updated Name",
            "source": "Mumbai",
            "destination": "Pune",
            "train_name": "Deccan Queen",
            "journey_date": new_future_date,
            "reminder_enabled": "true",
        },
        follow_redirects=True,
    )
    assert edit_res.status_code == 200
    assert b"Updated Name" in edit_res.data

    # Delete journey
    del_res = client.post(f"/journey/{j_id}/delete", follow_redirects=True)
    assert del_res.status_code == 200
    assert b"deleted successfully" in del_res.data


def test_api_calculate_booking_date(client):
    """Test JSON API for live booking date calculation."""
    future_date = (date.today() + timedelta(days=70)).strftime("%Y-%m-%d")
    res = client.post(
        "/api/v1/calculate-booking-date",
        json={"journey_date": future_date},
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert "expected_booking_date" in json_data
    assert json_data["days_until_journey"] == 70


def test_invalid_journey_id_404(client):
    """Test 404 page when requesting non-existent journey ID."""
    res = client.get("/journey/99999")
    assert res.status_code == 404
    assert b"404" in res.data
