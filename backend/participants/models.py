import secrets
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Participant(models.Model):
    LANGUAGE_EN = "en"
    LANGUAGE_ZH = "zh"
    LANGUAGE_CHOICES = [(LANGUAGE_EN, "English"), (LANGUAGE_ZH, "Mandarin")]

    GROUP1_INTERVENTION = "intervention"
    GROUP1_CONTROL = "control"
    GROUP1_CHOICES = [
        (GROUP1_INTERVENTION, "Intervention"),
        (GROUP1_CONTROL, "Control"),
    ]

    GROUP2_MILD = "mild"
    GROUP2_MODERATE = "moderate"
    GROUP2_SEVERE = "severe"
    GROUP2_CHOICES = [
        (GROUP2_MILD, "Mild"),
        (GROUP2_MODERATE, "Moderate"),
        (GROUP2_SEVERE, "Severe"),
    ]

    GROUP3_HIGH = "high"
    GROUP3_LOW = "low"
    GROUP3_CHOICES = [
        (GROUP3_HIGH, "High Stress"),
        (GROUP3_LOW, "Low Stress"),
    ]

    RELATIONSHIP_SPOUSE = "spouse"
    RELATIONSHIP_CHILDREN = "children"
    RELATIONSHIP_RELATIVE = "relative"
    RELATIONSHIP_CHOICES = [
        (RELATIONSHIP_SPOUSE, "Spouse"),
        (RELATIONSHIP_CHILDREN, "Children / Adult Child"),
        (RELATIONSHIP_RELATIVE, "Other Relative"),
    ]

    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_OTHER = "other"
    GENDER_CHOICES = [
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
        (GENDER_OTHER, "Other / Prefer not to say"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="participant"
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    label = models.CharField(max_length=100, blank=True, help_text='Short human-readable label e.g. Mrs. Smith')
    adrd_stage = models.CharField(
        max_length=20,
        blank=True,
        choices=[('mild', 'Mild'), ('moderate', 'Moderate'), ('severe', 'Severe')],
        help_text='Stage of ADRD of care recipient'
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_EN)
    group1 = models.CharField(max_length=20, choices=GROUP1_CHOICES)
    group2 = models.CharField(max_length=20, choices=GROUP2_CHOICES)
    group3 = models.CharField(max_length=20, choices=GROUP3_CHOICES)
    adrd_relationship_group = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    cohort = models.PositiveSmallIntegerField(default=1, help_text="Recruitment cohort/wave number (e.g., 1 = Cohort 1, 2 = Cohort 2). Represents which recruitment area/wave the participant belongs to — independent of group1/group2/group3.")

    enrollment_week = models.PositiveSmallIntegerField(default=1)
    enrolled_at = models.DateTimeField(null=True, blank=True)
    is_enrolled = models.BooleanField(default=False)
    enrollment_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    push_token = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.participant_id

    @property
    def participant_id(self) -> str:
        return f"P{self.pk:05d}"

    @property
    def current_week_number(self) -> int:
        """Cohort-anchored week number: 0 while waitlisted (cohort hasn't started, or has
        no CohortStartDate yet), otherwise the same value automatic_gated_week() computes."""
        if self.is_waitlisted():
            return 0
        return self.automatic_gated_week()

    def _cohort_start_date(self):
        """This participant's cohort's program_start_date, or None if no CohortStartDate
        row exists yet for their cohort."""
        try:
            return CohortStartDate.objects.get(cohort=self.cohort).program_start_date
        except CohortStartDate.DoesNotExist:
            return None

    def is_waitlisted(self) -> bool:
        """True if the participant's cohort hasn't started yet — either no CohortStartDate
        has been set for their cohort at all, or its program_start_date is still in the
        future. A waitlisted participant sees no content, regardless of enrolled_at."""
        start_date = self._cohort_start_date()
        if start_date is None:
            return True
        return timezone.localdate() < start_date

    def program_start_date(self):
        """The date this participant's cohort's content schedule starts (Week 1 Day 1),
        or None if no CohortStartDate has been set for their cohort yet."""
        return self._cohort_start_date()

    def _schedule_anchor(self):
        """Datetime anchor ('day 0') for content-schedule calculations: midnight local
        time on the participant's cohort's program_start_date. None while waitlisted —
        callers should check is_waitlisted() before relying on this."""
        if self.is_waitlisted():
            return None
        from datetime import datetime
        naive_midnight = datetime.combine(self._cohort_start_date(), datetime.min.time())
        return timezone.make_aware(naive_midnight)

    def _week_start(self, week_number: int):
        anchor = self._schedule_anchor()
        if anchor is None:
            return None
        return anchor + timedelta(days=7 * (week_number - 1))

    def _cohort_matched_session_ids(self, week_number: int) -> list[int]:
        """Session ids in a given week that this participant's cohort would ever see.
        Mirrors the cohort-matching in content.views._filter_sessions_for_participant —
        needed here so week-completion gating only counts sessions this participant
        could actually read, not ones targeted at a different cohort."""
        from content.models import Session
        ids = []
        for s in Session.objects.filter(is_active=True, week_number=week_number).only(
            "id", "target_group1", "target_group2", "target_group3"
        ):
            g1_ok = not s.target_group1 or s.target_group1 == self.group1
            g2_ok = not s.target_group2 or s.target_group2 == self.group2
            g3_ok = not s.target_group3 or s.target_group3 == self.group3
            if g1_ok and g2_ok and g3_ok:
                ids.append(s.id)
        return ids

    def automatic_gated_week(self) -> int:
        """Calendar-and-completion-gated week number: starting at week 1, advances one
        week at a time only once 7 calendar days have passed since that week's fixed
        calendar start AND every session in it (for this participant's cohort) is read.
        Anchored to the participant's cohort's program_start_date (shared by everyone in
        that cohort), not their individual enrolled_at."""
        if self.is_waitlisted():
            return 1
        from content.models import ParticipantSession

        now = timezone.now()
        week = 1
        while week < 7:
            days_elapsed = (now - self._week_start(week)).days
            if days_elapsed < 7:
                break
            session_ids = self._cohort_matched_session_ids(week)
            if not session_ids:
                break
            read_count = ParticipantSession.objects.filter(
                participant=self, session_id__in=session_ids, is_read=True
            ).count()
            if read_count < len(session_ids):
                break
            week += 1
        return week

    def effective_current_week(self) -> int:
        """The week whose sessions should be shown: the automatic calendar+completion
        calculation, unless an admin has manually pushed enrollment_week further ahead."""
        automatic = self.automatic_gated_week()
        if self.enrollment_week and self.enrollment_week > automatic:
            return self.enrollment_week
        return automatic

    def unlocked_day_number(self) -> int:
        """Highest day_number (1-6) unlocked within the participant's effective current
        week. A week reached via manual admin override has no calendar anchor to measure
        days-into-week from, so it's granted fully unlocked."""
        automatic = self.automatic_gated_week()
        effective = self.effective_current_week()
        if effective > automatic:
            return 6
        if self.is_waitlisted():
            return 1
        days_elapsed = (timezone.now() - self._week_start(effective)).days
        return max(1, min(days_elapsed + 1, 6))

    def generate_enrollment_code(self):
        while True:
            code = f"{secrets.randbelow(100_000):05d}"
            if not Participant.objects.exclude(pk=self.pk).filter(enrollment_code=code).exists():
                break
        self.enrollment_code = code
        self.save(update_fields=["enrollment_code"])
        return code


class CohortStartDate(models.Model):
    cohort = models.PositiveSmallIntegerField(unique=True, help_text="Matches Participant.cohort")
    program_start_date = models.DateField(help_text="The date this cohort's Week 1 Day 1 content unlocks for everyone in it, regardless of individual signup date.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cohort {self.cohort} — starts {self.program_start_date}"
