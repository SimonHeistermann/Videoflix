from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.user_auth_app.api.serializers import (
    RegisterSerializer,
    LoginSerializer,
    PasswordConfirmSerializer,
)

User = get_user_model()


class TestRegisterSerializer(TestCase):
    def test_register_success_creates_inactive_user(self):
        data = {"email": "a@example.com", "password": "Passw0rd!!", "confirmed_password": "Passw0rd!!"}
        s = RegisterSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertEqual(user.email, "a@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password("Passw0rd!!"))

    def test_register_password_mismatch(self):
        data = {"email": "a2@example.com", "password": "Passw0rd!!", "confirmed_password": "nope"}
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("detail", s.errors)

    def test_register_duplicate_email(self):
        User.objects.create_user(username="x", email="dup@example.com", password="Passw0rd!!", is_active=True)
        data = {"email": "dup@example.com", "password": "Passw0rd!!", "confirmed_password": "Passw0rd!!"}
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("detail", s.errors)


class TestLoginSerializer(TestCase):
    def test_login_success(self):
        user = User.objects.create_user(username="u", email="u@example.com", password="Passw0rd!!", is_active=True)
        s = LoginSerializer(data={"email": "u@example.com", "password": "Passw0rd!!"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIn("access", s.validated_data)
        self.assertIn("refresh", s.validated_data)
        self.assertEqual(s.validated_data["user"].id, user.id)

    def test_login_wrong_password(self):
        User.objects.create_user(username="u2", email="u2@example.com", password="Passw0rd!!", is_active=True)
        s = LoginSerializer(data={"email": "u2@example.com", "password": "wrong"})
        self.assertFalse(s.is_valid())
        self.assertIn("detail", s.errors)

    def test_login_inactive_user_denied(self):
        User.objects.create_user(username="u3", email="u3@example.com", password="Passw0rd!!", is_active=False)
        s = LoginSerializer(data={"email": "u3@example.com", "password": "Passw0rd!!"})
        self.assertFalse(s.is_valid())
        self.assertIn("detail", s.errors)

    def test_login_nonexistent_user(self):
        s = LoginSerializer(data={"email": "nope@example.com", "password": "Passw0rd!!"})
        self.assertFalse(s.is_valid())
        self.assertIn("detail", s.errors)


class TestPasswordConfirmSerializer(TestCase):
    def test_password_confirm_success(self):
        user = User.objects.create_user(username="u4", email="u4@example.com", password="OldPassw0rd!!", is_active=True)
        s = PasswordConfirmSerializer(instance=user, data={"new_password": "NewPassw0rd!!", "confirm_password": "NewPassw0rd!!"})
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewPassw0rd!!"))

    def test_password_confirm_mismatch(self):
        user = User.objects.create_user(username="u5", email="u5@example.com", password="OldPassw0rd!!", is_active=True)
        s = PasswordConfirmSerializer(instance=user, data={"new_password": "NewPassw0rd!!", "confirm_password": "nope"})
        self.assertFalse(s.is_valid())
        self.assertIn("detail", s.errors)