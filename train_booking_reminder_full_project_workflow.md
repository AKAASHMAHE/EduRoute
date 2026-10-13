# Train Booking Date Reminder System
## Complete Project Workflow, Implementation Status, and Remaining Work

**Document purpose:** This document records the current project workflow, what has been reported as implemented, what remains to be implemented, and the detailed steps required to finish the academic-calendar-to-Google-Calendar automation.

**Status basis:** The existing project `README.md` and the build report provided by the project team. The build report states that 22 automated tests passed. The source code and running application were not independently inspected as part of preparing this document, so implementation claims below are marked as *reported complete* where appropriate.

---

# 1. Project Overview

## 1.1 Project title

**Train Booking Date Reminder System**

## 1.2 Project objective

Build a Python web application that helps a passenger identify the expected date on which train-ticket booking may open for a planned journey. The extended project should also read an academic-calendar PDF, identify holidays, let the user select intended travel dates, calculate expected booking dates, and create reminders in Google Calendar.

## 1.3 Problem statement

Passengers may forget when train-ticket booking is expected to open for a future journey. This becomes harder when they have several journeys planned around college holidays, semester breaks, public holidays, or other days off. Manually reading an academic calendar, calculating booking dates, and adding reminders to a personal calendar creates repetitive work and opportunities for mistakes.

## 1.4 Intended final solution

The completed system should support this end-to-end workflow:

1. Open the web application.
2. Upload an academic-calendar PDF.
3. Validate and process the PDF.
4. Extract text and identify possible holidays and vacation periods.
5. Display detected dates for user review and correction.
6. Save confirmed holidays.
7. Let the user select holidays they may want to travel on.
8. collect journey details such as source, destination, and optional train information.
9. Treat the selected travel/holiday date as the planned journey date.
10. Calculate the expected booking opening date using the configured booking window.
11. Display the planned journey and booking reminder details.
12. Connect Google Calendar through an authorized Google OAuth flow.
13. Create a Google Calendar event on the expected booking date.
14. Configure a calendar notification where supported.
15. Record the external event ID and synchronization status.
16. Update or remove the external event when the linked journey changes or is deleted, subject to user confirmation and synchronization rules.
17. Show failures and provide a way to retry synchronization.
18. Test the complete workflow and document how to install, configure, run, and maintain it.

**Important:** A calculated booking date is an estimate based on configuration. It is not proof that a railway platform has opened bookings or that tickets are available. The system must not claim live availability unless a reliable, authorized data source verifies it.

---

# 2. Current Implementation Status

## 2.1 Reported complete in the existing project

The provided build report says the following features have been implemented:

- Flask application with modular structure.
- Flask application factory (`create_app()`).
- Centralized configuration in `config.py` and environment variables in `.env`.
- SQLite database using Flask-SQLAlchemy.
- Journey database model.
- Booking-date calculation service.
- Dynamic booking and reminder status calculations.
- Add, view, edit, and delete journey operations.
- Per-journey reminder toggle.
- Dashboard summary statistics.
- Search, status filtering, and sorting.
- Live AJAX booking-date preview.
- JSON API endpoints.
- Responsive Bootstrap-based UI.
- Reusable Jinja2 components.
- Server-side input validation.
- Automated tests.
- Project README and setup instructions.

The build report states **22/22 tests passed**. This is a reported test result, not an independent test run performed while preparing this document.

## 2.2 Confirmed by the uploaded README

The uploaded README documents the following:

- The project is a Flask/SQLAlchemy/Jinja2/Bootstrap 5 web application.
- The expected booking date is calculated as journey date minus a configurable booking window.
- The default example uses `BOOKING_WINDOW_DAYS=60`.
- Journey management and dashboard features are described.
- An AJAX calculation API is documented.
- The JSON API includes journey retrieval endpoints.
- pytest is the documented test runner.
- Academic-calendar PDF extraction and Google Calendar integration appear as future/unimplemented enhancements rather than existing features in that README.

## 2.3 Not yet implemented according to the available project documentation

The following requested workflow is not documented as implemented and should be treated as **remaining work until verified in source code**:

- Academic-calendar PDF upload and management.
- PDF extraction pipeline.
- Holiday and vacation date detection.
- User review and correction of extracted holidays.
- Academic-calendar and holiday database entities.
- Holiday selection and conversion to planned journeys.
- Google OAuth connection.
- Google Calendar API integration.
- Event creation, update, deletion, duplicate prevention, and sync status.
- Calendar notification configuration.
- End-to-end tests for the new workflow.

---

# 3. Existing Technology Stack

## 3.1 Current stack

- **Language:** Python 3.10+ as stated in the build report; the README describes Python 3.11+.
- **Web framework:** Flask.
- **Templates:** Jinja2.
- **Frontend:** HTML5, CSS3, JavaScript ES6, Bootstrap 5.3.
- **Database:** SQLite.
- **ORM:** Flask-SQLAlchemy.
- **Data processing:** pandas and NumPy, according to the build report.
- **Configuration:** `config.py`, `python-dotenv`, `.env`.
- **Testing:** pytest.
- **Application entry point:** `run.py`.

