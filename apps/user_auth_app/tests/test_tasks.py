"""
Tests for email task functions.

Verifies that sending functions render templates, create an EmailMultiAlternatives
instance, attach an HTML alternative, and call send().
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from apps.user_auth_app import tasks


class TestEmailTasks(TestCase):
    """
    Tests for tasks that send activation and password reset emails.
    """

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@example.com",
        BASE_DIR="/tmp",
        EMAIL_LOGO_PATH="",
    )
    @patch("apps.user_auth_app.tasks.render_to_string", return_value="<html><body>Hi</body></html>")
    @patch("apps.user_auth_app.tasks.EmailMultiAlternatives")
    def test_send_activation_email_sends(self, email_cls, render_mock):
        """
        send_activation_email should render template and send the email message.
        """
        msg = MagicMock()
        email_cls.return_value = msg

        tasks.send_activation_email("a@example.com", "https://link")

        render_mock.assert_called_once()
        email_cls.assert_called_once()
        msg.attach_alternative.assert_called_once()
        msg.send.assert_called_once()

    @override_settings(
        DEFAULT_FROM_EMAIL="noreply@example.com",
        BASE_DIR="/tmp",
        EMAIL_LOGO_PATH="",
    )
    @patch("apps.user_auth_app.tasks.render_to_string", return_value="<html><body>Hi</body></html>")
    @patch("apps.user_auth_app.tasks.EmailMultiAlternatives")
    def test_send_passwordreset_email_sends(self, email_cls, render_mock):
        """
        send_passwordreset_email should render template and send the email message.
        """
        msg = MagicMock()
        email_cls.return_value = msg

        tasks.send_passwordreset_email("b@example.com", "https://reset")

        render_mock.assert_called_once()
        email_cls.assert_called_once()
        msg.attach_alternative.assert_called_once()
        msg.send.assert_called_once()