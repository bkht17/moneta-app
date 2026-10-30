"""Halyk Bank card account statement in Russian ("Выписка по карточному счету"),
Kazakh ("Карт шоты бойынша үзінді көшірме") or English ("Card account statement").

Full layout columns: operation date, processing date, description, operation amount,
currency, credit, debit, fee, card. The short layout has only date, description, signed
amount and currency. A long description may wrap onto the next line; such lines are
joined to the previous row.

    05.10.2025 06.10.2025 Перевод с карты Kaspi 20 000,00 KZT 20 000,00 0,00 0,00 *5678
    06.10.2025 Spotify -2 000,00 KZT
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
SHORT_ROW_RE = re.compile(
    rf"^(?P<date>\d{{2}}\.\d{{2}}\.\d{{4}})\s+(?:{DATE_RE}\s+)?(?P<desc>.+?)\s+"
    rf"(?P<amount>{AMOUNT_RE})\s+(?P<currency>[A-Z]{{3}})(?:\s+\S+)?$"
)
CARD_RE = re.compile(r"(?:карт\w*|card)\D{0,25}\*+\s?(\d{4})", re.IGNORECASE)
STOP_WORDS = (
    "итого",
    "всего",
    "остаток",
    "сумма блокированных",
    "барлығы",
    "қалдық",
    "total",
    "balance",
)
BANK_NAMES = ("halyk", "народный", "халық")
TITLES = (
    "выписка по карточному счету",
    "карт шоты бойынша үзінді көшірме",
    "card account statement",
)


def matches(text):
    lowered = text.lower()
    is_halyk = any(name in lowered for name in BANK_NAMES)
    return is_halyk and any(title in lowered for title in TITLES)


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
        row = ROW_RE.match(line) or SHORT_ROW_RE.match(line)
        if row:
            if row["currency"] != "KZT":
                raise StatementError(
                    "Only statements for tenge accounts are supported.",
                    code="unsupported_currency",
                )
            amount = _signed_amount(row)
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


def _signed_amount(row):
    fields = row.groupdict()
    if "credit" not in fields:
        return parse_amount(row["amount"])
    credit = abs(parse_amount(row["credit"]))
    debit = abs(parse_amount(row["debit"]))
    amount = credit if credit > 0 else -debit
    return amount if amount != 0 else parse_amount(row["op_amount"])


def _is_footer(line):
    """Totals, balances and repeated column headers end a wrapped description."""
    lowered = line.lower()
    if ("дата" in lowered or "күні" in lowered or "date" in lowered) and (
        "операц" in lowered or "transaction" in lowered
    ):
        return True
    return any(word in lowered for word in STOP_WORDS)


OPERATION_WORDS = (
    ("Возврат", ("возврат", "қайтару", "refund")),
    ("Снятие", ("снятие", "банкомат", "atm", "шешу", "ақша алу", "cash withdrawal")),
    ("Перевод", ("перевод", "p2p", "аударым", "transfer")),
    ("Пополнение", ("пополнение", "зачисление", "толықтыру", "top-up", "replenish")),
)


def _operation(description):
    lowered = description.lower()
    for operation, words in OPERATION_WORDS:
        if any(word in lowered for word in words):
            return operation
    return "Покупка"
