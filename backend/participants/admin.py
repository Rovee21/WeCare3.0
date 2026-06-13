from django.contrib import admin
from django.core.mail import send_mail
from django.utils.html import format_html
from django.db.models import Count, Max, Q
from .models import Participant


class VoiceJournalInline(admin.TabularInline):
    model = None  # set below
    extra = 0
    can_delete = False
    fields = ["week_number", "duration_display", "vj_stress_level", "emotion_label", "transcription_status", "submitted_at"]
    readonly_fields = ["week_number", "duration_display", "vj_stress_level", "emotion_label", "transcription_status", "submitted_at"]
    verbose_name = "Voice Journal Submission"
    verbose_name_plural = "Voice Journal Submissions"
    ordering = ["week_number"]

    def duration_display(self, obj):
        m, s = divmod(obj.recording_seconds, 60)
        return f"{m}m {s:02d}s"
    duration_display.short_description = "Duration"

    def has_add_permission(self, request, obj=None):
        return False


class EngagementLogInline(admin.TabularInline):
    model = None  # set in _setup_inlines()
    extra = 0
    can_delete = False
    fields = [
        "week_number", "course_title",
        "video_watch_display", "video_open_count",
        "read_time_display", "read_count",
        "emoji_taps_display", "logged_at",
    ]
    readonly_fields = [
        "week_number", "course_title",
        "video_watch_display", "video_open_count",
        "read_time_display", "read_count",
        "emoji_taps_display", "logged_at",
    ]
    ordering = ["-logged_at"]
    verbose_name = "Engagement Event"
    verbose_name_plural = "Engagement Log"

    def video_watch_display(self, obj):
        if not obj.video_last_time:
            return "—"
        m, s = divmod(obj.video_last_time, 60)
        return f"{m}:{s:02d}"
    video_watch_display.short_description = "Watch Time"

    def read_time_display(self, obj):
        if not obj.read_minutes:
            return "—"
        return f"{obj.read_minutes:.1f} min"
    read_time_display.short_description = "Read Time"

    def emoji_taps_display(self, obj):
        return obj.interactive_feature_count or "—"
    emoji_taps_display.short_description = "Emoji Taps"

    def has_add_permission(self, request, obj=None):
        return False


class SessionCompletionInline(admin.TabularInline):
    model = None  # set below
    extra = 0
    can_delete = False
    fields = ["session", "is_read", "read_at"]
    readonly_fields = ["session", "is_read", "read_at"]
    verbose_name = "Session Completion"
    verbose_name_plural = "Session Completions"

    def has_add_permission(self, request, obj=None):
        return False


def _setup_inlines():
    from journal.models import VoiceJournalEntry
    from content.models import ParticipantSession, EngagementLog
    VoiceJournalInline.model = VoiceJournalEntry
    SessionCompletionInline.model = ParticipantSession
    EngagementLogInline.model = EngagementLog


