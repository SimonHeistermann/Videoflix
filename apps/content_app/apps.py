"""
App configuration for the content application.

Registers signal handlers on app readiness.
"""

from django.apps import AppConfig


class ContentAppConfig(AppConfig):
    """
    Django AppConfig for the content app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.content_app"

    def ready(self):
        """
        Import signal handlers when the application is ready.

        Django calls this method once the app registry is fully populated.
        Importing signals here ensures receiver registration happens exactly once.
        """
        from . import signals  # noqa: F401