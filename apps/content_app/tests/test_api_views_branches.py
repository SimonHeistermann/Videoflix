from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.content_app.models import Video

User = get_user_model()


@override_settings(MEDIA_ROOT="/tmp/videoflix_test_media_api_views_branches")
class TestApiViewsBranches(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="u",
            email="u@example.com",
            password="Passw0rd!!",
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

    def _create_video(self):
        return Video.objects.create(
            title="Movie",
            description="desc",
            category=Video.Category.MOVIE,
            video_file=SimpleUploadedFile("movie.mp4", b"dummy", content_type="video/mp4"),
        )

    def test_playlist_invalid_resolution_returns_404(self):
        v = self._create_video()
        res = self.client.get(f"/api/video/{v.id}/999p/index.m3u8")
        self.assertEqual(res.status_code, 404)

    def test_segment_invalid_resolution_returns_404(self):
        v = self._create_video()
        res = self.client.get(f"/api/video/{v.id}/999p/segment_000.ts/")
        self.assertEqual(res.status_code, 404)

    def test_segment_invalid_name_returns_404(self):
        """
        Must be a single <str:segment> without slashes, otherwise the URL won't resolve
        and the view code (lines 81-82) never runs.
        """
        v = self._create_video()

        for bad in ["evil.ts", "segment_00.ts", "segment_000.mp4", "segment_000.ts.bak"]:
            res = self.client.get(f"/api/video/{v.id}/480p/{bad}/")
            self.assertEqual(res.status_code, 404)