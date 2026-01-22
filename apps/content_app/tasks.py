"""
Background tasks for video processing in the content application.

This module provides:
- HLS conversion via FFmpeg for multiple target resolutions.
- Cleanup of generated HLS output folders.

Notes:
    - Conversion is done by invoking the configured FFmpeg binary via subprocess.
    - HLS outputs are stored in resolution-specific directories derived from the
      source file path.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

from django.conf import settings

from .utils import ALLOWED_RESOLUTIONS, hls_output_dir, video_base_path

logger = logging.getLogger(__name__)


def convert_video_to_hls(video_file_path: str) -> None:
    """
    Convert a source video file into HLS outputs for all allowed resolutions.

    For each label/height pair in ALLOWED_RESOLUTIONS, an HLS playlist
    (index.m3u8) and TS segments are produced under a resolution-specific
    output directory.

    Args:
        video_file_path (str): Absolute or relative path to the source video file.

    Returns:
        None
    """
    if not video_file_path or not os.path.exists(video_file_path):
        logger.warning("convert_video_to_hls: file missing: %s", video_file_path)
        return

    _ensure_parent_dirs(video_file_path)

    for label, height in ALLOWED_RESOLUTIONS.items():
        _convert_single_resolution(video_file_path, label, height)


def delete_hls_outputs(video_file_path: str) -> None:
    """
    Delete all HLS output folders for a given source video path.

    This removes resolution-specific output directories, if present.

    Args:
        video_file_path (str): Path to the original video file.

    Returns:
        None
    """
    if not video_file_path:
        return

    base = video_base_path(video_file_path)
    for label in ALLOWED_RESOLUTIONS.keys():
        folder = Path(f"{base}_{label}")
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)


def _convert_single_resolution(source: str, label: str, height: int) -> None:
    """
    Convert a video into a single HLS resolution output.

    Args:
        source (str): Path to the source video file.
        label (str): Resolution label (e.g., "480p").
        height (int): Target output height in pixels (width is auto-scaled).

    Returns:
        None

    Raises:
        subprocess.CalledProcessError: If FFmpeg fails (propagated by check=True).
    """
    out_dir = hls_output_dir(source, label)
    out_dir.mkdir(parents=True, exist_ok=True)

    playlist = out_dir / "index.m3u8"
    segment_tpl = str(out_dir / "segment_%03d.ts")

    ffmpeg = getattr(settings, "FFMPEG_BIN", "ffmpeg")
    cmd = _ffmpeg_cmd(ffmpeg, source, height, segment_tpl, str(playlist))

    logger.info("FFmpeg HLS start: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    logger.info("FFmpeg HLS done: %s", playlist)


def _ffmpeg_cmd(ffmpeg: str, source: str, height: int, segment_tpl: str, playlist: str):
    """
    Build the FFmpeg command used to generate HLS output.

    Args:
        ffmpeg (str): Path/name of the FFmpeg executable.
        source (str): Source video path.
        height (int): Target height used for scaling (width auto-scaled).
        segment_tpl (str): Segment filename template (e.g., ".../segment_%03d.ts").
        playlist (str): Output playlist path (e.g., ".../index.m3u8").

    Returns:
        list[str]: The FFmpeg command list suitable for subprocess.run.
    """
    return [
        ffmpeg,
        "-y",
        "-i",
        source,
        "-vf",
        f"scale=-2:{height}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-f",
        "hls",
        "-hls_time",
        "6",
        "-hls_playlist_type",
        "vod",
        "-hls_flags",
        "independent_segments",
        "-hls_segment_filename",
        segment_tpl,
        playlist,
    ]


def _ensure_parent_dirs(video_file_path: str) -> None:
    """
    Ensure the parent directory of the given video file path exists.

    Args:
        video_file_path (str): Video file path.

    Returns:
        None
    """
    p = Path(video_file_path)
    p.parent.mkdir(parents=True, exist_ok=True)