import os
import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password
from apps.accounts.models import User, Role


class Command(BaseCommand):
    help = "Safely creates the initial Platform Administrator user with least-privilege credentials."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, required=True, help="Administrator email address")
        parser.add_argument("--password", type=str, required=False, help="Administrator password (optional, reads from env or prompt)")
        parser.add_argument("--allow-additional", action="store_true", help="Allow creating additional platform administrators")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options.get("password")
        allow_additional = options.get("allow_additional", False)

        # Check existing admin accounts
        existing_admins = User.objects.filter(role=Role.PLATFORM_ADMIN).count()
        if existing_admins > 0 and not allow_additional:
            raise CommandError(
                f"A Platform Administrator already exists ({existing_admins} found). "
                "Use --allow-additional if you explicitly intend to create more."
            )

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f"A user with email '{email}' already exists.")

        # Resolve password
        if not password:
            password = os.getenv("INITIAL_ADMIN_PASSWORD")

        if not password:
            password = getpass.getpass(f"Enter password for Platform Admin ({email}): ")
            password_confirm = getpass.getpass("Confirm password: ")
            if password != password_confirm:
                raise CommandError("Passwords do not match.")

        # Validate password strength
        try:
            validate_password(password)
        except Exception as e:
            raise CommandError(f"Password validation failed: {e}")

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            role=Role.PLATFORM_ADMIN,
            is_staff=True,
            is_superuser=False,
            is_verified=True,
            is_active=True,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created Platform Administrator: {user.email} (ID: {user.id})")
        )
