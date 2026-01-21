from django import forms
from django.contrib import admin

from .models import Video


class VideoAdminForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = "__all__"
        widgets = {"video_file": forms.ClearableFileInput(attrs={"accept": "video/*"})}


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "created_at")
    search_fields = ("title", "description")
    list_filter = ("category", "created_at")
    ordering = ("-created_at",)
    form = VideoAdminForm