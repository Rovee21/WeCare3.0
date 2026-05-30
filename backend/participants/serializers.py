from rest_framework import serializers
from .models import Participant


class EnrollSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


class ParticipantProfileSerializer(serializers.ModelSerializer):
    participant_id = serializers.ReadOnlyField()
    week_number = serializers.ReadOnlyField(source="current_week_number")

    class Meta:
        model = Participant
        fields = [
            "participant_id",
            "label",
            "language",
            "group1",
            "group2",
            "group3",
            "adrd_relationship_group",
            "stage",
            "week_number",
            "enrolled_at",
        ]
