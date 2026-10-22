from rest_framework import serializers

from .models import BankAccount, Review, ReviewFlag, StatementImport, Transaction
from .services.categories import CATEGORIES


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ("id", "bank", "label", "last4", "created_at")
        read_only_fields = ("id", "last4", "created_at")


class StatementImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementImport
        fields = (
            "id",
            "account",
            "period_start",
            "period_end",
            "file_name",
            "row_count",
            "new_rows",
            "layout",
            "imported_at",
        )


class ReviewSerializer(serializers.ModelSerializer):
    accounts = serializers.PrimaryKeyRelatedField(
        many=True, queryset=BankAccount.objects.none()
    )
    open_flags = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "id",
            "month",
            "budget_kzt",
            "accounts",
            "status",
            "cutoff_date",
            "cash_kzt",
            "later_cash_kzt",
            "later_cash_until",
            "created_at",
            "intake_completed_at",
            "completed_at",
            "open_flags",
        )
        read_only_fields = (
            "id",
            "status",
            "cutoff_date",
            "cash_kzt",
            "later_cash_kzt",
            "later_cash_until",
            "created_at",
            "intake_completed_at",
            "completed_at",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            self.fields["accounts"].child_relation.queryset = (
                request.user.accounts.all()
            )

    def get_open_flags(self, obj) -> int:
        return obj.flags.filter(resolved_at__isnull=True).count()

    def validate_month(self, value):
        return value.replace(day=1)

    def validate_budget_kzt(self, value):
        if value < 0:
            raise serializers.ValidationError("The budget can't be negative.")
        return value

    def validate(self, attrs):
        if self.instance and self.instance.status != Review.Status.DRAFT:
            raise serializers.ValidationError(
                "This review is already calculated. Start a new review to change it."
            )
        return attrs


class SubmitSerializer(serializers.Serializer):
    # Kept as raw values so a blank field reaches the F1 check instead of a 400 from DRF.
    cash_kzt = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    later_cash_kzt = serializers.CharField(
        allow_blank=True, allow_null=True, required=False
    )
    later_cash_until = serializers.DateField(allow_null=True, required=False)


class UploadSerializer(serializers.Serializer):
    account = serializers.UUIDField()
    file = serializers.FileField()


class TransactionBriefSerializer(serializers.ModelSerializer):
    account_label = serializers.CharField(source="account.label")

    class Meta:
        model = Transaction
        fields = (
            "id",
            "booked_on",
            "amount",
            "description",
            "operation",
            "account_label",
        )


class FlagSerializer(serializers.ModelSerializer):
    first = TransactionBriefSerializer()
    second = TransactionBriefSerializer()

    class Meta:
        model = ReviewFlag
        fields = ("id", "type", "first", "second", "resolution", "resolved_at")


class ResolveSerializer(serializers.Serializer):
    resolution = serializers.ChoiceField(choices=ReviewFlag.Resolution.choices)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ("id", "category")

    def validate_category(self, value):
        if value not in CATEGORIES:
            raise serializers.ValidationError("Unknown category.")
        return value
