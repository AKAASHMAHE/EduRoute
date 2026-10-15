# EduRoute – Train Booking Date Reminder System

A Flask web application that helps students plan train journeys around academic holidays and calculates the **expected IRCTC booking opening date** (Journey Date − 60 days). Optionally syncs a reminder event to Google Calendar.

---

## Features

| Feature | Status |
|---|---|
| Journey CRUD with server-side validation | ✅ |
| Booking date calculator (60-day IRCTC advance booking window) | ✅ |
| Dashboard with search, filter, sort | ✅ |
| Academic calendar PDF upload & holiday extraction | ✅ |
| Multi-format date parsing (ISO, DMY, named month, ranges) | ✅ |
| Holiday review / confirm / reject / bulk-confirm | ✅ |
| Journey planning from confirmed holidays | ✅ |
| Google OAuth 2.0 + Google Calendar event sync | ✅ |
| Calendar sync lifecycle (create / update / delete / missing / re-auth) | ✅ |
| CSRF protection on all state-changing routes | ✅ |
| 46 automated tests (unit + integration, mocked Google API) | ✅ |

---

## Problem Statement

IRCTC opens tatkal / advance booking **60 days before** the journey date at 10:00 AM. Students often miss this window for academic holiday travel. EduRoute:
1. Extracts holidays from institutional academic-calendar PDFs.
2. Lets users plan trips against confirmed holidays.
3. Calculates the exact booking opening date.
4. Optionally creates a Google Calendar reminder on that date.

---

## PDF Upload – Approach & Limitations

- **Upload security**: Magic-byte check (`%PDF-`), 16 MB size limit, UUID filename, stored outside `static/`.
- **Text extraction**: Uses PyMuPDF (`fitz`) if installed. Falls back to a pure-Python FlateDecode stream extractor.
- **Scanned / image-only PDFs**: No OCR is attempted. Extraction will succeed but find zero text. The calendar is marked `PROCESSED` with 0 holidays and the message explains the limitation. Install Tesseract + `pytesseract` separately if OCR is required (not bundled).
- **Reprocessing**: Only `UNCONFIRMED` holidays are replaced. `CONFIRMED` and `REJECTED` holidays survive reprocessing.

---

## Holiday Workflow

```
Upload PDF → Extraction (UNCONFIRMED holidays) → Review UI
  → Confirm / Reject / Edit → CONFIRMED holidays appear in
  "Plan From Holiday" page → Journey linked to holiday
```

- Never auto-creates journeys for every holiday.
- Only CONFIRMED holidays are selectable for trip planning.
- Duplicate journeys (same source/destination/date/holiday) are blocked.

---

## Google Cloud Setup (Manual Steps Required)

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable **Google Calendar API** (`APIs & Services → Library`).
4. Create **OAuth 2.0 Credentials** (`APIs & Services → Credentials → Create Credentials → OAuth client ID`):
   - Application type: **Web application**
   - Authorised redirect URI: `http://localhost:5000/google/callback` (or your domain)
5. Download the credentials and note `Client ID` and `Client Secret`.
6. Add your test Google account to **Test users** under the OAuth consent screen (while in "Testing" publish status).

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```dotenv
# Flask core
SECRET_KEY=replace-with-a-strong-random-key
DEBUG=False
TESTING=False
DATABASE_URL=sqlite:///journeys.db

# IRCTC booking window (days before journey date)
BOOKING_WINDOW_DAYS=60

# File upload
ACADEMIC_CALENDAR_UPLOAD_DIR=instance/uploads
MAX_CONTENT_LENGTH=16777216   # 16 MB

# Google OAuth (required for Calendar sync)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/google/callback

# Google Calendar
GOOGLE_CALENDAR_ID=primary
CALENDAR_EVENT_TIMEZONE=Asia/Kolkata
CALENDAR_EVENT_HOUR=10
```

---

## Installation

```bash
# 1. Clone and enter project
cd EduRoute

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and edit environment file
copy .env.example .env
# Edit .env with your SECRET_KEY and (optionally) Google credentials

# 5. Initialise / migrate the database
python -m app.database.migration

# 6. Run the application
python run.py
# Visit http://localhost:5000
```

---

## Database Migrations

The project uses a **non-destructive raw-SQL migration runner** (`app/database/migration.py`).

- On first run it creates all tables via SQLAlchemy `create_all`.
- On subsequent runs it inspects existing tables and `ALTER TABLE … ADD COLUMN` for any missing columns.
- **Existing data is never deleted.**
- No Alembic / Flask-Migrate required.

Run manually at any time:
```bash
python -m app.database.migration
```

---

## Running Tests

```bash
.\.venv\Scripts\pytest -q --tb=short
```

Expected: **46 passed**. Tests use an in-memory SQLite DB, synthetic minimal PDFs, and a `MockGoogleCalendarService` — no real Google credentials are needed.

---

## Security Notes

| Control | Implementation |
|---|---|
| CSRF | Custom `CSRFProtect` token on every state-changing form |
| OAuth state | Random UUID validated on callback; mismatch → 400 |
| File upload | Magic bytes + extension + size limit + UUID filename + stored outside `static/` |
| Secrets | Only in `.env`, never logged, never in HTML |
| Production | Set `DEBUG=False`; use HTTPS (required for OAuth in production) |
| Stack traces | Disabled when `DEBUG=False`; custom 404/500/400 pages served |

### HTTPS for Production OAuth

Google OAuth requires `https://` redirect URIs in production. Use a reverse proxy (nginx / caddy) with TLS in front of Gunicorn. For local development `http://localhost:5000` is allowed as an exception.

---

## Notification Limitations

- Booking dates are **mathematical estimates** (`Journey Date − 60 days`). IRCTC may alter advance reservation periods.
- Google Calendar events are **reminders only**; actual ticket availability must be verified on the IRCTC platform.
- The system does **not** poll or check live railway availability.
- Calendar sync requires the app to be running and the user to trigger a sync; there is no background scheduler.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| PDF uploads 0 holidays | PDF is likely scanned / image-only; OCR not supported |
| Google connect fails "credentials missing" | Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env` |
| Sync status `REAUTH_REQUIRED` | User revoked access; click "Reconnect Google" |
| Sync status `EXTERNAL_EVENT_MISSING` | Event was deleted from Google Calendar; click "Re-sync" |
| `413 Request Entity Too Large` | PDF exceeds 16 MB; reduce file size or increase `MAX_CONTENT_LENGTH` |
| `WTF_CSRF_ENABLED` errors in tests | Ensure test config sets `WTF_CSRF_ENABLED = False` |

---

## Known Limitations

1. **No live IRCTC availability**: Booking dates are estimates only.
2. **No OCR**: Scanned academic calendars require a text-layer PDF.
3. **Single-user**: No multi-user auth; one Google Calendar connection per deployment.
4. **No background sync**: Calendar events must be synced manually via the UI or journey edit.
5. **SQLite only**: Suitable for development; switch to PostgreSQL for production.
6. **Google OAuth not tested with real credentials** in the automated test suite (mocked only).

---

## Architecture

```
app/
├── __init__.py          # App factory, blueprints, CSRF init
├── models/              # Journey, AcademicCalendar, Holiday, GoogleCalendarConnection, CalendarEventSync
├── routes/              # main_bp, academic_calendar_bp, google_bp
├── services/            # booking_service, pdf_extraction_service, holiday_extraction_service, google_calendar_service
├── utils/               # csrf.py, file_validators.py, validators.py, helpers.py
└── templates/           # Jinja2 + Bootstrap 5
tests/                   # 46 tests across 7 test modules
```
