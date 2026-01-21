from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from ..tasks import send_activation_email, send_passwordreset_email
from ..utils import (
    build_frontend_link,
    build_uid_and_token,
    delete_auth_cookies,
    enqueue_after_commit,
    get_user_from_uid,
    register_response,
    set_access_cookie,
    set_auth_cookies,
    try_get_user_by_email,
    cookie_name,
)
from .permissions import AuthenticatedViaRefreshToken
from .serializers import ActivateSerializer, LoginSerializer, PasswordConfirmSerializer, RegisterSerializer

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        uidb64, token = build_uid_and_token(user)
        activation_link = build_frontend_link("activate", uidb64, token)
        enqueue_after_commit(send_activation_email, user.email, activation_link)

        return Response(register_response(user, token), status=status.HTTP_201_CREATED)


class ActivateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        user = get_user_from_uid(uidb64)
        if not user:
            return Response({"message": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"message": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_active:
            return Response({"message": "User is already activated."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ActivateSerializer(user, data={}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response({"message": "Email or Password wrong"}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        refresh = serializer.validated_data["refresh"]
        access = serializer.validated_data["access"]

        response = Response(
            {"detail": "Login successful", "user": {"id": user.id, "username": user.email}},
            status=status.HTTP_200_OK,
        )
        set_auth_cookies(response, str(access), str(refresh))
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(cookie_name("refresh"))
        if not refresh_token:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            RefreshToken(refresh_token).blacklist()
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)

        response = Response(
            {"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK,
        )
        delete_auth_cookies(response)
        return response


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AuthenticatedViaRefreshToken]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(cookie_name("refresh"))
        if not refresh_token:
            return Response({"detail": "Refresh token not found."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except (ValidationError, TokenError):
            return Response({"detail": "Refresh token is invalid"}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get("access")
        response = Response({"detail": "Token refreshed", "access": access_token}, status=status.HTTP_200_OK)
        set_access_cookie(response, access_token)
        return response


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = (request.data.get("email") or "").strip()

        user = try_get_user_by_email(email)
        if user:
            uidb64, token = build_uid_and_token(user)
            reset_link = build_frontend_link("reset", uidb64, token)
            enqueue_after_commit(send_passwordreset_email, user.email, reset_link)

        return Response({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)


class PasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        user = get_user_from_uid(uidb64)
        if not user:
            return Response({"detail": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordConfirmSerializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)