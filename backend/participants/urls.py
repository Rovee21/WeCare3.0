from django.urls import path
from . import views

urlpatterns = [
    path("enroll/", views.enroll, name="enroll"),
    path("profile/", views.profile, name="profile"),
    path("account/", views.delete_account, name="delete_account"),
]
