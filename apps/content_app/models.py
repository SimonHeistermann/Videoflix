import os
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


def upload_video_path(instance, filename):
    name, ext = os.path.splitext(filename)
    safe = slugify(name) or "video"
    return f"videos/{uuid4().hex}_{safe}{ext.lower()}"


def validate_video_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    allowed = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"}
    if ext not in allowed:
        raise ValidationError(f"Unsupported file extension. Allowed: {', '.join(sorted(allowed))}")


class Video(models.Model):
    class Category(models.TextChoices):
        MOVIE = "Drama", "Drama"
        ROMANCE = "Romance", "Romance"
        ACTION = "Action", "Action"
        DOCUMENTARY = "Documentary", "Documentary"
        TUTORIAL = "Tutorial", "Tutorial"
        VLOG = "Vlog", "Vlog"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail_url = models.ImageField(upload_to="thumbnails/", null=True, blank=True)
    category = models.CharField(max_length=32, choices=Category.choices, default=Category.MOVIE)
    created_at = models.DateTimeField(auto_now_add=True)

    video_file = models.FileField(
        upload_to=upload_video_path,
        validators=[validate_video_file_extension],
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title