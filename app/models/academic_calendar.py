from datetime import datetime, timezone
from app.models import db


class AcademicCalendar(db.Model):
    """Model representing an uploaded institution academic calendar PDF."""

    __tablename__ = "academic_calendars"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    calendar_label = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), default="UPLOADED", nullable=False, index=True)
    holiday_count = db.Column(db.Integer, default=0, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    holidays = db.relationship(
        "Holiday",
        backref="calendar",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Holiday.start_date",
    )

    def to_dict(self):
        """Convert academic calendar model instance to dictionary representation."""
        return {
            "id": self.id,
            "filename": self.filename,
            "stored_filename": self.stored_filename,
            "calendar_label": self.calendar_label,
            "status": self.status,
            "holiday_count": self.holiday_count,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<AcademicCalendar {self.id}: {self.calendar_label} ({self.status})>"
