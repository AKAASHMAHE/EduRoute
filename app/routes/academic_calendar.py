import os
from datetime import datetime, date
from pathlib import Path
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from app.models import db, AcademicCalendar, Holiday
from app.utils.file_validators import validate_pdf_upload, save_secure_pdf
from app.services.pdf_extraction_service import extract_pdf_text
from app.services.holiday_extraction_service import process_academic_calendar_holidays

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/academic-calendars", methods=["GET"])
def list_calendars():
    """Display all uploaded academic calendars."""
    calendars = AcademicCalendar.query.order_by(AcademicCalendar.created_at.desc()).all()
    return render_template("academic_calendars.html", calendars=calendars)


@calendar_bp.route("/academic-calendars/upload", methods=["GET", "POST"])
def upload_calendar():
    """Upload and process a new academic calendar PDF."""
    if request.method == "POST":
        file = request.files.get("calendar_file")
        calendar_label = request.form.get("calendar_label", "").strip()

        if not calendar_label:
            calendar_label = f"Academic Calendar {date.today().year}"

        max_size = current_app.config.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
        is_valid, error_msg = validate_pdf_upload(file, max_size)

        if not is_valid:
            flash(error_msg, "danger")
            return render_template("upload_calendar.html", calendar_label=calendar_label)

        upload_dir = current_app.config.get(
            "ACADEMIC_CALENDAR_UPLOAD_DIR",
            str(Path(current_app.instance_path) / "uploads" / "academic_calendars"),
        )

        orig_name, stored_name, stored_path = save_secure_pdf(file, upload_dir)

        # Create calendar record
        calendar = AcademicCalendar(
            filename=orig_name,
            stored_filename=stored_name,
            calendar_label=calendar_label,
            status="PROCESSING",
        )
        db.session.add(calendar)
        db.session.commit()

        # Extract text
        success, extracted_text, extract_err = extract_pdf_text(stored_path)

        if not success:
            calendar.status = "FAILED"
            calendar.error_message = extract_err
            db.session.commit()
            flash(f"Upload saved, but text extraction failed: {extract_err}", "warning")
            return redirect(url_for("calendar.list_calendars"))

        # Process holidays from extracted text
        new_count, total_count = process_academic_calendar_holidays(calendar.id, extracted_text)

        flash(
            f"Calendar '{calendar_label}' processed successfully! Detected {total_count} candidate holidays.",
            "success",
        )
        return redirect(url_for("calendar.review_holidays", calendar_id=calendar.id))

    return render_template("upload_calendar.html", calendar_label="")


@calendar_bp.route("/academic-calendars/<int:calendar_id>", methods=["GET"])
def view_calendar(calendar_id):
    """View details of a specific calendar and its holidays."""
    calendar = db.get_or_404(AcademicCalendar, calendar_id)
    return render_template("calendar_holidays.html", calendar=calendar)


@calendar_bp.route("/academic-calendars/<int:calendar_id>/reprocess", methods=["POST"])
def reprocess_calendar(calendar_id):
    """Reprocess PDF text extraction and holiday detection non-destructively."""
    calendar = db.get_or_404(AcademicCalendar, calendar_id)
    upload_dir = current_app.config.get(
        "ACADEMIC_CALENDAR_UPLOAD_DIR",
        str(Path(current_app.instance_path) / "uploads" / "academic_calendars"),
    )
    file_path = Path(upload_dir) / calendar.stored_filename

    if not file_path.exists():
        flash("Source PDF file not found on disk. Please re-upload.", "danger")
        return redirect(url_for("calendar.list_calendars"))

    calendar.status = "PROCESSING"
    db.session.commit()

    success, extracted_text, extract_err = extract_pdf_text(file_path)

    if not success:
        calendar.status = "FAILED"
        calendar.error_message = extract_err
        db.session.commit()
        flash(f"Reprocessing failed: {extract_err}", "danger")
        return redirect(url_for("calendar.list_calendars"))

    new_count, total_count = process_academic_calendar_holidays(calendar.id, extracted_text)
    flash(
        f"Reprocessed '{calendar.calendar_label}'! {total_count} holidays total (confirmed/rejected preserved).",
        "success",
    )
    return redirect(url_for("calendar.review_holidays", calendar_id=calendar.id))


