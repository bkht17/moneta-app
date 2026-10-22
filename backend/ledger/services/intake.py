"""F1: coverage of declared accounts, the common cutoff date and intake validation."""

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ..models import Review
from .reconcile import reconcile

CURRENT_REVIEW_MAX_AGE_DAYS = 7


def month_end(month):
    return month.replace(day=calendar.monthrange(month.year, month.month)[1])


@dataclass
class AccountCoverage:
    account: object
    covered_until: date | None = None
    starts_late_on: date | None = None
    gap_after: date | None = None
    statements: list = field(default_factory=list)

    @property
    def ok(self):
        return self.covered_until is not None and self.starts_late_on is None


def account_coverage(account, month):
    """Contiguous statement coverage from the first day of the month."""
    coverage = AccountCoverage(account=account)
    statements = list(
        account.statements.filter(period_end__gte=month).order_by("period_start")
    )
    coverage.statements = statements
    if not statements:
        return coverage
    if statements[0].period_start > month:
        coverage.starts_late_on = statements[0].period_start
        return coverage

    covered_until = statements[0].period_end
    for statement in statements[1:]:
        if statement.period_start > covered_until + timedelta(days=1):
            coverage.gap_after = covered_until
            break
        covered_until = max(covered_until, statement.period_end)
    coverage.covered_until = min(covered_until, month_end(month))
    return coverage


@dataclass
class IntakeResult:
    coverages: list
    cutoff: date | None
    errors: list

    @property
    def ok(self):
        return not self.errors


def evaluate_coverage(review):
    coverages = [account_coverage(a, review.month) for a in review.accounts.all()]
    errors = []
    if not coverages:
        errors.append(_error("no_accounts", "Declare at least one account."))
    for cov in coverages:
        label = cov.account.label
        if not cov.statements:
            errors.append(
                _error(
                    "missing_statement",
                    f"Add a statement for {label} from {review.month:%d %b}.",
                    cov.account,
                )
            )
        elif cov.starts_late_on:
            errors.append(
                _error(
                    "coverage_gap",
                    f"The {label} statement starts on {cov.starts_late_on:%d %b}. "
                    f"It must start on {review.month:%d %b}.",
                    cov.account,
                )
            )
    cutoff = None
    if coverages and all(c.ok for c in coverages):
        cutoff = min(c.covered_until for c in coverages)
    return IntakeResult(coverages=coverages, cutoff=cutoff, errors=errors)


def _error(code, message, account=None):
    item = {"code": code, "message": message}
    if account is not None:
        item["account"] = str(account.id)
    return item


def _amount(value, field_name, errors, required):
    if value in (None, ""):
        if required:
            errors.append(
                _error(
                    "cash_missing",
                    "Enter the cash you spent, or 0 if you spent none. "
                    "A blank field can't be counted.",
                )
            )
        return None
    try:
        amount = Decimal(str(value))
    except Exception:
        errors.append(_error("invalid_amount", f"{field_name} must be a number."))
        return None
    if amount < 0:
        errors.append(_error("invalid_amount", f"{field_name} can't be negative."))
        return None
    return amount.quantize(Decimal("0.01"))


@transaction.atomic
def submit(review, cash, later_cash=None, later_cash_until=None):
    """Validate every input (F1-AC2). Only a fully valid intake starts calculation."""
    result = evaluate_coverage(review)
    errors = list(result.errors)
    cash_amount = _amount(cash, "Cash", errors, required=True)
    later_amount = _amount(later_cash, "Later cash", errors, required=False)

    if later_amount is not None:
        if not later_cash_until:
            errors.append(
                _error(
                    "later_cash_period",
                    "Give the last date of the later cash period.",
                )
            )
        elif result.cutoff and later_cash_until <= result.cutoff:
            errors.append(
                _error(
                    "later_cash_period",
                    f"Later cash must cover dates after {result.cutoff:%d %b}.",
                )
            )

    if errors:
        review.status = Review.Status.DRAFT
        review.save(update_fields=["status"])
        return errors

    review.cutoff_date = result.cutoff
    review.cash_kzt = cash_amount
    review.later_cash_kzt = later_amount
    review.later_cash_until = later_cash_until if later_amount is not None else None
    review.intake_completed_at = timezone.now()
    review.save()
    reconcile(review)
    return []


def is_current(review, today=None):
    today = today or timezone.localdate()
    return bool(
        review.cutoff_date
        and review.cutoff_date >= today - timedelta(days=CURRENT_REVIEW_MAX_AGE_DAYS)
    )
