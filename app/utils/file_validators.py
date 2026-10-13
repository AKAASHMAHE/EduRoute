import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename

PDF_MAGIC_BYTES = b"%PDF-"


def validate_pdf_upload(file_storage, max_size_bytes=10 * 1024 * 1024):
    """
    Validate an uploaded file for PDF security:
    1. Checks filename and extension
    2. Checks magic bytes signature (%PDF-)
    3. Enforces maximum content length
    
    Returns:
        (is_valid: bool, error_message: str or None)
    """
    if not file_storage or not file_storage.filename or file_storage.filename.strip() == "":
        return False, "No file selected for upload."

    original_filename = file_storage.filename.strip()
    ext = Path(original_filename).suffix.lower()
    if ext != ".pdf":
        return False, "Invalid file format. Only PDF (.pdf) documents are accepted."

    # Inspect file size using stream position if available
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    if size == 0:
        return False, "The uploaded PDF file is empty (0 bytes)."

    if size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        return False, f"File size exceeds the maximum allowed limit of {max_mb:.0f} MB."

    # Validate PDF signature magic bytes
    header = file_storage.read(5)
    file_storage.seek(0)
    if not header.startswith(PDF_MAGIC_BYTES):
        return False, "File is not a valid PDF document (missing %PDF signature header)."

    return True, None


def save_secure_pdf(file_storage, destination_dir):
    """
    Save the uploaded PDF to a secure storage location outside static/.
    Uses an unguessable UUID filename to prevent collision and directory traversal.
    
    Returns:
        (original_filename: str, stored_filename: str, absolute_filepath: Path)
    """
    original_filename = secure_filename(file_storage.filename) or "calendar.pdf"
    unique_key = f"{uuid.uuid4().hex}.pdf"
    dest_path = Path(destination_dir)
    dest_path.mkdir(parents=True, exist_ok=True)

    target_file = dest_path / unique_key
    file_storage.seek(0)
    file_storage.save(target_file)

    return original_filename, unique_key, target_file
