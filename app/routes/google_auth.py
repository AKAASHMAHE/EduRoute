import secrets
import json
import logging
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
    abort,
)
from app.models import db, GoogleCalendarConnection, CalendarEventSync, Journey
from app.services.google_calendar_service import (
    is_google_connected,
    get_calendar_connection,
    get_oauth_authorization_url,
    save_oauth_credentials,
    disconnect_google_calendar,
    sync_journey_to_calendar,
    CALENDAR_SCOPES,
)

logger = logging.getLogger(__name__)
google_bp = Blueprint("google", __name__, url_prefix="/google")


@google_bp.route("/settings", methods=["GET"])
def settings():
    """Display Google Calendar integration status, account details, and sync summary."""
    conn = get_calendar_connection()
    connected = is_google_connected()

    # Sync statistics
    total_journeys = Journey.query.count()
    synced_count = CalendarEventSync.query.filter_by(status=CalendarEventSync.STATUS_SYNCED).count()
    failed_count = CalendarEventSync.query.filter_by(status=CalendarEventSync.STATUS_SYNC_FAILED).count()
    missing_count = CalendarEventSync.query.filter_by(status=CalendarEventSync.STATUS_EXTERNAL_EVENT_MISSING).count()
    reauth_count = CalendarEventSync.query.filter_by(status=CalendarEventSync.STATUS_REAUTH_REQUIRED).count()
    not_synced_count = total_journeys - synced_count

    stats = {
        "total": total_journeys,
        "synced": synced_count,
        "failed": failed_count,
        "missing": missing_count,
        "reauth": reauth_count,
        "not_synced": max(0, not_synced_count),
    }

    timezone_setting = current_app.config.get("CALENDAR_EVENT_TIMEZONE", "Asia/Kolkata")
    event_hour = current_app.config.get("CALENDAR_EVENT_HOUR", 9)
    calendar_id = current_app.config.get("GOOGLE_CALENDAR_ID", "primary")

    has_client_secrets = bool(
        current_app.config.get("GOOGLE_CLIENT_ID") and current_app.config.get("GOOGLE_CLIENT_SECRET")
    )

    return render_template(
        "google_settings.html",
        connected=connected,
        connection=conn,
        stats=stats,
        timezone=timezone_setting,
        event_hour=event_hour,
        calendar_id=calendar_id,
        has_client_secrets=has_client_secrets,
    )


@google_bp.route("/connect", methods=["GET"])
def connect():
    """Initiate Google OAuth 2.0 authorization redirect."""
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        flash(
            "Google OAuth credentials are not configured. Please set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET in your .env file or environment variables.",
            "warning",
        )
        return redirect(url_for("google.settings"))

    redirect_uri = current_app.config.get(
        "GOOGLE_REDIRECT_URI",
        url_for("google.callback", _external=True),
    )

    # Cryptographic state parameter to prevent CSRF in OAuth callback
    state = secrets.token_hex(16)
    session["_google_oauth_state"] = state

    auth_url, err = get_oauth_authorization_url(redirect_uri, state)
    if err:
        flash(err, "danger")
        return redirect(url_for("google.settings"))

    return redirect(auth_url)


@google_bp.route("/callback", methods=["GET"])
def callback():
    """Handle callback from Google OAuth redirect."""
    expected_state = session.pop("_google_oauth_state", None)
    received_state = request.args.get("state")

    if not expected_state or not received_state or expected_state != received_state:
        abort(400, description="Invalid or expired OAuth state parameter (potential CSRF).")

    error_param = request.args.get("error")
    if error_param:
        flash(f"Google authorization was cancelled or failed: {error_param}", "warning")
        return redirect(url_for("google.settings"))

    code = request.args.get("code")
    if not code:
        flash("Authorization code missing from Google response.", "danger")
        return redirect(url_for("google.settings"))

    # For testing: check if mock credentials exchange handler is provided
    mock_exchange = current_app.config.get("MOCK_OAUTH_EXCHANGE")
    if mock_exchange:
        creds_data = mock_exchange(code)
    else:
        try:
            from google_auth_oauthlib.flow import Flow

            redirect_uri = current_app.config.get(
                "GOOGLE_REDIRECT_URI",
                url_for("google.callback", _external=True),
            )

            client_config = {
                "web": {
                    "client_id": current_app.config.get("GOOGLE_CLIENT_ID"),
                    "client_secret": current_app.config.get("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }

            flow = Flow.from_client_config(
                client_config,
                scopes=CALENDAR_SCOPES,
                redirect_uri=redirect_uri,
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials
            creds_data = json.loads(credentials.to_json())
        except Exception as e:
            logger.error(f"Failed to exchange Google OAuth code: {e}")
            flash(f"Could not complete Google authorization: {str(e)[:150]}", "danger")
            return redirect(url_for("google.settings"))

    save_oauth_credentials(creds_data, user_email="google_user")
    flash("Successfully connected to Google Calendar!", "success")
    return redirect(url_for("google.settings"))


@google_bp.route("/disconnect", methods=["POST"])
def disconnect():
    """Disconnect Google Calendar integration."""
    disconnect_google_calendar()
    flash(
        "Google Calendar integration disconnected. Existing events in your Google Calendar have been preserved.",
        "info",
    )
    return redirect(url_for("google.settings"))


@google_bp.route("/journey/<int:journey_id>/sync", methods=["POST"])
def sync_journey(journey_id):
    """Sync or retry synchronizing a specific journey to Google Calendar."""
    success, status, msg = sync_journey_to_calendar(journey_id)
    flash(msg, "success" if success else "warning")
    return redirect(request.referrer or url_for("main.journey_detail", journey_id=journey_id))
