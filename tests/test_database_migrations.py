import sqlite3
import tempfile
from pathlib import Path
from datetime import date
from flask import Flask
from config import Config
from app import create_app
from app.models import db, Journey, AcademicCalendar, Holiday, GoogleCalendarConnection, CalendarEventSync
from app.database.migration import run_migrations


def test_fresh_database_creation():
    """Test creating a fresh database with all Stage 3 models."""
    class FreshConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        WTF_CSRF_ENABLED = False

    app = create_app(FreshConfig)
    with app.app_context():
        # Verify all models can be created and queried
        cal = AcademicCalendar(
            filename="test_cal.pdf",
            stored_filename="cal_uuid.pdf",
            calendar_label="Fall 2026",
            status="UPLOADED",
        )
        db.session.add(cal)
        db.session.commit()

        hol = Holiday(
            calendar_id=cal.id,
            name="Diwali Holiday",
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 3),
            status="CONFIRMED",
        )
        db.session.add(hol)
        db.session.commit()

        j = Journey(
            trip_name="Diwali Trip",
            source="Delhi",
            destination="Jaipur",
            journey_date=date(2026, 11, 1),
            holiday_id=hol.id,
        )
        db.session.add(j)
        db.session.commit()

        sync = CalendarEventSync(
            journey_id=j.id,
            calendar_id="primary",
            event_id="google_event_123",
            status=CalendarEventSync.STATUS_SYNCED,
        )
        db.session.add(sync)
        db.session.commit()

        # Assert relationships
        assert j.holiday.name == "Diwali Holiday"
        assert j.sync_record.event_id == "google_event_123"
        assert hol.calendar.calendar_label == "Fall 2026"
        assert len(cal.holidays) == 1


def test_migration_on_existing_database_preserves_journeys():
    """Test non-destructive migration on existing DB with pre-existing journeys."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        # Step 1: Create a legacy database table without holiday_id column
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE journeys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_name VARCHAR(120) NOT NULL,
                source VARCHAR(100) NOT NULL,
                destination VARCHAR(100) NOT NULL,
                train_name VARCHAR(120),
                journey_date DATE NOT NULL,
                reminder_enabled BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        cursor.execute("""
            INSERT INTO journeys (trip_name, source, destination, train_name, journey_date, reminder_enabled, created_at, updated_at)
            VALUES ('Pre-existing Trip', 'Chennai', 'Bangalore', 'Lalbagh Express', '2026-11-20', 1, '2026-10-01 10:00:00', '2026-10-01 10:00:00')
        """)
        conn.commit()
        conn.close()

        # Step 2: Initialize app pointing to this legacy database
        class LegacyConfig(Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
            WTF_CSRF_ENABLED = False

        app = create_app(LegacyConfig)

        # Step 3: Verify migration succeeded and data was preserved
        with app.app_context():
            journeys = Journey.query.all()
            assert len(journeys) == 1
            existing = journeys[0]
            assert existing.trip_name == "Pre-existing Trip"
            assert existing.source == "Chennai"
            assert existing.destination == "Bangalore"
            assert existing.holiday_id is None

            # Verify new models can be added and linked to existing journey
            hol = Holiday(
                name="Legacy Linked Holiday",
                start_date=date(2026, 11, 20),
                end_date=date(2026, 11, 20),
                status="CONFIRMED",
            )
            db.session.add(hol)
            db.session.commit()

            existing.holiday_id = hol.id
            db.session.commit()

            refetched = db.session.get(Journey, existing.id)
            assert refetched.holiday_id == hol.id
            assert refetched.holiday.name == "Legacy Linked Holiday"
    finally:
        try:
            Path(db_path).unlink(missing_ok=True)
        except Exception:
            pass
