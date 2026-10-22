"""F3: the spending and remaining-budget overview for a complete review."""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from ..models import Kind
from .categories import CASH_CATEGORY
from .intake import account_coverage, is_current, month_end
from .reconcile import review_transactions

SPENDING_KINDS = (Kind.PURCHASE, Kind.TRANSFER_OUT)
ZERO = Decimal("0.00")


def _tx(tx):
    return {
        "id": str(tx.id),
        "date": tx.booked_on.isoformat(),
        "amount": tx.amount,
        "description": tx.description,
        "operation": tx.operation,
        "kind": tx.kind,
        "category": tx.category,
        "category_editable": tx.kind in SPENDING_KINDS + (Kind.REFUND,)
        and not tx.excluded_reason,
        "excluded_reason": tx.excluded_reason,
        "account": {"id": str(tx.account_id), "label": tx.account.label},
    }


def build_overview(review):
    cutoff = review.cutoff_date
    rows = list(review_transactions(review))
    main = [t for t in rows if t.booked_on <= cutoff]
    later = [t for t in rows if t.booked_on > cutoff and not t.excluded_reason]
    counted = [t for t in main if not t.excluded_reason]

    categories = defaultdict(lambda: ZERO)
    daily = defaultdict(lambda: ZERO)
    incoming = income = own = refunds = withdrawals = ZERO
    for tx in counted:
        if tx.amount > 0:
            incoming += tx.amount
        if tx.kind in SPENDING_KINDS:
            categories[tx.category] += -tx.amount
            daily[tx.booked_on] += -tx.amount
        elif tx.kind == Kind.REFUND:
            refunds += tx.amount
            categories[tx.category] -= tx.amount
            daily[tx.booked_on] -= tx.amount
        elif tx.kind in (Kind.INCOME, Kind.TRANSFER_IN):
            income += tx.amount
        elif tx.kind == Kind.OWN_TRANSFER and tx.amount > 0:
            own += tx.amount
        elif tx.kind == Kind.WITHDRAWAL:
            withdrawals += -tx.amount

    cash = review.cash_kzt or ZERO
    if cash > 0:
        categories[CASH_CATEGORY] += cash
    spending = sum(categories.values(), ZERO)

    coverage = []
    for account in review.accounts.all():
        cov = account_coverage(account, review.month)
        coverage.append(
            {
                "id": str(account.id),
                "label": account.label,
                "bank": account.bank,
                "last4": account.last4,
                "covered_until": (
                    cov.covered_until.isoformat() if cov.covered_until else None
                ),
            }
        )

    later_until = max([t.booked_on for t in later] + [cutoff])
    if review.later_cash_until:
        later_until = max(later_until, review.later_cash_until)

    day = review.month
    series = []
    while day <= cutoff:
        series.append({"date": day.isoformat(), "amount": daily.get(day, ZERO)})
        day += timedelta(days=1)

    return {
        "review_id": str(review.id),
        "month": review.month.isoformat(),
        "period": {"start": review.month.isoformat(), "end": cutoff.isoformat()},
        "is_current": is_current(review),
        "budget": review.budget_kzt,
        "spending": spending,
        "remaining": review.budget_kzt - spending,
        "incoming": incoming,
        "income": income,
        "own_transfers": own,
        "refunds": refunds,
        "withdrawals": withdrawals,
        "cash": {"amount": review.cash_kzt, "until": cutoff.isoformat()},
        "categories": sorted(
            ({"name": k, "amount": v} for k, v in categories.items() if v != 0),
            key=lambda c: c["amount"],
            reverse=True,
        ),
        "daily": series,
        "accounts": coverage,
        "transactions": [_tx(t) for t in main],
        "outside": {
            "from": (cutoff + timedelta(days=1)).isoformat(),
            "until": later_until.isoformat() if later_until > cutoff else None,
            "month_end": month_end(review.month).isoformat(),
            "transactions": [_tx(t) for t in later],
            "bank_spending": sum(
                (-t.amount for t in later if t.kind in SPENDING_KINDS), ZERO
            ),
            "cash": review.later_cash_kzt,
        },
    }
