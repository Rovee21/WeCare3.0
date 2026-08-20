from django.db import models
from django.contrib.auth.models import User


class Session(models.Model):
    title = models.CharField(max_length=200)
    title_zh = models.CharField(max_length=200, blank=True)
    week_number = models.PositiveSmallIntegerField()
    day_number = models.PositiveSmallIntegerField()

    video_url = models.URLField(blank=True)
    audio_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='session_videos/', blank=True, null=True)
    audio_file = models.FileField(upload_to='session_audio/', blank=True, null=True)
    text_content = models.TextField(blank=True)
    text_content_zh = models.TextField(blank=True)

    # Cohort targeting — blank means "show to all" for that dimension
    target_group1 = models.CharField(
        max_length=20, blank=True,
        choices=[('', 'All'), ('intervention', 'Intervention'), ('control', 'Control')]
    )
    target_group2 = models.CharField(
        max_length=20, blank=True,
        choices=[('', 'All'), ('mild', 'Mild'), ('moderate', 'Moderate'), ('severe', 'Severe')]
    )
    target_group3 = models.CharField(
        max_length=20, blank=True,
        choices=[('', 'All'), ('high', 'High Stress'), ('low', 'Low Stress')]
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["week_number", "day_number"]

    def __str__(self):
        return f"W{self.week_number}D{self.day_number}: {self.title}"

    @property
    def week_label(self) -> str:
        return f"WEEK {self.week_number}"

    @property
    def media_types(self) -> list[str]:
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
    """One row per engagement event."""
    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.CASCADE, related_name="engagement_logs"
    )
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True, blank=True)

    course_title = models.CharField(max_length=200, blank=True)
    week_number = models.PositiveSmallIntegerField(null=True, blank=True)

    video_open_count = models.PositiveIntegerField(default=0)
    video_last_time = models.PositiveIntegerField(default=0)       # seconds watched
    video_time_seconds = models.PositiveIntegerField(default=0)
    video_watch_seconds = models.PositiveIntegerField(default=0, help_text="Actual video playback time (from pressing play to pausing/stopping), as opposed to video_time_seconds which measures time the Video tab was simply active/visible.")
    audio_time_seconds = models.PositiveIntegerField(default=0)
    text_time_seconds = models.PositiveIntegerField(default=0)
    read_count = models.PositiveIntegerField(default=0)
    read_minutes = models.FloatField(default=0.0)
    interactive_feature_count = models.PositiveIntegerField(default=0)   # emoji taps
    interactive_feature_comment = models.PositiveIntegerField(default=0)
    infographic_open_count = models.PositiveIntegerField(default=0)
    tracking_download_count = models.PositiveIntegerField(default=0)
    pushup_time = models.DateTimeField(null=True, blank=True)
    push_up = models.CharField(max_length=200, blank=True)

    logged_at = models.DateTimeField(auto_now_add=True)
    @property
    def total_time_seconds(self):
        return self.video_time_seconds + self.audio_time_seconds + self.text_time_seconds

    class Meta:
        ordering = ["-logged_at"]
        unique_together = ["participant", "session"]

    def __str__(self):
        return f"{self.participant} engagement @ {self.logged_at:%Y-%m-%d %H:%M}"


class NotificationLog(models.Model):
    TYPE_DAILY = "daily"
    TYPE_UNREAD = "unread_reminder"
    TYPE_VJ = "vj_reminder"
    TYPE_MANUAL = "manual"
    TYPE_CHOICES = [
        (TYPE_DAILY, "Daily Session"),
        (TYPE_UNREAD, "24hr Unread Reminder"),
        (TYPE_VJ, "Voice Journal Reminder"),
        (TYPE_MANUAL, "Manual / Ad-hoc"),
    ]

    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_NO_TOKEN = "skipped_no_token"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
        (STATUS_NO_TOKEN, "Skipped — No Token"),
    ]

    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.CASCADE, related_name="notification_logs"
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    push_up = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SENT)
    # scheduled_for: null means "send immediately". A future datetime means this row was
    # created as a pending notification awaiting send_scheduled_notifications to process it.
    scheduled_for = models.DateTimeField(null=True, blank=True)
    # sent_at (auto_now_add) is the row's creation time — for a scheduled notification that's
    # when it was scheduled, not when it was delivered. actually_sent_at is set separately,
    # at the moment a real send attempt is made (immediately for direct sends, or later by
    # the management command for scheduled ones), regardless of whether that attempt succeeded.
    actually_sent_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.participant} — {self.notification_type} @ {self.sent_at:%Y-%m-%d}"


class DailyNotificationSettings(models.Model):
    """Singleton config for the automated daily reminder — one global row, not
    per-cohort or per-participant. See DailyNotificationSettingsAdmin for how the
    single-row constraint is enforced."""
    send_time = models.TimeField(default="19:00", help_text="Time of day (in the server's local timezone) the daily reminder is sent to all enrolled, non-waitlisted participants.")
    title = models.CharField(max_length=200, default="Your session is ready!", help_text="Notification title. Customizable by admin.")
    body = models.CharField(max_length=200, default="Come check out today's session in the WeCare app.", help_text="Notification body text. Customizable by admin.")
    is_enabled = models.BooleanField(default=True, help_text="If unchecked, no daily notifications will be sent, regardless of time.")
    last_sent_date = models.DateField(null=True, blank=True, help_text="The date the daily batch was last sent — used internally to prevent sending twice in the same day.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Daily notification — {self.send_time} ({'enabled' if self.is_enabled else 'disabled'})"


class SessionOverride(models.Model):
    """Per-participant, per-session manual unlock/lock, set by an admin — takes
    priority over the automatic day/sequential-read gating for that one session."""
    OVERRIDE_UNLOCK = "force_unlock"
    OVERRIDE_LOCK = "force_lock"
    OVERRIDE_CHOICES = [
        (OVERRIDE_UNLOCK, "Force Unlock"),
        (OVERRIDE_LOCK, "Force Lock"),
    ]

    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.CASCADE, related_name="session_overrides"
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="overrides")
    override_type = models.CharField(max_length=20, choices=OVERRIDE_CHOICES)
    set_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["participant", "session"]

    def __str__(self):
        return f"{self.participant} — {self.session} — {self.get_override_type_display()}"
