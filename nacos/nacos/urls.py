from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

from django.conf.urls.static import static


urlpatterns = [
    path('', include('nacos_app.urls')),
    path('officer/', include('election_officer.urls')),
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('nacos_app:login'), name='home'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

