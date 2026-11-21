from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.readiness.views import ReadinessAssessmentViewSet, AssessmentEvidenceViewSet

router = DefaultRouter()
router.register(r"assessments", ReadinessAssessmentViewSet, basename="assessment")
router.register(r"assessment-evidence", AssessmentEvidenceViewSet, basename="assessment-evidence")

urlpatterns = [
    path("", include(router.urls)),
]
