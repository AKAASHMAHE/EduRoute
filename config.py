import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Centralized Application Configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-train-reminder-2026")

    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///train_reminder.db")
    if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            instance_dir = BASE_DIR / "instance"
            instance_dir.mkdir(exist_ok=True)
            db_path = str(instance_dir / db_path)
            DATABASE_URL = f"sqlite:///{db_path}"

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))

    # Business Logic Configuration
    BOOKING_WINDOW_DAYS = int(os.getenv("BOOKING_WINDOW_DAYS", 60))
    REMINDER_DAYS_BEFORE = int(os.getenv("REMINDER_DAYS_BEFORE", 1))
    APPLICATION_NAME = os.getenv("APPLICATION_NAME", "Train Booking Date Reminder System")

    ITEMS_PER_PAGE = 10

    # PDF Processing & Upload Security
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10 MB limit
    ACADEMIC_CALENDAR_UPLOAD_DIR = os.getenv(
        "ACADEMIC_CALENDAR_UPLOAD_DIR",
        str(BASE_DIR / "instance" / "uploads" / "academic_calendars"),
    )

    # Google OAuth & Calendar Integration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/google/callback")
    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    CALENDAR_EVENT_TIMEZONE = os.getenv("CALENDAR_EVENT_TIMEZONE", "Asia/Kolkata")
    CALENDAR_EVENT_HOUR = int(os.getenv("CALENDAR_EVENT_HOUR", 9))

