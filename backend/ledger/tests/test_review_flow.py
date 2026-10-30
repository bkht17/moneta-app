"""Acceptance criteria from Assignment 7 as executable checks against the reference
ledger in ledger/samples.py (budget 100,000 ₸, cash 8,000 ₸)."""

from datetime import date
from decimal import Decimal

from ledger.models import BankAccount, Review, ReviewFlag, StatementImport, Transaction
from ledger.parsers import parse_lines
from ledger.samples import find_font, halyk_lines, kaspi_lines, write_pdf
from ledger.services.ingest import import_statement


def submit(client, review, **data):
    return client.post(f"/api/reviews/{review.id}/submit/", data, format="json")


def answer_all(client, review, duplicate="keep_both", transfer="own_transfer"):
    flags = client.get(f"/api/reviews/{review.id}/flags/").json()
    for flag in flags:
        resolution = duplicate if flag["type"] == "possible_duplicate" else transfer
        response = client.post(
            f"/api/flags/{flag['id']}/resolve/",
            {"resolution": resolution},
            format="json",
        )
        assert response.status_code == 200
    return flags


def overview(client, review):
    return client.get(f"/api/reviews/{review.id}/overview/")


def codes(response):
    return {e["code"] for e in response.json()["errors"]}


# --- F1: intake -------------------------------------------------------------------


class TestF1Intake:
    def test_ac1_complete_inputs_start_calculation_at_common_cutoff(
        self, client, imported
    ):
        response = submit(client, imported, cash_kzt="8000")

        assert response.status_code == 200
        body = response.json()
        assert body["cutoff_date"] == "2026-10-15"
        assert body["intake_completed_at"] is not None
        assert body["status"] == "needs_confirmation"

    def test_ac1_explicit_zero_cash_is_accepted(self, client, imported):
        assert submit(client, imported, cash_kzt="0").status_code == 200

    def test_ac2_blank_cash_blocks_calculation(self, client, imported):
        for blank in ("", None):
            response = submit(client, imported, cash_kzt=blank)
            assert response.status_code == 400
            assert "cash_missing" in codes(response)
        imported.refresh_from_db()
        assert imported.intake_completed_at is None
        assert imported.flags.count() == 0

    def test_ac2_missing_statement_is_named(self, client, review, accounts):
        kaspi, halyk = accounts
        import_statement(kaspi, parse_lines(kaspi_lines()), "kaspi.pdf", review)

        response = submit(client, review, cash_kzt="8000")

        assert response.status_code == 400
        errors = response.json()["errors"]
        assert errors[0]["code"] == "missing_statement"
        assert errors[0]["account"] == str(halyk.id)

    def test_ac2_statement_starting_after_month_start_is_a_gap(
        self, client, review, accounts
    ):
        kaspi, halyk = accounts
        lines = [line.replace("с 01.10.26", "с 03.10.26") for line in kaspi_lines()]
        import_statement(kaspi, parse_lines(lines), "kaspi.pdf", review)
        import_statement(halyk, parse_lines(halyk_lines()), "h.pdf", review)

        response = submit(client, review, cash_kzt="8000")

        assert "coverage_gap" in codes(response)

    def test_ac2_negative_cash_and_errors_are_reported_together(self, client, review):
        response = submit(client, review, cash_kzt="-5")
        assert {"missing_statement", "invalid_amount"} <= codes(response)

    def test_unsupported_file_is_rejected_on_upload(self, client, review, accounts):
        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile("photo.png", b"\x89PNG not a pdf", "image/png")
        response = client.post(
            f"/api/reviews/{review.id}/statements/",
            {"account": str(accounts[0].id), "file": upload},
            format="multipart",
        )
        assert response.status_code == 400
        assert codes(response) == {"not_pdf"}

    def test_pdf_upload_is_parsed_in_memory(self, client, review, accounts, tmp_path):
        import pytest
        from django.core.files.uploadedfile import SimpleUploadedFile

        pytest.importorskip("reportlab")
        if not find_font():
            pytest.skip("No Cyrillic font available to build the sample PDF")
        path = tmp_path / "kaspi.pdf"
        write_pdf(kaspi_lines(), path)
        upload = SimpleUploadedFile("kaspi.pdf", path.read_bytes(), "application/pdf")

        response = client.post(
            f"/api/reviews/{review.id}/statements/",
            {"account": str(accounts[0].id), "file": upload},
            format="multipart",
        )

        assert response.status_code == 201, response.json()
        assert response.json()["row_count"] == 8
        assert response.json()["period_end"] == "2026-10-15"
        accounts[0].refresh_from_db()
        assert accounts[0].last4 == "1234"

    def test_statement_for_the_wrong_bank_is_rejected(self, review, accounts):
        import pytest

        from ledger.services.ingest import AccountMismatch

        with pytest.raises(AccountMismatch):
            import_statement(accounts[1], parse_lines(kaspi_lines()), "k.pdf", review)


