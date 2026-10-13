"""
PDF Text Extraction Service.
Extracts digital text from academic calendar PDFs using PyMuPDF (fitz)
with a built-in fallback parser for resilience across environments.
"""

import os
import re
import zlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_with_pymupdf(filepath):
    """Attempt text extraction via PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None, "PyMuPDF (fitz) is not installed."

    try:
        doc = fitz.open(str(filepath))
        if doc.page_count == 0:
            return False, "", "PDF contains no pages."

        full_text = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text:
                full_text.append(text)
        doc.close()

        extracted = "\n".join(full_text).strip()
        if not extracted or len(extracted) < 15:
            return False, "", "No extractable digital text found. Document may be a scanned image or photo."

        return True, extracted, None
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}")
        return False, "", f"Could not read PDF: {str(e)}"


def extract_text_fallback(filepath):
    """
    Fallback pure-Python PDF stream text extractor.
    Decompresses FlateDecode streams and parses text blocks (BT...ET).
    """
    try:
        with open(filepath, "rb") as f:
            content = f.read()

        if not content.startswith(b"%PDF-"):
            return False, "", "Invalid PDF signature header."

        text_chunks = []

        # Find all streams
        stream_matches = re.finditer(rb"stream[\r\n]+(.*?)[\r\n]+endstream", content, re.DOTALL)
        for match in stream_matches:
            stream_data = match.group(1)
            # Try decompressing with zlib
            decompressed = None
            try:
                decompressed = zlib.decompress(stream_data)
            except Exception:
                decompressed = stream_data  # Uncompressed stream

            if decompressed:
                try:
                    # Extract literal string tokens within Tj, TJ, or quotes
                    # Standard PDF text strings: (Hello World) Tj or [(Hello) -10 (World)] TJ
                    tj_matches = re.findall(rb"\(([^)]+)\)\s*(?:Tj|')", decompressed)
                    for chunk in tj_matches:
                        try:
                            decoded = chunk.decode("utf-8", errors="ignore").strip()
                            if decoded:
                                text_chunks.append(decoded)
                        except Exception:
                            pass

                    # Also handle array text TJ
                    array_matches = re.findall(rb"\[(.*?)\]\s*TJ", decompressed)
                    for arr in array_matches:
                        sub_chunks = re.findall(rb"\(([^)]+)\)", arr)
                        line = "".join(c.decode("utf-8", errors="ignore") for c in sub_chunks).strip()
                        if line:
                            text_chunks.append(line)
                except Exception:
                    pass

        # If no streams yielded text, scan raw ASCII strings in PDF body
        if not text_chunks:
            raw_text_matches = re.findall(rb"\(([^)]{2,})\)", content)
            for m in raw_text_matches:
                try:
                    decoded = m.decode("utf-8", errors="ignore").strip()
                    if len(decoded) > 3 and not decoded.startswith(b"/".decode()):
                        text_chunks.append(decoded)
                except Exception:
                    pass

        extracted = "\n".join(text_chunks).strip()
        if not extracted or len(extracted) < 15:
            return False, "", "No extractable digital text found. Document may be a scanned image or photo."

        return True, extracted, None
    except Exception as e:
        logger.error(f"Fallback extraction failed: {e}")
        return False, "", f"Could not parse PDF content: {str(e)}"


def extract_pdf_text(filepath):
    """
    Primary interface for extracting text from an academic calendar PDF.
    
    Returns:
        (success: bool, text: str, error_message: str or None)
    """
    path = Path(filepath)
    if not path.exists():
        return False, "", "File not found on server storage."

    if path.stat().st_size == 0:
        return False, "", "The PDF file is empty (0 bytes)."

    # Try PyMuPDF first
    try:
        import fitz
        success, text, err = extract_text_with_pymupdf(path)
        if success or err and "scanned" in err.lower():
            return success, text, err
    except ImportError:
        pass

    # Use pure Python stream extractor fallback
    return extract_text_fallback(path)
