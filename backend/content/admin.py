from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from .models import Session, AdditionalResource, EngagementLog, NotificationLog, ParticipantSession


class AdditionalResourceInline(admin.TabularInline):
    model = AdditionalResource
    extra = 1
    fields = ["title", "title_zh", "resource_type", "url"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        "week_number", "day_number", "title",
        "cohort_target", "has_video", "has_text",
        "participants_read", "is_active",
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
            "fields": ("video_url",),
            "description": "Enter S3 URLs or external video embed URLs.",
        }),
        ("Text Content", {
            "fields": ("text_content", "text_content_zh"),
            "classes": ("wide",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _read_count=Count("participantsession", filter=Q(participantsession__is_read=True))
        )

    def cohort_target(self, obj):
        parts = [
            p for p in [obj.target_group1, obj.target_group2, obj.target_group3] if p
        ]
        return " · ".join(p.replace("_", " ").title() for p in parts) if parts else format_html('<span style="color:#999;">All</span>')
    cohort_target.short_description = "Cohort Target"

    def has_video(self, obj):
        return bool(obj.video_url)
    has_video.boolean = True
    has_video.short_description = "Video"

    def has_text(self, obj):
        return bool(obj.text_content)
    has_text.boolean = True
    has_text.short_description = "Text"

    def participants_read(self, obj):
        count = getattr(obj, "_read_count", 0)
        color = "#2e7d32" if count > 0 else "#999"
        return format_html('<span style="color:{};">{}</span>', color, count)
    participants_read.short_description = "# Read"
    participants_read.admin_order_field = "_read_count"


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
