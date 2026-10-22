import io

import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError

from .base import StatementError

MAX_PAGES = 30


def pdf_to_lines(fileobj):
    """Read an uploaded PDF from memory and return its text lines.

    The bytes stay in this process: nothing is written to disk or the database.
    """
    data = fileobj.read() if hasattr(fileobj, "read") else bytes(fileobj)
    if not data.startswith(b"%PDF"):
        raise StatementError("Upload the statement as a PDF file.", code="not_pdf")
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            if len(pdf.pages) > MAX_PAGES:
                raise StatementError(
                    "This statement is too long. Download one month at a time.",
                    code="too_long",
                )
            lines = []
            for page in pdf.pages:
                lines.extend((page.extract_text() or "").splitlines())
            return lines
    except (PDFSyntaxError, ValueError) as exc:
        raise StatementError(
            "This PDF could not be read.", code="unreadable_pdf"
        ) from exc
