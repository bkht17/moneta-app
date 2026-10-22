"""Halyk Bank card account statement ("Выписка по карточному счету").

Columns: operation date, processing date, description, operation amount, currency,
credit (приход), debit (расход), fee, card. A long description may wrap onto the
next line; such lines are joined to the previous row.

    05.10.2025 06.10.2025 Перевод с карты Kaspi 20 000,00 KZT 20 000,00 0,00 0,00 *5678
"""

import re

from .base import (
    AMOUNT_RE,
    DATE_RE,
    ParsedRow,
    ParsedStatement,
    StatementError,
    find_period,
    mask_numbers,
    parse_amount,
    parse_date,
    squash,
)

LAYOUT = "halyk-card-v1"
ROW_RE = re.compile(
    rf"^(?P<date>\d{{2}}\.\d{{2}}\.\d{{4}})\s+(?:{DATE_RE}\s+)?(?P<desc>.+?)\s+"
    rf"(?P<op_amount>{AMOUNT_RE})\s+(?P<currency>[A-Z]{{3}})\s+"
    rf"(?P<credit>{AMOUNT_RE})\s+(?P<debit>{AMOUNT_RE})\s+(?P<fee>{AMOUNT_RE})"
    r"(?:\s+\S+)?$"
)
CARD_RE = re.compile(r"(?:карт\w*|card)\D{0,25}\*+\s?(\d{4})", re.IGNORECASE)
STOP_WORDS = ("итого", "всего", "остаток", "сумма блокированных")


def matches(text):
    lowered = text.lower()
    is_halyk = "halyk" in lowered or "народный" in lowered
    return is_halyk and "выписка по карточному счету" in lowered


def parse(lines):
    start, end = find_period(lines)
    statement = ParsedStatement(
        bank="halyk", layout=LAYOUT, period_start=start, period_end=end
    )
    last = None
    for raw in lines:
        line = squash(raw)
        if not statement.last4:
            card = CARD_RE.search(line)
            if card:
                statement.last4 = card.group(1)
        row = ROW_RE.match(line)
        if row:
            if row["currency"] != "KZT":
                raise StatementError(
                    "Only statements for tenge accounts are supported.",
                    code="unsupported_currency",
                )
            credit = abs(parse_amount(row["credit"]))
            debit = abs(parse_amount(row["debit"]))
            amount = credit if credit > 0 else -debit
            if amount == 0:
                amount = parse_amount(row["op_amount"])
            last = ParsedRow(
                booked_on=parse_date(row["date"]),
                amount=amount,
                operation=_operation(row["desc"]),
                description=mask_numbers(row["desc"]),
            )
            statement.rows.append(last)
            continue
        if last and line and not line[:1].isdigit() and not _is_footer(line):
            last.description = mask_numbers(f"{last.description} {line}")
            last.operation = _operation(last.description)
        elif _is_footer(line):
            last = None
    if not statement.rows:
        raise StatementError(
            "No transactions were found in this Halyk statement.", code="no_rows"
        )
    return statement


def _is_footer(line):
    """Totals, balances and repeated column headers end a wrapped description."""
    lowered = line.lower()
    if "дата" in lowered and "операц" in lowered:
        return True
    return any(word in lowered for word in STOP_WORDS)


def _operation(description):
    lowered = description.lower()
    if "возврат" in lowered:
        return "Возврат"
    if "снятие" in lowered or "банкомат" in lowered or "atm" in lowered:
        return "Снятие"
    if "перевод" in lowered or "p2p" in lowered:
        return "Перевод"
    if "пополнение" in lowered or "зачисление" in lowered:
        return "Пополнение"
    return "Покупка"
