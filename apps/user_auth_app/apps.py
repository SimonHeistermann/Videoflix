"""
App configuration for the user authentication application.
"""

from django.apps import AppConfig


class UserAuthAppConfig(AppConfig):
    """
    Django AppConfig for the user authentication app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.user_auth_app"