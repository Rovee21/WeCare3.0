from django.db import models


class Session(models.Model):
    title = models.CharField(max_length=200)
    title_zh = models.CharField(max_length=200, blank=True)
    week_number = models.PositiveSmallIntegerField()
    day_number = models.PositiveSmallIntegerField()

    video_url = models.URLField(blank=True)
    audio_url = models.URLField(blank=True)
    text_content = models.TextField(blank=True)
    text_content_zh = models.TextField(blank=True)

    # Cohort targeting — blank means "show to all" for that dimension
    target_group1 = models.CharField(max_length=20, blank=True)
    target_group2 = models.CharField(max_length=20, blank=True)
    target_group3 = models.CharField(max_length=20, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["week_number", "day_number"]

    def __str__(self):
        return f"W{self.week_number}D{self.day_number}: {self.title}"

    @property
    def week_label(self):
        return f"WEEK {self.week_number}"

    @property
    def media_types(self):
        types = []
        if self.video_url:
            types.append("Video")
        if self.audio_url:
            types.append("Audio")
        if self.text_content:
            types.append("Text")
        return types


class AdditionalResource(models.Model):
    TYPE_VIDEO = "Video"
    TYPE_ARTICLE = "Article"
    TYPE_PDF = "PDF"
    TYPE_CHOICES = [(TYPE_VIDEO, "Video"), (TYPE_ARTICLE, "Article"), (TYPE_PDF, "PDF")]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=200)
    title_zh = models.CharField(max_length=200, blank=True)
    resource_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    url = models.URLField()

    def __str__(self):
        return f"{self.title} ({self.resource_type})"


class ParticipantSession(models.Model):
    """Tracks read/unread state per participant per session."""
    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.CASCADE, related_name="session_states"
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["participant", "session"]

    def __str__(self):
        state = "read" if self.is_read else "unread"
        return f"{self.participant} — {self.session} — {state}"


class EngagementLog(models.Model):
    """One row per engagement event. Fields match CLAUDE.md tracking variables exactly."""
    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.CASCADE, related_name="engagement_logs"
    )
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True)

    course_title = models.CharField(max_length=200, blank=True)
    week_number = models.PositiveSmallIntegerField(null=True, blank=True)

    video_open_count = models.PositiveIntegerField(default=0)
    video_last_time = models.PositiveIntegerField(default=0)       # seconds watched
    read_count = models.PositiveIntegerField(default=0)
    read_minutes = models.FloatField(default=0.0)
    interactive_feature_count = models.PositiveIntegerField(default=0)   # emoji taps
    interactive_feature_comment = models.PositiveIntegerField(default=0)
    infographic_open_count = models.PositiveIntegerField(default=0)
    tracking_download_count = models.PositiveIntegerField(default=0)
    pushup_time = models.DateTimeField(null=True, blank=True)
    push_up = models.CharField(max_length=200, blank=True)

    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-logged_at"]

    def __str__(self):
        return f"{self.participant} engagement @ {self.logged_at:%Y-%m-%d %H:%M}"


class NotificationLog(models.Model):
    TYPE_DAILY = "daily"
    TYPE_UNREAD = "unread_reminder"
    TYPE_VJ = "vj_reminder"
    TYPE_CHOICES = [
        (TYPE_DAILY, "Daily Session"),
        (TYPE_UNREAD, "24hr Unread Reminder"),
        (TYPE_VJ, "Voice Journal Reminder"),
    ]

    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.CASCADE, related_name="notification_logs"
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    push_up = models.CharField(max_length=200, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.participant} — {self.notification_type} @ {self.sent_at:%Y-%m-%d}"
