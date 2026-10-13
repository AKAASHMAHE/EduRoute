import io
import tempfile
from pathlib import Path
from datetime import date
from werkzeug.datastructures import FileStorage
from config import Config
from app import create_app
from app.models import db, AcademicCalendar, Holiday
from app.utils.file_validators import validate_pdf_upload, save_secure_pdf
from app.services.pdf_extraction_service import extract_pdf_text
from app.services.holiday_extraction_service import (
    parse_candidate_holidays_from_text,
    process_academic_calendar_holidays,
)


def create_minimal_pdf_bytes(text_content=""):
    """Generate a minimal valid digital PDF byte string with optional text."""
    stream_content = f"BT /F1 12 Tf 50 700 Td ({text_content}) Tj ET".encode("utf-8")
    stream_len = len(stream_content)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
        b"4 0 obj << /Length " + str(stream_len).encode("utf-8") + b" >>\nstream\n"
        + stream_content +
        b"\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000115 00000 n \n0000000280 00000 n \n"
        b"trailer << /Size 5 /Root 1 0 R >>\nstartxref\n380\n%%EOF\n"
    )
    return pdf


def test_pdf_upload_validators():
    """Test validation for valid, empty, non-pdf, and oversized uploads."""
    # 1. Valid PDF
    valid_bytes = create_minimal_pdf_bytes("Independence Day 15 August 2026")
    fs_valid = FileStorage(stream=io.BytesIO(valid_bytes), filename="calendar.pdf")
    is_valid, err = validate_pdf_upload(fs_valid)
    assert is_valid is True
    assert err is None

    # 2. Non-PDF extension
    fs_txt = FileStorage(stream=io.BytesIO(b"Hello world"), filename="test.txt")
    is_valid, err = validate_pdf_upload(fs_txt)
    assert is_valid is False
    assert "Only PDF" in err

    # 3. Empty file (0 bytes)
    fs_empty = FileStorage(stream=io.BytesIO(b""), filename="empty.pdf")
    is_valid, err = validate_pdf_upload(fs_empty)
    assert is_valid is False
    assert "empty" in err

    # 4. Invalid magic header
    fs_fake = FileStorage(stream=io.BytesIO(b"NOT A REAL PDF CONTENT"), filename="fake.pdf")
    is_valid, err = validate_pdf_upload(fs_fake)
    assert is_valid is False
    assert "%PDF signature" in err

    # 5. Oversized file
    big_bytes = b"%PDF-1.4\n" + (b"A" * 200)
    fs_oversized = FileStorage(stream=io.BytesIO(big_bytes), filename="big.pdf")
    is_valid, err = validate_pdf_upload(fs_oversized, max_size_bytes=100)
    assert is_valid is False
    assert "exceeds" in err


def test_pdf_extraction_service():
    """Test PDF text extraction including corrupt, scanned, and digital PDFs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Valid digital PDF
        valid_pdf_path = tmp_path / "valid.pdf"
        valid_pdf_path.write_bytes(create_minimal_pdf_bytes("Independence Day 15 August 2026"))
        success, text, err = extract_pdf_text(valid_pdf_path)
        assert success is True
        assert "Independence Day 15 August 2026" in text

        # 2. Corrupt PDF
        corrupt_path = tmp_path / "corrupt.pdf"
        corrupt_path.write_bytes(b"%PDF-1.4 corrupted incomplete stream without proper structure")
        success, text, err = extract_pdf_text(corrupt_path)
        assert success is False or len(text) == 0

        # 3. Scanned / image-only PDF (no text streams)
        scanned_pdf_path = tmp_path / "scanned.pdf"
        scanned_pdf_path.write_bytes(create_minimal_pdf_bytes(""))  # 0 text
        success, text, err = extract_pdf_text(scanned_pdf_path)
        assert success is False
        assert "scanned" in err.lower() or "no extractable" in err.lower()


def test_holiday_pattern_extractions():
    """Test extracting holidays with various date formats and ranges."""
    sample_text = """
    Academic Calendar 2026-2027
    Independence Day: 15 August 2026
    Gandhi Jayanti: 02-10-2026
    Diwali Break: 10-14 Oct 2026
    Winter Vacation: 24 Dec 2026 - 2 Jan 2027
    Pongal Holiday: 14/01/2027 to 16/01/2027
    Republic Day: 26 Jan
    """

    candidates = parse_candidate_holidays_from_text(sample_text, calendar_label="Academic Calendar 2026-2027")
    names = [c["name"].lower() for c in candidates]

    # Verify key holidays detected
    assert any("independence" in n for n in names)
    assert any("gandhi" in n for n in names)
    assert any("diwali" in n for n in names)
    assert any("winter" in n for n in names)
    assert any("pongal" in n for n in names)
    assert any("republic" in n for n in names)

    # Check multi-day range parsed properly
    diwali = next(c for c in candidates if "diwali" in c["name"].lower())
    assert diwali["start_date"] == date(2026, 10, 10)
    assert diwali["end_date"] == date(2026, 10, 14)


def test_calendar_and_holiday_routes_workflow():
    """Test end-to-end web workflow: upload -> list -> review -> confirm -> edit -> reprocess."""
    class CalTestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        WTF_CSRF_ENABLED = False

    app = create_app(CalTestConfig)
    with app.test_client() as client:
        with app.app_context():
            # 1. Upload Calendar
            pdf_bytes = create_minimal_pdf_bytes("Diwali Vacation: 10-14 Oct 2026\nChristmas Break: 25 Dec 2026")
            res_upload = client.post(
                "/academic-calendars/upload",
                data={
                    "calendar_label": "Engineering Calendar 2026",
                    "calendar_file": (io.BytesIO(pdf_bytes), "academic_2026.pdf"),
                },
                follow_redirects=True,
            )
            assert res_upload.status_code == 200
            assert b"Engineering Calendar 2026" in res_upload.data

            cal = AcademicCalendar.query.first()
            assert cal is not None
            assert cal.holiday_count >= 1

            holidays = Holiday.query.filter_by(calendar_id=cal.id).all()
            assert len(holidays) >= 1
            h1 = holidays[0]
            assert h1.status == "UNCONFIRMED"

            # 2. Confirm a holiday
            res_conf = client.post(f"/holidays/{h1.id}/confirm", follow_redirects=True)
            assert res_conf.status_code == 200
            updated_h1 = db.session.get(Holiday, h1.id)
            assert updated_h1.status == "CONFIRMED"

            # 3. Edit holiday details
            res_edit = client.post(
                f"/holidays/{h1.id}/edit",
                data={
                    "name": "Custom Diwali Holiday",
                    "start_date": "2026-10-10",
                    "end_date": "2026-10-15",
                },
                follow_redirects=True,
            )
            assert res_edit.status_code == 200
            edited_h1 = db.session.get(Holiday, h1.id)
            assert edited_h1.name == "Custom Diwali Holiday"
            assert edited_h1.end_date == date(2026, 10, 15)
            assert edited_h1.status == "CONFIRMED"

            # 4. Non-destructive reprocessing
            process_academic_calendar_holidays(cal.id, "Diwali Vacation: 10-14 Oct 2026\nNew Holiday: 15 Nov 2026")
            # Verified that edited/confirmed holiday still exists
            refetched = db.session.get(Holiday, h1.id)
            assert refetched is not None
            assert refetched.name == "Custom Diwali Holiday"
            assert refetched.status == "CONFIRMED"
