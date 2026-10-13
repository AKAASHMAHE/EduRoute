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


def test_api_journeys_list_and_detail(client):
    """Test GET /api/v1/journeys and GET /api/v1/journeys/<id>."""
    with client.application.app_context():
        j = Journey(
            trip_name="API Express",
            source="Delhi",
            destination="Jaipur",
            journey_date=date.today() + timedelta(days=20),
        )
        db.session.add(j)
        db.session.commit()
        j_id = j.id

    # Test list endpoint
    res_list = client.get("/api/v1/journeys")
    assert res_list.status_code == 200
    data = res_list.get_json()
    assert data["success"] is True
    assert data["count"] >= 1
    assert any(item["id"] == j_id for item in data["journeys"])

    # Test detail endpoint
    res_detail = client.get(f"/api/v1/journeys/{j_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.get_json()
    assert detail_data["success"] is True
    assert detail_data["journey"]["trip_name"] == "API Express"

    # Test detail endpoint 404
    res_detail_404 = client.get("/api/v1/journeys/99999")
    assert res_detail_404.status_code == 404
    assert res_detail_404.get_json()["success"] is False


def test_api_calculate_booking_date_bad_input(client):
    """Test API calculate-booking-date with missing or invalid date."""
    # Missing date
    res_missing = client.post("/api/v1/calculate-booking-date", json={})
    assert res_missing.status_code == 400
    assert res_missing.get_json()["success"] is False

    # Invalid date format
    res_invalid = client.post("/api/v1/calculate-booking-date", json={"journey_date": "invalid-date"})
    assert res_invalid.status_code == 400
    assert "Invalid date format" in res_invalid.get_json()["error"]


def test_toggle_reminder_route(client):
    """Test toggling reminder on a journey."""
    with client.application.app_context():
        j = Journey(
            trip_name="Reminder Trip",
            source="Bangalore",
            destination="Mysore",
            journey_date=date.today() + timedelta(days=25),
            reminder_enabled=True,
        )
        db.session.add(j)
        db.session.commit()
        j_id = j.id

    # Toggle off
    res = client.post(f"/journey/{j_id}/toggle-reminder", follow_redirects=True)
    assert res.status_code == 200
    with client.application.app_context():
        updated = db.session.get(Journey, j_id)
        assert updated.reminder_enabled is False

    # Toggle on
    res2 = client.post(f"/journey/{j_id}/toggle-reminder", follow_redirects=True)
    assert res2.status_code == 200
    with client.application.app_context():
        updated2 = db.session.get(Journey, j_id)
        assert updated2.reminder_enabled is True


def test_dashboard_search_and_filters(client):
    """Test dashboard search query and status filter."""
    with client.application.app_context():
        j1 = Journey(
            trip_name="Kolkata Mail",
            source="Howrah",
            destination="Delhi",
            journey_date=date.today() + timedelta(days=70),
        )
        j2 = Journey(
            trip_name="Goa Express",
            source="Vasco",
            destination="Pune",
            journey_date=date.today() + timedelta(days=10),
        )
        db.session.add_all([j1, j2])
        db.session.commit()

    # Search for Kolkata
    res = client.get("/dashboard?q=Kolkata")
    assert res.status_code == 200
    assert b"Kolkata Mail" in res.data
    assert b"Goa Express" not in res.data

    # Filter status upcoming
    res_status = client.get("/dashboard?status=upcoming")
    assert res_status.status_code == 200


def test_csrf_protection_enforcement():
    """Test that CSRF protection rejects requests when enabled and token is missing."""
    class CSRFActiveConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        WTF_CSRF_ENABLED = True
        SECRET_KEY = "test-csrf-secret"

    app = create_app(CSRFActiveConfig)
    with app.test_client() as c:
        with app.app_context():
            db.create_all()

        # Try to add journey without CSRF token -> should return 400 Bad Request
        res_no_token = c.post(
            "/journey/add",
            data={
                "trip_name": "No CSRF Trip",
                "source": "A",
                "destination": "B",
                "journey_date": "2026-12-01",
            },
        )
        assert res_no_token.status_code == 400
        assert b"CSRF" in res_no_token.data or b"Bad Request" in res_no_token.data
