from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from apps.user_auth_app.authentication import CookieJWTAuthentication

User = get_user_model()


class TestCookieJWTAuthentication(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.auth = CookieJWTAuthentication()

    def test_returns_none_when_no_cookie(self):
        request = self.factory.get("/")
        request.COOKIES = {}
        self.assertIsNone(self.auth.authenticate(request))

    def test_returns_none_when_invalid_token(self):
        request = self.factory.get("/")
        request.COOKIES = {"access_token": "invalid"}
        self.assertIsNone(self.auth.authenticate(request))

    def test_authenticates_with_valid_access_cookie(self):
        user = User.objects.create_user(username="u", email="u@example.com", password="Passw0rd!!", is_active=True)
        access = str(RefreshToken.for_user(user).access_token)

        request = self.factory.get("/")
        request.COOKIES = {"access_token": access}
        result = self.auth.authenticate(request)

        self.assertIsNotNone(result)
        authed_user, token = result
        self.assertEqual(authed_user.id, user.id)
        self.assertTrue(token is not None)