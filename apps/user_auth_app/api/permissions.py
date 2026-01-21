from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class IsActiveUser(BasePermission):
    """
    Allows access only to authenticated users with an active account.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_active)


class AuthenticatedViaRefreshToken(BasePermission):
    """
    Allows access only if a valid refresh_token cookie exists.
    Useful for /api/token/refresh/.
    """

    message = "Refresh token invalid or missing."

    def has_permission(self, request, view):
        token = request.COOKIES.get("refresh_token")
        if not token:
            return False

        try:
            RefreshToken(token)
            return True
        except TokenError:
            return False