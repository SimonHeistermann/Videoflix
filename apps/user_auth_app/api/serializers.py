from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

GENERIC_INPUT_ERROR = "Please check your input and try again."
GENERIC_AUTH_ERROR = "Email or Password wrong"


class RegisterSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirmed_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        self._validate_passwords(attrs)
        self._validate_email_available(attrs.get("email"))
        self._validate_password_strength(attrs.get("password"))
        return attrs

    def create(self, validated_data):
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
        if attrs.get("password") != attrs.get("confirmed_password"):
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})

    def _validate_email_available(self, email):
        if not email or User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})

    def _validate_password_strength(self, password):
        try:
            validate_password(password)
        except DjangoValidationError:
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})


class ActivateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["is_active"]

    def update(self, instance, validated_data):
        instance.is_active = True
        instance.save(update_fields=["is_active"])
        return instance


class LoginSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)

    def validate(self, attrs):
        user = self._get_user(attrs.get("email"))
        self._check_password(user, attrs.get("password"))
        self._check_active(user)
        data = super().validate({"username": user.username, "password": attrs.get("password")})
        data["user"] = user
        return data

    def _get_user(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": GENERIC_AUTH_ERROR})

    def _check_password(self, user, password):
        if not user.check_password(password):
            raise serializers.ValidationError({"detail": GENERIC_AUTH_ERROR})

    def _check_active(self, user):
        if not user.is_active:
            raise serializers.ValidationError({"detail": GENERIC_AUTH_ERROR})


class PasswordConfirmSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["new_password", "confirm_password"]

    def validate(self, attrs):
        self._validate_passwords(attrs)
        self._validate_password_strength(attrs.get("new_password"))
        return attrs

    def update(self, instance, validated_data):
        new_password = validated_data.get("new_password")
        instance.set_password(new_password)
        instance.save(update_fields=["password"])
        return instance

    def _validate_passwords(self, attrs):
        if attrs.get("new_password") != attrs.get("confirm_password"):
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})

    def _validate_password_strength(self, password):
        try:
            validate_password(password)
        except DjangoValidationError:
            raise serializers.ValidationError({"detail": GENERIC_INPUT_ERROR})