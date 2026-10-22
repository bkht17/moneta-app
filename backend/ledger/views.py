import logging
import time

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BankAccount, Review, ReviewFlag, Transaction
from .parsers import StatementError, parse_pdf
from .serializers import (
    BankAccountSerializer,
    CategorySerializer,
    FlagSerializer,
    ResolveSerializer,
    ReviewSerializer,
    StatementImportSerializer,
    SubmitSerializer,
    UploadSerializer,
)
from .services import intake
from .services.categories import CATEGORIES
from .services.ingest import import_statement
from .services.overview import build_overview
from .services.reconcile import InvalidResolution, open_flags, resolve

logger = logging.getLogger(__name__)


def error(code, message, http_status=status.HTTP_400_BAD_REQUEST, **extra):
    return Response(
        {"errors": [{"code": code, "message": message, **extra}]}, http_status
    )


class BankAccountViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BankAccountSerializer
    queryset = BankAccount.objects.none()  # typing for the schema; real one below
    lookup_value_converter = "uuid"

    def get_queryset(self):
        return self.request.user.accounts.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    queryset = Review.objects.none()  # typing for the schema; real one below
    lookup_value_converter = "uuid"

    def get_queryset(self):
        return self.request.user.reviews.prefetch_related("accounts")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def coverage(self, request, pk=None):
        review = self.get_object()
        result = intake.evaluate_coverage(review)
        return Response(
            {
                "cutoff": result.cutoff,
                "errors": result.errors,
                "accounts": [
                    {
                        "id": str(c.account.id),
                        "label": c.account.label,
                        "bank": c.account.bank,
                        "covered_until": c.covered_until,
                        "starts_late_on": c.starts_late_on,
                        "gap_after": c.gap_after,
                        "statements": StatementImportSerializer(
                            c.statements, many=True
                        ).data,
                    }
                    for c in result.coverages
                ],
            }
        )

    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
    )
    def statements(self, request, pk=None):
        """Upload one PDF statement. It is parsed in memory and then discarded."""
        review = self.get_object()
        if review.status != Review.Status.DRAFT:
            return error("review_locked", "Start a new review to add newer statements.")
        if not request.FILES.get("file"):
            return error(
                "file_missing",
                f"Choose a PDF statement up to {settings.STATEMENT_MAX_BYTES // 2**20} MB.",
            )
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = review.accounts.filter(
            pk=serializer.validated_data["account"]
        ).first()
        if account is None:
            return error("unknown_account", "Declare this account in the review first.")
        upload = serializer.validated_data["file"]
        started = time.perf_counter()
        try:
            parsed = parse_pdf(upload)
            statement = import_statement(account, parsed, upload.name, review=review)
        except StatementError as exc:
            logger.info("statement rejected: %s (%s)", exc.code, account.bank)
            return error(exc.code, str(exc), account=str(account.id))
        finally:
            upload.close()
        # NFR2 evidence: processing time per statement, without any statement content.
        logger.info(
            "statement processed: bank=%s layout=%s rows=%d ms=%d",
            account.bank,
            statement.layout,
            statement.row_count,
            (time.perf_counter() - started) * 1000,
        )
        return Response(
            StatementImportSerializer(statement).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        review = self.get_object()
        if review.status != Review.Status.DRAFT:
            return error("review_locked", "This review is already calculated.")
        data = SubmitSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        errors = intake.submit(
            review,
            data.validated_data.get("cash_kzt"),
            data.validated_data.get("later_cash_kzt"),
            data.validated_data.get("later_cash_until"),
        )
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        review.refresh_from_db()
        return Response(ReviewSerializer(review, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        """Back to draft to add a statement or fix cash. Answers already given stay."""
        review = self.get_object()
        review.status = Review.Status.DRAFT
        review.intake_completed_at = None
        review.completed_at = None
        review.save(update_fields=["status", "intake_completed_at", "completed_at"])
        review.flags.filter(resolved_at__isnull=True).delete()
        return Response(ReviewSerializer(review, context={"request": request}).data)

    @action(detail=True, methods=["get"])
    def flags(self, request, pk=None):
        review = self.get_object()
        return Response(FlagSerializer(open_flags(review), many=True).data)

    @action(detail=True, methods=["get"])
    def overview(self, request, pk=None):
        review = self.get_object()
        if review.status == Review.Status.DRAFT:
            return error(
                "intake_incomplete",
                "Finish adding statements and cash first.",
                status.HTTP_409_CONFLICT,
            )
        if review.status == Review.Status.NEEDS_CONFIRMATION:
            return error(
                "unresolved_flags",
                "Answer the flagged items before the total is shown.",
                status.HTTP_409_CONFLICT,
                count=review.flags.filter(resolved_at__isnull=True).count(),
            )
        if review.overview_opened_at is None:
            review.overview_opened_at = timezone.now()
            review.save(update_fields=["overview_opened_at"])
        return Response(build_overview(review))


class FlagResolveView(APIView):
    @extend_schema(request=ResolveSerializer, responses=OpenApiTypes.OBJECT)
    def post(self, request, pk):
        flag = get_object_or_404(ReviewFlag, pk=pk, review__user=request.user)
        data = ResolveSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            resolve(flag, data.validated_data["resolution"])
        except InvalidResolution as exc:
            return error("invalid_resolution", str(exc))
        flag.review.refresh_from_db()
        return Response(
            {
                "flag": FlagSerializer(flag).data,
                "review_status": flag.review.status,
            }
        )


class TransactionCategoryView(APIView):
    """Change a category. Category totals move; total spending does not (F2)."""

    @extend_schema(request=CategorySerializer, responses=CategorySerializer)
    def patch(self, request, pk):
        tx = get_object_or_404(Transaction, pk=pk, account__user=request.user)
        serializer = CategorySerializer(tx, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(category_set_by_user=True)
        return Response(serializer.data)


class CategoryListView(APIView):
    @extend_schema(responses={200: OpenApiTypes.STR})
    def get(self, request):
        return Response(CATEGORIES)
