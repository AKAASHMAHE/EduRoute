"""
Holiday Extraction Service.
Identifies calendar dates, multi-day ranges, and holiday descriptions
from extracted academic calendar PDF text.
"""

import re
from datetime import date, datetime
from app.models import db, Holiday, AcademicCalendar

MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Common holiday keywords to boost extraction relevance
HOLIDAY_KEYWORDS = [
    "holiday", "vacation", "break", "festival", "diwali", "deepavali", "pongal",
    "ramzan", "eid", "christmas", "new year", "dusserah", "dussehra", "navratri",
    "gandhi", "independence", "republic", "puja", "onam", "good friday",
    "muharram", "mahavir", "buddha", "guru nanak", "holidays", "recess", "leave"
]


def extract_year_from_context(text, fallback_year=None):
    """Attempt to determine the primary academic year from calendar title or context."""
    if fallback_year is None:
        fallback_year = date.today().year

    # Search for 4-digit years like 2025, 2026, 2027
    years = [int(y) for y in re.findall(r"\b(20[2-3][0-9])\b", text)]
    if years:
        # Return most frequent year or first year
        return max(set(years), key=years.count)
    return fallback_year


def parse_single_date(d_str, default_year):
    """Parse various string representations of a single date."""
    d_str = d_str.strip()

    # Pattern: YYYY-MM-DD or YYYY/MM/DD
    m_iso = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", d_str)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        try:
            return date(y, m, d)
        except ValueError:
            return None

    # Pattern: DD-MM-YYYY or DD/MM/YYYY or DD.MM.YYYY
    m_dmy = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", d_str)
    if m_dmy:
        d, m, y = int(m_dmy.group(1)), int(m_dmy.group(2)), int(m_dmy.group(3))
        try:
            return date(y, m, d)
        except ValueError:
            return None

    # Pattern: DD Month YYYY (e.g. 15 August 2026, 15th Aug 2026)
    m_named = re.match(r"^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)(?:\s+(\d{4}))?$", d_str)
    if m_named:
        d = int(m_named.group(1))
        m_name = m_named.group(2).lower()
        y = int(m_named.group(3)) if m_named.group(3) else default_year
        if m_name in MONTH_MAP:
            try:
                return date(y, MONTH_MAP[m_name], d)
            except ValueError:
                return None

    # Pattern: Month DD, YYYY (e.g. August 15, 2026)
    m_us = re.match(r"^([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?$", d_str)
    if m_us:
        m_name = m_us.group(1).lower()
        d = int(m_us.group(2))
        y = int(m_us.group(3)) if m_us.group(3) else default_year
        if m_name in MONTH_MAP:
            try:
                return date(y, MONTH_MAP[m_name], d)
            except ValueError:
                return None

    return None


