from datetime import date
from app import create_app
from app.models import db, Journey
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


def test_journey_model_creation():
    """Test model instantiation and dictionary serialization."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

        j = Journey(
            trip_name="Test Vacation",
            source="Chennai",
            destination="Madurai",
            train_name="Tejas Express",
            journey_date=date(2026, 11, 15),
            reminder_enabled=True,
        )
        db.session.add(j)
        db.session.commit()

        assert j.id is not None
        assert j.trip_name == "Test Vacation"
        assert j.source == "Chennai"
        assert j.destination == "Madurai"
        assert j.train_name == "Tejas Express"
        assert j.journey_date == date(2026, 11, 15)

        data = j.to_dict()
        assert data["trip_name"] == "Test Vacation"
        assert data["journey_date"] == "2026-11-15"
        assert data["reminder_enabled"] is True
