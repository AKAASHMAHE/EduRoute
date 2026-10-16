import os
from datetime import datetime, timezone
import pytest

# Ensure the config uses the default timezone (Asia/Kolkata)

def test_utc_to_local_conversion(monkeypatch):
    # Import after setting env var if needed
    from app.utils.helpers import utc_to_local
    # Create a UTC datetime
    utc_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    # Expected Kolkata time: 05:30 AM
    result = utc_to_local(utc_dt)
    assert result == "01 Jan 2026, 05:30 AM"
