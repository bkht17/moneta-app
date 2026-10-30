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


SUPPORTED = (
    "Supported: Kaspi Gold and Halyk card PDF statements in Russian, Kazakh or English."
)


def parse_lines(lines):
    """Pick the parser from the statement text and parse it."""
    text = "\n".join(lines)
    for module in PARSERS.values():
        if module.matches(text):
            return module.parse(lines)
    raise UnsupportedLayout(_unsupported_message(text.lower()))


def _unsupported_message(lowered):
    """Say which bank the file seems to come from, so the student knows what to fix."""
    if any(name in lowered for name in halyk.BANK_NAMES):
        found = "This looks like a Halyk statement, but not a card account statement."
    elif "kaspi" in lowered:
        found = "This looks like a Kaspi file, but not a Kaspi Gold statement."
    else:
        found = "This file doesn't look like a bank statement we can read."
    return (
        f"{found} {SUPPORTED} Download the statement from the bank app and try again."
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
