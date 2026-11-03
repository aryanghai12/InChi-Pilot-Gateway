from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.accounts.views import (
    CsrfCookieView,
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    VerifyAccountView,
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

    # Registration & Verification
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("verify/", VerifyAccountView.as_view(), name="auth-verify"),
    path("verify/status/", VerifyAccountView.as_view(), name="auth-verify-status"),

    # User Management (Platform Admin)
    path("", include(router.urls)),
]
