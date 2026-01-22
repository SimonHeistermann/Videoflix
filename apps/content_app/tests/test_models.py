"""
Tests for content app models and related helper functions.
"""

from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.content_app.models import Video, upload_video_path, validate_video_file_extension


class TestVideoModel(TestCase):
    """
    Unit tests for the Video model and model-level helper functions.
    """

    def test_str(self):
        """
        Video.__str__ should return the title.
        """
        v = Video(title="Hello", description="d", category=Video.Category.MOVIE)
        self.assertEqual(str(v), "Hello")

    def test_upload_video_path_slug_and_ext_lower(self):
        """
        upload_video_path should slugify the name and lowercase the extension.
        """
        p = upload_video_path(None, "My Cool Video.MP4")
        self.assertTrue(p.startswith("videos/"))
        self.assertTrue(p.endswith("_my-cool-video.mp4"))

        p2 = upload_video_path(None, "###.MOV")
        self.assertTrue(p2.startswith("videos/"))
        self.assertTrue(p2.endswith("_video.mov"))

    def test_validate_video_file_extension_ok(self):
        """
        validate_video_file_extension should accept allowed extensions.
        """
        f = SimpleNamespace(name="movie.mp4")
        validate_video_file_extension(f)

    def test_validate_video_file_extension_rejects(self):
        """
        validate_video_file_extension should reject disallowed extensions.
        """
        f = SimpleNamespace(name="evil.exe")
        with self.assertRaises(ValidationError):
            validate_video_file_extension(f)