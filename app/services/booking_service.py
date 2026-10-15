from datetime import date, datetime, timedelta
from flask import current_app


def get_default_booking_window():
    """Retrieve booking window days from Flask current_app config or default to 60."""
    try:
        return current_app.config.get("BOOKING_WINDOW_DAYS", 60)
    except RuntimeError:
        return 60


def parse_date(date_val):
    """Ensure date input is a datetime.date object."""
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, str):
        return datetime.strptime(date_val, "%Y-%m-%d").date()
    raise ValueError(f"Invalid date format: {date_val}")


def calculate_booking_date(journey_date, booking_window_days=None):
    """
    Calculate the expected booking opening date for a train journey.
    
    Expected Booking Date = Journey Date - Booking Window (in days)
    """
    j_date = parse_date(journey_date)
    if booking_window_days is None:
        booking_window_days = get_default_booking_window()
    return j_date - timedelta(days=int(booking_window_days))


def get_days_until_booking(journey_date, today=None, booking_window_days=None):
    """
    Calculate remaining days until expected booking opening date.
    
    Positive number = days remaining in future.
    0 = today is booking date.
    Negative number = booking date has passed.
    """
    if today is None:
        today = date.today()
    else:
        today = parse_date(today)

    booking_date = calculate_booking_date(journey_date, booking_window_days)
    return (booking_date - today).days


def get_days_until_journey(journey_date, today=None):
    """Calculate remaining days until actual journey date."""
    j_date = parse_date(journey_date)
    if today is None:
        today = date.today()
    else:
        today = parse_date(today)

    return (j_date - today).days


def get_booking_status(journey_date, today=None, booking_window_days=None):
    """
    Determine dynamic booking status.
    
    Returns tuple: (status_code, status_text, badge_class)
    """
    j_date = parse_date(journey_date)
    if today is None:
        today = date.today()
    else:
        today = parse_date(today)

    # 1. Journey completed
    if today > j_date:
        return (
            "JOURNEY_COMPLETED",
            "Journey Completed",
            "bg-secondary",
        )

    days_until_booking = get_days_until_booking(j_date, today, booking_window_days)

    if days_until_booking < 0:
        return (
            "BOOKING_DATE_PASSED",
            "Booking date arrived — check railway booking platform",
            "bg-warning text-dark",
        )
    elif days_until_booking == 0:
        return (
            "BOOKING_TODAY",
            "Booking date is TODAY!",
            "bg-danger animate-pulse",
        )
    elif days_until_booking == 1:
        return (
            "BOOKING_TOMORROW",
            "Booking opens tomorrow",
            "bg-warning text-dark",
        )
    elif days_until_booking <= 3:
        return (
            "BOOKING_SOON",
            f"Booking opens in {days_until_booking} days",
            "bg-info text-dark",
        )
    else:
        return (
            "UPCOMING",
            f"Booking opens in {days_until_booking} days",
            "bg-primary",
        )


def enrich_journey_data(journey, today=None, booking_window_days=None):
    """
    Enrich a Journey model or dict with calculated dynamic attributes.
    Does not persist calculated fields in database.
    """
    if today is None:
        today = date.today()
    else:
        today = parse_date(today)

    j_date = parse_date(journey.journey_date if hasattr(journey, "journey_date") else journey["journey_date"])
    b_window = booking_window_days if booking_window_days is not None else get_default_booking_window()

    booking_date = calculate_booking_date(j_date, b_window)
    days_until_b = get_days_until_booking(j_date, today, b_window)
    days_until_j = get_days_until_journey(j_date, today)
    status_code, status_text, status_class = get_booking_status(j_date, today, b_window)

    reminder_enabled = journey.reminder_enabled if hasattr(journey, "reminder_enabled") else journey.get("reminder_enabled", True)

    from app.services.reminder_service import is_reminder_active
    reminder_active, reminder_text = is_reminder_active(j_date, reminder_enabled, today)

    # Holiday and Calendar Sync metadata
    holiday_id = getattr(journey, "holiday_id", None) if hasattr(journey, "holiday_id") else (journey.get("holiday_id") if isinstance(journey, dict) else None)
    holiday_name = None
    if hasattr(journey, "holiday") and journey.holiday:
        holiday_name = journey.holiday.name
    elif isinstance(journey, dict):
        holiday_name = journey.get("holiday_name")

    sync_record = getattr(journey, "sync_record", None)
    sync_status = sync_record.status if sync_record else (journey.get("sync_status", "NOT_SYNCED") if isinstance(journey, dict) else "NOT_SYNCED")
    sync_error = sync_record.last_error if sync_record else (journey.get("sync_error") if isinstance(journey, dict) else None)
    sync_event_id = sync_record.event_id if sync_record else (journey.get("sync_event_id") if isinstance(journey, dict) else None)
    last_synced = sync_record.last_synced if sync_record else (journey.get("last_synced") if isinstance(journey, dict) else None)

    return {
        "id": journey.id if hasattr(journey, "id") else journey.get("id"),
        "trip_name": journey.trip_name if hasattr(journey, "trip_name") else journey.get("trip_name"),
        "source": journey.source if hasattr(journey, "source") else journey.get("source"),
        "destination": journey.destination if hasattr(journey, "destination") else journey.get("destination"),
        "train_name": journey.train_name if hasattr(journey, "train_name") else journey.get("train_name"),
        "journey_date": j_date,
        "journey_date_str": j_date.strftime("%Y-%m-%d"),
        "journey_date_formatted": j_date.strftime("%d %B %Y"),
        "expected_booking_date": booking_date,
        "expected_booking_date_str": booking_date.strftime("%Y-%m-%d"),
        "expected_booking_date_formatted": booking_date.strftime("%d %B %Y"),
        "days_until_booking": days_until_b,
        "days_until_journey": days_until_j,
        "status_code": status_code,
        "status_text": status_text,
        "status_class": status_class,
        "reminder_enabled": reminder_enabled,
        "reminder_active": reminder_active,
        "reminder_text": reminder_text,
        "holiday_id": holiday_id,
        "holiday_name": holiday_name,
        "sync_status": sync_status,
        "sync_error": sync_error,
        "sync_event_id": sync_event_id,
        "last_synced": last_synced,
        "raw_journey": journey,
    }
