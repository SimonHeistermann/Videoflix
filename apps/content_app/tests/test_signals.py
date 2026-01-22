"""
Tests for content app Django signal handlers.

Verifies that:
- post_save enqueues HLS conversion on video creation,
- post_delete enqueues cleanup actions when a video is deleted.
"""

import os
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.content_app.models import Video


@override_settings(MEDIA_ROOT="/tmp/videoflix_test_media_signals")
class TestContentSignals(TestCase):
    """
    Tests for the signal handlers registered for the Video model.
    """

    def test_post_save_enqueues_convert_on_create(self):
        """
        Creating a Video with a video_file should enqueue HLS conversion.
        """
        with patch("apps.content_app.signals.enqueue_after_commit") as enqueue:
            video = Video.objects.create(
                title="Movie",
                description="desc",
                category=Video.Category.MOVIE,
                video_file=SimpleUploadedFile("movie.mp4", b"dummy", content_type="video/mp4"),
            )

            self.assertTrue(enqueue.called)
            args, kwargs = enqueue.call_args
            self.assertTrue(video.video_file.path in args)

    def test_post_delete_enqueues_cleanup(self):
        """
        Deleting a Video should enqueue cleanup for generated outputs and source file.
        """
        video = Video.objects.create(
            title="Movie2",
            description="desc",
            category=Video.Category.MOVIE,
            video_file=SimpleUploadedFile("movie2.mp4", b"dummy", content_type="video/mp4"),
        )

        self.assertTrue(os.path.exists(video.video_file.path))

        with patch("apps.content_app.signals.enqueue_after_commit") as enqueue:
            video.delete()
            self.assertTrue(enqueue.called)