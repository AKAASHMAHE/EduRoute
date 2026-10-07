from datetime import date, datetime
import pandas as pd
import numpy as np


def format_date_human(d):
    """Format a date object or ISO string into human readable format (e.g. 15 Oct 2026)."""
    if not d:
        return ""
    if isinstance(d, str):
        try:
            d = datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            return d
    if isinstance(d, (date, datetime)):
        return d.strftime("%d %b %Y")
    return str(d)


def filter_and_sort_journeys(enriched_journeys, search_query=None, status_filter=None, sort_by="booking_date"):
    """
    Filter and sort list of enriched journey dictionaries using pandas for clean data processing.
    
    Parameters:
        enriched_journeys (list): List of enriched journey dictionaries.
        search_query (str): Substring to search in trip_name, source, destination, or train_name.
        status_filter (str): Filter by status_code or category ('upcoming', 'passed', 'completed', 'active_reminder').
        sort_by (str): Sort option ('booking_date', 'journey_date', 'trip_name', 'created_at').
        
    Returns:
        list: Filtered and sorted list of enriched journey dicts.
    """
    if not enriched_journeys:
        return []

    # Convert to pandas DataFrame for robust processing
    df = pd.DataFrame(enriched_journeys)

    # 1. Search Query Filter
    if search_query and search_query.strip():
        q = search_query.strip().lower()
        mask = (
            df["trip_name"].astype(str).str.lower().str.contains(q)
            | df["source"].astype(str).str.lower().str.contains(q)
            | df["destination"].astype(str).str.lower().str.contains(q)
            | df["train_name"].fillna("").astype(str).str.lower().str.contains(q)
        )
        df = df[mask]

    if df.empty:
        return []

    # 2. Status Filter
    if status_filter and status_filter != "all":
        sf = status_filter.lower()
        if sf == "upcoming":
            df = df[df["status_code"].isin(["UPCOMING", "BOOKING_SOON", "BOOKING_TOMORROW", "BOOKING_TODAY"])]
        elif sf == "passed":
            df = df[df["status_code"] == "BOOKING_DATE_PASSED"]
        elif sf == "completed":
            df = df[df["status_code"] == "JOURNEY_COMPLETED"]
        elif sf == "reminder":
            df = df[df["reminder_active"] == True]
        elif sf in df["status_code"].str.lower().values:
            df = df[df["status_code"].str.lower() == sf]

    if df.empty:
        return []

    # 3. Sorting using pandas/numpy
    if sort_by == "booking_date":
        df = df.sort_values(by="expected_booking_date", ascending=True)
    elif sort_by == "journey_date":
        df = df.sort_values(by="journey_date", ascending=True)
    elif sort_by == "trip_name":
        df = df.sort_values(by="trip_name", ascending=True)
    elif sort_by == "days_remaining":
        df = df.sort_values(by="days_until_booking", ascending=True)
    else:
        df = df.sort_values(by="journey_date", ascending=True)

    return df.to_dict(orient="records")


def get_dashboard_summary_stats(enriched_journeys):
    """
    Calculate summary statistics for dashboard metrics using pandas/numpy.
    """
    if not enriched_journeys:
        return {
            "total_journeys": 0,
            "active_reminders": 0,
            "booking_today": 0,
            "booking_soon": 0,
            "completed": 0,
        }

    df = pd.DataFrame(enriched_journeys)
    
    total = len(df)
    active_reminders = int(np.sum(df["reminder_active"].values)) if "reminder_active" in df.columns else 0
    booking_today = int(np.sum((df["status_code"] == "BOOKING_TODAY").values)) if "status_code" in df.columns else 0
    booking_soon = int(np.sum(df["status_code"].isin(["BOOKING_TOMORROW", "BOOKING_SOON"]).values)) if "status_code" in df.columns else 0
    completed = int(np.sum((df["status_code"] == "JOURNEY_COMPLETED").values)) if "status_code" in df.columns else 0

    return {
        "total_journeys": total,
        "active_reminders": active_reminders,
        "booking_today": booking_today,
        "booking_soon": booking_soon,
        "completed": completed,
    }
