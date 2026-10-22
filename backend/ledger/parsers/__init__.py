from . import halyk, kaspi
from .base import (
    ParsedRow,
    ParsedStatement,
    PeriodNotFound,
    StatementError,
    UnsupportedLayout,
)
from .pdf import pdf_to_lines

PARSERS = {"kaspi": kaspi, "halyk": halyk}


def parse_lines(lines):
    """Pick the parser from the statement text and parse it."""
    text = "\n".join(lines)
    for module in PARSERS.values():
        if module.matches(text):
            return module.parse(lines)
    raise UnsupportedLayout(
        "This file doesn't look like a Kaspi Gold or Halyk card statement. "
        "Download the PDF statement from the bank app and try again."
    )


def parse_pdf(fileobj):
    return parse_lines(pdf_to_lines(fileobj))


__all__ = [
    "ParsedRow",
    "ParsedStatement",
    "PeriodNotFound",
    "StatementError",
    "UnsupportedLayout",
    "parse_lines",
    "parse_pdf",
]
