"""
Branch coverage tests for content API HLS endpoints.

These tests focus on ensuring that invalid inputs (resolution or segment names)
are rejected with 404 responses, exercising the view-level validation branches.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.content_app.models import Video

User = get_user_model()


@override_settings(MEDIA_ROOT="/tmp/videoflix_test_media_api_views_branches")
class TestApiViewsBranches(TestCase):
    """
    Tests covering edge branches for HLS playlist and segment endpoints.
    """

    def setUp(self):
        """
        Create an authenticated API client and an active user.
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="u",
            email="u@example.com",
            password="Passw0rd!!",
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

    def _create_video(self):
        """
        Helper to create a minimal Video instance with an uploaded dummy file.

        Returns:
            Video: Newly created video instance.
        """
        return Video.objects.create(
            title="Movie",
            description="desc",
            category=Video.Category.MOVIE,
            video_file=SimpleUploadedFile("movie.mp4", b"dummy", content_type="video/mp4"),
        )

    def test_playlist_invalid_resolution_returns_404(self):
        """
        Playlist endpoint should return 404 when resolution is invalid.
        """
        v = self._create_video()
        res = self.client.get(f"/api/video/{v.id}/999p/index.m3u8")
        self.assertEqual(res.status_code, 404)

    def test_segment_invalid_resolution_returns_404(self):
        """
        Segment endpoint should return 404 when resolution is invalid.
        """
        v = self._create_video()
        res = self.client.get(f"/api/video/{v.id}/999p/segment_000.ts/")
        self.assertEqual(res.status_code, 404)

    def test_segment_invalid_name_returns_404(self):
        """
        Segment endpoint should return 404 when the segment name is invalid.

        Note:
            The segment is captured as a single <str:segment> without slashes.
            If the URL contains slashes, routing won't match and the view code
            will not be executed.
        """
        v = self._create_video()

        for bad in ["evil.ts", "segment_00.ts", "segment_000.mp4", "segment_000.ts.bak"]:
            res = self.client.get(f"/api/video/{v.id}/480p/{bad}/")
            self.assertEqual(res.status_code, 404)