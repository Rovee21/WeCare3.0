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
        "cohort_target", "has_video", "has_audio", "has_text",
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
            "fields": ("video_url", "audio_url"),
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

    def has_audio(self, obj):
        return bool(obj.audio_url)
    has_audio.boolean = True
    has_audio.short_description = "Audio"

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
        "video_watch_time", "video_open_count",
        "read_time", "read_count",
        "emoji_taps", "logged_at",
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
    participant_label.admin_order_field = "participant__email"

    def video_watch_time(self, obj):
        if not obj.video_last_time:
            return format_html('<span style="color:#999;">—</span>')
        m, s = divmod(obj.video_last_time, 60)
        return f"{m}:{s:02d}"
    video_watch_time.short_description = "Watch Time"
    video_watch_time.admin_order_field = "video_last_time"

    def read_time(self, obj):
        if not obj.read_minutes:
            return format_html('<span style="color:#999;">—</span>')
        return f"{obj.read_minutes:.1f} min"
    read_time.short_description = "Read Time"
    read_time.admin_order_field = "read_minutes"

    def emoji_taps(self, obj):
        if not obj.interactive_feature_count:
            return format_html('<span style="color:#999;">—</span>')
        return obj.interactive_feature_count
    emoji_taps.short_description = "Emoji Taps"
    emoji_taps.admin_order_field = "interactive_feature_count"


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        "participant_label", "notification_type", "push_up",
        "sent_at", "opened_at", "was_opened",
    ]
    list_filter = ["notification_type", "sent_at"]
    search_fields = ["participant__email", "push_up"]
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