# --- F2: combine and check --------------------------------------------------------


class TestF2Combine:
    def test_ac2_nothing_is_removed_silently_and_total_is_withheld(
        self, client, imported
    ):
        submit(client, imported, cash_kzt="8000")

        flags = client.get(f"/api/reviews/{imported.id}/flags/").json()
        assert sorted(f["type"] for f in flags) == [
            "possible_duplicate",
            "possible_own_transfer",
        ]
        assert Transaction.objects.filter(description="Coffee Boom").count() == 3
        response = overview(client, imported)
        assert response.status_code == 409
        assert codes(response) == {"unresolved_flags"}

    def test_ac1_reference_ledger(self, client, imported):
        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported)

        body = overview(client, imported).json()

        assert body["spending"] == 35000
        categories = {c["name"]: c["amount"] for c in body["categories"]}
        assert categories["Cash, unspecified"] == 8000
        assert categories["Cafés"] == 6900
        assert "Own transfers" not in categories
        assert body["withdrawals"] == 10000
        assert body["own_transfers"] == 20000
        assert body["income"] == 42000

    def test_same_purchase_answer_removes_one_coffee(self, client, imported):
        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported, duplicate="same_purchase")

        assert overview(client, imported).json()["spending"] == 33800

    def test_not_own_transfer_counts_as_spending_and_income(self, client, imported):
        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported, transfer="not_own_transfer")

        body = overview(client, imported).json()
        assert body["spending"] == 55000
        assert body["income"] == 62000

    def test_repeat_import_adds_nothing(self, client, imported, accounts):
        before = Transaction.objects.count()
        statement = import_statement(
            accounts[0], parse_lines(kaspi_lines()), "kaspi-again.pdf", imported
        )
        assert statement.new_rows == 0
        assert Transaction.objects.count() == before

        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported)
        assert overview(client, imported).json()["spending"] == 35000

    def test_category_change_keeps_total(self, client, imported):
        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported)
        glovo = Transaction.objects.get(description="Glovo")

        response = client.patch(
            f"/api/transactions/{glovo.id}/", {"category": "Cafés"}, format="json"
        )

        assert response.status_code == 200
        body = overview(client, imported).json()
        categories = {c["name"]: c["amount"] for c in body["categories"]}
        assert body["spending"] == 35000
        assert categories["Cafés"] == 11500
        assert "Food delivery" not in categories

    def test_wrong_answer_type_is_rejected(self, client, imported):
        submit(client, imported, cash_kzt="8000")
        flag = imported.flags.get(type=ReviewFlag.Type.POSSIBLE_DUPLICATE)
        response = client.post(
            f"/api/flags/{flag.id}/resolve/",
            {"resolution": "own_transfer"},
            format="json",
        )
        assert response.status_code == 400


# --- F3: overview -----------------------------------------------------------------


class TestF3Overview:
    def test_ac1_remaining_budget_and_coverage(self, client, imported):
        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported)

        body = overview(client, imported).json()

        assert body["remaining"] == 65000
        assert body["period"] == {"start": "2026-10-01", "end": "2026-10-15"}
        covered = {a["label"]: a["covered_until"] for a in body["accounts"]}
        assert covered == {"Kaspi Gold": "2026-10-15", "Halyk card": "2026-10-18"}
        assert imported.__class__.objects.get(pk=imported.pk).overview_opened_at

    def test_ac2_rows_after_cutoff_stay_outside_the_total(self, client, imported):
        submit(
            client,
            imported,
            cash_kzt="8000",
            later_cash_kzt="1500",
            later_cash_until="2026-10-18",
        )
        answer_all(client, imported)

        body = overview(client, imported).json()

        outside = body["outside"]
        assert [t["date"] for t in outside["transactions"]] == [
            "2026-10-16",
            "2026-10-17",
            "2026-10-18",
        ]
        assert outside["bank_spending"] == 4300
        assert outside["cash"] == 1500
        assert body["spending"] == 35000
        assert body["remaining"] == 65000

    def test_extended_coverage_counts_later_rows_once(
        self, client, imported, user, accounts
    ):
        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported)

        newer = Review.objects.create(
            user=user, month=date(2026, 10, 1), budget_kzt=Decimal("100000")
        )
        newer.accounts.set(accounts)
        lines = [
            line.replace("по 15.10.26", "по 18.10.26") for line in kaspi_lines()
        ] + ["17.10.26 - 900,00 ₸ Покупка Coffee Boom"]
        import_statement(accounts[0], parse_lines(lines), "kaspi-18.pdf", newer)

        response = submit(client, newer, cash_kzt="9000")
        assert response.json()["cutoff_date"] == "2026-10-18"
        # Answers from the first review still apply: nothing new to confirm.
        assert response.json()["status"] == "complete"

        body = overview(client, newer).json()
        assert body["spending"] == 35000 - 8000 + 9000 + 4300 + 900
        assert body["outside"]["transactions"] == []


