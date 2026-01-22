"""
Integration tests for content API views.

Covers:
- authentication requirements for the video list endpoint,
- ordering of listed videos,
- serving HLS playlists and segments when files exist,
- 404 behavior for missing videos/playlists/segments.
"""

import os
import shutil

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.content_app.models import Video

User = get_user_model()


@override_settings(MEDIA_ROOT="/tmp/videoflix_test_media_content_views")
class TestContentViews(TestCase):
    """
    Integration tests for the content app's API endpoints.
    """

    def setUp(self):
        """
        Create an API client and an active user (authentication is performed per test).
        """
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="u",
            email="u@example.com",
            password="Passw0rd!!",
            is_active=True,
        )

    def _auth(self):
        """
        Authenticate the API client as the test user.
        """
        self.client.force_authenticate(user=self.user)

    def _create_video(self, title="A", filename="a.mp4"):
        """
        Helper to create a Video instance with a dummy uploaded video file.

        Args:
            title (str): Video title.
            filename (str): Uploaded file name.

        Returns:
            Video: Newly created video instance.
        """
        return Video.objects.create(
            title=title,
            description="desc",
            category=Video.Category.MOVIE,
            video_file=SimpleUploadedFile(filename, b"dummy", content_type="video/mp4"),
        )

    def test_video_list_requires_auth(self):
        """
        Video list endpoint should return 401 when unauthenticated.
        """
        res = self.client.get("/api/video/")
        self.assertEqual(res.status_code, 401)

    def test_video_list_returns_desc_order(self):
        """
        Video list endpoint should return videos in descending created_at order.
        """
        self._auth()
        v1 = self._create_video(title="Old", filename="old.mp4")
        v2 = self._create_video(title="New", filename="new.mp4")

        res = self.client.get("/api/video/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)

        self.assertEqual(res.data[0]["id"], v2.id)
        self.assertEqual(res.data[1]["id"], v1.id)

    def test_hls_playlist_200_when_file_exists(self):
        """
        Playlist endpoint should return 200 and correct content type when file exists.
        """
        self._auth()
        video = self._create_video(title="Movie", filename="movie.mp4")

        base, _ = os.path.splitext(video.video_file.path)
        out_dir = f"{base}_720p"
        os.makedirs(out_dir, exist_ok=True)

        playlist_path = os.path.join(out_dir, "index.m3u8")
        with open(playlist_path, "wb") as f:
            f.write(b"#EXTM3U\n")

        res = self.client.get(f"/api/video/{video.id}/720p/index.m3u8")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "application/vnd.apple.mpegurl")

        shutil.rmtree(out_dir, ignore_errors=True)

    def test_hls_playlist_404_if_video_missing(self):
        """
        Playlist endpoint should return 404 if the referenced video does not exist.
        """
        self._auth()
        res = self.client.get("/api/video/999999/720p/index.m3u8")
        self.assertEqual(res.status_code, 404)

    def test_hls_playlist_404_if_playlist_missing(self):
        """
        Playlist endpoint should return 404 when the playlist file is missing.
        """
        self._auth()
        video = self._create_video(title="Movie2", filename="movie2.mp4")

        res = self.client.get(f"/api/video/{video.id}/720p/index.m3u8")
        self.assertEqual(res.status_code, 404)

    def test_hls_segment_200_when_file_exists(self):
        """
        Segment endpoint should return 200 and correct content type when file exists.
        """
        self._auth()
        video = self._create_video(title="Movie3", filename="movie3.mp4")

        base, _ = os.path.splitext(video.video_file.path)
        out_dir = f"{base}_480p"
        os.makedirs(out_dir, exist_ok=True)

        segment_path = os.path.join(out_dir, "segment_000.ts")
        with open(segment_path, "wb") as f:
            f.write(b"\x00\x01\x02")

        res = self.client.get(f"/api/video/{video.id}/480p/segment_000.ts/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "video/MP2T")

        shutil.rmtree(out_dir, ignore_errors=True)

    def test_hls_segment_404_if_segment_missing(self):
        """
        Segment endpoint should return 404 when the segment file is missing.
        """
        self._auth()
        video = self._create_video(title="Movie4", filename="movie4.mp4")

        res = self.client.get(f"/api/video/{video.id}/480p/segment_000.ts/")
        self.assertEqual(res.status_code, 404)