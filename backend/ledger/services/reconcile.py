"""F2: find rows the student must confirm and apply their answers.

Nothing is removed only because date and amount match. A pair that identifiers can't
settle becomes a flag, and the total stays hidden until every flag is answered.
"""

from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from ..models import Kind, Review, ReviewFlag, Transaction

TRANSFER_MATCH_DAYS = 2


def review_transactions(review, until=None):
    from .intake import month_end

    qs = Transaction.objects.filter(
        account__in=review.accounts.all(),
        booked_on__gte=review.month,
        booked_on__lte=until or month_end(review.month),
    ).select_related("account")
    return qs


def _resolved_pairs(review):
    pairs = set()
    flags = ReviewFlag.objects.filter(
        review__user=review.user, resolved_at__isnull=False
    ).values_list("first_id", "second_id")
    for first, second in flags:
        pairs.add(frozenset((first, second)))
    return pairs


@transaction.atomic
def reconcile(review):
    review.flags.filter(resolved_at__isnull=True).delete()
    rows = list(
        review_transactions(review, until=review.cutoff_date).filter(excluded_reason="")
    )
    resolved = _resolved_pairs(review)
    flags = []

    groups = defaultdict(list)
    for tx in rows:
        if tx.kind == Kind.PURCHASE:
            key = (tx.account_id, tx.booked_on, tx.amount, tx.description.lower())
            groups[key].append(tx)
    for group in groups.values():
        for first, second in zip(group, group[1:]):
            if frozenset((first.id, second.id)) not in resolved:
                flags.append(
                    ReviewFlag(
                        review=review,
                        type=ReviewFlag.Type.POSSIBLE_DUPLICATE,
                        first=first,
                        second=second,
                    )
                )

    outgoing = [t for t in rows if t.kind == Kind.TRANSFER_OUT]
    incoming = [t for t in rows if t.kind in (Kind.TRANSFER_IN, Kind.INCOME)]
    used = set()
    for out in outgoing:
        for inc in incoming:
            if inc.id in used or inc.account_id == out.account_id:
                continue
            if inc.amount != -out.amount:
                continue
            if abs((inc.booked_on - out.booked_on).days) > TRANSFER_MATCH_DAYS:
                continue
            if frozenset((out.id, inc.id)) in resolved:
                continue
            used.add(inc.id)
            flags.append(
                ReviewFlag(
                    review=review,
                    type=ReviewFlag.Type.POSSIBLE_OWN_TRANSFER,
                    first=out,
                    second=inc,
                )
            )
            break

    ReviewFlag.objects.bulk_create(flags)
    _update_status(review)
    return flags


VALID = {
    ReviewFlag.Type.POSSIBLE_DUPLICATE: {
        ReviewFlag.Resolution.KEEP_BOTH,
        ReviewFlag.Resolution.SAME_PURCHASE,
    },
    ReviewFlag.Type.POSSIBLE_OWN_TRANSFER: {
        ReviewFlag.Resolution.OWN_TRANSFER,
        ReviewFlag.Resolution.NOT_OWN_TRANSFER,
    },
}


class InvalidResolution(ValueError):
    pass


@transaction.atomic
def resolve(flag, resolution):
    if resolution not in VALID[flag.type]:
        raise InvalidResolution(f"“{resolution}” doesn't answer a {flag.type} flag.")
    if resolution == ReviewFlag.Resolution.SAME_PURCHASE:
        Transaction.objects.filter(pk=flag.second_id).update(
            excluded_reason="duplicate"
        )
    elif resolution == ReviewFlag.Resolution.OWN_TRANSFER:
        Transaction.objects.filter(pk__in=[flag.first_id, flag.second_id]).update(
            kind=Kind.OWN_TRANSFER, category="Own transfers"
        )
    flag.resolution = resolution
    flag.resolved_at = timezone.now()
    flag.save(update_fields=["resolution", "resolved_at"])
    _update_status(flag.review)
    return flag


def _update_status(review):
    if review.status == Review.Status.DRAFT and review.intake_completed_at is None:
        return
    open_flags = review.flags.filter(resolved_at__isnull=True).exists()
    if open_flags:
        review.status = Review.Status.NEEDS_CONFIRMATION
        review.completed_at = None
    else:
        review.status = Review.Status.COMPLETE
        review.completed_at = review.completed_at or timezone.now()
    review.save(update_fields=["status", "completed_at"])


def open_flags(review):
    return review.flags.filter(resolved_at__isnull=True).select_related(
        "first__account", "second__account"
    )
