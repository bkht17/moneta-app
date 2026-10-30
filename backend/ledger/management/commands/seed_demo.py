from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ledger.models import BankAccount, Review
from ledger.parsers import parse_lines
from ledger.samples import halyk_lines, kaspi_lines
from ledger.services.ingest import import_statement
from users.models import User

DEMO_EMAIL = "demo@moneta.test"


class Command(BaseCommand):
    help = (
        "Create a demo student with the synthetic October statements imported and a "
        "draft review waiting for the cash amount. Replaces an existing demo user."
    )

    def add_arguments(self, parser):
        parser.add_argument("--password", default="moneta-demo-2026")
        parser.add_argument(
            "--kaspi-last4",
            default="",
            help="Card ending for the demo Kaspi account, so a real statement for that "
            "card can be uploaded to it. Defaults to the sample statement's card.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User.objects.filter(email=DEMO_EMAIL).delete()
        user = User.objects.create_user(
            DEMO_EMAIL, options["password"], full_name="Demo Student"
        )
        kaspi = BankAccount.objects.create(user=user, bank="kaspi", label="Kaspi Gold")
        halyk = BankAccount.objects.create(user=user, bank="halyk", label="Halyk card")
        review = Review.objects.create(
            user=user, month=date(2026, 10, 1), budget_kzt=Decimal("100000")
        )
        review.accounts.set([kaspi, halyk])
        import_statement(
            kaspi, parse_lines(kaspi_lines()), "kaspi_gold_sample.pdf", review
        )
        import_statement(
            halyk, parse_lines(halyk_lines()), "halyk_card_sample.pdf", review
        )
        if options["kaspi_last4"]:
            kaspi.last4 = options["kaspi_last4"]
            kaspi.save(update_fields=["last4"])
        self.stdout.write(
            self.style.SUCCESS(f"Demo user {DEMO_EMAIL} ready (review {review.id}).")
        )
