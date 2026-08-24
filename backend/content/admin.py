from types import SimpleNamespace
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Session, AdditionalResource, EngagementLog, NotificationLog, ParticipantSession,
    DailyNotificationSettings,
)
from .services import upload_video_to_s3


class AdditionalResourceInline(admin.TabularInline):
    model = AdditionalResource
    extra = 1
    fields = ["title", "title_zh", "resource_type", "url"]


class SessionAdminForm(forms.ModelForm):
    video_upload = forms.FileField(
        required=False,
        label="Upload MP4 video",
        help_text="Uploads directly to S3 and fills in Video URL below.",
    )

    class Meta:
        model = Session
        fields = "__all__"

    def clean_video_upload(self):
        f = self.cleaned_data.get("video_upload")
        if f and not (f.content_type == "video/mp4" or f.name.lower().endswith(".mp4")):
            raise forms.ValidationError("Please upload an MP4 video file.")
        return f

    def clean(self):
        cleaned_data = super().clean()
        upload = cleaned_data.get("video_upload")
        week = cleaned_data.get("week_number")
        day = cleaned_data.get("day_number")
        if upload and week is not None and day is not None:
            try:
                cleaned_data["video_url"] = upload_video_to_s3(
                    upload, SimpleNamespace(week_number=week, day_number=day)
                )
            except Exception as e:
                raise forms.ValidationError(f"Video upload failed: {e}")
        return cleaned_data


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    form = SessionAdminForm
    list_display = [
        "week_number", "day_number", "title",
        "target_group1_display", "target_group2_display", "target_group3_display",
        "is_active",
    ]
    list_filter = ["week_number", "target_group1", "target_group2", "target_group3", "is_active"]
    search_fields = ["title", "title_zh"]
    inlines = [AdditionalResourceInline]
    list_per_page = 50

    fieldsets = (
        ("Identity", {
            "fields": ("week_number", "day_number", "title", "title_zh", "is_active"),
        }),
        ("Cohort Targeting", {
            "fields": ("target_group1", "target_group2", "target_group3"),
            "description": "Leave blank to show this session to all participants in that dimension.",
        }),
        ("Media URLs", {
            "fields": ("video_upload", "video_url"),
            "description": "Upload an MP4 directly, or paste an S3/external video URL.",
        }),
        ("Text Content", {
            "fields": ("text_content", "text_content_zh"),
            "classes": ("wide",),
        }),
    )

    def target_group1_display(self, obj):
        if not obj.target_group1:
            return format_html('<span style="color:#999;">All</span>')
        return obj.get_target_group1_display()
    target_group1_display.short_description = "Group 1 (Intervention/Control)"
    target_group1_display.admin_order_field = "target_group1"

    def target_group2_display(self, obj):
        if not obj.target_group2:
            return format_html('<span style="color:#999;">All</span>')
        return obj.get_target_group2_display()
    target_group2_display.short_description = "Group 2 (Mild/Moderate/Severe)"
    target_group2_display.admin_order_field = "target_group2"

    def target_group3_display(self, obj):
        if not obj.target_group3:
            return format_html('<span style="color:#999;">All</span>')
        return obj.get_target_group3_display()
    target_group3_display.short_description = "Group 3 (High/Low Stress)"
    target_group3_display.admin_order_field = "target_group3"


@admin.register(EngagementLog)
class EngagementLogAdmin(admin.ModelAdmin):
    list_display = [
        "participant_label", "course_title", "week_number",
        "total_time", "video_time", "video_watch_time", "text_time",
        "video_open_count", "emoji_taps", "logged_at",
    ]
    list_filter = ["week_number", "logged_at"]
    search_fields = ["participant__email", "course_title"]
    date_hierarchy = "logged_at"
    list_per_page = 100
    readonly_fields = [f.name for f in EngagementLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def participant_label(self, obj):
        return obj.participant.participant_id if obj.participant else "—"
    participant_label.short_description = "Participant"

    def _fmt_time(self, seconds):
        if not seconds:
            return format_html('<span style="color:#999;">—</span>')
        m, s = divmod(seconds, 60)
        return f"{m}:{s:02d}"

    def total_time(self, obj):
        total = obj.video_time_seconds + obj.text_time_seconds
        return self._fmt_time(total)
    total_time.short_description = "Total Time"

    def video_time(self, obj):
        return self._fmt_time(obj.video_time_seconds)
    video_time.short_description = "Video Time"

    def video_watch_time(self, obj):
        return self._fmt_time(obj.video_watch_seconds)
    video_watch_time.short_description = "Video Watch Time"

    def text_time(self, obj):
        return self._fmt_time(obj.text_time_seconds)
    text_time.short_description = "Text Time"

    def emoji_taps(self, obj):
        if not obj.interactive_feature_count:
            return format_html('<span style="color:#999;">—</span>')
        return obj.interactive_feature_count
    emoji_taps.short_description = "Emoji Taps"


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        "participant_label", "notification_type", "title", "push_up", "status",
        "scheduled_for", "sent_at", "actually_sent_at", "opened_at", "was_opened",
    ]
    list_filter = ["notification_type", "status", "sent_at"]
    search_fields = ["participant__email", "title", "push_up"]
    date_hierarchy = "sent_at"
    list_per_page = 100
    readonly_fields = [f.name for f in NotificationLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def participant_label(self, obj):
        return obj.participant.participant_id if obj.participant else "—"
    participant_label.short_description = "Participant"
    participant_label.admin_order_field = "participant__email"

    def was_opened(self, obj):
        if obj.opened_at:
            return format_html('<span style="color:#2e7d32;">✓ Opened</span>')
        return format_html('<span style="color:#e53935;">Not opened</span>')
    was_opened.short_description = "Opened?"


@admin.register(DailyNotificationSettings)
class DailyNotificationSettingsAdmin(admin.ModelAdmin):
    """Singleton settings — only one row should ever exist. Adding is blocked once a
    row exists, and deleting is blocked outright so there's always exactly one to edit."""
    list_display = ["send_time", "title", "body", "is_enabled", "updated_at"]
    fields = ["send_time", "title", "body", "is_enabled", "last_sent_date"]
    readonly_fields = ["last_sent_date"]

    def has_add_permission(self, request):
        return not DailyNotificationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Skip straight to the (only) row's edit form instead of a list view of one item.
        settings_obj, _ = DailyNotificationSettings.objects.get_or_create()
        from django.shortcuts import redirect
        return redirect("admin:content_dailynotificationsettings_change", settings_obj.pk)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                "<int:object_id>/reset-last-sent/",
                self.admin_site.admin_view(self.reset_last_sent_view),
                name="content_dailynotificationsettings_reset_last_sent",
            ),
        ]
        return custom + urls

    def reset_last_sent_view(self, request, object_id):
        from django.shortcuts import redirect, get_object_or_404
        settings_obj = get_object_or_404(DailyNotificationSettings, pk=object_id)
        settings_obj.last_sent_date = None
        settings_obj.save(update_fields=["last_sent_date"])
        self.message_user(
            request,
            "Reset — the daily notification can now send again today. "
            "This does not send anything itself; it only clears the "
            "\"already sent today\" flag for the next scheduled check-in.",
        )
        return redirect("admin:content_dailynotificationsettings_change", object_id)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["reset_last_sent_url"] = f"/admin/content/dailynotificationsettings/{object_id}/reset-last-sent/"
        return super().change_view(request, object_id, form_url, extra_context)
