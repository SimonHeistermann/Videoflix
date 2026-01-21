import os
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.content_app.models import Video
from apps.content_app import signals


@override_settings(MEDIA_ROOT="/tmp/videoflix_test_media_signals_extra")
class TestSignalsExtras(TestCase):
    def test_safe_remove_swallows_exceptions(self):
        with patch("apps.content_app.signals.Path.unlink", side_effect=OSError("boom")):
            signals.safe_remove("/tmp/does-not-matter.txt")

    def test_post_save_returns_early_when_not_created(self):
        inst = type("X", (), {"video_file": None})()
        with patch("apps.content_app.signals.enqueue_after_commit") as enqueue:
            signals.video_created_convert_to_hls(sender=None, instance=inst, created=False)
            enqueue.assert_not_called()

    def test_post_save_returns_early_when_no_video_file(self):
        inst = type("X", (), {"video_file": None})()
        with patch("apps.content_app.signals.enqueue_after_commit") as enqueue:
            signals.video_created_convert_to_hls(sender=None, instance=inst, created=True)
            enqueue.assert_not_called()

    def test_post_delete_enqueues_thumbnail_cleanup_when_thumbnail_exists(self):
        video = Video.objects.create(
            title="WithThumb",
            description="desc",
            category=Video.Category.MOVIE,
            thumbnail_url=SimpleUploadedFile("thumb.jpg", b"img", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("movie.mp4", b"dummy", content_type="video/mp4"),
        )
        self.assertTrue(video.thumbnail_url and os.path.isfile(video.thumbnail_url.path))

        with patch("apps.content_app.signals.enqueue_after_commit") as enqueue:
            video.delete()

            self.assertTrue(enqueue.called)
            thumb_path = video.thumbnail_url.path
            calls = enqueue.call_args_list
            self.assertTrue(
                any(
                    (len(c.args) >= 2 and c.args[0] == signals.safe_remove and c.args[1] == thumb_path)
                    for c in calls
                ),
                "Expected enqueue_after_commit(safe_remove, thumbnail_path) call not found.",
            )