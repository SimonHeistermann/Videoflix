"""
Tests for content app serializers.

Ensures VideoSerializer returns the intended public fields and
does not expose the raw video file field.
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.content_app.api.serializers import VideoSerializer
from apps.content_app.models import Video


@override_settings(MEDIA_ROOT="/tmp/videoflix_test_media")
class TestVideoSerializer(TestCase):
    """
    Tests for VideoSerializer field behavior.
    """

    def test_video_serializer_excludes_video_file(self):
        """
        VideoSerializer should exclude the video_file field while including key metadata fields.
        """
        video = Video.objects.create(
            title="Test",
            description="Desc",
            category=Video.Category.MOVIE,
            video_file=SimpleUploadedFile("movie.mp4", b"dummy", content_type="video/mp4"),
        )

        data = VideoSerializer(video).data
        self.assertIn("id", data)
        self.assertIn("title", data)
        self.assertIn("description", data)
        self.assertIn("thumbnail_url", data)
        self.assertIn("category", data)
        self.assertIn("created_at", data)

        self.assertNotIn("video_file", data)