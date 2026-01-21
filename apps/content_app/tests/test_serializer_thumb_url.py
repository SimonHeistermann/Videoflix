from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.content_app.api.serializers import VideoSerializer
from apps.content_app.models import Video


@override_settings(MEDIA_ROOT="/tmp/videoflix_test_media_serializer_thumb")
class TestVideoSerializerThumbUrl(TestCase):
    def test_thumbnail_url_none_when_missing(self):
        v = Video.objects.create(
            title="NoThumb",
            description="d",
            category=Video.Category.MOVIE,
            video_file=SimpleUploadedFile("a.mp4", b"dummy", content_type="video/mp4"),
        )
        data = VideoSerializer(v).data
        self.assertIsNone(data["thumbnail_url"])

    def test_thumbnail_url_absolute_with_request(self):
        v = Video.objects.create(
            title="WithThumb",
            description="d",
            category=Video.Category.MOVIE,
            thumbnail_url=SimpleUploadedFile("thumb.jpg", b"img", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("b.mp4", b"dummy", content_type="video/mp4"),
        )

        rf = APIRequestFactory()
        req = rf.get("/api/video/")
        ser = VideoSerializer(v, context={"request": req})
        url = ser.data["thumbnail_url"]

        self.assertTrue(url.startswith("http://testserver/"))
        self.assertIn("/media/", url)