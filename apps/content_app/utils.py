"""
Utility helpers for HLS serving and background job scheduling.

Includes:
- RQ enqueue helper that runs only after transaction commit
- HLS output path helpers (output directories, playlist paths)
- validation helpers for allowed resolutions and segment naming
"""

import os
import re
from pathlib import Path

import django_rq
from django.db import transaction
from rq import Retry

DEFAULT_RETRY = Retry(max=3, interval=[10, 30, 60])

ALLOWED_RESOLUTIONS = {"480p": 480, "720p": 720, "1080p": 1080}
SEGMENT_RE = re.compile(r"^segment_\d{3}\.ts$")


def enqueue_after_commit(task, *args, queue="default", **kwargs):
    """
    Enqueue an RQ job only after the current DB transaction commits.

    This prevents background processing (like HLS conversion or file deletion)
    from running before related database state is fully persisted.

    Args:
        task (callable): Callable to enqueue.
        *args: Positional task arguments.
        queue (str): Queue name to enqueue into.
        **kwargs: Keyword task arguments.

    Returns:
        None
    """

    def _enqueue():
        django_rq.get_queue(queue).enqueue(task, *args, retry=DEFAULT_RETRY, **kwargs)

    transaction.on_commit(_enqueue)


def video_base_path(video_file_path: str) -> Path:
    """
    Return the base path of a video file without its extension.

    Example:
        "/path/movie.mp4" -> Path("/path/movie")

    Args:
        video_file_path (str): Path to a video file.

    Returns:
        pathlib.Path: Base path without extension.
    """
    base, _ = os.path.splitext(video_file_path)
    return Path(base)


def hls_output_dir(video_file_path: str, resolution: str) -> Path:
    """
    Compute the HLS output directory for the given video and resolution.

    Output directory format:
        "<base>_<resolution>"

    Args:
        video_file_path (str): Path to the source video.
        resolution (str): Resolution label (e.g., "480p").

    Returns:
        pathlib.Path: Directory where HLS outputs for this resolution are stored.
    """
    base = video_base_path(video_file_path)
    return Path(f"{base}_{resolution}")


def hls_playlist_path(video_file_path: str, resolution: str) -> Path:
    """
    Compute the path to the HLS playlist file for the given video and resolution.

    Args:
        video_file_path (str): Path to the source video.
        resolution (str): Resolution label.

    Returns:
        pathlib.Path: Path to "index.m3u8" within the HLS output directory.
    """
    return hls_output_dir(video_file_path, resolution) / "index.m3u8"


def validate_resolution(resolution: str) -> None:
    """
    Validate that the given resolution is supported.

    Args:
        resolution (str): Resolution label.

    Raises:
        ValueError: If the resolution is not allowed.
    """
    if resolution not in ALLOWED_RESOLUTIONS:
        raise ValueError("Invalid resolution.")


def validate_segment_name(segment: str) -> None:
    """
    Validate that the given HLS segment filename is safe and well-formed.

    The expected format is:
        "segment_###.ts" where ### are three digits.

    Args:
        segment (str): Segment filename.

    Raises:
        ValueError: If the segment name does not match the expected pattern.
    """
    if not SEGMENT_RE.match(segment):
        raise ValueError("Invalid segment name.")