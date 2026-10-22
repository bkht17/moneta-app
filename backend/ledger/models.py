import uuid

from django.conf import settings
from django.db import models


class Bank(models.TextChoices):
    KASPI = "kaspi", "Kaspi"
    HALYK = "halyk", "Halyk"


class BankAccount(models.Model):
    """An account the student declares (F1). Only a label and the last four digits
    are kept, never the full card or IBAN number (NFR1)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="accounts"
    )
    bank = models.CharField(max_length=16, choices=Bank.choices)
    label = models.CharField(max_length=60)
    last4 = models.CharField(max_length=4, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bank_accounts"
        ordering = ("created_at",)

    def __str__(self):
        return self.label


class Review(models.Model):
    """One combined spending review for a budget month (UC1)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        NEEDS_CONFIRMATION = "needs_confirmation", "Needs confirmation"
        COMPLETE = "complete", "Complete"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    month = models.DateField(help_text="First day of the budget month")
    budget_kzt = models.DecimalField(max_digits=12, decimal_places=2)
    accounts = models.ManyToManyField(BankAccount, related_name="reviews")
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.DRAFT
    )
    cutoff_date = models.DateField(null=True, blank=True)
    # Null means "not declared": a blank cash field never silently becomes 0 (F1).
    cash_kzt = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    later_cash_kzt = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    later_cash_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    intake_completed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    overview_opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reviews"
        ordering = ("-created_at",)


class StatementImport(models.Model):
    """Metadata about an uploaded statement. The PDF itself is never stored."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="statements"
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="statements",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    file_name = models.CharField(max_length=120)
    row_count = models.PositiveIntegerField()
    new_rows = models.PositiveIntegerField(default=0)
    layout = models.CharField(max_length=32)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "statement_imports"
        ordering = ("period_start",)


class Kind(models.TextChoices):
    PURCHASE = "purchase", "Purchase"
    INCOME = "income", "Income"
    TRANSFER_OUT = "transfer_out", "Transfer out"
    TRANSFER_IN = "transfer_in", "Transfer in"
    OWN_TRANSFER = "own_transfer", "Own-account transfer"
    WITHDRAWAL = "withdrawal", "Cash withdrawal"
    REFUND = "refund", "Refund"


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="transactions"
    )
    statement = models.ForeignKey(
        StatementImport,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transactions",
    )
    booked_on = models.DateField()
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Signed, KZT"
    )
    operation = models.CharField(max_length=60, blank=True)
    description = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    category = models.CharField(max_length=40)
    category_set_by_user = models.BooleanField(default=False)
    # Stable identity of a source row: repeat imports of the same row update it
    # instead of adding it again (F2).
    fingerprint = models.CharField(max_length=64)
    excluded_reason = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions"
        ordering = ("booked_on", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("account", "fingerprint"),
                name="uniq_tx_fingerprint_per_account",
            )
        ]
        indexes = [models.Index(fields=("account", "booked_on"))]


class ReviewFlag(models.Model):
    """An item the student must confirm before the total is shown (F2-AC2)."""

    class Type(models.TextChoices):
        POSSIBLE_DUPLICATE = "possible_duplicate", "Possible duplicate"
        POSSIBLE_OWN_TRANSFER = "possible_own_transfer", "Possible own transfer"

    class Resolution(models.TextChoices):
        KEEP_BOTH = "keep_both", "Two separate purchases"
        SAME_PURCHASE = "same_purchase", "The same purchase twice"
        OWN_TRANSFER = "own_transfer", "My own transfer"
        NOT_OWN_TRANSFER = "not_own_transfer", "Not my own transfer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="flags")
    type = models.CharField(max_length=32, choices=Type.choices)
    first = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="+")
    second = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="+")
    resolution = models.CharField(
        max_length=24, choices=Resolution.choices, blank=True, default=""
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "review_flags"
        ordering = ("first__booked_on",)
