from datetime import timedelta

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase, override_settings

from apps.user_auth_app import utils

User = get_user_model()


class TestUtils(TestCase):
    def test_build_uid_and_token(self):
        user = User.objects.create_user(
            username="u",
            email="u@example.com",
            password="Passw0rd!!",
            is_active=False,
        )
        uidb64, token = utils.build_uid_and_token(user)
        self.assertTrue(uidb64)
        self.assertTrue(token)

    def test_get_user_from_uid_invalid(self):
        self.assertIsNone(utils.get_user_from_uid("not-base64"))

    def test_try_get_user_by_email(self):
        self.assertIsNone(utils.try_get_user_by_email(""))

        user = User.objects.create_user(
            username="u2",
            email="u2@example.com",
            password="Passw0rd!!",
            is_active=True,
        )
        found = utils.try_get_user_by_email("u2@example.com")
        self.assertIsNotNone(found)
        self.assertEqual(found.id, user.id)

    @override_settings(
        FRONTEND_BASE_URL="https://frontend.example",
        FRONTEND_ACTIVATE_PATH="activate.html",
        FRONTEND_RESET_PATH="reset.html",
    )
    def test_build_frontend_link(self):
        user = User.objects.create_user(
            username="u3",
            email="u3@example.com",
            password="Passw0rd!!",
            is_active=False,
        )
        uidb64, token = utils.build_uid_and_token(user)
        link = utils.build_frontend_link("activate", uidb64, token)
        self.assertIn("https://frontend.example/activate.html", link)
        self.assertIn("uid=", link)
        self.assertIn("token=", link)

    @override_settings(
        AUTH_COOKIE_PREFIX="",
        SECURE_COOKIES=False,
        JWT_COOKIE_SAMESITE="Lax",
        JWT_COOKIE_DOMAIN=None,
        JWT_COOKIE_PATH="/",
        SIMPLE_JWT={
            "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
            "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
        },
    )
    def test_cookie_set_and_delete(self):
        response = HttpResponse()
        utils.set_access_cookie(response, "ACCESS")
        utils.set_refresh_cookie(response, "REFRESH")
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

        self.assertEqual(response.cookies["access_token"].value, "ACCESS")
        self.assertEqual(response.cookies["refresh_token"].value, "REFRESH")
        response2 = HttpResponse()
        utils.delete_auth_cookies(response2)
        self.assertIn("access_token", response2.cookies)
        self.assertIn("refresh_token", response2.cookies)
        self.assertEqual(response2.cookies["access_token"]["max-age"], 0)
        self.assertEqual(response2.cookies["refresh_token"]["max-age"], 0)