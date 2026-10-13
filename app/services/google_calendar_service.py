"""
Google Calendar Service & OAuth Manager.
Handles OAuth lifecycle, event payload creation, event synchronization,
error recovery, and retry logic.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from flask import current_app, session
from app.models import db, GoogleCalendarConnection, CalendarEventSync, Journey
from app.services.booking_service import calculate_booking_date

logger = logging.getLogger(__name__)

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# Hook for testing with mocked Google API service
_mock_service = None


def set_mock_google_service(mock):
    """Set a mock Google Calendar API service for testing."""
    global _mock_service
    _mock_service = mock


def get_calendar_connection():
    """Retrieve the primary Google Calendar Connection record."""
    return GoogleCalendarConnection.query.first()


def is_google_connected():
    """Check if an authorized, active Google Calendar connection exists."""
    conn = get_calendar_connection()
    return conn is not None and conn.is_connected and conn.credentials_json is not None


def get_oauth_authorization_url(redirect_uri, state):
    """Build the Google OAuth 2.0 authorization URL."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        return None, "GOOGLE_CLIENT_ID is not configured in .env."

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        f"scope={CALENDAR_SCOPES[0]}&"
        "access_type=offline&"
        "prompt=consent&"
        f"state={state}"
    )
    return auth_url, None


def save_oauth_credentials(credentials_dict, user_email="primary_user"):
    """Save Google OAuth credentials into database connection record."""
    conn = get_calendar_connection()
    if not conn:
        conn = GoogleCalendarConnection()
        db.session.add(conn)

    conn.user_email = user_email
    conn.credentials_json = json.dumps(credentials_dict)
    conn.is_connected = True
    conn.connected_at = datetime.now(timezone.utc)
    db.session.commit()
    return conn


def disconnect_google_calendar():
    """Disconnect Google Calendar integration and clear stored credentials."""
    conn = get_calendar_connection()
    if conn:
        conn.is_connected = False
        conn.credentials_json = None
        db.session.commit()
    return True


def get_google_service():
    """
    Build and return an authorized Google Calendar service instance.
    Uses mock service if configured, or builds real google-api client.
    """
    global _mock_service
    if _mock_service is not None:
        return _mock_service

    app_mock = current_app.config.get("MOCK_GOOGLE_SERVICE")
    if app_mock is not None:
        return app_mock

    conn = get_calendar_connection()
    if not conn or not conn.is_connected or not conn.credentials_json:
        return None

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        data = json.loads(conn.credentials_json)
        creds = Credentials.from_authorized_user_info(data, CALENDAR_SCOPES)

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            conn.credentials_json = json.dumps(json.loads(creds.to_json()))
            db.session.commit()

        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to initialize Google Calendar client: {e}")
        return None


def construct_calendar_event_payload(journey):
    """
    Construct the Google Calendar event payload for the expected booking date.
    
    Includes:
    - Title: Train Booking Opens - <Source> to <Destination>
    - Description: trip, route, train, holiday, expected booking date, journey date, booking window, disclaimer
    - Date and time: Start and end datetime in specified timezone
    - Reminder overrides: 1 day before + 1 hour before (if reminders enabled)
    """
    booking_window = current_app.config.get("BOOKING_WINDOW_DAYS", 60)
    tz_str = current_app.config.get("CALENDAR_EVENT_TIMEZONE", "Asia/Kolkata")
    event_hour = current_app.config.get("CALENDAR_EVENT_HOUR", 9)

    booking_date = calculate_booking_date(journey.journey_date, booking_window)
    holiday_info = f"Holiday: {journey.holiday.name}\n" if journey.holiday else ""
    train_info = f"Train: {journey.train_name}\n" if journey.train_name else ""

    summary = f"Train Booking Opens - {journey.source} to {journey.destination}"

    description = (
        f"Planned Train Journey: {journey.trip_name}\n"
        f"Route: {journey.source} -> {journey.destination}\n"
        f"{train_info}"
        f"{holiday_info}"
        f"Planned Journey Date: {journey.journey_date.strftime('%d %B %Y')}\n"
        f"Expected Booking Opening Date: {booking_date.strftime('%d %B %Y')}\n"
        f"Advance Reservation Period: {booking_window} days\n\n"
        "Important Note: Railway booking opening dates are mathematical estimates. "
        "Verify live seat availability and official opening timings (e.g. 8:00 AM IST) "
        "directly on the official railway reservation platform."
    )

    # Calculate ISO start and end timestamps (1-hour window on booking date)
    start_dt_str = f"{booking_date.isoformat()}T{event_hour:02d}:00:00"
    end_dt_str = f"{booking_date.isoformat()}T{(event_hour + 1):02d}:00:00"

    event_body = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": f"{start_dt_str}+05:30",  # Default IST offset format
            "timeZone": tz_str,
        },
        "end": {
            "dateTime": f"{end_dt_str}+05:30",
            "timeZone": tz_str,
        },
    }

    if journey.reminder_enabled:
        event_body["reminders"] = {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 24 * 60},  # 1 day before
                {"method": "popup", "minutes": 60},       # 1 hour before
            ],
        }
    else:
        event_body["reminders"] = {
            "useDefault": False,
            "overrides": [],
        }

    return event_body, booking_date


