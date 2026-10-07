from datetime import date, datetime


def validate_journey_input(data, is_edit=False, existing_journey_date=None):
    """
    Validate user form data for adding or editing a train journey.
    
    Returns:
        (is_valid: bool, errors: dict)
    """
    errors = {}

    # 1. Trip Name
    trip_name = data.get("trip_name", "").strip() if data.get("trip_name") else ""
    if not trip_name:
        errors["trip_name"] = "Trip name is required."
    elif len(trip_name) > 120:
        errors["trip_name"] = "Trip name cannot exceed 120 characters."

    # 2. Source
    source = data.get("source", "").strip() if data.get("source") else ""
    if not source:
        errors["source"] = "Source location is required."
    elif len(source) > 100:
        errors["source"] = "Source location cannot exceed 100 characters."

    # 3. Destination
    destination = data.get("destination", "").strip() if data.get("destination") else ""
    if not destination:
        errors["destination"] = "Destination location is required."
    elif len(destination) > 100:
        errors["destination"] = "Destination location cannot exceed 100 characters."

    # 4. Source & Destination comparison
    if source and destination and source.lower() == destination.lower():
        errors["destination"] = "Source and destination cannot be the same station."

    # 5. Train Name (Optional)
    train_name = data.get("train_name", "").strip() if data.get("train_name") else ""
    if train_name and len(train_name) > 120:
        errors["train_name"] = "Train name/number cannot exceed 120 characters."

    # 6. Journey Date
    raw_date = data.get("journey_date", "").strip() if data.get("journey_date") else ""
    if not raw_date:
        errors["journey_date"] = "Journey date is required."
    else:
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            today = date.today()
            # If not edit or changing date, check if in past
            if parsed_date < today:
                if not is_edit or (existing_journey_date and parsed_date != existing_journey_date):
                    errors["journey_date"] = "Journey date cannot be in the past."
        except ValueError:
            errors["journey_date"] = "Invalid date format. Use YYYY-MM-DD."

    is_valid = len(errors) == 0
    return is_valid, errors
