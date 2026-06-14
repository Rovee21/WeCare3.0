from django.contrib import admin
from django.utils.html import format_html
from .models import VoiceJournalPrompt, VoiceJournalEntry


@admin.register(VoiceJournalPrompt)
class VoiceJournalPromptAdmin(admin.ModelAdmin):
    list_display = ["week_number", "prompt_en"]
    ordering = ["week_number"]
    fields = ["week_number", "prompt_en", "prompt_zh"]


@admin.register(VoiceJournalEntry)
class VoiceJournalEntryAdmin(admin.ModelAdmin):
    list_display = [
        "participant_label", "week_number", "duration_display",
        "vj_stress_display", "transcription_status_display",
        "transcript_excerpt", "submitted_at",
    ]
    list_filter = ["week_number", "transcription_status", "submitted_at"]
    search_fields = ["participant__email", "transcript"]
    date_hierarchy = "submitted_at"
    list_per_page = 50
    readonly_fields = [
        "participant", "week_number", "audio_s3_key",
        "recording_seconds", "transcription_status", "submitted_at",
    ]
    # Transcript is editable so the research team can correct/annotate it
    fields = [
        "participant", "week_number", "recording_seconds",
        "vj_stress_level", "transcription_status", "submitted_at",
        "audio_s3_key", "transcript",
    ]

    def has_add_permission(self, request):
        return False

    def participant_label(self, obj):
        return obj.participant.participant_id if obj.participant else "—"
    participant_label.short_description = "Participant"
    participant_label.admin_order_field = "participant__email"

    def duration_display(self, obj):
        m, s = divmod(obj.recording_seconds, 60)
        return f"{m}m {s:02d}s"
    duration_display.short_description = "Duration"
    duration_display.admin_order_field = "recording_seconds"

    def vj_stress_display(self, obj):
        if obj.vj_stress_level is None:
            return format_html('<span style="color:#999;">—</span>')
        level = obj.vj_stress_level
        if level <= 3:
            color = "#2e7d32"
        elif level <= 6:
            color = "#f57c00"
        else:
            color = "#c62828"
        return format_html(
            '<span style="color:{};font-weight:600;">{}/10</span>', color, level
        )
    vj_stress_display.short_description = "Stress"
    vj_stress_display.admin_order_field = "vj_stress_level"

    def transcription_status_display(self, obj):
        colors = {
            "pending": ("#999", "⏳ Pending"),
            "processing": ("#1565c0", "⚙ Processing"),
            "completed": ("#2e7d32", "✓ Done"),
            "failed": ("#c62828", "✗ Failed"),
        }
        color, label = colors.get(obj.transcription_status, ("#999", obj.transcription_status))
        return format_html('<span style="color:{};">{}</span>', color, label)
    transcription_status_display.short_description = "Transcription"

    def transcript_excerpt(self, obj):
        if not obj.transcript:
            return format_html('<span style="color:#999;">No transcript</span>')
        excerpt = obj.transcript[:80] + ("…" if len(obj.transcript) > 80 else "")
        return format_html('<span style="font-style:italic;color:#555;">{}</span>', excerpt)
    transcript_excerpt.short_description = "Transcript Preview"
