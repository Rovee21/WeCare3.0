from django.urls import path
from . import views

urlpatterns = [
    path("journal/prompt/", views.journal_prompt, name="journal_prompt"),
    path("journal/upload/", views.upload_url, name="journal_upload_url"),
    path("journal/submit/", views.submit_entry, name="journal_submit"),
]
