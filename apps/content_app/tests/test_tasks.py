import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.content_app import tasks


class TestContentTasks(TestCase):
    def test_convert_video_to_hls_returns_if_missing_path(self):
        with patch("apps.content_app.tasks.subprocess.run") as run:
            tasks.convert_video_to_hls("")
            tasks.convert_video_to_hls("/does/not/exist.mp4")
            run.assert_not_called()

    @override_settings(FFMPEG_BIN="ffmpeg")
    def test_convert_video_to_hls_calls_ffmpeg_for_each_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "video.mp4")
            Path(src).write_bytes(b"dummy")

            expected_calls = len(tasks.ALLOWED_RESOLUTIONS)

            with patch("apps.content_app.tasks.subprocess.run") as run:
                tasks.convert_video_to_hls(src)

                self.assertEqual(run.call_count, expected_calls)

                cmd = run.call_args_list[0][0][0]
                self.assertEqual(cmd[0], "ffmpeg")
                self.assertIn("-i", cmd)
                self.assertIn(src, cmd)
                self.assertIn("-f", cmd)
                self.assertIn("hls", cmd)

            base, _ = os.path.splitext(src)
            for label in tasks.ALLOWED_RESOLUTIONS.keys():
                out_dir = Path(f"{base}_{label}")
                self.assertTrue(out_dir.exists())
                self.assertTrue(out_dir.is_dir())

    def test_delete_hls_outputs_removes_existing_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "video.mp4")
            Path(src).write_bytes(b"dummy")

            base, _ = os.path.splitext(src)

            created = []
            for label in tasks.ALLOWED_RESOLUTIONS.keys():
                out_dir = Path(f"{base}_{label}")
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "index.m3u8").write_bytes(b"#EXTM3U\n")
                (out_dir / "segment_000.ts").write_bytes(b"\x00\x01")
                created.append(out_dir)

            tasks.delete_hls_outputs(src)

            for out_dir in created:
                self.assertFalse(out_dir.exists())

    def test_delete_hls_outputs_noop_on_empty(self):
        tasks.delete_hls_outputs("")

    def test_ffmpeg_cmd_contains_expected_flags(self):
        cmd = tasks._ffmpeg_cmd(
            ffmpeg="ffmpeg",
            source="/x/video.mp4",
            height=720,
            segment_tpl="/out/segment_%03d.ts",
            playlist="/out/index.m3u8",
        )
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("-y", cmd)
        self.assertIn("-i", cmd)
        self.assertIn("/x/video.mp4", cmd)
        self.assertIn("scale=-2:720", cmd)
        self.assertIn("-hls_playlist_type", cmd)
        self.assertIn("vod", cmd)
        self.assertIn("-hls_flags", cmd)
        self.assertIn("independent_segments", cmd)
        self.assertIn("/out/index.m3u8", cmd)

    def test_ensure_parent_dirs_creates_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            deep = Path(tmp) / "a" / "b" / "video.mp4"
            self.assertFalse(deep.parent.exists())

            tasks._ensure_parent_dirs(str(deep))

            self.assertTrue(deep.parent.exists())
            self.assertTrue(deep.parent.is_dir())