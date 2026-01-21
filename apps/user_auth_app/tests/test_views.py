from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch

User = get_user_model()


@override_settings(
    FRONTEND_BASE_URL="https://frontend.example",
    FRONTEND_ACTIVATE_PATH="pages/auth/activate.html",
    FRONTEND_RESET_PATH="pages/auth/confirm_password.html",
    AUTH_COOKIE_PREFIX="",
    SECURE_COOKIES=False,
    JWT_COOKIE_SAMESITE="Lax",
    JWT_COOKIE_DOMAIN=None,
    JWT_COOKIE_PATH="/",
)
class TestAuthViews(APITestCase):
    def _create_user(self, email="u@example.com", password="Passw0rd!!", is_active=True):
        return User.objects.create_user(username=email, email=email, password=password, is_active=is_active)

    @patch("apps.user_auth_app.api.views.enqueue_after_commit")
    def test_register_success(self, enqueue_mock):
        url = reverse("register")
        payload = {"email": "new@example.com", "password": "Passw0rd!!", "confirmed_password": "Passw0rd!!"}

        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", res.data)
        self.assertIn("token", res.data)
        self.assertEqual(res.data["user"]["email"], "new@example.com")

        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.is_active)
        enqueue_mock.assert_called_once()

    @patch("apps.user_auth_app.api.views.enqueue_after_commit")
    def test_register_duplicate_email_fails(self, enqueue_mock):
        self._create_user(email="dup@example.com")
        url = reverse("register")
        payload = {"email": "dup@example.com", "password": "Passw0rd!!", "confirmed_password": "Passw0rd!!"}

        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        enqueue_mock.assert_not_called()

    @patch("apps.user_auth_app.api.views.enqueue_after_commit")
    def test_register_password_mismatch_fails(self, enqueue_mock):
        url = reverse("register")
        payload = {"email": "x@example.com", "password": "Passw0rd!!", "confirmed_password": "nope"}

        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        enqueue_mock.assert_not_called()

    def test_activate_success(self):
        user = self._create_user(email="inactive@example.com", is_active=False)
        uidb64 = __import__("django.utils.http").utils.http.urlsafe_base64_encode(__import__("django.utils.encoding").utils.encoding.force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse("activate", kwargs={"uidb64": uidb64, "token": token})
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_activate_invalid_uid(self):
        url = reverse("activate", kwargs={"uidb64": "bad", "token": "t"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_invalid_token(self):
        user = self._create_user(email="inactive2@example.com", is_active=False)
        uidb64 = __import__("django.utils.http").utils.http.urlsafe_base64_encode(__import__("django.utils.encoding").utils.encoding.force_bytes(user.pk))

        url = reverse("activate", kwargs={"uidb64": uidb64, "token": "bad-token"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_activate_already_active(self):
        user = self._create_user(email="active@example.com", is_active=True)
        uidb64 = __import__("django.utils.http").utils.http.urlsafe_base64_encode(__import__("django.utils.encoding").utils.encoding.force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse("activate", kwargs={"uidb64": uidb64, "token": token})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success_sets_cookies(self):
        self._create_user(email="login@example.com", password="Passw0rd!!", is_active=True)
        url = reverse("login")
        res = self.client.post(url, {"email": "login@example.com", "password": "Passw0rd!!"}, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["detail"], "Login successful")

        self.assertIn("access_token", res.cookies)
        self.assertIn("refresh_token", res.cookies)

    def test_login_wrong_password(self):
        self._create_user(email="login2@example.com", password="Passw0rd!!", is_active=True)
        url = reverse("login")
        res = self.client.post(url, {"email": "login2@example.com", "password": "wrong"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        self._create_user(email="inactive_login@example.com", password="Passw0rd!!", is_active=False)
        url = reverse("login")
        res = self.client.post(url, {"email": "inactive_login@example.com", "password": "Passw0rd!!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_requires_refresh_cookie(self):
        url = reverse("logout")
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalid_refresh_cookie(self):
        url = reverse("logout")
        self.client.cookies["refresh_token"] = "invalid"
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_success_deletes_cookies(self):
        user = self._create_user(email="logout@example.com", password="Passw0rd!!", is_active=True)
        refresh = RefreshToken.for_user(user)
        url = reverse("logout")
        self.client.cookies["refresh_token"] = str(refresh)
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", res.cookies)
        self.assertIn("refresh_token", res.cookies)
        self.assertEqual(res.cookies["access_token"]["max-age"], 0)
        self.assertEqual(res.cookies["refresh_token"]["max-age"], 0)

    def test_token_refresh_denied_without_cookie_permission(self):
        url = reverse("token-refresh")
        res = self.client.post(url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_refresh_success_sets_access_cookie(self):
        user = self._create_user(email="refresh@example.com", password="Passw0rd!!", is_active=True)
        refresh = RefreshToken.for_user(user)

        url = reverse("token-refresh")
        self.client.cookies["refresh_token"] = str(refresh)
        res = self.client.post(url, {}, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", res.cookies)

    @patch("apps.user_auth_app.api.views.enqueue_after_commit")
    def test_password_reset_always_200_and_enqueues_if_user_exists(self, enqueue_mock):
        self._create_user(email="reset@example.com", password="Passw0rd!!", is_active=True)
        url = reverse("password-reset")

        res = self.client.post(url, {"email": "reset@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        enqueue_mock.assert_called_once()

    @patch("apps.user_auth_app.api.views.enqueue_after_commit")
    def test_password_reset_always_200_and_does_not_enqueue_if_missing(self, enqueue_mock):
        url = reverse("password-reset")

        res = self.client.post(url, {"email": "missing@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        enqueue_mock.assert_not_called()

    def test_password_confirm_success(self):
        user = self._create_user(email="pc@example.com", password="OldPassw0rd!!", is_active=True)
        uidb64 = __import__("django.utils.http").utils.http.urlsafe_base64_encode(__import__("django.utils.encoding").utils.encoding.force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse("password-confirm", kwargs={"uidb64": uidb64, "token": token})
        res = self.client.post(url, {"new_password": "NewPassw0rd!!", "confirm_password": "NewPassw0rd!!"}, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewPassw0rd!!"))

    def test_password_confirm_invalid_uid(self):
        url = reverse("password-confirm", kwargs={"uidb64": "bad", "token": "t"})
        res = self.client.post(url, {"new_password": "NewPassw0rd!!", "confirm_password": "NewPassw0rd!!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_invalid_token(self):
        user = self._create_user(email="pc2@example.com", password="OldPassw0rd!!", is_active=True)
        uidb64 = __import__("django.utils.http").utils.http.urlsafe_base64_encode(__import__("django.utils.encoding").utils.encoding.force_bytes(user.pk))

        url = reverse("password-confirm", kwargs={"uidb64": uidb64, "token": "bad"})
        res = self.client.post(url, {"new_password": "NewPassw0rd!!", "confirm_password": "NewPassw0rd!!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirm_password_mismatch(self):
        user = self._create_user(email="pc3@example.com", password="OldPassw0rd!!", is_active=True)
        uidb64 = __import__("django.utils.http").utils.http.urlsafe_base64_encode(__import__("django.utils.encoding").utils.encoding.force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        url = reverse("password-confirm", kwargs={"uidb64": uidb64, "token": token})
        res = self.client.post(url, {"new_password": "NewPassw0rd!!", "confirm_password": "nope"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)