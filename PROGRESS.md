Stage: STAGE 1 - BASELINE + AUDIT
Result: Completed baseline audit; 22/22 tests passed; AUDIT_REPORT.md saved with 5 items flagged (CSRF missing, debug default, API test gaps, deprecations).
Next: STAGE 2 - FIX (implement CSRF protection, fix debug default, resolve deprecation warnings, add tests for uncovered routes/APIs).

Stage: STAGE 2 - FIX
Result: Fixed all FAIL/PARTIAL issues (CSRFProtect utility added and enforced, DEBUG default False, UTC datetime deprecations resolved, 400 template added); test suite expanded to 27/27 passing (0 warnings).
Next: STAGE 3 - FOUNDATION (Sections 14, 15: schema extensions, models for AcademicCalendar, Holiday, GoogleCalendarConnection, CalendarEventSync, Journey->Holiday link, real migration tool, config settings).

Stage: STAGE 3 - FOUNDATION
Result: Added all Stage 3 models (AcademicCalendar, Holiday, GoogleCalendarConnection, CalendarEventSync, Journey link), non-destructive migration runner, config & env extensions, requirements; 29/29 tests pass.
Next: STAGE 4 - PDF UPLOAD + HOLIDAY EXTRACTION + REVIEW (Sections 7, 8: PDF upload validation with %PDF signature, text extraction, multi-format holiday detection, UNCONFIRMED review UI with bulk confirm/reject/edit, tests with synthetic fixtures).

Stage: STAGE 4 - PDF UPLOAD + HOLIDAY EXTRACTION + REVIEW
Result: Built PDF upload with %PDF signature and size checks, text extraction with PyMuPDF/fallback, multi-format holiday detection, review/edit/bulk confirm UI, and non-destructive reprocessing; 33/33 tests pass.
Next: STAGE 5 - HOLIDAY-BASED JOURNEY PLANNING (Section 9: List confirmed holidays, travel date picker inside range, trip details form with live preview, reject unconfirmed/duplicates, link Journey to Holiday).
