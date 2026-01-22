"""
API views for listing videos and serving HLS playlists/segments.

Endpoints:
- VideoListView: Lists available videos.
- HLSPlaylistView: Serves the generated HLS playlist (.m3u8) for a given video and resolution.
- HLSSegmentView: Serves individual HLS segment files (.ts) for a given video and resolution.

All endpoints require authentication by default.
"""

from django.http import FileResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from rest_framework import status

from ..models import Video
from ..utils import hls_playlist_path, hls_output_dir, validate_resolution, validate_segment_name
from .serializers import VideoSerializer


class VideoListView(ListAPIView):
    """
    List API endpoint for Video objects.

    Returns all videos ordered by creation date (newest first). Adds the request
    object to serializer context so that serializers can build absolute URLs.
    """

    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return the queryset of videos to list.

        Returns:
            QuerySet[Video]: Video queryset ordered by newest first.
        """
        return Video.objects.all().order_by("-created_at")

    def get_serializer_context(self):
        """
        Extend serializer context with the current request.

        Returns:
            dict: Serializer context including request.
        """
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class HLSPlaylistView(APIView):
    """
    Serve an HLS playlist (.m3u8) for a video and a given resolution.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """
        Return the HLS playlist for the given video and resolution.

        Args:
            request: The incoming HTTP request.
            movie_id (int): Video ID.
            resolution (str): Resolution identifier used by the HLS pipeline.

        Returns:
            FileResponse: The playlist file response.

        Raises:
            NotFound: If the video, resolution, or playlist does not exist.
        """
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
    """
    Serve individual HLS segment files (.ts) for a video and given resolution.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """
        Return the HLS segment file for the given video, resolution, and segment name.

        Args:
            request: The incoming HTTP request.
            movie_id (int): Video ID.
            resolution (str): Resolution identifier used by the HLS pipeline.
            segment (str): Segment filename.

        Returns:
            FileResponse: The segment file response.

        Raises:
            NotFound: If the video, resolution, or segment does not exist/validate.
        """
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
    """
    Retrieve a Video by ID or raise NotFound.

    Args:
        movie_id (int): Video ID.

    Returns:
        Video: The matching Video instance.

    Raises:
        NotFound: If no video with the given ID exists.
    """
    try:
        return Video.objects.get(id=movie_id)
    except Video.DoesNotExist:
        raise NotFound("Video not found.")


def _ensure_valid_resolution(resolution: str) -> None:
    """
    Validate the given resolution identifier.

    Args:
        resolution (str): Resolution identifier.

    Raises:
        NotFound: If the resolution is invalid.
    """
    try:
        validate_resolution(resolution)
    except ValueError:
        raise NotFound("Video or Manifest not found.")


def _ensure_valid_segment(segment: str) -> None:
    """
    Validate the given HLS segment filename.

    Args:
        segment (str): Segment filename.

    Raises:
        NotFound: If the segment name is invalid.
    """
    try:
        validate_segment_name(segment)
    except ValueError:
        raise NotFound("Video or Segment not found.")