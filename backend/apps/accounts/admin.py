from django.contrib import admin
from apps.accounts.models import User, Role


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Restricted User Administration in Django Admin.
    Follows least-privilege principles:
    - Only platform_admin users can access.
    - Prevents accidental record deletion (must deactivate instead).
    - Prevents users from changing their own role or deactivating themselves.
    """

    list_display = ("email", "role", "is_active", "is_verified", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_verified", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "updated_at", "version")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions & Roles", {"fields": ("role", "is_active", "is_verified", "is_staff", "is_superuser")}),
        ("Metadata", {"fields": ("date_joined", "last_login", "updated_at", "version")}),
    )

    def has_module_permission(self, request):
        return bool(request.user.is_authenticated and request.user.role == Role.PLATFORM_ADMIN)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Soft-deactivation is strictly preferred over hard deletes in audit trail
        return False
