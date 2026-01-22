"""
Tests for content app utility helpers.

Covers:
- path helper functions,
- validation functions for resolution and segment naming,
- enqueue_after_commit behavior,
- constants such as ALLOWED_RESOLUTIONS and SEGMENT_RE.
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.content_app import utils


class TestContentUtils(TestCase):
    """
    Unit tests for apps.content_app.utils.
    """

    def test_video_paths_helpers(self):
        """
        Path helpers should generate correct base, output directory, and playlist paths.
        """
        base = utils.video_base_path("/tmp/foo/video.mp4")
        self.assertTrue(str(base).endswith("/tmp/foo/video"))

        out = utils.hls_output_dir("/tmp/foo/video.mp4", "720p")
        self.assertTrue(str(out).endswith("/tmp/foo/video_720p"))

        playlist = utils.hls_playlist_path("/tmp/foo/video.mp4", "720p")
        self.assertTrue(str(playlist).endswith("/tmp/foo/video_720p/index.m3u8"))

    def test_validate_resolution_ok_and_fail(self):
        """
        validate_resolution should accept allowed resolutions and reject others.
        """
        utils.validate_resolution("720p")  # ok
        with self.assertRaises(ValueError):
            utils.validate_resolution("999p")

    def test_validate_segment_name_ok_and_fail(self):
        """
        validate_segment_name should accept properly formatted segment names and reject others.
        """
        utils.validate_segment_name("segment_000.ts")  # ok

        for bad in ["000.ts", "segment_00.ts", "segment_000.mp4", "../segment_000.ts", "segment_000.ts/"]:
            with self.assertRaises(ValueError):
                utils.validate_segment_name(bad)

    def test_enqueue_after_commit_registers_and_executes_callback(self):
        """
        enqueue_after_commit should register a transaction.on_commit callback that enqueues the job.
        """
        dummy_task = lambda *args, **kwargs: None

        fake_queue = MagicMock()
        fake_django_rq = MagicMock()
        fake_django_rq.get_queue.return_value = fake_queue

        with patch("apps.content_app.utils.transaction.on_commit") as on_commit, patch(
            "apps.content_app.utils.django_rq", fake_django_rq
        ):
            utils.enqueue_after_commit(dummy_task, 1, 2, queue="default")

            self.assertTrue(on_commit.called)
            cb = on_commit.call_args[0][0]
            self.assertTrue(callable(cb))

            cb()

            fake_django_rq.get_queue.assert_called_once_with("default")
            self.assertTrue(fake_queue.enqueue.called)

    def test_constants(self):
        """
        Basic sanity checks for exported constants and regex patterns.
        """
        self.assertIn("480p", utils.ALLOWED_RESOLUTIONS)
        self.assertTrue(utils.SEGMENT_RE.match("segment_123.ts"))
        self.assertFalse(utils.SEGMENT_RE.match("segment_12.ts"))