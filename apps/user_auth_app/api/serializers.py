"""
Serializers for user authentication and account management.

This module contains serializers for:
- user registration,
- account activation,
- login (JWT-based),
- password reset and confirmation.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

GENERIC_INPUT_ERROR = "Please check your input and try again."
GENERIC_AUTH_ERROR = "Email or Password wrong"


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Handles email uniqueness, password confirmation,
    and Django password strength validation.
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirmed_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        """
        Validate registration input.

        Ensures matching passwords, email availability,
        and sufficient password strength.

        Args:
            attrs (dict): Incoming serializer attributes.

        Returns:
            dict: Validated attributes.
        """
        self._validate_passwords(attrs)
        self._validate_email_available(attrs.get("email"))
        self._validate_password_strength(attrs.get("password"))
        return attrs

    def create(self, validated_data):
        """
        Create a new inactive user instance.

        Args:
            validated_data (dict): Validated serializer data.

        Returns:
            User: Newly created user instance.
        """
        validated_data.pop("confirmed_password", None)
        email = validated_data.get("email")
        password = validated_data.get("password")
        return User.objects.create_user(
            username=email,
            email=email,
            password=password,
            is_active=False,
        )

    def _validate_passwords(self, attrs):
        """
        Ensure password and confirmation password match.

        Raises:
            serializers.ValidationError: If passwords do not match.
        """
        if attrs.get("password") != attrs.get("confirmed_password"):
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})

    def _validate_email_available(self, email):
        """
        Ensure the email is provided and not already in use.

        Raises:
            serializers.ValidationError: If email is missing or already exists.
        """
        if not email or User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})

    def _validate_password_strength(self, password):
        """
        Validate password strength using Django validators.

        Raises:
            serializers.ValidationError: If password does not meet requirements.
        """
        try:
            validate_password(password)
        except DjangoValidationError:
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})


class ActivateSerializer(serializers.ModelSerializer):
    """
    Serializer used to activate a user account.
    """

    class Meta:
        model = User
        fields = ["is_active"]

    def update(self, instance, validated_data):
        """
        Activate the given user instance.

        Args:
            instance (User): User instance to update.
            validated_data (dict): Validated data (unused).

        Returns:
            User: Updated user instance.
        """
        instance.is_active = True
        instance.save(update_fields=["is_active"])
        return instance


class LoginSerializer(TokenObtainPairSerializer):
    """
    Custom JWT login serializer using email instead of username.

    Adds additional checks for password correctness
    and active user status.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        """
        Initialize serializer and remove the username field.
        """
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)

    def validate(self, attrs):
        """
        Validate login credentials and generate JWT tokens.

        Args:
            attrs (dict): Incoming login data.

        Returns:
            dict: Token data including user reference.
        """
        user = self._get_user(attrs.get("email"))
        self._check_password(user, attrs.get("password"))
        self._check_active(user)

        data = super().validate(
            {"username": user.username, "password": attrs.get("password")}
        )
        data["user"] = user
        return data

    def _get_user(self, email):
        """
        Retrieve a user by email.

        Raises:
            serializers.ValidationError: If user does not exist.
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": GENERIC_AUTH_ERROR})

    def _check_password(self, user, password):
        """
        Validate the user's password.

        Raises:
            serializers.ValidationError: If password is incorrect.
        """
        if not user.check_password(password):
            raise serializers.ValidationError({"detail": GENERIC_AUTH_ERROR})

    def _check_active(self, user):
        """
        Ensure the user account is active.

        Raises:
            serializers.ValidationError: If user is inactive.
        """
        if not user.is_active:
            raise serializers.ValidationError({"detail": GENERIC_AUTH_ERROR})


class PasswordConfirmSerializer(serializers.ModelSerializer):
    """
    Serializer for confirming and setting a new password.
    """

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["new_password", "confirm_password"]

    def validate(self, attrs):
        """
        Validate new password input.

        Args:
            attrs (dict): Incoming serializer data.

        Returns:
            dict: Validated attributes.
        """
        self._validate_passwords(attrs)
        self._validate_password_strength(attrs.get("new_password"))
        return attrs

    def update(self, instance, validated_data):
        """
        Update the user's password.

        Args:
            instance (User): User instance to update.
            validated_data (dict): Validated password data.

        Returns:
            User: Updated user instance.
        """
        new_password = validated_data.get("new_password")
        instance.set_password(new_password)
        instance.save(update_fields=["password"])
        return instance

    def _validate_passwords(self, attrs):
        """
        Ensure new password and confirmation match.

        Raises:
            serializers.ValidationError: If passwords do not match.
        """
        if attrs.get("new_password") != attrs.get("confirm_password"):
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})

    def _validate_password_strength(self, password):
        """
        Validate password strength using Django validators.

        Raises:
            serializers.ValidationError: If password is too weak.
        """
        try:
            validate_password(password)
        except DjangoValidationError:
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})