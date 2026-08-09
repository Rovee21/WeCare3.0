from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Participant


class EnrollSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


class EnrollResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    language = serializers.CharField()
    participant_id = serializers.CharField()
    week_number = serializers.IntegerField()
    group1 = serializers.CharField()
    group2 = serializers.CharField()
    group3 = serializers.CharField()
    adrd_relationship_group = serializers.CharField()


class ParticipantProfileSerializer(serializers.ModelSerializer):
    participant_id = serializers.ReadOnlyField()
    week_number = serializers.ReadOnlyField(source="current_week_number")
    is_waitlisted = serializers.SerializerMethodField()
    program_start_date = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            "participant_id",
            "language",
            "group1",
            "group2",
            "group3",
            "adrd_relationship_group",
            "week_number",
            "enrolled_at",
            "is_waitlisted",
            "program_start_date",
        ]

    @extend_schema_field(serializers.BooleanField)
    def get_is_waitlisted(self, obj):
        return obj.is_waitlisted()

    @extend_schema_field(serializers.DateField(allow_null=True))
    def get_program_start_date(self, obj):
        return obj.program_start_date()
