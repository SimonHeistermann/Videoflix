"""
Smoke test for importing the content app views module.

This test ensures that the module imports successfully (e.g., no import-time
errors from missing dependencies or syntax issues).
"""

from django.test import TestCase


class TestImportViewsModule(TestCase):
    """
    Import tests for modules that should be import-safe.
    """

    def test_import_apps_content_app_views(self):
        """
        Import the content app views module.
        """
        import apps.content_app.views  # noqa: F401