import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.utils import timezone


class Role(models.TextChoices):
    PLATFORM_ADMIN = "platform_admin", "Platform Administrator"
    COMMERCIAL_ANALYST = "commercial_analyst", "Commercial Analyst"
    REVIEWER = "reviewer", "Reviewer / Approver"


class CustomUserManager(BaseUserManager):
    """Custom user manager supporting UUID PKs and email as primary identifier."""

    def create_user(self, email, password=None, role=Role.COMMERCIAL_ANALYST, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email).lower()

        # If role is platform_admin, grant staff permission by default
        if role == Role.PLATFORM_ADMIN:
            extra_fields.setdefault("is_staff", True)

        user = self.model(email=email, role=role, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            password=password,
            role=Role.PLATFORM_ADMIN,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    """
    InChi Pilot Gateway Custom User Model.
    Uses UUID as the immutable primary key and lowercase email for authentication.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True, max_length=254)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.COMMERCIAL_ANALYST,
        db_index=True,
        help_text="Primary internal application role.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user account is active.",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Designates whether this internal user account has completed verification.",
    )
    verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Security token used for account activation or verification.",
    )

    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into the Django admin site.",
    )
    is_superuser = models.BooleanField(
        default=False,
        help_text="Designates that this user has all permissions without explicitly assigning them.",
    )

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    version = models.PositiveIntegerField(
        default=1,
        help_text="Optimistic concurrency tracking version.",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        # Normalize email
        if self.email:
            self.email = self.email.lower().strip()

        # Derive is_staff from role for platform_admin
        if self.role == Role.PLATFORM_ADMIN:
            self.is_staff = True

        super().save(*args, **kwargs)