@calendar_bp.route("/academic-calendars/<int:calendar_id>/delete", methods=["POST"])
def delete_calendar(calendar_id):
    """Delete an academic calendar and unlink/cascade holidays."""
    calendar = db.get_or_404(AcademicCalendar, calendar_id)
    upload_dir = current_app.config.get(
        "ACADEMIC_CALENDAR_UPLOAD_DIR",
        str(Path(current_app.instance_path) / "uploads" / "academic_calendars"),
    )
    file_path = Path(upload_dir) / calendar.stored_filename

    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        current_app.logger.warning(f"Error removing file {file_path}: {e}")

    calendar_label = calendar.calendar_label
    db.session.delete(calendar)
    db.session.commit()

    flash(f"Academic calendar '{calendar_label}' deleted successfully.", "success")
    return redirect(url_for("calendar.list_calendars"))


@calendar_bp.route("/holidays/review", methods=["GET"])
def review_holidays():
    """Interface to review, edit, confirm, or reject candidate holidays."""
    calendar_id = request.args.get("calendar_id", type=int)
    status_filter = request.args.get("status", "all").strip().upper()

    query = Holiday.query
    if calendar_id:
        query = query.filter(Holiday.calendar_id == calendar_id)
    if status_filter != "ALL":
        query = query.filter(Holiday.status == status_filter)

    holidays = query.order_by(Holiday.start_date.asc()).all()
    calendars = AcademicCalendar.query.all()

    return render_template(
        "holiday_review.html",
        holidays=holidays,
        calendars=calendars,
        selected_calendar_id=calendar_id,
        status_filter=status_filter,
    )


@calendar_bp.route("/holidays/<int:holiday_id>/confirm", methods=["POST"])
def confirm_holiday(holiday_id):
    """Mark a candidate holiday as CONFIRMED."""
    holiday = db.get_or_404(Holiday, holiday_id)
    holiday.status = "CONFIRMED"
    db.session.commit()
    flash(f"Holiday '{holiday.name}' confirmed!", "success")
    return redirect(request.referrer or url_for("calendar.review_holidays"))


@calendar_bp.route("/holidays/<int:holiday_id>/reject", methods=["POST"])
def reject_holiday(holiday_id):
    """Mark a candidate holiday as REJECTED."""
    holiday = db.get_or_404(Holiday, holiday_id)
    holiday.status = "REJECTED"
    db.session.commit()
    flash(f"Holiday '{holiday.name}' marked as rejected.", "info")
    return redirect(request.referrer or url_for("calendar.review_holidays"))


@calendar_bp.route("/holidays/<int:holiday_id>/edit", methods=["POST"])
def edit_holiday(holiday_id):
    """Update holiday name and date range, then mark confirmed."""
    holiday = db.get_or_404(Holiday, holiday_id)
    name = request.form.get("name", "").strip()
    start_date_str = request.form.get("start_date", "").strip()
    end_date_str = request.form.get("end_date", "").strip()

    if not name or not start_date_str:
        flash("Holiday name and start date are required.", "danger")
        return redirect(request.referrer or url_for("calendar.review_holidays"))

    try:
        s_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else s_date
        if e_date < s_date:
            flash("End date cannot be earlier than start date.", "danger")
            return redirect(request.referrer or url_for("calendar.review_holidays"))
    except ValueError:
        flash("Invalid date format provided.", "danger")
        return redirect(request.referrer or url_for("calendar.review_holidays"))

    holiday.name = name
    holiday.start_date = s_date
    holiday.end_date = e_date
    holiday.status = "CONFIRMED"  # User edited and approved
    db.session.commit()

    flash(f"Holiday '{holiday.name}' updated and confirmed!", "success")
    return redirect(request.referrer or url_for("calendar.review_holidays"))


@calendar_bp.route("/holidays/bulk-confirm", methods=["POST"])
def bulk_confirm_holidays():
    """Bulk confirm multiple selected candidate holidays."""
    holiday_ids = request.form.getlist("holiday_ids")
    if not holiday_ids:
        flash("No holidays were selected for confirmation.", "warning")
        return redirect(request.referrer or url_for("calendar.review_holidays"))

    confirmed_count = 0
    for h_id in holiday_ids:
        try:
            h = db.session.get(Holiday, int(h_id))
            if h and h.status != "CONFIRMED":
                h.status = "CONFIRMED"
                confirmed_count += 1
        except (ValueError, TypeError):
            continue

    db.session.commit()
    flash(f"Successfully confirmed {confirmed_count} holidays!", "success")
    return redirect(request.referrer or url_for("calendar.review_holidays"))


@calendar_bp.route("/holidays/<int:holiday_id>/delete", methods=["POST"])
def delete_holiday(holiday_id):
    """Delete a holiday record permanently."""
    holiday = db.get_or_404(Holiday, holiday_id)
    name = holiday.name
    db.session.delete(holiday)
    db.session.commit()
    flash(f"Holiday '{name}' deleted.", "info")
    return redirect(request.referrer or url_for("calendar.review_holidays"))
