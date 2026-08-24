from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.http import HttpResponseRedirect
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.models import TokenProxy


class WeCareAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        response = super().login(request, extra_context)
        if isinstance(response, HttpResponseRedirect):
            return HttpResponseRedirect('/admin/')
        return response


admin.site.__class__ = WeCareAdminSite

# Accounts are managed via `createsuperuser`/`eb ssh`, not the admin UI —
# these built-in Django/DRF admin sections have no use here.
admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)

admin.site.site_header = "WeCare Research Admin"
admin.site.site_title = "WeCare Admin"
admin.site.index_title = "Research Dashboard"
admin.site.enable_nav_sidebar = False

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include("participants.urls")),
    path("api/", include("content.urls")),
    path("api/", include("journal.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)