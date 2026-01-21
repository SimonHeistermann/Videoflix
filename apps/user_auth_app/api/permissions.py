"""
Custom permission classes for authentication and authorization.

These permissions are used to control access to API endpoints based on
user authentication state and the presence/validity of JWT refresh tokens.
"""

from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class IsActiveUser(BasePermission):
    """
    Permission that allows access only to authenticated and active users.

    This permission ensures that:
    - a user object exists on the request,
    - the user is authenticated,
    - the user's account is marked as active.
    """

    def has_permission(self, request, view):
        """
        Determine whether the request should be permitted.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is authenticated and active, otherwise False.
        """
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_active)


class AuthenticatedViaRefreshToken(BasePermission):
    """
    Permission that allows access only if a valid refresh token cookie exists.

    This is primarily intended for endpoints such as `/api/token/refresh/`,
    where authentication is based on a refresh token stored in cookies
    rather than an access token header.
    """

    message = "Refresh token invalid or missing."

    def has_permission(self, request, view):
        """
        Determine whether the request contains a valid refresh token.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if a valid refresh token cookie exists, otherwise False.
        """
        token = request.COOKIES.get("refresh_token")
        if not token:
            return False

        try:
            RefreshToken(token)
            return True
        except TokenError:
            return False