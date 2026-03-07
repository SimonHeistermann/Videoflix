from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('django-rq/', include('django_rq.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('apps.user_auth_app.api.urls')),
    path('api/', include('apps.content_app.api.urls')),
    # path('__debug__/', include('debug_toolbar.urls')),
]

# In DEBUG mode, Django serves media files automatically.
# In production (DEBUG=False) we still need to serve uploaded media (thumbnails)
# since this is a demo project without an external file storage backend.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]