"""
Tests for custom permission classes.

Includes:
- IsActiveUser
- AuthenticatedViaRefreshToken
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user_auth_app.api.permissions import IsActiveUser, AuthenticatedViaRefreshToken

User = get_user_model()


class DummyView(APIView):
    """
    Minimal DRF view used solely for permission testing.
    """

    pass


class TestIsActiveUserPermission(TestCase):
    """
    Tests for IsActiveUser permission.
    """

    def setUp(self):
        """
        Prepare request factory, permission instance, and dummy view.
        """
        self.factory = APIRequestFactory()
        self.perm = IsActiveUser()
        self.view = DummyView()

    def test_denies_when_no_user(self):
        """
        Permission should deny access if request.user is None.
        """
        request = self.factory.get("/")
        request.user = None
        self.assertFalse(self.perm.has_permission(request, self.view))

    def test_denies_when_not_authenticated(self):
        """
        Permission should deny access if user is not authenticated.
        """
        request = self.factory.get("/")

        class Anon:
            is_authenticated = False
            is_active = False

        request.user = Anon()
        self.assertFalse(self.perm.has_permission(request, self.view))

    def test_denies_when_inactive(self):
        """
        Permission should deny access if user is authenticated but inactive.
        """
        user = User.objects.create_user(
            username="u1",
            email="u1@example.com",
            password="Passw0rd!!",
            is_active=False,
        )
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.perm.has_permission(request, self.view))

    def test_allows_when_active(self):
        """
        Permission should allow access if user is authenticated and active.
        """
        user = User.objects.create_user(
            username="u2",
            email="u2@example.com",
            password="Passw0rd!!",
            is_active=True,
        )
        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.perm.has_permission(request, self.view))


class TestAuthenticatedViaRefreshTokenPermission(TestCase):
    """
    Tests for AuthenticatedViaRefreshToken permission.
    """

    def setUp(self):
        """
        Prepare request factory, permission instance, and dummy view.
        """
        self.factory = APIRequestFactory()
        self.perm = AuthenticatedViaRefreshToken()
        self.view = DummyView()

    def test_denies_when_missing_cookie(self):
        """
        Permission should deny access if refresh cookie is missing.
        """
        request = self.factory.post("/")
        request.COOKIES = {}
        self.assertFalse(self.perm.has_permission(request, self.view))

    def test_denies_when_invalid_cookie(self):
        """
        Permission should deny access if refresh cookie token is invalid.
        """
        request = self.factory.post("/")
        request.COOKIES = {"refresh_token": "not-a-jwt"}
        self.assertFalse(self.perm.has_permission(request, self.view))

    def test_allows_when_valid_refresh_cookie(self):
        """
        Permission should allow access if refresh cookie contains a valid token.
        """
        user = User.objects.create_user(
            username="u3",
            email="u3@example.com",
            password="Passw0rd!!",
            is_active=True,
        )
        refresh = RefreshToken.for_user(user)

        request = self.factory.post("/")
        request.COOKIES = {"refresh_token": str(refresh)}
        self.assertTrue(self.perm.has_permission(request, self.view))