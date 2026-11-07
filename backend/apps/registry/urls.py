from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.registry.views import (
    SupplierViewSet,
    ProductViewSet,
    EvidenceItemViewSet,
)

router = DefaultRouter()
router.register(r"suppliers", SupplierViewSet, basename="supplier")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"evidence", EvidenceItemViewSet, basename="evidence")

urlpatterns = [
    path("", include(router.urls)),
]
