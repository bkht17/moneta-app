"""Kaspi Gold statement ("Выписка по Kaspi Gold").

Expected table rows, one per line after text extraction:
    02.10.25  + 42 000,00 ₸  Пополнение  С карты другого банка
    03.10.25  - 6 200,00 ₸   Покупка     MAGNUM CASH&CARRY
"""

import re

from .base import (
    AMOUNT_RE,
    ParsedRow,
    ParsedStatement,
    StatementError,
    find_period,
    mask_numbers,
    parse_amount,
    parse_date,
    squash,
)

LAYOUT = "kaspi-gold-v1"
ROW_RE = re.compile(
    # The tenge sign is optional: some PDF fonts lack the glyph and extract it as "\x00".
    rf"^(?P<date>\d{{2}}\.\d{{2}}\.\d{{2}})\s+(?P<amount>{AMOUNT_RE})\s*(?:₸|KZT|[^\w\s])?\s+"
    r"(?P<op>Покупки|Покупка|Пополнения|Пополнение|Переводы|Перевод|Снятия|Снятие|Разное)"
    r"\s*(?P<details>.*)$"
)
CARD_RE = re.compile(r"(?:номер карты|карта)\D{0,20}\*+\s?(\d{4})", re.IGNORECASE)
OPERATIONS = {
    "Покупки": "Покупка",
    "Пополнения": "Пополнение",
    "Переводы": "Перевод",
    "Снятия": "Снятие",
}


def matches(text):
    return bool(re.search(r"выписка\s+по\s+kaspi\s+gold", text, re.IGNORECASE))


def parse(lines):
    start, end = find_period(lines)
    statement = ParsedStatement(
        bank="kaspi", layout=LAYOUT, period_start=start, period_end=end
    )
    for line in lines:
        if not statement.last4:
            card = CARD_RE.search(line)
            if card:
                statement.last4 = card.group(1)
        row = ROW_RE.match(squash(line))
        if not row:
            continue
        operation = OPERATIONS.get(row["op"], row["op"])
        statement.rows.append(
            ParsedRow(
                booked_on=parse_date(row["date"]),
                amount=parse_amount(row["amount"]),
                operation=operation,
                description=mask_numbers(squash(row["details"])),
            )
        )
    if not statement.rows and not _says_no_operations(lines):
        raise StatementError(
            "No transactions were found in this Kaspi statement.", code="no_rows"
        )
    return statement


def _says_no_operations(lines):
    return any("операций нет" in line.lower() for line in lines)
