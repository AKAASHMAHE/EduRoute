from datetime import datetime, timezone
from app.models import db


class GoogleCalendarConnection(db.Model):
    """Model tracking authorized Google Calendar account credentials."""

    __tablename__ = "google_calendar_connections"

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(150), nullable=True)
    credentials_json = db.Column(db.Text, nullable=True)
    is_connected = db.Column(db.Boolean, default=False, nullable=False)
    connected_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        """Safe representation without leaking credentials."""
        return {
            "id": self.id,
            "user_email": self.user_email,
            "is_connected": self.is_connected,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<GoogleCalendarConnection {self.id}: {self.user_email} (Connected={self.is_connected})>"


class CalendarEventSync(db.Model):
    """Model tracking synchronization of a Journey to a Google Calendar event."""

    __tablename__ = "calendar_event_syncs"

    # Status constants
    STATUS_NOT_CONNECTED = "NOT_CONNECTED"
    STATUS_NOT_SYNCED = "NOT_SYNCED"
    STATUS_SYNC_PENDING = "SYNC_PENDING"
    STATUS_SYNCED = "SYNCED"
    STATUS_SYNC_FAILED = "SYNC_FAILED"
    STATUS_REAUTH_REQUIRED = "REAUTH_REQUIRED"
    STATUS_EXTERNAL_EVENT_MISSING = "EXTERNAL_EVENT_MISSING"

    id = db.Column(db.Integer, primary_key=True)
    journey_id = db.Column(
        db.Integer,
        db.ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    calendar_id = db.Column(db.String(150), default="primary", nullable=False)
    event_id = db.Column(db.String(255), nullable=True, index=True)
    status = db.Column(
        db.String(50),
        default="NOT_SYNCED",
        nullable=False,
        index=True,
    )
    synced_booking_date = db.Column(db.Date, nullable=True)
    last_synced = db.Column(db.DateTime, nullable=True)
    last_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship back to journey is backref from Journey model

    def to_dict(self):
        """Convert sync record to dictionary representation."""
        return {
            "id": self.id,
            "journey_id": self.journey_id,
            "calendar_id": self.calendar_id,
            "event_id": self.event_id,
            "status": self.status,
            "synced_booking_date": self.synced_booking_date.isoformat() if self.synced_booking_date else None,
            "last_synced": self.last_synced.isoformat() if self.last_synced else None,
            "last_error": self.last_error,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CalendarEventSync journey={self.journey_id} status={self.status} event={self.event_id}>"