# --- NFR1: privacy ----------------------------------------------------------------


class TestNFR1Privacy:
    def test_no_model_stores_files(self):
        from django.apps import apps
        from django.db.models import FileField

        for model in apps.get_app_config("ledger").get_models():
            assert not any(isinstance(f, FileField) for f in model._meta.get_fields())

    def test_uploads_never_spool_to_disk(self, settings):
        assert settings.FILE_UPLOAD_HANDLERS == [
            "django.core.files.uploadhandler.MemoryFileUploadHandler"
        ]

    def test_delete_my_data_removes_everything(self, client, imported):
        submit(client, imported, cash_kzt="8000")

        assert client.delete("/api/auth/me/").status_code == 204

        assert BankAccount.objects.count() == 0
        assert Review.objects.count() == 0
        assert StatementImport.objects.count() == 0
        assert Transaction.objects.count() == 0
        assert ReviewFlag.objects.count() == 0

    def test_other_users_cannot_read_a_review(self, imported, db):
        from rest_framework.test import APIClient

        from users.models import User

        stranger = User.objects.create_user("other@example.test", "another-pass-77")
        api = APIClient()
        api.force_authenticate(stranger)
        assert api.get(f"/api/reviews/{imported.id}/").status_code == 404


# --- One account and unfinished reviews ------------------------------------------


class TestSingleAccount:
    def test_review_with_one_account_reaches_the_overview(self, client, user, accounts):
        kaspi = accounts[0]
        created = client.post(
            "/api/reviews/",
            {"month": "2026-10-01", "budget_kzt": 100000, "accounts": [str(kaspi.id)]},
            format="json",
        )
        assert created.status_code == 201
        review = Review.objects.get(pk=created.json()["id"])
        import_statement(kaspi, parse_lines(kaspi_lines()), "kaspi.pdf", review)

        response = submit(client, review, cash_kzt="8000")
        assert response.status_code == 200
        assert response.json()["cutoff_date"] == "2026-10-15"
        flags = answer_all(client, review)
        # With one account there is no second side for an own-account transfer.
        assert [f["type"] for f in flags] == ["possible_duplicate"]

        body = overview(client, review).json()
        categories = {c["name"]: c["amount"] for c in body["categories"]}
        assert [a["label"] for a in body["accounts"]] == ["Kaspi Gold"]
        assert body["spending"] == 43000
        assert categories["Transfers to people"] == 20000
        assert body["remaining"] == 57000

    def test_removing_an_account_without_a_statement_unblocks_intake(
        self, client, review, accounts
    ):
        kaspi, halyk = accounts
        import_statement(kaspi, parse_lines(kaspi_lines()), "kaspi.pdf", review)
        assert "missing_statement" in codes(submit(client, review, cash_kzt="8000"))

        response = client.patch(
            f"/api/reviews/{review.id}/", {"accounts": [str(kaspi.id)]}, format="json"
        )
        assert response.status_code == 200
        assert submit(client, review, cash_kzt="8000").status_code == 200

    def test_review_needs_at_least_one_account(self, client):
        response = client.post(
            "/api/reviews/",
            {"month": "2026-10-01", "budget_kzt": 100000, "accounts": []},
            format="json",
        )
        assert response.status_code == 400
        assert "accounts" in response.json()


class TestUnfinishedReviews:
    def test_history_filter_returns_only_complete_reviews(self, client, imported, user):
        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported)
        draft = Review.objects.create(
            user=user, month=date(2026, 10, 1), budget_kzt=Decimal("100000")
        )

        complete = client.get("/api/reviews/?status=complete").json()
        unfinished = client.get("/api/reviews/?status=draft,needs_confirmation").json()

        assert [r["id"] for r in complete] == [str(imported.id)]
        assert [r["id"] for r in unfinished] == [str(draft.id)]

    def test_finished_review_lists_only_statements_it_was_built_from(
        self, client, imported, accounts
    ):
        submit(client, imported, cash_kzt="8000")
        answer_all(client, imported)
        import_statement(accounts[0], parse_lines(kaspi_lines()), "later.pdf")

        body = client.get(f"/api/reviews/{imported.id}/").json()
        files = [st["file_name"] for s in body["sources"] for st in s["statements"]]
        assert "later.pdf" not in files

    def test_each_review_names_its_accounts_and_statements(self, client, imported):
        body = client.get(f"/api/reviews/{imported.id}/").json()

        sources = {s["label"]: s for s in body["sources"]}
        assert set(sources) == {"Kaspi Gold", "Halyk card"}
        assert sources["Kaspi Gold"]["statements"] == [
            {
                "file_name": "kaspi.pdf",
                "period_start": "2026-10-01",
                "period_end": "2026-10-15",
            }
        ]

    def test_a_draft_can_be_discarded(self, client, review):
        assert client.delete(f"/api/reviews/{review.id}/").status_code == 204
        assert not Review.objects.filter(pk=review.id).exists()
