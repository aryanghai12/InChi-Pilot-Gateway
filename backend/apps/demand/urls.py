from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.demand.views import BuyerRequirementViewSet

router = DefaultRouter()
router.register(r"requirements", BuyerRequirementViewSet, basename="requirement")

urlpatterns = [
    path("", include(router.urls)),
]
