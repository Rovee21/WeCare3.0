from django.db import models


class VoiceJournalPrompt(models.Model):
    week_number = models.PositiveSmallIntegerField(unique=True)
    prompt_en = models.TextField()
    prompt_zh = models.TextField()

    class Meta:
        ordering = ["week_number"]

    def __str__(self):
        return f"Week {self.week_number} VJ Prompt"


class VoiceJournalEntry(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    EMOTION_CALM = "calm"
    EMOTION_NEUTRAL = "neutral"
    EMOTION_ANXIOUS = "anxious"
    EMOTION_SAD = "sad"
    EMOTION_OVERWHELMED = "overwhelmed"
    EMOTION_CHOICES = [
        (EMOTION_CALM, "Calm"),
        (EMOTION_NEUTRAL, "Neutral"),
        (EMOTION_ANXIOUS, "Anxious"),
        (EMOTION_SAD, "Sad"),
        (EMOTION_OVERWHELMED, "Overwhelmed"),
    ]

    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.CASCADE, related_name="journal_entries"
    )
    week_number = models.PositiveSmallIntegerField()
    audio_s3_key = models.CharField(max_length=500, blank=True)
    recording_seconds = models.PositiveIntegerField(default=0)
    transcript = models.TextField(blank=True)
    vj_stress_level = models.PositiveSmallIntegerField(null=True, blank=True)
    emotion_label = models.CharField(
        max_length=20, choices=EMOTION_CHOICES, blank=True
    )
    transcription_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        # One submission per participant per week
        unique_together = ["participant", "week_number"]

    def __str__(self):
        return f"{self.participant} — Week {self.week_number} VJ"
