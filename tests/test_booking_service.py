from datetime import date
import pytest
from app.services.booking_service import (
    calculate_booking_date,
    get_days_until_booking,
    get_days_until_journey,
    get_booking_status,
)


def test_calculate_booking_date_normal():
    """Test booking date calculation with normal date range."""
    journey_date = date(2026, 12, 20)
    booking_date = calculate_booking_date(journey_date, booking_window_days=60)
    assert booking_date == date(2026, 10, 21)


def test_calculate_booking_date_month_boundary():
    """Test booking date calculation crossing month boundary."""
    journey_date = date(2026, 3, 15)
    booking_date = calculate_booking_date(journey_date, booking_window_days=60)
    # March 15 minus 60 days -> Jan 14
    assert booking_date == date(2026, 1, 14)


def test_calculate_booking_date_year_boundary():
    """Test booking date calculation crossing year boundary."""
    journey_date = date(2027, 1, 15)
    booking_date = calculate_booking_date(journey_date, booking_window_days=60)
    # Jan 15 2027 minus 60 days -> Nov 16 2026
    assert booking_date == date(2026, 11, 16)


def test_calculate_booking_date_leap_year():
    """Test booking date calculation during leap year."""
    journey_date = date(2028, 3, 1)  # 2028 is a leap year (Feb has 29 days)
    booking_date = calculate_booking_date(journey_date, booking_window_days=60)
    # March 1 minus 60 days in leap year -> Jan 1 (Jan 31 + Feb 29 = 60 days)
    assert booking_date == date(2028, 1, 1)


def test_get_days_until_booking():
    """Test remaining days calculation until booking date."""
    journey_date = date(2026, 12, 20)
    # Expected booking date: 2026-10-21
    today = date(2026, 10, 1)
    days = get_days_until_booking(journey_date, today=today, booking_window_days=60)
    assert days == 20


def test_get_days_until_journey():
    """Test remaining days calculation until journey date."""
    journey_date = date(2026, 12, 20)
    today = date(2026, 10, 1)
    days = get_days_until_journey(journey_date, today=today)
    assert days == 80


def test_get_booking_status():
    """Test dynamic booking status determinations."""
    journey_date = date(2026, 12, 20)
    # Booking date is 2026-10-21

    # 1. Booking Today
    status_code, text, badge = get_booking_status(journey_date, today=date(2026, 10, 21), booking_window_days=60)
    assert status_code == "BOOKING_TODAY"

    # 2. Booking Tomorrow
    status_code, text, badge = get_booking_status(journey_date, today=date(2026, 10, 20), booking_window_days=60)
    assert status_code == "BOOKING_TOMORROW"

    # 3. Booking Soon (3 days)
    status_code, text, badge = get_booking_status(journey_date, today=date(2026, 10, 18), booking_window_days=60)
    assert status_code == "BOOKING_SOON"

    # 4. Booking Passed
    status_code, text, badge = get_booking_status(journey_date, today=date(2026, 10, 25), booking_window_days=60)
    assert status_code == "BOOKING_DATE_PASSED"

    # 5. Journey Completed
    status_code, text, badge = get_booking_status(journey_date, today=date(2026, 12, 25), booking_window_days=60)
    assert status_code == "JOURNEY_COMPLETED"

    # 6. Upcoming
    status_code, text, badge = get_booking_status(journey_date, today=date(2026, 9, 1), booking_window_days=60)
    assert status_code == "UPCOMING"
