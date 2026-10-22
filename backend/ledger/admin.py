from django.contrib import admin

from .models import BankAccount, Review, ReviewFlag, StatementImport


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("label", "bank", "last4", "user", "created_at")
    list_filter = ("bank",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "month",
        "status",
        "cutoff_date",
        "created_at",
        "completed_at",
    )
    list_filter = ("status",)


@admin.register(StatementImport)
class StatementImportAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "period_start",
        "period_end",
        "row_count",
        "new_rows",
        "layout",
    )


@admin.register(ReviewFlag)
class ReviewFlagAdmin(admin.ModelAdmin):
    list_display = ("review", "type", "resolution", "resolved_at")
