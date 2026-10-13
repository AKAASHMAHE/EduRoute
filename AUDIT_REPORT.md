# Stage 1 Audit Report: Train Booking Date Reminder System

**Date:** 2026-10-13  
**Auditor:** Senior Flask Engineer  
**Baseline Test Result:** 22/22 PASSED (with 7 `datetime.utcnow()` deprecation warnings)

---

## 1. Audit Verification Matrix

| Checklist Item | Status | Evidence / Observation |
|---|---|---|
| **1. App factory / config / .env** | **PARTIAL** | App factory structure is modular (`create_app`), but `config.py` defaults `DEBUG` to `True` if unset; `.env` is absent by default; `SECRET_KEY` falls back to hardcoded dev string. |
| **2. Journey model** | **PASS** | Complete schema in `Journey` (`id`, `trip_name`, `source`, `destination`, `train_name`, `journey_date`, `reminder_enabled`, timestamps); uses deprecated `datetime.utcnow`. |
| **3. Booking-date calculation edge cases** | **PASS** | Date delta math is exact (`timedelta(days=60)`); leap years (2028-03-01 -> 2028-01-01), month ends, and year boundaries are correctly handled and tested. |
| **4. Journey add/edit/delete + server validation** | **PASS** | `validate_journey_input` validates required fields, lengths, prevents identical source/destination, and disallows past dates on add. |
| **5. Delete & reminder toggle use POST + CSRF** | **FAIL** | Delete and toggle routes use `POST`, but CSRF protection (`Flask-WTF` / `CSRFProtect`) is not installed or configured; forms lack CSRF tokens. |
| **6. Dashboard search/filter/sort** | **PASS** | `filter_and_sort_journeys` implements multi-column search, status filters (upcoming, passed, completed, reminder), and multiple sorting options via pandas. |
| **7. AJAX preview** | **PASS** | `main.js` correctly issues POST requests to `/api/v1/calculate-booking-date` to dynamically render expected booking dates without page reloads. |
| **8. API endpoints** | **PARTIAL** | Endpoints `/api/v1/calculate-booking-date`, `/api/v1/journeys`, `/api/v1/journeys/<id>` exist, but missing tests for GET endpoints and error payloads (missing/invalid date). |
| **9. 404/500 error pages** | **PASS** | Custom templates `404.html` and `500.html` exist with friendly messaging and no raw traceback leakage; 400 handler renders 404 template. |
| **10. No debug exposure in production** | **PARTIAL** | `config.py` sets `DEBUG = os.getenv("DEBUG", "True")...` which enables debug mode if `DEBUG` environment variable is omitted. |
| **11. DB init does not wipe data** | **PASS** | App uses `db.create_all()`, which creates missing tables without dropping existing data. |
| **12. Test quality** | **PARTIAL** | 22 tests pass; gaps exist for API GET endpoints, API bad-input handling, reminder toggle route, and timezone-aware datetime usage. |
| **13. requirements.txt sanity** | **PARTIAL** | Base dependencies are pinned with `>=`; missing `Flask-WTF` (CSRF) and `Flask-Migrate` (database migrations). |

---

## 2. Identified Bugs & Vulnerabilities

1. **[CRITICAL] CSRF Protection Missing:** State-changing routes (`/journey/add`, `/journey/<id>/edit`, `/journey/<id>/delete`, `/journey/<id>/toggle-reminder`) accept POST requests without validating CSRF tokens.
2. **[HIGH] Debug Default in Production:** `config.py` defaults `DEBUG` to `True`, risking debugger exposure if deployed without explicit `DEBUG=False`.
3. **[MEDIUM] Untested API Endpoints & Gaps:** No automated test coverage for `GET /api/v1/journeys`, `GET /api/v1/journeys/<id>` (valid and 404), and `POST /api/v1/calculate-booking-date` bad input handling.
4. **[LOW] Deprecated `datetime.utcnow()`:** `Journey` model and route handlers trigger SQLAlchemy/Python 3.12+ `DeprecationWarning` by using `datetime.utcnow()` instead of timezone-aware UTC datetime.
5. **[LOW] 400 Bad Request Error Handler Misalignment:** `@app.errorhandler(400)` renders `404.html` instead of a 400-specific or standard error message.

---

## 3. Stage 2 Fix Summary & Verification

- **CSRF Protection Implemented:** Built-in modular `CSRFProtect` utility with cryptographic session tokens, injected into all forms/templates (`add_journey`, `edit_journey`, `journey_card`, `journey_detail`, `base.html`), API endpoints properly exempted. Verified via automated test `test_csrf_protection_enforcement`.
- **Debug Flag Fixed:** Changed `config.py` default to `DEBUG = False`.
- **Deprecation Warnings Resolved:** Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)` across `Journey` model and route handlers. Zero warnings reported during pytest.
- **Error Handler Fixed:** Added `400.html` and bound 400 handler to render appropriate bad request template.
- **Test Suite Extended:** Added 5 new tests covering API journeys list & detail, bad calculate inputs, toggle reminder, dashboard search/filter, and CSRF protection. Test count increased from 22 to 27 (100% passing).
