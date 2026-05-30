from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "WeCare Research Admin"
admin.site.site_title = "WeCare Admin"
admin.site.index_title = "Research Dashboard"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("participants.urls")),
    path("api/", include("content.urls")),
    path("api/", include("journal.urls")),
]
