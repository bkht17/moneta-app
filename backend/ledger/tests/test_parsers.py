from datetime import date
from decimal import Decimal

import pytest

from ledger.parsers import PeriodNotFound, UnsupportedLayout, parse_lines
from ledger.parsers.base import mask_numbers, parse_amount
from ledger.models import Kind
from ledger.samples import halyk_lines, kaspi_lines, kaspi_lines_en
from ledger.services.categories import category_for, kind_for


def test_kaspi_sample_is_parsed():
    statement = parse_lines(kaspi_lines())

    assert statement.bank == "kaspi"
    assert statement.last4 == "1234"
    assert (statement.period_start, statement.period_end) == (
        date(2026, 10, 1),
        date(2026, 10, 15),
    )
    assert len(statement.rows) == 8
    first = statement.rows[0]
    assert first.amount == Decimal("42000.00")
    assert first.operation == "Пополнение"
    assert statement.rows[1].amount == Decimal("-6200.00")
    assert statement.rows[-1].operation == "Снятие"


def test_kaspi_english_statement_is_parsed():
    statement = parse_lines(kaspi_lines_en())

    assert statement.bank == "kaspi"
    assert statement.last4 == "1234"
    assert statement.period_end == date(2026, 10, 15)
    assert [r.operation for r in statement.rows] == [
        "Пополнение",
        "Покупка",
        "Пополнение",
        "Перевод",
        "Покупка",
        "Снятие",
    ]
    # Summary lines such as "Purchases - 10 800,00 ₸" are not transactions.
    assert len(statement.rows) == 6


def test_atm_deposit_is_own_money_not_income():
    assert kind_for("Пополнение", Decimal("5000"), "At Kaspi ATM") == Kind.OWN_TRANSFER
    assert kind_for("Пополнение", Decimal("42000"), "Stipend KBTU") == Kind.TRANSFER_IN


@pytest.mark.parametrize(
    "description, category",
    [
        ("Додо пицца", "Cafés"),
        ("Popeyes", "Cafés"),
        ("Вузы и колледжи", "Study"),
        ("Магазин Сымбат", "Groceries"),
        ("Магазин одежды", "Clothing"),
        ("YANDEX.GO", "Transport"),
    ],
)
def test_category_keywords(description, category):
    assert category_for(Kind.PURCHASE, description) == category


def test_halyk_sample_is_parsed_with_signs_from_credit_and_debit():
    statement = parse_lines(halyk_lines())

    assert statement.bank == "halyk"
    assert statement.last4 == "5678"
    assert statement.period_end == date(2026, 10, 18)
    assert len(statement.rows) == 8
    assert statement.rows[0].amount == Decimal("20000.00")
    assert statement.rows[0].operation == "Пополнение"
    assert statement.rows[1].amount == Decimal("-2000.00")


def test_halyk_wrapped_description_is_joined():
    lines = halyk_lines()
    header_end = 5
    lines.insert(header_end + 2, "продолжение описания")
    statement = parse_lines(lines)

    assert statement.rows[1].description.endswith("продолжение описания")
    assert len(statement.rows) == 8


def test_halyk_statement_mentioning_kaspi_is_not_read_as_kaspi():
    assert parse_lines(halyk_lines()).bank == "halyk"


def test_unknown_layout_is_rejected():
    with pytest.raises(UnsupportedLayout):
        parse_lines(["Some other bank", "Выписка за период с 01.10.2026 по 15.10.2026"])


def test_missing_period_is_reported():
    lines = [line for line in kaspi_lines() if "период" not in line]
    lines.insert(0, "Выписка по Kaspi Gold")
    with pytest.raises(PeriodNotFound):
        parse_lines(lines)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("- 2 500,00 ₸", Decimal("-2500.00")),
        ("+ 42 000,00", Decimal("42000.00")),
        ("−700,00", Decimal("-700.00")),
        ("1 234 567,89 KZT", Decimal("1234567.89")),
    ],
)
def test_parse_amount(text, expected):
    assert parse_amount(text) == expected


def test_long_numbers_are_masked():
    masked = mask_numbers("Перевод KZ12345678901234567890 на 4400 4301 2345 6789")
    assert "1234567890" not in masked
    assert "••7890" in masked
    assert "••6789" in masked