def clean_holiday_name(name):
    """Clean extracted text to produce a succinct, clean holiday name."""
    if not name:
        return "Academic Holiday"

    # Strip symbols, leading bullets, colons, dashes
    cleaned = re.sub(r"^[\s\-:–—*•\d.]+", "", name)
    cleaned = re.sub(r"[\s\-:–—]+$", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # If too long, truncate safely
    if len(cleaned) > 120:
        cleaned = cleaned[:117] + "..."

    return cleaned if len(cleaned) >= 2 else "Academic Holiday"


def parse_candidate_holidays_from_text(raw_text, calendar_label=""):
    """
    Parse raw extracted text into a structured list of candidate holiday dictionaries:
    [{'name': str, 'start_date': date, 'end_date': date, 'source_text': str, 'category': str}]
    """
    if not raw_text or not raw_text.strip():
        return []

    context_year = extract_year_from_context(calendar_label + " " + raw_text)
    candidates = []
    seen_keys = set()

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Regular expressions for different line formats
    # 1. Date Range: e.g., "10-14 Oct 2026", "10 Oct to 14 Oct 2026", "24 Dec 2026 - 2 Jan 2027", "10/10/2026 - 14/10/2026"
    range_regex = re.compile(
        r"(?:(\d{1,2})(?:st|nd|rd|th)?(?:\s+([A-Za-z]+))?\s*(?:-|to|–|—)\s*(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)(?:\s+(\d{4}))?)|"
        r"(?:(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\s*(?:-|to|–|—)\s*(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}))|"
        r"(?:(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\s*(?:-|to|–|—)\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4}))",
        re.IGNORECASE,
    )

    # 2. Single Date: e.g., "15 August 2026", "15-08-2026", "2026-08-15"
    single_date_regex = re.compile(
        r"(?:(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)(?:\s+(\d{4}))?)|"
        r"(?:([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?)|"
        r"(?:\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b)|"
        r"(?:\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\b)",
        re.IGNORECASE,
    )

    for line in lines:
        if len(line) < 4:
            continue

        # Try Range match first
        range_match = range_regex.search(line)
        if range_match:
            g = range_match.groups()
            s_date = None
            e_date = None

            # Subpattern 1: DD [Month] - DD Month [YYYY]
            if g[0] and g[2] and g[3]:
                start_day = int(g[0])
                start_month_str = (g[1] or g[3]).lower()
                end_day = int(g[2])
                end_month_str = g[3].lower()
                yr = int(g[4]) if g[4] else context_year

                if start_month_str in MONTH_MAP and end_month_str in MONTH_MAP:
                    try:
                        s_date = date(yr, MONTH_MAP[start_month_str], start_day)
                        # Year boundary check (e.g. Dec to Jan)
                        e_yr = yr + 1 if MONTH_MAP[end_month_str] < MONTH_MAP[start_month_str] else yr
                        e_date = date(e_yr, MONTH_MAP[end_month_str], end_day)
                    except ValueError:
                        pass

            # Subpattern 2: YYYY-MM-DD to YYYY-MM-DD
            elif g[5] and g[6]:
                s_date = parse_single_date(g[5], context_year)
                e_date = parse_single_date(g[6], context_year)

            # Subpattern 3: DD-MM-YYYY to DD-MM-YYYY
            elif g[7] and g[8]:
                s_date = parse_single_date(g[7], context_year)
                e_date = parse_single_date(g[8], context_year)

            if s_date and e_date and s_date <= e_date:
                # Name is remaining line text
                name_part = range_regex.sub("", line)
                name = clean_holiday_name(name_part)
                key = (name.lower(), s_date, e_date)
                if key not in seen_keys:
                    seen_keys.add(key)
                    candidates.append({
                        "name": name,
                        "start_date": s_date,
                        "end_date": e_date,
                        "source_text": line,
                        "category": "Vacation / Break",
                    })
                continue

        # Try single date match
        single_match = single_date_regex.search(line)
        if single_match:
            date_str = single_match.group(0)
            parsed_d = parse_single_date(date_str, context_year)

            if parsed_d:
                name_part = single_date_regex.sub("", line)
                name = clean_holiday_name(name_part)

                key = (name.lower(), parsed_d, parsed_d)
                if key not in seen_keys:
                    seen_keys.add(key)
                    candidates.append({
                        "name": name,
                        "start_date": parsed_d,
                        "end_date": parsed_d,
                        "source_text": line,
                        "category": "Public / Academic Holiday",
                    })

    return candidates


def process_academic_calendar_holidays(calendar_id, extracted_text):
    """
    Process extracted text for an AcademicCalendar instance, create Holiday records,
    and preserve any already CONFIRMED or REJECTED holidays upon reprocessing.
    
    Returns:
        (new_count: int, total_count: int)
    """
    calendar = db.session.get(AcademicCalendar, calendar_id)
    if not calendar:
        return 0, 0

    candidates = parse_candidate_holidays_from_text(extracted_text, calendar.calendar_label)

    # Fetch existing non-unconfirmed holidays to preserve user decisions
    preserved_holidays = Holiday.query.filter(
        Holiday.calendar_id == calendar_id,
        Holiday.status.in_(["CONFIRMED", "REJECTED"]),
    ).all()
    preserved_keys = {(h.name.lower(), h.start_date, h.end_date) for h in preserved_holidays}

    # Remove existing UNCONFIRMED candidates for this calendar
    Holiday.query.filter(
        Holiday.calendar_id == calendar_id,
        Holiday.status == "UNCONFIRMED",
    ).delete()

    created_count = 0
    for cand in candidates:
        key = (cand["name"].lower(), cand["start_date"], cand["end_date"])
        if key in preserved_keys:
            continue  # Do not overwrite already confirmed/rejected records

        hol = Holiday(
            calendar_id=calendar.id,
            name=cand["name"],
            start_date=cand["start_date"],
            end_date=cand["end_date"],
            category=cand.get("category", "Holiday"),
            source_text=cand.get("source_text"),
            status="UNCONFIRMED",
        )
        db.session.add(hol)
        created_count += 1

    calendar.holiday_count = len(preserved_holidays) + created_count
    calendar.status = "PROCESSED"
    calendar.error_message = None
    db.session.commit()

    return created_count, calendar.holiday_count
