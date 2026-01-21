from rest_framework import serializers

from ..models import Video


class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ("id", "created_at", "title", "description", "thumbnail_url", "category")

    def get_thumbnail_url(self, obj: Video):
        request = self.context.get("request")
        if not obj.thumbnail_url:
            return None
        url = obj.thumbnail_url.url
        return request.build_absolute_uri(url) if request else url