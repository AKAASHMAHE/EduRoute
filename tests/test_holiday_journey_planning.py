from datetime import date, timedelta
from config import Config
from app import create_app
from app.models import db, Journey, Holiday, AcademicCalendar, CalendarEventSync


class PlanningTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


def test_plan_journey_get_page_shows_only_confirmed_holidays():
    """Verify that only confirmed holidays are offered for planning trips."""
    app = create_app(PlanningTestConfig)
    with app.test_client() as client:
        with app.app_context():
            h_unconfirmed = Holiday(
                name="Candidate Holiday",
                start_date=date(2026, 11, 10),
                end_date=date(2026, 11, 10),
                status="UNCONFIRMED",
            )
            h_confirmed = Holiday(
                name="Confirmed Diwali",
                start_date=date(2026, 11, 15),
                end_date=date(2026, 11, 18),
                status="CONFIRMED",
            )
            db.session.add_all([h_unconfirmed, h_confirmed])
            db.session.commit()

        res = client.get("/journey/plan-from-holiday")
        assert res.status_code == 200
        assert b"Confirmed Diwali" in res.data
        assert b"Candidate Holiday" not in res.data


def test_plan_journey_from_confirmed_holiday_success():
    """Test successful journey creation linked to a multi-day holiday."""
    app = create_app(PlanningTestConfig)
    with app.test_client() as client:
        with app.app_context():
            h = Holiday(
                name="Diwali Vacation",
                start_date=date.today() + timedelta(days=70),
                end_date=date.today() + timedelta(days=75),
                status="CONFIRMED",
            )
            db.session.add(h)
            db.session.commit()
            h_id = h.id

            # Select departure date on 2nd day of holiday
            departure_date = (date.today() + timedelta(days=71)).strftime("%Y-%m-%d")

        res = client.post(
            "/journey/plan-from-holiday",
            data={
                "holiday_id": h_id,
                "trip_name": "Diwali Family Visit",
                "source": "Chennai Central",
                "destination": "Coimbatore Junction",
                "train_name": "Cheran Express",
                "journey_date": departure_date,
                "reminder_enabled": "true",
            },
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert b"Diwali Family Visit" in res.data
        assert b"planned successfully" in res.data

        with app.app_context():
            journey = Journey.query.filter_by(trip_name="Diwali Family Visit").first()
            assert journey is not None
            assert journey.holiday_id == h_id
            assert journey.holiday.name == "Diwali Vacation"
            assert journey.sync_record is not None
            assert journey.sync_record.status == CalendarEventSync.STATUS_NOT_SYNCED


def test_plan_journey_rejects_unconfirmed_holiday():
    """Verify that unconfirmed holidays cannot be used to create journeys."""
    app = create_app(PlanningTestConfig)
    with app.test_client() as client:
        with app.app_context():
            h_unconfirmed = Holiday(
                name="Unconfirmed Break",
                start_date=date.today() + timedelta(days=50),
                end_date=date.today() + timedelta(days=50),
                status="UNCONFIRMED",
            )
            db.session.add(h_unconfirmed)
            db.session.commit()
            h_id = h_unconfirmed.id

        res = client.post(
            "/journey/plan-from-holiday",
            data={
                "holiday_id": h_id,
                "trip_name": "Illegal Trip",
                "source": "Delhi",
                "destination": "Agra",
                "journey_date": (date.today() + timedelta(days=50)).strftime("%Y-%m-%d"),
            },
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert b"Cannot plan journeys from unconfirmed holidays" in res.data

        with app.app_context():
            assert Journey.query.filter_by(trip_name="Illegal Trip").first() is None


def test_plan_journey_rejects_date_outside_range():
    """Verify validation fails if travel date is outside holiday period."""
    app = create_app(PlanningTestConfig)
    with app.test_client() as client:
        with app.app_context():
            h = Holiday(
                name="Short Break",
                start_date=date.today() + timedelta(days=30),
                end_date=date.today() + timedelta(days=32),
                status="CONFIRMED",
            )
            db.session.add(h)
            db.session.commit()
            h_id = h.id

        # Travel date outside range (40 days ahead)
        res = client.post(
            "/journey/plan-from-holiday",
            data={
                "holiday_id": h_id,
                "trip_name": "Out of Range Trip",
                "source": "Mumbai",
                "destination": "Goa",
                "journey_date": (date.today() + timedelta(days=40)).strftime("%Y-%m-%d"),
            },
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert b"Selected travel date must be within holiday period" in res.data

        with app.app_context():
            assert Journey.query.filter_by(trip_name="Out of Range Trip").first() is None


def test_plan_journey_prevents_duplicate_trips():
    """Verify duplicate prevention for same route, date, and holiday."""
    app = create_app(PlanningTestConfig)
    with app.test_client() as client:
        with app.app_context():
            h = Holiday(
                name="Pongal Break",
                start_date=date.today() + timedelta(days=45),
                end_date=date.today() + timedelta(days=47),
                status="CONFIRMED",
            )
            db.session.add(h)
            db.session.commit()
            h_id = h.id
            travel_d = (date.today() + timedelta(days=45)).strftime("%Y-%m-%d")

        payload = {
            "holiday_id": h_id,
            "trip_name": "Pongal Trip",
            "source": "Chennai",
            "destination": "Madurai",
            "journey_date": travel_d,
        }

        # First creation succeeds
        res1 = client.post("/journey/plan-from-holiday", data=payload, follow_redirects=True)
        assert res1.status_code == 200
        assert b"planned successfully" in res1.data

        # Second creation with identical route and date is rejected as duplicate
        res2 = client.post("/journey/plan-from-holiday", data=payload, follow_redirects=True)
        assert res2.status_code == 200
        assert b"already exists" in res2.data

        with app.app_context():
            journeys = Journey.query.filter_by(holiday_id=h_id).all()
            assert len(journeys) == 1


def test_manual_journey_creation_remains_functional():
    """Verify that manual journey creation still works without any holiday link."""
    app = create_app(PlanningTestConfig)
    with app.test_client() as client:
        future_date = (date.today() + timedelta(days=40)).strftime("%Y-%m-%d")
        res = client.post(
            "/journey/add",
            data={
                "trip_name": "Pure Manual Journey",
                "source": "Vellore",
                "destination": "Bangalore",
                "journey_date": future_date,
            },
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert b"Pure Manual Journey" in res.data

        with app.app_context():
            manual_j = Journey.query.filter_by(trip_name="Pure Manual Journey").first()
            assert manual_j is not None
            assert manual_j.holiday_id is None
            assert manual_j.sync_record is not None
