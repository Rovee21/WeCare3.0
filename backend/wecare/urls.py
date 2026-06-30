import types
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect as _redirect
from django.urls import path, include, reverse as _reverse

admin.site.site_header = "WeCare Research Admin"
admin.site.site_title = "WeCare Admin"
admin.site.index_title = "Research Dashboard"
admin.site.enable_nav_sidebar = False

def _admin_index(self, request, extra_context=None):
    return _redirect(_reverse("admin:participants_participant_changelist"))

admin.site.index = types.MethodType(_admin_index, admin.site)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("participants.urls")),
    path("api/", include("content.urls")),
    path("api/", include("journal.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)