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
    def _enqueue():
        django_rq.get_queue(queue).enqueue(task, *args, retry=DEFAULT_RETRY, **kwargs)

    transaction.on_commit(_enqueue)


def video_base_path(video_file_path: str) -> Path:
    base, _ = os.path.splitext(video_file_path)
    return Path(base)


def hls_output_dir(video_file_path: str, resolution: str) -> Path:
    base = video_base_path(video_file_path)
    return Path(f"{base}_{resolution}")


def hls_playlist_path(video_file_path: str, resolution: str) -> Path:
    return hls_output_dir(video_file_path, resolution) / "index.m3u8"


def validate_resolution(resolution: str) -> None:
    if resolution not in ALLOWED_RESOLUTIONS:
        raise ValueError("Invalid resolution.")


def validate_segment_name(segment: str) -> None:
    if not SEGMENT_RE.match(segment):
        raise ValueError("Invalid segment name.")