from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-rq/', include('django_rq.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('apps.user_auth_app.api.urls')),
    path('api/', include('apps.content_app.api.urls')),
    # path('__debug__/', include('debug_toolbar.urls')),
] 

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)