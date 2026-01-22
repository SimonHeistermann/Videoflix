"""
Serializers for the content application.

This module currently provides a serializer for the Video model,
including a computed absolute thumbnail URL when a request context
is available.
"""

from rest_framework import serializers

from ..models import Video


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for Video objects.

    Adds:
        thumbnail_url: A computed field that returns an absolute URL if the
        request is present in serializer context, otherwise the relative URL.
    """

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ("id", "created_at", "title", "description", "thumbnail_url", "category")

    def get_thumbnail_url(self, obj: Video):
        """
        Build a thumbnail URL for the given video.

        If a request is available in serializer context, this returns an absolute
        URL using `request.build_absolute_uri`. Otherwise, it returns the stored
        (relative) URL.

        Args:
            obj (Video): Video instance.

        Returns:
            str | None: Absolute or relative thumbnail URL, or None if not set.
        """
        request = self.context.get("request")
        if not obj.thumbnail_url:
            return None

        url = obj.thumbnail_url.url
        return request.build_absolute_uri(url) if request else url