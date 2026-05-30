from django.contrib import admin
from django.core.mail import send_mail
from django.utils.html import format_html
from django.db.models import Count, Max, Q
from .models import Participant


class VoiceJournalInline(admin.TabularInline):
    # Late import to avoid circular dependency at module load
    @classmethod
    def _get_model(cls):
        from journal.models import VoiceJournalEntry
        return VoiceJournalEntry

    model = None  # set below after class definition
    extra = 0
    can_delete = False
    fields = ["week_number", "duration_display", "vj_stress_level", "transcription_status", "submitted_at"]
    readonly_fields = ["week_number", "duration_display", "vj_stress_level", "transcription_status", "submitted_at"]
    verbose_name = "Voice Journal Submission"
    verbose_name_plural = "Voice Journal Submissions"
    ordering = ["week_number"]

    def duration_display(self, obj):
        m, s = divmod(obj.recording_seconds, 60)
        return f"{m}m {s:02d}s"
    duration_display.short_description = "Duration"

    def has_add_permission(self, request, obj=None):
        return False


class SessionCompletionInline(admin.TabularInline):
    model = None  # set below after class definition
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
    from content.models import ParticipantSession
    VoiceJournalInline.model = VoiceJournalEntry
    SessionCompletionInline.model = ParticipantSession


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
    list_filter = [
        "is_enrolled", "language",
        "group1", "group2", "group3",
        "adrd_relationship_group", "stage",
    ]
    search_fields = ["label", "email"]
    readonly_fields = [
        "participant_id_display", "is_enrolled", "enrolled_at",
        "current_week_display", "user", "created_at", "updated_at",
    ]
    inlines = [SessionCompletionInline, VoiceJournalInline]
    date_hierarchy = "enrolled_at"
    list_per_page = 50

    fieldsets = (
        ("Identity", {
            "fields": ("participant_id_display", "label", "email", "language"),
        }),
        ("Cohort Assignment (from baseline survey)", {
            "fields": ("group1", "group2", "group3", "adrd_relationship_group", "stage"),
            "description": "Set from offline baseline survey data. Do not change after enrollment.",
        }),
        ("Enrollment", {
            "fields": ("enrollment_code", "enrollment_week", "is_enrolled", "enrolled_at", "current_week_display"),
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
    current_week_display.short_description = "Program Week"

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
