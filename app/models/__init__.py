from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models.journey import Journey
from app.models.academic_calendar import AcademicCalendar
from app.models.holiday import Holiday
from app.models.google_calendar import GoogleCalendarConnection, CalendarEventSync

__all__ = [
    "db",
    "Journey",
    "AcademicCalendar",
    "Holiday",
    "GoogleCalendarConnection",
    "CalendarEventSync",
]
