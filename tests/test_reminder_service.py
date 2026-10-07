from datetime import date
from app.services.reminder_service import is_reminder_active


def test_reminder_disabled():
    """Test reminder service when reminder toggle is disabled."""
    journey_date = date(2026, 12, 20)
    active, msg = is_reminder_active(journey_date, reminder_enabled=False)
    assert active is False
    assert msg == "Disabled"


def test_reminder_active_on_booking_date():
    """Test reminder active status on booking date."""
    journey_date = date(2026, 12, 20)
    # Booking date with window 60 = 2026-10-21
    active, msg = is_reminder_active(journey_date, reminder_enabled=True, today=date(2026, 10, 21), reminder_days_before=1)
    assert active is True


def test_reminder_inactive_future():
    """Test reminder inactive when booking date is far in future."""
    journey_date = date(2026, 12, 20)
    active, msg = is_reminder_active(journey_date, reminder_enabled=True, today=date(2026, 9, 1), reminder_days_before=1)
    assert active is False
    assert "Scheduled" in msg


def test_reminder_completed_journey():
    """Test reminder inactive when journey is already completed."""
    journey_date = date(2026, 12, 20)
    active, msg = is_reminder_active(journey_date, reminder_enabled=True, today=date(2026, 12, 25))
    assert active is False
    assert msg == "Journey Completed"
