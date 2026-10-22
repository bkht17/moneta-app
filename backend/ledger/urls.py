from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BankAccountViewSet,
    CategoryListView,
    FlagResolveView,
    ReviewViewSet,
    TransactionCategoryView,
)

router = DefaultRouter()
router.register("accounts", BankAccountViewSet, basename="account")
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = [
    path("flags/<uuid:pk>/resolve/", FlagResolveView.as_view(), name="flag-resolve"),
    path(
        "transactions/<uuid:pk>/",
        TransactionCategoryView.as_view(),
        name="transaction-category",
    ),
    path("categories/", CategoryListView.as_view(), name="categories"),
    *router.urls,
]
