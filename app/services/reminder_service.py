from datetime import date, datetime, timedelta
from flask import current_app


def get_default_reminder_days():
    """Retrieve reminder threshold from Flask current_app config or default to 1."""
    try:
        return current_app.config.get("REMINDER_DAYS_BEFORE", 1)
    except RuntimeError:
        return 1


def is_reminder_active(journey_date, reminder_enabled=True, today=None, reminder_days_before=None):
    """
    Determine if a reminder should be active for a given journey.
    
    Returns tuple: (is_active: bool, description: str)
    """
    if not reminder_enabled:
        return False, "Disabled"

    if today is None:
        today = date.today()
    elif isinstance(today, datetime):
        today = today.date()
    elif isinstance(today, str):
        today = datetime.strptime(today, "%Y-%m-%d").date()

    if isinstance(journey_date, datetime):
        j_date = journey_date.date()
    elif isinstance(journey_date, str):
        j_date = datetime.strptime(journey_date, "%Y-%m-%d").date()
    else:
        j_date = journey_date

    if today > j_date:
        return False, "Journey Completed"

    if reminder_days_before is None:
        reminder_days_before = get_default_reminder_days()

    from app.services.booking_service import calculate_booking_date
    booking_date = calculate_booking_date(j_date)
    reminder_trigger_date = booking_date - timedelta(days=int(reminder_days_before))

    if today >= reminder_trigger_date:
        if today == booking_date:
            return True, "Active (Booking date is TODAY)"
        elif today < booking_date:
            return True, "Active (Booking opens soon)"
        else:
            return True, "Active (Booking date passed - check availability)"
    else:
        days_to_reminder = (reminder_trigger_date - today).days
        return False, f"Scheduled (Reminder in {days_to_reminder} days)"
