"""
Django admin configuration for the content application.

Provides a customized admin form and admin interface for Video objects,
including an upload widget restricted to video files.
"""

from django import forms
from django.contrib import admin

from .models import Video


class VideoAdminForm(forms.ModelForm):
    """
    ModelForm for Video in Django admin.

    Configures the file input widget to accept video types.
    """

    class Meta:
        model = Video
        fields = "__all__"
        widgets = {"video_file": forms.ClearableFileInput(attrs={"accept": "video/*"})}


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Video model.
    """

    list_display = ("id", "title", "category", "created_at")
    search_fields = ("title", "description")
    list_filter = ("category", "created_at")
    ordering = ("-created_at",)
    form = VideoAdminForm