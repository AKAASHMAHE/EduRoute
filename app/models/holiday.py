from datetime import datetime, timezone
from app.models import db


class Holiday(db.Model):
    """Model representing an extracted or manually verified academic holiday."""

    __tablename__ = "holidays"

    id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(
        db.Integer,
        db.ForeignKey("academic_calendars.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=True)
    source_text = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(20),
        default="UNCONFIRMED",
        nullable=False,
        index=True,
    )  # UNCONFIRMED, CONFIRMED, REJECTED
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    journeys = db.relationship(
        "Journey",
        backref="holiday",
        lazy="select",
    )

    @property
    def is_multi_day(self):
        """Check if holiday spans multiple dates."""
        return self.start_date != self.end_date

    @property
    def duration_days(self):
        """Calculate number of days in the holiday range."""
        if not self.start_date or not self.end_date:
            return 1
        return (self.end_date - self.start_date).days + 1

    def to_dict(self):
        """Convert holiday model instance to dictionary representation."""
        return {
            "id": self.id,
            "calendar_id": self.calendar_id,
            "name": self.name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "category": self.category,
            "source_text": self.source_text,
            "status": self.status,
            "is_multi_day": self.is_multi_day,
            "duration_days": self.duration_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Holiday {self.id}: {self.name} ({self.start_date} to {self.end_date}) [{self.status}]>"
