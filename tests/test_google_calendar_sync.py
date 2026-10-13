from datetime import date, timedelta
from flask import session
from config import Config
from app import create_app
from app.models import db, Journey, Holiday, GoogleCalendarConnection, CalendarEventSync
from app.services.google_calendar_service import (
    set_mock_google_service,
    save_oauth_credentials,
    disconnect_google_calendar,
    is_google_connected,
    sync_journey_to_calendar,
    construct_calendar_event_payload,
)


class MockGoogleCalendarService:
    def __init__(self):
        self.events_db = {}
        self.fail_on_insert = False
        self.fail_with_404_on_patch = False
        self.fail_with_network_error = False
        self.fail_with_auth_error = False
        self.insert_calls = 0
        self.patch_calls = 0
        self.delete_calls = 0

    def events(self):
        return self

    def insert(self, calendarId, body):
        self.insert_calls += 1
        self.last_calendar_id = calendarId
        self.last_body = body

        if self.fail_with_auth_error:
            raise Exception("401 Unauthorized: invalid_grant")
        if self.fail_with_network_error:
            raise Exception("503 Service Unavailable: Network timeout")
        if self.fail_on_insert:
            raise Exception("Google API Error")

        event_id = f"evt_{len(self.events_db) + 1}"
        b = dict(body)
        b["id"] = event_id
        self.events_db[event_id] = b
        self._current_result = b
        return self

    def patch(self, calendarId, eventId, body):
        self.patch_calls += 1
        self.last_patched_id = eventId
        self.last_patched_body = body

        if self.fail_with_404_on_patch:
            raise Exception("404 Not Found: Event deleted on Google")
        if self.fail_with_network_error:
            raise Exception("503 Service Unavailable")

        if eventId in self.events_db:
            self.events_db[eventId].update(body)
            self._current_result = self.events_db[eventId]
        else:
            self._current_result = body
        return self

    def delete(self, calendarId, eventId):
        self.delete_calls += 1
        self.events_db.pop(eventId, None)
        self._current_result = {}
        return self

    def execute(self):
        return getattr(self, "_current_result", {})


class GoogleTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    GOOGLE_CLIENT_ID = "mock-client-id"
    GOOGLE_CLIENT_SECRET = "mock-client-secret"
    CALENDAR_EVENT_TIMEZONE = "Asia/Kolkata"
    CALENDAR_EVENT_HOUR = 9


def test_oauth_state_mismatch_and_callback():
    """Test OAuth state mismatch rejection and successful callback credential storage."""
    app = create_app(GoogleTestConfig)
    app.config["MOCK_OAUTH_EXCHANGE"] = lambda code: {"access_token": "mock_token", "refresh_token": "mock_refresh"}

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_google_oauth_state"] = "valid_state_123"

        # 1. State mismatch -> 400 Bad Request
        res_mismatch = client.get("/google/callback?code=mock_code&state=wrong_state")
        assert res_mismatch.status_code == 400
        assert b"OAuth state" in res_mismatch.data or b"Bad Request" in res_mismatch.data

        # Restore state in session
        with client.session_transaction() as sess:
            sess["_google_oauth_state"] = "valid_state_123"

        # 2. Matching state -> Success
        res_success = client.get("/google/callback?code=mock_code&state=valid_state_123", follow_redirects=True)
        assert res_success.status_code == 200
        assert b"Successfully connected" in res_success.data

        with app.app_context():
            assert is_google_connected() is True


def test_google_disconnect():
    """Test disconnecting Google Calendar integration."""
    app = create_app(GoogleTestConfig)
    with app.test_client() as client:
        with app.app_context():
            save_oauth_credentials({"access_token": "sample"}, user_email="test@user.com")
            assert is_google_connected() is True

        res_disc = client.post("/google/disconnect", follow_redirects=True)
        assert res_disc.status_code == 200
        assert b"disconnected" in res_disc.data

        with app.app_context():
            assert is_google_connected() is False


def test_event_payload_construction_and_reminders():
    """Test payload details: title, description, time window, timezone, and reminders."""
    app = create_app(GoogleTestConfig)
    with app.app_context():
        j = Journey(
            trip_name="Summer Vacation",
            source="Chennai",
            destination="Delhi",
            train_name="Tamil Nadu Express",
            journey_date=date(2026, 12, 20),
            reminder_enabled=True,
        )

        payload, booking_d = construct_calendar_event_payload(j)
        assert "Train Booking Opens - Chennai to Delhi" == payload["summary"]
        assert "Tamil Nadu Express" in payload["description"]
        assert "mathematical estimates" in payload["description"]
        assert payload["start"]["timeZone"] == "Asia/Kolkata"
        assert "09:00:00" in payload["start"]["dateTime"]
        assert "10:00:00" in payload["end"]["dateTime"]
        assert len(payload["reminders"]["overrides"]) == 2  # 1 day and 1 hour

        # Test reminder disabled
        j.reminder_enabled = False
        payload_no_rem, _ = construct_calendar_event_payload(j)
        assert len(payload_no_rem["reminders"]["overrides"]) == 0