def sync_journey_to_calendar(journey_id):
    """
    Synchronize a Journey's expected booking date with Google Calendar.
    
    Handles:
    - Insert for new events
    - Patch/Update for existing events (never duplicates)
    - Re-creation if external event was deleted (EXTERNAL_EVENT_MISSING)
    - Error classification (REAUTH_REQUIRED, SYNC_FAILED, etc.)
    
    Returns:
        (success: bool, status: str, message: str)
    """
    journey = db.session.get(Journey, journey_id)
    if not journey:
        return False, CalendarEventSync.STATUS_SYNC_FAILED, "Journey not found."

    sync = CalendarEventSync.query.filter_by(journey_id=journey.id).first()
    if not sync:
        sync = CalendarEventSync(
            journey_id=journey.id,
            calendar_id=current_app.config.get("GOOGLE_CALENDAR_ID", "primary"),
            status=CalendarEventSync.STATUS_NOT_SYNCED,
        )
        db.session.add(sync)

    if not is_google_connected() and _mock_service is None and not current_app.config.get("MOCK_GOOGLE_SERVICE"):
        sync.status = CalendarEventSync.STATUS_NOT_CONNECTED
        sync.last_error = "Google Calendar integration is not connected."
        db.session.commit()
        return False, sync.status, "Google Calendar is not connected. Please connect your account in Settings."

    service = get_google_service()
    if not service:
        sync.status = CalendarEventSync.STATUS_REAUTH_REQUIRED
        sync.last_error = "Authentication credentials expired or invalid. Please reauthorize."
        db.session.commit()
        return False, sync.status, "Google credentials invalid or expired. Re-authentication required."

    event_payload, expected_booking_date = construct_calendar_event_payload(journey)
    calendar_id = sync.calendar_id or current_app.config.get("GOOGLE_CALENDAR_ID", "primary")

    try:
        # Case 1: Existing event ID -> Update / Patch
        if sync.event_id:
            try:
                updated_event = service.events().patch(
                    calendarId=calendar_id,
                    eventId=sync.event_id,
                    body=event_payload,
                ).execute()

                sync.status = CalendarEventSync.STATUS_SYNCED
                sync.synced_booking_date = expected_booking_date
                sync.last_synced = datetime.now(timezone.utc)
                sync.last_error = None
                db.session.commit()
                return True, sync.status, "Google Calendar event updated successfully."

            except Exception as patch_err:
                err_str = str(patch_err).lower()
                # 404 Not Found indicates event was deleted externally
                if "404" in err_str or "not found" in err_str:
                    logger.warning(f"External event {sync.event_id} missing on Google. Recreating.")
                    sync.status = CalendarEventSync.STATUS_EXTERNAL_EVENT_MISSING
                    sync.event_id = None  # Clear stale ID so subsequent insert recreates it
                    db.session.commit()
                    # Fall through to recreate event
                else:
                    raise patch_err

        # Case 2: New Event or Recreation
        new_event = service.events().insert(
            calendarId=calendar_id,
            body=event_payload,
        ).execute()

        event_id = new_event.get("id")
        sync.event_id = event_id
        sync.status = CalendarEventSync.STATUS_SYNCED
        sync.synced_booking_date = expected_booking_date
        sync.last_synced = datetime.now(timezone.utc)
        sync.last_error = None
        db.session.commit()
        return True, sync.status, "Google Calendar event created successfully!"

    except Exception as e:
        err_str = str(e)
        logger.error(f"Google Calendar sync error for journey {journey_id}: {err_str}")

        if "invalid_grant" in err_str.lower() or "unauthorized" in err_str.lower() or "401" in err_str:
            sync.status = CalendarEventSync.STATUS_REAUTH_REQUIRED
            sync.last_error = "Authorization expired or revoked. Please reconnect."
            msg = "Authorization revoked or expired. Please re-connect your Google account."
        else:
            sync.status = CalendarEventSync.STATUS_SYNC_FAILED
            sync.last_error = f"Calendar sync failed: {err_str[:200]}"
            msg = f"Failed to sync with Google Calendar: {err_str[:150]}"

        db.session.commit()
        return False, sync.status, msg


def delete_calendar_event_for_journey(journey_id):
    """
    Delete the external event on Google Calendar when a journey is deleted.
    Never crashes if Google is disconnected or event is already deleted.
    """
    sync = CalendarEventSync.query.filter_by(journey_id=journey_id).first()
    if not sync or not sync.event_id:
        return True

    service = get_google_service()
    if not service:
        logger.info("Skipping external event deletion: Google service not connected.")
        return False

    try:
        service.events().delete(
            calendarId=sync.calendar_id or "primary",
            eventId=sync.event_id,
        ).execute()
        return True
    except Exception as e:
        logger.warning(f"Failed to delete Google event {sync.event_id}: {e}")
        return False
