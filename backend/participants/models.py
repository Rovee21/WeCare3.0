import secrets
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
        (GROUP1_CONTROL, "Non-intervention"),
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
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_EN)
    group1 = models.CharField(max_length=20, choices=GROUP1_CHOICES)
    group2 = models.CharField(max_length=20, choices=GROUP2_CHOICES)
    group3 = models.CharField(max_length=20, choices=GROUP3_CHOICES)
    adrd_relationship_group = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)

    enrollment_week = models.PositiveSmallIntegerField(default=1)
    enrolled_at = models.DateTimeField(null=True, blank=True)
    is_enrolled = models.BooleanField(default=False)
    enrollment_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.participant_id

    @property
    def participant_id(self):
        return f"P{self.pk:05d}"

    @property
    def current_week_number(self):
        if not self.enrolled_at:
            return 1
        days_since = (timezone.now() - self.enrolled_at).days
        week = (days_since // 7) + 1
        return min(week, 7)

    def generate_enrollment_code(self):
        code = secrets.token_urlsafe(6).upper()[:8]
        self.enrollment_code = code
        self.save(update_fields=["enrollment_code"])
        return code
