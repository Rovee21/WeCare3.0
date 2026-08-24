from django.urls import path
from . import views

urlpatterns = [
    path("sessions/", views.session_list, name="session_list"),
    path("sessions/today/", views.session_today, name="session_today"),
    path("sessions/<int:session_id>/start/", views.mark_in_progress, name="mark_in_progress"),
    path("sessions/<int:session_id>/read/", views.mark_read, name="mark_read"),
    path("engagement/", views.log_engagement, name="log_engagement"),
    path("internal/trigger-daily-notification/", views.trigger_daily_notification_check, name="trigger_daily_notification"),
    path("internal/trigger-scheduled-notifications/", views.trigger_scheduled_notifications, name="trigger_scheduled_notifications"),
]