def test_sync_journey_create_and_prevent_duplicates():
    """Test creating an event on Google and verify repeating sync updates without duplicate."""
    app = create_app(GoogleTestConfig)
    mock = MockGoogleCalendarService()
    set_mock_google_service(mock)

    with app.app_context():
        save_oauth_credentials({"token": "valid"})

        j = Journey(
            trip_name="Conference Trip",
            source="Mumbai",
            destination="Ahmedabad",
            journey_date=date.today() + timedelta(days=50),
        )
        db.session.add(j)
        db.session.commit()

        # First sync -> calls insert
        ok, status, msg = sync_journey_to_calendar(j.id)
        assert ok is True
        assert status == CalendarEventSync.STATUS_SYNCED
        assert mock.insert_calls == 1
        assert mock.patch_calls == 0

        sync_rec = CalendarEventSync.query.filter_by(journey_id=j.id).first()
        assert sync_rec.event_id is not None
        first_event_id = sync_rec.event_id

        # Repeat sync -> calls patch, NEVER duplicates
        ok2, status2, msg2 = sync_journey_to_calendar(j.id)
        assert ok2 is True
        assert status2 == CalendarEventSync.STATUS_SYNCED
        assert mock.insert_calls == 1  # No second insert!
        assert mock.patch_calls == 1   # Patched instead
        assert sync_rec.event_id == first_event_id


def test_sync_recovers_from_missing_external_event():
    """Test recovery when external Google event was deleted (404 on patch)."""
    app = create_app(GoogleTestConfig)
    mock = MockGoogleCalendarService()
    set_mock_google_service(mock)

    with app.app_context():
        save_oauth_credentials({"token": "valid"})
        j = Journey(
            trip_name="Recreate Trip",
            source="Bangalore",
            destination="Goa",
            journey_date=date.today() + timedelta(days=40),
        )
        db.session.add(j)
        db.session.commit()

        # Step 1: Initial sync
        sync_journey_to_calendar(j.id)
        assert mock.insert_calls == 1

        # Step 2: External event gets deleted on Google (simulate 404)
        mock.fail_with_404_on_patch = True
        ok, status, msg = sync_journey_to_calendar(j.id)
        # Should detect missing and recreate
        assert ok is True
        assert status == CalendarEventSync.STATUS_SYNCED
        assert mock.insert_calls == 2  # Recreated cleanly


def test_sync_failure_preserves_local_journey_and_retry():
    """Test that Google failures never block saving a local journey and retry works."""
    app = create_app(GoogleTestConfig)
    mock = MockGoogleCalendarService()
    mock.fail_with_network_error = True
    set_mock_google_service(mock)

    with app.app_context():
        save_oauth_credentials({"token": "valid"})
        j = Journey(
            trip_name="Resilient Local Trip",
            source="Pune",
            destination="Nagpur",
            journey_date=date.today() + timedelta(days=35),
        )
        db.session.add(j)
        db.session.commit()
        j_id = j.id

        # Sync fails due to network error
        ok, status, msg = sync_journey_to_calendar(j_id)
        assert ok is False
        assert status == CalendarEventSync.STATUS_SYNC_FAILED

        # Verify local journey survived completely untouched
        refetched = db.session.get(Journey, j_id)
        assert refetched is not None
        assert refetched.trip_name == "Resilient Local Trip"

        # Now network restores -> retry succeeds
        mock.fail_with_network_error = False
        retry_ok, retry_status, retry_msg = sync_journey_to_calendar(j_id)
        assert retry_ok is True
        assert retry_status == CalendarEventSync.STATUS_SYNCED


def test_sync_auth_revocation_sets_reauth_required():
    """Test handling of revoked OAuth tokens."""
    app = create_app(GoogleTestConfig)
    mock = MockGoogleCalendarService()
    mock.fail_with_auth_error = True
    set_mock_google_service(mock)

    with app.app_context():
        save_oauth_credentials({"token": "revoked"})
        j = Journey(
            trip_name="Auth Failure Trip",
            source="Delhi",
            destination="Lucknow",
            journey_date=date.today() + timedelta(days=30),
        )
        db.session.add(j)
        db.session.commit()

        ok, status, msg = sync_journey_to_calendar(j.id)
        assert ok is False
        assert status == CalendarEventSync.STATUS_REAUTH_REQUIRED
        assert "re-connect" in msg.lower() or "re-authentication" in msg.lower()
