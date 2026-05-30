from rest_framework import serializers
from .models import VoiceJournalEntry, VoiceJournalPrompt


class VoiceJournalPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceJournalPrompt
        fields = ["week_number", "prompt_en", "prompt_zh"]


class VoiceJournalSubmitSerializer(serializers.Serializer):
    audio_s3_key = serializers.CharField(max_length=500)
    recording_seconds = serializers.IntegerField(min_value=0)
    vj_stress_level = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)


class VoiceJournalEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceJournalEntry
        fields = [
            "id", "week_number", "recording_seconds",
            "vj_stress_level", "transcription_status", "submitted_at",
        ]