_setup_inlines()


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = [
        "label", "email", "language",
        "group1", "group2", "group3",
        "adrd_relationship_group",
        "is_enrolled", "current_week_display",
        "sessions_completed", "vj_count", "last_active",
        "code_status",
    ]
    search_fields = ["label", "email"]
    readonly_fields = [
        "participant_id_display", "is_enrolled", "enrolled_at",
        "current_week_display", "latest_vj_stress", "latest_emotion_status",
        "user", "created_at", "updated_at",
    ]
    inlines = [EngagementLogInline, SessionCompletionInline, VoiceJournalInline]
    date_hierarchy = "enrolled_at"
    list_per_page = 50

    fieldsets = (
        ("Identity", {
            "fields": ("participant_id_display", "label", "email", "language", "is_enrolled"),
        }),
        ("Demographics", {
            "fields": ("gender", "age"),
            "description": "From baseline survey.",
        }),
        ("Study Progress", {
            "fields": ("enrolled_at", "current_week_display", "enrollment_week"),
        }),
        ("Caregiver Profile", {
            "fields": ("adrd_relationship_group", "group3"),
            "description": "Relationship and burden level from baseline survey.",
        }),
        ("Cohort Assignment", {
            "fields": ("group1", "group2", "stage"),
            "description": "Set from offline baseline survey data. Do not change after enrollment.",
        }),
        ("Clinical Indicators (from Voice Journal)", {
            "fields": ("latest_vj_stress", "latest_emotion_status"),
        }),
        ("Enrollment", {
            "fields": ("enrollment_code",),
            "classes": ("collapse",),
        }),
        ("System", {
            "fields": ("user", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    actions = ["generate_code_only", "generate_and_email_code"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _sessions_completed=Count("session_states", filter=Q(session_states__is_read=True)),
            _vj_count=Count("journal_entries"),
            _last_active=Max("engagement_logs__logged_at"),
        )

    def participant_id_display(self, obj):
        return obj.participant_id if obj.pk else "—"
    participant_id_display.short_description = "Participant ID"

    def current_week_display(self, obj):
        if not obj.is_enrolled:
            return "—"
        week = obj.current_week_number
        return format_html(
            '<span style="background:#e8f5e9;color:#2e7d32;padding:2px 8px;border-radius:10px;font-weight:600;">Week {}</span>',
            week,
        )
    current_week_display.short_description = "Current Week"

    def latest_vj_stress(self, obj):
        entry = obj.journal_entries.order_by("-submitted_at").first()
        if not entry:
            return format_html('<span style="color:#999;">No submissions yet</span>')
        if entry.vj_stress_level is None:
            return format_html('<span style="color:#999;">— awaiting report</span>')
        level = entry.vj_stress_level
        if level <= 3:
            color = "#2e7d32"
        elif level <= 6:
            color = "#f57c00"
        else:
            color = "#c62828"
        return format_html(
            '<span style="color:{};font-weight:600;">{}/10</span> '
            '<span style="color:#999;font-size:11px;">(Week {})</span>',
            color, level, entry.week_number,
        )
    latest_vj_stress.short_description = "VJ Stress Level"

    def latest_emotion_status(self, obj):
        entry = obj.journal_entries.exclude(emotion_label="").order_by("-submitted_at").first()
        if not entry:
            return format_html('<span style="color:#999;">No data yet</span>')
        colors = {
            "calm": "#2e7d32",
            "neutral": "#555",
            "anxious": "#f57c00",
            "sad": "#1565c0",
            "overwhelmed": "#c62828",
        }
        color = colors.get(entry.emotion_label, "#555")
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span> '
            '<span style="color:#999;font-size:11px;">(Week {})</span>',
            color, entry.get_emotion_label_display(), entry.week_number,
        )
    latest_emotion_status.short_description = "Emotion Status"

    def sessions_completed(self, obj):
        count = getattr(obj, "_sessions_completed", 0)
        color = "#2e7d32" if count > 0 else "#999"
        return format_html('<span style="color:{};">{}</span>', color, count)
    sessions_completed.short_description = "Sessions Read"
    sessions_completed.admin_order_field = "_sessions_completed"

    def vj_count(self, obj):
        count = getattr(obj, "_vj_count", 0)
        color = "#1565c0" if count > 0 else "#999"
        return format_html('<span style="color:{};">{} / 7</span>', color, count)
    vj_count.short_description = "VJ Submitted"
    vj_count.admin_order_field = "_vj_count"

    def last_active(self, obj):
        dt = getattr(obj, "_last_active", None)
        if not dt:
            return format_html('<span style="color:#999;">Never</span>')
        return format_html('<span title="{}">{}</span>', dt.strftime("%Y-%m-%d %H:%M"), dt.strftime("%b %d"))
    last_active.short_description = "Last Active"
    last_active.admin_order_field = "_last_active"

    def code_status(self, obj):
        if obj.is_enrolled:
            return format_html('<span style="color:#2e7d32;font-weight:600;">✓ Enrolled</span>')
        if obj.enrollment_code:
            return format_html(
                '<code style="background:#fff8e1;padding:2px 8px;border-radius:3px;letter-spacing:1px;">{}</code>',
                obj.enrollment_code,
            )
        return format_html('<span style="color:#e53935;">No code</span>')
    code_status.short_description = "Code / Status"

    @admin.action(description="Generate enrollment code (no email)")
    def generate_code_only(self, request, queryset):
        count = 0
        for p in queryset.filter(is_enrolled=False):
            p.generate_enrollment_code()
            count += 1
        self.message_user(request, f"Generated enrollment codes for {count} participant(s).")

    @admin.action(description="Generate code and email participant")
    def generate_and_email_code(self, request, queryset):
        sent, skipped = 0, 0
        for p in queryset:
            if p.is_enrolled:
                skipped += 1
                continue
            code = p.generate_enrollment_code()
            send_mail(
                subject="Your WeCare Enrollment Code",
                message=(
                    f"Hello {p.label},\n\n"
                    f"Your WeCare program enrollment code is:\n\n"
                    f"    {code}\n\n"
                    f"Please enter this code in the WeCare app to get started.\n\n"
                    f"If you have any questions, reply to this email or contact us at wecaremason@gmail.com\n\n"
                    f"— The WeCare Research Team"
                ),
                from_email="wecaremason@gmail.com",
                recipient_list=[p.email],
                fail_silently=False,
            )
            sent += 1
        msg = f"Sent enrollment codes to {sent} participant(s)."
        if skipped:
            msg += f" Skipped {skipped} already-enrolled participant(s)."
        self.message_user(request, msg)
