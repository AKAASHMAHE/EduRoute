from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.models import db, Journey
from app.services.booking_service import enrich_journey_data, calculate_booking_date
from app.utils.validators import validate_journey_input
from app.utils.helpers import filter_and_sort_journeys, get_dashboard_summary_stats

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing page introducing the Train Booking Date Reminder System."""
    booking_window = current_app.config.get("BOOKING_WINDOW_DAYS", 60)
    return render_template("index.html", booking_window=booking_window)


@main_bp.route("/dashboard")
def dashboard():
    """Dashboard displaying all saved journeys with stats, search, filter, and sorting."""
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all").strip()
    sort_by = request.args.get("sort", "booking_date").strip()

    # Fetch raw journeys from database
    journeys_db = Journey.query.all()

    # Enrich each journey with calculated booking and reminder data
    enriched_list = [enrich_journey_data(j) for j in journeys_db]

    # Compute aggregate stats using pandas/numpy helpers
    stats = get_dashboard_summary_stats(enriched_list)

    # Filter and sort journeys
    filtered_journeys = filter_and_sort_journeys(
        enriched_list,
        search_query=search_query,
        status_filter=status_filter,
        sort_by=sort_by,
    )

    booking_window = current_app.config.get("BOOKING_WINDOW_DAYS", 60)

    return render_template(
        "dashboard.html",
        journeys=filtered_journeys,
        stats=stats,
        search_query=search_query,
        status_filter=status_filter,
        sort_by=sort_by,
        booking_window=booking_window,
    )


@main_bp.route("/journey/add", methods=["GET", "POST"])
def add_journey():
    """Add a new train journey."""
    booking_window = current_app.config.get("BOOKING_WINDOW_DAYS", 60)

    if request.method == "POST":
        form_data = request.form.to_dict()
        reminder_enabled = True if request.form.get("reminder_enabled") in ["on", "true", "1", "True"] else False
        form_data["reminder_enabled"] = reminder_enabled

        is_valid, errors = validate_journey_input(form_data)

        if not is_valid:
            flash("Please correct the errors in the form.", "danger")
            return render_template(
                "add_journey.html",
                errors=errors,
                form_data=form_data,
                booking_window=booking_window,
            )

        # Parse date and create Journey model
        journey_date_obj = datetime.strptime(form_data["journey_date"], "%Y-%m-%d").date()

        new_journey = Journey(
            trip_name=form_data["trip_name"].strip(),
            source=form_data["source"].strip(),
            destination=form_data["destination"].strip(),
            train_name=form_data.get("train_name", "").strip() or None,
            journey_date=journey_date_obj,
            reminder_enabled=reminder_enabled,
        )

        db.session.add(new_journey)
        db.session.commit()

        expected_date = calculate_booking_date(journey_date_obj, booking_window)
        flash(
            f"Journey '{new_journey.trip_name}' added successfully! Expected booking date: {expected_date.strftime('%d %b %Y')}",
            "success",
        )
        return redirect(url_for("main.dashboard"))

    return render_template("add_journey.html", errors={}, form_data={}, booking_window=booking_window)


@main_bp.route("/journey/<int:journey_id>")
def journey_detail(journey_id):
    """View detailed information about a specific journey."""
    journey = db.get_or_404(Journey, journey_id)
    enriched = enrich_journey_data(journey)
    booking_window = current_app.config.get("BOOKING_WINDOW_DAYS", 60)
    return render_template("journey_detail.html", journey=enriched, booking_window=booking_window)


@main_bp.route("/journey/<int:journey_id>/edit", methods=["GET", "POST"])
def edit_journey(journey_id):
    """Edit an existing journey."""
    journey = db.get_or_404(Journey, journey_id)
    booking_window = current_app.config.get("BOOKING_WINDOW_DAYS", 60)

    if request.method == "POST":
        form_data = request.form.to_dict()
        reminder_enabled = True if request.form.get("reminder_enabled") in ["on", "true", "1", "True"] else False
        form_data["reminder_enabled"] = reminder_enabled

        is_valid, errors = validate_journey_input(
            form_data,
            is_edit=True,
            existing_journey_date=journey.journey_date,
        )

        if not is_valid:
            flash("Please correct the errors in the form.", "danger")
            return render_template(
                "edit_journey.html",
                journey=journey,
                errors=errors,
                form_data=form_data,
                booking_window=booking_window,
            )

        journey_date_obj = datetime.strptime(form_data["journey_date"], "%Y-%m-%d").date()

        journey.trip_name = form_data["trip_name"].strip()
        journey.source = form_data["source"].strip()
        journey.destination = form_data["destination"].strip()
        journey.train_name = form_data.get("train_name", "").strip() or None
        journey.journey_date = journey_date_obj
        journey.reminder_enabled = reminder_enabled
        journey.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        flash(f"Journey '{journey.trip_name}' updated successfully!", "success")
        return redirect(url_for("main.journey_detail", journey_id=journey.id))

    # Pre-populate form data for GET request
    form_data = {
        "trip_name": journey.trip_name,
        "source": journey.source,
        "destination": journey.destination,
        "train_name": journey.train_name or "",
        "journey_date": journey.journey_date.strftime("%Y-%m-%d"),
        "reminder_enabled": journey.reminder_enabled,
    }

    return render_template(
        "edit_journey.html",
        journey=journey,
        errors={},
        form_data=form_data,
        booking_window=booking_window,
    )


@main_bp.route("/journey/<int:journey_id>/delete", methods=["POST"])
def delete_journey(journey_id):
    """Delete a journey. Requires POST method for security."""
    journey = db.get_or_404(Journey, journey_id)
    trip_name = journey.trip_name
    db.session.delete(journey)
    db.session.commit()

    flash(f"Journey '{trip_name}' deleted successfully.", "success")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/journey/<int:journey_id>/toggle-reminder", methods=["POST"])
def toggle_reminder(journey_id):
    """Toggle reminder enabled/disabled for a journey."""
    journey = db.get_or_404(Journey, journey_id)
    journey.reminder_enabled = not journey.reminder_enabled
    journey.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    status_str = "enabled" if journey.reminder_enabled else "disabled"
    flash(f"Reminder for '{journey.trip_name}' has been {status_str}.", "info")
    return redirect(request.referrer or url_for("main.dashboard"))
