from datetime import date, timedelta
from app.utils.validators import validate_journey_input


def test_validate_journey_valid():
    """Test validator with valid journey input."""
    future_date = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    data = {
        "trip_name": "Goa Trip",
        "source": "Mumbai",
        "destination": "Goa",
        "journey_date": future_date,
        "train_name": "Konkan Kanya Express",
    }
    is_valid, errors = validate_journey_input(data)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_journey_missing_fields():
    """Test validator with missing required fields."""
    data = {
        "trip_name": "",
        "source": "    ",
        "destination": "",
        "journey_date": "",
    }
    is_valid, errors = validate_journey_input(data)
    assert is_valid is False
    assert "trip_name" in errors
    assert "source" in errors
    assert "destination" in errors
    assert "journey_date" in errors


def test_validate_journey_same_source_dest():
    """Test validator when source and destination stations are identical."""
    future_date = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")
    data = {
        "trip_name": "Local Loop",
        "source": "Chennai Central",
        "destination": "chennai central",
        "journey_date": future_date,
    }
    is_valid, errors = validate_journey_input(data)
    assert is_valid is False
    assert "destination" in errors
    assert "same station" in errors["destination"].lower()


def test_validate_journey_past_date():
    """Test validator with a past journey date."""
    past_date = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
    data = {
        "trip_name": "Past Trip",
        "source": "Delhi",
        "destination": "Agra",
        "journey_date": past_date,
    }
    is_valid, errors = validate_journey_input(data)
    assert is_valid is False
    assert "journey_date" in errors
    assert "past" in errors["journey_date"].lower()
