from django.http import FileResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status

from ..models import Video
from ..utils import hls_playlist_path, hls_output_dir, validate_resolution, validate_segment_name
from .serializers import VideoSerializer


class VideoListView(ListAPIView):
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Video.objects.all().order_by("-created_at")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class HLSPlaylistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        video = _get_video(movie_id)
        _ensure_valid_resolution(resolution)

        playlist = hls_playlist_path(video.video_file.path, resolution)
        if not playlist.exists():
            raise NotFound("HLS Playlist not found.")

        return FileResponse(
            playlist.open("rb"),
            content_type="application/vnd.apple.mpegurl",
            status=status.HTTP_200_OK,
        )


class HLSSegmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        video = _get_video(movie_id)
        _ensure_valid_resolution(resolution)
        _ensure_valid_segment(segment)

        seg = hls_output_dir(video.video_file.path, resolution) / segment
        if not seg.exists():
            raise NotFound("Segment not found.")

        return FileResponse(
            seg.open("rb"),
            content_type="video/MP2T",
            status=status.HTTP_200_OK,
        )


def _get_video(movie_id: int) -> Video:
    try:
        return Video.objects.get(id=movie_id)
    except Video.DoesNotExist:
        raise NotFound("Video not found.")


def _ensure_valid_resolution(resolution: str) -> None:
    try:
        validate_resolution(resolution)
    except ValueError:
        raise NotFound("Video or Manifest not found.")


def _ensure_valid_segment(segment: str) -> None:
    try:
        validate_segment_name(segment)
    except ValueError:
        raise NotFound("Video or Segment not found.")