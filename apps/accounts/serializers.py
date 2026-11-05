import uuid
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from apps.accounts.models import User, Role


class UserSerializer(serializers.ModelSerializer):
    """Public profile serializer for authenticated users and administration."""

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_display",
            "is_active",
            "is_verified",
            "is_staff",
            "date_joined",
            "last_login",
            "version",
        ]
        read_only_fields = [
            "id",
            "role_display",
            "is_staff",
            "date_joined",
            "last_login",
            "version",
        ]


class LoginSerializer(serializers.Serializer):
    """Serializer for authenticating existing internal users."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated. Please contact an administrator.")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new internal users.
    Generates a secure verification token for the verification workflow.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    role = serializers.ChoiceField(choices=Role.choices, default=Role.COMMERCIAL_ANALYST)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        # Generate verification token
        verification_token = str(uuid.uuid4())

        user = User.objects.create_user(
            password=password,
            is_verified=False,
            verification_token=verification_token,
            **validated_data,
        )
        return user


class VerifyAccountSerializer(serializers.Serializer):
    """Serializer to verify internal user accounts using a token."""

    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get("email", "").strip().lower()
        token = attrs.get("token", "").strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No account matches the provided email.")

        if user.is_verified:
            raise serializers.ValidationError("This account is already verified.")

        if not user.verification_token or user.verification_token != token:
            raise serializers.ValidationError("Invalid or expired verification token.")

        attrs["user"] = user
        return attrs


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for Platform Administrators to update user role or status."""

    class Meta:
        model = User
        fields = ["role", "is_active", "is_verified", "first_name", "last_name", "version"]

    def validate_version(self, value):
        if self.instance and value != self.instance.version:
            raise serializers.ValidationError(
                "This user record has been modified by another process. Please refresh and try again."
            )
        return value

    def update(self, instance, validated_data):
        # Increment version for optimistic concurrency
        validated_data["version"] = instance.version + 1
        return super().update(instance, validated_data)
