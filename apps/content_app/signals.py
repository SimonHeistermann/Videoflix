import os
from pathlib import Path

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Video
from .tasks import convert_video_to_hls, delete_hls_outputs
from .utils import enqueue_after_commit


def safe_remove(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


@receiver(post_save, sender=Video)
def video_created_convert_to_hls(sender, instance: Video, created: bool, **kwargs):
    if not created or not instance.video_file:
        return
    enqueue_after_commit(convert_video_to_hls, instance.video_file.path)


@receiver(post_delete, sender=Video)
def video_deleted_cleanup_files(sender, instance: Video, **kwargs):
    if instance.video_file and os.path.isfile(instance.video_file.path):
        enqueue_after_commit(delete_hls_outputs, instance.video_file.path)
        enqueue_after_commit(safe_remove, instance.video_file.path)

    if instance.thumbnail_url and os.path.isfile(instance.thumbnail_url.path):
        enqueue_after_commit(safe_remove, instance.thumbnail_url.path)