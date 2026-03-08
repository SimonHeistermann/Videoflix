"""
Management command to seed demo videos from Pexels.

Downloads 3 short, free stock videos and their thumbnails from Pexels CDN,
creates Video model entries, and lets the existing post_save signal trigger
HLS conversion via the RQ worker.

On ephemeral filesystems (e.g. Render free tier), DB entries persist but
files are lost on redeploy. This command detects missing files and
re-downloads them automatically.

Usage:
    python manage.py seed_demos          # seed or restore missing files
    python manage.py seed_demos --force  # delete all and re-seed from scratch

All videos are licensed under the Pexels License (free for personal and
commercial use, no attribution required).
"""

import os
import tempfile
from urllib.request import Request, urlopen

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.content_app.models import Video

DEMO_VIDEOS = [
    {
        "title": "Ocean Waves Crashing on Shore",
        "description": "Relaxing ocean waves rolling onto a sandy beach. Free stock footage from Pexels.",
        "category": "Documentary",
        "video_url": "https://videos.pexels.com/video-files/1093662/1093662-hd_1920_1080_30fps.mp4",
        "thumb_url": "https://images.pexels.com/videos/1093662/free-video-1093662.jpg?auto=compress&cs=tinysrgb&w=800",
        "video_filename": "ocean_waves.mp4",
        "thumb_filename": "ocean_waves.jpg",
    },
    {
        "title": "Aerial View of Green Mountains",
        "description": "Stunning aerial footage of lush green mountain landscape. Free stock footage from Pexels.",
        "category": "Documentary",
        "video_url": "https://videos.pexels.com/video-files/3571264/3571264-hd_1920_1080_30fps.mp4",
        "thumb_url": "https://images.pexels.com/videos/3571264/free-video-3571264.jpg?auto=compress&cs=tinysrgb&w=800",
        "video_filename": "green_mountains.mp4",
        "thumb_filename": "green_mountains.jpg",
    },
    {
        "title": "City Night Traffic Timelapse",
        "description": "Vibrant city traffic at night with streaking lights. Free stock footage from Pexels.",
        "category": "Documentary",
        "video_url": "https://videos.pexels.com/video-files/1409899/1409899-hd_1920_1080_25fps.mp4",
        "thumb_url": "https://images.pexels.com/videos/1409899/free-video-1409899.jpg?auto=compress&cs=tinysrgb&w=800",
        "video_filename": "city_night.mp4",
        "thumb_filename": "city_night.jpg",
    },
]


def _download(url):
    """Download a URL to a temporary file and return the file path."""
    suffix = os.path.splitext(url.split("?")[0])[1] or ".tmp"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=120) as resp:
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                tmp.write(chunk)
        tmp.close()
        return tmp.name
    except Exception:
        tmp.close()
        os.unlink(tmp.name)
        raise


def _files_exist(video):
    """Check if both video file and thumbnail exist on disk."""
    try:
        vid_ok = video.video_file and os.path.isfile(video.video_file.path)
        thumb_ok = video.thumbnail_url and os.path.isfile(video.thumbnail_url.path)
        return vid_ok and thumb_ok
    except Exception:
        return False


class Command(BaseCommand):
    help = "Seed 3 demo videos from Pexels (restores files after ephemeral redeploy)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete existing demo videos and re-seed from scratch.",
        )

    def handle(self, *args, **options):
        if options["force"]:
            deleted, _ = Video.objects.filter(
                title__in=[v["title"] for v in DEMO_VIDEOS]
            ).delete()
            self.stdout.write(f"  Force mode: deleted {deleted} existing entries.")

        for entry in DEMO_VIDEOS:
            existing = Video.objects.filter(title=entry["title"]).first()

            if existing and _files_exist(existing):
                self.stdout.write(f"  '{entry['title']}' OK — skipping.")
                continue

            # DB entry exists but files are missing (ephemeral filesystem wiped)
            if existing:
                self.stdout.write(f"  '{entry['title']}' files missing — re-downloading...")
                existing.delete()

            self.stdout.write(f"  Downloading video: {entry['title']}...")
            video_tmp = _download(entry["video_url"])

            self.stdout.write(f"  Downloading thumbnail: {entry['title']}...")
            thumb_tmp = _download(entry["thumb_url"])

            try:
                video = Video(
                    title=entry["title"],
                    description=entry["description"],
                    category=entry["category"],
                )
                with open(thumb_tmp, "rb") as tf:
                    video.thumbnail_url.save(entry["thumb_filename"], File(tf), save=False)
                with open(video_tmp, "rb") as vf:
                    video.video_file.save(entry["video_filename"], File(vf), save=False)
                video.save()  # triggers post_save signal → HLS conversion
                self.stdout.write(self.style.SUCCESS(f"  Created: {entry['title']}"))
            finally:
                os.unlink(video_tmp)
                os.unlink(thumb_tmp)

        self.stdout.write(self.style.SUCCESS("Demo seeding complete."))
