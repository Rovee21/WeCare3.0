from django.template.response import TemplateResponse
from django.urls import path
from django.contrib import admin
from django.core.mail import send_mail
from django.utils.html import format_html
from django.db.models import Count, Max, Q
from .models import Participant
import csv
import io
from django.http import HttpResponse

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
        "total_time_display",
        "video_time_display", "text_time_display",
        "video_open_count", "emoji_taps_display", "logged_at",
    ]
    readonly_fields = [
        "week_number", "course_title",
        "total_time_display",
        "video_time_display", "text_time_display",
        "video_open_count", "emoji_taps_display", "logged_at",
    ]
    ordering = ["-logged_at"]
    verbose_name = "Engagement Event"
    verbose_name_plural = "Engagement Log"

    def _fmt(self, seconds):
        if not seconds:
            return "—"
        m, s = divmod(seconds, 60)
        return f"{m}:{s:02d}"

    def total_time_display(self, obj):
        total = obj.video_time_seconds + obj.text_time_seconds
        return self._fmt(total)
    total_time_display.short_description = "Total Time"

    def video_time_display(self, obj):
        return self._fmt(obj.video_time_seconds)
    video_time_display.short_description = "Video Time"

    def text_time_display(self, obj):
        return self._fmt(obj.text_time_seconds)
    text_time_display.short_description = "Text Time"

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
        "participant_id_display", "email", "language",
        "group1", "group2", "group3",
        "adrd_relationship_group",
        "is_enrolled", "current_week_display",
        "sessions_completed", "vj_count", "last_active",
        "code_status",
    ]
    search_fields = ["email"]
    readonly_fields = [
        "participant_id_display", "is_enrolled", "enrolled_at",
        "current_week_display", "latest_vj_stress",
        "user", "created_at", "updated_at",
    ]
    inlines = []
    list_per_page = 50

    fieldsets = (
        ("Identity", {
            "fields": ("participant_id_display", "email", "language", "is_enrolled"),
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
            "fields": ("group1", "group2"),
            "description": "Set from offline baseline survey data. Do not change after enrollment.",
        }),
        ("Clinical Indicators (from Voice Journal)", {
            "fields": ("latest_vj_stress",),
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

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:participant_id>/stats/', self.admin_site.admin_view(self.stats_view), name='participant_stats'),
            path('import-csv/', self.admin_site.admin_view(self.csv_import_view), name='participant_csv_import'),
        ]
        return custom + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = '/admin/participants/participant/import-csv/'
        return super().changelist_view(request, extra_context=extra_context)
    
    def csv_import_view(self, request):
        from django.template.response import TemplateResponse

        # Step 3: Final import (no file, has 'import' flag)
        if request.method == 'POST' and request.POST.get('import') == '1':
            print("=== IMPORT TRIGGERED ===")
            csv_data = request.session.get('csv_import_data', '')
            print("Session data length:", len(csv_data))
            reader = csv.DictReader(io.StringIO(csv_data))
            mapping = {
                'email':                   request.POST.get('map_email', ''),
                'first_name':              request.POST.get('map_first_name', ''),
                'last_name':               request.POST.get('map_last_name', ''),
                'label':                   request.POST.get('map_label', ''),
                'gender':                  request.POST.get('map_gender', ''),
                'age':                     request.POST.get('map_age', ''),
                'adrd_relationship_group': request.POST.get('map_relationship', ''),
                'group1':                  request.POST.get('map_group1', ''),
                'group2':                  request.POST.get('map_group2', ''),
                'group3':                  request.POST.get('map_group3', ''),
                'adrd_stage':              request.POST.get('map_adrd_stage', ''),
            }

            created, skipped, errors = 0, 0, []
            for row in reader:
                email = row.get(mapping['email'], '').strip()
                if not email:
                    skipped += 1
                    continue
                if Participant.objects.filter(email=email).exists():
                    skipped += 1
                    continue
                try:
                    age_val = row.get(mapping['age'], '').strip()
                    p = Participant(
                        email=email,
                        first_name=row.get(mapping['first_name'], '').strip(),
                        last_name=row.get(mapping['last_name'], '').strip(),
                        label=row.get(mapping['label'], '').strip(),
                        gender=row.get(mapping['gender'], '').strip().lower()[:10],
                        age=int(age_val) if age_val.isdigit() else None,
                        adrd_relationship_group=row.get(mapping['adrd_relationship_group'], '').strip().lower()[:20] or 'relative',
                        group1=row.get(mapping['group1'], '').strip().lower()[:20] or 'intervention',
                        group2=row.get(mapping['group2'], '').strip().lower()[:20] or 'moderate',
                        group3=row.get(mapping['group3'], '').strip().lower()[:20] or 'low',
                        adrd_stage=row.get(mapping['adrd_stage'], '').strip().lower()[:20],
                        language='en',
                        enrollment_week=1,
                    )
                    p.save()
                    p.generate_enrollment_code()
                    created += 1
                except Exception as e:
                    errors.append(f"Row {email}: {e}")

            self.message_user(request, f"Import complete: {created} created, {skipped} skipped, {len(errors)} errors.")
            if errors:
                for err in errors[:5]:
                    self.message_user(request, err, level='warning')
            return self._redirect_to_changelist(request)

        # Step 2: Preview (has file upload)
        if request.method == 'POST' and 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            decoded = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded))
            rows = list(reader)
            headers = reader.fieldnames
            request.session['csv_import_data'] = decoded

            context = {
                **self.admin_site.each_context(request),
                'title': 'Import Participants from CSV',
                'headers': headers,
                'rows': rows[:5],
                'all_rows': rows,
                'field_map': {
                    'email': 'Email *',
                    'first_name': 'First Name',
                    'last_name': 'Last Name',
                    'label': 'Label / Display Name',
                    'gender': 'Gender',
                    'age': 'Age',
                    'relationship': 'Care Relationship',
                    'group1': 'Study Cohort (intervention/control)',
                    'group2': 'Condition Group (mild/moderate/severe)',
                    'group3': 'Stress Group (high/low)',
                    'adrd_stage': 'ADRD Stage',
                },
            }
            return TemplateResponse(request, 'admin/participants/csv_preview.html', context)

        # Step 1: Show upload form
        context = {
            **self.admin_site.each_context(request),
            'title': 'Import Participants from CSV',
        }
        return TemplateResponse(request, 'admin/participants/csv_upload.html', context)

    def _redirect_to_changelist(self, request):
        from django.shortcuts import redirect
        return redirect('/admin/participants/participant/')

    def stats_view(self, request, participant_id):
        from content.models import EngagementLog, ParticipantSession
        from journal.models import VoiceJournalEntry
        from django.db.models import Sum

        participant = Participant.objects.get(pk=participant_id)

        raw_logs = EngagementLog.objects.filter(participant=participant).select_related('session').order_by('week_number', 'session__day_number')

        totals = raw_logs.aggregate(
            total_video=Sum('video_time_seconds'),
            total_text=Sum('text_time_seconds'),
        )

        engagement_logs = []
        for log in raw_logs:
            total = log.video_time_seconds + log.text_time_seconds
            m, s = divmod(total, 60)
            log.total_time_display = f"{m}:{s:02d}" if total else "—"
            m, s = divmod(log.video_time_seconds, 60)
            log.video_time_display = f"{m}:{s:02d}" if log.video_time_seconds else "—"
            m, s = divmod(log.text_time_seconds, 60)
            log.text_time_display = f"{m}:{s:02d}" if log.text_time_seconds else "—"
            engagement_logs.append(log)
        session_completions = ParticipantSession.objects.filter(participant=participant).select_related('session').order_by('session__week_number', 'session__day_number')
        vj_entries = VoiceJournalEntry.objects.filter(participant=participant).order_by('week_number')

        def fmt(seconds):
            if not seconds:
                return '—'
            m, s = divmod(seconds, 60)
            return f'{m}:{s:02d}'

        total_seconds = (totals['total_video'] or 0) + (totals['total_text'] or 0)

        context = {
            **self.admin_site.each_context(request),
            'participant': participant,
            'engagement_logs': engagement_logs,
            'session_completions': session_completions,
            'vj_entries': vj_entries,
            'summary': {
                'sessions_read': session_completions.filter(is_read=True).count(),
                'total_time': fmt(total_seconds),
                'total_video_time': fmt(totals['total_video'] or 0),
                'total_text_time': fmt(totals['total_text'] or 0),
                'vj_submitted': vj_entries.count(),
                'latest_stress': vj_entries.last().vj_stress_level if vj_entries.exists() else '—',
                'latest_emotion': vj_entries.last().get_emotion_label_display() if vj_entries.exists() else '—',
                'last_active': raw_logs.order_by('-logged_at').first().logged_at if raw_logs.exists() else None,
            },
            'fmt': fmt,
            'title': f'{participant.participant_id} — Stats',
        }
        return TemplateResponse(request, 'admin/participant_stats.html', context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_history'] = False
        extra_context['stats_url'] = f'/admin/participants/participant/{object_id}/stats/'
        return super().change_view(request, object_id, form_url, extra_context)

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
                    f"Hello {p.participant_id},\n\n"
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