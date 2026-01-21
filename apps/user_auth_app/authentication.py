"""
Custom authentication backend(s) for JWT stored in cookies.

This module contains an authentication class that can authenticate requests
using a JWT access token stored in an HttpOnly cookie. If the cookie is
missing or the token is invalid/expired, the request remains unauthenticated.
"""

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticate using the access token stored in an HttpOnly cookie.

    Behavior:
        - No cookie: returns None (unauthenticated)
        - Invalid/expired token: returns None (unauthenticated)
        - Valid token: returns (user, validated_token)
    """

    def authenticate(self, request):
        """
        Authenticate the request using an access token from cookies or header.

        Args:
            request: The incoming HTTP request.

        Returns:
            tuple | None: (user, validated_token) if authentication succeeds,
            otherwise None.
        """
        raw_token = self._get_raw_token(request)
        if not raw_token:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
        except (InvalidToken, TokenError):
            return None

        return (user, validated_token)

    def _get_raw_token(self, request):
        """
        Retrieve the raw JWT token either from the access cookie or from the
        Authorization header.

        Args:
            request: The incoming HTTP request.

        Returns:
            str | None: The raw token if found, otherwise None.
        """
        cookie_name = self._access_cookie_name()
        token = request.COOKIES.get(cookie_name)
        if token:
            return token

        header = self.get_header(request)
        if not header:
            return None

        return self.get_raw_token(header)

    def _access_cookie_name(self):
        """
        Build the configured access cookie name, honoring AUTH_COOKIE_PREFIX.

        Returns:
            str: The cookie key that stores the access token.
        """
        prefix = getattr(settings, "AUTH_COOKIE_PREFIX", "") or ""
        return f"{prefix}access_token"