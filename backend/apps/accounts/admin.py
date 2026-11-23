from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from apps.accounts.models import User, Role


class CustomUserCreationForm(UserCreationForm):
    """Admin form to safely create users with standard PBKDF2 hashed passwords."""

    class Meta:
        model = User
        fields = ("email", "role")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_verified = True
        user.is_active = True
        if user.role == Role.PLATFORM_ADMIN:
            user.is_staff = True
        else:
            user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """Admin change form for custom user model."""

    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Restricted User Administration in Django Admin.
    Follows least-privilege principles per ARCHITECTURE §5 and Baseline v2.2 §14.1:
    - Subclasses django.contrib.auth.admin.UserAdmin for secure password hashing.
    - Prevents admins from granting superuser status.
    - Prevents users from modifying their own role or deactivating themselves.
    - Generates append-only audit events on all administrative saves.
    """

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ("email", "role", "is_active", "is_verified", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_verified", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login", "updated_at", "version", "is_superuser", "is_staff")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions & Roles", {"fields": ("role", "is_active", "is_verified", "is_staff", "is_superuser")}),
        ("Metadata", {"fields": ("date_joined", "last_login", "updated_at", "version")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "password1", "password2"),
            },
        ),
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

    def get_readonly_fields(self, request, obj=None):
        ro = list(self.readonly_fields)
        # Prevent self role change and self-deactivation
        if obj and obj.pk == request.user.pk:
            if "role" not in ro:
                ro.append("role")
            if "is_active" not in ro:
                ro.append("is_active")
        return tuple(ro)

    def save_model(self, request, obj, form, change):
        # Guard self role change and self-deactivation
        if change and obj.pk == request.user.pk:
            if "role" in form.changed_data:
                raise ValidationError("You cannot change your own role.")
            if "is_active" in form.changed_data and not obj.is_active:
                raise ValidationError("You cannot deactivate your own account.")

        # Ensure is_staff matches role (only platform_admin has is_staff)
        if obj.role == Role.PLATFORM_ADMIN:
            obj.is_staff = True
        else:
            obj.is_staff = False

        # is_superuser must never be granted through Django Admin
        obj.is_superuser = False

        # Build changes diff for audit event
        action = "update" if change else "create"
        changes = {}
        if change:
            for field in form.changed_data:
                if field != "password":
                    changes[field] = {
                        "before": str(form.initial.get(field)),
                        "after": str(form.cleaned_data.get(field)),
                    }
        else:
            changes = {
                "email": {"before": None, "after": obj.email},
                "role": {"before": None, "after": obj.role},
            }

        super().save_model(request, obj, form, change)

        # Audit event record
        from apps.audit.services import record_event

        record_event(
            actor=request.user,
            action=f"admin_{action}",
            obj=obj,
            reason=f"Admin {action} on user {obj.email}.",
            changes=changes,
        )
