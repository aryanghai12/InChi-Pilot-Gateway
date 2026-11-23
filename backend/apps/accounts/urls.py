from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.accounts.views import (
    CsrfCookieView,
    LoginView,
    LogoutView,
    MeView,
    UserManagementViewSet,
)

router = DefaultRouter()
router.register(r"users", UserManagementViewSet, basename="user-management")

urlpatterns = [
    # Auth Lifecycle
    path("csrf/", CsrfCookieView.as_view(), name="auth-csrf"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("me/", MeView.as_view(), name="auth-me"),

    # User Management (Platform Admin only per D-12)
    path("", include(router.urls)),
]
