"""
Models for the content application.

Includes the Video model and related helpers such as upload path generation
and file-extension validation for uploaded videos.
"""

import os
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


def upload_video_path(instance, filename):
    """
    Build a safe, unique upload path for video files.

    The filename is slugified and prefixed with a UUID to avoid collisions.

    Args:
        instance: Model instance (unused, but required by Django's upload_to API).
        filename (str): Original filename.

    Returns:
        str: Relative upload path for the video file.
    """
    name, ext = os.path.splitext(filename)
    safe = slugify(name) or "video"
    return f"videos/{uuid4().hex}_{safe}{ext.lower()}"


def validate_video_file_extension(value):
    """
    Validate that the uploaded file has an allowed video extension.

    Args:
        value: Uploaded file object (must provide a .name attribute).

    Raises:
        ValidationError: If file extension is not in the allowed list.
    """
    ext = os.path.splitext(value.name)[1].lower()
    allowed = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"}
    if ext not in allowed:
        raise ValidationError(f"Unsupported file extension. Allowed: {', '.join(sorted(allowed))}")


class Video(models.Model):
    """
    Represents a video entry in the content system.

    Fields:
        title: Human-readable title.
        description: Optional description text.
        thumbnail_url: Optional image thumbnail file.
        category: Categorization label from a controlled vocabulary.
        created_at: Timestamp when the record was created.
        video_file: Optional uploaded video file.
    """

    class Category(models.TextChoices):
        """
        Available categories for videos.
        """

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
        """
        Return a readable string representation of the video.

        Returns:
            str: Video title.
        """
        return self.title