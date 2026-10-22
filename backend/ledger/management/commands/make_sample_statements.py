from pathlib import Path

from django.core.management.base import BaseCommand

from ledger.samples import halyk_lines, kaspi_lines, write_pdf


class Command(BaseCommand):
    help = "Write synthetic Kaspi and Halyk PDF statements for demos and parser checks."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="samples", help="Output folder")
        parser.add_argument("--font", default=None, help="Cyrillic TrueType font path")

    def handle(self, *args, **options):
        out = Path(options["out"])
        out.mkdir(parents=True, exist_ok=True)
        files = {
            "kaspi_gold_sample.pdf": kaspi_lines(),
            "halyk_card_sample.pdf": halyk_lines(),
        }
        for name, lines in files.items():
            write_pdf(lines, out / name, options["font"])
            self.stdout.write(self.style.SUCCESS(f"Wrote {out / name}"))