Before changing Python versions or dependencies, inspect the existing `requirements.txt` and the installed environment. Avoid upgrading dependencies without a reason.

## 3.2 Additional dependencies likely needed for the remaining work

Select and pin compatible versions after checking the existing environment.

- A PDF text extraction library, such as **PyMuPDF** (`pymupdf`).
- Google API client library, typically `google-api-python-client`.
- Google OAuth/authentication libraries compatible with the chosen flow, such as `google-auth`, `google-auth-oauthlib`, and `google-auth-httplib2`.
- A CSRF-protection solution such as Flask-WTF if not already included.
- Optional PDF text/OCR fallback tooling only if required by real scanned calendar PDFs. OCR may require a separate system dependency and should not be assumed available.

Do not add all possible libraries automatically. Inspect existing dependencies, select what is necessary, and document the choice.

---

# 4. Existing Application Architecture

The existing application is intended to follow this flow:

```text
Browser
  |
  v
Flask web route / API route
  |
  v
Server-side validation
  |
  v
Service layer
  |
  +--> Booking-date calculation
  |
  +--> Reminder/status calculations
  |
  +--> Dashboard data processing
  |
  v
SQLAlchemy models
  |
  v
SQLite database
  |
  v
Jinja2 template or JSON response
  |
  v
Browser
```

Keep the existing architecture. Do not rewrite the project as a new application.

---

# 5. Existing Project Structure

The uploaded README documents this general structure:

```text
train-booking-reminder/
|
├── app/
│   ├── __init__.py
│   ├── config/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── dashboard.html
│   │   ├── add_journey.html
│   │   ├── edit_journey.html
│   │   ├── journey_detail.html
│   │   ├── 404.html
│   │   ├── 500.html
│   │   └── components/
│   └── static/
│       ├── css/style.css
│       └── js/main.js
|
├── tests/
├── instance/
├── .env
├── .env.example
├── .gitignore
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

The build report identifies these existing files as important:

- `app/models/journey.py`
- `app/routes/main.py`
- `app/routes/api.py`
- `app/services/booking_service.py`
- `app/services/reminder_service.py`
- `app/utils/validators.py`
- `app/utils/helpers.py`
- `app/templates/`
- `app/static/css/style.css`
- `app/static/js/main.js`
- `tests/`

The agent implementing the remaining features must inspect the actual workspace first. The real source tree takes precedence over this illustrative listing.

---

# 6. Detailed Workflow of the Existing Completed Features

## 6.1 Application startup

1. The developer installs dependencies from `requirements.txt`.
2. Environment settings are read from `.env` through the configuration system.
3. `run.py` imports `create_app()`.
4. `create_app()` creates the Flask application.
5. Configuration is loaded.
6. SQLAlchemy is initialized.
7. Web and API Blueprints are registered.
8. Error handlers and required template helpers are registered.
9. Database tables are initialized using the existing development strategy.
10. Flask starts on the configured host and port.
11. The user opens the local website in a browser.

**Verification needed:** Check that production mode does not expose debug details, that initialization does not erase existing data, and that database creation/migration behavior is documented.

## 6.2 Manual journey creation

1. The user opens the add-journey page.
2. The user enters a trip name.
3. The user enters the source station.
4. The user enters the destination station.
5. The user optionally enters a train name or number.
6. The user selects the journey date.
7. The user chooses whether the reminder is enabled.
8. Client-side validation provides convenience feedback.
9. The form is submitted to Flask.
10. Server-side validation checks required fields and allowed values.
11. The system rejects an empty trip name, source, or destination.
12. The system rejects identical source and destination values.
13. The system rejects invalid dates and past journey dates.
14. If invalid, the page redisplays useful validation messages.
15. If valid, the Journey model is created.
16. SQLAlchemy saves the journey to SQLite.
17. The user is redirected to the dashboard.
18. A success message is displayed.

## 6.3 Booking-date calculation

1. The system receives a journey date.
2. The date is parsed as a date object.
3. The booking window is read from configuration.
4. The booking service subtracts the configured number of days.
5. The calculated date is returned.
6. The application calculates days until the expected booking date.
7. The application calculates days until the journey date.
8. A display-friendly date format is produced.
9. The expected booking date is displayed in the UI/API.
10. The system describes it as expected, not confirmed live availability.

The configured window must be reviewed against the applicable railway rules before relying on it for real trips. It should not be described as universally correct for every train, quota, booking category, or future policy.

## 6.4 Dashboard

1. The user opens `/dashboard`.
2. The application retrieves stored journeys.
3. The service enriches each journey with calculated booking metadata.
4. Dashboard statistics are computed.
5. Search input is applied where present.
6. Status filters are applied where present.
7. Sorting is applied according to the selected option.
8. Each journey is rendered as a card or appropriate responsive UI component.
9. The dashboard displays trip details, expected booking date, journey date, status, and reminder state.
10. Empty-state messaging is displayed when no journeys exist.

## 6.5 Journey details and editing

1. The user selects a journey.
2. The application loads the matching record.
3. If no record exists, a 404 response is returned.
4. The detail page displays stored and calculated information.
5. The user may open the edit form.
6. Existing values are pre-filled.
7. The user changes one or more fields.
8. Server-side validation runs again.
9. Valid changes are saved.
10. Booking metadata is recalculated from the updated journey date.
11. A success message is shown.
12. The user returns to the dashboard or detail page.

## 6.6 Journey deletion and reminder toggle

1. The user requests deletion from the journey interface.
2. A confirmation is presented in the UI.
3. Deletion is submitted using a state-changing request, preferably POST with CSRF protection.
4. The server validates the record and request.
5. The record is deleted if the operation is valid.
6. A success message is shown.
7. The reminder toggle similarly submits a state-changing request.
8. The stored reminder preference is updated.
9. The UI reflects the new preference.

The existing report says these features work; source code should still be reviewed for CSRF protection and correct HTTP methods.

## 6.7 Existing API workflow

The README documents these endpoints:

- `POST /api/v1/calculate-booking-date`
- `GET /api/v1/journeys`
- `GET /api/v1/journeys/<id>`

For the calculation endpoint:

1. A client sends a journey date as JSON.
2. The API validates the payload.
3. The booking service calculates the expected booking date.
4. The API returns JSON metadata such as the configured window, calculated date, days remaining, status, and reminder information.
5. The frontend uses the result for the live preview.

For journey endpoints:

1. The client requests a collection or a single journey.
2. The API retrieves records.
3. Calculated metadata is included as documented by the implementation.
4. A JSON response is returned.
5. Invalid IDs or malformed input should produce appropriate error responses.

---

# 7. Remaining Phase 1 — Academic Calendar PDF Upload and Management

## 7.1 Goal

Let the user upload an academic-calendar PDF and extract possible holiday dates without manually entering every holiday.

## 7.2 Required UI

Add an Academic Calendar page with:

- Upload form.
- PDF-only file selection.
- Maximum file-size guidance.
- Upload button and processing state.
- Uploaded calendar list.
- Processing status.
- Extracted holiday count.
- Actions to view holidays, reprocess, or remove an uploaded calendar.
- Clear errors when a PDF cannot be processed.

## 7.3 Required backend steps

1. Add a route to display the academic-calendar page.
2. Add a POST route for upload.
3. Validate that a file was supplied.
4. Validate extension and MIME/content signature where practical; do not rely solely on the filename.
5. Enforce a configured upload-size limit.
6. Generate a safe internal filename rather than trusting the original filename.
7. Store files in a controlled directory outside executable/static paths.
8. Avoid exposing arbitrary filesystem paths to users.
9. Record metadata for the uploaded calendar.
10. Create a processing state such as `UPLOADED`, `PROCESSING`, `PROCESSED`, or `FAILED`.
11. Extract PDF text using the selected PDF library.
12. Detect whether the PDF contains extractable text.
13. If the PDF is image-only/scanned, show a clear message or implement a separately configured OCR fallback.
14. Normalize whitespace and line breaks without losing meaningful date context.
15. Preserve a safe reference to the source PDF and its extracted text or processing result as appropriate.
16. Store processing errors in logs and show user-safe messages.
17. Add tests for successful, invalid, oversized, empty, corrupted, and scanned PDFs.

## 7.4 Suggested new modules

These are suggestions, not a claim that files already exist:

```text
app/
├── models/
│   ├── academic_calendar.py
│   └── holiday.py
├── routes/
│   └── academic_calendar.py
├── services/
│   ├── pdf_extraction_service.py
│   └── holiday_extraction_service.py
├── utils/
│   └── file_validators.py
└── templates/
    ├── academic_calendars.html
    ├── upload_calendar.html
    └── calendar_holidays.html
