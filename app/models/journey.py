from datetime import datetime, timezone
from app.models import db


class Journey(db.Model):
    """Model representing a planned train journey."""

    __tablename__ = "journeys"

    id = db.Column(db.Integer, primary_key=True)
    trip_name = db.Column(db.String(120), nullable=False)
    source = db.Column(db.String(100), nullable=False, index=True)
    destination = db.Column(db.String(100), nullable=False, index=True)
    train_name = db.Column(db.String(120), nullable=True)
    journey_date = db.Column(db.Date, nullable=False, index=True)
    reminder_enabled = db.Column(db.Boolean, default=True, nullable=False)
    holiday_id = db.Column(
        db.Integer,
        db.ForeignKey("holidays.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to sync record
    sync_record = db.relationship(
        "CalendarEventSync",
        backref="journey",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def to_dict(self):
        """Convert journey model instance to dictionary representation."""
        sync_info = self.sync_record.to_dict() if self.sync_record else None
        return {
            "id": self.id,
            "trip_name": self.trip_name,
            "source": self.source,
            "destination": self.destination,
            "train_name": self.train_name,
            "journey_date": self.journey_date.isoformat() if self.journey_date else None,
            "reminder_enabled": self.reminder_enabled,
            "holiday_id": self.holiday_id,
            "holiday_name": self.holiday.name if self.holiday else None,
            "sync_status": sync_info.get("status") if sync_info else "NOT_SYNCED",
            "sync_info": sync_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Journey {self.id}: {self.trip_name} ({self.source} -> {self.destination}) on {self.journey_date}>"
