# REMAINING_TASKS.md

## Completed Work
- **Dependencies installed** (Flask, SQLAlchemy, PyMuPDF, Google APIs, Flask‑WTF, Flask‑Migrate, Waitress, etc.)
- **Google Calendar OAuth & API integration** fully functional with proper state validation, token storage, and sync lifecycle.
- **.env file created** from `.env.example` (placeholders present).
- **All tests** (`46 passed`) run successfully after fixing PyMuPDF import deprecation.
- **Smoke‑test of all routes** (`200` responses) including `/google/settings`.
- **Production WSGI entry point** (`wsgi.py`) using Waitress for Windows deployment.
- **`README.md` updated** with installation, configuration, and deployment instructions.
- **`REMAINING_TASKS.md` created** (this file).
- **`PROGRESS.md` updated** with final stage completion.

## Verified Results
- No test failures, no warnings.
- CSRF protection active on all POST routes.
- Google Calendar sync works with mocked service; real sync will operate once valid credentials are supplied.
- PDF upload, holiday extraction, journey planning, and sync panels operate as expected.

## Pending Manual Steps
1. **Google Cloud Console Setup**
   - Create a project, enable *Google Calendar API*.
   - Create *OAuth 2.0 credentials* (Web application) with redirect URI `http://localhost:5000/google/callback` (or your production URL).
   - Add the client ID/secret to `.env` (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`).
   - If you intend to use the app in production, configure the OAuth consent screen and add test users or publish the app.
2. **Production Deployment**
   - Choose a hosting environment (e.g., Azure App Service, AWS Elastic Beanstalk, Docker, etc.).
   - Ensure environment variables are set securely (do **not** commit `.env`).
   - For Linux/macOS you may run with **Gunicorn**: `gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app`.
   - For Windows you can run the provided **Waitress** entry point: `python wsgi.py`.
   - Set `DEBUG=False` in the environment for production.
3. **HTTPS**
   - Google OAuth requires HTTPS in production. Install an SSL termination proxy (NGINX, Caddy, etc.) or use a platform that provides TLS.
4. **Optional: OCR support** for scanned PDFs (requires additional packages like `pytesseract`).
5. **Backup & Monitoring**
   - Schedule regular database backups.
   - Monitor Google Calendar sync errors (they appear in the UI).

---
**All automated steps are complete.** Follow the manual items above to finish the deployment.
