"""Shared types and helpers for bank statement parsers.

Parsers work on plain text lines so they can be tested without PDF files. The PDF
step (pdf.py) only turns an in-memory file into lines.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


class StatementError(Exception):
    """A statement that cannot be used. `code` is stable for the frontend."""

    code = "invalid_statement"

    def __init__(self, message, code=None):
        super().__init__(message)
        if code:
            self.code = code


class UnsupportedLayout(StatementError):
    code = "unsupported_layout"


class PeriodNotFound(StatementError):
    code = "period_not_found"


@dataclass
class ParsedRow:
    booked_on: date
    amount: Decimal
    operation: str
    description: str


@dataclass
class ParsedStatement:
    bank: str
    layout: str
    period_start: date
    period_end: date
    last4: str = ""
    rows: list[ParsedRow] = field(default_factory=list)


SPACES = "    "
AMOUNT_RE = r"[+\-−]?\s?\d[\d" + SPACES + r"]*,\d{2}"
DATE_RE = r"\d{2}\.\d{2}\.(?:\d{4}|\d{2})"
PERIOD_PATTERNS = (
    re.compile(rf"с\s+({DATE_RE})\s+по\s+({DATE_RE})", re.IGNORECASE),
    re.compile(rf"период\D{{0,20}}({DATE_RE})\s*[-–—]\s*({DATE_RE})", re.IGNORECASE),
    re.compile(rf"from\s+({DATE_RE})\s+to\s+({DATE_RE})", re.IGNORECASE),
    re.compile(rf"({DATE_RE})\s+бастап\s+({DATE_RE})", re.IGNORECASE),
    re.compile(rf"кезең\D{{0,20}}({DATE_RE})\s*[-–—]\s*({DATE_RE})", re.IGNORECASE),
)
LONG_NUMBER_RE = re.compile(r"(?:KZ\d{2}[0-9A-Z]{13,})|\d[\d ]{7,}\d")


def parse_amount(text):
    """'- 2 500,00 ₸' -> Decimal('-2500.00')."""
    cleaned = text.replace("₸", "").replace("KZT", "").replace("−", "-")
    for ch in SPACES:
        cleaned = cleaned.replace(ch, "")
    cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise StatementError(f"Unreadable amount: {text!r}") from exc


def parse_date(text):
    fmt = "%d.%m.%Y" if len(text) == 10 else "%d.%m.%y"
    return datetime.strptime(text, fmt).date()


def find_period(lines):
    for line in lines:
        for pattern in PERIOD_PATTERNS:
            match = pattern.search(line)
            if match:
                start, end = parse_date(match.group(1)), parse_date(match.group(2))
                if start <= end:
                    return start, end
    raise PeriodNotFound(
        "The statement period was not found. Download the full statement for the month "
        "from the bank app.",
    )


def mask_numbers(text):
    """Keep only the last four digits of anything that looks like a card, phone or
    account number (NFR1: no full account numbers in stored records)."""

    def _mask(match):
        digits = re.sub(r"\D", "", match.group(0))
        return f"••{digits[-4:]}"

    return LONG_NUMBER_RE.sub(_mask, text)


def squash(text):
    return re.sub(r"\s+", " ", text).strip()
