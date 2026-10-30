"""Store a parsed statement for one declared account (F1 intake, F2 repeat imports)."""

import hashlib
from collections import Counter

from django.db import transaction

from ..models import StatementImport, Transaction
from ..parsers import StatementError
from .categories import category_for, kind_for


class AccountMismatch(StatementError):
    code = "account_mismatch"


def fingerprint(bank, row, occurrence):
    """Identity of a source row. Identical rows on the same day are told apart by their
    order of appearance, so two real 1,200 ₸ coffees stay two rows, while importing the
    same statement again matches the rows already stored."""
    key = "|".join(
        [
            bank,
            row.booked_on.isoformat(),
            f"{row.amount:.2f}",
            row.description.lower(),
            str(occurrence),
        ]
    )
    return hashlib.sha256(key.encode()).hexdigest()


@transaction.atomic
def import_statement(account, parsed, file_name, review=None):
    if parsed.bank != account.bank:
        raise AccountMismatch(
            f"This is a {parsed.bank.title()} statement, but the account "
            f"“{account.label}” is {account.get_bank_display()}."
        )
    if account.last4 and parsed.last4 and account.last4 != parsed.last4:
        raise AccountMismatch(
            f"This statement is for card ••{parsed.last4}, but “{account.label}” "
            f"is ••{account.last4}."
        )
    if parsed.last4 and not account.last4:
        account.last4 = parsed.last4
        account.save(update_fields=["last4"])

    statement = StatementImport.objects.create(
        account=account,
        review=review,
        period_start=parsed.period_start,
        period_end=parsed.period_end,
        file_name=file_name[:120],
        row_count=len(parsed.rows),
        layout=parsed.layout,
    )

    seen = Counter()
    new_rows = 0
    for row in parsed.rows:
        identity = (row.booked_on, row.amount, row.description.lower())
        occurrence = seen[identity]
        seen[identity] += 1
        kind = kind_for(row.operation, row.amount, row.description)
        tx, created = Transaction.objects.get_or_create(
            account=account,
            fingerprint=fingerprint(parsed.bank, row, occurrence),
            defaults={
                "statement": statement,
                "booked_on": row.booked_on,
                "amount": row.amount,
                "operation": row.operation,
                "description": row.description,
                "kind": kind,
                "category": category_for(kind, row.description),
            },
        )
        if created:
            new_rows += 1
        else:
            tx.statement = statement
            tx.save(update_fields=["statement"])

    statement.new_rows = new_rows
    statement.save(update_fields=["new_rows"])
    return statement
