from django.urls import path
from . import views

urlpatterns = [
    path("sessions/", views.session_list, name="session_list"),
    path("sessions/today/", views.session_today, name="session_today"),
    path("sessions/<int:session_id>/read/", views.mark_read, name="mark_read"),
    path("engagement/", views.log_engagement, name="log_engagement"),
]