```

Follow existing naming and Blueprint conventions when implementing.

## 7.5 Academic calendar data to retain

Where useful, retain:

- Internal ID.
- Original display filename.
- Safe stored filename or storage key.
- Upload timestamp.
- Calendar label/academic year.
- Processing status.
- Number of detected holidays.
- Error summary, if processing failed.
- Created and updated timestamps.

Avoid storing unnecessary duplicate copies of large extracted text.

---

# 8. Remaining Phase 2 — Holiday Detection and Review

## 8.1 Goal

Turn raw PDF text into a structured list of candidate holidays that a user can verify.

## 8.2 Extraction workflow

1. Read the extracted text.
2. Split the text into lines or meaningful sections.
3. Detect date patterns such as:
   - `15 August 2026`
   - `15-08-2026`
   - `2026-08-15`
   - `15 Aug`
   - Date ranges such as `20 December – 2 January`
4. Resolve missing years only when the academic-calendar context makes the year reasonably clear.
5. Detect likely holiday names from nearby text.
6. Detect possible vacation ranges.
7. Normalize dates to a standard internal format.
8. Validate that candidate dates are real dates.
9. Flag ambiguous dates and ranges for user review.
10. Detect duplicate candidates within the same calendar.
11. Preserve source context or page/line information where available.
12. Store candidates as unconfirmed until the user reviews them.

## 8.3 Important limitations

PDF layouts vary significantly. Text extraction may not preserve table columns, reading order, or date-to-description relationships perfectly.

Therefore:

- Do not automatically treat every date in a PDF as a holiday.
- Do not silently guess an ambiguous date.
- Do not automatically create a journey from an unconfirmed extraction.
- Let the user correct the holiday name and date.
- Let the user reject false positives.
- Show the original extracted context where useful.
- Record whether a date was detected automatically or corrected by the user.

## 8.4 Holiday review interface

The user should see a table or list containing:

- Selection checkbox.
- Holiday name.
- Start date.
- End date, if applicable.
- Holiday category/type, if detected.
- Source academic calendar.
- Extraction/review status.
- Edit action.
- Confirm action.
- Reject/delete action.

The user should be able to:

1. Edit an incorrect name.
2. Edit an incorrect date.
3. Correct a multi-day range.
4. Mark a candidate as confirmed.
5. Reject a false positive.
6. Confirm several selected candidates where appropriate.
7. View the source calendar.
8. Reprocess the source PDF without silently duplicating confirmed records.

## 8.5 Suggested holiday model

A Holiday record may contain:

- ID.
- Academic calendar ID.
- Holiday name.
- Start date.
- End date.
- Category/type, if known.
- Source text/context.
- Extraction confidence or review notes, if supported.
- Review status.
- Created and updated timestamps.

Use database constraints and relationships appropriate to the existing SQLAlchemy design.

---

# 9. Remaining Phase 3 — Holiday-Based Journey Planning

## 9.1 Goal

Allow the user to select a confirmed holiday and create a planned journey using that date, without manually retyping the date.

## 9.2 Workflow

1. Display confirmed holidays.
2. User selects one holiday or a suitable travel date within a holiday range.
3. The application displays the selected holiday name and date.
4. The user enters source station.
5. The user enters destination station.
6. The user optionally enters train name/number.
7. The user enables or disables the reminder.
8. The server validates the selected holiday and journey details.
9. The system sets the journey date from the confirmed holiday/travel date.
10. The booking service calculates the expected booking date.
11. The application previews the journey date and expected booking date.
12. The user confirms creation.
13. A Journey record is created and associated with the holiday when appropriate.
14. The dashboard shows the resulting journey.
15. The application indicates whether calendar synchronization is configured and available.

## 9.3 User choice is essential

A college holiday does not necessarily mean the user will travel. The application should suggest dates and let the user decide. It must not automatically create unwanted journeys for every holiday.

## 9.4 Multi-day holidays

For a holiday spanning several days:

- Display the complete range.
- Let the user choose a specific departure date.
- Avoid automatically generating one journey for every day.
- Allow a journey date to differ from the first day of the holiday when appropriate.
- Explain which date is used for booking-date calculation.

## 9.5 Data association

A Journey may optionally reference the Holiday that inspired it. Keep manual journeys working even when they are not associated with any academic calendar.

---

# 10. Remaining Phase 4 — Google OAuth and Calendar Authorization

## 10.1 Goal

Allow the user to authorize the application to create and manage events in their Google Calendar.

## 10.2 Prerequisites

Before implementation:

1. Create or select a Google Cloud project.
2. Enable the Google Calendar API.
3. Configure the OAuth consent screen.
4. Create OAuth credentials for the appropriate application type.
5. Register the correct redirect URI for local development and deployment.
6. Configure authorized test users if the consent screen is in testing mode.
7. Store client credentials in environment variables or a secure secret store.
8. Never commit credentials or token files to source control.

## 10.3 Application workflow

1. User opens Calendar Integration settings.
2. Application explains what access is requested and why.
3. User selects Connect Google Calendar.
4. Flask redirects to Google's OAuth authorization flow.
5. User signs in and grants consent.
6. Google redirects to the registered callback URL.
7. Application validates the authorization response and state.
8. Application exchanges the authorization code for credentials.
9. Application stores authorization data securely.
10. Application confirms the connection status.
11. User can disconnect the integration.
12. If access is revoked or credentials expire, the application reports the issue and provides a recovery path.

## 10.4 Security requirements

- Request the minimum suitable Calendar scopes.
- Use secure OAuth state validation.
- Use HTTPS in deployment.
- Do not expose access tokens in HTML or logs.
- Do not store tokens in plaintext without evaluating the security implications.
- Protect OAuth callbacks against forgery.
- Support token refresh where permitted.
- Support disconnect/revocation behavior.
- Do not treat a single-user local development shortcut as a secure multi-user production design.
- Keep Google account identity separate from journey data if multiple users are added later.

For a single-user academic demonstration, a simple authorized account design may be sufficient, but it still must protect credentials.

---

# 11. Remaining Phase 5 — Google Calendar Event Management

## 11.1 Goal

Create a real calendar event on the expected booking date for each selected planned journey.

## 11.2 Event creation workflow

1. Confirm the Journey has a valid journey date.
2. Calculate the expected booking date from current configuration.
3. Confirm the user has connected Google Calendar.
4. Check whether an event is already linked to the Journey.
5. If no event exists, construct an event payload.
6. Use a clear event title, for example:
   `Train Booking Opens — Chennai to Bengaluru`
7. Include relevant details in the description:
   - Trip name.
   - Source and destination.
   - Train name/number if provided.
   - Holiday name if applicable.
   - Expected booking date.
   - Journey date.
   - Booking-window assumption.
   - Reminder to verify actual booking availability on the relevant railway platform.
8. Set the event date and time according to the selected reminder policy.
9. Configure Google Calendar notification overrides if supported and permitted by the API and calendar settings.
10. Submit the event creation request.
11. Save the returned Google event ID and calendar ID.
12. Mark synchronization as successful.
13. Display the resulting status in the application.

## 11.3 Date and time policy

The expected booking date is a date, not inherently a specific time.

Define a configurable default event time and timezone rather than silently inventing one. The UI should clearly explain the chosen reminder time. Consider all-day events where appropriate, but validate Google Calendar's all-day event date semantics carefully.

Use a consistent timezone strategy. Do not mix naive local datetimes, UTC timestamps, and date-only values without explicit conversion rules.

## 11.4 Notifications

Google Calendar event creation and actual notification delivery are different concerns.

- Create the event.
- Configure supported event reminders if appropriate.
- Explain that notification behavior may also depend on the user's Google Calendar settings, device settings, and account configuration.
- Do not claim that a notification was delivered merely because event creation succeeded.

## 11.5 Sync metadata

Maintain enough metadata to manage the external event:

- Linked Journey ID.
- Google calendar ID.
- Google event ID.
- Last sync status.
- Last successful sync timestamp.
- Last error summary, without secrets.
- Expected booking date last synchronized.
- Optional version/hash of synchronized event content.

A separate sync table is preferable if it makes the relationship cleaner or if more than one calendar/account can be supported. Follow the simplest architecture suitable for the project.

---

# 12. Remaining Phase 6 — Synchronization Lifecycle

## 12.1 Duplicate prevention

When the user clicks Sync more than once:

1. Look up the existing sync record.
2. If the event is already linked, update it when appropriate rather than creating a second event.
3. If the external event ID is stale or deleted, recover gracefully.
4. Store the external event ID after successful creation.
5. Make repeated sync attempts safe where practical.
6. Test retries and partial failures.

## 12.2 Journey edit

When a linked journey changes:

1. Save and validate the new journey values.
2. Recalculate the expected booking date.
3. Identify the linked Google event.
4. Compare current event data with the updated journey.
5. Update the existing event rather than creating a duplicate.
6. Record sync success/failure.
7. Inform the user if synchronization failed.
8. Provide a retry action.

If the Google account is disconnected, preserve the local journey and mark the sync as needing attention rather than losing data.

## 12.3 Journey deletion

When a linked journey is deleted:

1. Check whether a Google event is linked.
2. Explain the effect of deletion in the UI.
3. Decide whether external event deletion should be automatic or require confirmation.
4. If authorized, delete the linked event.
5. Record the outcome.
6. Avoid losing track of an external event if deletion fails.
7. Use a clear policy for retained sync records or cleanup.

Do not silently leave orphaned Google events without informing the user.

## 12.4 Calendar disconnect

1. User chooses Disconnect.
2. Application stops future API operations.
3. Token data is revoked/deleted as appropriate.
4. Existing calendar events are not assumed to be deleted.
5. Explain whether already-created events remain in Google Calendar.
6. Mark sync operations as disconnected or requiring reconnection.

## 12.5 Error and retry states

Support statuses such as:

- `NOT_CONNECTED`
- `NOT_SYNCED`
- `SYNC_PENDING`
- `SYNCED`
- `SYNC_FAILED`
- `REAUTH_REQUIRED`
- `EXTERNAL_EVENT_MISSING`

Use a consistent set of statuses and avoid contradictory state transitions.

---

# 13. Remaining Phase 7 — User Interface Integration

The new features should be added to the existing interface rather than replacing it.

## 13.1 Navigation

Add suitable navigation entries, for example:

- Dashboard.
- Add Journey.
- Academic Calendars.
- Detected Holidays.
- Google Calendar Integration.

Keep navigation labels simple and consistent.

## 13.2 Academic calendar page

Display:

- Uploaded calendar list.
- Upload action.
- Processing status.
- Number of confirmed holidays.
- Number of candidates needing review.
- Failed processing messages.
- View/reprocess/delete actions.

## 13.3 Holiday review page

Display:

- Holiday name.
- Date or date range.
- Academic-calendar source.
- Review state.
- Edit and confirm controls.
- Selection for trip planning.

## 13.4 Dashboard enhancements

Add relevant sections:

- Upcoming expected booking dates.
- Selected holiday-based trips.
- Calendar synchronization state.
- Failed sync items requiring attention.
- Link to review detected holidays.
- Link to connect Google Calendar when disconnected.

Avoid overcrowding the existing dashboard. Use cards or separate pages where more appropriate.

## 13.5 Journey detail page

Display:

- Journey details.
- Expected booking date.
- Booking-window assumption.
- Reminder preference.
- Source holiday, if any.
- Google Calendar sync status.
- Last synchronization time.
- Retry sync action where applicable.
- Link to the Google Calendar event when a valid URL is available.

## 13.6 User feedback

Use consistent success, warning, and error messages for:

- PDF uploaded.
- PDF processing started/completed/failed.
- Holidays extracted.
- Holiday corrected/confirmed.
- Journey created from a holiday.
- Google account connected/disconnected.
- Calendar event created/updated/deleted.
- Sync failed and retry required.

---

# 14. Remaining Phase 8 — Configuration and Secrets

Extend the current centralized configuration system. Do not create a competing configuration source.

Likely new environment settings include:

```env
# Existing settings: preserve current names and behavior
BOOKING_WINDOW_DAYS=60
REMINDER_DAYS_BEFORE=1

