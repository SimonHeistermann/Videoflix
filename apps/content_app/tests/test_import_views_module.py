from django.test import TestCase


class TestImportViewsModule(TestCase):
    def test_import_apps_content_app_views(self):
        import apps.content_app.views