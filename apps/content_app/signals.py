"""
Signal handlers for the content application.

This module hooks into Django model signals to:
- enqueue HLS conversion after a Video is created (and has a video file),
- enqueue cleanup tasks after a Video is deleted (HLS outputs + original files).
"""

import os
from pathlib import Path

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Video
from .tasks import convert_video_to_hls, delete_hls_outputs
from .utils import enqueue_after_commit


def safe_remove(path: str) -> None:
    """
    Attempt to remove a file path without raising exceptions.

    Args:
        path (str): File path to remove.
    """
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        # Intentionally suppress all exceptions: this helper is used in cleanup paths.
        pass


@receiver(post_save, sender=Video)
def video_created_convert_to_hls(sender, instance: Video, created: bool, **kwargs):
    """
    Enqueue HLS conversion for newly created videos.

    Only enqueues conversion if:
    - the model instance was newly created,
    - a video file is present.

    Args:
        sender: The model class that sent the signal.
        instance (Video): The saved Video instance.
        created (bool): True if this is a newly created record.
        **kwargs: Additional signal keyword arguments.
    """
    if not created or not instance.video_file:
        return
    enqueue_after_commit(convert_video_to_hls, instance.video_file.path)


@receiver(post_delete, sender=Video)
def video_deleted_cleanup_files(sender, instance: Video, **kwargs):
    """
    Enqueue cleanup tasks when a Video is deleted.

    Behavior:
    - If the video file exists, enqueue deletion of HLS outputs and the original file.
    - If the thumbnail exists, enqueue deletion of the thumbnail file.

    Args:
        sender: The model class that sent the signal.
        instance (Video): The deleted Video instance.
        **kwargs: Additional signal keyword arguments.
    """
    if instance.video_file and os.path.isfile(instance.video_file.path):
        enqueue_after_commit(delete_hls_outputs, instance.video_file.path)
        enqueue_after_commit(safe_remove, instance.video_file.path)

    if instance.thumbnail_url and os.path.isfile(instance.thumbnail_url.path):
        enqueue_after_commit(safe_remove, instance.thumbnail_url.path)