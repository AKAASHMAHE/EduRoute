from datetime import datetime, date
from flask import Blueprint, jsonify, request, current_app
from app.models import Journey, db
from app.services.booking_service import (
    enrich_journey_data,
    calculate_booking_date,
    get_days_until_booking,
    get_days_until_journey,
    get_booking_status,
)
from app.services.reminder_service import is_reminder_active
from app.utils.helpers import filter_and_sort_journeys, get_dashboard_summary_stats

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/journeys", methods=["GET"])
def get_journeys():
    """API Endpoint: Fetch all journeys with filters and calculated metadata."""
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all").strip()
    sort_by = request.args.get("sort", "booking_date").strip()

    journeys_db = Journey.query.all()
    enriched_list = [enrich_journey_data(j) for j in journeys_db]

    # Convert non-serializable objects (datetime/date) for JSON output
    filtered = filter_and_sort_journeys(enriched_list, search_query, status_filter, sort_by)

    clean_output = []
    for item in filtered:
        clean_item = dict(item)
        clean_item.pop("raw_journey", None)
        if isinstance(clean_item.get("journey_date"), (date, datetime)):
            clean_item["journey_date"] = clean_item["journey_date"].isoformat()
        if isinstance(clean_item.get("expected_booking_date"), (date, datetime)):
            clean_item["expected_booking_date"] = clean_item["expected_booking_date"].isoformat()
        clean_output.append(clean_item)

    stats = get_dashboard_summary_stats(enriched_list)

    return jsonify({
        "success": True,
        "count": len(clean_output),
        "stats": stats,
        "journeys": clean_output
    })


@api_bp.route("/journeys/<int:journey_id>", methods=["GET"])
def get_journey(journey_id):
    """API Endpoint: Fetch a single journey details by ID."""
    journey = db.session.get(Journey, journey_id)
    if not journey:
        return jsonify({"success": False, "error": "Journey not found"}), 404

    enriched = enrich_journey_data(journey)
    enriched.pop("raw_journey", None)
    if isinstance(enriched.get("journey_date"), (date, datetime)):
        enriched["journey_date"] = enriched["journey_date"].isoformat()
    if isinstance(enriched.get("expected_booking_date"), (date, datetime)):
        enriched["expected_booking_date"] = enriched["expected_booking_date"].isoformat()

    return jsonify({"success": True, "journey": enriched})


@api_bp.route("/calculate-booking-date", methods=["POST"])
def api_calculate_booking_date():
    """API Endpoint: Calculate expected booking date on the fly for AJAX form updates."""
    data = request.get_json() or {}
    raw_date = data.get("journey_date")

    if not raw_date:
        return jsonify({"success": False, "error": "journey_date is required"}), 400

    try:
        j_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400

    booking_window = current_app.config.get("BOOKING_WINDOW_DAYS", 60)
    expected_booking = calculate_booking_date(j_date, booking_window)
    days_until_b = get_days_until_booking(j_date, booking_window_days=booking_window)
    days_until_j = get_days_until_journey(j_date)
    status_code, status_text, status_class = get_booking_status(j_date, booking_window_days=booking_window)
    reminder_active, reminder_text = is_reminder_active(j_date)

    return jsonify({
        "success": True,
        "journey_date": j_date.isoformat(),
        "expected_booking_date": expected_booking.isoformat(),
        "expected_booking_date_formatted": expected_booking.strftime("%d %B %Y"),
        "days_until_booking": days_until_b,
        "days_until_journey": days_until_j,
        "status_code": status_code,
        "status_text": status_text,
        "status_class": status_class,
        "reminder_active": reminder_active,
        "reminder_text": reminder_text,
        "booking_window_days": booking_window
    })