# PDF processing
MAX_CONTENT_LENGTH=10485760
ACADEMIC_CALENDAR_UPLOAD_DIR=instance/uploads/academic_calendars

# Google OAuth: provide real values outside source control
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/google/callback

# Calendar event policy
GOOGLE_CALENDAR_ID=primary
CALENDAR_EVENT_TIMEZONE=Asia/Kolkata
CALENDAR_EVENT_HOUR=9
```

These are illustrative values. Inspect the existing configuration and adapt names to match it. Do not overwrite current settings blindly.

Requirements:

- Add safe placeholders to `.env.example`.
- Keep actual `.env` and credentials out of Git.
- Add upload folders and token/credential files to `.gitignore` as appropriate.
- Validate required settings at startup or when the feature is used.
- Give helpful setup errors if Google credentials are missing.
- Keep debug mode disabled in production.
- Do not assume local callback URLs work in deployment.

---

# 15. Remaining Phase 9 — Database and Migrations

Inspect the current database schema before changing it.

Potential new entities:

1. **AcademicCalendar**
   - Upload metadata and processing state.
2. **Holiday**
   - Detected/confirmed holiday and date range.
3. **Journey-Holiday relationship**
   - Optional link showing which holiday inspired a journey.
4. **GoogleCalendarConnection**
   - Authorized account/token metadata where required.
5. **CalendarEventSync**
   - External event IDs and synchronization state.

Possible relationships:

```text
AcademicCalendar
      |
      +----< Holiday
                  |
                  | optional reference
                  v
                Journey
                  |
                  +----< CalendarEventSync
