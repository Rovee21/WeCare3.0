from rest_framework import serializers
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
        ]
