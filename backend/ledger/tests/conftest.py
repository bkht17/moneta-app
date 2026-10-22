from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from ledger.models import BankAccount, Review
from ledger.parsers import parse_lines
from ledger.samples import halyk_lines, kaspi_lines
from ledger.services.ingest import import_statement
from users.models import User


@pytest.fixture
def user(db):
    return User.objects.create_user("student@example.test", "a-long-test-pass-42")


@pytest.fixture
def client(user):
    api = APIClient()
    api.force_authenticate(user)
    return api


@pytest.fixture
def accounts(user):
    kaspi = BankAccount.objects.create(user=user, bank="kaspi", label="Kaspi Gold")
    halyk = BankAccount.objects.create(user=user, bank="halyk", label="Halyk card")
    return kaspi, halyk


@pytest.fixture
def review(user, accounts):
    review = Review.objects.create(
        user=user, month=date(2026, 10, 1), budget_kzt=Decimal("100000")
    )
    review.accounts.set(accounts)
    return review


@pytest.fixture
def imported(review, accounts):
    """The reference case: Kaspi to 15 Oct, Halyk to 18 Oct."""
    kaspi, halyk = accounts
    import_statement(kaspi, parse_lines(kaspi_lines()), "kaspi.pdf", review)
    import_statement(halyk, parse_lines(halyk_lines()), "halyk.pdf", review)
    return review