```

The exact relationship design should follow the actual app requirements.

Requirements:

- Do not delete existing journey data.
- Do not drop the database as a migration strategy.
- Do not rely on `create_all()` alone to update an existing schema.
- Use a migration strategy compatible with the current project if schema changes are needed.
- Add indexes and unique constraints where appropriate.
- Define behavior for duplicate holidays and duplicate sync records.
- Test both a fresh database and an existing database containing journeys.

---

# 16. Remaining Phase 10 — Security and Reliability

## 16.1 PDF upload security

- Restrict file types.
- Enforce upload size.
- Use generated filenames.
- Do not execute uploaded content.
- Keep uploaded files outside public static directories.
- Avoid path traversal.
- Handle malformed/corrupt PDFs.
- Do not trust MIME types supplied by the browser.
- Consider retention and deletion policies for uploaded documents.

## 16.2 Web security

- Protect state-changing routes against CSRF.
- Validate all server-side input.
- Keep secrets out of responses and logs.
- Use safe SQLAlchemy queries.
- Use secure session settings appropriate to deployment.
- Do not expose stack traces in production.
- Validate OAuth state and callback inputs.

## 16.3 External API reliability

- Handle network and timeout failures.
- Handle expired or revoked authorization.
- Handle permission errors.
- Handle API quota/rate-limit responses.
- Avoid infinite retry loops.
- Use bounded retries where appropriate.
- Record safe, actionable error messages.
- Keep the local application usable when Google Calendar is unavailable.

## 16.4 Data integrity

- Do not create journeys from unconfirmed holiday candidates.
- Avoid duplicate holidays on repeated processing.
- Avoid duplicate calendar events on retries.
- Recalculate booking dates when configuration or journey dates change.
- Explain when a changed booking-window configuration requires re-syncing events.
- Keep external synchronization failure separate from local journey save failure.

---

# 17. Remaining Phase 11 — Automated Testing

The existing build report states that 22 tests passed. Preserve and rerun the current suite after every major change.

Add tests for the new features.

## 17.1 PDF upload tests

- Valid PDF upload.
- Missing file.
- Wrong file extension.
- Wrong or invalid file content.
- File exceeding size limit.
- Corrupt PDF.
- Empty PDF.
- Text extraction failure.
- Scanned/image-only PDF handling.
- Safe filename generation.

## 17.2 Holiday extraction tests

- Full date with month name.
- Numeric date format.
- ISO date format.
- Date without year where context supplies it.
- Multi-day date range.
- Invalid date.
- Ambiguous date.
- Holiday name extraction.
- Duplicate detection.
- False-positive candidate review.
- User correction and confirmation.

Use synthetic test PDFs or text fixtures. Do not make tests depend on a real college calendar or external service.

## 17.3 Holiday-to-journey tests

- Create a journey from a confirmed holiday.
- Reject unconfirmed holiday use.
- Correctly select a date within a multi-day range.
- Preserve manual journey creation.
- Calculate the booking date from the chosen travel date.
- Avoid creating duplicate journeys unintentionally.

## 17.4 Google OAuth tests

- Connection settings page.
- Missing credentials.
- OAuth state mismatch.
- Successful callback using mocked Google responses.
- Authorization failure.
- Expired/revoked credentials.
- Disconnect behavior.

Do not use real credentials in unit tests.

## 17.5 Calendar synchronization tests

Mock the Google Calendar API.

Test:

- Create event.
- Update event.
- Delete event.
- Repeat sync without duplicate creation.
- External event missing.
- Network failure.
- Permission failure.
- Retry after failure.
- Correct event date and timezone.
- Notification configuration in event payload.
- Local journey remains saved when Google sync fails.

## 17.6 Regression tests

Rerun all existing tests for:

- Booking-date calculations.
- Reminder logic.
- Journey model.
- Existing routes.
- Existing API.
- Validation.
- Dashboard behavior.

Do not remove or weaken existing tests simply to make the suite pass.

---

# 18. Remaining Phase 12 — Manual End-to-End Verification

After automated tests pass, perform a manual walkthrough.

1. Start with a fresh test database.
2. Open the application.
3. Confirm existing manual journey functionality.
4. Upload a valid academic-calendar PDF.
5. Confirm upload validation.
6. Verify extracted text.
7. Review detected holiday candidates.
8. Correct one candidate and reject another.
9. Confirm selected holidays.
10. Choose one confirmed holiday for a planned trip.
11. Enter source and destination.
12. Confirm the expected booking date.
13. Save the journey.
14. Confirm the journey appears on the dashboard.
15. Connect a Google test account.
16. Sync the journey to Google Calendar.
17. Open Google Calendar and confirm the event.
18. Confirm event title, date, description, and configured notification settings.
19. Repeat sync and confirm no duplicate event is created.
20. Edit the journey date and confirm the existing event is updated.
21. Disable the reminder and verify the documented behavior.
22. Delete a linked journey and verify the chosen external-event deletion policy.
23. Simulate a Google API failure and confirm a useful error is shown.
24. Disconnect Google Calendar and verify the local application still works.
25. Restart the application and verify persistent records remain.
26. Run the entire automated test suite.
27. Check logs for unexpected exceptions or sensitive data.
28. Verify README setup steps from a clean environment.

Use a test Google account and test calendar for manual integration tests.

---

# 19. Remaining Phase 13 — Documentation

Update `README.md` with:

1. Project overview.
2. Problem statement.
3. Existing features.
4. Academic calendar upload workflow.
5. PDF extraction approach and limitations.
6. Holiday review workflow.
7. Holiday-to-journey workflow.
8. Google Cloud setup requirements.
9. Google OAuth configuration.
10. Required environment variables.
11. Database schema/migration instructions.
12. Installation steps.
13. Run instructions.
14. Test instructions.
15. Google Calendar connection steps.
16. Notification behavior and limitations.
17. Troubleshooting guide.
18. Security notes.
19. Known limitations.
20. Future enhancements.

Also document:

- Which features are implemented.
- Which features require Google credentials.
- Whether OCR is supported.
- What the booking-window assumption means.
- Whether the app has been tested with a real Google test calendar.

Never claim that a live external integration has been verified if only mocked tests were run.

---

# 20. Detailed Implementation Order for the Coding Agent

The coding agent should follow this order without rebuilding the entire project.

## Step 1 — Inspect and protect the existing project

- List all existing files.
- Read `README.md`, `requirements.txt`, `.env.example`, `config.py`, and `run.py`.
- Inspect application factory, models, routes, services, templates, and tests.
- Run existing tests before changes.
- Record the baseline result.
- Identify the real current schema.
- Do not overwrite functioning files blindly.

## Step 2 — Agree on the extension design

- Define the AcademicCalendar, Holiday, and sync data model.
- Define the PDF upload workflow.
- Define holiday review states.
- Define Google OAuth flow.
- Define calendar event lifecycle.
- Keep the design modular and proportionate to an academic project.

## Step 3 — Extend configuration and dependencies

- Add only necessary libraries.
- Extend `config.py`.
- Extend `.env.example`.
- Update `.gitignore`.
- Keep credentials out of source control.

## Step 4 — Add database models and migrations

- Add the new models.
- Define relationships and constraints.
- Implement a migration strategy.
- Test fresh and existing databases.
- Preserve existing journey records.

## Step 5 — Implement PDF upload

- Create UI and routes.
- Validate uploaded files.
- Store them safely.
- Record metadata and processing state.
- Add tests.

## Step 6 — Implement PDF text extraction

- Add the extraction service.
- Handle text-based and image-only PDFs appropriately.
- Add errors and logging.
- Add tests using fixtures.

## Step 7 — Implement holiday extraction

- Parse candidate dates and descriptions.
- Handle date formats and ranges.
- Store unconfirmed candidates.
- Detect duplicates.
- Add tests.

## Step 8 — Implement holiday review

- Build the holiday list/review UI.
- Add correction, confirmation, rejection, and deletion operations.
- Protect state-changing operations.
- Add tests.

## Step 9 — Implement holiday-based journey creation

- Let users select confirmed holidays.
- Collect source, destination, and optional train details.
- Use the existing booking service.
- Keep manual journey creation intact.
- Add tests.

## Step 10 — Implement Google OAuth

- Configure Google credentials.
- Implement connect/callback/disconnect routes.
- Protect the OAuth flow.
- Store credentials securely.
- Add mocked tests.

## Step 11 — Implement calendar event creation

- Construct correct event payloads.
- Define event date/timezone behavior.
- Add notification settings where supported.
- Store event IDs and sync status.
- Add mocked tests.

## Step 12 — Implement synchronization lifecycle

- Prevent duplicates.
- Update linked events after journey edits.
- Handle deletions.
- Handle disconnects and revoked access.
- Implement safe retry behavior.
- Add tests.

## Step 13 — Integrate the UI

- Update navigation.
- Add academic-calendar pages.
- Add holiday review pages.
- Add Google Calendar settings.
- Add dashboard and journey sync indicators.
- Keep responsive styling consistent.

## Step 14 — Security review

- Review upload security.
- Review CSRF.
- Review OAuth state.
- Review secrets and logs.
- Review access tokens.
- Review error responses.
- Review data retention.

## Step 15 — Regression and end-to-end tests

- Run the original suite.
- Run all new tests.
- Fix regressions.
- Perform manual Google test-calendar verification where credentials are available.

## Step 16 — Documentation and final report

- Update README and environment examples.
- Document setup and limitations.
- Provide the actual test results.
- List implemented and remaining features honestly.
- Do not claim success for any unexecuted test or unverified external integration.

---

# 21. Final Acceptance Criteria

The extension is complete only when the applicable criteria below have been verified.

## Existing application

- [ ] Existing application still starts.
- [ ] Existing journey CRUD works.
- [ ] Existing booking-date calculation works.
- [ ] Existing dashboard and API work.
- [ ] Existing tests still pass.

## Academic calendar

- [ ] PDF upload works.
- [ ] File validation and size limits work.
- [ ] PDF extraction works on supported PDFs.
- [ ] Scanned PDF behavior is explained or OCR is implemented.
- [ ] Holiday candidates are detected.
- [ ] User can review and correct candidates.
- [ ] Confirmed holidays are persisted.
- [ ] Duplicate processing does not create duplicate holiday records.

## Holiday-based planning

- [ ] User can select a confirmed holiday.
- [ ] User can select a date within a holiday range.
- [ ] User can enter journey details.
- [ ] Expected booking date is calculated correctly.
- [ ] Journey is saved and shown on the dashboard.
- [ ] Existing manual journey creation still works.

## Google Calendar

- [ ] OAuth connection works with configured credentials.
- [ ] Credentials are not hardcoded or committed.
- [ ] Calendar event creation works.
- [ ] Event includes useful journey/holiday details.
- [ ] Event date and timezone are correct.
- [ ] Supported reminder settings are configured.
- [ ] Event ID and sync state are persisted.
- [ ] Repeated sync avoids duplicate events.
- [ ] Journey edits update the linked event.
- [ ] Deletion follows the documented external-event policy.
- [ ] API failures produce actionable errors.
- [ ] Disconnect and reauthorization behavior are handled.
- [ ] Real Google test-calendar behavior has been verified before claiming full integration success.

## Final quality

- [ ] All old and new tests pass.
- [ ] End-to-end workflow is tested.
- [ ] Database migrations preserve existing data.
- [ ] Upload and OAuth security checks are complete.
- [ ] README and `.env.example` are updated.
- [ ] No placeholder core functionality remains.
- [ ] Final report accurately distinguishes tested features from unverified features.

---

# 22. Explicit Scope Boundaries

The following are not automatically required for the current milestone unless separately approved:

- Automatic purchase of train tickets.
- Storing railway account passwords.
- Payment processing.
- Automatic creation of trips for every detected holiday.
- Guaranteed real-time ticket availability.
- SMS delivery through a paid provider.
- Full multi-user account management.
- Production cloud deployment.
- OCR for every possible scanned PDF if it is not feasible within the project's environment.

The core new milestone is **academic calendar PDF → reviewed holidays → user-selected travel date → expected booking date → Google Calendar event and reminder**.

---

# 23. Final Project Status Summary

## Reported complete

- Flask web application.
- Journey management.
- Booking-date calculation.
- Dashboard and filtering.
- In-app reminder/status logic.
- JSON API.
- Responsive interface.
- Centralized configuration.
- SQLite/SQLAlchemy integration.
- Existing automated test suite, reported as 22 passing tests.

## Remaining

- Academic calendar PDF upload and secure storage.
- PDF text extraction.
- Holiday/vacation date detection.
- Holiday review and correction.
- Academic calendar and holiday database models.
- Holiday-based journey planning.
- Google OAuth connection.
- Google Calendar API integration.
- Event creation and notification configuration.
- Duplicate prevention and event updates/deletion.
- Sync status and retry handling.
- Regression tests and new end-to-end tests.
- README/configuration/security documentation for the new features.

**Overall conclusion:** The existing manual journey and booking-date website is reported as working. The distinctive automation that connects academic holidays to expected train-booking dates and Google Calendar is the principal remaining development milestone.

The implementation agent must inspect the current repository and verify these statuses before modifying code. It must preserve working features, implement the missing workflow incrementally, run tests, and report only results it has actually verified.
